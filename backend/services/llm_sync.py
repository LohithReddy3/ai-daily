"""
Synchronous version of the LLM agent service.
Uses synchronous database session to avoid async/greenlet conflicts.
"""
import google.generativeai as genai
import json
import logging
import os
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.database_sync import SyncSessionLocal
import uuid
from backend.models import Story, StorySummary, Persona, StoryState, Item, StoryItem

logger = logging.getLogger(__name__)

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

PROMPT_VERSION = "v2.0"
MODEL_NAME = "gemini-2.0-flash"

# Import prompts and hierarchy from async version
from backend.services.llm import (
    SIGNAL_JUDGE_PROMPT,
    PERSONA_ROUTER_PROMPT,
    PERSONA_WRITER_PROMPT,
    CRITIC_PROMPT,
    HIERARCHY
)

def call_llm_with_retry_sync(prompt, model_name=MODEL_NAME, max_retries=3):
    """
    Synchronous LLM call with retry logic.
    """
    import time
    delay = 1
    
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            # Parsing attempt
            try:
                text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(text)
                return data
            except json.JSONDecodeError:
                logger.warning(f"JSON Parse failed (attempt {attempt+1}). Trying repair...")
                repair_prompt = f"Fix this invalid JSON and return ONLY the valid JSON:\n\n{text}"
                repair_resp = model.generate_content(repair_prompt)
                fixed_text = repair_resp.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(fixed_text)
                return data
                
        except Exception as e:
            logger.error(f"LLM Call Error (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                logger.error("Max retries reached.")
                return None
    return None

def run_signal_judge_sync(story, evidence_block, sources_block):
    prompt = SIGNAL_JUDGE_PROMPT.format(
        story_id=story.id,
        canonical_title=story.canonical_title,
        created_at=str(story.created_at),
        updated_at=str(story.updated_at),
        signal_score=story.signal_score,
        confidence_score=story.confidence_score,
        sources_block=sources_block,
        evidence_block=evidence_block
    )
    return call_llm_with_retry_sync(prompt)

def run_persona_router_sync(story, evidence_block):
    prompt = PERSONA_ROUTER_PROMPT.format(
        story_id=story.id,
        canonical_title=story.canonical_title,
        evidence_block=evidence_block,
        hierarchy_json=json.dumps(HIERARCHY, indent=2)
    )
    return call_llm_with_retry_sync(prompt)

def run_persona_writer_sync(story, persona, category, evidence_pack):
    prompt = PERSONA_WRITER_PROMPT.format(
        story_id=story.id,
        persona=persona,
        category=category,
        canonical_title=story.canonical_title,
        evidence_pack=evidence_pack
    )
    return call_llm_with_retry_sync(prompt)

def run_critic_sync(story, persona, category, evidence_pack, draft_json):
    prompt = CRITIC_PROMPT.format(
        story_id=story.id,
        persona=persona,
        category=category,
        evidence_pack=evidence_pack,
        draft_summary_json=json.dumps(draft_json, indent=2)
    )
    return call_llm_with_retry_sync(prompt)

def job_run_agents_sync():
    """
    Synchronous version of the agent job.
    Generates summaries for stories from the last 7 days.
    """
    session = SyncSessionLocal()
    
    try:
        # Get stories from last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # Fetch larger pool of unclassified stories to find diverse candidates
        stmt = (
            select(Story)
            .where(Story.is_active == True)
            .where(Story.created_at >= seven_days_ago)
            .where(Story.classification_json.is_(None))  # ONLY process stories that haven't been classified yet
            .options(selectinload(Story.story_items).selectinload(StoryItem.item).selectinload(Item.source))
            .order_by(Story.created_at.desc())  # Recent first
            .limit(1000)
        )
        
        result = session.execute(stmt)
        candidates = result.scalars().unique().all()
        
        # Diversity Selection: Prioritize coverage of all sources
        stories = []
        source_counts = {}
        MAX_PER_SOURCE = 5 # Ensure we cover 5 stories per source
        TARGET_BATCH = 50  # Process 50 at a time (fast feedback)
        
        for s in candidates:
            src = "Unknown"
            if s.story_items and s.story_items[0].item.source:
                src = s.story_items[0].item.source.name
            
            # Prioritize sources we haven't seen much of
            if source_counts.get(src, 0) < MAX_PER_SOURCE:
                stories.append(s)
                source_counts[src] = source_counts.get(src, 0) + 1
            else:
                pass # Skipping due to cap
                
            if len(stories) >= TARGET_BATCH:
                break
        
        logger.info(f"Selected {len(stories)} stories for processing")
        logger.info(f"Source Counts in Batch: {source_counts}")
                
        # If we didn't fill the batch with diverse stories, fill with remaining
        if len(stories) < TARGET_BATCH:
            remaining = [s for s in candidates if s.id not in {x.id for x in stories}]
            stories.extend(remaining[:TARGET_BATCH - len(stories)])
        
        logger.info(f"Processing {len(stories)} stories from last 7 days")
        
        for story in stories:
            # Skip if already classified
            if story.classification_json and story.classified_at and story.updated_at and story.classified_at > story.updated_at:
                continue
            
            logger.info(f"Processing Story: {story.canonical_title}")
            
            # Prepare evidence
            primary_items = sorted(story.story_items, key=lambda x: (x.is_primary, x.similarity_score), reverse=True)[:3]
            evidence_lines = []
            sources_info = []
            
            for si in primary_items:
                item = si.item
                # Fallback to raw_text (RSS description) if clean_text is missing
                content = item.clean_text or item.raw_text or item.title # Last resort
                evidence_lines.append(f"TITLE: {item.title}\nURL: {item.url}\nTEXT: {content[:1000]}...")
                if item.source:
                    sources_info.append(f"{item.source.name} (weight: {item.source.reputation_weight})")
            
            evidence_block = "\n---\n".join(evidence_lines)
            sources_block = "\n".join(sources_info)
            
            # 1. Signal Judge
            judge_result = run_signal_judge_sync(story, evidence_block, sources_block)
            if not judge_result:
                continue
            
            story.classification_json = judge_result
            story.classified_at = datetime.utcnow()
            
            if not judge_result.get("show", False):
                logger.info("  -> Judge said SKIP")
                continue
            
            logger.info("  -> Judge said SHOW")
            
            # 2. Persona Router
            router_result = run_persona_router_sync(story, evidence_block)
            if not router_result:
                continue
            
            targets = router_result.get("classifications", [])
            logger.info(f"  -> Routed to: {targets}")
            
            # 3. Writer & Critic Loop
            for target in targets:
                persona_val = target.get("persona")
                category = target.get("category")
                
                try:
                    persona_enum = Persona(persona_val)
                except:
                    continue
                
                # Write
                draft = run_persona_writer_sync(story, persona_val, category, evidence_block)
                if not draft:
                    continue
                
                # Critic
                critic_res = run_critic_sync(story, persona_val, category, evidence_block, draft)
                
                final_summary_json = draft
                quality_score = 0
                
                if critic_res:
                    if critic_res.get("approve"):
                        quality_score = critic_res.get("quality_score_0_to_100", 80)
                    else:
                        revised = critic_res.get("revised_summary_json")
                        if revised:
                            final_summary_json = revised
                            quality_score = critic_res.get("quality_score_0_to_100", 0)
                
                # Save StorySummary
                stmt_exist = select(StorySummary).where(
                    StorySummary.story_id == story.id,
                    StorySummary.persona == persona_enum,
                    StorySummary.category == category
                )
                res = session.execute(stmt_exist)
                summary = res.scalars().first()
                
                if not summary:
                    summary = StorySummary(
                        id=str(uuid.uuid4()),
                        story_id=story.id,
                        persona=persona_enum,
                        category=category
                    )
                    session.add(summary)
                
                # Update fields
                summary.summary_short = final_summary_json.get("summary_short", "")
                summary.summary_bullets = final_summary_json.get("bullets", [])
                summary.why_it_matters = final_summary_json.get("why_it_matters", "")
                summary.key_entities = [final_summary_json.get("actionable_next_step", "")] if "actionable_next_step" in final_summary_json else final_summary_json.get("open_questions", [])
                summary.supporting_urls = final_summary_json.get("supporting_urls", [])
                summary.confidence = final_summary_json.get("confidence", "med")
                summary.insufficient_evidence = final_summary_json.get("insufficient_evidence", False)
                summary.quality_score = quality_score
                summary.model_name = MODEL_NAME
                summary.prompt_version = PROMPT_VERSION
                summary.last_reviewed_at = datetime.utcnow()
                
            session.commit()
            logger.info(f"  -> Saved summaries for {story.canonical_title}")
        
        logger.info("Agent job completed successfully")
        
    except Exception as e:
        logger.error(f"Agent job failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    job_run_agents_sync()
