# ========== 管理员模块测试 ==========
import pytest


class TestAdminUserList:
    """管理员查看用户列表测试"""

    def test_list_users_success(self, admin_headers, client):
        """管理员成功获取用户列表"""
        c, _ = client
        resp = c.get("/api/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_list_users_not_admin(self, jia_headers, client):
        """非管理员不能访问"""
        c, _ = client
        resp = c.get("/api/admin/users", headers=jia_headers)
        assert resp.status_code == 403


class TestAdminApproveUser:
    """审核通过测试"""

    def test_approve_user_success(self, admin_headers, client):
        """管理员成功审核通过"""
        c, session = client
        from models import User
        from auth import get_password_hash

        user = User(
            phone="13800008888",
            email="approve@test.com",
            hashed_password=get_password_hash("test1234"),
            real_name="待审核用户",
            user_type="owner",
            status="待审核"
        )
        session.add(user)
        session.commit()

        resp = c.post(f"/api/admin/users/{user.id}/approve", headers=admin_headers)
        assert resp.status_code == 200
        assert "审核通过" in resp.json()["message"]

        # 验证数据库
        session.refresh(user)
        assert user.status == "通过"


class TestAdminStats:
    """统计面板测试"""

    def test_get_stats_success(self, admin_headers, client):
        """管理员成功获取统计"""
        c, _ = client
        resp = c.get("/api/admin/stats", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_users" in data
        assert "total_demands" in data
        assert "total_orders" in data
