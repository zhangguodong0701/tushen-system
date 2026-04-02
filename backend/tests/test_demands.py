# ========== 需求模块测试 ==========
import pytest


class TestDemandCreate:
    """需求创建测试"""

    def test_create_demand_success(self, jia_headers, client):
        """甲方正常创建需求"""
        c, _ = client
        resp = c.post("/api/demands", json={
            "title": "施工图审查需求",
            "description": "需要专业审图",
            "budget": 50000,
            "payment_type": "一次性",
            "profession": "施工图",
            "demand_type": "施工图审查"
        }, headers=jia_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "施工图审查需求"
        assert data["status"] == "草稿"
        assert data["budget"] == 50000

    def test_create_demand_as_yi_forbidden(self, yi_headers, client):
        """乙方不能创建需求"""
        c, _ = client
        resp = c.post("/api/demands", json={
            "title": "非法需求",
            "description": "test",
            "budget": 1000
        }, headers=yi_headers)
        assert resp.status_code == 403

    def test_create_demand_without_auth(self, client):
        """未认证不能创建"""
        c, _ = client
        resp = c.post("/api/demands", json={
            "title": "test", "description": "test", "budget": 1000
        })
        assert resp.status_code == 401


class TestDemandList:
    """需求列表测试"""

    def test_list_demands_pagination(self, jia_headers, yi_headers, client):
        """需求列表分页"""
        c, _ = client
        # 甲方创建多个需求
        for i in range(15):
            c.post("/api/demands", json={
                "title": f"需求{i}",
                "description": f"描述{i}",
                "budget": 10000 + i,
                "payment_type": "一次性"
            }, headers=jia_headers)

        # 乙方可见列表
        resp = c.get("/api/demands?page=1&page_size=10", headers=yi_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert len(data["items"]) == 10
        assert data["total"] == 15

        # 第二页
        resp2 = c.get("/api/demands?page=2&page_size=10", headers=yi_headers)
        data2 = resp2.json()
        assert len(data2["items"]) == 5

    def test_list_demands_keyword_search(self, jia_headers, client):
        """关键词搜索（标题+描述）"""
        c, _ = client
        c.post("/api/demands", json={
            "title": "消防审查项目",
            "description": "高层建筑消防",
            "budget": 80000
        }, headers=jia_headers)
        c.post("/api/demands", json={
            "title": "节能评估项目",
            "description": "绿色建筑节能",
            "budget": 30000
        }, headers=jia_headers)

        # 搜索标题
        resp = c.get("/api/demands?keyword=消防")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) >= 1

        # 搜索描述
        resp2 = c.get("/api/demands?keyword=节能")
        assert resp2.status_code == 200
        assert len(resp2.json()["items"]) >= 1

    def test_list_demands_status_filter(self, jia_headers, client):
        """状态筛选"""
        c, _ = client
        resp = c.get("/api/demands?status=草稿", headers=jia_headers)
        assert resp.status_code == 200


class TestDemandPublish:
    """需求发布测试"""

    def test_publish_demand_success(self, jia_headers, client):
        """发布需求成功"""
        c, _ = client
        # 创建
        resp = c.post("/api/demands", json={
            "title": "待发布需求",
            "description": "test",
            "budget": 10000
        }, headers=jia_headers)
        demand_id = resp.json()["id"]
        # 发布
        resp2 = c.post(f"/api/demands/{demand_id}/publish", headers=jia_headers)
        assert resp2.status_code == 200

        # 验证状态
        resp3 = c.get(f"/api/demands/{demand_id}")
        assert resp3.json()["status"] == "已发布"

    def test_delete_demand_forbidden_status(self, jia_headers, client):
        """已发布需求不允许删除"""
        c, _ = client
        resp = c.post("/api/demands", json={
            "title": "不可删除",
            "description": "test",
            "budget": 10000
        }, headers=jia_headers)
        demand_id = resp.json()["id"]
        c.post(f"/api/demands/{demand_id}/publish", headers=jia_headers)

        resp2 = c.delete(f"/api/demands/{demand_id}", headers=jia_headers)
        assert resp2.status_code == 400

    def test_delete_draft_demand_success(self, jia_headers, client):
        """草稿状态可以删除"""
        c, _ = client
        resp = c.post("/api/demands", json={
            "title": "可删除草稿",
            "description": "test",
            "budget": 10000
        }, headers=jia_headers)
        demand_id = resp.json()["id"]

        resp2 = c.delete(f"/api/demands/{demand_id}", headers=jia_headers)
        assert resp2.status_code == 200
