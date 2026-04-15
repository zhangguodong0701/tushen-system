# routers/feedback.py - 投诉反馈 API
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db, User, Feedback, Notification
from constants import FeedbackStatus
from auth import get_current_user
from schemas import FeedbackCreate
from utils import paginate_query

router = APIRouter(prefix="/api", tags=["反馈"])


def _notify(db, user_id, title, content_text):
    n = Notification(user_id=user_id, title=title, content=content_text)
    db.add(n)
    return n


@router.post("/feedback")
def create_feedback(data: FeedbackCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 内容安全校验：禁止测试关键字
    test_patterns = ["RANDOM=", "test", "Test", "TEST", "mock", "Mock", "MOCK", "测试"]
    content_lower = data.content.lower()
    for pattern in test_patterns:
        if pattern.lower() in content_lower:
            raise HTTPException(400, "反馈内容包含无效关键字，请填写真实反馈内容")
    if len(data.content.strip()) < 5:
        raise HTTPException(400, "反馈内容至少5个字符")
    
    fb = Feedback(user_id=current_user.id, content=data.content)
    db.add(fb)
    db.commit()
    return {"id": fb.id, "message": "反馈已提交，我们会尽快处理"}


@router.get("/feedback")
def list_my_feedback(status: Optional[str] = None,
                     page: int = 1, page_size: int = 20,
                     current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 审核员/管理员能看到所有反馈，普通用户只能看自己的
    is_admin_or_reviewer = current_user.is_admin == 1 or current_user.is_reviewer == 1
    if is_admin_or_reviewer:
        q = db.query(Feedback)
    else:
        q = db.query(Feedback).filter(Feedback.user_id == current_user.id)
    if status:
        q = q.filter(Feedback.status == status)
    q = q.order_by(Feedback.created_at.asc())  # 最早的反馈排前面
    page_result = paginate_query(q, page, page_size)
    items = []
    for f in page_result["items"]:
        user = db.query(User).filter(User.id == f.user_id).first()
        items.append({
            "id": f.id, "user_id": f.user_id,
            "user_name": user.real_name if user else (user.phone if user else ""),
            "content": f.content, "status": f.status,
            "reply": f.reply,
            "created_at": str(f.created_at),
            "updated_at": str(f.updated_at)
        })
    return {"total": page_result["total"], "page": page_result["page"],
            "page_size": page_result["page_size"], "items": items}


# ========== 管理员反馈管理 ==========
# 统一单数路径：/api/admin/feedback（原 /api/admin/feedbacks，修复单复数不一致）
@router.get("/admin/feedback")
def admin_list_feedback(status: Optional[str] = None,
                         page: int = 1, page_size: int = 20,
                         db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_reviewer and not current_user.is_admin:
        raise HTTPException(403, "需要审核员或管理员权限")
    q = db.query(Feedback)
    if status:
        q = q.filter(Feedback.status == status)
    q = q.order_by(Feedback.created_at.asc())  # 最早的反馈排前面
    page_result = paginate_query(q, page, page_size)
    items = []
    for f in page_result["items"]:
        user = db.query(User).filter(User.id == f.user_id).first()
        items.append({
            "id": f.id, "user_id": f.user_id,
            "user_name": user.real_name if user else "",
            "content": f.content, "status": f.status,
            "reply": f.reply,
            "created_at": str(f.created_at),
            "updated_at": str(f.updated_at)
        })
    return {"total": page_result["total"], "page": page_result["page"],
            "page_size": page_result["page_size"], "items": items}


@router.post("/admin/feedback/{feedback_id}/reply")
async def admin_reply_feedback(feedback_id: int, req: Request,
                               db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_reviewer and not current_user.is_admin:
        raise HTTPException(403, "需要审核员或管理员权限")
    body = await req.json()
    reply = body.get("reply", "").strip()
    if not reply:
        raise HTTPException(400, "回复内容不能为空")
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(404, "反馈不存在")
    fb.reply = reply
    fb.status = FeedbackStatus.resolved.value
    _notify(db, fb.user_id, "投诉反馈回复", f"您提交的投诉反馈已有处理结果：{reply}")
    db.commit()
    return {"message": "回复已发送"}
