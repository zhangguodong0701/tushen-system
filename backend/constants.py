# backend/constants.py - 全局状态常量枚举
# 前后端统一引用此处，禁止硬编码状态字符串
from enum import Enum


class UserStatus(str, Enum):
    pending = "待审核"          # 已提交，等待审核
    approved = "通过"
    rejected = "已驳回"


class DemandStatus(str, Enum):
    draft = "草稿"
    published = "已发布"
    in_progress = "进行中"
    completed = "已完成"
    closed = "已关闭"


class QuoteStatus(str, Enum):
    pending = "待选标"    # 待甲方选择
    accepted = "中标"     # 已中标（被甲方选中）
    rejected = "未中标"    # 未中标（其他报价方）


class OrderStatus(str, Enum):
    pending_payment = "待付款"
    in_progress = "进行中"
    pending_review = "待验收"   # 甲方确认，等待验收
    completed = "已完成"
    refunded = "已退款"


class PhaseStatus(str, Enum):
    pending_review = "待验收"
    completed = "已验收"        # 阶段验收完成


class DisputeStatus(str, Enum):
    open = "处理中"
    resolved = "已解决"
    closed = "已关闭"


class FeedbackStatus(str, Enum):
    pending = "待处理"
    resolved = "已处理"
