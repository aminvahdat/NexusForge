#!/usr/bin/env python3
"""
NexusForge Integrated Local Services Runner.
Orchestrates:
- Redis TCP Server (port 6379 via fakeredis)
- Backend API (port 8000 via FastAPI & Uvicorn)
- Autonomous Worker (background loop)
- Reverse Proxy & Frontend Static Web Server (port 3000 via FastAPI & Uvicorn)
"""

import sys
import os
import asyncio
import threading
import time
from pathlib import Path

# Paths
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
DIST_DIR = WORKSPACE_ROOT / "dist"
BIN_DIR = WORKSPACE_ROOT / "bin"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(WORKSPACE_ROOT))
os.environ["PATH"] = str(BIN_DIR) + os.pathsep + os.environ.get("PATH", "")

# Ensure environment variables are loaded
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///nexusforge.db")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")
os.environ.setdefault("REDIS_HOST", "127.0.0.1")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("JWT_SECRET_KEY", "nexusforge-dev-secret-key-must-be-32-chars-long")
os.environ.setdefault("JWT_SECRET", "nexusforge-dev-secret-key-must-be-32-chars-long")
os.environ.setdefault("SECRET_KEY", "nexusforge-dev-secret-key-must-be-32-chars-long")
os.environ.setdefault("API_ENV", "development")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("MAX_CONCURRENT_WORKERS", "2")

import fakeredis
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx

from app.db import init_database, close_database
from app.main import create_app
from worker import WorkerProcess


def start_redis_server():
    """Start FakeRedis TCP Server on 127.0.0.1:6379."""
    server = fakeredis.TcpFakeServer(("127.0.0.1", 6379))
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print("[+] FakeRedis TCP Server listening on 127.0.0.1:6379")
    return server


def create_proxy_app():
    """Create reverse proxy & static file server for port 3000."""
    proxy = FastAPI(title="NexusForge Reverse Proxy")

    # Static assets
    assets_dir = DIST_DIR / "assets"
    if assets_dir.exists():
        proxy.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Reusable HTTP client for proxying
    client = httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=30.0)

    @proxy.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    async def proxy_api(path: str, request: Request):
        query = str(request.url.query)
        target_url = f"/api/{path}" + (f"?{query}" if query else "")
        body = await request.body()

        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("content-length", None)

        resp = await client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers=headers,
        )

        resp_headers = {
            k: v for k, v in resp.headers.items()
            if k.lower() not in ("content-encoding", "transfer-encoding", "content-length", "connection")
        }
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=resp_headers,
            media_type=resp.headers.get("content-type"),
        )

    @proxy.api_route("/health", methods=["GET"])
    async def proxy_health(request: Request):
        resp = await client.get("/health")
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            media_type="application/json"
        )

    from starlette.websockets import WebSocket as StarletteWebSocket, WebSocketDisconnect
    import websockets

    @proxy.websocket("/execution/ws/{client_id}")
    async def proxy_ws_execution(client_ws: StarletteWebSocket, client_id: str):
        await client_ws.accept()
        backend_ws_url = f"ws://127.0.0.1:8000/execution/ws/{client_id}"
        try:
            async with websockets.connect(backend_ws_url) as server_ws:
                async def c2s():
                    while True:
                        data = await client_ws.receive_text()
                        await server_ws.send(data)

                async def s2c():
                    while True:
                        data = await server_ws.recv()
                        await client_ws.send_text(data)

                done, pending = await asyncio.wait(
                    [asyncio.create_task(c2s()), asyncio.create_task(s2c())],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
        except (WebSocketDisconnect, Exception):
            pass
        finally:
            try:
                await client_ws.close()
            except Exception:
                pass

    @proxy.websocket("/ws/{client_id}")
    async def proxy_ws(client_ws: StarletteWebSocket, client_id: str):
        await proxy_ws_execution(client_ws, client_id)

    @proxy.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = DIST_DIR / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST_DIR / "index.html")

    return proxy


async def main():
    print("==================================================")
    print("   Starting NexusForge Local Full-Stack Services  ")
    print("==================================================")

    # 1. Start Redis
    redis_server = start_redis_server()
    await asyncio.sleep(0.5)

    # 2. Initialize Database & Seeds
    print("[*] Initializing Database and Admin Seed...")
    await init_database()
    print("[+] Database and Seeds initialized successfully")

    # 3. Create Apps
    backend_app = create_app()
    proxy_app = create_proxy_app()

    # 4. Initialize Worker
    worker = WorkerProcess(worker_id="nexusforge-worker-01", hostname="worker-01")
    worker.running = True

    # 5. Setup Servers
    backend_config = uvicorn.Config(
        backend_app,
        host="127.0.0.1",
        port=8000,
        log_level="warning",
        access_log=False
    )
    backend_server = uvicorn.Server(backend_config)

    proxy_config = uvicorn.Config(
        proxy_app,
        host="0.0.0.0",
        port=3000,
        log_level="warning",
        access_log=False
    )
    proxy_server = uvicorn.Server(proxy_config)

    print("[+] Backend API running on http://127.0.0.1:8000")
    print("[+] Reverse Proxy & Frontend running on http://localhost:3000")
    print("[+] Autonomous Worker running in background")
    print("==================================================")

    try:
        await asyncio.gather(
            backend_server.serve(),
            proxy_server.serve(),
            worker.run_loop(),
        )
    except asyncio.CancelledError:
        pass
    finally:
        worker.running = False
        await close_database()
        redis_server.shutdown()
        print("\n[*] Services stopped cleanly.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
