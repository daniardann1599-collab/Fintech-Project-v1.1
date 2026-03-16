from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.pacs.manager import bank_ws_manager

router = APIRouter(tags=["pacs.008"])


@router.websocket("/ws/banks/{bank_code}")
async def websocket_banks(
    websocket: WebSocket,
    bank_code: str,
    token: str | None = Query(default=None),
) -> None:
    if not token:
        await websocket.close(code=4401)
        return

    try:
        decode_access_token(token)
    except (ValueError, TypeError):
        await websocket.close(code=4401)
        return

    await bank_ws_manager.connect(bank_code, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        bank_ws_manager.disconnect(bank_code, websocket)
        return
