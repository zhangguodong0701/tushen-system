# routers/admin.py - 管理员 API
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session
from typing import Optional

from sqlalchemy import func
from models import get_db, User, Demand, Order, Dispute, Notification, FundRecord, OperationLog, Feedback
from constants import UserStatus, DemandStatus, OrderStatus, DisputeStatus
from auth import get_current_user
from utils import user_to_dict, demand_to_dict, order_to_dict, paginate_query

router = APIRouter(prefix="/api/admin", tags=["管理"])


def get_current_reviewer(current_user: User = Depends(get_current_user)):
    if not current_user.is_reviewer and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要审核员或管理员权限")
    return current_user


def get_current_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


def _notify(db, user_id, title, content_text):
    n = Notification(user_id=user_id, title=title, content=content_text)
    db.add(n)
    return n


def _fund_record(db, order_id, user_id, ftype, amount, direction, description):
    rec = FundRecord(order_id=order_id, user_id=user_id, type=ftype, amount=amount, direction=direction, description=description)
    db.add(rec)
    return rec


def _log_action(db, user_id, action, target_type, target_id, detail=""):
    log = OperationLog(user_id=user_id, action=action, target_type=target_type, target_id=target_id, detail=detail)
    db.add(log)
    return log


# ========== 用户管理 ==========
@router.get("/users")
def admin_list_users(status: Optional[str] = None, keyword: Optional[str] = None,
                    user_type: Optional[str] = None,
                    page: int = 1, page_size: int = 20,
                    db: Session = Depends(get_db), reviewer=Depends(get_current_reviewer)):
    q = db.query(User)
    if status:
        q = q.filter(User.status == status)
    if user_type:
        q = q.filter(User.user_type == user_type)
    if keyword:
        q = q.filter(
            (User.real_name.contains(keyword)) |
            (User.phone.contains(keyword)) |
            (User.email.contains(keyword)) |
            (User.company_name.contains(keyword))
        )
    q = q.order_by(User.created_at.asc())  # 最早的待审核用户排前面
    result = paginate_query(q, page, page_size)
    result["items"] = [user_to_dict(u) for u in result["items"]]
    return result


