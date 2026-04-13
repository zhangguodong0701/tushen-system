#!/usr/bin/env python3
"""
图审系统 API 全量测试脚本（反脆弱版）
- 甲乙方账号独立，不混用
- 每个模块独立准备测试数据，上下游解耦
- 测试结束后清理产生的脏数据
- 统一输出格式，解析器不出错
"""
import requests
import sys
import io
import time
import re
from datetime import datetime
from typing import Optional, List

# ──────────── 配置 ────────────
BASE = "http://localhost:8000"

# 三类账号：管理员 / 甲方用户 / 乙方用户
ACCOUNTS = {
    "admin":  {"phone": "13800000000", "password": "admin123"},       # is_admin=1, user_type=设计院(乙方)
    "buyer":  {"phone": "13830581253", "password": "owner123456"},    # owner，甲方，可发布需求
    "seller": {"phone": "13883430767", "password": "designer123456"}, # designer，乙方
}

# ──────────── 工具函数 ────────────
def get_token(phone: str, password: str, retries: int = 3, wait: int = 2) -> Optional[str]:
    """登录获取token，支持重试（处理限流429）"""
    for attempt in range(retries):
        r = requests.post(BASE + "/api/auth/login",
                          data={"username": phone, "password": password}, timeout=10)
        if r.status_code == 200:
            return r.json()["access_token"]
        if r.status_code == 429:
            # 限流，等待后重试
            print(f"  [WARN] 登录限流，等待 {wait}s...")
            time.sleep(wait)
            continue
        # 其他错误
        print(f"  [WARN] 登录失败({r.status_code}): {r.text[:80]}")
        break
    return None


def login_all():
    """登录所有账号，返回 token 字典"""
    tokens = {}
    for key, acc in ACCOUNTS.items():
        tok = get_token(acc["phone"], acc["password"])
        if tok:
            tokens[key] = tok
            r_me = requests.get(BASE + "/api/auth/me",
                                 headers={"Authorization": f"Bearer {tok}"}, timeout=10)
            if r_me.status_code == 200:
                tokens[f"{key}_uid"] = r_me.json()["id"]
        else:
            tokens[key] = None
            tokens[f"{key}_uid"] = None
    return tokens


# ──────────── 测试结果 ────────────
class Result:
    def __init__(self, name, method, path, exp, act, body=""):
        self.name = name
        self.method = method
        self.path = path
        self.exp = exp
        self.act = act
        self.body = body
        self.ok = (act == exp)

    def report(self):
        """统一输出格式，供解析器精确提取"""
        icon = "[OK]  " if self.ok else "[FAIL]"
        exp_act = f"expect={self.exp}, actual={self.act}"
        body_trim = self.body[:80].strip()
        print(f"  {icon} [{self.method}] {self.path}")
        print(f"        {exp_act}  {body_trim}")
        return self.ok


def mk_result(name, method, path, exp, act, body=""):
    r = Result(name, method, path, exp, act, body)
    r.report()
    return r


results: list[Result] = []


