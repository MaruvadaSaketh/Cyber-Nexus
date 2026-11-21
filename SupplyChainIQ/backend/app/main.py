
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.approval import router as approval_router
from app.api.decisions import router as decisions_router
from app.api.risk import router as risk_router

# Initialize FastAPI application
app = FastAPI(
    title="SupplyChainIQ API",
    description="AI-Powered Supply Chain Decision Intelligence",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(risk_router)
app.include_router(approval_router)
app.include_router(decisions_router)

@app.get("/")
def root() -> dict[str, Any]:
    return {
        "project": "SupplyChainIQ",
        "status": "running",
        "tracks": [
            "Track 01 - Supply Chain Intelligence",
            "Track 02 - AI Agents and Flagsmith"
        ]
    }

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}
