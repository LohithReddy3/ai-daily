import google.generativeai as genai
import json
import asyncio
import logging
import os
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from ..database import SessionLocal
import uuid
from ..models import Story, StorySummary, Persona, StoryState, Item, StoryItem
from .retrieval import search_similar_stories

logger = logging.getLogger(__name__)

from .image_gen import generate_story_image

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

PROMPT_VERSION = "v6.1"
MODEL_NAME = "gemini-2.0-flash" 

# --- Prompts ---

# --- 1. EVIDENCE CONSTRUCTION ---

def build_evidence_pack(story, items):
    """
    Constructs a structured evidence pack for LLM analysis.
    includes metadata, excerpts, and specific signal extraction.
    """
    if not items:
        return "NO EVIDENCE AVAILABLE"
        
    # Sort to find the best item (primary first, then by similarity/date if available)
    # StoryItem objects have 'is_primary'
    sorted_items = items
    if hasattr(items[0], 'is_primary'):
        sorted_items = sorted(items, key=lambda x: x.is_primary, reverse=True)
        primary_obj = sorted_items[0].item # Access the Item object from StoryItem
    else:
        primary_obj = items[0] # Assume it's already an Item object
    
    if not primary_obj:
         return "NO EVIDENCE AVAILABLE"
    
    # Metadata
    source_name = primary_obj.source.name if primary_obj.source else "Unknown"
    source_kind = primary_obj.source.source_kind if primary_obj.source else "Unknown"
    source_weight = primary_obj.source.reputation_weight if primary_obj.source else 1.0
    
    # Text Content
    full_text = primary_obj.clean_text or primary_obj.raw_text or ""
    
    # Structured Excerpts

    # 1. Start (Lead)
    lead = full_text[:1200]
    
    # 2. Middle (Best Paragraphs - simplistic heuristic for now: length)
    paragraphs = full_text.split('\n')
    # Filter short lines
    paragraphs = [p for p in paragraphs if len(p) > 100]
    # Sort by length and take top 3
    best_paragraphs = sorted(paragraphs, key=len, reverse=True)[:3]
    middle = "\n\n".join(best_paragraphs)
    
    # 3. End (Conclusion)
    end = full_text[-600:]
    
    # Signal Extraction (Regex)
    import re
    # Numbers (including decimals, percentages, $)
    numeric_lines = []
    for line in full_text.split('\n'):
        if len(line) < 200 and re.search(r'\d+(\.\d+)?%|\$\d+|\d+x|benchmark|latency|throughput|parameters', line, re.IGNORECASE):
            numeric_lines.append(line.strip())
            
    extracted_signals = "\n".join(numeric_lines[:10]) # Limit to top 10 detections
    
    evidence = f"TITLE: {story.canonical_title}\nSOURCE: {source_name} ({source_kind}, weight={source_weight})\nDATE: {primary_obj.published_at}\nURL: {primary_obj.url}\n\n=== KEY EXCERPT (LEAD) ===\n{lead}\n\n=== KEY EXCERPT (HIGHLIGHTS) ===\n{middle}\n\n=== KEY EXCERPT (CONCLUSION) ===\n{end}\n\n=== EXTRACTED SIGNALS (NUMBERS/METRICS) ===\n{extracted_signals}\n"
    return evidence

SIGNAL_JUDGE_PROMPT = """
You are a news signal judge. Determine if this story is worth showing to users.
Review the evidence pack and duplicate candidates (if any).
EVIDENCE PACK:
{evidence_pack}

DUPLICATE CANDIDATES:
{duplicate_candidates}

Decide if the story has high enough signal to show.
Return strictly JSON formatting:
{{
  "show": true or false,
  "signal_score": 0 to 100,
  "confidence": "low" | "med" | "high",
  "reason": "short explanation"
}}
"""

