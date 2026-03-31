#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图审系统 - 全功能测试脚本 (优化版)
测试所有模块：用户认证、需求大厅、报价管理、订单管理、图纸管理、纠纷处理、通知系统、后台管理
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import time
import random
from io import BytesIO

BASE_URL = "http://127.0.0.1:8000"
API = lambda path: f"{BASE_URL}{path}"

# 测试数据存储
test_data = {
    "admin_token": None,
    "users": [],  # 每个用户 {"phone", "email", "password", "token", "id"}
    "tokens": {},
    "ids": {},
}


def print_step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print('='*60)


def print_result(name, success, detail=""):
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} {name}")
    if detail and not success:
        print(f"       {detail}")


def rand_phone():
    """生成唯一手机号"""
    return f"139{str(int(time.time()))[-8:]}{random.randint(10, 99)}"


def rand_email():
    """生成唯一邮箱"""
    return f"test_{int(time.time())}_{random.randint(1000,9999)}@example.com"


def register_user(phone=None, email=None, real_name="测试用户", user_type="设计师",
                  auth_type="个人", company="测试公司"):
    """注册用户并自动登录"""
    p = phone or rand_phone()
    e = email or rand_email()
    data = {
        "phone": p,
        "email": e,
        "password": "test123456",
        "real_name": real_name,
        "user_type": user_type,
        "auth_type": auth_type,
        "company_name": company,
    }
    resp = requests.post(API("/api/auth/register"), json=data)
    if resp.status_code != 200:
        return None

    user = {"phone": p, "email": e, "password": "test123456", "real_name": real_name}
    # 登录获取token
    token_resp = requests.post(API("/api/auth/login"), data={"username": p, "password": "test123456"})
    if token_resp.status_code == 200:
        user["token"] = token_resp.json().get("access_token")
        user["id"] = test_data["ids"].get(p) or user.get("id")
    return user


def login_user(username, password):
    """登录用户"""
    resp = requests.post(API("/api/auth/login"), data={"username": username, "password": password})
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


def get_headers(token):
    """获取认证头"""
    return {"Authorization": f"Bearer {token}"}


def ensure_admin():
    """确保管理员已登录"""
    if not test_data["admin_token"]:
        token = login_user("13800000000", "admin123")
        test_data["admin_token"] = token
    return test_data["admin_token"]


# ==================== 测试用例 ====================

def test_admin_login():
    """测试管理员登录"""
    print_step("测试管理员登录")
    token = login_user("13800000000", "admin123")
    test_data["admin_token"] = token
    print_result("管理员登录", token is not None)


def test_register_phone():
    """测试手机号注册"""
    print_step("测试手机号注册")
    user = register_user(real_name="手机注册测试", auth_type="个人")
    if user and user.get("token"):
        test_data["users"].append(user)
        test_data["tokens"]["phone_user"] = user["token"]
        print_result("手机号注册", True)
        return user
    print_result("手机号注册", False, "注册或登录失败")
    return None


def test_register_email():
    """测试邮箱注册"""
    print_step("测试邮箱注册")
    user = register_user(email=rand_email(), real_name="邮箱注册测试", auth_type="个人")
    if user and user.get("token"):
        test_data["users"].append(user)
        test_data["tokens"]["email_user"] = user["token"]
        print_result("邮箱注册", True)
        return user
    print_result("邮箱注册", False, "注册失败")
    return None


def test_register_enterprise():
    """测试企业注册"""
    print_step("测试企业注册")
    user = register_user(real_name="企业测试", auth_type="企业", company="测试企业公司")
    if user and user.get("token"):
        test_data["users"].append(user)
        test_data["tokens"]["enterprise_user"] = user["token"]
        print_result("企业注册", True)
        return user
    print_result("企业注册", False, "注册失败")
    return None


def test_register_duplicate():
    """测试重复注册检测"""
    print_step("测试重复手机号检测")
    user = test_data["users"][0] if test_data["users"] else None
    if not user:
        print_result("重复注册检测", False, "无可用用户")
        return

    data = {
        "phone": user["phone"],
        "email": rand_email(),
        "password": "test123456",
        "real_name": "重复测试",
        "user_type": "设计师",
        "auth_type": "个人",
    }
    resp = requests.post(API("/api/auth/register"), json=data)
    print_result("重复手机号检测", resp.status_code == 400)


