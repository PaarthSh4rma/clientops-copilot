"""Read-only recruiter deployment: real retrieval and AI, no durable local writes."""

import os

# These deployment invariants keep the public demo within free service tiers.
os.environ.update(
    APP_ENVIRONMENT="production",
    API_PREFIX="/api",
    DEMO_MODE="true",
    SERVERLESS_DEMO_BOOTSTRAP="true",
    DATABASE_URL="sqlite:////tmp/clientops-recruiter-demo.db",
    UPLOAD_DIRECTORY="/tmp/clientops-recruiter-uploads",
    FRONTEND_DIRECTORY="",
    EMBEDDING_PROVIDER="pinecone_inference",
    PINECONE_EMBEDDING_MODEL="llama-text-embed-v2",
    PINECONE_INDEX_NAME="clientops-recruiter-demo",
    OPENROUTER_MODEL="openrouter/free",
    DEMO_CHAT_HOURLY_LIMIT="15",
    PROVIDER_TIMEOUT_SECONDS="45",
    ALLOWED_CORS_ORIGINS="",
)

from app.main import app  # noqa: E402, F401
