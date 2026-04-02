# routers/disputes.py - 纠纷处理 API
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import json, os, uuid

from models import get_db, User, Order, Dispute, Notification
from auth import get_current_user
from schemas import DisputeCreate
from utils import paginate_query

router = APIRouter(prefix="/api", tags=["纠纷"])

UPLOAD_DIR = "./uploads"


def _save_file(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1].lower()
    ALLOWED = {".pdf", ".jpg", ".jpeg", ".png", ".zip", ".rar"}
    if ext not in ALLOWED:
        raise HTTPException(400, f"不支持的文件类型: {ext}")
    content = file.file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(400, "文件大小超过20MB")
    fname = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, fname), "wb") as f:
        f.write(content)
    return f"/uploads/{fname}"


@router.post("/disputes")
def create_dispute(data: DisputeCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(404, "关联订单不存在")
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        raise HTTPException(403, "只有订单参与方才能发起纠纷")
    if order.status not in ["进行中", "待验收"]:
        raise HTTPException(400, f"当前订单状态（{order.status}）不允许发起纠纷")
    existing = db.query(Dispute).filter(
        Dispute.order_id == data.order_id,
        Dispute.status == "处理中"
    ).first()
    if existing:
        raise HTTPException(400, "该订单已有处理中的纠纷")
    dispute = Dispute(initiator_id=current_user.id, **data.model_dump())
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    return {"id": dispute.id, "status": dispute.status}


@router.post("/disputes/{dispute_id}/upload-evidence")
def upload_evidence(dispute_id: int, file: UploadFile = File(...),
                    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(404, "纠纷不存在")
    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    if not order:
        raise HTTPException(404, "关联订单不存在")
    is_initiator = dispute.initiator_id == current_user.id
    is_participant = order.buyer_id == current_user.id or order.seller_id == current_user.id
    if not is_initiator and not is_participant:
        raise HTTPException(403, "无权为此纠纷上传证据")
    url = _save_file(file)
    dispute.evidence_url = url
    db.commit()
    return {"url": url}


@router.get("/disputes")
def list_disputes(status: Optional[str] = None,
                  page: int = 1, page_size: int = 12,
                  current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 审核员/管理员能看到所有纠纷，普通用户只能看自己发起的
    is_admin_or_reviewer = current_user.is_admin == 1 or current_user.is_reviewer == 1
    if is_admin_or_reviewer:
        q = db.query(Dispute)
    else:
        q = db.query(Dispute).filter(Dispute.initiator_id == current_user.id)
    if status:
        q = q.filter(Dispute.status == status)
    q = q.order_by(Dispute.created_at.desc())
    result = paginate_query(q, page, page_size)
    items = []
    for d in result["items"]:
        order_title = None
        if d.order_id:
            order = db.query(Order).filter(Order.id == d.order_id).first()
            if order and order.demand:
                order_title = order.demand.title
        items.append({
            "id": d.id, "order_id": d.order_id,
            "order_title": order_title or f"订单 #{d.order_id}",
            "dispute_type": "服务纠纷",
            "description": d.description,
            "evidence_url": d.evidence_url,
            "evidence_files": d.evidence_files,
            "status": d.status, "result": d.result,
            "created_at": str(d.created_at)
        })
    result["items"] = items
    return result


@router.post("/disputes/{dispute_id}/evidence-multiple")
def upload_multiple_evidence(dispute_id: int, file: UploadFile = File(...),
                             current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(404, "纠纷不存在")
    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    if not order:
        raise HTTPException(404, "关联订单不存在")
    is_initiator = dispute.initiator_id == current_user.id
    is_participant = order.buyer_id == current_user.id or order.seller_id == current_user.id
    if not is_initiator and not is_participant:
        raise HTTPException(403, "无权为此纠纷上传证据")
    url = _save_file(file)
    files = []
    if dispute.evidence_files:
        try:
            files = json.loads(dispute.evidence_files)
        except:
            pass
    files.append({"filename": file.filename, "url": url})
    dispute.evidence_files = json.dumps(files, ensure_ascii=False)
    db.commit()
    return {"url": url, "files": files}


@router.get("/disputes/{dispute_id}/evidence-files")
def get_evidence_files(dispute_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(404, "纠纷不存在")
    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    is_initiator = dispute.initiator_id == current_user.id
    is_participant = order and (order.buyer_id == current_user.id or order.seller_id == current_user.id)
    is_admin_or_reviewer = current_user.is_admin == 1 or current_user.is_reviewer == 1
    if not is_initiator and not is_participant and not is_admin_or_reviewer:
        raise HTTPException(403, "无权查看此纠纷的证据")
    files = []
    if dispute.evidence_files:
        try:
            files = json.loads(dispute.evidence_files)
        except:
            pass
    return files
