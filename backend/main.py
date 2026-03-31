from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import os, shutil, uuid, json

from models import (
    init_db, get_db, User, Demand, Quote, Order, Drawing, Notification, Dispute,
    PaymentPhase, FundRecord, OperationLog, Feedback
)
from auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, get_current_admin
)

# 审核员权限依赖
def get_current_reviewer(current_user: User = Depends(get_current_user)):
    """审核员/客服权限验证"""
    if not current_user.is_reviewer and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要审核员或管理员权限")
    return current_user
from pydantic import BaseModel

app = FastAPI(title="图审系统API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.on_event("startup")
def startup():
    init_db()
    db = next(get_db())
    admin = db.query(User).filter(User.is_admin == 1).first()
    if not admin:
        admin_user = User(
            phone="13800000000",
            email="admin@tushen.com",
            hashed_password=get_password_hash("admin123"),
            real_name="系统管理员",
            user_type="设计院",
            status="通过",
            is_admin=1,
            company_name="图审平台"
        )
        db.add(admin_user)
    # 创建审核员账号（如果不存在）
    reviewer = db.query(User).filter(User.is_reviewer == 1).first()
    if not reviewer:
        reviewer_user = User(
            phone="13900000000",
            email="reviewer@tushen.com",
            hashed_password=get_password_hash("reviewer123"),
            real_name="平台审核员",
            user_type="设计师",
            status="通过",
            is_reviewer=1,
            company_name="图审平台"
        )
        db.add(reviewer_user)
    db.commit()
    db.close()

# ========== Schemas ==========
class UserRegister(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    password: str
    real_name: str
    user_type: str
    company_name: Optional[str] = None
    auth_type: Optional[str] = "个人"
    role: Optional[str] = None  # 甲/乙方（前端用）

class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class DemandCreate(BaseModel):
    title: str
    description: str
    budget: float
    payment_type: str = "一次性"
    payment_phases: Optional[str] = None  # JSON格式的阶段配置
    profession: Optional[str] = None
    demand_type: Optional[str] = None

class DemandUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = None
    payment_type: Optional[str] = None
    payment_phases: Optional[str] = None  # JSON格式的阶段配置
    profession: Optional[str] = None
    demand_type: Optional[str] = None

class QuoteCreate(BaseModel):
    price: float
    remark: Optional[str] = None

class OrderCreate(BaseModel):
    demand_id: int
    seller_id: Optional[int] = None  # 可选，后端会从中标报价中获取
    amount: float
    payment_type: str = "一次性"

class DisputeCreate(BaseModel):
    order_id: int
    description: str

class NotificationCreate(BaseModel):
    user_id: int
    title: str
    content: str

class PhaseCreate(BaseModel):
    name: str
    amount: float
    ratio: int = 0  # 阶段比例（百分比）

class FeedbackCreate(BaseModel):
    content: str

def save_file(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1]
    fname = f"{uuid.uuid4().hex}{ext}"
    fpath = os.path.join(UPLOAD_DIR, fname)
    with open(fpath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return f"/uploads/{fname}"

def user_to_dict(u: User):
    return {
        "id": u.id, "phone": u.phone, "email": u.email,
        "real_name": u.real_name, "user_type": u.user_type,
        "status": u.status, "is_admin": u.is_admin,
        "is_reviewer": u.is_reviewer,
        "company_name": u.company_name, "license_url": u.license_url,
        "cert_url": u.cert_url, "avatar": u.avatar,
        "auth_type": u.auth_type or "", "is_blacklisted": u.is_blacklisted,
        "id_card_front": u.id_card_front or "",
        "id_card_back": u.id_card_back or "",
        "business_license": u.business_license or "",
        "created_at": str(u.created_at)
    }

def demand_to_dict(d: Demand):
    return {
        "id": d.id, "title": d.title, "description": d.description,
        "budget": d.budget, "payment_type": d.payment_type,
        "payment_phases": json.loads(d.payment_phases) if d.payment_phases else None,
        "status": d.status, "profession": d.profession,
        "demand_type": d.demand_type, "file_url": d.file_url,
        "owner_id": d.owner_id,
        "owner_name": d.owner.real_name if d.owner else "",
        "created_at": str(d.created_at), "updated_at": str(d.updated_at),
        "quote_count": len(d.quotes) if d.quotes else 0
    }

def order_to_dict(o: Order):
    return {
        "id": o.id, "demand_id": o.demand_id,
        "buyer_id": o.buyer_id, "seller_id": o.seller_id,
        "amount": o.amount, "status": o.status,
        "payment_type": o.payment_type,
        "escrow_status": getattr(o, 'escrow_status', '') or '',
        "buyer_name": o.buyer.real_name if o.buyer else "",
        "seller_name": o.seller.real_name if o.seller else "",
        "demand_title": o.demand.title if o.demand else "",
        "demand_file_url": getattr(o.demand, 'file_url', None) if o.demand else None,
        "demand_filename": getattr(o.demand, 'filename', None) if o.demand else None,
        "created_at": str(o.created_at), "updated_at": str(o.updated_at)
    }

def _notify(db, user_id, title, content):
    n = Notification(user_id=user_id, title=title, content=content)
    db.add(n)
    return n

def _log_action(db, user_id, action, target_type, target_id, detail=""):
    log = OperationLog(user_id=user_id, action=action, target_type=target_type, target_id=target_id, detail=detail)
    db.add(log)
    return log

def _fund_record(db, order_id, user_id, ftype, amount, direction, description):
    rec = FundRecord(order_id=order_id, user_id=user_id, type=ftype, amount=amount, direction=direction, description=description)
    db.add(rec)
    return rec

# ========== Auth API ==========
@app.post("/api/auth/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    if data.phone:
        if db.query(User).filter(User.phone == data.phone).first():
            raise HTTPException(400, "手机号已注册")
    if data.email:
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(400, "邮箱已注册")
    user = User(
        phone=data.phone, email=data.email,
        hashed_password=get_password_hash(data.password),
        real_name=data.real_name, user_type=data.user_type,
        company_name=data.company_name, status="待审核",
        auth_type=data.auth_type or "个人"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "注册成功，等待审核", "user_id": user.id}

@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.phone == form_data.username) | (User.email == form_data.username)
    ).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="账号或密码错误")
    # 检查用户审核状态
    if user.status == "待审核":
        raise HTTPException(status_code=403, detail="您的账号正在等待审核，请耐心等待管理员处理")
    if user.status == "已驳回":
        raise HTTPException(status_code=403, detail="您的账号审核未通过，请完善资料后重新注册")
    if user.is_blacklisted == 1:
        raise HTTPException(status_code=403, detail="您的账号已被限制登录，如有疑问请联系客服")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user_to_dict(user)}

