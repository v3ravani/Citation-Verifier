from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.paths import ensure_directories
from backend.app.core.logging_config import logger
from backend.app.nlp.model_loader import get_sentence_model
from backend.app.api.routes_upload import router as upload_router
from backend.app.api.routes_analysis import router as analysis_router
from backend.app.api.routes_results import router as results_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure local filesystem directories exist
    ensure_directories()
    logger.info("Initializing Citation Verifier storage directories...")
    
    # Pre-warm local SentenceTransformer embedding model once
    try:
        model = get_sentence_model()
        if model is not None:
            logger.info("SentenceTransformer model successfully loaded into memory.")
    except Exception as e:
        logger.warning(f"Embedding model pre-warm error (will retry on demand): {e}")

    yield

    # Shutdown
    logger.info("Shutting down Citation Verifier backend service.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Deterministic, transparent academic research integrity and citation verification platform.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router)
app.include_router(analysis_router)
app.include_router(results_router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@app.get("/")
async def root():
    return {
        "message": "Citation Verifier API is running.",
        "documentation": "/docs"
    }
