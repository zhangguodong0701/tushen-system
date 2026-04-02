# routers/notifications.py - 通知 API
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db, User, Notification
from auth import get_current_user
from utils import paginate_query, extract_notification_type

router = APIRouter(prefix="/api", tags=["通知"])


@router.get("/notifications")
def list_notifications(is_read: Optional[str] = None,
                      page: int = 1, page_size: int = 20,
                      current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Notification).filter(Notification.user_id == current_user.id)
    if is_read == "1":
        q = q.filter(Notification.is_read == 1)
    elif is_read == "0":
        q = q.filter(Notification.is_read == 0)
    q = q.order_by(Notification.created_at.desc())
    result = paginate_query(q, page, page_size)
    result["items"] = [{"id": n.id, "title": n.title, "content": n.content,
                        "message": n.content,
                        "type": extract_notification_type(n.title),
                        "is_read": n.is_read, "created_at": str(n.created_at)} for n in result["items"]]
    return result


@router.post("/notifications/{notif_id}/read")
def read_notification(notif_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(
        Notification.id == notif_id, Notification.user_id == current_user.id
    ).first()
    if notif:
        notif.is_read = 1
        db.commit()
    return {"message": "已读"}


@router.post("/notifications/mark-all-read")
def mark_all_notifications_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == 0
    ).update({"is_read": 1})
    db.commit()
    return {"message": "已全部标记为已读", "success": True}