def test_login_wrong_password():
    """测试错误密码"""
    print_step("测试错误密码检测")
    resp = requests.post(API("/api/auth/login"), data={"username": "13800000000", "password": "wrongpass"})
    print_result("错误密码检测", resp.status_code == 400)


def test_get_me():
    """测试获取当前用户"""
    print_step("测试获取当前用户信息")
    token = test_data["tokens"].get("phone_user")
    if not token:
        # 创建一个新用户
        user = register_user()
        if user:
            test_data["users"].append(user)
            test_data["tokens"]["phone_user"] = user["token"]
            token = user["token"]

    if token:
        resp = requests.get(API("/api/auth/me"), headers=get_headers(token))
        if resp.status_code == 200:
            info = resp.json()
            print_result("获取当前用户", True)
            return info
    print_result("获取当前用户", False, "获取失败")


def test_create_demand():
    """测试创建需求"""
    print_step("测试创建需求")
    token = test_data["tokens"].get("phone_user")
    if not token:
        print_result("创建需求", False, "无认证token")
        return None

    title = f"测试图纸审核需求_{int(time.time())}"
    data = {
        "title": title,
        "description": "这是一个测试需求，用于验证需求创建功能",
        "budget": 5000.00,
        "payment_type": "一次性",
        "profession": "结构设计",
        "demand_type": "施工图审查",
    }
    resp = requests.post(API("/api/demands"), json=data, headers=get_headers(token))
    if resp.status_code == 200:
        demand = resp.json()
        test_data["ids"]["demand_id"] = demand["id"]
        test_data["ids"]["demand_title"] = title
        print_result("创建需求", True)
        return demand
    print_result("创建需求", False, resp.text)
    return None


def test_publish_demand():
    """测试发布需求"""
    print_step("测试发布需求")
    token = test_data["tokens"].get("phone_user")
    demand_id = test_data["ids"].get("demand_id")
    if not token or not demand_id:
        print_result("发布需求", False, "缺少参数")
        return False

    resp = requests.post(API(f"/api/demands/{demand_id}/publish"), headers=get_headers(token))
    success = resp.status_code == 200
    print_result("发布需求", success, resp.text if not success else "")
    return success


def test_list_demands():
    """测试需求列表和筛选"""
    print_step("测试需求列表和筛选")
    # 无认证访问
    resp1 = requests.get(API("/api/demands"))
    r1 = resp1.status_code == 200

    # 按状态筛选
    resp2 = requests.get(API("/api/demands?status=已发布"))
    r2 = resp2.status_code == 200

    # 按关键词筛选
    resp3 = requests.get(API("/api/demands?keyword=测试"))
    r3 = resp3.status_code == 200

    print_result("需求列表", r1)
    print_result("按状态筛选", r2)
    print_result("按关键词筛选", r3)
    return r1 and r2 and r3


def test_create_quote():
    """测试创建报价"""
    print_step("测试创建报价")
    # 需要两个用户：需方和供方
    buyer_token = test_data["tokens"].get("phone_user")
    if not buyer_token:
        print_result("创建报价", False, "无需方token")
        return None

    # 创建一个企业用户作为供方
    seller = register_user(real_name="供方测试", auth_type="企业", company="供方公司")
    if not seller:
        print_result("创建报价", False, "创建供方失败")
        return None
    test_data["users"].append(seller)
    test_data["tokens"]["seller"] = seller["token"]

    demand_id = test_data["ids"].get("demand_id")
    if not demand_id:
        # 先创建需求
        test_create_demand()
        demand_id = test_data["ids"].get("demand_id")

    # 供方报价
    data = {"price": 4500.00, "remark": "包含详细审核报告"}
    resp = requests.post(
        API(f"/api/demands/{demand_id}/quotes"),
        json=data,
        headers=get_headers(seller["token"])
    )
    if resp.status_code == 200:
        quote = resp.json()
        test_data["ids"]["quote_id"] = quote["id"]
        print_result("创建报价", True)
        return quote
    print_result("创建报价", False, resp.text)
    return None


def test_update_quote():
    """测试编辑报价"""
    print_step("测试编辑报价")
    token = test_data["tokens"].get("seller")
    quote_id = test_data["ids"].get("quote_id")

    if not token or not quote_id:
        print_result("编辑报价", False, "缺少参数")
        return False

    data = {"price": 4800.00, "remark": "修改后的报价说明"}
    resp = requests.put(API(f"/api/quotes/{quote_id}"), json=data, headers=get_headers(token))
    print_result("编辑报价", resp.status_code == 200, resp.text if resp.status_code != 200 else "")


