from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app_mvc.config.config import settings
from app_mvc.db.database import db
from app_mvc.responses import register_exception_handlers
from app_mvc.routes import router as api_router
import uvicorn


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.open()
    try:
        yield
    finally:
        db.close()


app = FastAPI(
    title="Salón API",
    version="1.10.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)
register_exception_handlers(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(
        "app_mvc.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment != "production",
    )
