# ========== 图纸模块测试 ==========
import pytest
from models import Demand, Quote, Order, User
from constants import DemandStatus, OrderStatus
from auth import get_password_hash


class TestDrawingUpload:
    """图纸上传测试"""

    def _create_order(self, c, jia_headers, yi_headers):
        """辅助方法：创建并选标，返回 order_id"""
        # 创建需求
        resp = c.post("/api/demands", json={
            "title": "图纸测试需求",
            "description": "测试",
            "budget": 10000,
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
            "price": 8000
        }, headers=yi_headers)
        assert resp.status_code == 200, f"报价失败: {resp.text}"
        quote_id = resp.json()["id"]

        # 甲方选标
        resp = c.post(f"/api/demands/{demand_id}/select-winner/{quote_id}",
                       headers=jia_headers)
        assert resp.status_code == 200, f"选标失败: {resp.text}"
        order_id = resp.json().get("order_id")
        assert order_id, f"响应中无 order_id: {resp.json()}"
        return order_id

    def test_upload_drawing_success(self, jia_headers, yi_headers, client):
        """成功上传图纸"""
        c, _ = client
        order_id = self._create_order(c, jia_headers, yi_headers)

        # 上传图纸（使用 UploadFile）
        resp = c.post(
            f"/api/orders/{order_id}/drawings",
            files={"file": ("test_drawing.pdf", b"fake pdf content for test", "application/pdf")},
            headers=yi_headers
        )
        assert resp.status_code == 200, f"上传图纸失败: {resp.text}"
        assert "id" in resp.json()

    def test_upload_drawing_without_auth(self, client):
        """未登录不能上传"""
        c, _ = client
        resp = c.post("/api/orders/1/drawings", json={
            "file_url": "http://example.com/d.pdf",
            "file_name": "a.pdf"
        })
        assert resp.status_code == 401
