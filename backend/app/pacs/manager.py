from __future__ import annotations

import asyncio
from collections import defaultdict

from fastapi import WebSocket


class BankWebSocketManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, bank_code: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[bank_code].add(websocket)

    def disconnect(self, bank_code: str, websocket: WebSocket) -> None:
        self._connections[bank_code].discard(websocket)
        if not self._connections[bank_code]:
            self._connections.pop(bank_code, None)

    async def broadcast(self, bank_code: str, payload: dict) -> None:
        connections = list(self._connections.get(bank_code, set()))
        if not connections:
            return
        for websocket in connections:
            await websocket.send_json(payload)

    def broadcast_sync(self, bank_code: str, payload: dict) -> None:
        if not self._loop:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(bank_code, payload), self._loop)


bank_ws_manager = BankWebSocketManager()