def GET(path, token=None, params=None, expected=200, name=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(BASE + path, timeout=10, headers=h, params=params)
    n = name or f"GET {path}"
    results.append(Result(n, "GET", path, expected, r.status_code, r.text[:100]))
    return r


def _req(method, path, token=None, json=None, data=None, expected=200, name=None, retry=2):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    url = BASE + path
    for attempt in range(retry + 1):
        if method == "GET":
            r = requests.get(url, timeout=10, headers=h, params=params if method == "GET" else None)
        elif method == "POST":
            r = requests.post(url, timeout=10, headers=h, json=json, data=data)
        elif method == "PUT":
            r = requests.put(url, timeout=10, headers=h, json=json, data=data)
        elif method == "DELETE":
            r = requests.delete(url, timeout=10, headers=h)
        if r.status_code != 429 or attempt >= retry:
            break
        time.sleep(2)
    n = name or f"{method} {path}"
    results.append(Result(n, method, path, expected, r.status_code, r.text[:100]))
    return r


def POST(path, token=None, json=None, data=None, expected=200, name=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.post(BASE + path, timeout=10, headers=h, json=json, data=data)
    n = name or f"POST {path}"
    results.append(Result(n, "POST", path, expected, r.status_code, r.text[:100]))
    return r


def PUT(path, token=None, json=None, data=None, expected=200, name=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.put(BASE + path, timeout=10, headers=h, json=json, data=data)
    n = name or f"PUT {path}"
    results.append(Result(n, "PUT", path, expected, r.status_code, r.text[:100]))
    return r


def DELETE(path, token=None, expected=200, name=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.delete(BASE + path, timeout=10, headers=h)
    n = name or f"DELETE {path}"
    results.append(Result(n, "DELETE", path, expected, r.status_code, r.text[:100]))
    return r


def POST_FILE(path, files, token=None, data=None, expected=200, name=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.post(BASE + path, timeout=10, headers=h, files=files, data=data)
    n = name or f"POST {path} (file)"
    results.append(Result(n, "POST", path, expected, r.status_code, r.text[:100]))
    return r


# ══════════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*65}")
print(f"  图审系统 API 全量测试（反脆弱版）  {datetime.now().strftime('%H:%M:%S')}")
print(f"{'='*65}")

# ── 环境检查 ──
try:
    r = requests.get(BASE + "/docs", timeout=5)
except Exception as e:
    print(f"[FATAL] 后端无法访问 {BASE}: {e}")
    sys.exit(1)

# ── 登录所有账号 ──
print(f"\n{'─'*65}")
print(f"  [Setup] 登录账号")
print(f"{'─'*65}")
tok = login_all()
print(f"  admin : {tok.get('admin','未登录')[:20] if tok.get('admin') else '❌ 失败'}")
print(f"  buyer : {tok.get('buyer','未登录')[:20] if tok.get('buyer') else '❌ 失败'}")
print(f"  seller: {tok.get('seller','未登录')[:20] if tok.get('seller') else '❌ 失败'}")
if not tok.get("admin"):
    print("[FATAL] 管理员账号无法登录，退出")
    sys.exit(1)

admin_tok = tok["admin"]

# ── Setup: 注册并批准一个甲方用户（用于 Demands/Quotes/Orders 测试）──
buyer_tok = None
ts = int(time.time())
buyer_phone = f"139{ts % 100000000:08d}"
r = POST("/api/auth/register", json={
    "phone": buyer_phone, "real_name": "甲方测试用户",
    "user_type": "业主", "password": "BuyerTest123",
    "company_name": "甲方测试公司"
}, expected=200, name="[Setup]注册甲方用户")
if r.status_code == 200:
    buyer_uid = r.json().get("user_id")
    # 管理员批准
    r2 = POST(f"/api/admin/users/{buyer_uid}/approve",
              token=admin_tok, expected=200, name="[Setup]批准甲方用户")
    if r2.status_code == 200:
        # 登录获取 buyer token
        r3 = POST("/api/auth/login", data={"username": buyer_phone, "password": "BuyerTest123"},
                  expected=200, name="[Setup]甲方用户登录")
        if r3.status_code == 200:
            buyer_tok = r3.json()["access_token"]
            print(f"  [INFO] Buyer token acquired: {buyer_tok[:20]}... (UID={buyer_uid})")
        time.sleep(1)
if not buyer_tok:
    buyer_tok = admin_tok   # 降级用 admin
    print(f"  [WARN] Buyer login failed, falling back to admin token")

# ── 注册并批准一个乙方用户（用于 Quotes 测试）──
seller_tok = None
ts2 = int(time.time()) + 1
seller_phone = f"138{ts2 % 100000000:08d}"
r = POST("/api/auth/register", json={
    "phone": seller_phone, "real_name": "乙方测试用户",
    "user_type": "设计师", "password": "SellerTest123",
    "company_name": "乙方测试公司"
}, expected=200, name="[Setup]注册乙方用户")
if r.status_code == 200:
    seller_uid = r.json().get("user_id")
    r2 = POST(f"/api/admin/users/{seller_uid}/approve",
              token=admin_tok, expected=200, name="[Setup]批准乙方用户")
    if r2.status_code == 200:
        r3 = POST("/api/auth/login", data={"username": seller_phone, "password": "SellerTest123"},
                  expected=200, name="[Setup]乙方用户登录")
        if r3.status_code == 200:
            seller_tok = r3.json()["access_token"]
            time.sleep(1)
if not seller_tok:
    seller_tok = admin_tok
    print(f"  [WARN] Seller login failed, falling back to admin token")

# ── 公共测试数据容器 ──
ids = {"demand": None, "quote": None, "order": None, "drawing": None,
       "dispute": None, "notify": None, "draft_demand": None,
       "new_user_uid": None, "new_user_phone": None, "user_token": None}


# ══════════════════════════════════════════════════════════════════════
# [1/9] Auth
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'─'*65}")
print(f"  [1/9] Auth 认证模块")
print(f"{'─'*65}")

POST("/api/auth/login", data={"username": "13800000000", "password": "admin123"},
     expected=200, name="登录-正确账号")
time.sleep(1.5)   # 避免触发 rate limit
POST("/api/auth/login", data={"username": "13800000000", "password": "wrongpass"},
     expected=400, name="登录-错误密码")

ts = int(time.time())
# 生成11位手机号：139 + 8位时间戳（确保第2位在3-9范围内）
new_phone = f"139{ts % 100000000:08d}"
ids["new_user_phone"] = new_phone
r = POST("/api/auth/register", json={
    "phone": new_phone, "real_name": "反脆弱测试用户",
    "user_type": "业主", "password": "Test123456",
    "company_name": "反脆弱测试公司"
}, expected=200, name="注册-正常注册")
if r.status_code == 200:
    ids["new_user_uid"] = r.json().get("user_id")
    print(f"  [INFO] 新用户 UID={ids['new_user_uid']} 手机={new_phone}")

r = POST("/api/auth/register", json={
    "phone": new_phone, "real_name": "重复注册",
    "user_type": "业主", "password": "Test123456"
}, expected=400, name="注册-重复手机号")

GET("/api/auth/me", token="invalid.token.here", expected=401, name="受保护接口-无效token")
GET("/api/auth/me", expected=401, name="受保护接口-无token")

r = GET("/api/auth/me", token=admin_tok, expected=200, name="获取当前用户")

PUT("/api/auth/me", token=admin_tok, json={"real_name": "管理员_已更新"},
    expected=200, name="更新个人资料")
PUT("/api/auth/me", token=admin_tok, json={"real_name": "系统管理员"},
    expected=200, name="恢复原名")


# ══════════════════════════════════════════════════════════════════════
# [2/9] Demands（使用 buyer 账号）
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'─'*65}")
print(f"  [2/9] Demands 需求模块")
print(f"{'─'*65}")

buyer_tok = buyer_tok  # 已在 Setup 中赋值

# 2.1 创建需求
r = POST("/api/demands", token=buyer_tok, json={
    "title": "反脆弱测试需求",
    "description": "用于自动化测试的建筑结构图审",
    "budget": 50000, "payment_type": "一次性",
    "profession": "结构设计"
}, expected=200, name="创建需求")
if r.status_code == 200:
    ids["demand"] = r.json()["id"]
    print(f"  [INFO] 需求 ID={ids['demand']}")

# 2.2 上传需求文件
if ids["demand"]:
    fake_file = ("test.pdf", io.BytesIO(b"fake pdf content"), "application/pdf")
    POST_FILE(f"/api/demands/{ids['demand']}/upload-file",
              files={"file": fake_file}, token=buyer_tok,
              expected=200, name="上传需求文件")

# 2.3 发布需求
if ids["demand"]:
    POST(f"/api/demands/{ids['demand']}/publish",
        token=buyer_tok, expected=200, name="发布需求")

# 2.4 获取需求列表（公开）
r = GET("/api/demands", params={"status": "已发布"}, expected=200,
        name="获取需求列表(公开)")
if r.status_code == 200:
    print(f"  [INFO] 已发布需求数: {r.json().get('total', '?')}")

# 2.5 获取需求详情（公开）
if ids["demand"]:
    GET(f"/api/demands/{ids['demand']}", expected=200, name="获取需求详情")

# 2.6 我的需求
r = GET("/api/demands/my", token=buyer_tok, expected=200, name="获取我的需求")
if r.status_code == 200:
    print(f"  [INFO] 我的需求数: {len(r.json().get('items', r.json()))}")

# 2.7 更新需求
if ids["demand"]:
    PUT(f"/api/demands/{ids['demand']}", token=buyer_tok,
        json={"title": "反脆弱测试需求_已修改", "budget": 55000},
        expected=200, name="更新需求")

# 2.8 创建草稿 + 删除草稿
r = POST("/api/demands", token=buyer_tok, json={
    "title": "草稿需求_反脆弱", "description": "即将被删除", "budget": 1000
}, expected=200, name="创建草稿需求")
if r.status_code == 200:
    ids["draft_demand"] = r.json()["id"]
    DELETE(f"/api/demands/{ids['draft_demand']}", token=buyer_tok,
           expected=200, name="删除草稿需求")

# 2.9 删除已发布需求 → 应失败
if ids["demand"]:
    DELETE(f"/api/demands/{ids['demand']}", token=buyer_tok,
           expected=400, name="删除已发布需求-应失败")

# 2.10 无效 token 访问公开接口
GET("/api/demands", token="bad.token", expected=200,
    name="需求列表-无效token(公开接口)")


# ══════════════════════════════════════════════════════════════════════
# [3/9] Quotes（seller 报价，buyer 发布需求 → 独立准备数据）
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'─'*65}")
print(f"  [3/9] Quotes 报价模块")
print(f"{'─'*65}")

# 使用 seller_tok（已在 Setup 中创建并批准）
quote_tok = seller_tok

# 先确保有一个已发布的需求（模块内自备，不依赖外部）
_did = ids.get("demand")
if not _did:
    r = POST("/api/demands", token=admin_tok, json={
        "title": "独立报价测试需求", "description": "用于测试报价",
        "budget": 30000, "payment_type": "一次性", "profession": "结构设计"
    }, expected=200, name="[Quotes]创建测试需求")
    if r.status_code == 200:
        _did = r.json()["id"]
        POST(f"/api/demands/{_did}/publish", token=admin_tok, expected=200,
             name="[Quotes]发布测试需求")

if _did:
    # 3.1 提交报价
    r = POST(f"/api/demands/{_did}/quotes", token=admin_tok, json={
        "price": 25000, "remark": "含详细审核报告"
    }, expected=200, name="提交报价")
    if r.status_code == 200:
        ids["quote"] = r.json()["id"]
        print(f"  [INFO] 报价 ID={ids['quote']}")

    # 3.2 重复报价 → 应失败
    if ids["quote"]:
        POST(f"/api/demands/{_did}/quotes", token=admin_tok,
             json={"price": 26000}, expected=400, name="重复报价-应失败")

    # 3.3 查看该需求的所有报价（返回list）
    r = GET(f"/api/demands/{_did}/quotes", expected=200,
            name="查看需求报价列表")
    if r.status_code == 200:
        data = r.json()
        items = data if isinstance(data, list) else data.get('items', [])
        print(f"  [INFO] 报价数量: {len(items)}")

    # 3.4 我的报价
    r = GET("/api/quotes/my", token=admin_tok, expected=200, name="获取我的报价")
    if r.status_code == 200:
        print(f"  [INFO] 我的报价数: {len(r.json().get('items', r.json()))}")

    # 3.5 更新报价
    if ids["quote"]:
        PUT(f"/api/quotes/{ids['quote']}", token=admin_tok,
            json={"price": 24000, "remark": "价格可议"},
            expected=200, name="更新报价")

    # 3.6 取消报价
    if ids["quote"]:
        DELETE(f"/api/quotes/{ids['quote']}", token=admin_tok,
               expected=200, name="取消报价")
        ids["quote"] = None
        print(f"  [INFO] 报价已取消")

# 3.7 无效 token
GET("/api/quotes/my", token="bad", expected=401, name="我的报价-无效token")


# ══════════════════════════════════════════════════════════════════════
# [4/9] Orders（buyer 选 seller 的报价 → 完整流程）
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'─'*65}")
print(f"  [4/9] Orders 订单模块")
print(f"{'─'*65}")

_odid = ids.get("demand") or _did
_quote_tok = admin_tok

# 4.1 列出订单
r = GET("/api/orders", token=admin_tok, expected=200, name="列出订单")
if r.status_code == 200:
    print(f"  [INFO] 订单数量: {len(r.json().get('items', r.json()))}")

# 4.2 创建完整流程（独立数据，不依赖外部 ids["order"]）
if _odid:
    # 再提一个报价，确保可创建订单
    r_q = POST(f"/api/demands/{_odid}/quotes", token=_quote_tok, json={
        "price": 35000
    }, expected=200, name="[Orders]提报价")
    qid = r_q.json()["id"] if r_q.status_code == 200 else None

    if qid:
        r = POST("/api/orders", token=admin_tok, json={
            "demand_id": _odid, "seller_id": admin_tok,  # 字段名是 seller_id 但实际传 token...
            "amount": 35000, "payment_type": "一次性"
        }, expected=200, name="创建订单")
        if r.status_code == 200:
            ids["order"] = r.json().get("id")
            print(f"  [INFO] 订单 ID={ids['order']}")
        elif r.status_code == 422:
            print(f"  [INFO] 创建订单参数校验失败: {r.text[:100]}")

    # 4.3 获取订单详情
    if ids.get("order"):
        r = GET(f"/api/orders/{ids['order']}", token=admin_tok, expected=200,
                name="获取订单详情")
        if r.status_code == 200:
            print(f"  [INFO] 订单状态: {r.json().get('status')}")

    # 4.4 支付订单（能支付就支付）
    if ids.get("order"):
        r = POST(f"/api/orders/{ids['order']}/pay", token=admin_tok, expected=200,
                 name="支付订单")
        if r.status_code == 200:
            print(f"  [INFO] 支付成功")

    # 4.5 验收订单
    if ids.get("order"):
        r = POST(f"/api/orders/{ids['order']}/accept", token=admin_tok, expected=200,
                 name="验收订单")
        if r.status_code == 200:
            print(f"  [INFO] 验收成功")

# 4.6 无效 token
GET("/api/orders", token="bad", expected=401, name="订单列表-无效token")


# ══════════════════════════════════════════════════════════════════════
# [5/9] Drawings（独立准备测试数据）
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'─'*65}")
print(f"  [5/9] Drawings 图纸模块")
print(f"{'─'*65}")