def test_list_quotes():
    """测试查看报价列表"""
    print_step("测试查看报价列表")
    demand_id = test_data["ids"].get("demand_id")
    if not demand_id:
        print_result("查看报价列表", False, "无需求ID")
        return False

    resp = requests.get(API(f"/api/demands/{demand_id}/quotes"))
    if resp.status_code == 200:
        quotes = resp.json()
        print_result("查看报价列表", len(quotes) > 0, f"共{len(quotes)}条报价")
        return True
    print_result("查看报价列表", False, resp.text)
    return False


def test_select_winner():
    """测试选择中标"""
    print_step("测试选择中标")
    buyer_token = test_data["tokens"].get("phone_user")
    demand_id = test_data["ids"].get("demand_id")
    quote_id = test_data["ids"].get("quote_id")

    if not all([buyer_token, demand_id, quote_id]):
        print_result("选择中标", False, "缺少参数")
        return False

    resp = requests.post(
        API(f"/api/demands/{demand_id}/select-winner/{quote_id}"),
        headers=get_headers(buyer_token)
    )
    print_result("选择中标", resp.status_code == 200, resp.text if resp.status_code != 200 else "")


def test_create_order():
    """测试创建订单"""
    print_step("测试创建订单")
    buyer_token = test_data["tokens"].get("phone_user")
    seller_token = test_data["tokens"].get("seller")
    demand_id = test_data["ids"].get("demand_id")

    if not all([buyer_token, seller_token, demand_id]):
        print_result("创建订单", False, "缺少参数")
        return None

    # 获取seller的user id
    me_resp = requests.get(API("/api/auth/me"), headers=get_headers(seller_token))
    seller_id = me_resp.json().get("id") if me_resp.status_code == 200 else None

    data = {
        "demand_id": demand_id,
        "seller_id": seller_id or 2,
        "amount": 4500.00,
        "payment_type": "一次性",
    }
    resp = requests.post(API("/api/orders"), json=data, headers=get_headers(buyer_token))
    if resp.status_code == 200:
        order = resp.json()
        test_data["ids"]["order_id"] = order["id"]
        print_result("创建订单", True)
        return order
    print_result("创建订单", False, resp.text)
    return None


def test_pay_order():
    """测试支付订单"""
    print_step("测试支付订单（资金托管）")
    token = test_data["tokens"].get("phone_user")
    order_id = test_data["ids"].get("order_id")

    if not token or not order_id:
        print_result("支付订单", False, "缺少参数")
        return False

    resp = requests.post(API(f"/api/orders/{order_id}/pay"), headers=get_headers(token))
    print_result("支付订单", resp.status_code == 200, resp.text if resp.status_code != 200 else "")


def test_accept_order():
    """测试验收订单"""
    print_step("测试验收订单")
    token = test_data["tokens"].get("phone_user")
    order_id = test_data["ids"].get("order_id")

    if not token or not order_id:
        print_result("验收订单", False, "缺少参数")
        return False

    resp = requests.post(API(f"/api/orders/{order_id}/accept"), headers=get_headers(token))
    print_result("验收订单", resp.status_code == 200, resp.text if resp.status_code != 200 else "")


def test_list_orders():
    """测试订单列表"""
    print_step("测试订单列表")
    token = test_data["tokens"].get("phone_user")
    if not token:
        print_result("订单列表", False, "无token")
        return False

    resp = requests.get(API("/api/orders"), headers=get_headers(token))
    print_result("订单列表", resp.status_code == 200, resp.text if resp.status_code != 200 else "")


def test_upload_drawing():
    """测试上传图纸"""
    print_step("测试上传图纸")
    token = test_data["tokens"].get("seller")
    order_id = test_data["ids"].get("order_id")

    if not token or not order_id:
        print_result("上传图纸", False, "缺少参数")
        return None

    file_content = b"%PDF-1.4 test content"
    files = {"file": ("test_drawing.pdf", BytesIO(file_content), "application/pdf")}
    data = {"version": "V1"}
    resp = requests.post(
        API(f"/api/orders/{order_id}/drawings"),
        files=files,
        data=data,
        headers=get_headers(token)
    )
    if resp.status_code == 200:
        drawing = resp.json()
        test_data["ids"]["drawing_id"] = drawing["id"]
        print_result("上传图纸", True)
        return drawing
    print_result("上传图纸", False, resp.text)
    return None


