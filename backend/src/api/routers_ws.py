import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError

from src.core.security import decode_token
from src.db.session import db_session
from src.models.user import User

router = APIRouter(tags=["websocket"])


# PUBLIC_INTERFACE
@router.get("/ws/usage", summary="WebSocket usage help", tags=["websocket"])
def websocket_usage():
    """
    Usage notes for WebSocket notifications.

    Connect:
    - URL: ws(s)://<host>/ws/notifications?token=<JWT>
    - Protocol: WebSocket

    On connect:
    - Server validates token and sends a welcome message.
    - Demo notifications may be sent periodically or triggered by actions.

    Close:
    - Client should close cleanly when done.
    """
    return {
        "path": "/ws/notifications",
        "query": "token=<JWT access token>",
        "note": "This is a demo notification stream. Use token from /auth/login.",
    }


# PUBLIC_INTERFACE
@router.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket, token: Optional[str] = Query(default=None, alias="token")):
    """
    WebSocket endpoint for real-time notifications.

    Parameters:
    - token: JWT access token as query string (required)

    Behavior:
    - Validates the token and associates the connection with the user.
    - Sends a welcome event and awaits ping messages.
    - Echoes back minimal demo notifications on 'ping'.
    """
    # Accept early to allow clean close messages
    await websocket.accept()
    if not token:
        await websocket.send_json({"type": "error", "message": "token required"})
        await websocket.close()
        return
    # Validate token and fetch user
    try:
        payload = decode_token(token)
    except JWTError:
        await websocket.send_json({"type": "error", "message": "invalid token"})
        await websocket.close()
        return
    sub = payload.get("sub")
    user: Optional[User] = None
    with db_session() as db:  # type: Session
        if str(sub).isdigit():
            user = db.query(User).filter(User.id == int(sub)).first()
        if not user:
            user = db.query(User).filter(User.email == str(sub)).first()
    if not user or not user.is_active:
        await websocket.send_json({"type": "error", "message": "user not found"})
        await websocket.close()
        return

    await websocket.send_json({"type": "welcome", "user_id": user.id})

    try:
        while True:
            data = await websocket.receive_text()
            # simple echo/trigger behavior
            if data.strip().lower() == "ping":
                await websocket.send_json({"type": "notification", "message": "pong"})
            else:
                # basic broadcast of receipt
                await websocket.send_text(json.dumps({"type": "ack", "received": data}))
    except WebSocketDisconnect:
        # client disconnected; simply exit
        return
