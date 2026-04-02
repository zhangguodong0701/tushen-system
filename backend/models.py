from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import enum
import os

# 优先读取环境变量，回退到 SQLite（本地开发）
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./tushen.db"
)

if DATABASE_URL.startswith("mysql"):
    # MySQL 连接池配置
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,       # 自动检测连接是否断开
        pool_recycle=3600,        # 1小时回收连接，避免 MySQL 超时断开
        pool_size=10,
        max_overflow=20,
        echo=False
    )
else:
    # SQLite 本地开发
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserType(str, enum.Enum):
    material_supplier = "材料商"
    equipment_supplier = "设备商"
    design_institute = "设计院"
    designer = "设计师"

class UserStatus(str, enum.Enum):
    pending = "待审核"
    approved = "通过"
    rejected = "驳回"

class DemandStatus(str, enum.Enum):
    draft = "草稿"
    published = "已发布"
    in_progress = "进行中"
    completed = "已完成"
    closed = "已关闭"

class OrderStatus(str, enum.Enum):
    pending_payment = "待付款"
    in_progress = "进行中"
    completed = "已完成"
    refunded = "已退款"

class DisputeStatus(str, enum.Enum):
    open = "处理中"
    resolved = "已解决"
    closed = "已关闭"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(200))
    real_name = Column(String(50))
    user_type = Column(String(20))
    status = Column(String(20), default="待审核")
    is_admin = Column(Integer, default=0)
    is_reviewer = Column(Integer, default=0)  # 审核员/客服标记
    company_name = Column(String(100))
    license_url = Column(String(300))
    cert_url = Column(String(300))
    avatar = Column(String(300), default="")
    # 实名认证
    auth_type = Column(String(20), default="")   # 个人 / 企业
    id_card_front = Column(String(300), default="")  # 身份证正面
    id_card_back = Column(String(300), default="")   # 身份证背面
    business_license = Column(String(300), default="")  # 营业执照（企业）
    is_blacklisted = Column(Integer, default=0)  # 黑名单标记
    created_at = Column(DateTime, default=datetime.utcnow)
    demands = relationship("Demand", back_populates="owner", foreign_keys="Demand.owner_id")
    orders_as_buyer = relationship("Order", back_populates="buyer", foreign_keys="Order.buyer_id")
    orders_as_seller = relationship("Order", back_populates="seller", foreign_keys="Order.seller_id")
    fund_records = relationship("FundRecord", foreign_keys="FundRecord.user_id")
    operation_logs = relationship("OperationLog", foreign_keys="OperationLog.user_id")
    feedbacks = relationship("Feedback", foreign_keys="Feedback.user_id")

class Demand(Base):
    __tablename__ = "demands"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    description = Column(Text)
    budget = Column(Float, default=0)
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    deadline = Column(String(100), nullable=True)
    payment_type = Column(String(20), default="一次性")
    payment_phases = Column(Text)  # JSON格式，存储分阶段付款配置，如：[{"name":"初稿交付","ratio":30},{"name":"终稿验收","ratio":70}]
    status = Column(String(20), default="草稿")
    profession = Column(String(50))
    demand_type = Column(String(50))
    file_url = Column(String(300))
    owner_id = Column(Integer, ForeignKey("users.id"))
    chosen_quote_id = Column(Integer, nullable=True)  # 中标的报价ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner = relationship("User", back_populates="demands", foreign_keys=[owner_id])
    quotes = relationship("Quote", back_populates="demand")

class Quote(Base):
    __tablename__ = "quotes"
    id = Column(Integer, primary_key=True, index=True)
    demand_id = Column(Integer, ForeignKey("demands.id"))
    bidder_id = Column(Integer, ForeignKey("users.id"))
    price = Column(Float)
    remark = Column(Text)
    status = Column(String(20), default="待选择")
    created_at = Column(DateTime, default=datetime.utcnow)
    demand = relationship("Demand", back_populates="quotes")
    bidder = relationship("User", foreign_keys=[bidder_id])

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    demand_id = Column(Integer, ForeignKey("demands.id"))
    buyer_id = Column(Integer, ForeignKey("users.id"))
    seller_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    status = Column(String(20), default="待付款")
    payment_type = Column(String(20), default="一次性")
    escrow_status = Column(String(20), default="未托管")  # 未托管/已托管/已释放
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    buyer = relationship("User", back_populates="orders_as_buyer", foreign_keys=[buyer_id])
    seller = relationship("User", back_populates="orders_as_seller", foreign_keys=[seller_id])
    demand = relationship("Demand", foreign_keys=[demand_id])
    drawings = relationship("Drawing", back_populates="order")
    phases = relationship("PaymentPhase", back_populates="order")
    # fund_records relationship removed to avoid circular import

class Drawing(Base):
    __tablename__ = "drawings"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    uploader_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String(200))
    file_url = Column(String(300))
    version = Column(String(20), default="V1")
    comments = Column(Text, default="")
    comment_images = Column(Text, default="")  # JSON array of image URLs
    created_at = Column(DateTime, default=datetime.utcnow)
    order = relationship("Order", back_populates="drawings")
    uploader = relationship("User", foreign_keys=[uploader_id])

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200))
    content = Column(Text)
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Dispute(Base):
    __tablename__ = "disputes"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    initiator_id = Column(Integer, ForeignKey("users.id"))
    description = Column(Text)
    evidence_url = Column(String(300))
    evidence_files = Column(Text, default="")  # JSON array of URLs
    status = Column(String(20), default="处理中")
    result = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    initiator = relationship("User", foreign_keys=[initiator_id])


# ========== 新增模型 ==========
class PaymentPhase(Base):
    """分阶段付款里程碑"""
    __tablename__ = "payment_phases"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    name = Column(String(100))           # 阶段名称，如"初稿提交"
    ratio = Column(Integer, default=0)   # 阶段比例（百分比），如30表示30%
    phase_order = Column(Integer, default=0)  # 阶段序号，用于排序
    amount = Column(Float)               # 该阶段金额
    status = Column(String(20), default="待验收")  # 待验收/已验收
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # 关系定义
    order = relationship("Order", back_populates="phases", foreign_keys=[order_id])


class FundRecord(Base):
    """资金流水记录"""
    __tablename__ = "fund_records"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String(20))    # 托管/放款/退款
    amount = Column(Float)
    direction = Column(String(10))  # in=入账 out=出账
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    # 关系定义
    user = relationship("User", foreign_keys=[user_id])


class OperationLog(Base):
    """异常操作记录"""
    __tablename__ = "operation_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50))    # 取消订单/发起纠纷/黑名单
    target_type = Column(String(30))   # order/dispute/user
    target_id = Column(Integer)
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    # 关系定义
    user = relationship("User", foreign_keys=[user_id])


class Feedback(Base):
    """用户投诉反馈"""
    __tablename__ = "feedbacks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    status = Column(String(20), default="待处理")   # 待处理/已处理
    reply = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
