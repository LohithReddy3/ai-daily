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

# Allow all for now to permit Vercel preview deployments if needed, or stick to strict list
# origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Temporarily allowing all to prevent CORS issues on first deploy
    allow_credentials=True,
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