PERSONA_ROUTER_PROMPT = """
You are a routing agent. Evaluate the evidence pack and determine which personas this story is genuinely relevant to. Do not force classifications if the story is deeply niche.

EVIDENCE PACK:
{evidence_pack}

Available Categories by Persona:
BUILDERS: Models, RAG & Agents, Papers, Open Source, Infrastructure
EXECUTORS: Markets, Enterprise, Industry, Policy, Startups, Strategy, Compute
EXPLORERS: AGI & Future, Ethics, Jobs & Society, Demos & Creativity

Return STRICTLY JSON formatting matching this structure. The array should contain 1 to 3 objects, mapping the best category to any relevant personas based on the content.
{{
  "classifications": [
    {{"persona": "builders", "category": "<valid BUILDERS category>"}},
    {{"persona": "executors", "category": "<valid EXECUTORS category>"}}
  ],
  "reason": "short explanation of your choices"
}}
"""

PERSONA_WRITER_PROMPT = """
ROLE: StrategicIntelligenceUnit
PROMPT_VERSION: v6.1

SYSTEM ROLE:
You are not summarizing blog posts.
You are generating differentiated strategic intelligence briefs for three distinct personas:
- BUILDERS
- EXECUTORS
- EXPLORERS

INPUT:
{evidence_pack}

PERSONA:
{persona}
CATEGORY:
{category}

GLOBAL RULES (STRICT):
1. NO DESCRIPTION: Do not describe "what happened". Focus ONLY on constraints removed, capabilities unlocked, and workflow changes.
2. NO FEATURE LISTS: Convert features into capability shifts. (Bad: "1M context window". Good: "Enables full-repository reasoning").
3. NO HEDGING: Use decisive language. Avoid "could", "may", "potential".
4. NO FLUFF: Zero marketing tone. Zero "This story discusses...".
5. DISTINCT LENSES: If two personas sound similar, you have FAILED.

PERSONA LENSES:

🏗 BUILDERS (Audience: Engineers, architects, AI developers)
Tone: Technical leverage, architectural implications, autonomy, scale.
IMPACT must answer:
- What constraint was removed?
- What new architectural pattern is emerging?
- What integration primitive is being introduced?
TAKEAWAYS must:
- Highlight reusable patterns and system-level shifts.
- Explain "How does this change my design?"
CONTEXT must:
- Anchor to toolchain evolution and engineering complexity shifts.

⚙️ EXECUTORS (Audience: Operators, VPs, transformation leads)
Tone: Efficiency, cost reduction, operational simplification, risk management.
IMPACT must answer:
- What operational burden is being reduced?
- What becomes faster, cheaper, or more autonomous?
- What competitive leverage does this create?
TAKEAWAYS must:
- Focus on workflow redesign and procurement simplification.
- Explain "How does this change our operations?"
CONTEXT must:
- Anchor to enterprise adoption friction and cost/governance implications.

🔭 EXPLORERS (Audience: Strategists, long-term thinkers)
Tone: Trajectory, industry shifts, systemic change, competitive positioning.
IMPACT must answer:
- What structural shift does this signal?
- Is this incremental or paradigm-shifting?
- What trajectory is confirmed or disrupted?
TAKEAWAYS must:
- Identify capability evolution and ecosystem consolidation.
- Explain "Where is the puck going?"
CONTEXT must:
- Connect to 2–5 year horizon implications and second-order effects.

OUTPUT STRUCTURE (STRICT JSON):
{{
  "impact": "...",
  "takeaways": [
    "...",
    "...",
    "..."
  ],
  "context": "...",
  "confidence": "low" | "med" | "high"
}}

SELF-CHECK BEFORE FINAL OUTPUT:
- Did I describe "what happened"? -> REWRITE.
- Did I list features? -> REWRITE.
- Did I use "could" or "may"? -> REWRITE.
- Does it answer "What changes for this persona?" -> IF NO, REWRITE.

Return ONLY the final JSON.
"""

# (Critic Removed as per SPEC - using Verifier instead)




# HIERARCHY constant
HIERARCHY = {
    "builders": ["Models", "RAG & Agents", "Papers", "Open Source", "Infrastructure"],
    "executors": ["Markets", "Enterprise", "Industry", "Policy", "Startups", "Strategy", "Compute"],
    "explorers": ["AGI & Future", "Ethics", "Jobs & Society", "Demos & Creativity"],
    "thought_leaders": ["Deep Dives", "Concepts", "Hot Takes"]
}

