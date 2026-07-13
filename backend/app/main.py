import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.session import build_session_factory
from app.integrations.embeddings import SentenceTransformerEmbeddings
from app.integrations.file_storage import LocalFileStorage
from app.integrations.llm import OpenRouterLLM, UnconfiguredLLM
from app.integrations.vector_store import PineconeVectorStore, UnconfiguredVectorStore

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

    app = FastAPI(title="ClientOps Copilot API", version="0.1.5", lifespan=lifespan)
    app.state.settings = settings
    app.state.session_factory = build_session_factory(settings)
    app.state.storage = storage or LocalFileStorage(settings.upload_directory)
    app.state.embeddings = embeddings or SentenceTransformerEmbeddings(settings.embedding_model)
    app.state.vector_store = vector_store or (
        PineconeVectorStore(settings.pinecone_api_key, settings.pinecone_index_name)
        if settings.pinecone_api_key and settings.pinecone_index_name
        else UnconfiguredVectorStore()
    )
    app.state.llm = llm or (
        OpenRouterLLM(settings.openrouter_api_key, settings.openrouter_model)
        if settings.openrouter_api_key
        else UnconfiguredLLM()
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.include_router(health_router)
    app.include_router(documents_router)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error(
            "Unhandled API error on %s %s",
            request.method,
            request.url.path,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred"})

    return app


app = create_app()
