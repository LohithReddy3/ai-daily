import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
import json
import asyncio
import logging
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from ..database import SessionLocal
from ..models import Story, StorySummary, Persona, SourceType

logger = logging.getLogger(__name__)

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

HIERARCHY = {
    "builders": ["Models", "RAG & Agents", "Papers", "Open Source"],
    "executors": ["Markets", "Enterprise", "Industry", "Policy", "Startups", "Strategy", "Compute"],
    "explorers": ["AGI & Future", "Ethics", "Jobs & Society", "Demos & Creativity"],
    "thought_leaders": ["Deep Dives", "Concepts", "Hot Takes"]
}

async def generate_summary(story_text, persona: Persona, category: str):
    if not api_key:
        logger.warning("GEMINI_API_KEY not set. Skipping summarization.")
        return None

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        logger.error(f"Error creating model: {e}")
        return None
    
    prompt = f"""
    You are an expert AI analyst. Analyze the following news items and generate a summary for the '{persona.value}' persona, specifically under the category '{category}'.
    
    Input Text:
    {story_text}
    
    Output must be strict JSON with the following schema:
    
    If Persona is BUILDERS (Technical/Developer focus):
    {{
        "summary_short": "max 40 words",
        "bullets": ["technical specs/architecture", "API/Library changes", "performance metrics", "how to implement"],
        "actionable_next_step": "1 code-centric or implementation line",
        "confidence": "low/med/high"
    }}

    If Persona is EXECUTORS (Business/Strategic focus):
    {{
        "why_it_matters": "The strategic 'so what' for decision makers",
        "summary_short": "max 35 words",
        "bullets": ["market impact", "enterprise adoption", "competitive shift", "ROI/Efficiency gains"],
        "confidence": "low/med/high"
    }}

    If Persona is EXPLORERS (Future/Society/Ethics focus):
    {{
        "summary_short": "max 45 words",
        "bullets": ["long-term societal shift", "ethical considerations", "creative possibilities", "impact on human labor"],
        "open_questions": ["1-2 philosophical or future-looking bullets"],
        "confidence": "low/med/high"
    }}
    
    If Persona is THOUGHT_LEADERS (High Signal/Expert focus):
    {{
        "summary_short": "max 40 words, very dense and insightful",
        "bullets": ["key arguments", "contrarian points", "mental models", "predictions"],
        "actionable_next_step": "1 insight to apply",
        "confidence": "high"
    }}
    
    Critical rule: Focus purely on the {persona.value} perspective and the {category} context. Do not invent.
    """
    
    try:
        response = await model.generate_content_async(prompt)
        text = response.text
        # Clean up json markdown if present
        text = text.replace("```json", "").replace("```", "")
        data = json.loads(text)
        return data
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        if "404" in str(e) or "not found" in str(e):
             logger.info("listing available models...")
             for m in genai.list_models():
                 logger.info(f"Model: {m.name}")
        return None

async def summarize_stories():
    async with SessionLocal() as session:
        from sqlalchemy import func

        # Get stories without 3 summaries, but only the Top 15 by signal strength
        # To avoid wasting tokens on old or low-interest items
        stmt = (
            select(Story)
            .outerjoin(Story.items)
            .group_by(Story.id)
            .options(selectinload(Story.items), selectinload(Story.summaries))
            .order_by(func.count(Story.items.property.mapper.class_.id).desc(), Story.created_at.desc())
            .limit(50)
        )
        
        result = await session.execute(stmt)
        stories = result.scalars().unique().all()
        
        model = genai.GenerativeModel('gemini-2.5-flash')

        for story in stories:
            # Gather existing personas
            existing_personas = {s.persona for s in story.summaries}
            
            # Prepare story text for classification
            if not story.items:
                continue
                
            story_context = f"Title: {story.canonical_title}\n"
            for i in story.items[:3]:
                story_context += f"- {i.title}: {i.raw_text[:300] if i.raw_text else ''}\n"

            # Decide which personas/categories this is relevant for
            relevance_prompt = f"""
Given this AI news story, classify it into the most relevant PERSONAS and CATEGORIES.
Hierarchy:
{json.dumps(HIERARCHY, indent=2)}

Rules:
1. Pick at most 2 Personas.
2. For each Persona, pick exactly 1 relevant Category from the hierarchy.

Story:
{story_context}

Return strict JSON:
{{
    "classifications": [
        {{"persona": "builders", "category": "Models"}},
        ...
    ]
}}
"""
            try:
                response = await model.generate_content_async(relevance_prompt)
                text = response.text.replace("```json", "").replace("```", "")
                result = json.loads(text)
                targets = result.get("classifications", [])
                logger.info(f"Target classifications for {story.id}: {targets}")
            except Exception as e:
                logger.error(f"Relevance check failed: {e}. Using fallback...")
                targets = [{"persona": "builders", "category": "Models"}]

            for target in targets:
                persona_val = target.get("persona")
                category = target.get("category")
                
                try:
                    persona = Persona(persona_val)
                except ValueError:
                    continue

                # Check if this specific persona/category combo already exists
                existing = any(s.persona == persona and s.category == category for s in story.summaries)
                if existing:
                    continue
                
                logger.info(f"Generating {persona.value}/{category} summary for story {story.id}")
                story_text = "\n\n".join([f"Title: {i.title}\nUrl: {i.url}\nText: {i.raw_text}" for i in story.items[:5]])
                data = await generate_summary(story_text, persona, category)
                
                if data:
                    new_summary = StorySummary(
                        story_id=story.id,
                        persona=persona,
                        category=category,
                        summary_short=data.get("summary_short", ""),
                        summary_bullets=data.get("bullets", []),
                        why_it_matters=data.get("why_it_matters", "") if persona == Persona.executors else "",
                        confidence=data.get("confidence", "low")
                    )
                    
                    if persona == Persona.builders and "actionable_next_step" in data:
                         new_summary.key_entities = [data["actionable_next_step"]]
                    elif persona == Persona.explorers and "open_questions" in data:
                         new_summary.key_entities = data["open_questions"]
                    elif persona == Persona.thought_leaders and "actionable_next_step" in data:
                         new_summary.key_entities = [data["actionable_next_step"]]

                    session.add(new_summary)
            
            await session.commit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(summarize_stories())
