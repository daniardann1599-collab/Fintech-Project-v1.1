import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.entities import EventStatus, OutboxEvent

router = APIRouter(tags=["events"])


@router.websocket("/ws/events")
async def websocket_events(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    if not token:
        await websocket.close(code=4401)
        return

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", "0"))
    except (ValueError, TypeError):
        await websocket.close(code=4401)
        return

    await websocket.accept()

    try:
        while True:
            with SessionLocal() as db:
                pending_count = db.scalar(
                    select(func.count(OutboxEvent.id)).where(OutboxEvent.status == EventStatus.PENDING)
                )
                latest_events = list(
                    db.scalars(select(OutboxEvent).order_by(OutboxEvent.id.desc()).limit(5))
                )

            await websocket.send_json(
                {
                    "type": "outbox_snapshot",
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "pending_events": int(pending_count or 0),
                    "latest_events": [
                        {
                            "id": event.id,
                            "aggregate_type": event.aggregate_type,
                            "aggregate_id": event.aggregate_id,
                            "event_type": event.event_type,
                            "status": event.status,
                            "created_at": event.created_at.isoformat(),
                        }
                        for event in latest_events
                    ],
                }
            )
            await asyncio.sleep(settings.websocket_poll_seconds)
    except WebSocketDisconnect:
        return
