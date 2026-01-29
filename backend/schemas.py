from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum

class PersonaEnum(str, Enum):
    builders = "builders"
    executors = "executors"
    explorers = "explorers"
    thought_leaders = "thought_leaders"

class SourceTypeEnum(str, Enum):
    paper = "paper"
    blog = "blog"
    news = "news"
    video = "video"
    newsletter = "newsletter"

class TrustLevelEnum(str, Enum):
    high = "high"
    medium = "medium"
    signal = "signal"

# --- Source ---
class SourceBase(BaseModel):
    name: str
    type: SourceTypeEnum
    url: str
    feed_url: Optional[str] = None
    trust_level: TrustLevelEnum

class Source(SourceBase):
    id: int
    class Config:
        from_attributes = True

# --- Item ---
class ItemBase(BaseModel):
    title: str
    url: str
    published_at: datetime
    
class Item(ItemBase):
    id: UUID
    source_id: int
    class Config:
        from_attributes = True

# --- Story Summary ---
class StorySummaryBase(BaseModel):
    persona: PersonaEnum
    category: Optional[str] = None
    summary_short: str
    summary_bullets: List[str]
    why_it_matters: Optional[str] = None
    key_entities: Optional[List[str]] = None
    confidence: Optional[str] = None

class StorySummary(StorySummaryBase):
    id: UUID
    class Config:
        from_attributes = True

# --- Story ---
class StoryBase(BaseModel):
    canonical_title: str
    score: float
    tags: List[str]

class Story(StoryBase):
    id: UUID
    created_at: datetime
    items: List[Item] = []
    summaries: List[StorySummary] = []
    is_saved: bool = False
    
    class Config:
        from_attributes = True

# --- User ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class User(UserBase):
    id: UUID
    default_persona: PersonaEnum
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
