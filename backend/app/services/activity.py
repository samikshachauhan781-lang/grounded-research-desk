"""Persisted activity timeline events."""

import json
import uuid

from sqlalchemy.orm import Session

from backend.app.database.models import ActivityEvent, utc_now_iso


def record_activity(db: Session, event_type: str, payload: dict) -> None:
    event = ActivityEvent(
        id=str(uuid.uuid4()),
        event_type=event_type,
        payload_json=json.dumps(payload, separators=(",", ":")),
        created_at=utc_now_iso(),
    )
    db.add(event)
    db.commit()
