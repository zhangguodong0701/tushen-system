# ========== 订单模块测试 ==========
import pytest


class TestQuoteAndOrder:
    """报价和订单流程测试"""

    def test_quote_and_order_flow(self, jia_headers, yi_headers, client):
        """完整报价→选标→创建订单流程"""
        c, _ = client

        # 1. 甲方创建需求
        resp = c.post("/api/demands", json={
            "title": "完整流程测试需求",
            "description": "测试完整流程",
            "budget": 50000,
            "payment_type": "一次性"
        }, headers=jia_headers)
        demand_id = resp.json()["id"]

        # 2. 发布需求
        c.post(f"/api/demands/{demand_id}/publish", headers=jia_headers)

        # 3. 乙方报价
        resp = c.post(f"/api/demands/{demand_id}/quotes", json={
            "price": 45000,
            "remark": "含税发票"
        }, headers=yi_headers)
        assert resp.status_code == 200
        quote_id = resp.json()["id"]

        # 4. 甲方选标
        resp = c.post(f"/api/demands/{demand_id}/select-winner/{quote_id}", headers=jia_headers)
        assert resp.status_code == 200
        assert "order_id" in resp.json()
        order_id = resp.json()["order_id"]

        # 5. 验证订单已创建
        resp = c.get(f"/api/orders/{order_id}", headers=jia_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "待付款"

    def test_yi_cannot_quote_own_demand(self, jia_headers, client):
        """不能给自己发布的需求报价"""
        c, _ = client
        resp = c.post("/api/demands", json={
            "title": "自测需求",
            "description": "test",
            "budget": 10000
        }, headers=jia_headers)
        demand_id = resp.json()["id"]
        c.post(f"/api/demands/{demand_id}/publish", headers=jia_headers)

        resp = c.post(f"/api/demands/{demand_id}/quotes", json={
            "price": 8000
        }, headers=jia_headers)
        # 不能给自己报价，返回 403 Forbidden
        assert resp.status_code == 403


class TestOrderPayment:
    """订单支付测试"""

    def test_order_pay_success(self, jia_headers, yi_headers, client):
        """甲方支付成功"""
        c, _ = client

        resp = c.post("/api/demands", json={
            "title": "支付测试",
            "description": "test",
            "budget": 20000
        }, headers=jia_headers)
        demand_id = resp.json()["id"]
        c.post(f"/api/demands/{demand_id}/publish", headers=jia_headers)
        resp = c.post(f"/api/demands/{demand_id}/quotes", json={
            "price": 18000
        }, headers=yi_headers)
        quote_id = resp.json()["id"]
        resp = c.post(f"/api/demands/{demand_id}/select-winner/{quote_id}", headers=jia_headers)
        order_id = resp.json()["order_id"]

        resp = c.post(f"/api/orders/{order_id}/pay", headers=jia_headers)
        assert resp.status_code == 200

        resp = c.get(f"/api/orders/{order_id}", headers=jia_headers)
        assert resp.json()["status"] == "进行中"
        assert resp.json()["escrow_status"] == "已托管"

    def test_yi_cannot_pay(self, yi_headers, jia_headers, client):
        """乙方不能支付"""
        c, _ = client
        resp = c.post("/api/demands", json={
            "title": "乙方支付测试",
            "description": "test",
            "budget": 10000
        }, headers=jia_headers)
        demand_id = resp.json()["id"]
        c.post(f"/api/demands/{demand_id}/publish", headers=jia_headers)
        resp = c.post(f"/api/demands/{demand_id}/quotes", json={
            "price": 8000
        }, headers=yi_headers)
        quote_id = resp.json()["id"]
        resp = c.post(f"/api/demands/{demand_id}/select-winner/{quote_id}", headers=jia_headers)
        order_id = resp.json()["order_id"]
        resp = c.post(f"/api/orders/{order_id}/pay", headers=yi_headers)
        assert resp.status_code == 404


class TestOrderAccept:
    """订单验收测试"""

    def test_order_accept_and_complete(self, jia_headers, yi_headers, client):
        """甲方验收一次性订单"""
        c, _ = client
        resp = c.post("/api/demands", json={
            "title": "验收测试",
            "description": "test",
            "budget": 30000
        }, headers=jia_headers)
        demand_id = resp.json()["id"]
        c.post(f"/api/demands/{demand_id}/publish", headers=jia_headers)
        resp = c.post(f"/api/demands/{demand_id}/quotes", json={
            "price": 28000
        }, headers=yi_headers)
        quote_id = resp.json()["id"]
        resp = c.post(f"/api/demands/{demand_id}/select-winner/{quote_id}", headers=jia_headers)
        order_id = resp.json()["order_id"]
        c.post(f"/api/orders/{order_id}/pay", headers=jia_headers)

        resp = c.post(f"/api/orders/{order_id}/accept", headers=jia_headers)
        assert resp.status_code == 200
        resp = c.get(f"/api/orders/{order_id}", headers=jia_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "已完成"


class TestOrderPagination:
    """订单分页测试"""

    def test_orders_pagination(self, jia_headers, yi_headers, client):
        """订单列表分页"""
        c, _ = client
        for i in range(5):
            resp = c.post("/api/demands", json={
                "title": f"分页需求{i}",
                "description": "test",
                "budget": 10000 + i
            }, headers=jia_headers)
            demand_id = resp.json()["id"]
            c.post(f"/api/demands/{demand_id}/publish", headers=jia_headers)
            resp = c.post(f"/api/demands/{demand_id}/quotes", json={
                "price": 9000 + i
            }, headers=yi_headers)
            c.post(f"/api/demands/{demand_id}/select-winner/{resp.json()['id']}", headers=jia_headers)

        resp = c.get("/api/orders?page=1&page_size=3", headers=jia_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert len(data["items"]) == 3
