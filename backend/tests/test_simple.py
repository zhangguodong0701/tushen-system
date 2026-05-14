# ========== 简单测试 ==========
import pytest


class TestBasic:
    """基本功能测试"""

    def test_auth_me_success(self, jia_headers, client):
        """获取当前用户信息"""
        c, _ = client
        resp = c.get("/api/auth/me", headers=jia_headers)
        assert resp.status_code == 200
