# schemas.py - Pydantic 请求/响应模型
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
import re


class UserRegister(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    password: str
    real_name: str
    user_type: str
    company_name: Optional[str] = None
    auth_type: Optional[str] = "个人"
    role: Optional[str] = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None and v != '':
            # 中国大陆手机号：1开头，第二位3-9，共11位
            if not re.match(r'^1[3-9]\d{9}$', v):
                raise ValueError('手机号格式不正确，应为11位数字，以1开头')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None and v != '':
            # 标准邮箱格式
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                raise ValueError('邮箱格式不正确')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码至少8位')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('密码必须包含字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含数字')
        return v


class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class ChangePassword(BaseModel):
    old_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('新密码至少8位')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('新密码必须包含字母')
        if not re.search(r'\d', v):
            raise ValueError('新密码必须包含数字')
        return v


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


class DrawingGroupResponse(BaseModel):
    id: int
    group_id: int
    filename: str
    file_url: str
    version: str
    version_num: int
    version_count: int
    comments: Optional[str] = ""
    uploader_name: str
    created_at: str


class DrawingVersionItem(BaseModel):
    id: int
    version: str
    version_num: int
    file_url: str
    comments: Optional[str] = ""
    comment_images: Optional[str] = ""
    uploader_name: str
    created_at: str


class DrawingVersionsResponse(BaseModel):
    filename: str
    order_title: str
    group_id: int
    versions: list[DrawingVersionItem]
