
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.resume import router as resume_router
from app.routes import voice, interviews
from app.routes import voice_ws, dashboard
from app.core.database import connect_database, close_database
from app.routes import auth
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_database()

    try:
        yield
    finally:
        await close_database()

app = FastAPI(
    title="VoxHire AI",
    description="AI-powered voice interview platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://voxhire-beta.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(voice.router)
app.include_router(interviews.router)
app.include_router(resume_router)
app.include_router(
    voice_ws.router,
    prefix="/api/voice",
    tags=["Real-time Voice"]
)
app.include_router(
    dashboard.router,
    prefix="/api/dashboard",
    tags=["Career Dashboard"]
)
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to VoxHire AI"
    }


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "application": "VoxHire AI"
    }
