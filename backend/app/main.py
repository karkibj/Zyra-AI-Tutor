"""
FastAPI Application - Zyra AI Tutor Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware  # ADD THIS!
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Zyra AI Tutor Backend...")
    await init_db()
    print("✅ Database initialized")
    
    # Initialize vector store on startup
    from app.services.vector_store_service import get_vector_store
    vector_store = get_vector_store()
    stats = vector_store.get_stats()
    print(f"📊 Vector store loaded: {stats['total_vectors']} vectors")
    
    yield
    # Shutdown
    print("👋 Shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Zyra AI Tutor API",
        description="AI-Powered Math Tutor with Authentication & LangGraph Multi-Agent System",
        version="2.1.0",
        lifespan=lifespan
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # SESSION MIDDLEWARE (NEW - Required for Google OAuth!)
    app.add_middleware(
       SessionMiddleware,
       secret_key=settings.SECRET_KEY,
       max_age=3600,  # Session expires after 1 hour
       same_site="lax",  # Changed from default
       https_only=False,  # Set to False for localhost development
    )

    # Import routers
    from app.api.v1 import health
    from app.api.v1.auth import router as auth_router
    from app.api.v1.tutor import router as tutor_router
    from app.api.v1.admin import router as admin_router

    # Register routes
    app.include_router(health.router, prefix=settings.API_PREFIX, tags=["Health"])
    app.include_router(auth_router, prefix=settings.API_PREFIX)
    app.include_router(tutor_router, prefix=settings.API_PREFIX)
    app.include_router(admin_router, prefix=settings.API_PREFIX)

    @app.get("/")
    def root():
        return {
            "message": "Zyra AI Tutor API",
            "version": "2.1.0",
            "status": "operational",
            "features": [
                "🔐 User Authentication (JWT + OAuth)",
                "🤖 LangGraph Multi-Agent Workflow",
                "📚 Intelligent Content Management",
                "🔍 Vector-based RAG System",
                "💬 Real-time Tutoring"
            ],
            "endpoints": {
                "health": f"{settings.API_PREFIX}/health",
                "auth": f"{settings.API_PREFIX}/auth/login",
                "signup": f"{settings.API_PREFIX}/auth/signup",
                "tutor": f"{settings.API_PREFIX}/tutor/ask",
                "admin": f"{settings.API_PREFIX}/admin/dashboard/stats",
                "docs": "/docs"
            }
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )