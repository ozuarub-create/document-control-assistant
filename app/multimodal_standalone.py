"""Standalone FastAPI application for the Week 23 prototype."""

from fastapi import FastAPI

from app.multimodal_api import router


app = FastAPI(
    title="Week 23 Multimodal Document Intelligence",
    description=(
        "Standalone PDF page intelligence service that compares text-layer extraction "
        "with vision-capable page analysis and returns structured evidence."
    ),
    version="1.0.0",
)
app.include_router(router)


@app.get("/")
def home() -> dict[str, str]:
    return {
        "message": "Week 23 Multimodal Document Intelligence is running.",
        "docs": "/docs",
        "capabilities": "/multimodal/capabilities",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "week": "23"}