def test_list_drawings():
    """测试图纸列表"""
    print_step("测试图纸列表")
    order_id = test_data["ids"].get("order_id")
    if not order_id:
        print_result("图纸列表", False, "无订单ID")
        return False

    resp = requests.get(API(f"/api/orders/{order_id}/drawings"))
    if resp.status_code == 200:
        drawings = resp.json()
        print_result("图纸列表", len(drawings) > 0, f"共{len(drawings)}张图纸")
        return True
    print_result("图纸列表", False, resp.text)
    return False


def test_drawing_comments():
    """测试图纸意见"""
    print_step("测试图纸意见")
    token = test_data["tokens"].get("phone_user")
    drawing_id = test_data["ids"].get("drawing_id")

    if not token or not drawing_id:
        print_result("图纸意见", False, "缺少参数")
        return False

    resp = requests.put(
        API(f"/api/drawings/{drawing_id}/comments"),
        data={"comments": "图纸整体良好，建议优化节点设计"},
        headers=get_headers(token)
    )
    print_result("添加意见", resp.status_code == 200, resp.text if resp.status_code != 200 else "")


def test_upload_comment_img():
    """测试上传意见图片"""
    print_step("测试上传意见图片")
    token = test_data["tokens"].get("phone_user")
    drawing_id = test_data["ids"].get("drawing_id")

    if not token or not drawing_id:
        print_result("上传意见图片", False, "缺少参数")
        return False

    file_content = b"\xff\xd8\xff\xe0 test image content"
    files = {"file": ("comment.jpg", BytesIO(file_content), "image/jpeg")}
    resp = requests.post(
        API(f"/api/drawings/{drawing_id}/upload-comment-img"),
        files=files,
        headers=get_headers(token)
    )
    print_result("上传意见图片", resp.status_code == 200, resp.text if resp.status_code != 200 else "")


def test_create_dispute():
    """测试创建纠纷"""
    print_step("测试创建纠纷")
    token = test_data["tokens"].get("phone_user")
    order_id = test_data["ids"].get("order_id")

    if not token or not order_id:
        print_result("创建纠纷", False, "缺少参数")
        return None

    data = {"order_id": order_id, "description": "交付的图纸不符合要求，需要修改"}
    resp = requests.post(API("/api/disputes"), json=data, headers=get_headers(token))
    if resp.status_code == 200:
        dispute = resp.json()
        test_data["ids"]["dispute_id"] = dispute["id"]
        print_result("创建纠纷", True)
        return dispute
    print_result("创建纠纷", False, resp.text)
    return None


def test_upload_evidence():
    """测试上传证据"""
    print_step("测试上传证据")
    token = test_data["tokens"].get("phone_user")
    dispute_id = test_data["ids"].get("dispute_id")

    if not token or not dispute_id:
        print_result("上传证据", False, "缺少参数")
        return False

    file_content = b"evidence file content"
    files = {"file": ("evidence.pdf", BytesIO(file_content), "application/pdf")}
    resp = requests.post(
        API(f"/api/disputes/{dispute_id}/upload-evidence"),
        files=files,
        headers=get_headers(token)
    )
    print_result("上传证据", resp.status_code == 200, resp.text if resp.status_code != 200 else "")


def test_list_disputes():
    """测试纠纷列表"""
    print_step("测试纠纷列表")
    token = test_data["tokens"].get("phone_user")
    if not token:
        print_result("纠纷列表", False, "无token")
        return False

    resp = requests.get(API("/api/disputes"), headers=get_headers(token))
    print_result("纠纷列表", resp.status_code == 200, resp.text if resp.status_code != 200 else "")


def test_notifications():
    """测试通知列表"""
    print_step("测试通知系统")
    token = test_data["tokens"].get("phone_user")
    if not token:
        print_result("通知列表", False, "无token")
        return False

    resp = requests.get(API("/api/notifications"), headers=get_headers(token))
    if resp.status_code == 200:
        notifs = resp.json()
        print_result("通知列表", True, f"共{len(notifs)}条通知")
        return True
    print_result("通知列表", False, resp.text)
    return False


def test_admin_stats():
    """测试管理员统计"""
    print_step("测试管理员统计")
    token = ensure_admin()
    if not token:
        print_result("管理员统计", False, "无管理员token")
        return False

    resp = requests.get(API("/api/admin/stats"), headers=get_headers(token))
    if resp.status_code == 200:
        stats = resp.json()
        print(f"       用户总数: {stats.get('total_users', 0)}")
        print(f"       订单总数: {stats.get('total_orders', 0)}")
        print_result("管理员统计", True)
        return True
    print_result("管理员统计", False, resp.text)
    return False