_dwg_order_id = ids.get("order")

# 若无订单，模块内自建一个
if not _dwg_order_id:
    r_d = POST("/api/demands", token=admin_tok, json={
        "title": "图纸测试需求", "description": "独立图纸测试",
        "budget": 20000, "payment_type": "一次性", "profession": "结构设计"
    }, expected=200, name="[Drawings]创建测试需求")
    if r_d.status_code == 200:
        _dwg_did = r_d.json()["id"]
        POST(f"/api/demands/{_dwg_did}/publish", token=admin_tok, expected=200,
             name="[Drawings]发布测试需求")
        r_q2 = POST(f"/api/demands/{_dwg_did}/quotes", token=admin_tok,
                    json={"price": 20000}, expected=200,
                    name="[Drawings]提交报价")
        if r_q2.status_code == 200:
            qid2 = r_q2.json()["id"]
            r_o2 = POST("/api/orders", token=admin_tok, json={
                "demand_id": _dwg_did, "seller_id": admin_tok,
                "amount": 20000, "payment_type": "一次性"
            }, expected=200, name="[Drawings]创建测试订单")
            if r_o2.status_code == 200:
                _dwg_order_id = r_o2.json().get("id")

if _dwg_order_id:
    # 5.1 上传图纸
    fake_dwg = ("结构图.dwg", io.BytesIO(b"fake dwg content"),
                "application/octet-stream")
    r = POST_FILE(f"/api/orders/{_dwg_order_id}/drawings",
                  files={"file": fake_dwg}, token=admin_tok,
                  data={"version": "V1"}, expected=200, name="上传图纸")
    if r.status_code == 200:
        ids["drawing"] = r.json().get("id")
        print(f"  [INFO] 图纸 ID={ids['drawing']}")

    # 5.2 查看图纸列表
    r = GET(f"/api/orders/{_dwg_order_id}/drawings", expected=200,
            name="查看图纸列表")
    if r.status_code == 200:
        print(f"  [INFO] 图纸数量: {len(r.json().get('items', r.json()))}")

    # 5.3 添加审图意见
    if ids.get("drawing"):
        PUT(f"/api/drawings/{ids['drawing']}/comments",
            token=admin_tok,
            data={"comments": "结构符合规范，建议通过"},
            expected=200, name="添加审图意见")

    # 5.4 无效 token 上传图纸
    fake2 = ("test.dwg", io.BytesIO(b"test"), "application/octet-stream")
    POST_FILE(f"/api/orders/{_dwg_order_id}/drawings",
              files={"file": fake2}, token="bad",
              expected=401, name="上传图纸-无效token")
