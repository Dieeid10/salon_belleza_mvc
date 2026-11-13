from fastapi import FastAPI
from app.routes import router as api_router
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from app.middleware.ip_whitelist import IPWhitelistMiddleware
from app.middleware.LoggingMiddleware import LoggingMiddleware
from app.config import ALLOWED_ORIGINS
from app.logger_config import setup_logger
from app.responses import register_exception_handlers
import uvicorn
import os
import sys

setup_logger()

app = FastAPI()
register_exception_handlers(app)

app.add_middleware(IPWhitelistMiddleware)
app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.add_middleware(SessionMiddleware, secret_key="your_secret_key_here")

app.title = "Elearning - Facebook ads"
app.version = "1.0.1"

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

cert_path = resource_path('certs/fb_ca_chain_bundle.crt')
os.environ['FB_CA_BUNDLE_PATH'] = cert_path

@app.get("/")
async def health_check():
    return "Contenedor conectado"

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)