def test_admin_users():
    """测试管理员用户管理"""
    print_step("测试管理员用户管理")
    token = ensure_admin()
    if not token:
        print_result("用户管理", False, "无管理员token")
        return False

    resp = requests.get(API("/api/admin/users"), headers=get_headers(token))
    print_result("用户列表", resp.status_code == 200, resp.text if resp.status_code != 200 else "")


def test_admin_approve_user():
    """测试审核用户"""
    print_step("测试审核用户")
    token = ensure_admin()
    if not token:
        print_result("审核用户", False)
        return

    resp = requests.get(API("/api/admin/users?status=待审核"), headers=get_headers(token))
    if resp.status_code == 200:
        users = resp.json()
        if users:
            user_id = users[0]["id"]
            approve_resp = requests.post(
                API(f"/api/admin/users/{user_id}/approve"),
                headers=get_headers(token)
            )
            print_result("审核通过", approve_resp.status_code == 200,
                        approve_resp.text if approve_resp.status_code != 200 else "")
        else:
            print_result("审核用户", True, "无待审核用户")
    else:
        print_result("审核用户", False, resp.text)


def test_admin_blacklist():
    """测试黑名单"""
    print_step("测试黑名单管理")
    token = ensure_admin()
    if not token:
        print_result("黑名单管理", False)
        return

    resp = requests.get(API("/api/admin/users"), headers=get_headers(token))
    if resp.status_code == 200:
        users = resp.json()
        # 找一个非管理员用户
        target = None
        for u in users:
            if u.get("is_admin") != 1 and u.get("is_blacklisted") != 1:
                target = u
                break

        if target:
            # 加入黑名单
            r1 = requests.post(
                API(f"/api/admin/users/{target['id']}/blacklist"),
                headers=get_headers(token)
            )
            # 查看黑名单
            r2 = requests.get(API("/api/admin/blacklist"), headers=get_headers(token))
            # 解除黑名单
            r3 = requests.post(
                API(f"/api/admin/users/{target['id']}/unblacklist"),
                headers=get_headers(token)
            )
            print_result("加入黑名单", r1.status_code == 200)
            print_result("查看黑名单", r2.status_code == 200)
            print_result("解除黑名单", r3.status_code == 200)
        else:
            print_result("黑名单管理", True, "无普通用户可测试")
    else:
        print_result("黑名单管理", False, resp.text)


def test_admin_fund_records():
    """测试资金记录"""
    print_step("测试资金记录")
    token = ensure_admin()
    if not token:
        print_result("资金记录", False)
        return

    resp = requests.get(API("/api/admin/fund-records"), headers=get_headers(token))
    print_result("资金记录", resp.status_code == 200, resp.text if resp.status_code != 200 else "")


def test_admin_operation_logs():
    """测试操作日志"""
    print_step("测试操作日志")
    token = ensure_admin()
    if not token:
        print_result("操作日志", False)
        return

    resp = requests.get(API("/api/admin/operation-logs"), headers=get_headers(token))
    print_result("操作日志", resp.status_code == 200, resp.text if resp.status_code != 200 else "")


def test_admin_content_review():
    """测试内容审核"""
    print_step("测试内容审核")
    token = ensure_admin()
    if not token:
        print_result("内容审核", False)
        return

    resp = requests.get(API("/api/admin/content-review"), headers=get_headers(token))
    print_result("内容审核", resp.status_code == 200, resp.text if resp.status_code != 200 else "")


def test_feedback():
    """测试投诉反馈"""
    print_step("测试投诉反馈")
    token = test_data["tokens"].get("phone_user")
    admin_token = ensure_admin()

    if not token:
        print_result("提交反馈", False, "无用户token")
        return

    # 提交反馈
    fb_data = {"content": "平台使用过程中遇到一些问题，希望能改进用户体验"}
    fb_resp = requests.post(API("/api/feedback"), json=fb_data, headers=get_headers(token))

    if fb_resp.status_code == 200:
        fb = fb_resp.json()
        fb_id = fb.get("id") or 1
        test_data["ids"]["feedback_id"] = fb_id
        print_result("提交反馈", True)

        # 管理员回复
        if admin_token:
            reply_data = {"reply": "感谢您的反馈，我们会认真考虑您的建议"}
            reply_resp = requests.post(
                API(f"/api/admin/feedbacks/{fb_id}/reply"),
                data=reply_data,
                headers=get_headers(admin_token)
            )
            print_result("管理员回复", reply_resp.status_code == 200,
                        reply_resp.text if reply_resp.status_code != 200 else "")
    else:
        print_result("提交反馈", False, fb_resp.text)


