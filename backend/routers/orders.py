# routers/orders.py - 订单和分阶段付款 API
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from models import get_db, User, Order, PaymentPhase, Notification, FundRecord, OperationLog, Drawing, Quote
from constants import OrderStatus, QuoteStatus, PhaseStatus
from auth import get_current_user
from schemas import OrderCreate, PhaseCreate
from utils import order_to_dict, paginate_query, generate_serial_number

router = APIRouter(prefix="/api", tags=["订单"])


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


# ========== Order API ==========
@router.post("/orders")
def create_order(data: OrderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models import Demand, Quote
    demand = db.query(Demand).filter(Demand.id == data.demand_id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    winning_quote = db.query(Quote).filter(
        Quote.demand_id == data.demand_id,
        Quote.status == QuoteStatus.accepted.value,
        Quote.bidder_id == current_user.id
    ).first()
    if not winning_quote:
        raise HTTPException(403, "只有中标方才能创建订单")
    if data.amount <= 0:
        raise HTTPException(400, "订单金额必须大于0")
    existing_order = db.query(Order).filter(Order.demand_id == data.demand_id).first()
    if existing_order:
        raise HTTPException(400, "该需求已创建过订单")
    order = Order(
        buyer_id=demand.owner_id,
        demand_id=data.demand_id,
        seller_id=current_user.id,
        amount=data.amount,
        payment_type=data.payment_type
    )
    order.serial_number = generate_serial_number("O")
    db.add(order)
    db.commit()
    db.refresh(order)
    _notify(db, demand.owner_id, "新订单通知", f"您有一个新订单，需求：{demand.title}，金额：{data.amount}元。")
    _notify(db, current_user.id, "订单创建成功", f"订单已创建，需求：{demand.title}，金额：{data.amount}元。")
    db.commit()
    return order_to_dict(order)


@router.get("/orders")
def list_orders(status: Optional[str] = None,
                page: int = 1, page_size: int = 12,
                current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Order).filter(
        (Order.buyer_id == current_user.id) | (Order.seller_id == current_user.id)
    )
    if status:
        q = q.filter(Order.status == status)
    q = q.order_by(Order.created_at.desc())
    result = paginate_query(q, page, page_size)
    result["items"] = [order_to_dict(o) for o in result["items"]]
    return result


@router.get("/orders/{order_id}")
def get_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    is_participant = (order.buyer_id == current_user.id or order.seller_id == current_user.id)
    is_admin_or_reviewer = (current_user.is_admin == 1 or current_user.is_reviewer == 1)
    if not is_participant and not is_admin_or_reviewer:
        raise HTTPException(403, "无权查看此订单详情")
    return order_to_dict(order)


@router.post("/orders/{order_id}/pay")
def pay_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.buyer_id == current_user.id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status != OrderStatus.pending_payment.value:
        raise HTTPException(400, "订单状态不允许支付")
    order.status = OrderStatus.in_progress.value
    order.escrow_status = "已托管"
    _fund_record(db, order.id, current_user.id, "托管", order.amount, "out", f"订单资金托管，金额：{order.amount}元")
    _notify(db, order.seller_id, "资金托管通知", f"买方已支付{order.amount}元，资金已由平台托管，等待服务完成。")
    db.commit()
    return {"message": "支付成功（资金已托管）"}


@router.post("/orders/{order_id}/accept")
def accept_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.buyer_id == current_user.id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status != OrderStatus.in_progress.value:
        raise HTTPException(400, "订单状态不允许验收")

    if order.payment_type == "一次性":
        order.status = OrderStatus.completed.value
        order.escrow_status = "已释放"
        _fund_record(db, order.id, order.seller_id, "放款", order.amount, "in", f"订单验收完成，一次性放款{order.amount}元")
        _notify(db, order.seller_id, "验收通过，资金已放款",
                f"买方已确认验收，订单完成，金额{order.amount}元已放款至您的账户。")
        _log_action(db, current_user.id, "确认验收", "order", order_id, "买方确认验收，订单完成（一次性付款）")
        db.commit()
        return {"message": "验收确认，平台已放款"}
    else:
        phases = db.query(PaymentPhase).filter(PaymentPhase.order_id == order_id).all()
        if not phases:
            raise HTTPException(400, "分阶段订单尚未配置付款阶段")
        unverified = [p for p in phases if p.status != PhaseStatus.completed.value]
        if unverified:
            raise HTTPException(400, f"还有{len(unverified)}个阶段未验收")
        order.status = OrderStatus.completed.value
        order.escrow_status = "已释放"
        _notify(db, order.seller_id, "订单完成", "所有付款阶段已验收，订单全部完成。")
        _log_action(db, current_user.id, "确认验收", "order", order_id, "买方确认全部阶段验收，订单完成（分阶段付款）")
        db.commit()
        return {"message": "所有阶段验收完成，订单已完结"}


@router.post("/orders/{order_id}/refund")
def refund_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(403, "只有管理员才能执行退款操作")
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status in (OrderStatus.completed.value, OrderStatus.refunded.value):
        raise HTTPException(400, f"当前订单「{order.status}」状态不允许退款")
    order.status = OrderStatus.refunded.value
    order.escrow_status = "已释放"
    _fund_record(db, order.id, order.buyer_id, "退款", order.amount, "in", f"管理员操作退款：{order.amount}元")
    _notify(db, order.buyer_id, "退款通知", f"您的订单已退款，金额{order.amount}元已退还。")
    _notify(db, order.seller_id, "退款通知", f"订单已退款，资金{order.amount}元已退给买方。")
    db.commit()
    return {"message": "退款成功"}


# ========== 分阶段付款 ==========
@router.post("/orders/{order_id}/phases")
def create_phase(order_id: int, data: PhaseCreate,
                 current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.buyer_id != current_user.id:
        raise HTTPException(403, "只有订单甲方才能添加付款阶段")
    existing_phases = db.query(PaymentPhase).filter(PaymentPhase.order_id == order_id).count()
    phase = PaymentPhase(
        order_id=order_id,
        name=data.name,
        amount=data.amount,
        ratio=data.ratio,
        phase_order=existing_phases + 1
    )
    db.add(phase)
    db.commit()
    return {"id": phase.id, "name": phase.name, "ratio": phase.ratio, "phase_order": phase.phase_order,
            "amount": phase.amount, "status": phase.status}


@router.get("/orders/{order_id}/phases")
def list_phases(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    is_participant = order.buyer_id == current_user.id or order.seller_id == current_user.id
    is_admin_or_reviewer = current_user.is_admin == 1 or current_user.is_reviewer == 1
    if not is_participant and not is_admin_or_reviewer:
        raise HTTPException(403, "无权查看此订单的付款阶段")
    phases = db.query(PaymentPhase).filter(PaymentPhase.order_id == order_id).order_by(PaymentPhase.phase_order).all()
    return [{"id": p.id, "name": p.name, "ratio": p.ratio, "phase_order": p.phase_order,
             "amount": p.amount, "status": p.status,
             "completed_at": str(p.completed_at) if p.completed_at else None,
             "created_at": str(p.created_at)} for p in phases]


@router.post("/phases/{phase_id}/complete")
def complete_phase(phase_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    phase = db.query(PaymentPhase).filter(PaymentPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(404, "阶段不存在")
    order = db.query(Order).filter(Order.id == phase.order_id).first()
    if not order:
        raise HTTPException(404, "关联订单不存在")
    if order.buyer_id != current_user.id:
        raise HTTPException(403, "只有订单甲方才能验收阶段")
    if phase.status != PhaseStatus.pending_review.value:
        raise HTTPException(400, f"当前阶段状态「{phase.status}」不允许验收")
    phase.status = PhaseStatus.completed.value
    phase.completed_at = datetime.utcnow()
    _fund_record(db, phase.order_id, phase.order.seller_id if phase.order else None,
                 "阶段放款", phase.amount, "in", f"阶段「{phase.name}」验收放款")
    _notify(db, phase.order.seller_id if phase.order else 0, "阶段验收通过",
            f"订单阶段「{phase.name}」已通过验收，金额{phase.amount}元即将到账。")
    db.commit()
    return {"message": "阶段验收完成"}
