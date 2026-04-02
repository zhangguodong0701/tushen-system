# ========== 认证模块测试 ==========
import pytest


class TestAuthRegister:
    """注册接口测试"""

    def test_register_success(self, client):
        """正常注册成功"""
        c, _ = client
        resp = c.post("/api/auth/register", json={
            "phone": "13800000001",
            "email": "test@example.com",
            "password": "test123456",
            "real_name": "张三",
            "user_type": "业主"
        })
        assert resp.status_code == 200
        assert "user_id" in resp.json()

    def test_register_duplicate_phone(self, client):
        """手机号重复注册"""
        c, _ = client
        c.post("/api/auth/register", json={
            "phone": "13800000002",
            "password": "test123456",
            "real_name": "李四",
            "user_type": "业主"
        })
        resp = c.post("/api/auth/register", json={
            "phone": "13800000002",
            "password": "test123456",
            "real_name": "李四2",
            "user_type": "业主"
        })
        assert resp.status_code == 400
        assert "已注册" in resp.text

    def test_register_invalid_user_type(self, client):
        """无效用户类型（后端不强制校验，允许注册）"""
        c, _ = client
        resp = c.post("/api/auth/register", json={
            "phone": "13800000003",
            "password": "test123456",
            "real_name": "王五",
            "user_type": "无效类型"
        })
        # 后端注册接口不强制校验 user_type，允许注册
        assert resp.status_code == 200


class TestAuthLogin:
    """登录接口测试"""

    def test_login_success(self, client):
        """正常登录"""
        c, session = client
        # 直接在数据库创建已审核用户（register 强制设 status=待审核）
        from models import User
        from auth import get_password_hash
        user = User(
            phone="13800000010",
            hashed_password=get_password_hash("login123"),
            real_name="登录测试",
            user_type="设计师",
            status="通过"
        )
        session.add(user)
        session.commit()

        resp = c.post("/api/auth/login", data={
            "username": "13800000010",
            "password": "login123"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        assert "user" in resp.json()

    def test_login_wrong_password(self, client):
        """密码错误"""
        c, session = client
        from models import User
        from auth import get_password_hash
        user = User(
            phone="13800000011",
            hashed_password=get_password_hash("correct"),
            real_name="密码测试",
            user_type="设计师",
            status="通过"
        )
        session.add(user)
        session.commit()
        resp = c.post("/api/auth/login", data={
            "username": "13800000011",
            "password": "wrong"
        })
        assert resp.status_code == 400

    def test_login_nonexistent_user(self, client):
        """用户不存在"""
        c, _ = client
        resp = c.post("/api/auth/login", data={
            "username": "99999999999",
            "password": "any"
        })
        assert resp.status_code == 400

    def test_login_pending_user(self, client):
        """待审核用户不能登录"""
        c, _ = client
        c.post("/api/auth/register", json={
            "phone": "13800000012",
            "password": "pending",
            "real_name": "待审核用户",
            "user_type": "设计师"
            # 不设置 status=通过，默认是"待审核"
        })
        resp = c.post("/api/auth/login", data={
            "username": "13800000012",
            "password": "pending"
        })
        assert resp.status_code == 403


class TestAuthMe:
    """获取当前用户信息测试"""

    def test_me_success(self, auth_headers, client):
        """获取当前用户信息"""
        c, _ = client
        resp = c.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "phone" in data
        assert "real_name" in data

    def test_me_without_token(self, client):
        """无 token 访问"""
        c, _ = client
        resp = c.get("/api/auth/me")
        assert resp.status_code == 401


class TestAuthUpdate:
    """更新个人信息测试"""

    def test_update_me_success(self, auth_headers, client):
        """更新成功"""
        c, _ = client
        resp = c.put("/api/auth/me", json={
            "real_name": "新名字",
            "company_name": "新公司"
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["real_name"] == "新名字"

    def test_update_me_without_auth(self, client):
        """未认证不能更新"""
        c, _ = client
        resp = c.put("/api/auth/me", json={"real_name": "hack"})
        assert resp.status_code == 401