@app.get("/api/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return user_to_dict(current_user)

@app.put("/api/auth/me")
def update_me(data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for k, v in data.dict(exclude_none=True).items():
        setattr(current_user, k, v)
    db.commit()
    return user_to_dict(current_user)

@app.post("/api/auth/upload-cert")
def upload_cert(file: UploadFile = File(...), cert_type: str = Form("license"),
                current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    url = save_file(file)
    if cert_type == "license":
        current_user.license_url = url
    elif cert_type == "id_card_front":
        current_user.id_card_front = url
    elif cert_type == "id_card_back":
        current_user.id_card_back = url
    elif cert_type == "business_license":
        current_user.business_license = url
    else:
        current_user.cert_url = url
    db.commit()
    return {"url": url}

# ========== Demand API ==========
# 角色判断辅助函数
JIA_FANG_TYPES = ['业主', '建设单位', '项目方']
YI_FANG_TYPES = ['设计院', '设计师', '材料商', '设备商']

def is_jia_fang(user: User) -> bool:
    """判断是否为甲方用户"""
    return user.user_type in JIA_FANG_TYPES

def is_yi_fang(user: User) -> bool:
    """判断是否为乙方用户"""
    return user.user_type in YI_FANG_TYPES

@app.post("/api/demands")
def create_demand(data: DemandCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P01: 角色校验 - 只有甲方才能发布需求
    if not is_jia_fang(current_user):
        raise HTTPException(403, "只有甲方（业主/建设单位/项目方）才能发布需求")
    demand = Demand(**data.dict(), owner_id=current_user.id, status="草稿")
    db.add(demand)
    db.commit()
    db.refresh(demand)
    return demand_to_dict(demand)

@app.put("/api/demands/{demand_id}")
def update_demand(demand_id: int, data: DemandUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P20: 需求编辑需要验证状态 - 只允许编辑草稿状态的需求
    demand = db.query(Demand).filter(Demand.id == demand_id, Demand.owner_id == current_user.id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    if demand.status not in ("草稿",):
        raise HTTPException(400, f"当前需求状态为「{demand.status}」，不允许编辑")
    for k, v in data.dict(exclude_none=True).items():
        setattr(demand, k, v)
    demand.updated_at = datetime.utcnow()
    db.commit()
    return demand_to_dict(demand)

@app.post("/api/demands/{demand_id}/publish")
def publish_demand(demand_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    demand = db.query(Demand).filter(Demand.id == demand_id, Demand.owner_id == current_user.id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    demand.status = "已发布"
    db.commit()
    return {"message": "发布成功"}

@app.delete("/api/demands/{demand_id}")
def delete_demand(demand_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P21: 需求删除增加状态校验 - 不允许删除已发布/进行中/已完成状态的需求
    demand = db.query(Demand).filter(Demand.id == demand_id, Demand.owner_id == current_user.id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    if demand.status in ("已发布", "进行中", "已完成"):
        raise HTTPException(400, f"当前需求「{demand.status}」状态不允许删除")
    db.delete(demand)
    db.commit()
    return {"message": "删除成功"}

@app.post("/api/demands/{demand_id}/close")
def close_demand(demand_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """甲方关闭已发布的需求（如果有中标则不允许关闭）"""
    demand = db.query(Demand).filter(Demand.id == demand_id, Demand.owner_id == current_user.id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    if demand.status != "已发布":
        raise HTTPException(400, "只有已发布状态的需求才能关闭")
    # 检查是否有中标
    from models import Quote
    winner = db.query(Quote).filter(Quote.demand_id == demand_id, Quote.status == "中标").first()
    if winner:
        raise HTTPException(400, "该需求已有中标方，无法关闭，请先取消中标")
    demand.status = "已关闭"
    db.commit()
    _notify(db, demand.owner_id, "需求已关闭", f"您发布的需求「{demand.title}」已被关闭。")
    return {"message": "需求已关闭"}

@app.get("/api/demands")
def list_demands(status: Optional[str] = None, profession: Optional[str] = None,
                 min_budget: Optional[float] = None, max_budget: Optional[float] = None,
                 keyword: Optional[str] = None, page: int = 1, page_size: int = 10,
                 db: Session = Depends(get_db)):
    q = db.query(Demand)
    if status:
        q = q.filter(Demand.status == status)
    if profession:
        q = q.filter(Demand.profession == profession)
    if min_budget is not None:
        q = q.filter(Demand.budget >= min_budget)
    if max_budget is not None:
        q = q.filter(Demand.budget <= max_budget)
    if keyword:
        q = q.filter(Demand.title.contains(keyword))
    total = q.count()
    demands = q.order_by(Demand.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"total": total, "page": page, "items": [demand_to_dict(d) for d in demands]}

@app.get("/api/demands/my")
def my_demands(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    demands = db.query(Demand).filter(Demand.owner_id == current_user.id).order_by(Demand.created_at.desc()).all()
    return [demand_to_dict(d) for d in demands]

@app.get("/api/demands/{demand_id}")
def get_demand(demand_id: int, db: Session = Depends(get_db)):
    demand = db.query(Demand).filter(Demand.id == demand_id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    return demand_to_dict(demand)

@app.post("/api/demands/{demand_id}/upload-file")
def upload_demand_file(demand_id: int, file: UploadFile = File(...),
                       current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    demand = db.query(Demand).filter(Demand.id == demand_id, Demand.owner_id == current_user.id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    url = save_file(file)
    demand.file_url = url
    db.commit()
    return {"url": url}

# ========== Quote API ==========
@app.post("/api/demands/{demand_id}/quotes")
def create_quote(demand_id: int, data: QuoteCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P02: 角色校验 - 只有乙方才能提交报价
    if not is_yi_fang(current_user):
        raise HTTPException(403, "只有乙方（设计院/设计师/材料商/设备商）才能提交报价")
    
    # 验证需求存在且状态为已发布
    demand = db.query(Demand).filter(Demand.id == demand_id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    if demand.status != "已发布":
        raise HTTPException(400, f"当前需求「{demand.status}」状态不允许报价")
    
    # 不能给自己发布的需求报价
    if demand.owner_id == current_user.id:
        raise HTTPException(400, "不能给自己的需求报价")
    
    existing = db.query(Quote).filter(Quote.demand_id == demand_id, Quote.bidder_id == current_user.id).first()
    if existing:
        raise HTTPException(400, "已提交过报价")
    quote = Quote(demand_id=demand_id, bidder_id=current_user.id, **data.dict())
    db.add(quote)
    db.commit()
    db.refresh(quote)
    
    # 通知甲方有新报价
    _notify(db, demand.owner_id, "📬 您有新报价", 
            f"用户「{current_user.real_name}」对您的需求「{demand.title}」提交了报价：¥{data.price.toLocaleString()}元。请及时查看并选择合适的乙方。")
    
    return {"id": quote.id, "price": quote.price, "remark": quote.remark, "status": quote.status}

@app.put("/api/quotes/{quote_id}")
def update_quote(quote_id: int, data: QuoteCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 只能编辑自己的报价，且只能编辑"待选择"状态的报价
    quote = db.query(Quote).filter(Quote.id == quote_id, Quote.bidder_id == current_user.id).first()
    if not quote:
        raise HTTPException(404, "报价不存在")
    if quote.status != "待选择":
        raise HTTPException(400, f"当前报价状态「{quote.status}」不允许编辑")
    quote.price = data.price
    quote.remark = data.remark
    db.commit()
    return {"message": "更新成功"}

@app.delete("/api/quotes/{quote_id}")
def cancel_quote(quote_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 只能取消自己的报价，且只能取消"待选择"状态的报价
    quote = db.query(Quote).filter(Quote.id == quote_id, Quote.bidder_id == current_user.id).first()
    if not quote:
        raise HTTPException(404, "报价不存在")
    if quote.status != "待选择":
        raise HTTPException(400, f"当前报价状态「{quote.status}」不允许取消")
    db.delete(quote)
    db.commit()
    return {"message": "取消成功"}

@app.get("/api/demands/{demand_id}/quotes")
def list_quotes(demand_id: int, db: Session = Depends(get_db)):
    quotes = db.query(Quote).filter(Quote.demand_id == demand_id).all()
    return [{"id": q.id, "price": q.price, "remark": q.remark, "status": q.status,
             "bidder_id": q.bidder_id, "bidder_name": q.bidder.real_name if q.bidder else "",
             "created_at": str(q.created_at)} for q in quotes]

@app.get("/api/quotes/my")
def my_quotes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quotes = db.query(Quote).filter(Quote.bidder_id == current_user.id).all()
    return [{"id": q.id, "price": q.price, "remark": q.remark, "status": q.status,
             "demand_id": q.demand_id, "demand_title": q.demand.title if q.demand else "",
             "created_at": str(q.created_at)} for q in quotes]

@app.post("/api/demands/{demand_id}/select-winner/{quote_id}")
def select_winner(demand_id: int, quote_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """选择中标方，同时自动创建订单"""
    demand = db.query(Demand).filter(Demand.id == demand_id, Demand.owner_id == current_user.id).first()
    if not demand:
        raise HTTPException(404, "需求不存在或无权限")
    if demand.status == "草稿":
        raise HTTPException(400, "需求尚未发布，请先发布需求后再选择中标方")
    if demand.status == "已关闭":
        raise HTTPException(400, "需求已关闭，无法选择中标方")
    if demand.status == "进行中":
        raise HTTPException(400, "该需求已有中标方")
    if demand.status != "已发布":
        raise HTTPException(400, f"该需求状态为「{demand.status}」，不允许选择中标方")
    quote = db.query(Quote).filter(Quote.id == quote_id, Quote.demand_id == demand_id).first()
    if not quote:
        raise HTTPException(404, "报价不存在")
    if quote.status == "中标":
        raise HTTPException(400, "该报价已经是中标方")
    
    # 更新报价状态
    quote.status = "中标"
    demand.status = "进行中"
    
    # 自动创建订单
    order = Order(
        buyer_id=current_user.id,  # 甲方（需求发布方）
        demand_id=demand_id,
        seller_id=quote.bidder_id,  # 乙方（中标方）
        amount=quote.price,
        payment_type=demand.payment_type,
        status="待付款"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # 如果是分阶段付款，自动创建订单阶段
    if demand.payment_type == "分阶段" and demand.payment_phases:
        try:
            phases = json.loads(demand.payment_phases)
            if phases and len(phases) > 0:
                for i, phase in enumerate(phases):
                    phase_amount = round(quote.price * phase.get("ratio", 0) / 100, 2)
                    payment_phase = PaymentPhase(
                        order_id=order.id,
                        name=phase.get("name", f"阶段{i+1}"),
                        ratio=phase.get("ratio", 0),
                        amount=phase_amount,
                        status="待验收",
                        phase_order=i + 1
                    )
                    db.add(payment_phase)
                db.commit()
        except json.JSONDecodeError:
            pass  # 阶段配置解析失败，跳过阶段创建
    
    # 通知中标方
    _notify(db, quote.bidder_id, "恭喜中标！", f"您对需求「{demand.title}」的报价已被选中，中标金额：{quote.price}元。请等待甲方付款。")
    # 通知甲方
    _notify(db, current_user.id, "中标已确定", f"已选定服务方，订单已创建，金额：{quote.price}元。请尽快完成支付。")
    db.commit()
    return {"message": "已选定中标方并创建订单", "winner_id": quote.bidder_id, "order_id": order.id}

# ========== Order API ==========
@app.post("/api/orders")
def create_order(data: OrderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    创建订单接口
    乙方（中标方）点击"创建订单"时调用，或甲方选择中标后自动创建
    """
    # 验证需求存在
    demand = db.query(Demand).filter(Demand.id == data.demand_id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    
    # 验证该报价是否中标，且当前用户是中标的乙方
    winning_quote = db.query(Quote).filter(
        Quote.demand_id == data.demand_id, 
        Quote.status == "中标",
        Quote.bidder_id == current_user.id  # 当前用户必须是中标的乙方
    ).first()
    if not winning_quote:
        raise HTTPException(403, "只有中标方才能创建订单")
    
    if data.amount <= 0:
        raise HTTPException(400, "订单金额必须大于0")
    
    # 检查是否已存在该需求的订单
    existing_order = db.query(Order).filter(Order.demand_id == data.demand_id).first()
    if existing_order:
        raise HTTPException(400, "该需求已创建过订单")
    
    order = Order(
        buyer_id=demand.owner_id,  # 甲方是买方
        demand_id=data.demand_id,
        seller_id=current_user.id,  # 乙方是卖方
        amount=data.amount,
        payment_type=data.payment_type
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # 通知甲方有新订单
    _notify(db, demand.owner_id, "新订单通知", f"您有一个新订单，需求：{demand.title}，金额：{data.amount}元。")
    # 通知乙方订单创建成功
    _notify(db, current_user.id, "订单创建成功", f"订单已创建，需求：{demand.title}，金额：{data.amount}元。")
    db.commit()
    return order_to_dict(order)

@app.get("/api/orders")
def list_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(Order).filter(
        (Order.buyer_id == current_user.id) | (Order.seller_id == current_user.id)
    ).order_by(Order.created_at.desc()).all()
    return [order_to_dict(o) for o in orders]

@app.get("/api/orders/{order_id}")
def get_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P09: 增加订单归属校验 - 只有订单参与方（买方/卖方）或管理员/审核员才能查看订单详情
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    # 检查是否为订单参与方或管理员/审核员
    is_participant = (order.buyer_id == current_user.id or order.seller_id == current_user.id)
    is_admin_or_reviewer = (current_user.is_admin == 1 or current_user.is_reviewer == 1)
    if not is_participant and not is_admin_or_reviewer:
        raise HTTPException(403, "无权查看此订单详情")
    return order_to_dict(order)

@app.post("/api/orders/{order_id}/pay")
def pay_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.buyer_id == current_user.id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status not in ("待付款",):
        raise HTTPException(400, "订单状态不允许支付")
    order.status = "进行中"
    order.escrow_status = "已托管"
    _fund_record(db, order.id, current_user.id, "托管", order.amount, "out", f"订单资金托管，金额：{order.amount}元")
    _notify(db, order.seller_id, "资金托管通知", f"买方已支付{order.amount}元，资金已由平台托管，等待服务完成。")
    db.commit()
    return {"message": "支付成功（资金已托管）"}

@app.post("/api/orders/{order_id}/accept")
def accept_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.buyer_id == current_user.id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status != "进行中":
        raise HTTPException(400, "订单状态不允许验收")
    
    # 一次性订单：直接完成整个订单
    if order.payment_type == "一次性":
        order.status = "已完成"
        order.escrow_status = "已释放"
        _fund_record(db, order.id, order.seller_id, "放款", order.amount, "in", f"订单验收完成，一次性放款{order.amount}元")
        _notify(db, order.seller_id, "验收通过，资金已放款", f"买方已确认验收，订单完成，金额{order.amount}元已放款至您的账户。")
        _log_action(db, current_user.id, "确认验收", "order", order_id, f"买方确认验收，订单完成（一次性付款）")
        db.commit()
        return {"message": "验收确认，平台已放款"}
    else:
        # 分阶段订单：检查是否所有阶段都已验收
        phases = db.query(PaymentPhase).filter(PaymentPhase.order_id == order_id).all()
        if not phases:
            raise HTTPException(400, "分阶段订单尚未配置付款阶段，请先配置阶段")
        unverified = [p for p in phases if p.status != "已验收"]
        if unverified:
            raise HTTPException(400, f"还有{len(unverified)}个阶段未验收，请先完成所有阶段的验收")
        # 所有阶段都已验收，订单完成
        order.status = "已完成"
        order.escrow_status = "已释放"
        _notify(db, order.seller_id, "订单完成", f"所有付款阶段已验收，订单全部完成。")
        _log_action(db, current_user.id, "确认验收", "order", order_id, f"买方确认全部阶段验收，订单完成（分阶段付款）")
        db.commit()
        return {"message": "所有阶段验收完成，订单已完结"}

@app.post("/api/orders/{order_id}/refund")
def refund_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P03: 权限校验 - 只有管理员才能执行退款操作
    if not current_user.is_admin:
        raise HTTPException(403, "只有管理员才能执行退款操作")
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    # 退款状态校验
    if order.status in ("已完成", "已退款"):
        raise HTTPException(400, f"当前订单「{order.status}」状态不允许退款")
    order.status = "已退款"
    order.escrow_status = "已释放"
    # 生成退款资金记录
    _fund_record(db, order.id, order.buyer_id, "退款", order.amount, "in", f"管理员操作退款：{order.amount}元")
    _notify(db, order.buyer_id, "退款通知", f"您的订单已退款，金额{order.amount}元已退还。")
    _notify(db, order.seller_id, "退款通知", f"订单已退款，资金{order.amount}元已退给买方。")
    db.commit()
    return {"message": "退款成功"}

# ========== Drawing API ==========
@app.post("/api/orders/{order_id}/drawings")
def upload_drawing(order_id: int, file: UploadFile = File(...), version: str = Form("V1"),
                   current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 权限验证：只有订单卖方才能上传图纸
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.seller_id != current_user.id:
        raise HTTPException(403, "只有订单承接方（乙方）才能上传图纸")
    
    url = save_file(file)
    drawing = Drawing(order_id=order_id, uploader_id=current_user.id,
                      filename=file.filename, file_url=url, version=version)
    db.add(drawing)
    db.commit()
    db.refresh(drawing)
    return {"id": drawing.id, "filename": drawing.filename, "file_url": drawing.file_url,
            "version": drawing.version, "created_at": str(drawing.created_at)}

@app.get("/api/orders/{order_id}/drawings")
def list_drawings(order_id: int, db: Session = Depends(get_db)):
    drawings = db.query(Drawing).filter(Drawing.order_id == order_id).order_by(Drawing.created_at.desc()).all()
    return [{"id": d.id, "filename": d.filename, "file_url": d.file_url,
             "version": d.version, "comments": d.comments,
             "comment_images": d.comment_images,
             "uploader_name": d.uploader.real_name if d.uploader else "",
             "created_at": str(d.created_at)} for d in drawings]

@app.put("/api/drawings/{drawing_id}/comments")
def add_comment(drawing_id: int, comments: str = Form(""), comment_images: str = Form(""),
                current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P06: 权限校验 - 只有订单买方（甲方）才能提交修改意见
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(404, "图纸不存在")
    
    # 获取订单信息
    order = db.query(Order).filter(Order.id == drawing.order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    
    # 只有买方（甲方）才能提交修改意见
    if order.buyer_id != current_user.id:
        raise HTTPException(403, "只有订单甲方才能提交修改意见")
    
    drawing.comments = comments
    if comment_images:
        drawing.comment_images = comment_images
    db.commit()
    return {"message": "意见已保存"}

@app.post("/api/drawings/{drawing_id}/upload-comment-img")
def upload_comment_img(drawing_id: int, file: UploadFile = File(...),
                       current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P06: 权限校验 - 只有订单买方（甲方）才能上传意见图片
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(404, "图纸不存在")
    
    # 获取订单信息
    order = db.query(Order).filter(Order.id == drawing.order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    
    # 只有买方（甲方）才能上传意见图片
    if order.buyer_id != current_user.id:
        raise HTTPException(403, "只有订单甲方才能上传意见图片")
    
    url = save_file(file)
    return {"url": url}

# ========== Notification API ==========
@app.get("/api/notifications")
def list_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(50).all()
    return [{"id": n.id, "title": n.title, "content": n.content,
             "is_read": n.is_read, "created_at": str(n.created_at)} for n in notifs]

@app.post("/api/notifications/{notif_id}/read")
def read_notification(notif_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == current_user.id).first()
    if notif:
        notif.is_read = 1
        db.commit()
    return {"message": "已读"}

# ========== Dispute API ==========
@app.post("/api/disputes")
def create_dispute(data: DisputeCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P15: 增加订单归属校验 - 只有订单参与方才能发起纠纷
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(404, "关联订单不存在")
    # 检查是否为订单参与方
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        raise HTTPException(403, "只有订单参与方才能发起纠纷")
    # 检查是否已有处理中的纠纷
    existing = db.query(Dispute).filter(
        Dispute.order_id == data.order_id, 
        Dispute.status == "处理中"
    ).first()
    if existing:
        raise HTTPException(400, "该订单已有处理中的纠纷，请等待处理完成")
    dispute = Dispute(initiator_id=current_user.id, **data.dict())
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    return {"id": dispute.id, "status": dispute.status}

@app.post("/api/disputes/{dispute_id}/upload-evidence")
def upload_evidence(dispute_id: int, file: UploadFile = File(...),
                    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P16: 权限校验 - 只有纠纷发起人或订单另一方才能上传证据
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(404, "纠纷不存在")
    # 获取订单信息
    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    if not order:
        raise HTTPException(404, "关联订单不存在")
    # 检查是否为纠纷发起人或订单参与方
    is_initiator = dispute.initiator_id == current_user.id
    is_participant = order.buyer_id == current_user.id or order.seller_id == current_user.id
    if not is_initiator and not is_participant:
        raise HTTPException(403, "无权为此纠纷上传证据")
    url = save_file(file)
    dispute.evidence_url = url
    db.commit()
    return {"url": url}

@app.get("/api/disputes")
def list_disputes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    disputes = db.query(Dispute).filter(Dispute.initiator_id == current_user.id).all()
    return [{"id": d.id, "order_id": d.order_id, "description": d.description,
             "evidence_url": d.evidence_url, "evidence_files": d.evidence_files,
             "status": d.status, "result": d.result, "created_at": str(d.created_at)} for d in disputes]

# ========== Admin API ==========
@app.get("/api/admin/users")
def admin_list_users(status: Optional[str] = None, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    q = db.query(User)
    if status:
        q = q.filter(User.status == status)
    users = q.all()
    return [user_to_dict(u) for u in users]

@app.post("/api/admin/users/{user_id}/approve")
def approve_user(user_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.status = "通过"
    db.commit()
    notif = Notification(user_id=user_id, title="审核通过", content="您的账号已审核通过，可以正常使用平台。")
    db.add(notif)
    db.commit()
    return {"message": "已审核通过"}

@app.post("/api/admin/users/{user_id}/reject")
def reject_user(user_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.status = "驳回"
    db.commit()
    notif = Notification(user_id=user_id, title="审核驳回", content="您的账号审核未通过，请完善资质后重新提交。")
    db.add(notif)
    db.commit()
    return {"message": "已驳回"}

@app.get("/api/admin/demands")
def admin_list_demands(status: Optional[str] = None, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    q = db.query(Demand)
    if status:
        q = q.filter(Demand.status == status)
    demands = q.order_by(Demand.created_at.desc()).all()
    return [demand_to_dict(d) for d in demands]

@app.get("/api/admin/orders")
def admin_list_orders(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return [order_to_dict(o) for o in orders]

@app.get("/api/admin/disputes")
def admin_list_disputes(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    disputes = db.query(Dispute).order_by(Dispute.created_at.desc()).all()
    return [{"id": d.id, "order_id": d.order_id, "description": d.description,
             "evidence_url": d.evidence_url, "evidence_files": d.evidence_files,
             "status": d.status, "result": d.result,
             "initiator_id": d.initiator_id,
             "initiator_name": d.initiator.real_name if d.initiator else "",
             "created_at": str(d.created_at)} for d in disputes]

@app.post("/api/admin/disputes/{dispute_id}/resolve")
def resolve_dispute(dispute_id: int, result: str = Form(...), action: str = Form("refund"),
                    db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(404, "纠纷不存在")
    dispute.result = result
    dispute.status = "已解决"
    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    if order:
        if action == "refund":
            order.status = "已退款"
            order.escrow_status = "已释放"
            _fund_record(db, order.id, order.buyer_id, "退款", order.amount, "in", f"纠纷裁决退款：{result}")
        else:
            order.status = "已完成"
            order.escrow_status = "已释放"
            _fund_record(db, order.id, order.seller_id, "放款", order.amount, "in", f"纠纷裁决放款：{result}")
        _log_action(db, dispute.initiator_id, "纠纷裁决", "dispute", dispute_id, result)
    # 通知双方
    if order:
        _notify(db, order.buyer_id, "纠纷处理结果通知", f"您的纠纷已有处理结果：{result}")
        _notify(db, order.seller_id, "纠纷处理结果通知", f"您的纠纷已有处理结果：{result}")
    db.commit()
    return {"message": "纠纷已处理"}

@app.get("/api/admin/stats")
def admin_stats(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return {
        "total_users": db.query(User).count(),
        "pending_users": db.query(User).filter(User.status == "待审核").count(),
        "total_demands": db.query(Demand).count(),
        "published_demands": db.query(Demand).filter(Demand.status == "已发布").count(),
        "total_orders": db.query(Order).count(),
        "active_orders": db.query(Order).filter(Order.status == "进行中").count(),
        "total_disputes": db.query(Dispute).count(),
        "open_disputes": db.query(Dispute).filter(Dispute.status == "处理中").count(),
        "total_amount": sum(o.amount for o in db.query(Order).filter(Order.status == "已完成").all()),
    }

# ========== 黑名单管理 ==========
@app.get("/api/admin/blacklist")
def admin_blacklist(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    users = db.query(User).filter(User.is_blacklisted == 1).all()
    return [user_to_dict(u) for u in users]

@app.post("/api/admin/users/{user_id}/blacklist")
def blacklist_user(user_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    if user.is_admin:
        raise HTTPException(400, "无法将管理员加入黑名单")
    if user.is_reviewer:
        raise HTTPException(400, "无法将审核员加入黑名单")
    user.is_blacklisted = 1
    _log_action(db, user_id, "加入黑名单", "user", user_id, f"管理员操作，被加黑名单")
    _notify(db, user_id, "账号黑名单通知", "您的账号已被平台加入黑名单，如有疑问请联系客服。")
    db.commit()
    return {"message": "已加入黑名单"}

@app.post("/api/admin/users/{user_id}/unblacklist")
def unblacklist_user(user_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.is_blacklisted = 0
    _notify(db, user_id, "黑名单解除通知", "您的账号已解除黑名单限制，可以正常使用平台。")
    db.commit()
    return {"message": "已解除黑名单"}

# ========== 资金记录 ==========
@app.get("/api/admin/fund-records")
def admin_fund_records(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    records = db.query(FundRecord).order_by(FundRecord.created_at.desc()).limit(200).all()
    return [{"id": r.id, "order_id": r.order_id, "user_id": r.user_id,
             "user_name": r.user.real_name if r.user else "",
             "type": r.type, "amount": r.amount, "direction": r.direction,
             "description": r.description, "created_at": str(r.created_at)} for r in records]

# ========== 操作日志 ==========
@app.get("/api/admin/operation-logs")
def admin_operation_logs(limit: int = 50, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    logs = db.query(OperationLog).order_by(OperationLog.created_at.desc()).limit(limit).all()
    return [{"id": l.id, "user_id": l.user_id,
             "user_name": l.user.real_name if l.user else "",
             "action": l.action, "target_type": l.target_type,
             "target_id": l.target_id, "detail": l.detail,
             "created_at": str(l.created_at)} for l in logs]

# ========== 内容审核 ==========
@app.get("/api/admin/content-review")
def admin_content_review(db: Session = Depends(get_db), reviewer=Depends(get_current_reviewer)):
    demands = db.query(Demand).filter(Demand.status == "已发布").all()
    drawings = db.query(Drawing).all()
    return {
        "demands": [demand_to_dict(d) for d in demands[:20]],
        "drawings": [{"id": d.id, "filename": d.filename, "file_url": d.file_url, "order_id": d.order_id,
                      "uploader_name": d.uploader.real_name if d.uploader else "",
                      "version": d.version, "created_at": str(d.created_at)} for d in drawings[:50]]
    }

@app.post("/api/admin/demands/{demand_id}/close")
def admin_close_demand(demand_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    demand = db.query(Demand).filter(Demand.id == demand_id).first()
    if not demand:
        raise HTTPException(404, "需求不存在")
    demand.status = "已关闭"
    _log_action(db, demand.owner_id, "关闭需求", "demand", demand_id, f"管理员关闭需求：{demand.title}")
    _notify(db, demand.owner_id, "需求关闭通知", f"您的需求「{demand.title}」已被管理员关闭。")
    db.commit()
    return {"message": "需求已关闭"}

# ========== 投诉反馈 ==========
@app.post("/api/feedback")
def create_feedback(data: FeedbackCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fb = Feedback(user_id=current_user.id, content=data.content)
    db.add(fb)
    db.commit()
    return {"id": fb.id, "message": "反馈已提交，我们会尽快处理"}

@app.get("/api/feedback")
def list_my_feedback(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    feedbacks = db.query(Feedback).filter(Feedback.user_id == current_user.id).order_by(Feedback.created_at.desc()).all()
    return [{"id": f.id, "content": f.content, "status": f.status,
             "reply": f.reply, "created_at": str(f.created_at),
             "updated_at": str(f.updated_at)} for f in feedbacks]

@app.get("/api/admin/feedbacks")
def admin_list_feedbacks(db: Session = Depends(get_db), current_user: User = Depends(get_current_reviewer)):
    feedbacks = db.query(Feedback).order_by(Feedback.created_at.desc()).all()
    result = []
    for f in feedbacks:
        user = db.query(User).filter(User.id == f.user_id).first()
        result.append({
            "id": f.id, 
            "user_id": f.user_id, 
            "user_name": user.real_name if user else "",
            "content": f.content, 
            "status": f.status, 
            "reply": f.reply,
            "created_at": str(f.created_at), 
            "updated_at": str(f.updated_at)
        })
    return result

@app.post("/api/admin/feedbacks/{feedback_id}/reply")
def admin_reply_feedback(feedback_id: int, reply: str = Query(...),
                         db: Session = Depends(get_db), current_user: User = Depends(get_current_reviewer)):
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(404, "反馈不存在")
    fb.reply = reply
    fb.status = "已处理"
    _notify(db, fb.user_id, "投诉反馈回复", f"您提交的投诉反馈已有处理结果：{reply}")
    db.commit()
    return {"message": "回复已发送"}

# ========== 分阶段付款 ==========
@app.post("/api/orders/{order_id}/phases")
def create_phase(order_id: int, data: PhaseCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P05: 权限校验 - 只有订单买方（甲方）才能添加付款阶段
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.buyer_id != current_user.id:
        raise HTTPException(403, "只有订单甲方才能添加付款阶段")
    # 自动计算阶段序号
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

@app.get("/api/orders/{order_id}/phases")
def list_phases(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P13: 增加鉴权 - 只有订单参与方或管理员/审核员才能查看阶段列表
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

@app.post("/api/phases/{phase_id}/complete")
def complete_phase(phase_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P04: 权限校验 - 只有订单买方（甲方）才能验收阶段
    phase = db.query(PaymentPhase).filter(PaymentPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(404, "阶段不存在")
    
    # 获取订单信息
    order = db.query(Order).filter(Order.id == phase.order_id).first()
    if not order:
        raise HTTPException(404, "关联订单不存在")
    
    if order.buyer_id != current_user.id:
        raise HTTPException(403, "只有订单甲方才能验收阶段")
    
    if phase.status != "待验收":
        raise HTTPException(400, f"当前阶段状态「{phase.status}」不允许验收")
    
    phase.status = "已验收"
    phase.completed_at = datetime.utcnow()
    # 自动生成资金记录（阶段放款）
    _fund_record(db, phase.order_id, phase.order.seller_id if phase.order else None,
                 "阶段放款", phase.amount, "in", f"阶段「{phase.name}」验收放款")
    _notify(db, phase.order.seller_id if phase.order else 0, "阶段验收通过",
            f"订单阶段「{phase.name}」已通过验收，金额{phase.amount}元即将到账。")
    db.commit()
    return {"message": "阶段验收完成"}

# ========== 纠纷多证据上传 ==========
@app.post("/api/disputes/{dispute_id}/evidence-multiple")
def upload_multiple_evidence(dispute_id: int, file: UploadFile = File(...),
                             current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P16: 权限校验 - 只有纠纷发起人或订单参与方才能上传证据
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(404, "纠纷不存在")
    
    # 获取订单信息
    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    if not order:
        raise HTTPException(404, "关联订单不存在")
    
    # 检查是否为纠纷发起人或订单参与方
    is_initiator = dispute.initiator_id == current_user.id
    is_participant = order.buyer_id == current_user.id or order.seller_id == current_user.id
    if not is_initiator and not is_participant:
        raise HTTPException(403, "无权为此纠纷上传证据")
    
    url = save_file(file)
    # 追加到 evidence_files JSON 数组
    files = []
    if dispute.evidence_files:
        try: files = json.loads(dispute.evidence_files)
        except: pass
    files.append({"filename": file.filename, "url": url})
    dispute.evidence_files = json.dumps(files, ensure_ascii=False)
    db.commit()
    return {"url": url, "files": files}

@app.get("/api/disputes/{dispute_id}/evidence-files")
def get_evidence_files(dispute_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # P14: 增加鉴权 - 只有纠纷发起人、订单参与方或管理员/审核员才能查看证据
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(404, "纠纷不存在")
    
    # 获取订单信息
    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    
    # 检查是否有权限查看
    is_initiator = dispute.initiator_id == current_user.id
    is_participant = order and (order.buyer_id == current_user.id or order.seller_id == current_user.id)
    is_admin_or_reviewer = current_user.is_admin == 1 or current_user.is_reviewer == 1
    if not is_initiator and not is_participant and not is_admin_or_reviewer:
        raise HTTPException(403, "无权查看此纠纷的证据")
    
    files = []
    if dispute.evidence_files:
        try: files = json.loads(dispute.evidence_files)
        except: pass
    return files

# ========== 完善通知自动化（订单各状态变更） ==========
# 已在 pay_order, accept_order 中增加通知

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
