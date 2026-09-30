from fastapi import FastAPI

from app.database.db import Base, engine
from app.api.leads import router as leads_router
from app.scheduler.call_scheduler import scheduler
from app.voice.websocket import router as voice_router
from app.api.calls import router as calls_router

import app.database.models


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AI Voice Agent"
)


app.include_router(leads_router)
app.include_router(calls_router)
app.include_router(voice_router)

@app.on_event("startup")
def startup_event():
    if not scheduler.running:
        scheduler.start()


@app.get("/")
def home():
    return {
        "message": "AI Voice Agent is running"
    }