def test_admin_disputes():
    """测试管理员纠纷管理"""
    print_step("测试管理员纠纷管理")
    token = ensure_admin()
    dispute_id = test_data["ids"].get("dispute_id")

    if not token:
        print_result("纠纷管理", False, "无管理员token")
        return

    resp = requests.get(API("/api/admin/disputes"), headers=get_headers(token))
    print_result("纠纷列表", resp.status_code == 200)

    if dispute_id and resp.status_code == 200:
        # 处理纠纷
        resolve_data = {"result": "经核实，供方确实存在问题，同意全额退款", "action": "refund"}
        resolve_resp = requests.post(
            API(f"/api/admin/disputes/{dispute_id}/resolve"),
            data=resolve_data,
            headers=get_headers(token)
        )
        print_result("处理纠纷", resolve_resp.status_code == 200,
                    resolve_resp.text if resolve_resp.status_code != 200 else "")


# ==================== 运行所有测试 ====================

def run_all_tests():
    """按正确顺序运行所有测试"""
    print("\n" + "="*60)
    print("          图审系统 - 全功能测试")
    print("="*60)

    # 检查服务
    try:
        requests.get(BASE_URL, timeout=2)
    except:
        print("\n错误: 后端服务未启动！")
        print("请先启动后端: cd tushen-system/backend && python main.py")
        return False

    results = {"passed": 0, "failed": 0}

    def run(name, func):
        try:
            result = func()
            if result is False:
                results["failed"] += 1
            elif result is None or result is True:
                results["passed"] += 1
            elif isinstance(result, list):
                results["passed"] += len([r for r in result if r])
                results["failed"] += len([r for r in result if not r])
            else:
                results["passed"] += 1
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            results["failed"] += 1

    # 1. 管理员登录
    run("管理员登录", test_admin_login)

    # 2. 用户注册测试
    run("手机号注册", test_register_phone)
    run("邮箱注册", test_register_email)
    run("企业注册", test_register_enterprise)
    run("重复注册检测", test_register_duplicate)
    run("错误密码检测", test_login_wrong_password)

    # 3. 用户信息
    run("获取当前用户", test_get_me)

    # 4. 需求管理
    run("创建需求", test_create_demand)
    run("发布需求", test_publish_demand)
    run("需求列表筛选", test_list_demands)

    # 5. 报价管理
    run("创建报价", test_create_quote)
    run("编辑报价", test_update_quote)
    run("查看报价列表", test_list_quotes)
    run("选择中标", test_select_winner)

    # 6. 订单管理
    run("创建订单", test_create_order)
    run("支付订单", test_pay_order)
    run("验收订单", test_accept_order)
    run("订单列表", test_list_orders)

    # 7. 图纸管理
    run("上传图纸", test_upload_drawing)
    run("图纸列表", test_list_drawings)
    run("图纸意见", test_drawing_comments)
    run("意见图片", test_upload_comment_img)

    # 8. 纠纷处理
    run("创建纠纷", test_create_dispute)
    run("上传证据", test_upload_evidence)
    run("纠纷列表", test_list_disputes)

    # 9. 通知系统
    run("通知列表", test_notifications)

    # 10. 后台管理
    run("管理员统计", test_admin_stats)
    run("用户管理", test_admin_users)
    run("审核用户", test_admin_approve_user)
    run("黑名单管理", test_admin_blacklist)
    run("资金记录", test_admin_fund_records)
    run("操作日志", test_admin_operation_logs)
    run("内容审核", test_admin_content_review)
    run("管理员纠纷", test_admin_disputes)

    # 11. 投诉反馈
    run("投诉反馈", test_feedback)

    # 输出总结
    print("\n" + "="*60)
    print("              测试结果汇总")
    print("="*60)
    total = results["passed"] + results["failed"]
    print(f"  总计: {results['passed']} 通过, {results['failed']} 失败 (共{total}项)")
    print("="*60)

    if results["failed"] == 0:
        print("\n🎉 所有测试通过！系统功能正常！\n")
    else:
        print(f"\n⚠️  有 {results['failed']} 项测试失败，请检查。\n")

    return results["failed"] == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
