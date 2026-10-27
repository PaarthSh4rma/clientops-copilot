import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.demo import DemoAnswerCache, DemoChatLimiter
from app.core.logging import configure_logging
from app.db.session import build_session_factory
from app.integrations.embeddings import PineconeInferenceEmbeddings, SentenceTransformerEmbeddings
from app.integrations.file_storage import LocalFileStorage
from app.integrations.llm import OpenRouterLLM, UnconfiguredLLM
from app.integrations.vector_store import PineconeVectorStore, UnconfiguredVectorStore
from app.services.demo_bootstrap import bootstrap_demo_metadata

logger = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None, *, embeddings=None, vector_store=None, llm=None, storage=None
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    settings.validate_production_integrations()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings.upload_directory.mkdir(parents=True, exist_ok=True)
        yield

    app = FastAPI(title="ClientOps Copilot API", version="0.1.6", lifespan=lifespan)
    app.state.settings = settings
    app.state.demo_chat_limiter = DemoChatLimiter(settings.demo_chat_hourly_limit)
    app.state.demo_upload_limiter = DemoChatLimiter(10)
    app.state.demo_answer_cache = DemoAnswerCache()
    app.state.session_factory = build_session_factory(settings)
    if settings.serverless_demo_bootstrap:
        if not settings.demo_mode:
            raise RuntimeError("Serverless metadata bootstrap requires read-only demo mode")
        samples = Path(__file__).resolve().parents[1] / "demo_documents"
        bootstrap_demo_metadata(app.state.session_factory, samples)
    app.state.storage = storage or LocalFileStorage(settings.upload_directory)
    app.state.embeddings = embeddings or (
        PineconeInferenceEmbeddings(settings.pinecone_api_key, settings.pinecone_embedding_model)
        if settings.embedding_provider == "pinecone_inference" and settings.pinecone_api_key
        else SentenceTransformerEmbeddings(settings.embedding_model)
    )
    app.state.vector_store = vector_store or (
        PineconeVectorStore(settings.pinecone_api_key, settings.pinecone_index_name)
        if settings.pinecone_api_key and settings.pinecone_index_name
        else UnconfiguredVectorStore()
    )
    app.state.llm = llm or (
        OpenRouterLLM(settings.openrouter_api_key, settings.openrouter_model, settings.provider_timeout_seconds)
        if settings.openrouter_api_key
        else UnconfiguredLLM()
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-Demo-Session"],
    )
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(documents_router, prefix=settings.api_prefix)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error(
            "Unhandled API error on %s %s",
            request.method,
            request.url.path,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred"})

    if settings.frontend_directory and settings.frontend_directory.is_dir():
        app.mount("/", StaticFiles(directory=settings.frontend_directory, html=True), name="frontend")

    return app


app = create_app()
