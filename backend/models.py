from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Float, Enum as SQLEnum, JSON, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from .database import Base

class Persona(str, enum.Enum):
    builders = "builders"
    executors = "executors"
    explorers = "explorers"
    thought_leaders = "thought_leaders"

class SourceType(str, enum.Enum):
    paper = "paper"
    blog = "blog"
    news = "news"
    video = "video"
    newsletter = "newsletter"

class TrustLevel(str, enum.Enum):
    high = "high"
    medium = "medium"
    signal = "signal"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    default_persona = Column(SQLEnum(Persona), default=Persona.builders)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    saves = relationship("UserSave", back_populates="user")

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    type = Column(SQLEnum(SourceType))
    url = Column(String)
    feed_url = Column(String)
    trust_level = Column(SQLEnum(TrustLevel), default=TrustLevel.medium)
    fetch_method = Column(String, default="rss") # rss, api
    
    items = relationship("Item", back_populates="source")

class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(Integer, ForeignKey("sources.id"))
    title = Column(String)
    url = Column(String)
    published_at = Column(DateTime(timezone=True))
    raw_text = Column(Text, nullable=True) # Full text or abstract
    content_type = Column(String, nullable=True)
    hash = Column(String, unique=True, index=True) # For deduplication
    metadata_json = Column(JSON, nullable=True)
    
    source = relationship("Source", back_populates="items")
    # An item can belong to a story (many-to-many potentially, but usually many-to-one for clustering. 
    # Simplified: We'll store the link in 'Story' json for now or create a StoryItem link table.
    # For MVP, let's assume we copy item data into context or link them. 
    # Let's add a FK for simple clustering.
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"), nullable=True)
    story = relationship("Story", back_populates="items")

class Story(Base):
    __tablename__ = "stories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_title = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tags = Column(JSON, default=list) # List of strings
    score = Column(Float, default=0.0)
    
    items = relationship("Item", back_populates="story")
    summaries = relationship("StorySummary", back_populates="story")
    saves = relationship("UserSave", back_populates="story")

class StorySummary(Base):
    __tablename__ = "story_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"))
    persona = Column(SQLEnum(Persona))
    category = Column(String, nullable=True) # e.g., "Models", "Markets"
    summary_short = Column(String)
    summary_bullets = Column(JSON) # List of strings
    why_it_matters = Column(Text)
    key_entities = Column(JSON, nullable=True)
    confidence = Column(String) # low, med, high
    
    story = relationship("Story", back_populates="summaries")

class UserSave(Base):
    __tablename__ = "user_saves"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"), primary_key=True)
    saved_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="saves")
    story = relationship("Story", back_populates="saves")

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    followed_topics = Column(JSON, default=list)
    preferred_source_ids = Column(JSON, default=list)
    
    user = relationship("User", back_populates="preferences")