@router.post("/users/{user_id}/approve")
def approve_user(user_id: int, db: Session = Depends(get_db), reviewer=Depends(get_current_reviewer)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.status = UserStatus.approved.value
    db.commit()
    notif = Notification(user_id=user_id, title="审核通过", content="您的账号已审核通过，可以正常使用平台。")
    db.add(notif)
    db.commit()
    return {"message": "已审核通过"}


@router.post("/users/{user_id}/reject")
async def reject_user(user_id: int, req: Request,
                      db: Session = Depends(get_db), reviewer=Depends(get_current_reviewer)):
    body = await req.json()
    reason = body.get("reason", "")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.status = UserStatus.rejected.value
    db.commit()
    reason_text = f"（原因：{reason}）" if reason else "请完善资质后重新提交。"
    notif = Notification(user_id=user_id, title="审核驳回", content=f"您的账号审核未通过，{reason_text}")
    db.add(notif)
    db.commit()
    return {"message": "已驳回"}


# ========== 需求管理 ==========
@router.get("/demands")
def admin_list_demands(status: Optional[str] = None, profession: Optional[str] = None,
                       keyword: Optional[str] = None,
                       page: int = 1, page_size: int = 20,
                       db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    q = db.query(Demand)
    if status:
        q = q.filter(Demand.status == status)
    if profession:
        q = q.filter(Demand.profession == profession)
    if keyword:
        q = q.filter(
            (Demand.title.contains(keyword)) | (Demand.description.contains(keyword))
        )
    q = q.order_by(Demand.created_at.desc())
    result = paginate_query(q, page, page_size)
    result["items"] = [demand_to_dict(d) for d in result["items"]]
    return result


@router.post("/demands/{demand_id}/close")
def admin_close_demand(demand_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    demand = db.query(Demand).filter(Demand.id == demand_id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    demand.status = DemandStatus.closed.value
    _log_action(db, demand.owner_id, "关闭需求", "demand", demand_id, f"管理员关闭需求：{demand.title}")
    _notify(db, demand.owner_id, "需求关闭通知", f"您的需求「{demand.title}」已被管理员关闭。")
    db.commit()
    return {"message": "需求已关闭"}


# ========== 订单管理 ==========
@router.get("/orders")
def admin_list_orders(status: Optional[str] = None,
                     page: int = 1, page_size: int = 20,
                     db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    q = q.order_by(Order.created_at.desc())
    result = paginate_query(q, page, page_size)
    result["items"] = [order_to_dict(o) for o in result["items"]]
    return result


# ========== 纠纷管理 ==========
@router.get("/disputes")
def admin_list_disputes(status: Optional[str] = None,
                        page: int = 1, page_size: int = 20,
                        db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    q = db.query(Dispute)
    if status:
        q = q.filter(Dispute.status == status)
    q = q.order_by(Dispute.created_at.desc())
    result = paginate_query(q, page, page_size)
    result["items"] = [{"id": d.id, "order_id": d.order_id, "description": d.description,
                        "evidence_url": d.evidence_url, "evidence_files": d.evidence_files,
                        "status": d.status, "result": d.result,
                        "initiator_id": d.initiator_id,
                        "initiator_name": d.initiator.real_name if d.initiator else "",
                        "created_at": str(d.created_at)} for d in result["items"]]
    return result


@router.post("/disputes/{dispute_id}/resolve")
def resolve_dispute(dispute_id: int, result: str = Form(...), action: str = Form("refund"),
                    db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(404, "纠纷不存在")
    dispute.result = result
    dispute.status = DisputeStatus.resolved.value
    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    if order:
        if action == "refund":
            order.status = OrderStatus.refunded.value
            order.escrow_status = "已释放"
            _fund_record(db, order.id, order.buyer_id, "退款", order.amount, "in", f"纠纷裁决退款：{result}")
        else:
            order.status = OrderStatus.completed.value
            order.escrow_status = "已释放"
            _fund_record(db, order.id, order.seller_id, "放款", order.amount, "in", f"纠纷裁决放款：{result}")
        _log_action(db, dispute.initiator_id, "纠纷裁决", "dispute", dispute_id, result)
        _notify(db, order.buyer_id, "纠纷处理结果通知", f"您的纠纷已有处理结果：{result}")
        _notify(db, order.seller_id, "纠纷处理结果通知", f"您的纠纷已有处理结果：{result}")
    db.commit()
    return {"message": "纠纷已处理"}


# ========== 统计 ==========
@router.get("/stats")
def admin_stats(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return {
        "total_users": db.query(User).count(),
        "pending_users": db.query(User).filter(User.status == UserStatus.pending.value).count(),
        "total_demands": db.query(Demand).count(),
        "published_demands": db.query(Demand).filter(Demand.status == DemandStatus.published.value).count(),
        "total_orders": db.query(Order).count(),
        "active_orders": db.query(Order).filter(Order.status == OrderStatus.in_progress.value).count(),
        "total_disputes": db.query(Dispute).count(),
        "open_disputes": db.query(Dispute).filter(Dispute.status == DisputeStatus.open.value).count(),
        # 修复F1: 用数据库聚合替代内存遍历，避免N+1
        "total_amount": db.query(func.sum(Order.amount)).filter(
            Order.status == OrderStatus.completed.value
        ).scalar() or 0,
    }


# ========== 黑名单 ==========
@router.get("/blacklist")
def admin_blacklist(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    users = db.query(User).filter(User.is_blacklisted == 1).all()
    return [user_to_dict(u) for u in users]


@router.post("/users/{user_id}/blacklist")
def blacklist_user(user_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    if user.is_admin:
        raise HTTPException(400, "无法将管理员加入黑名单")
    if user.is_reviewer:
        raise HTTPException(400, "无法将审核员加入黑名单")
    user.is_blacklisted = 1
    _log_action(db, user_id, "加入黑名单", "user", user_id, "管理员操作，被加黑名单")
    _notify(db, user_id, "账号黑名单通知", "您的账号已被平台加入黑名单，如有疑问请联系客服。")
    db.commit()
    return {"message": "已加入黑名单"}


@router.post("/users/{user_id}/unblacklist")
def unblacklist_user(user_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.is_blacklisted = 0
    _notify(db, user_id, "黑名单解除通知", "您的账号已解除黑名单限制，可以正常使用平台。")
    db.commit()
    return {"message": "已解除黑名单"}


# ========== 内容审核 ==========
@router.get("/content-review")
def admin_content_review(db: Session = Depends(get_db), reviewer=Depends(get_current_reviewer)):
    demands = db.query(Demand).filter(Demand.status == DemandStatus.published.value).all()
    from models import Drawing
    drawings = db.query(Drawing).all()
    return {
        "demands": [demand_to_dict(d) for d in demands[:20]],
        "drawings": [{"id": d.id, "filename": d.filename, "file_url": d.file_url, "order_id": d.order_id,
                      "uploader_name": d.uploader.real_name if d.uploader else "",
                      "version": d.version, "created_at": str(d.created_at)} for d in drawings[:50]]
    }


# ========== 资金记录 & 操作日志 ==========
@router.get("/fund-records")
def admin_fund_records(page: int = 1, page_size: int = 50,
                       db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    result = paginate_query(db.query(FundRecord).order_by(FundRecord.created_at.desc()), page, page_size)
    result["items"] = [{"id": r.id, "order_id": r.order_id, "user_id": r.user_id,
                        "user_name": r.user.real_name if r.user else "",
                        "type": r.type, "amount": r.amount, "direction": r.direction,
                        "description": r.description, "created_at": str(r.created_at)} for r in result["items"]]
    return result


@router.get("/operation-logs")
def admin_operation_logs(page: int = 1, page_size: int = 50,
                         db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    result = paginate_query(db.query(OperationLog).order_by(OperationLog.created_at.desc()), page, page_size)
    result["items"] = [{"id": l.id, "user_id": l.user_id,
                        "user_name": l.user.real_name if l.user else "",
                        "action": l.action, "target_type": l.target_type,
                        "target_id": l.target_id, "detail": l.detail,
                        "created_at": str(l.created_at)} for l in result["items"]]
    return result
