# ========== 纠纷模块测试 ==========
import pytest
from models import Demand, Quote, Order, Dispute, User
from constants import DemandStatus, OrderStatus, DisputeStatus
from auth import get_password_hash


class TestDisputeCreate:
    """发起纠纷测试"""

    def _setup_order(self, c, jia_headers, yi_headers):
        """辅助方法：完整走通流程，返回 order_id"""
        # 创建需求
        resp = c.post("/api/demands", json={
            "title": "纠纷测试需求",
            "description": "测试纠纷流程",
            "budget": 5000,
            "profession": "土建",
            "payment_type": "一次性"
        }, headers=jia_headers)
        assert resp.status_code == 200, f"创建需求失败: {resp.text}"
        demand_id = resp.json()["id"]

        # 发布需求
        resp = c.post(f"/api/demands/{demand_id}/publish", headers=jia_headers)
        assert resp.status_code == 200

        # 乙方报价
        resp = c.post(f"/api/demands/{demand_id}/quotes", json={
            "price": 4000
        }, headers=yi_headers)
        assert resp.status_code == 200, f"报价失败: {resp.text}"
        quote_id = resp.json()["id"]

        # 甲方选标（后端自动创建订单，状态：待付款）
        resp = c.post(f"/api/demands/{demand_id}/select-winner/{quote_id}",
                       headers=jia_headers)
        assert resp.status_code == 200, f"选标失败: {resp.text}"
        order_id = resp.json().get("order_id")
        assert order_id, f"响应中无 order_id: {resp.json()}"
        return order_id

    def test_create_dispute_success(self, jia_headers, yi_headers, client):
        """甲方成功发起纠纷（需先付款使订单进入进行中）"""
        c, session = client
        order_id = self._setup_order(c, jia_headers, yi_headers)

        # 甲方付款，订单状态变为 进行中
        from models import Order
        from constants import OrderStatus
        order = session.query(Order).filter(Order.id == order_id).first()
        order.status = OrderStatus.in_progress.value
        session.commit()

        # 甲方发起纠纷
        resp = c.post("/api/disputes", json={
            "order_id": order_id,
            "reason": "图纸质量不合格",
            "description": "图纸与需求严重不符，要求退款"
        }, headers=jia_headers)
        assert resp.status_code == 200, f"发起纠纷失败: {resp.text}"
        assert "id" in resp.json()

    def test_create_dispute_without_auth(self, client):
        """未登录不能发起纠纷"""
        c, _ = client
        resp = c.post("/api/disputes", json={
            "order_id": 1,
            "reason": "test"
        })
        assert resp.status_code == 401
