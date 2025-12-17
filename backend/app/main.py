from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.api.v1 import health, tutor

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="Zyra AI Tutor - SEE Grade 10 Mathematics Tutor API",
        version="1.0.0"
    )

    # CORS middleware - Allow frontend to communicate
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(health.router, prefix=settings.API_PREFIX, tags=["health"])
    app.include_router(tutor.router, prefix=settings.API_PREFIX, tags=["tutor"])

    @app.on_event("startup")
    def startup_event():
        logger.info(f"{settings.APP_NAME} started in {settings.ENV} mode")
        logger.info("Registered routes:")
        for route in app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                logger.info(f"  {route.methods} {route.path}")

    @app.get("/")
    def root():
        return {
            "message": "Welcome to Zyra AI Tutor API",
            "version": "1.0.0",
            "docs": "/docs"
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