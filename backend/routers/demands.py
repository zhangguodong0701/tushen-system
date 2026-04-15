# routers/demands.py - 需求和报价 API
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import os

from models import get_db, User, Demand, Quote, Notification
from constants import DemandStatus, QuoteStatus, OrderStatus
from auth import get_current_user
from schemas import DemandCreate, DemandUpdate, QuoteCreate
from utils import demand_to_dict, is_jia_fang, is_yi_fang, paginate_query, generate_serial_number

router = APIRouter(prefix="/api", tags=["需求"])

UPLOAD_DIR = "./uploads"


def _save_file(file: UploadFile) -> str:
    """安全保存文件（复用 main.py 逻辑）"""
    import uuid
    from fastapi import HTTPException
    ext = os.path.splitext(file.filename)[1].lower()
    ALLOWED = {".pdf", ".dwg", ".dxf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar"}
    if ext not in ALLOWED:
        raise HTTPException(400, f"不支持的文件类型: {ext}")
    content = file.file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(400, "文件大小超过50MB")
    fname = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, fname), "wb") as f:
        f.write(content)
    return f"/uploads/{fname}"


def _notify(db, user_id, title, content_text):
    n = Notification(user_id=user_id, title=title, content=content_text)
    db.add(n)
    return n


# ========== Demand API ==========
@router.post("/demands")
def create_demand(data: DemandCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not is_jia_fang(current_user):
        raise HTTPException(403, "只有甲方（业主/建设单位/项目方）才能发布需求")
    demand = Demand(**data.model_dump(), owner_id=current_user.id, status=DemandStatus.draft.value)
    demand.serial_number = generate_serial_number("D")
    db.add(demand)
    db.commit()
    db.refresh(demand)
    return demand_to_dict(demand)


@router.put("/demands/{demand_id}")
def update_demand(demand_id: int, data: DemandUpdate,
                 current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    demand = db.query(Demand).filter(Demand.id == demand_id, Demand.owner_id == current_user.id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    if demand.status not in ("草稿", "待完善"):
        raise HTTPException(400, f"当前需求状态为「{demand.status}」，不允许编辑")
    for k, v in data.dict(exclude_none=True).items():
        setattr(demand, k, v)
    demand.updated_at = datetime.utcnow()
    db.commit()
    return demand_to_dict(demand)


@router.post("/demands/{demand_id}/publish")
def publish_demand(demand_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    demand = db.query(Demand).filter(Demand.id == demand_id, Demand.owner_id == current_user.id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    demand.status = DemandStatus.published.value
    db.commit()
    return {"message": "发布成功"}


@router.delete("/demands/{demand_id}")
def delete_demand(demand_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    demand = db.query(Demand).filter(Demand.id == demand_id, Demand.owner_id == current_user.id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    if demand.status in (DemandStatus.published.value, DemandStatus.in_progress.value, DemandStatus.completed.value):
        raise HTTPException(400, f"当前需求「{demand.status}」状态不允许删除")
    db.delete(demand)
    db.commit()
    return {"message": "删除成功"}


@router.post("/demands/{demand_id}/close")
def close_demand(demand_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    demand = db.query(Demand).filter(Demand.id == demand_id, Demand.owner_id == current_user.id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    if demand.status != DemandStatus.published.value:
        raise HTTPException(400, "只有已发布状态的需求才能关闭")
    winner = db.query(Quote).filter(Quote.demand_id == demand_id, Quote.status == QuoteStatus.accepted.value).first()
    if winner:
        raise HTTPException(400, "该需求已有中标方，无法关闭，请先取消中标")
    demand.status = DemandStatus.closed.value
    db.commit()
    _notify(db, demand.owner_id, "需求已关闭", f"您发布的需求「{demand.title}」已被关闭。")
    return {"message": "需求已关闭"}


@router.get("/demands")
def list_demands(status: Optional[str] = None, profession: Optional[str] = None,
                 min_budget: Optional[float] = None, max_budget: Optional[float] = None,
                 keyword: Optional[str] = None, payment_type: Optional[str] = None,
                 demand_type: Optional[str] = None,
                 page: int = 1, page_size: int = 12,
                 db: Session = Depends(get_db)):
    q = db.query(Demand)
    if status:
        q = q.filter(Demand.status == status)
    if profession:
        q = q.filter(Demand.profession == profession)
    if payment_type:
        q = q.filter(Demand.payment_type == payment_type)
    if demand_type:
        q = q.filter(Demand.demand_type == demand_type)
    if min_budget is not None:
        q = q.filter(Demand.budget >= min_budget)
    if max_budget is not None:
        q = q.filter(Demand.budget <= max_budget)
    if keyword:
        q = q.filter(
            (Demand.title.contains(keyword)) | (Demand.description.contains(keyword))
        )
    q = q.order_by(Demand.created_at.desc())
    result = paginate_query(q, page, page_size)
    result["items"] = [demand_to_dict(d) for d in result["items"]]
    return result


@router.get("/demands/my")
def my_demands(status: Optional[str] = None,
               page: int = 1, page_size: int = 12,
               current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Demand).filter(Demand.owner_id == current_user.id)
    if status:
        q = q.filter(Demand.status == status)
    q = q.order_by(Demand.created_at.desc())
    result = paginate_query(q, page, page_size)
    result["items"] = [demand_to_dict(d) for d in result["items"]]
    return result


@router.get("/demands/{demand_id}")
def get_demand(demand_id: int, db: Session = Depends(get_db)):
    demand = db.query(Demand).filter(Demand.id == demand_id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    return demand_to_dict(demand)


@router.post("/demands/{demand_id}/upload-file")
def upload_demand_file(demand_id: int, file: UploadFile = File(...),
                       current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    demand = db.query(Demand).filter(Demand.id == demand_id, Demand.owner_id == current_user.id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    url = _save_file(file)
    demand.file_url = url
    db.commit()
    return {"url": url}


# ========== Quote API ==========
@router.post("/demands/{demand_id}/quotes")
def create_quote(demand_id: int, data: QuoteCreate,
                 current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not is_yi_fang(current_user):
        raise HTTPException(403, "只有乙方才能提交报价")
    demand = db.query(Demand).filter(Demand.id == demand_id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    if demand.status != DemandStatus.published.value:
        raise HTTPException(400, f"当前需求「{demand.status}」状态不允许报价")
    if demand.owner_id == current_user.id:
        raise HTTPException(400, "不能给自己的需求报价")
    existing = db.query(Quote).filter(Quote.demand_id == demand_id, Quote.bidder_id == current_user.id).first()
    if existing:
        raise HTTPException(400, "已提交过报价")
    quote = Quote(demand_id=demand_id, bidder_id=current_user.id, **data.model_dump())
    quote.serial_number = generate_serial_number("Q")
    db.add(quote)
    db.commit()
    db.refresh(quote)
    _notify(db, demand.owner_id, "📬 您有新报价",
            f"用户「{current_user.real_name}」对您的需求「{demand.title}」提交了报价：¥{data.price:,.0f}元。")
    return {"id": quote.id, "serial_number": quote.serial_number, "price": quote.price, "remark": quote.remark, "status": quote.status}


@router.put("/quotes/{quote_id}")
def update_quote(quote_id: int, data: QuoteCreate,
                 current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quote = db.query(Quote).filter(Quote.id == quote_id, Quote.bidder_id == current_user.id).first()
    if not quote:
        raise HTTPException(404, "报价不存在")
    if quote.status != QuoteStatus.pending.value:
        raise HTTPException(400, f"当前报价状态「{quote.status}」不允许编辑")
    quote.price = data.price
    quote.remark = data.remark
    db.commit()
    return {"message": "更新成功"}


@router.delete("/quotes/{quote_id}")
def cancel_quote(quote_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quote = db.query(Quote).filter(Quote.id == quote_id, Quote.bidder_id == current_user.id).first()
    if not quote:
        raise HTTPException(404, "报价不存在")
    if quote.status != QuoteStatus.pending.value:
        raise HTTPException(400, f"当前报价状态「{quote.status}」不允许取消")
    db.delete(quote)
    db.commit()
    return {"message": "取消成功"}


@router.get("/demands/{demand_id}/quotes")
def list_quotes(demand_id: int, db: Session = Depends(get_db)):
    quotes = db.query(Quote).filter(Quote.demand_id == demand_id).all()
    return [{"id": q.id, "serial_number": getattr(q, 'serial_number', '') or '',
             "price": q.price, "remark": q.remark, "status": q.status,
             "seller_id": q.bidder_id,
             "seller_name": q.bidder.phone if q.bidder else "",
             "seller_real_name": q.bidder.real_name if q.bidder else "",
             "created_at": str(q.created_at)} for q in quotes]


@router.get("/quotes/my")
def my_quotes(status: Optional[str] = None,
              page: int = 1, page_size: int = 12,
              current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Quote).filter(Quote.bidder_id == current_user.id)
    if status:
        q = q.filter(Quote.status == status)
    q = q.order_by(Quote.created_at.desc())
    result = paginate_query(q, page, page_size)
    result["items"] = [{"id": q.id, "serial_number": getattr(q, 'serial_number', '') or '',
                        "price": q.price, "remark": q.remark, "status": q.status,
                        "demand_id": q.demand_id, "demand_title": q.demand.title if q.demand else "",
                        "created_at": str(q.created_at)} for q in result["items"]]
    return result


@router.post("/demands/{demand_id}/select-winner/{quote_id}")
def select_winner(demand_id: int, quote_id: int,
                  current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models import Order, PaymentPhase
    import json

    demand = db.query(Demand).filter(Demand.id == demand_id, Demand.owner_id == current_user.id).first()
    if not demand:
        raise HTTPException(404, "需求不存在或无权限")
    if demand.status not in (DemandStatus.published.value, DemandStatus.in_progress.value):
        raise HTTPException(400, f"该需求状态为「{demand.status}」，不允许选择中标方")
    if demand.status == DemandStatus.in_progress.value:
        raise HTTPException(400, "该需求已有中标方")

    quote = db.query(Quote).filter(Quote.id == quote_id, Quote.demand_id == demand_id).first()
    if not quote:
        raise HTTPException(404, "报价不存在")

    quote.status = QuoteStatus.accepted.value
    other_quotes = db.query(Quote).filter(Quote.demand_id == demand_id, Quote.id != quote_id).all()
    for other in other_quotes:
        other.status = QuoteStatus.rejected.value
    demand.chosen_quote_id = quote_id
    demand.status = DemandStatus.in_progress.value

    order = Order(
        buyer_id=current_user.id,
        demand_id=demand_id,
        seller_id=quote.bidder_id,
        amount=quote.price,
        payment_type=demand.payment_type,
        status=OrderStatus.pending_payment.value
    )
    order.serial_number = generate_serial_number("O")
    db.add(order)
    db.commit()
    db.refresh(order)

    # 分阶段付款：自动创建订单阶段
    if demand.payment_type == "分阶段" and demand.payment_phases:
        try:
            phases = json.loads(demand.payment_phases)
            for i, phase in enumerate(phases):
                phase_amount = round(quote.price * phase.get("ratio", 0) / 100, 2)
                payment_phase = PaymentPhase(
                    order_id=order.id,
                    name=phase.get("name", f"阶段{i+1}"),
                    ratio=phase.get("ratio", 0),
                    amount=phase_amount,
                    status=OrderStatus.pending_review.value,
                    phase_order=i + 1
                )
                db.add(payment_phase)
            db.commit()
        except json.JSONDecodeError:
            pass

    _notify(db, quote.bidder_id, "恭喜中标！",
            f"您对需求「{demand.title}」的报价已被选中，中标金额：{quote.price}元。请等待甲方付款。")
    _notify(db, current_user.id, "中标已确定",
            f"已选定服务方，订单已创建，金额：{quote.price}元。请尽快完成支付。")
    db.commit()
    return {"message": "已选定中标方并创建订单", "winner_id": quote.bidder_id, "order_id": order.id}
