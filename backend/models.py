from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Float, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from .database import Base

# --- Enums (defined in plan) ---
class Persona(str, enum.Enum):
    builders = "builders"
    executors = "executors"
    explorers = "explorers"
    thought_leaders = "thought_leaders"

class SourceKind(str, enum.Enum):
    rss = "rss"
    api = "api"
    social = "social"
    blog = "blog"

class StoryState(str, enum.Enum):
    new = "new"
    evolving = "evolving"
    stable = "stable"
    stale = "stale"

class EnrichmentStatus(str, enum.Enum):
    none = "none"
    queued = "queued"
    done = "done"
    failed = "failed"

# --- Models ---

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    url = Column(String)
    feed_url = Column(String, nullable=True)
    source_kind = Column(SQLEnum(SourceKind), default=SourceKind.rss)
    
    # New fields from V2 plan
    reputation_weight = Column(Float, default=1.0)
    topic_bias = Column(JSON, default=list) # ["technical", "business"...]
    fetch_interval_minutes = Column(Integer, default=60)
    is_enabled = Column(Boolean, default=True)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    etag = Column(String, nullable=True)
    last_modified = Column(String, nullable=True)
    fail_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    
    items = relationship("Item", back_populates="source")

class Item(Base):
    __tablename__ = "items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())) # UUID check
    source_id = Column(Integer, ForeignKey("sources.id"))
    
    title = Column(String)
    url = Column(String) # Original URL
    canonical_url = Column(String, nullable=True) # Stripped
    
    published_at = Column(DateTime(timezone=True))
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    
    raw_html = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    clean_text = Column(Text, nullable=True)
    content_length = Column(Integer, default=0)
    language = Column(String, default="en")
    image_url = Column(String, nullable=True)
    
    enrichment_status = Column(SQLEnum(EnrichmentStatus), default=EnrichmentStatus.none)
    enriched_at = Column(DateTime(timezone=True), nullable=True)
    enrichment_error = Column(Text, nullable=True)
    
    hash = Column(String, unique=True, index=True)
    metadata_json = Column(JSON, nullable=True)
    
    source = relationship("Source", back_populates="items")
    story_items = relationship("StoryItem", back_populates="item")

class Story(Base):
    __tablename__ = "stories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_title = Column(String)
    canonical_summary_seed = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    story_hash = Column(String, unique=True, index=True)
    cluster_version = Column(Integer, default=1)
    
    is_active = Column(Boolean, default=True)
    signal_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    
    story_state = Column(SQLEnum(StoryState), default=StoryState.new)
    
    classification_json = Column(JSON, nullable=True)
    classified_at = Column(DateTime(timezone=True), nullable=True)
    last_scored_at = Column(DateTime(timezone=True), nullable=True)
    
    # RAG: Vector Embedding (stored as JSON list of floats for SQLite/Postgres compatibility without pgvector extension initially)
    embedding = Column(JSON, nullable=True)
    generated_image_url = Column(String, nullable=True)
    
    # Data Universe: 2D Projection and Cluster ID for 90-Day Trends View
    universe_x = Column(Float, nullable=True)
    universe_y = Column(Float, nullable=True)
    universe_cluster = Column(Integer, nullable=True)
    
    story_items = relationship("StoryItem", back_populates="story")
    # Helper for Pydantic/Frontend
    items = relationship("Item", secondary="story_items", viewonly=True)

    summaries = relationship("StorySummary", back_populates="story")
    saves = relationship("UserSave", back_populates="story")

class StoryItem(Base):
    __tablename__ = "story_items"
    
    story_id = Column(String, ForeignKey("stories.id"), primary_key=True)
    item_id = Column(String, ForeignKey("items.id"), primary_key=True)
    
    is_primary = Column(Boolean, default=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    similarity_score = Column(Float, nullable=True)
    
    story = relationship("Story", back_populates="story_items")
    item = relationship("Item", back_populates="story_items")

class StorySummary(Base):
    __tablename__ = "story_summaries"
    # Unique constraint handled by DB if possible, logical here
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String, ForeignKey("stories.id"))
    
    persona = Column(SQLEnum(Persona))
    category = Column(String) # "Models", etc.
    
    summary_short = Column(String)
    summary_bullets = Column(JSON)
    why_it_matters = Column(Text, nullable=True)
    key_entities = Column(JSON, nullable=True) # or open_questions / actionable_next_step
    
    supporting_urls = Column(JSON, default=list) # URLs
    evidence_snippets = Column(JSON, default=list) # Optional
    
    quality_score = Column(Float, default=0.0)
    revision_count = Column(Integer, default=0)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    model_name = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    
    confidence = Column(String) # low/med/high kept for back-compat or display
    insufficient_evidence = Column(Boolean, default=False)
    
    story = relationship("Story", back_populates="summaries")

class DailyBrief(Base):
    __tablename__ = "daily_briefs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(String, index=True) # YYYY-MM-DD
    persona = Column(SQLEnum(Persona))
    
    items_json = Column(JSON) # Ordered list of story_ids + titles + 1-liners
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    model_name = Column(String, nullable=True)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    default_persona = Column(SQLEnum(Persona), default=Persona.builders)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    saves = relationship("UserSave", back_populates="user")

class UserSave(Base):
    __tablename__ = "user_saves"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    story_id = Column(String, ForeignKey("stories.id"), primary_key=True)
    saved_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="saves")
    story = relationship("Story", back_populates="saves")