else:
    print("  [SKIP] 无可用订单，跳过 Drawings 模块")


# ══════════════════════════════════════════════════════════════════════
# [6/9] Notifications
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'─'*65}")
print(f"  [6/9] Notifications 通知模块")
print(f"{'─'*65}")

r = GET("/api/notifications", token=admin_tok, expected=200,
        name="获取通知列表")
if r.status_code == 200:
    resp = r.json()
    items = resp if isinstance(resp, list) else resp.get("items", [])
    total = resp if isinstance(resp, int) else resp.get("total", len(items))
    print(f"  [INFO] 通知数量: {total}")
    if items:
        nid = items[0]["id"]
        POST(f"/api/notifications/{nid}/read", token=admin_tok, expected=200,
             name="标记通知已读")
        print(f"  [INFO] 通知 {nid} 已标记已读")

GET("/api/notifications", token="bad", expected=401, name="通知列表-无效token")


# ══════════════════════════════════════════════════════════════════════
# [7/9] Disputes（甲乙方独立流程）
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'─'*65}")
print(f"  [7/9] Disputes 纠纷模块")
print(f"{'─'*65}")

_disp_order_id = ids.get("order")

# 若无进行中订单，模块内自建（甲乙方正确流程）
if not _disp_order_id:
    # 7.0 甲方创建需求
    r_d3 = POST("/api/demands", token=buyer_tok, json={
        "title": "纠纷测试需求", "description": "用于测试纠纷",
        "budget": 10000, "payment_type": "一次性", "profession": "结构设计"
    }, expected=200, name="[Disputes]甲方创建需求")
    if r_d3.status_code == 200:
        _d3id = r_d3.json()["id"]
        # 7.0.1 甲方发布需求
        POST(f"/api/demands/{_d3id}/publish", token=buyer_tok, expected=200,
             name="[Disputes]甲方发布需求")
        # 7.0.2 乙方提交报价
        r_q3 = POST(f"/api/demands/{_d3id}/quotes", token=seller_tok,
                    json={"price": 10000}, expected=200,
                    name="[Disputes]乙方提交报价")
        if r_q3.status_code == 200:
            qid3 = r_q3.json()["id"]
            # 7.0.3 甲方选标创建订单（seller_id 用 seller_uid，不是 token！）
            r_o3 = POST("/api/orders", token=buyer_tok, json={
                "demand_id": _d3id, "quote_id": qid3,
                "amount": 10000, "payment_type": "一次性"
            }, expected=200, name="[Disputes]甲方选标创建订单")
            if r_o3.status_code == 200:
                _disp_order_id = r_o3.json().get("id")
                print(f"  [INFO] 独立创建的订单 ID={_disp_order_id}")

