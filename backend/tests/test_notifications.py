# ========== 通知模块测试 ==========
import pytest


class TestNotificationList:
    """通知列表测试"""

    def test_list_notifications_success(self, jia_headers, client):
        """成功获取通知列表"""
        c, _ = client
        resp = c.get("/api/notifications", headers=jia_headers)
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_list_notifications_not_auth(self, client):
        """未认证不能访问"""
        c, _ = client
        resp = c.get("/api/notifications")
        assert resp.status_code == 401


class TestNotificationUnread:
    """未读通知测试"""

    def test_get_unread_count(self, jia_headers, client):
        """获取未读数量"""
        c, _ = client
        resp = c.get("/api/notifications/unread-count", headers=jia_headers)
        assert resp.status_code == 200
        assert "unread_count" in resp.json()
