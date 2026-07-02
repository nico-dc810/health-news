from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

import app.models  # noqa: F401
from app.api.routes import api_router
from app.core.config import settings
from app.db.session import Base, engine
from app.services.intelligence_scheduler import start_intelligence_scheduler


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # CORS —— 允许 GitHub Pages 和本地调试跨域调用
    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_prefix)
    app.mount("/demo", StaticFiles(directory="static", html=True), name="demo")

    @app.get("/", include_in_schema=False)
    def index() -> RedirectResponse:
        return RedirectResponse(url="/demo")

    return app


app = create_app()


def _run_lightweight_migrations() -> None:
    """为已有表补充新增列（SQLite/PostgreSQL 通用）"""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if "subscriber_accesses" in insp.get_table_names():
        existing = {col["name"] for col in insp.get_columns("subscriber_accesses")}
        with engine.begin() as conn:
            if "expires_at" not in existing:
                conn.execute(text("ALTER TABLE subscriber_accesses ADD COLUMN expires_at DATETIME"))
            if "remark" not in existing:
                conn.execute(text("ALTER TABLE subscriber_accesses ADD COLUMN remark VARCHAR(500)"))


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    _run_lightweight_migrations()
    start_intelligence_scheduler()
