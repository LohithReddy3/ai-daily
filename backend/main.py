from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import stories, admin, brief, trends
from .scheduler import start_scheduler
import os

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

app = FastAPI(title="AI Daily API V2", lifespan=lifespan)

# CORS - Allow all origins since frontend (Vercel) and backend (EC2) are on different domains
origins = ["*"]

frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(stories.router)
app.include_router(admin.router)
app.include_router(brief.router)
app.include_router(trends.router)

@app.get("/")
def read_root():
    return {"message": "AI Daily Intelligence API V2 - Operational"}

@app.get("/health")
def health_check():
    return {"status": "ok", "pipeline_active": True}
