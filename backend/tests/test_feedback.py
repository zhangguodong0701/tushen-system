# ========== 反馈模块测试 ==========
import pytest
from models import Feedback
from routers.feedback import FeedbackCreate


class TestFeedbackCreate:
    """提交反馈测试"""

    def test_create_feedback_success(self, jia_headers, client):
        """成功提交反馈（内容不能包含'测试'等关键字）"""
        c, _ = client
        resp = c.post("/api/feedback", json={
            "content": "希望增加订单导出Excel功能，方便财务对账，请考虑添加"
        }, headers=jia_headers)
        assert resp.status_code == 200, f"提交失败: {resp.text}"
        assert "提交" in resp.json()["message"]
        assert "id" in resp.json()

    def test_create_feedback_too_short(self, jia_headers, client):
        """反馈内容太短"""
        c, _ = client
        resp = c.post("/api/feedback", json={
            "content": "短"
        }, headers=jia_headers)
        assert resp.status_code == 400
        assert "5个" in resp.text

    def test_create_feedback_without_token(self, client):
        """未登录不能提交"""
        c, _ = client
        resp = c.post("/api/feedback", json={
            "content": "希望增加导出功能"
        })
        assert resp.status_code == 401


class TestFeedbackList:
    """查看反馈列表测试"""

    def test_list_feedback_success(self, jia_headers, client):
        """成功查看我的反馈"""
        c, _ = client
        resp = c.get("/api/feedback", headers=jia_headers)
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_list_feedback_without_token(self, client):
        """未登录不能查看"""
        c, _ = client
        resp = c.get("/api/feedback")
        assert resp.status_code == 401
