#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图审系统 - 全量 API 测试脚本 v2.0
覆盖后端全部 56 个端点，含权限防护、边界异常、业务流程验证
运行方式: python tushen-system/test_full.py
"""
import sys, io, time, random, json
from io import BytesIO

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import requests

BASE = "http://127.0.0.1:8000"

# ============================================================
# 基础工具
# ============================================================

_pass = 0
_fail = 0
_skip = 0
_fail_list = []


def ok(name):
    global _pass
    _pass += 1
    print(f"  [PASS] {name}")


def fail(name, detail=""):
    global _fail
    _fail += 1
    _fail_list.append((name, detail))
    print(f"  [FAIL] {name}  →  {detail[:120]}")


def skip(name, reason=""):
    global _skip
    _skip += 1
    print(f"  [SKIP] {name}  ({reason})")


def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


def api(path):
    return BASE + path


def h(token):
    return {"Authorization": f"Bearer {token}"} if token else {}


def get(path, token=None, params=None, expect=200, name=None):
    r = requests.get(api(path), headers=h(token), params=params, timeout=10)
    _check(name or f"GET {path}", r, expect)
    return r


def post(path, token=None, json_data=None, data=None, params=None, expect=200, name=None):
    r = requests.post(api(path), headers=h(token), json=json_data, data=data, params=params, timeout=10)
    _check(name or f"POST {path}", r, expect)
    return r


def put(path, token=None, json_data=None, data=None, expect=200, name=None):
    r = requests.put(api(path), headers=h(token), json=json_data, data=data, timeout=10)
    _check(name or f"PUT {path}", r, expect)
    return r


def delete(path, token=None, expect=200, name=None):
    r = requests.delete(api(path), headers=h(token), timeout=10)
    _check(name or f"DELETE {path}", r, expect)
    return r


def post_file(path, files, token=None, data=None, expect=200, name=None):
    r = requests.post(api(path), headers=h(token), files=files, data=data, timeout=10)
    _check(name or f"POST {path}(file)", r, expect)
    return r


def _check(name, r, expect):
    if r.status_code == expect:
        ok(name)
    else:
        fail(name, f"期望{expect} 实际{r.status_code} | {r.text[:100]}")


def rand_phone():
    ts = str(int(time.time()))[-7:]
    return f"139{ts}{random.randint(10,99)}"


def rand_email():
    return f"t_{int(time.time())}_{random.randint(1000,9999)}@test.com"


def fake_file(name="test.pdf", content=b"%PDF test", ctype="application/pdf"):
    return (name, BytesIO(content), ctype)


# ============================================================
# 环境检查
# ============================================================

print(f"\n{'='*60}")
print(f"  图审系统 全量 API 测试 v2.0")
print(f"{'='*60}")
try:
    r = requests.get(BASE + "/docs", timeout=5)
    if r.status_code not in (200, 404):
        raise Exception(f"status={r.status_code}")
    print(f"[OK] 后端运行正常 ({BASE})")
except Exception as e:
    print(f"[FAIL] 后端未启动: {e}")
    sys.exit(1)

# ============================================================
# 全局状态（token / id 传递）
# ============================================================
admin_token = None
reviewer_token = None
buyer_token = None   # 甲方
seller_token = None  # 乙方
buyer_id = None
seller_id = None
demand_id = None
quote_id = None
order_id = None
drawing_id = None
dispute_id = None
phase_id = None
feedback_id = None
notif_id = None
draft_demand_id = None

# ============================================================
# 1. Auth 接口
# ============================================================
section("[1/11] Auth 接口")

# 1.1 管理员登录
r = post("/api/auth/login", data={"username": "13800000000", "password": "admin123"},
         name="管理员登录-正确")
if r.status_code == 200:
    admin_token = r.json()["access_token"]
else:
    print("[FATAL] 管理员登录失败，无法继续测试")
    sys.exit(1)

# 1.2 审核员登录
r = post("/api/auth/login", data={"username": "13900000000", "password": "reviewer123"},
         name="审核员登录-正确")
if r.status_code == 200:
    reviewer_token = r.json()["access_token"]

# 1.3 登录-错误密码
post("/api/auth/login", data={"username": "13800000000", "password": "wrong"},
     expect=400, name="登录-错误密码应返回400")

# 1.4 注册甲方用户
buyer_phone = rand_phone()
r = post("/api/auth/register", json_data={
    "phone": buyer_phone, "password": "test123456",
    "real_name": "甲方测试", "user_type": "业主", "company_name": "甲方公司"
}, name="注册甲方用户")
if r.status_code == 200:
    buyer_id_new = r.json().get("user_id")
    # 管理员审核通过
    requests.post(api(f"/api/admin/users/{buyer_id_new}/approve"), headers=h(admin_token))
    # 甲方登录
    r2 = post("/api/auth/login", data={"username": buyer_phone, "password": "test123456"},
              name="甲方登录")
    if r2.status_code == 200:
        buyer_token = r2.json()["access_token"]
        buyer_id = r2.json()["user"]["id"]

# 1.5 注册乙方用户
seller_phone = rand_phone()
r = post("/api/auth/register", json_data={
    "phone": seller_phone, "password": "test123456",
    "real_name": "乙方测试", "user_type": "设计院", "company_name": "乙方公司"
}, name="注册乙方用户")
if r.status_code == 200:
    seller_id_new = r.json().get("user_id")
    requests.post(api(f"/api/admin/users/{seller_id_new}/approve"), headers=h(admin_token))
    r2 = post("/api/auth/login", data={"username": seller_phone, "password": "test123456"},
              name="乙方登录")
    if r2.status_code == 200:
        seller_token = r2.json()["access_token"]
        seller_id = r2.json()["user"]["id"]

# 1.6 重复注册手机号
post("/api/auth/register", json_data={
    "phone": buyer_phone, "password": "test123456",
    "real_name": "重复", "user_type": "业主"
}, expect=400, name="注册-重复手机号应返回400")

# 1.7 无效 Token 访问受保护接口
get("/api/auth/me", token="bad.token", expect=401, name="无效Token访问受保护接口应返回401")
get("/api/auth/me", expect=401, name="无Token访问受保护接口应返回401")

# 1.8 获取当前用户信息
r = get("/api/auth/me", token=buyer_token, name="获取当前用户信息")
if r.status_code == 200:
    print(f"       当前用户: {r.json()['real_name']} ({r.json()['user_type']})")

# 1.9 更新个人资料
r = put("/api/auth/me", token=buyer_token,
        json_data={"real_name": "甲方_已更新", "company_name": "甲方公司_已更新"},
        name="更新个人资料")
put("/api/auth/me", token=buyer_token, json_data={"real_name": "甲方测试"}, name="恢复原名")

# 1.10 上传证件
post_file("/api/auth/upload-cert",
          files={"file": fake_file("id_front.jpg", b"\xff\xd8\xff test", "image/jpeg")},
          data={"cert_type": "id_card_front"},
          token=buyer_token,
          name="上传身份证正面")

post_file("/api/auth/upload-cert",
          files={"file": fake_file("id_back.jpg", b"\xff\xd8\xff test", "image/jpeg")},
          data={"cert_type": "id_card_back"},
          token=buyer_token,
          name="上传身份证反面")

post_file("/api/auth/upload-cert",
          files={"file": fake_file("license.jpg", b"\xff\xd8\xff test", "image/jpeg")},
          data={"cert_type": "business_license"},
          token=seller_token,
          name="上传营业执照(乙方)")

# 1.11 提交实名认证
# 个人认证需要身份证正反面，企业认证需要营业执照
# 先更新甲方auth_type为个人
put("/api/auth/me", token=buyer_token, json_data={"real_name": "甲方测试"}, name="确认auth_type")
post("/api/auth/certification", token=buyer_token, name="提交实名认证(甲方个人)")

# ============================================================
# 2. Demands 接口
# ============================================================
section("[2/11] Demands 接口")

if not buyer_token:
    skip("需求全部测试", "甲方token缺失")
else:
    # 2.1 甲方创建需求（草稿）
    r = post("/api/demands", token=buyer_token, json_data={
        "title": f"图纸审核需求_{int(time.time())}",
        "description": "建筑结构图纸审核，需要有资质的设计院",
        "budget": 50000.0, "payment_type": "一次性",
        "profession": "结构设计", "demand_type": "施工图审查"
    }, name="甲方创建需求(草稿)")
    if r.status_code == 200:
        demand_id = r.json()["id"]
        print(f"       需求ID: {demand_id}")

    # 2.2 乙方不能创建需求（角色权限）
    post("/api/demands", token=seller_token, json_data={
        "title": "非法需求", "description": "测试", "budget": 1000
    }, expect=403, name="乙方创建需求应返回403(权限拦截)")

    # 2.3 创建草稿需求（待删除）
    r = post("/api/demands", token=buyer_token, json_data={
        "title": "草稿待删除", "description": "将被删除", "budget": 100
    }, name="创建草稿需求(待删除)")
    if r.status_code == 200:
        draft_demand_id = r.json()["id"]

    # 2.4 编辑草稿需求
    if demand_id:
        put(f"/api/demands/{demand_id}", token=buyer_token,
            json_data={"title": f"图纸审核需求_已编辑_{int(time.time())}", "budget": 55000},
            name="编辑草稿需求")

    # 2.5 上传需求附件
    if demand_id:
        post_file(f"/api/demands/{demand_id}/upload-file",
                  files={"file": fake_file("spec.pdf")},
                  token=buyer_token,
                  name="上传需求附件")

    # 2.6 发布需求
    if demand_id:
        post(f"/api/demands/{demand_id}/publish", token=buyer_token, name="发布需求")

    # 2.7 发布后不能再编辑
    if demand_id:
        put(f"/api/demands/{demand_id}", token=buyer_token,
            json_data={"title": "非法编辑"}, expect=400,
            name="已发布需求不能编辑应返回400")

    # 2.8 公开需求列表（无需认证）
    r = get("/api/demands", params={"status": "已发布"}, name="公开需求列表")
    if r.status_code == 200:
        print(f"       已发布需求数: {r.json()['total']}")

    # 2.9 按关键词/专业/预算筛选
    get("/api/demands", params={"keyword": "图纸", "profession": "结构设计"},
        name="需求列表-关键词+专业筛选")
    get("/api/demands", params={"min_budget": 1000, "max_budget": 100000},
        name="需求列表-预算范围筛选")
    get("/api/demands", params={"page": 1, "page_size": 5},
        name="需求列表-分页")

    # 2.10 获取单条需求详情
    if demand_id:
        get(f"/api/demands/{demand_id}", name="获取需求详情")

    # 2.11 我的需求列表
    r = get("/api/demands/my", token=buyer_token, name="获取我的需求列表")
    if r.status_code == 200:
        print(f"       我的需求数: {len(r.json())}")

    # 2.12 不存在的需求
    get("/api/demands/99999", expect=404, name="获取不存在需求应返回404")

    # 2.13 甲方关闭已发布需求（无中标时才能关闭）
    # 先创建一个专门用来关闭的需求
    r = post("/api/demands", token=buyer_token, json_data={
        "title": "待关闭需求", "description": "测试关闭", "budget": 100
    }, name="创建待关闭需求")
    if r.status_code == 200:
        close_demand_id = r.json()["id"]
        post(f"/api/demands/{close_demand_id}/publish", token=buyer_token, name="发布待关闭需求")
        post(f"/api/demands/{close_demand_id}/close", token=buyer_token, name="甲方关闭已发布需求")

    # 2.14 删除草稿需求
    if draft_demand_id:
        delete(f"/api/demands/{draft_demand_id}", token=buyer_token, name="删除草稿需求")

    # 2.15 删除已发布需求应失败
    if demand_id:
        delete(f"/api/demands/{demand_id}", token=buyer_token, expect=400,
               name="删除已发布需求应返回400")

# ============================================================
# 3. Quotes 接口
# ============================================================
section("[3/11] Quotes 接口")

if not seller_token or not demand_id:
    skip("报价全部测试", "乙方token或需求ID缺失")
else:
    # 3.1 甲方不能报价（角色权限）
    post(f"/api/demands/{demand_id}/quotes", token=buyer_token,
         json_data={"price": 10000}, expect=403,
         name="甲方报价应返回403(权限拦截)")

    # 3.2 乙方报价
    r = post(f"/api/demands/{demand_id}/quotes", token=seller_token,
             json_data={"price": 45000.0, "remark": "包含详细审核报告，资质齐全"},
             name="乙方提交报价")
    if r.status_code == 200:
        quote_id = r.json()["id"]
        print(f"       报价ID: {quote_id}")

    # 3.3 重复报价
    post(f"/api/demands/{demand_id}/quotes", token=seller_token,
         json_data={"price": 46000}, expect=400,
         name="重复报价应返回400")

    # 3.4 查看需求报价列表（公开）
    r = get(f"/api/demands/{demand_id}/quotes", name="查看需求报价列表(公开)")
    if r.status_code == 200:
        print(f"       报价数: {len(r.json())}")

    # 3.5 我的报价列表
    r = get("/api/quotes/my", token=seller_token, name="获取我的报价列表")
    if r.status_code == 200:
        print(f"       我的报价数: {len(r.json())}")

    # 3.6 更新报价
    if quote_id:
        put(f"/api/quotes/{quote_id}", token=seller_token,
            json_data={"price": 43000.0, "remark": "价格调整，更有竞争力"},
            name="更新报价价格")

    # 3.7 选中标（甲方）
    if quote_id:
        r = post(f"/api/demands/{demand_id}/select-winner/{quote_id}",
                 token=buyer_token, name="甲方选定中标方")
        if r.status_code == 200:
            order_id = r.json().get("order_id")
            print(f"       自动创建订单ID: {order_id}")

    # 3.8 中标后再更新报价应失败
    if quote_id:
        put(f"/api/quotes/{quote_id}", token=seller_token,
            json_data={"price": 99999}, expect=400,
            name="中标后修改报价应返回400")

    # 3.9 中标后再取消报价应失败
    if quote_id:
        delete(f"/api/quotes/{quote_id}", token=seller_token, expect=400,
               name="中标后取消报价应返回400")

    # 3.10 无效token获取报价
    get("/api/quotes/my", token="bad", expect=401, name="无效Token获取我的报价应返回401")

# ============================================================
# 4. Orders 接口
# ============================================================
section("[4/11] Orders 接口")

if not buyer_token or not order_id:
    skip("订单全部测试", "buyer_token或order_id缺失")
else:
    # 4.1 获取订单列表
    r = get("/api/orders", token=buyer_token, name="甲方获取订单列表")
    if r.status_code == 200:
        print(f"       甲方订单数: {len(r.json())}")

    r = get("/api/orders", token=seller_token, name="乙方获取订单列表")
    if r.status_code == 200:
        print(f"       乙方订单数: {len(r.json())}")

    # 4.2 获取订单详情（参与方）
    get(f"/api/orders/{order_id}", token=buyer_token, name="甲方获取订单详情")
    get(f"/api/orders/{order_id}", token=seller_token, name="乙方获取订单详情")

    # 4.3 非参与方不能查看订单详情
    # 创建另一个无关用户
    other_phone = rand_phone()
    r = post("/api/auth/register", json_data={
        "phone": other_phone, "password": "test123456",
        "real_name": "无关用户", "user_type": "业主"
    }, name="注册无关用户")
    if r.status_code == 200:
        other_id = r.json().get("user_id")
        requests.post(api(f"/api/admin/users/{other_id}/approve"), headers=h(admin_token))
        r2 = post("/api/auth/login", data={"username": other_phone, "password": "test123456"},
                  name="无关用户登录")
        if r2.status_code == 200:
            other_token = r2.json()["access_token"]
            get(f"/api/orders/{order_id}", token=other_token, expect=403,
                name="非参与方查看订单详情应返回403")

    # 4.4 获取不存在订单
    get("/api/orders/99999", token=buyer_token, expect=404, name="获取不存在订单应返回404")

    # 4.5 支付订单（甲方）
    post(f"/api/orders/{order_id}/pay", token=buyer_token, name="甲方支付订单(资金托管)")

    # 4.6 重复支付应失败
    post(f"/api/orders/{order_id}/pay", token=buyer_token, expect=400,
         name="重复支付订单应返回400")

    # 4.7 付款阶段管理（先查一次）
    get(f"/api/orders/{order_id}/phases", token=buyer_token, name="查看订单付款阶段列表")

    # 4.8 手动添加付款阶段（此订单为一次性，但接口允许）
    r = post(f"/api/orders/{order_id}/phases", token=buyer_token,
             json_data={"name": "交付阶段", "amount": 20000, "ratio": 40},
             name="甲方添加付款阶段")
    if r.status_code == 200:
        phase_id = r.json()["id"]
        print(f"       阶段ID: {phase_id}")

    # 4.9 乙方不能添加付款阶段
    post(f"/api/orders/{order_id}/phases", token=seller_token,
         json_data={"name": "非法阶段", "amount": 1000, "ratio": 10},
         expect=403, name="乙方添加付款阶段应返回403")

    # 4.10 验收某一付款阶段
    if phase_id:
        post(f"/api/phases/{phase_id}/complete", token=buyer_token,
             name="甲方验收某一付款阶段")
        # 重复验收应失败
        post(f"/api/phases/{phase_id}/complete", token=buyer_token,
             expect=400, name="重复验收阶段应返回400")

    # 4.11 乙方不能验收阶段
    if phase_id:
        post(f"/api/phases/{phase_id}/complete", token=seller_token,
             expect=403, name="乙方验收阶段应返回403")

    # 4.12 验收整个订单
    post(f"/api/orders/{order_id}/accept", token=buyer_token, name="甲方验收整个订单")

    # 4.13 已完成订单不能再支付/验收
    post(f"/api/orders/{order_id}/pay", token=buyer_token, expect=400,
         name="已完成订单再支付应返回400")

    # 4.14 无效token
    get("/api/orders", token="bad", expect=401, name="无效Token获取订单列表应返回401")

# ============================================================
# 5. Drawings 接口
# ============================================================
section("[5/11] Drawings 接口")

if not seller_token or not order_id:
    skip("图纸全部测试", "seller_token或order_id缺失")
else:
    # 5.1 乙方上传图纸（自动版本号）
    r = post_file(f"/api/orders/{order_id}/drawings",
                  files={"file": fake_file("结构图V1.dwg", b"DWG content", "application/octet-stream")},
                  token=seller_token,
                  name="乙方上传图纸(自动版本号)")
    if r.status_code == 200:
        drawing_id = r.json()["id"]
        print(f"       图纸ID: {drawing_id}, 版本: {r.json()['version']}")

    # 5.2 再次上传图纸，版本号自动递增
    r2 = post_file(f"/api/orders/{order_id}/drawings",
                   files={"file": fake_file("结构图V2.dwg", b"DWG v2 content", "application/octet-stream")},
                   token=seller_token,
                   name="上传第二张图纸-版本号自动递增")
    if r2.status_code == 200:
        v = r2.json()["version"]
        print(f"       第二张版本号: {v}")
        if v == "V2":
            ok("版本号自动递增验证(V2)")
        else:
            fail("版本号自动递增验证", f"期望V2，实际{v}")

    # 5.3 甲方不能上传图纸
    post_file(f"/api/orders/{order_id}/drawings",
              files={"file": fake_file("非法上传.pdf")},
              token=buyer_token, expect=403,
              name="甲方上传图纸应返回403(权限拦截)")

    # 5.4 查看订单图纸列表（公开）
    r = get(f"/api/orders/{order_id}/drawings", name="查看订单图纸列表(公开)")
    if r.status_code == 200:
        print(f"       图纸数: {len(r.json())}")

    # 5.5 获取我的所有图纸
    r = get("/api/drawings", token=seller_token, name="乙方获取我的所有图纸")
    if r.status_code == 200:
        print(f"       我的图纸总数: {len(r.json())}")

    r = get("/api/drawings", token=buyer_token, name="甲方获取我的所有图纸")

    # 5.6 甲方上传意见图片
    if drawing_id:
        r = post_file(f"/api/drawings/{drawing_id}/upload-comment-img",
                      files={"file": fake_file("意见批注.jpg", b"\xff\xd8\xff test", "image/jpeg")},
                      token=buyer_token,
                      name="甲方上传图纸意见图片")
        comment_img_url = r.json().get("url", "") if r.status_code == 200 else ""

        # 乙方不能上传意见图片
        post_file(f"/api/drawings/{drawing_id}/upload-comment-img",
                  files={"file": fake_file("非法.jpg", b"\xff\xd8\xff test", "image/jpeg")},
                  token=seller_token, expect=403,
                  name="乙方上传意见图片应返回403")

        # 5.7 甲方提交审图意见（含图片URL）
        put(f"/api/drawings/{drawing_id}/comments", token=buyer_token,
            data={"comments": "节点设计符合规范，但钢筋配置需调整",
                  "comment_images": comment_img_url},
            name="甲方提交审图意见")

        # 乙方不能提交意见
        put(f"/api/drawings/{drawing_id}/comments", token=seller_token,
            data={"comments": "非法意见"}, expect=403,
            name="乙方提交审图意见应返回403")

    # 5.8 无效token上传图纸
    post_file(f"/api/orders/{order_id}/drawings",
              files={"file": fake_file()}, token="bad", expect=401,
              name="无效Token上传图纸应返回401")

# ============================================================
# 6. Notifications 接口
# ============================================================
section("[6/11] Notifications 接口")

# 6.1 获取通知列表
r = get("/api/notifications", token=buyer_token, name="甲方获取通知列表")
if r.status_code == 200:
    notifs = r.json()
    print(f"       甲方通知数: {len(notifs)}")
    if notifs:
        notif_id = notifs[0]["id"]

r = get("/api/notifications", token=seller_token, name="乙方获取通知列表")
if r.status_code == 200:
    print(f"       乙方通知数: {len(r.json())}")

# 6.2 标记单条通知已读
if notif_id:
    post(f"/api/notifications/{notif_id}/read", token=buyer_token, name="标记单条通知已读")

# 6.3 一键全部标记已读
post("/api/notifications/mark-all-read", token=buyer_token, name="一键全部标记已读")

# 6.4 审核员通知
if reviewer_token:
    get("/api/notifications", token=reviewer_token, name="审核员获取通知列表")

# 6.5 无效token
get("/api/notifications", token="bad", expect=401, name="无效Token获取通知应返回401")

# ============================================================
# 7. Disputes 接口
# ============================================================
section("[7/11] Disputes 接口")

# 7.1 需要在进行中/待验收的订单上发起纠纷
# 先创建新的完整链路：需求→报价→选标→支付（不验收）
if buyer_token and seller_token:
    # 创建新需求
    r = post("/api/demands", token=buyer_token, json_data={
        "title": f"纠纷测试需求_{int(time.time())}",
        "description": "专门用于纠纷测试",
        "budget": 8000.0, "payment_type": "一次性"
    }, name="纠纷测试-创建需求")
    dispute_demand_id = r.json().get("id") if r.status_code == 200 else None

    if dispute_demand_id:
        post(f"/api/demands/{dispute_demand_id}/publish", token=buyer_token,
             name="纠纷测试-发布需求")
        r = post(f"/api/demands/{dispute_demand_id}/quotes", token=seller_token,
                 json_data={"price": 7000, "remark": "纠纷测试报价"},
                 name="纠纷测试-乙方报价")
        dispute_quote_id = r.json().get("id") if r.status_code == 200 else None

        if dispute_quote_id:
            r = post(f"/api/demands/{dispute_demand_id}/select-winner/{dispute_quote_id}",
                     token=buyer_token, name="纠纷测试-选定中标")
            dispute_order_id = r.json().get("order_id") if r.status_code == 200 else None

            if dispute_order_id:
                # 支付，让订单变为"进行中"
                post(f"/api/orders/{dispute_order_id}/pay", token=buyer_token,
                     name="纠纷测试-支付订单")

                # 7.2 发起纠纷
                r = post("/api/disputes", token=buyer_token,
                         json_data={"order_id": dispute_order_id,
                                    "description": "乙方迟迟不交付图纸，违约"},
                         name="甲方发起纠纷")
                if r.status_code == 200:
                    dispute_id = r.json()["id"]
                    print(f"       纠纷ID: {dispute_id}")

                # 7.3 重复发起纠纷应失败
                post("/api/disputes", token=buyer_token,
                     json_data={"order_id": dispute_order_id, "description": "重复纠纷"},
                     expect=400, name="重复发起纠纷应返回400")

                # 7.4 非参与方不能发起纠纷（用admin）
                post("/api/disputes", token=admin_token,
                     json_data={"order_id": dispute_order_id, "description": "非法纠纷"},
                     expect=403, name="非参与方发起纠纷应返回403")

                # 7.5 上传单证据
                if dispute_id:
                    r = post_file(f"/api/disputes/{dispute_id}/upload-evidence",
                                  files={"file": fake_file("证据1.pdf")},
                                  token=buyer_token,
                                  name="甲方上传纠纷证据(单文件)")
                    if r.status_code == 200:
                        print(f"       证据URL: {r.json()['url'][:40]}...")

                    # 7.6 上传多证据（追加）
                    post_file(f"/api/disputes/{dispute_id}/evidence-multiple",
                              files={"file": fake_file("证据2.jpg", b"\xff\xd8\xff", "image/jpeg")},
                              token=buyer_token,
                              name="上传多证据-追加第1张")

                    post_file(f"/api/disputes/{dispute_id}/evidence-multiple",
                              files={"file": fake_file("证据3.pdf")},
                              token=seller_token,
                              name="乙方也能上传多证据-追加第2张")

                    # 7.7 查看证据列表
                    r = get(f"/api/disputes/{dispute_id}/evidence-files",
                            token=buyer_token, name="查看纠纷证据列表(参与方)")
                    if r.status_code == 200:
                        print(f"       证据文件数: {len(r.json())}")

                    # 非参与方不能查看证据
                    get(f"/api/disputes/{dispute_id}/evidence-files",
                        token=admin_token, name="管理员查看纠纷证据列表")

                    # 无效token不能查看
                    get(f"/api/disputes/{dispute_id}/evidence-files",
                        token="bad", expect=401, name="无效Token查看证据应返回401")

# 7.8 获取我的纠纷列表
r = get("/api/disputes", token=buyer_token, name="获取我的纠纷列表")
if r.status_code == 200:
    print(f"       我的纠纷数: {len(r.json())}")

# 7.9 无效token
get("/api/disputes", token="bad", expect=401, name="无效Token获取纠纷列表应返回401")

# ============================================================
# 8. Admin 接口
# ============================================================
section("[8/11] Admin 接口")

# 8.1 统计数据
r = get("/api/admin/stats", token=admin_token, name="管理员获取统计数据")
if r.status_code == 200:
    s = r.json()
    print(f"       用户:{s['total_users']} | 需求:{s['total_demands']} | "
          f"订单:{s['total_orders']} | 纠纷:{s['total_disputes']}")

# 8.2 用户列表
r = get("/api/admin/users", token=admin_token, name="管理员获取用户列表")
if r.status_code == 200:
    print(f"       用户总数: {len(r.json())}")

# 8.3 按状态筛选用户
get("/api/admin/users", token=admin_token, params={"status": "待审核"},
    name="管理员筛选待审核用户")

# 8.4 审核通过 / 驳回
# 创建新待审核用户
new_phone = rand_phone()
r = post("/api/auth/register", json_data={
    "phone": new_phone, "password": "test123456",
    "real_name": "待审核用户", "user_type": "设计师"
}, name="注册待审核用户")
if r.status_code == 200:
    new_uid = r.json().get("user_id")
    post(f"/api/admin/users/{new_uid}/approve", token=admin_token, name="管理员审核通过用户")

# 再注册一个用于驳回
reject_phone = rand_phone()
r = post("/api/auth/register", json_data={
    "phone": reject_phone, "password": "test123456",
    "real_name": "被驳回用户", "user_type": "业主"
}, name="注册待驳回用户")
if r.status_code == 200:
    reject_uid = r.json().get("user_id")
    post(f"/api/admin/users/{reject_uid}/reject", token=admin_token, name="管理员驳回用户")

# 8.5 普通用户不能访问管理接口
get("/api/admin/stats", token=buyer_token, expect=403,
    name="普通用户访问管理接口应返回403")
get("/api/admin/users", token=seller_token, expect=403,
    name="乙方访问管理接口应返回403")

# 8.6 管理员查看所有需求/订单/纠纷
r = get("/api/admin/demands", token=admin_token, name="管理员查看所有需求")
if r.status_code == 200:
    print(f"       全平台需求数: {len(r.json())}")

r = get("/api/admin/orders", token=admin_token, name="管理员查看所有订单")
if r.status_code == 200:
    print(f"       全平台订单数: {len(r.json())}")

r = get("/api/admin/disputes", token=admin_token, name="管理员查看所有纠纷")
if r.status_code == 200:
    print(f"       全平台纠纷数: {len(r.json())}")

# 8.7 管理员强制关闭需求
r = post("/api/demands", token=buyer_token, json_data={
    "title": "管理员关闭测试需求", "description": "测试", "budget": 100
}, name="创建待管理员关闭的需求")
if r.status_code == 200:
    admin_close_id = r.json()["id"]
    post(f"/api/demands/{admin_close_id}/publish", token=buyer_token,
         name="发布待管理员关闭的需求")
    post(f"/api/admin/demands/{admin_close_id}/close", token=admin_token,
         name="管理员强制关闭需求")

# 8.8 黑名单管理
r = get("/api/admin/blacklist", token=admin_token, name="管理员查看黑名单列表")
if r.status_code == 200:
    print(f"       黑名单用户数: {len(r.json())}")

# 找一个普通用户加黑名单
r = get("/api/admin/users", token=admin_token)
if r.status_code == 200:
    targets = [u for u in r.json()
               if not u.get("is_admin") and not u.get("is_reviewer")
               and not u.get("is_blacklisted")]
    if targets:
        bl_uid = targets[0]["id"]
        post(f"/api/admin/users/{bl_uid}/blacklist", token=admin_token,
             name="管理员将用户加入黑名单")
        get("/api/admin/blacklist", token=admin_token, name="查看黑名单(加入后)")
        post(f"/api/admin/users/{bl_uid}/unblacklist", token=admin_token,
             name="管理员解除用户黑名单")

# 8.9 管理员不能黑自己（管理员）
post(f"/api/admin/users/1/blacklist", token=admin_token,
     expect=400, name="将管理员加入黑名单应返回400")

# 8.10 资金记录
r = get("/api/admin/fund-records", token=admin_token, name="管理员查看资金流水")
if r.status_code == 200:
    print(f"       资金记录数: {len(r.json())}")

# 8.11 操作日志
r = get("/api/admin/operation-logs", token=admin_token, name="管理员查看操作日志")
if r.status_code == 200:
    print(f"       操作日志数: {len(r.json())}")
get("/api/admin/operation-logs", token=admin_token, params={"limit": 10},
    name="操作日志-指定条数")

# 8.12 内容审核（管理员和审核员均可访问）
get("/api/admin/content-review", token=admin_token, name="管理员-内容审核")
if reviewer_token:
    get("/api/admin/content-review", token=reviewer_token, name="审核员-内容审核")
    # 普通用户不能访问内容审核
    get("/api/admin/content-review", token=buyer_token, expect=403,
        name="普通用户访问内容审核应返回403")

# 8.13 管理员退款（需要进行中的订单）
# 用纠纷测试中的订单（已进行中，尚未验收）
if dispute_id:
    # dispute_order_id 应该还在进行中（甲方支付后未验收）
    r = get("/api/admin/orders", token=admin_token)
    if r.status_code == 200:
        inprogress = [o for o in r.json() if o["status"] == "进行中"]
        if inprogress:
            refund_order_id = inprogress[0]["id"]
            post(f"/api/orders/{refund_order_id}/refund", token=admin_token,
                 name="管理员对进行中订单执行退款")
        else:
            skip("管理员退款", "无进行中订单可用")

# 8.14 普通用户不能退款
if order_id:
    post(f"/api/orders/{order_id}/refund", token=buyer_token, expect=403,
         name="普通用户退款应返回403")

# 8.15 纠纷裁决（需要处理中的纠纷）
if dispute_id:
    post(f"/api/admin/disputes/{dispute_id}/resolve", token=admin_token,
         data={"result": "经核实，供方存在违约，甲方胜诉，全额退款", "action": "refund"},
         name="管理员裁决纠纷(退款)")

# 管理员裁决放款
# 创建另一个纠纷用于放款测试
if buyer_token and seller_token:
    r = post("/api/demands", token=buyer_token, json_data={
        "title": f"纠纷放款测试_{int(time.time())}", "description": "测试放款", "budget": 5000
    }, name="纠纷放款测试-创建需求")
    if r.status_code == 200:
        dp_demand_id = r.json()["id"]
        post(f"/api/demands/{dp_demand_id}/publish", token=buyer_token, name="纠纷放款测试-发布")
        r = post(f"/api/demands/{dp_demand_id}/quotes", token=seller_token,
                 json_data={"price": 4500}, name="纠纷放款测试-报价")
        if r.status_code == 200:
            dp_quote_id = r.json()["id"]
            r = post(f"/api/demands/{dp_demand_id}/select-winner/{dp_quote_id}",
                     token=buyer_token, name="纠纷放款测试-选标")
            if r.status_code == 200:
                dp_order_id = r.json().get("order_id")
                if dp_order_id:
                    post(f"/api/orders/{dp_order_id}/pay", token=buyer_token,
                         name="纠纷放款测试-支付")
                    r = post("/api/disputes", token=buyer_token,
                             json_data={"order_id": dp_order_id, "description": "测试放款裁决"},
                             name="纠纷放款测试-发起纠纷")
                    if r.status_code == 200:
                        dp_dispute_id = r.json()["id"]
                        post(f"/api/admin/disputes/{dp_dispute_id}/resolve",
                             token=admin_token,
                             data={"result": "经核实，乙方完成交付，甲方违约，放款给乙方",
                                   "action": "release"},
                             name="管理员裁决纠纷(放款给乙方)")

# 8.16 无效token访问管理接口
get("/api/admin/stats", token="bad", expect=401, name="无效Token访问管理接口应返回401")

# ============================================================
# 9. Feedback 接口
# ============================================================
section("[9/11] Feedback 接口")

# 9.1 用户提交反馈
r = post("/api/feedback", token=buyer_token,
         json_data={"content": "平台使用体验良好，建议增加实时消息推送功能"},
         name="用户提交投诉反馈")
if r.status_code == 200:
    feedback_id = r.json().get("id")
    print(f"       反馈ID: {feedback_id}")

# 乙方也提交一条
post("/api/feedback", token=seller_token,
     json_data={"content": "支付流程复杂，建议简化"},
     name="乙方提交投诉反馈")

# 9.2 用户查看自己的反馈列表
r = get("/api/feedback", token=buyer_token, name="用户查看自己的反馈列表")
if r.status_code == 200:
    print(f"       我的反馈数: {len(r.json())}")

# 9.3 管理员查看所有反馈
r = get("/api/admin/feedback", token=admin_token, name="管理员查看所有反馈")
if r.status_code == 200:
    data = r.json()
    print(f"       全平台反馈数: {len(data.get('items', data))}")

# 9.4 审核员查看所有反馈
if reviewer_token:
    r = get("/api/admin/feedback", token=reviewer_token, name="审核员查看所有反馈")
    if r.status_code == 200:
        data = r.json()
        print(f"       审核员看到反馈数: {len(data.get('items', data))}")

# 9.5 普通用户不能查看所有反馈
get("/api/admin/feedback", token=seller_token, expect=403,
    name="普通用户查看所有反馈应返回403")

# 9.6 管理员回复反馈
if feedback_id:
    post(f"/api/admin/feedback/{feedback_id}/reply",
         token=admin_token,
         json_data={"reply": "感谢您的建议，我们已纳入产品规划"},
         name="管理员回复用户反馈")

# 9.7 审核员回复反馈
r = get("/api/admin/feedback", token=admin_token)
if r.status_code == 200 and r.json().get('items'):
    any_fb_id = r.json()["items"][-1]["id"]
    if reviewer_token:
        post(f"/api/admin/feedback/{any_fb_id}/reply",
             token=reviewer_token,
             json_data={"reply": "审核员已受理您的反馈"},
             name="审核员回复用户反馈")

# 9.8 不存在的反馈
post("/api/admin/feedback/99999/reply", token=admin_token,
     json_data={"reply": "test"}, expect=404,
     name="回复不存在反馈应返回404")

# 9.9 无效token提交反馈
post("/api/feedback", token="bad",
     json_data={"content": "test"}, expect=401,
     name="无效Token提交反馈应返回401")

# ============================================================
# 10. 审核员专项权限测试
# ============================================================
section("[10/11] 审核员专项权限测试")

if not reviewer_token:
    skip("审核员权限测试", "reviewer_token缺失")
else:
    # 审核员可以访问内容审核
    get("/api/admin/content-review", token=reviewer_token, name="审核员-访问内容审核")
    # 审核员可以查看和回复反馈
    get("/api/admin/feedback", token=reviewer_token, name="审核员-查看所有反馈")

    # 审核员不能访问管理员专属接口（如用户审核、黑名单）
    get("/api/admin/stats", token=reviewer_token, expect=403,
        name="审核员访问管理员统计应返回403")
    get("/api/admin/users", token=reviewer_token, expect=403,
        name="审核员访问用户列表应返回403")
    get("/api/admin/orders", token=reviewer_token, expect=403,
        name="审核员访问订单列表应返回403")
    get("/api/admin/blacklist", token=reviewer_token, expect=403,
        name="审核员访问黑名单应返回403")

# ============================================================
# 11. 边界与异常测试
# ============================================================
section("[11/11] 边界与异常测试")

# 11.1 不存在资源
get("/api/demands/99999", expect=404, name="不存在需求应返回404")
get("/api/orders/99999", token=admin_token, expect=404, name="不存在订单应返回404")
post("/api/orders/99999/pay", token=admin_token, expect=404, name="支付不存在订单应返回404")
post("/api/orders/99999/accept", token=admin_token, expect=404, name="验收不存在订单应返回404")
post("/api/phases/99999/complete", token=admin_token, expect=404, name="验收不存在阶段应返回404")
post("/api/disputes", token=buyer_token,
     json_data={"order_id": 99999, "description": "test"}, expect=404,
     name="对不存在订单发起纠纷应返回404")
post_file("/api/disputes/99999/upload-evidence",
     files={"file": fake_file()}, token=buyer_token, expect=404,
     name="上传证据到不存在纠纷应返回404")

# 11.2 注册缺少必填字段
post("/api/auth/register", json_data={"phone": "13900000199"},
     expect=422, name="注册缺必填字段应返回422")

# 11.3 待审核用户不能登录
pending_phone = rand_phone()
post("/api/auth/register", json_data={
    "phone": pending_phone, "password": "test123456",
    "real_name": "待审核", "user_type": "业主"
}, name="注册待审核用户(不批准)")
post("/api/auth/login", data={"username": pending_phone, "password": "test123456"},
     expect=403, name="待审核用户登录应返回403")

# 11.4 黑名单用户不能登录
bl_phone = rand_phone()
r = post("/api/auth/register", json_data={
    "phone": bl_phone, "password": "test123456",
    "real_name": "黑名单用户", "user_type": "设计师"
}, name="注册待黑名单用户")
if r.status_code == 200:
    bl_new_uid = r.json().get("user_id")
    requests.post(api(f"/api/admin/users/{bl_new_uid}/approve"), headers=h(admin_token))
    requests.post(api(f"/api/admin/users/{bl_new_uid}/blacklist"), headers=h(admin_token))
    post("/api/auth/login", data={"username": bl_phone, "password": "test123456"},
         expect=403, name="黑名单用户登录应返回403")

# 11.5 已发布需求重复发布是幂等的（后端不阻止，返回200）
if demand_id:
    post(f"/api/demands/{demand_id}/publish", token=buyer_token,
         expect=200, name="重复发布已发布需求(幂等操作,期望200)")

# ============================================================
# 最终汇总
# ============================================================
total = _pass + _fail + _skip
print(f"\n{'='*60}")
print(f"  测试结果汇总")
print(f"{'='*60}")
print(f"  总计: {total} 项")
print(f"  通过: {_pass}")
print(f"  失败: {_fail}")
print(f"  跳过: {_skip}")
print(f"{'='*60}")

if _fail_list:
    print(f"\n  失败详情:")
    for name, detail in _fail_list:
        print(f"  [FAIL] {name}")
        if detail:
            print(f"         {detail}")

if _fail == 0:
    print(f"\n  全部通过！系统功能正常。\n")
else:
    print(f"\n  有 {_fail} 项失败，请检查后端日志。\n")

sys.exit(0 if _fail == 0 else 1)
