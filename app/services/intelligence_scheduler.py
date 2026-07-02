from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.intelligence_center import crawl_active_sources, seed_intelligence_sources


_scheduler_started = False
_scheduler_lock = threading.Lock()
_scheduler_state = {
    "enabled": settings.intelligence_auto_crawl_enabled,
    "running": False,
    "last_run_at": None,
    "next_run_at": None,
    "last_message": "尚未启动自动抓取",
}


def start_intelligence_scheduler() -> None:
    global _scheduler_started
    if not settings.intelligence_auto_crawl_enabled:
        _scheduler_state["last_message"] = "自动抓取未启用"
        return

    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True

    worker = threading.Thread(target=_scheduler_loop, name="intelligence-auto-crawler", daemon=True)
    worker.start()


def get_intelligence_schedule_status() -> dict:
    return dict(_scheduler_state)


def _scheduler_loop() -> None:
    interval_seconds = max(1, settings.intelligence_auto_crawl_interval_hours) * 60 * 60
    next_run = datetime.utcnow() + timedelta(seconds=interval_seconds)
    _scheduler_state.update(
        {
            "enabled": True,
            "running": True,
            "next_run_at": next_run,
            "last_message": "自动抓取已启动，将按每日频率运行",
        }
    )

    while True:
        time.sleep(interval_seconds)
        _run_scheduled_crawl()
        next_run = datetime.utcnow() + timedelta(seconds=interval_seconds)
        _scheduler_state["next_run_at"] = next_run


def _run_scheduled_crawl() -> None:
    db = SessionLocal()
    try:
        seed_intelligence_sources(
            db,
            workspace_id=settings.intelligence_auto_crawl_workspace_id,
            reset_existing=False,
        )
        result = crawl_active_sources(
            db,
            workspace_id=settings.intelligence_auto_crawl_workspace_id,
            max_sources=settings.intelligence_auto_crawl_max_sources,
        )
        _scheduler_state["last_run_at"] = datetime.utcnow()
        _scheduler_state["last_message"] = result["message"]
    except Exception as exc:
        _scheduler_state["last_run_at"] = datetime.utcnow()
        _scheduler_state["last_message"] = f"自动抓取失败：{exc}"
    finally:
        db.close()
