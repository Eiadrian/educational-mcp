"""将 FastAPI 应用一键注册为 MCP 服务的入口脚本。"""
#this  is a mcp
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

import threading

import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from mcp.server.fastmcp import FastMCP

from app import app as fastapi_app


class FastApiMCP:
    """Registers FastAPI POST routes as MCP tools and exposes stdio runner.

    中文：遍历 FastAPI 的 POST 路由，将其注册为 MCP 工具供上层大模型调用。
    """

    def __init__(
        self,
        app: FastAPI,
        *,
        name: str,
        description: Optional[str] = None,
        mount_path: str = "/mcp",
    ) -> None:
        self.app = app
        self.client = TestClient(app)
        self.mcp = FastMCP(name, instructions=description)
        self.mount_path = mount_path
        self._registered = False
        self._tools: List[str] = []

    @property
    def tools(self) -> List[str]:
        return list(self._tools)

    def setup_server(self) -> None:
        if self._registered:
            return
        for route in self._iter_post_routes():
            self._register_route(route)
        self._registered = True

    def mount(self, target_app: Optional[FastAPI] = None, *, path: Optional[str] = None) -> None:
        """可选：把 MCP 的 streaming HTTP 入口挂载到原 FastAPI 应用。"""
        self.setup_server()
        mount_path = path or self.mount_path
        target = target_app or self.app
        target.mount(mount_path, self.mcp.streamable_http_app())

    def run_stdio(self) -> None:
        """通过 stdio 启动 MCP 服务器。"""
        self.setup_server()
        self.mcp.run("stdio")

    def _iter_post_routes(self) -> Iterable[APIRoute]:
        for route in self.app.routes:
            if isinstance(route, APIRoute) and "POST" in route.methods:
                yield route

    def _register_route(self, route: APIRoute) -> None:
        path = route.path
        tool_name = route.name or path.lstrip("/").replace("/", "_")
        description = route.summary or route.description or f"调用 {path}"

        @self.mcp.tool(name=tool_name, description=description)
        async def call_endpoint(payload: Dict[str, Any], path: str = path) -> Dict[str, Any]:
            response = self.client.post(path, json=payload or {})
            response.raise_for_status()
            return response.json()

        self._tools.append(tool_name)
        _ = call_endpoint


mcp = FastApiMCP(
    fastapi_app,
    name="edu-fastapi-mcp",
    description="将 FastAPI 教育小模型接口导出为 MCP 服务",
)
mcp.setup_server()
# 可选挂载，便于同时走 HTTP 查看 /mcp/stream
mcp.mount(fastapi_app)

def main() -> None:
    """在子线程启动 HTTP，主线程跑 MCP stdio。"""

    def _run_http() -> None:
        uvicorn.run("app:app", host="127.0.0.1", port=8000)

    threading.Thread(target=_run_http, daemon=True).start()
    mcp.run_stdio()


if __name__ == "__main__":
    main()