async def call_llm_with_retry(prompt, model_name=MODEL_NAME, max_retries=3):
    """
    Robust LLM call with exponential backoff and JSON repair.
    """
    delay = 1
    
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(model_name)
            # Use sync API in thread to avoid greenlet context issues
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            # Parsing attempt 1
            try:
                text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(text)
                return data
            except json.JSONDecodeError:
                logger.warning(f"JSON Parse failed (attempt {attempt+1}). Trying repair...")
                # Repair attempt
                repair_prompt = f"Fix this invalid JSON and return ONLY the valid JSON:\n\n{text}"
                repair_resp = await asyncio.to_thread(model.generate_content, repair_prompt)
                fixed_text = repair_resp.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(fixed_text)
                return data
                
        except Exception as e:
            logger.error(f"LLM Call Error (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.error("Max retries reached.")
                return None
    return None

async def run_signal_judge(story, evidence_pack, duplicate_candidates="None"):
    # STAGE 0: Deterministic Prefilter
    # Reject if content too short or no signal
    if "EXTRACTED SIGNALS (NUMBERS/METRICS) ===" in evidence_pack:
        signals = evidence_pack.split("=== EXTRACTED SIGNALS (NUMBERS/METRICS) ===")[1].strip()
        if not signals and len(evidence_pack) < 800:
             logger.info(f"PREFILTER REJECT: {story.canonical_title} (Too short, no signals)")
             return {"show": False, "signal_score": 0, "reason": "Prefilter: Low signal density"}

    prompt = SIGNAL_JUDGE_PROMPT.format(
        evidence_pack=evidence_pack,
        duplicate_candidates=duplicate_candidates
    )
    result = await call_llm_with_retry(prompt)
    
    if not result:
        return None
        
    # STAGE 2: Confidence Gate
    confidence = result.get("confidence", "low")
    score = result.get("signal_score", 0)
    
    if confidence == "high":
        pass # Accept decision
    elif confidence == "med" and score > 50:
        pass # Accept decision
    elif confidence == "low":
        # Downgrade or reject
        if result.get("show", False):
            logger.info("  -> GATE: Low confidence, forcing re-review or drop. (For now: Drop)")
            result["show"] = False
            result["reason"] += " [GATE: Low Confidence]"
            
    return result

async def run_persona_router(story, evidence_pack):
    prompt = PERSONA_ROUTER_PROMPT.format(
        evidence_pack=evidence_pack
    )
    result = await call_llm_with_retry(prompt)
    if not result: return None
    
    # helper to validate category
    def validate(persona, cat):
        valid_cats = HIERARCHY.get(persona, [])
        if cat in valid_cats: return cat
        # Repair: fuzzy match or default?
        # For now, simplistic repair or fail
        for v in valid_cats:
            if v.lower() in cat.lower(): return v
        return valid_cats[0] if valid_cats else "General" # Fallback

    # Transform output dynamically based on LLM response (1-3 classifications)
    classifications = []
    
    raw_classifications = result.get("classifications", [])
    
    if not isinstance(raw_classifications, list):
         logger.warning("Router didn't return a list for classifications. Falling back.")
         raw_classifications = []
         
    for item in raw_classifications:
         p = item.get("persona", "").lower()
         c = item.get("category", "")
         if p in HIERARCHY and c:
             valid_c = validate(p, c)
             # De-dupe persona
             if not any(x["persona"] == p for x in classifications):
                 classifications.append({"persona": p, "category": valid_c})
                 
    # Absolute fallback if LLM completely hallucinates the structure
    if not classifications:
         classifications.append({"persona": "builders", "category": validate("builders", "")})
             
    return {"classifications": classifications, "routing_reason": result.get("reason", "")}

async def run_persona_writer(story, persona, category, evidence_pack):
    prompt = PERSONA_WRITER_PROMPT.format(
        evidence_pack=evidence_pack,
        persona=persona,
        category=category
    )
    return await call_llm_with_retry(prompt)



async def job_run_agents():
    async with SessionLocal() as session:
        # Get stories that need classification
        # Only process stories from last 7 days
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        stmt = (
            select(Story)
            .where(Story.is_active == True)
            .where(Story.created_at >= seven_days_ago)  # Only last 7 days
            .where(Story.signal_score > 10) # Low threshold to let judge decide
            .where(Story.classified_at == None) # Only unprocessed stories
            .order_by(Story.created_at.desc()) # Process newest first
            .options(selectinload(Story.story_items).selectinload(StoryItem.item).selectinload(Item.source))
            .limit(50) # Process up to 50 stories
        )
        # In reality, refine query to check timestamps. 
        # For simplicity, we check timestamps in python loop or assume job frequency handles it.
        
        result = await session.execute(stmt)
        stories = result.scalars().unique().all()
        
        for story in stories:
            if story.classification_json and story.classified_at and story.updated_at and story.classified_at > story.updated_at:
                continue 
            
            logger.info(f"Processing Story: {story.canonical_title}")
            
            # 0. Build Evidence Pack
            evidence_pack = build_evidence_pack(story, story.story_items)
            
            # 1. Signal Judge
            # TODO: Logic to find duplicate candidates can be added here
            judge_result = await run_signal_judge(story, evidence_pack)
            if not judge_result: continue
            
            story.classification_json = judge_result
            story.classified_at = datetime.utcnow()
            
            if not judge_result.get("show", False):
                logger.info("  -> Judge said SKIP")
                continue
            
            logger.info("  -> Judge said SHOW")
                
            # 2. Persona Router
            router_result = await run_persona_router(story, evidence_pack)
            if not router_result: continue
            
            targets = router_result.get("classifications", [])
            logger.info(f"  -> Routed to: {targets}")
            
            # 2.5 Generative Art (Existing)
            if not story.generated_image_url:
                try:
                    gen_prompt = f"Futuristic concept art, 4k render, {story.canonical_title}, highly detailed, tech style"
                    img_url = await generate_story_image(gen_prompt)
                    if img_url: 
                        story.generated_image_url = img_url
                        logger.info(f"  -> Generated Art: {img_url}")
                except Exception as e:
                    logger.error(f"  -> Art Gen Failed: {e}")
            
            # 3. Writer Loop
            for target in targets:
                persona_val = target.get("persona")
                category = target.get("category")
                
                try:
                    persona_enum = Persona(persona_val.lower())
                except ValueError:
                    logger.warning(f"Invalid persona '{persona_val}'")
                    continue
                    
                # Write
                draft = await run_persona_writer(story, persona_val, category, evidence_pack)
                if not draft: continue
                
                # 4. Verifier (Quality Check)
                # Simple deterministic check
                if "context" not in draft or "impact" not in draft or "takeaways" not in draft:
                    logger.warning(f"  -> Verifier Failed ({persona_val}): Missing keys")
                    continue
                    
                if len(draft.get("takeaways", [])) != 3:
                     logger.warning(f"  -> Verifier Failed ({persona_val}): Bullet count != 3")
                     continue

                # Save
                stmt_exist = select(StorySummary).where(
                    StorySummary.story_id == story.id,
                    StorySummary.persona == persona_enum,
                    StorySummary.category == category
                )
                res = await session.execute(stmt_exist)
                summary = res.scalars().first()
                
                if not summary:
                    summary = StorySummary(
                        id=str(uuid.uuid4()),
                        story_id=story.id,
                        persona=persona_enum,
                        category=category
                    )
                    session.add(summary)
                
                # Map V4 keys to DB model
                summary.summary_short = draft.get("impact", "") # Map Impact -> summary_short
                summary.why_it_matters = draft.get("context", "") # Map Context -> why_it_matters
                summary.summary_bullets = draft.get("takeaways", [])
                summary.confidence = draft.get("confidence", "med")
                summary.model_name = MODEL_NAME
                summary.prompt_version = PROMPT_VERSION
                summary.last_reviewed_at = datetime.utcnow()
                
            await session.commit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(job_run_agents())
