from fastapi import FastAPI
from .config import settings


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
    )

    return app


app = create_application()