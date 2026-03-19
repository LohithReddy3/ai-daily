"""
Synchronous database configuration for agent service.
This avoids async/greenlet conflicts when using the Gemini API.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

# Use synchronous SQLite engine for agent job
SYNC_DATABASE_URL = "sqlite:///./ai_daily.db"

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    echo=False
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
    class_=Session
)

def get_sync_db():
    """Get synchronous database session for agent job"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
