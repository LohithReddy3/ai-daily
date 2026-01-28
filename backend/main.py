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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
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