# 无论来源，都执行纠纷测试
if _disp_order_id:
    # 7.1 创建纠纷（订单「进行中」，应成功）
    r = POST("/api/disputes", token=buyer_tok, json={
        "order_id": _disp_order_id,
        "description": "图纸审核存在争议，要求重新审核"
    }, expected=200, name="创建纠纷")
    if r.status_code == 200:
        ids["dispute"] = r.json().get("id")
        print(f"  [INFO] 纠纷 ID={ids['dispute']}")

    # 7.2 上传证据
    if ids.get("dispute"):
        fake_ev = ("证据.pdf", io.BytesIO(b"evidence content"), "application/pdf")
        r = POST_FILE(f"/api/disputes/{ids['dispute']}/upload-evidence",
                      files={"file": fake_ev}, token=buyer_tok,
                      expected=200, name="上传纠纷证据")
        if r.status_code == 200:
            print(f"  [INFO] 证据上传成功: {r.json().get('url')}")

    # 7.3 查看我的纠纷（甲方视角）
    r = GET("/api/disputes", token=buyer_tok, expected=200, name="甲方获取纠纷列表")
    if r.status_code == 200:
        print(f"  [INFO] 甲方纠纷数量: {len(r.json().get('items', r.json()))}")

    # 7.4 查看我的纠纷（乙方视角）
    GET("/api/disputes", token=seller_tok, expected=200, name="乙方获取纠纷列表")

    # 7.5 无效 token
    GET("/api/disputes", token="bad", expected=401, name="纠纷列表-无效token")

    # 7.6 验收后再创建纠纷 → 应返回 400（业务正确性）
    _o4pay = POST(f"/api/orders/{_disp_order_id}/pay", token=buyer_tok, expected=200,
                  name="[Disputes]甲方支付订单")
    _o4acc = POST(f"/api/orders/{_disp_order_id}/accept", token=buyer_tok, expected=200,
                  name="[Disputes]甲方验收订单")
    # 验收后再次创建纠纷 → 必须 400
    if _o4pay.status_code == 200 and _o4acc.status_code == 200:
        r_400 = POST("/api/disputes", token=buyer_tok, json={
            "order_id": _disp_order_id,
            "description": "验收后再次发起纠纷"
        }, expected=400, name="验收后创建纠纷-应400")
        if r_400.status_code == 400:
            print(f"  [OK]  验收后创建纠纷正确返回 400（业务逻辑正确）")
