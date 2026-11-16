
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import voice, interviews

app = FastAPI(
    title="VoxHire AI",
    description="AI-powered voice interview platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://your-project.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(voice.router)
app.include_router(interviews.router)


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
