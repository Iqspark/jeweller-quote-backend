from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.logging_config import setup_logging
from app.routers import health, submissions
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logging.getLogger(__name__).info("Application starting up...")
    yield
    logging.getLogger(__name__).info("Application shutting down...")


app = FastAPI(
    title="JSON → MongoDB → Email API",
    description="Accepts any JSON, saves to MongoDB/CosmosDB, renders HTML email and sends via ACS or SMTP.",
    version="2.0.0",
    lifespan=lifespan
)

app.include_router(health.router)
app.include_router(submissions.router)