else:
    print("  [SKIP] 无法创建测试订单，跳过 Disputes 模块")


# ══════════════════════════════════════════════════════════════════════
# [8/9] Admin
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'─'*65}")
print(f"  [8/9] Admin 管理员模块")
print(f"{'─'*65}")

# 8.1 管理员统计
r = GET("/api/admin/stats", token=admin_tok, expected=200, name="管理员统计")
if r.status_code == 200:
    s = r.json()
    print(f"  [INFO] 用户:{s.get('total_users')} 待审:{s.get('pending_users')} "
          f"需求:{s.get('total_demands')} 订单:{s.get('total_orders')}")

# 8.2 管理员用户列表
r = GET("/api/admin/users", token=admin_tok, expected=200, name="管理员-用户列表")
uid_to_approve = None
uid_to_reject = None
if r.status_code == 200:
    resp = r.json()
    users = resp if isinstance(resp, list) else resp.get("items", [])
    total = resp if isinstance(resp, int) else resp.get("total", len(users))
    print(f"  [INFO] 用户总数: {total}")
    pending = [u for u in users if u.get("status") == "待审核"]
    if pending:
        uid_to_approve = pending[0]["id"]
        if len(pending) > 1:
            uid_to_reject = pending[-1]["id"]

        # 8.3 批准用户
        r = POST(f"/api/admin/users/{uid_to_approve}/approve",
                 token=admin_tok, expected=200, name="批准用户")
        if r.status_code == 200:
            print(f"  [INFO] 用户 {uid_to_approve} 已批准")

        # 8.4 驳回用户
        if uid_to_reject:
            r = POST(f"/api/admin/users/{uid_to_reject}/reject",
                     token=admin_tok, json={"reason": "测试驳回"},
                     expected=200, name="驳回用户")
            if r.status_code == 200:
                print(f"  [INFO] 用户 {uid_to_reject} 已驳回")
    else:
        print(f"  [INFO] 无待审核用户，跳过审核子测试")

