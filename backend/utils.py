# utils.py - 共享工具函数
from sqlalchemy.orm import Session
from fastapi import UploadFile
from typing import Optional
import json
import random
import string
from datetime import datetime


# ========== 流水号生成 ==========
def generate_serial_number(prefix: str) -> str:
    """生成统一格式流水号：PREFIX-YYYYMMDD-XXXX（4位随机大写字母+数字）
    
    示例：D-20260415-A3K9、O-20260415-7X2M、J-20260415-P9L3
    """
    date_part = datetime.utcnow().strftime("%Y%m%d")
    chars = string.ascii_uppercase + string.digits  # 0-9, A-Z
    # 去除易混淆字符：0, 1, O, I（数字0/1 与字母O/I 易混淆）
    chars = chars.replace('I', '').replace('O', '').replace('0', '').replace('1', '')
    random_part = ''.join(random.choices(chars, k=4))
    return f"{prefix}-{date_part}-{random_part}"


# ========== 分页辅助 ==========
def paginate_query(q, page: int, page_size: int):
    """通用分页：返回 {total, page, page_size, items}"""
    total = q.count()
    items = q.order_by().offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


# ========== 序列化函数 ==========
def user_to_dict(u):
    # 根据 user_type 判断角色（兼容甲乙方）
    if u.user_type in JIA_FANG_TYPES:
        role = "甲方"
    elif u.user_type in YI_FANG_TYPES:
        role = "乙方"
    else:
        role = u.user_type or ""
    return {
        "id": u.id,
        "serial_number": getattr(u, 'serial_number', None) or "",
        "phone": u.phone, "email": u.email,
        "real_name": u.real_name, "user_type": u.user_type,
        "role": role,  # 添加 role 字段
        "status": u.status, "is_admin": u.is_admin,
        "is_reviewer": u.is_reviewer,
        "company_name": u.company_name, "license_url": u.license_url,
        "cert_url": u.cert_url, "avatar": u.avatar,
        "auth_type": u.auth_type or "",
        "is_blacklisted": u.is_blacklisted,
        "id_card_front": u.id_card_front or "",
        "id_card_back": u.id_card_back or "",
        "business_license": u.business_license or "",
        "created_at": u.created_at.isoformat() if u.created_at else None
    }


def demand_to_dict(d):
    return {
        "id": d.id,
        "serial_number": getattr(d, 'serial_number', None) or "",
        "title": d.title, "description": d.description,
        "budget": d.budget,
        "budget_min": getattr(d, 'budget_min', None),
        "budget_max": getattr(d, 'budget_max', None),
        "payment_type": d.payment_type,
        "payment_phases": json.loads(d.payment_phases) if d.payment_phases else None,
        "status": d.status, "profession": d.profession,
        "demand_type": d.demand_type, "file_url": d.file_url,
        "owner_id": d.owner_id, "deadline": getattr(d, 'deadline', None),
        "chosen_quote_id": getattr(d, 'chosen_quote_id', None),
        "owner_name": d.owner.real_name if d.owner else "",
        "created_at": str(d.created_at),
        "updated_at": str(d.updated_at),
        "quote_count": len(d.quotes) if d.quotes else 0
    }


def order_to_dict(o):
    return {
        "id": o.id,
        "serial_number": getattr(o, 'serial_number', None) or "",
        "demand_id": o.demand_id,
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


# ========== 通知类型提取 ==========
def extract_notification_type(title: str) -> str:
    if not title:
        return "系统通知"
    if "报价" in title:
        return "报价通知"
    if "订单" in title or "支付" in title or "验收" in title or "托管" in title:
        return "订单状态变更"
    if "纠纷" in title or "仲裁" in title:
        return "纠纷通知"
    if "资金" in title or "到账" in title or "退款" in title:
        return "资金变动"
    return "系统通知"


# ========== 角色判断辅助 ==========
JIA_FANG_TYPES = ['业主', '建设单位', '项目方']
YI_FANG_TYPES = ['设计院', '设计师', '材料商', '设备商']


def is_jia_fang(user) -> bool:
    if user.is_admin == 1 or user.is_reviewer == 1:
        return False
    return user.user_type in JIA_FANG_TYPES


def is_yi_fang(user) -> bool:
    if user.is_admin == 1 or user.is_reviewer == 1:
        return False
    return user.user_type in YI_FANG_TYPES
