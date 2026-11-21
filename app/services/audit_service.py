import json

from app.extensions import db
from app.models.audit import AuditLog


def log_action(user_id, action: str, entity: str, entity_id: int = None, before=None, after=None) -> AuditLog:
    row = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        before_json=json.dumps(before) if before is not None else None,
        after_json=json.dumps(after) if after is not None else None,
    )
    db.session.add(row)
    db.session.commit()
    return row
