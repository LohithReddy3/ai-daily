from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class PersonaEnum(str, Enum):
    builders = "builders"
    executors = "executors"
    explorers = "explorers"
    thought_leaders = "thought_leaders"

class SourceKindEnum(str, Enum):
    rss = "rss"
    api = "api"
    social = "social"
    blog = "blog"

# --- Source ---
class SourceBase(BaseModel):
    name: str
    url: Optional[str] = None
    feed_url: Optional[str] = None
    source_kind: SourceKindEnum
    reputation_weight: float = 1.0

class Source(SourceBase):
    id: int
    class Config:
        from_attributes = True

# --- Item ---
class ItemBase(BaseModel):
    title: str
    url: str
    published_at: datetime
    content_length: int = 0
    clean_text: Optional[str] = None # For detail view maybe?
    image_url: Optional[str] = None
    
class Item(ItemBase):
    id: str # UUID string
    source_id: int
    source: Optional[Source] = None
    
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
    supporting_urls: List[str] = []
    insufficient_evidence: bool = False

    @field_validator('summary_bullets', 'key_entities', mode='before')
    @classmethod
    def clean_lists(cls, v):
        if not v:
            return []
        if not isinstance(v, list):
            return []
        
        new_list = []
        for item in v:
            if item is None:
                continue
            if isinstance(item, dict):
                # Convert {"key": "value"} to "**key**: value"
                for k, val in item.items():
                    if val is not None:
                        new_list.append(f"**{k}**: {val}")
            elif isinstance(item, str):
                new_list.append(item)
            else:
                new_list.append(str(item))
        return new_list

class StorySummary(StorySummaryBase):
    id: str
    class Config:
        from_attributes = True

# --- Story ---
class StoryBase(BaseModel):
    canonical_title: str
    signal_score: float
    confidence_score: float = 0.0
    story_state: str
    
class RelatedStory(BaseModel):
    id: str
    canonical_title: str
    created_at: datetime
    similarity_score: float

class Story(StoryBase):
    id: str
    created_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    generated_image_url: Optional[str] = None
    
    items: List[Item] = [] 
    summaries: List[StorySummary] = []
    related_stories: List[RelatedStory] = []
    
    is_saved: bool = False
    
    is_saved: bool = False
    
    class Config:
        from_attributes = True

# --- Daily Brief ---
class DailyBriefItem(BaseModel):
    story_id: str
    title: str
    summary: str
    importance: str
    signal_score: float
    bullets: List[str]
    urls: List[str]
    why_it_matters: Optional[str] = None

class DailyBrief(BaseModel):
    id: str
    date: str
    persona: PersonaEnum
    items_json: List[DailyBriefItem]
    generated_at: datetime
    
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
    id: str
    default_persona: PersonaEnum
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