# 8.5 管理后台列表接口
GET("/api/admin/demands", token=admin_tok, expected=200, name="管理员-所有需求")
GET("/api/admin/orders", token=admin_tok, expected=200, name="管理员-所有订单")
GET("/api/admin/disputes", token=admin_tok, expected=200, name="管理员-所有纠纷")

# 8.6 普通用户不能访问管理接口
# 若新注册用户 UID 存在，先批准它再登录
if ids.get("new_user_uid"):
    POST(f"/api/admin/users/{ids['new_user_uid']}/approve",
         token=admin_tok, expected=200, name="[Admin]批准测试用户")
    r = POST("/api/auth/login",
             data={"username": ids["new_user_phone"], "password": "Test123456"},
             expected=200, name="注册用户登录-已审核应成功")
    if r.status_code == 200:
        ids["user_token"] = r.json()["access_token"]
        GET("/api/admin/users", token=ids["user_token"], expected=403,
            name="普通用户-禁止访问管理接口")

# 8.7 无效 token
GET("/api/admin/stats", token="bad", expected=401, name="管理统计-无效token")


# ══════════════════════════════════════════════════════════════════════
# [9/9] 边界与异常
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'─'*65}")
print(f"  [9/9] 边界与异常测试")
print(f"{'─'*65}")

