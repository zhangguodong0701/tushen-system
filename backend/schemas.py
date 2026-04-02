# schemas.py - Pydantic 请求/响应模型
from pydantic import BaseModel
from typing import Optional


class UserRegister(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    password: str
    real_name: str
    user_type: str
    company_name: Optional[str] = None
    auth_type: Optional[str] = "个人"
    role: Optional[str] = None


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
    payment_phases: Optional[str] = None
    profession: Optional[str] = None
    demand_type: Optional[str] = None


class DemandUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    deadline: Optional[str] = None
    payment_type: Optional[str] = None
    payment_phases: Optional[str] = None
    profession: Optional[str] = None
    demand_type: Optional[str] = None


class QuoteCreate(BaseModel):
    price: float
    remark: Optional[str] = None


class OrderCreate(BaseModel):
    demand_id: int
    seller_id: Optional[int] = None
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
    ratio: int = 0


class FeedbackCreate(BaseModel):
    content: str
