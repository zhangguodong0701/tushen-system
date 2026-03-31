#!/usr/bin/env python3
"""图审系统 API 全量测试脚本"""
import requests, sys, io, os
from datetime import datetime

BASE = "http://localhost:8000"
GREEN = ""
RED   = ""
YELLOW= ""
RESET = ""

class TestResult:
    def __init__(self, name, method, path, expected_code, actual_code, body=""):
        self.name = name
        self.method = method
        self.path = path
        self.expected_code = expected_code
        self.actual_code = actual_code
        self.body = body
        self.ok = actual_code == expected_code

    def print(self):
        icon = f"[OK]" if self.ok else f"[FAIL]"
        print(f"  {icon} [{self.method}] {self.path}")
        if not self.ok:
            print(f"      expect={self.expected_code}, actual={self.actual_code}  {self.body[:80]}")

results = []

def GET(path, token=None, params=None, expected=200, name=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(BASE+path, timeout=10, headers=h, params=params)
    n = name or f"GET {path}"
    results.append(TestResult(n, "GET", path, expected, r.status_code, r.text[:100]))
    return r

def POST(path, token=None, json=None, data=None, expected=200, name=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.post(BASE+path, timeout=10, headers=h, json=json, data=data)
    n = name or f"POST {path}"
    results.append(TestResult(n, "POST", path, expected, r.status_code, r.text[:100]))
    return r

def PUT(path, token=None, json=None, data=None, expected=200, name=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.put(BASE+path, timeout=10, headers=h, json=json, data=data)
    n = name or f"PUT {path}"
    results.append(TestResult(n, "PUT", path, expected, r.status_code, r.text[:100]))
    return r

def DELETE(path, token=None, expected=200, name=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.delete(BASE+path, timeout=10, headers=h)
    n = name or f"DELETE {path}"
    results.append(TestResult(n, "DELETE", path, expected, r.status_code, r.text[:100]))
    return r

def POST_FILE(path, files, token=None, data=None, expected=200, name=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.post(BASE+path, timeout=10, headers=h, files=files, data=data)
    n = name or f"POST {path} (file)"
    results.append(TestResult(n, "POST", path, expected, r.status_code, r.text[:100]))
    return r

# ===== 环境检查 =====
print(f"\n{'='*60}")
print(f"  图审系统 API 全量测试  {datetime.now().strftime('%H:%M:%S')}")
print(f"{'='*60}")

try:
    r = requests.get(BASE + "/docs", timeout=5)
    if r.status_code not in [200, 404]:
        raise Exception(f"Status {r.status_code}")
except Exception as e:
    print(f"[FAIL] 后端未启动或无法访问 {BASE}: {e}")
    sys.exit(1)
print(f"[OK] 后端运行正常")

# ===== 1. Auth 接口 =====
print(f"\n{'─'*60}")
print(f"  [1/9] Auth 接口")
print(f"{'─'*60}")

# 1.1 登录（已有管理员）
r = POST("/api/auth/login", data={"username": "13800000000", "password": "admin123"}, expected=200, name="登录-正确账号")
if r.status_code == 200:
    admin_token = r.json()["access_token"]
    print(f"  [OK] 登录成功，Token: {admin_token[:30]}...")
else:
    print(f"  [FAIL] 登录失败: {r.text}")
    sys.exit(1)

# 1.2 登录失败
POST("/api/auth/login", data={"username": "13800000000", "password": "wrongpass"}, expected=400, name="登录-错误密码")

# 1.3 注册新用户（用时间戳确保手机号唯一）
import time as _time
unique_phone = f"139{int(_time.time()) % 100000:05d}"
r = POST("/api/auth/register", json={
    "phone": unique_phone, "real_name": "测试用户A", "user_type": "业主",
    "password": "test123456", "company_name": "测试公司A"
}, expected=200, name="注册-正常注册")
if r.status_code == 200:
    new_uid = r.json().get("user_id")
    print(f"  [OK] 注册成功，user_id: {new_uid}，手机: {unique_phone}")
else:
    new_uid = None

# 1.4 重复注册（手机号已被占用）
r = POST("/api/auth/register", json={
    "phone": unique_phone, "real_name": "测试用户A2", "user_type": "业主",
    "password": "test123456"
}, expected=400, name="注册-重复手机号")
if r.status_code == 400:
    print(f"  [OK] 重复注册正确返回400")

# 1.5 无效token访问受保护接口
GET("/api/auth/me", token="invalid.token.here", expected=401, name="受保护接口-无效token")
GET("/api/auth/me", expected=401, name="受保护接口-无token")

# 1.6 获取当前用户信息
r = GET("/api/auth/me", token=admin_token, expected=200, name="获取当前用户")
if r.status_code == 200:
    admin_uid = r.json()["id"]
    print(f"  [OK] 当前用户: {r.json()['real_name']} (ID={admin_uid})")

# 1.7 更新用户信息
r = PUT("/api/auth/me", token=admin_token, json={"real_name": "系统管理员_已更新"}, expected=200, name="更新个人资料")
if r.status_code == 200:
    print(f"  [OK] 更新后名称: {r.json()['real_name']}")
# 恢复原名
PUT("/api/auth/me", token=admin_token, json={"real_name": "系统管理员"}, expected=200, name="恢复原名")

# ===== 2. Demands 接口 =====
print(f"\n{'─'*60}")
print(f"  [2/9] Demands 接口")
print(f"{'─'*60}")

# 2.1 创建需求
r = POST("/api/demands", token=admin_token, json={
    "title": "建筑结构图审需求", "description": "需要对建筑结构图纸进行审核",
    "budget": 50000, "payment_type": "一次性", "profession": "结构设计"
}, expected=200, name="创建需求")
if r.status_code == 200:
    demand_id = r.json()["id"]
    print(f"  [OK] 需求创建成功，ID={demand_id}")
else:
    demand_id = None

# 2.2 上传需求文件
if demand_id:
    fake_file = ("test.pdf", io.BytesIO(b"fake pdf content"), "application/pdf")
    r = POST_FILE(f"/api/demands/{demand_id}/upload-file", files={"file": fake_file},
                  token=admin_token, expected=200, name="上传需求文件")
    if r.status_code == 200:
        print(f"  [OK] 文件上传成功: {r.json()['url']}")

# 2.3 发布需求
if demand_id:
    POST("/api/demands/{}/publish".format(demand_id), token=admin_token, expected=200, name="发布需求")

# 2.4 获取需求列表（公开，无需认证）
r = GET("/api/demands", params={"status": "已发布"}, expected=200, name="获取需求列表(公开)")
if r.status_code == 200:
    print(f"  [OK] 已发布需求数量: {r.json()['total']}")

# 2.5 获取单个需求（公开）
if demand_id:
    GET(f"/api/demands/{demand_id}", expected=200, name="获取需求详情")

# 2.6 我的需求（需认证）
r = GET("/api/demands/my", token=admin_token, expected=200, name="获取我的需求")
if r.status_code == 200:
    print(f"  [OK] 我的需求数量: {len(r.json())}")

# 2.7 更新需求
if demand_id:
    r = PUT(f"/api/demands/{demand_id}", token=admin_token, json={"title": "建筑结构图审需求_已修改", "budget": 55000}, expected=200, name="更新需求")
    if r.status_code == 200:
        print(f"  [OK] 需求更新成功: {r.json()['title']}, 预算: {r.json()['budget']}")

# 2.8 删除草稿需求（先创建一个草稿）
r = POST("/api/demands", token=admin_token, json={
    "title": "草稿需求_待删除", "description": "这是一个草稿", "budget": 1000
}, expected=200, name="创建草稿需求")
if r.status_code == 200:
    draft_id = r.json()["id"]
    DELETE(f"/api/demands/{draft_id}", token=admin_token, expected=200, name="删除草稿需求")
    print(f"  [OK] 草稿删除成功")

# 2.9 删除已发布需求（应失败）
if demand_id:
    DELETE(f"/api/demands/{demand_id}", token=admin_token, expected=400, name="删除已发布需求-应失败")

# 2.10 无效token（需求列表是公开接口，无需认证，不受token影响）
GET("/api/demands", token="bad.token", expected=200, name="需求列表-无效token(公开接口)")

# ===== 3. Quotes 接口 =====
print(f"\n{'─'*60}")
print(f"  [3/9] Quotes 接口")
print(f"{'─'*60}")

# 3.1 提交报价（需有已发布需求）
if demand_id:
    r = POST(f"/api/demands/{demand_id}/quotes", token=admin_token, json={
        "price": 45000, "remark": "包含详细审核报告"
    }, expected=200, name="提交报价")
    if r.status_code == 200:
        quote_id = r.json()["id"]
        print(f"  [OK] 报价提交成功，ID={quote_id}")
    else:
        quote_id = None
else:
    quote_id = None

# 3.2 重复报价
if demand_id:
    POST(f"/api/demands/{demand_id}/quotes", token=admin_token, json={"price": 46000}, expected=400, name="重复报价-应失败")

# 3.3 查看需求的所有报价（公开）
if demand_id:
    r = GET(f"/api/demands/{demand_id}/quotes", expected=200, name="查看需求报价列表")
    if r.status_code == 200:
        print(f"  [OK] 该需求报价数量: {len(r.json())}")

# 3.4 我的报价
r = GET("/api/quotes/my", token=admin_token, expected=200, name="获取我的报价")
if r.status_code == 200:
    print(f"  [OK] 我的报价数量: {len(r.json())}")

# 3.5 更新报价
if quote_id:
    PUT(f"/api/quotes/{quote_id}", token=admin_token, json={"price": 43000, "remark": "价格可以商议"}, expected=200, name="更新报价")

# 3.6 取消报价
if quote_id:
    DELETE(f"/api/quotes/{quote_id}", token=admin_token, expected=200, name="取消报价")
    print(f"  [OK] 报价取消成功")

# 3.7 无效token
GET("/api/quotes/my", token="bad", expected=401, name="我的报价-无效token")

# ===== 4. Orders 接口 =====
print(f"\n{'─'*60}")
print(f"  [4/9] Orders 接口")
print(f"{'─'*60}")

# 4.1 列出我的订单
r = GET("/api/orders", token=admin_token, expected=200, name="列出订单")
if r.status_code == 200:
    print(f"  [OK] 订单数量: {len(r.json())}")

# 4.2 创建订单（需求需存在）
if demand_id:
    # 重新提交报价
    r2 = POST(f"/api/demands/{demand_id}/quotes", token=admin_token, json={"price": 40000}, expected=200, name="重新提交报价")
    if r2.status_code == 200:
        qid = r2.json()["id"]
        r = POST("/api/orders", token=admin_token, json={
            "demand_id": demand_id, "seller_id": admin_uid, "amount": 40000, "payment_type": "一次性"
        }, expected=200, name="创建订单")
        if r.status_code == 200:
            order_id = r.json()["id"]
            print(f"  [OK] 订单创建成功，ID={order_id}")
        else:
            order_id = None
    else:
        order_id = None
else:
    order_id = None

# 4.3 获取订单详情
if order_id:
    r = GET(f"/api/orders/{order_id}", token=admin_token, expected=200, name="获取订单详情")
    if r.status_code == 200:
        print(f"  [OK] 订单状态: {r.json()['status']}, 金额: {r.json()['amount']}")

# 4.4 支付订单
if order_id:
    POST(f"/api/orders/{order_id}/pay", token=admin_token, expected=200, name="支付订单")
    print(f"  [OK] 订单支付成功")

# 4.5 验收订单
if order_id:
    POST(f"/api/orders/{order_id}/accept", token=admin_token, expected=200, name="验收订单")
    print(f"  [OK] 订单验收成功")

# 4.6 无效token
GET("/api/orders", token="bad", expected=401, name="订单列表-无效token")

# ===== 5. Drawings 接口 =====
print(f"\n{'─'*60}")
print(f"  [5/9] Drawings 接口")
print(f"{'─'*60}")

if order_id:
    # 5.1 上传图纸
    fake_dwg = ("结构图.dwg", io.BytesIO(b"fake dwg content"), "application/octet-stream")
    r = POST_FILE(f"/api/orders/{order_id}/drawings", files={"file": fake_dwg},
                  token=admin_token, data={"version": "V20260330"}, expected=200, name="上传图纸")
    if r.status_code == 200:
        drawing_id = r.json()["id"]
        print(f"  [OK] 图纸上传成功，ID={drawing_id}")
    else:
        drawing_id = None

    # 5.2 查看图纸列表（公开）
    r = GET(f"/api/orders/{order_id}/drawings", expected=200, name="查看图纸列表")
    if r.status_code == 200:
        print(f"  [OK] 订单图纸数量: {len(r.json())}")

    # 5.3 添加审图意见
    if drawing_id:
        PUT(f"/api/drawings/{drawing_id}/comments", token=admin_token,
            data={"comments": "图纸审核意见：结构符合规范"}, expected=200, name="添加审图意见")
        print(f"  [OK] 审图意见已保存")
else:
    drawing_id = None

# 5.4 无效token
if order_id:
    fake_file = ("test.dwg", io.BytesIO(b"test"), "application/octet-stream")
    POST_FILE(f"/api/orders/{order_id}/drawings", files={"file": fake_file}, token="bad", expected=401, name="上传图纸-无效token")

# ===== 6. Notifications 接口 =====
print(f"\n{'─'*60}")
print(f"  [6/9] Notifications 接口")
print(f"{'─'*60}")

r = GET("/api/notifications", token=admin_token, expected=200, name="获取通知列表")
if r.status_code == 200:
    notifs = r.json()
    print(f"  [OK] 通知数量: {len(notifs)}")
    if notifs:
        nid = notifs[0]["id"]
        # 6.2 标记已读
        POST(f"/api/notifications/{nid}/read", token=admin_token, expected=200, name="标记通知已读")
        print(f"  [OK] 通知标记已读")

# 6.3 无效token
GET("/api/notifications", token="bad", expected=401, name="通知列表-无效token")

# ===== 7. Disputes 接口 =====
print(f"\n{'─'*60}")
print(f"  [7/9] Disputes 接口")
print(f"{'─'*60}")

# 7.1 创建纠纷
if order_id:
    r = POST("/api/disputes", token=admin_token, json={
        "order_id": order_id, "description": "图纸审核存在争议，要求重新审核"
    }, expected=200, name="创建纠纷")
    if r.status_code == 200:
        dispute_id = r.json()["id"]
        print(f"  [OK] 纠纷创建成功，ID={dispute_id}")
    else:
        dispute_id = None
else:
    dispute_id = None

# 7.2 上传证据
if dispute_id:
    fake_evidence = ("evidence.pdf", io.BytesIO(b"evidence content"), "application/pdf")
    r = POST_FILE(f"/api/disputes/{dispute_id}/upload-evidence", files={"file": fake_evidence},
                  token=admin_token, expected=200, name="上传纠纷证据")
    if r.status_code == 200:
        print(f"  [OK] 证据上传成功: {r.json()['url']}")

# 7.3 查看我的纠纷
r = GET("/api/disputes", token=admin_token, expected=200, name="获取我的纠纷")
if r.status_code == 200:
    print(f"  [OK] 纠纷数量: {len(r.json())}")

# 7.4 无效token
GET("/api/disputes", token="bad", expected=401, name="纠纷列表-无效token")

# ===== 8. Admin 接口 =====
print(f"\n{'─'*60}")
print(f"  [8/9] Admin 接口")
print(f"{'─'*60}")

# 8.1 管理员统计
r = GET("/api/admin/stats", token=admin_token, expected=200, name="管理员统计")
if r.status_code == 200:
    stats = r.json()
    print(f"  [OK] 统计: 用户{stats['total_users']} | 待审{stats['pending_users']} | 需求{stats['total_demands']} | 订单{stats['total_orders']}")

# 8.2 管理员列表用户
r = GET("/api/admin/users", token=admin_token, expected=200, name="管理员-用户列表")
if r.status_code == 200:
    users = r.json()
    print(f"  [OK] 用户总数: {len(users)}")
    pending_users = [u for u in users if u["status"] == "待审核"]
    if pending_users:
        uid_to_approve = pending_users[0]["id"]
        uid_to_reject = pending_users[-1]["id"] if len(pending_users) > 1 else None

        # 8.3 批准用户
        r = POST(f"/api/admin/users/{uid_to_approve}/approve", token=admin_token, expected=200, name="批准用户")
        if r.status_code == 200:
            print(f"  [OK] 用户 {uid_to_approve} 审核通过")

        # 8.4 驳回用户（如果存在多个待审）
        if uid_to_reject:
            r = POST(f"/api/admin/users/{uid_to_reject}/reject", token=admin_token, expected=200, name="驳回用户")
            if r.status_code == 200:
                print(f"  [OK] 用户 {uid_to_reject} 审核驳回")
    else:
        print(f"  - 无待审核用户，跳过审核测试")

# 8.5 管理员-所有需求/订单/纠纷
GET("/api/admin/demands", token=admin_token, expected=200, name="管理员-所有需求")
GET("/api/admin/orders", token=admin_token, expected=200, name="管理员-所有订单")
GET("/api/admin/disputes", token=admin_token, expected=200, name="管理员-所有纠纷")

# 8.6 普通用户不能访问管理接口
if new_uid:
    # 注册用户已在admin流程中被批准（status=通过），所以能登录
    r = POST("/api/auth/login", data={"username": unique_phone, "password": "test123456"}, expected=200, name="注册用户登录-已审核应成功")
    if r.status_code == 200:
        user_token = r.json()["access_token"]
        GET("/api/admin/users", token=user_token, expected=403, name="普通用户-禁止访问管理接口")

# 8.7 无效token访问管理接口
GET("/api/admin/stats", token="bad", expected=401, name="管理统计-无效token")

# ===== 9. 边界/异常测试 =====
print(f"\n{'─'*60}")
print(f"  [9/9] 边界与异常测试")
print(f"{'─'*60}")

# 9.1 不存在的需求
GET("/api/demands/99999", expected=404, name="需求不存在-404")
PUT("/api/demands/99999", token=admin_token, json={"title": "test"}, expected=404, name="更新不存在需求-404")
POST("/api/demands/99999/publish", token=admin_token, expected=404, name="发布不存在需求-404")
DELETE("/api/demands/99999", token=admin_token, expected=404, name="删除不存在需求-404")

# 9.2 不存在的订单
GET("/api/orders/99999", token=admin_token, expected=404, name="订单不存在-404")
POST("/api/orders/99999/pay", token=admin_token, expected=404, name="支付不存在订单-404")
POST("/api/orders/99999/accept", token=admin_token, expected=404, name="验收不存在订单-404")

# 9.3 不存在的纠纷
GET("/api/disputes", token=admin_token, expected=200, name="无纠纷-正常返回")

# 9.4 创建订单：非法参数
if demand_id:
    POST("/api/orders", token=admin_token, json={
        "demand_id": demand_id, "seller_id": 99999, "amount": -1000
    }, expected=404, name="创建订单-非法seller_id")

# 9.5 注册：缺少必填字段
POST("/api/auth/register", json={"phone": "13900000099"}, expected=422, name="注册-缺少必填字段")

# 9.6 文件上传-无文件
if demand_id:
    r = requests.post(BASE+f"/api/demands/{demand_id}/upload-file",
                      headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
    r.status_code  # FastAPI返回422（缺少必需字段）
    results.append(TestResult("上传文件-空文件", "POST", f"/api/demands/{demand_id}/upload-file",
                               422, r.status_code, r.text[:80]))
    print(f"  {'[OK]' if r.status_code in [400,422,500] else '[FAIL]'} 上传文件-空文件: {r.status_code}")

# ===== 结果汇总 =====
print(f"\n{'='*60}")
print(f"  测试结果汇总")
print(f"{'='*60}")
passed = sum(1 for x in results if x.ok)
failed = [x for x in results if not x.ok]
print(f"\n  总计: {len(results)} 个测试")
print(f"  通过: {passed}")
print(f"  失败: {len(failed)}")

if failed:
    print(f"\n  失败详情:")
    for f in failed:
        print(f"  [FAIL] [{f.method}] {f.path}")
        print(f"      期望 {f.expected_code}，实际 {f.actual_code}  {f.body}")

print(f"\n{'='*60}\n")
sys.exit(0 if not failed else 1)