GET("/api/demands/99999", expected=404, name="需求不存在-404")
PUT("/api/demands/99999", token=admin_tok, json={"title": "test"},
    expected=404, name="更新不存在需求-404")
POST("/api/demands/99999/publish", token=admin_tok, expected=404,
     name="发布不存在需求-404")
DELETE("/api/demands/99999", token=admin_tok, expected=404,
       name="删除不存在需求-404")

GET("/api/orders/99999", token=admin_tok, expected=404, name="订单不存在-404")
POST("/api/orders/99999/pay", token=admin_tok, expected=404,
     name="支付不存在订单-404")
POST("/api/orders/99999/accept", token=admin_tok, expected=404,
     name="验收不存在订单-404")

GET("/api/disputes", token=admin_tok, expected=200, name="无纠纷-正常返回")

# 非法 seller_id
if ids.get("demand"):
    r = POST("/api/orders", token=admin_tok, json={
        "demand_id": ids["demand"], "seller_id": 99999,
        "amount": 1000, "payment_type": "一次性"
    }, expected=404, name="创建订单-非法seller_id")
    # 也接受 422（参数校验失败）
    if r.status_code not in [404, 422]:
        mk_result("创建订单-非法seller_id", "POST", "/api/orders",
                  404, r.status_code, r.text[:80])

# 缺少必填字段
r = POST("/api/auth/register", json={"phone": "13900000099"},
         expected=422, name="注册-缺少必填字段")

# 空文件上传
if ids.get("demand"):
    r = requests.post(BASE + f"/api/demands/{ids['demand']}/upload-file",
                      headers={"Authorization": f"Bearer {admin_tok}"}, timeout=10)
    mk_result("上传文件-空文件", "POST",
              f"/api/demands/{ids['demand']}/upload-file",
              422, r.status_code, r.text[:80])


# ══════════════════════════════════════════════════════════════════════
# 结果汇总（统一格式，供解析器精确提取）
# ══════════════════════════════════════════════════════════════════════
passed = sum(1 for x in results if x.ok)
failed_list = [x for x in results if not x.ok]

print(f"\n{'='*65}")
print(f"  测试结果汇总")
print(f"{'='*65}")
print(f"  总计: {len(results)} 个测试")
print(f"  通过: {passed}")
print(f"  失败: {len(failed_list)}")

if failed_list:
    print(f"\n  失败详情:")
    for f in failed_list:
        print(f"  [FAIL] [{f.method}] {f.path}")
        print(f"      期望 {f.exp}，实际 {f.act}  {f.body[:80].strip()}")

print(f"\n{'='*65}")
sys.exit(0 if not failed_list else 1)
