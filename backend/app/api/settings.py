import json
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import verify_auth_token
from app.models.setting import Setting

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("")
def get_settings(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_auth_token)
):
    """Retrieve all saved settings."""
    records = db.query(Setting).all()
    res = {}
    for r in records:
        try:
            res[r.key] = json.loads(r.value)
        except Exception:
            res[r.key] = r.value
    return res

@router.post("")
def save_settings(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_auth_token)
):
    """Save or update user settings dictionary."""
    for k, v in payload.items():
        existing = db.query(Setting).filter(Setting.key == k).first()
        serialized = json.dumps(v)
        if existing:
            existing.value = serialized
        else:
            db.add(Setting(key=k, value=serialized))
    db.commit()
    return {"status": "success", "updated_keys": list(payload.keys())}
