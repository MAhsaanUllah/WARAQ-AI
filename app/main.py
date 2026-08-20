"""FastAPI application factory for Waraq AI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes.rag import router as rag_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.qdrant import close_client, ping_qdrant


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ping Qdrant on startup (non-fatal); close the client on shutdown."""
    settings = get_settings()
    logger = get_logger("app.lifespan")
    configure_logging()

    qdrant_ok = await ping_qdrant()
    logger.info(
        "startup_complete",
        version=__version__,
        qdrant="connected" if qdrant_ok else "unavailable",
        provider=settings.llm_provider,
    )
    yield
    await close_client()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    """Build the FastAPI app with CORS, the RAG router, and /health."""
    settings = get_settings()

    app = FastAPI(
        title="Waraq AI",
        description="Hybrid retrieval + cross-encoder reranking + deterministic page-level citations.",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    app.include_router(rag_router)

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        """Liveness + readiness: report Qdrant connectivity without failing."""
        qdrant_ok = await ping_qdrant()
        return {
            "status": "ok",
            "version": __version__,
            "qdrant": "connected" if qdrant_ok else "unavailable",
        }

    return app


app = create_app()
