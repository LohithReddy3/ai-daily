from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import stories, auth
from .scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Start scheduler
    scheduler = start_scheduler()
    
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(title="AI Daily API", lifespan=lifespan)

import os

# CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

# Dynamic CORS configuration
# If we have a specific FRONTEND_URL, we use strict origins and allow credentials.
# If not (e.g. initial deploy), we allow all origins ("*") but MUST disable credentials to be valid.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if frontend_url else ["*"],
    allow_credentials=True if frontend_url else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stories.router)
app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "AI Daily Intelligence API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
