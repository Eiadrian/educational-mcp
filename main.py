"""FastAPI 主应用，装配各功能路由。"""

from __future__ import annotations

from fastapi import FastAPI

from routers import cognitive, tracking, emotion, planning


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Teaching Agent API",
        version="0.2.0",
        description="大模型 + 小模型协同的教学智能体示例。",
    )
    app.include_router(cognitive.router, prefix="/diagnose", tags=["cognitive"])
    app.include_router(tracking.router, prefix="/track", tags=["knowledge-tracking"])
    app.include_router(emotion.router, prefix="/emotion", tags=["affective"])
    app.include_router(planning.router, prefix="/plan", tags=["planning"])
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
