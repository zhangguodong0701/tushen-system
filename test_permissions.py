"""图审系统权限测试脚本 - 验证所有权限修复"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_api(name, method, path, data=None, token=None, expected_status=None, description=""):
    """测试API并输出结果"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        if method == "GET":
            r = requests.get(f"{BASE_URL}{path}", headers=headers)
        elif method == "POST":
            r = requests.post(f"{BASE_URL}{path}", json=data, headers=headers)
        elif method == "PUT":
            r = requests.put(f"{BASE_URL}{path}", json=data, headers=headers)
        elif method == "DELETE":
            r = requests.delete(f"{BASE_URL}{path}", headers=headers)
        
        success = True
        if expected_status:
            success = r.status_code == expected_status
        
        status_icon = "[OK]" if success else "[FAIL]"
        print(f"{status_icon} {name}")
        if description:
            print(f"   {description}")
        print(f"   期望: {expected_status}, 实际: {r.status_code}")
        if not success:
            try:
                detail = r.json().get("detail", r.text[:100])
                print(f"   响应: {detail}")
            except:
                print(f"   响应: {r.text[:100]}")
        return success
    except Exception as e:
        print(f"[FAIL] {name}: 请求失败 - {e}")
        return False

def main():
    print("=" * 60)
    print("图审系统权限测试")
    print("=" * 60)
    
    # 1. 登录获取 token
    print("\n[1] 登录获取Token")
    
    # 甲方用户 (业主) - 使用data参数因为OAuth2PasswordRequestForm需要form数据
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": "13811112222", "password": "test123"})
    jia_token = r.json().get("access_token") if r.status_code == 200 else None
    jia_user = r.json().get("user", {}) if r.status_code == 200 else {}
    
    # 乙方用户 (设计师)
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": "13911112222", "password": "test123"})
    yi_token = r.json().get("access_token") if r.status_code == 200 else None
    
    # 管理员
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": "13800000000", "password": "admin123"})
    admin_token = r.json().get("access_token") if r.status_code == 200 else None
    
    print(f"甲方Token: {'获取成功' if jia_token else '失败'}")
    print(f"乙方Token: {'获取成功' if yi_token else '失败'}")
    print(f"管理员Token: {'获取成功' if admin_token else '失败'}")
    
    if not all([jia_token, yi_token, admin_token]):
        print("\n[ERROR] Token获取失败，测试终止")
        return False
    
    results = []
    
    # 2. 测试需求发布权限 (P01)
    print("\n[2] 测试需求发布权限 (P01)")
    
    # 乙方不能发布需求
    r = test_api(
        "乙方(设计师)发布需求",
        "POST",
        "/demands",
        {"title": "测试需求", "description": "测试", "budget": "1000"},
        yi_token,
        expected_status=403,
        description="只有甲方才能发布需求"
    )
    results.append(("P01-1 乙方不能发布", r))
    
    # 甲方可以发布需求
    r = test_api(
        "甲方(业主)发布需求",
        "POST",
        "/demands",
        {"title": "权限测试需求", "description": "测试权限控制", "budget": "5000"},
        jia_token,
        expected_status=200,
        description="甲方可以发布需求"
    )
    results.append(("P01-2 甲方可以发布", r == True))  # 200也视为成功
    
    # 获取刚创建的需求ID用于后续测试
    demand_id = None
    if r:
        r2 = requests.get(f"{BASE_URL}/demands", headers={"Authorization": f"Bearer {jia_token}"})
        result = r2.json()
        # API返回分页格式 {"total":10,"page":1,"items":[...]}
        demands = result.get("items", result if isinstance(result, list) else [])
        if demands:
            demand_id = demands[0].get("id")
            print(f"   找到需求ID: {demand_id}")
    
    # 3. 测试报价权限 (P02)
    print("\n[3] 测试报价权限 (P02)")
    
    # 发布需求以便测试报价
    if demand_id:
        requests.put(f"{BASE_URL}/demands/{demand_id}", json={"status": "已发布"},
                     headers={"Authorization": f"Bearer {jia_token}"})
        
        # 乙方可以报价
        r = test_api(
            "乙方(设计师)报价",
            "POST",
            f"/demands/{demand_id}/quotes",
            {"price": 5000, "remark": "测试报价"},
            yi_token,
            expected_status=201,
            description="乙方可以报价"
        )
        results.append(("P02-1 乙方可以报价", r))
    
    # 甲方不能报价
    r = test_api(
        "甲方(业主)尝试报价",
        "POST",
        "/demands/1/quotes",
        {"price": 3000, "remark": "非法报价"},
        jia_token,
        expected_status=403,
        description="甲方不能报价(角色限制)"
    )
    results.append(("P02-2 甲方不能报价", r))
    
    # 4. 测试退款权限 (P03)
    print("\n[4] 测试退款权限 (P03)")
    
    # 非管理员不能退款
    r = test_api(
        "乙方尝试退款",
        "POST",
        "/orders/1/refund",
        token=yi_token,
        expected_status=403,
        description="只有管理员才能退款"
    )
    results.append(("P03-1 非管理员不能退款", r))
    
    # 管理员可以访问退款API（虽然订单不存在会返回404）
    r = test_api(
        "管理员访问退款API",
        "POST",
        "/orders/999/refund",
        token=admin_token,
        expected_status=404,
        description="管理员权限验证（订单不存在返回404）"
    )
    results.append(("P03-2 管理员可以访问退款", r))
    
    # 5. 测试阶段验收权限 (P04)
    print("\n[5] 测试阶段验收权限 (P04)")
    
    # 乙方不能验收阶段
    r = test_api(
        "乙方尝试验收阶段",
        "POST",
        "/phases/1/complete",
        token=yi_token,
        expected_status=403,
        description="只有甲方才能验收阶段"
    )
    results.append(("P04-1 乙方不能验收阶段", r))
    
    # 6. 测试添加阶段权限 (P05)
    print("\n[6] 测试添加阶段权限 (P05)")
    
    # 乙方不能添加阶段
    r = test_api(
        "乙方尝试添加阶段",
        "POST",
        "/orders/1/phases",
        {"name": "阶段1", "amount": 1000},
        yi_token,
        expected_status=403,
        description="只有甲方才能添加阶段"
    )
    results.append(("P05-1 乙方不能添加阶段", r))
    
    # 7. 测试图纸评论权限 (P06)
    print("\n[7] 测试图纸评论权限 (P06)")
    
    # 乙方不能评论图纸
    r = test_api(
        "乙方尝试评论图纸",
        "PUT",
        "/drawings/1/comments",
        data={"comments": "测试评论"},
        token=yi_token,
        expected_status=403,
        description="只有甲方才能评论图纸"
    )
    results.append(("P06-1 乙方不能评论图纸", r))
    
    # 8. 测试订单详情权限 (P09)
    print("\n[8] 测试订单详情权限 (P09)")
    
    # 无关用户不能查看订单（权限校验会先于订单存在性检查）
    r = test_api(
        "无关用户查看订单",
        "GET",
        "/orders/1",
        token=yi_token,
        expected_status=403,
        description="只有订单参与方才能查看"
    )
    results.append(("P09-1 无关用户不能查看订单", r))
    
    # 9. 测试纠纷发起权限 (P15)
    print("\n[9] 测试纠纷发起权限 (P15)")
    
    # 无关用户不能发起纠纷
    r = test_api(
        "无关用户发起纠纷",
        "POST",
        "/disputes",
        {"order_id": 999, "description": "测试"},
        yi_token,
        expected_status=403,
        description="只有订单参与方才能发起纠纷"
    )
    results.append(("P15-1 无关用户不能发起纠纷", r))
    
    # 10. 测试阶段列表权限 (P13)
    print("\n[10] 测试阶段列表权限 (P13)")
    
    # 无关用户不能查看阶段列表
    r = test_api(
        "无关用户查看阶段列表",
        "GET",
        "/orders/1/phases",
        token=yi_token,
        expected_status=403,
        description="只有订单参与方才能查看"
    )
    results.append(("P13-1 无关用户不能查看阶段", r))
    
    # 11. 测试证据查看权限 (P14)
    print("\n[11] 测试证据查看权限 (P14)")
    
    # 无关用户不能查看证据
    r = test_api(
        "无关用户查看证据",
        "GET",
        "/disputes/1/evidence-files",
        token=yi_token,
        expected_status=403,
        description="只有相关方才能查看证据"
    )
    results.append(("P14-1 无关用户不能查看证据", r))
    
    # 12. 测试审核员API路径 (P07-P08)
    print("\n[12] 测试审核员API路径 (P07-P08)")
    
    r = test_api(
        "管理员获取待审核用户",
        "GET",
        "/admin/users?status=待审核",
        token=admin_token,
        expected_status=200,
        description="使用正确的admin路径"
    )
    results.append(("P07 管理员获取待审核用户", r))
    
    r = test_api(
        "管理员获取纠纷列表",
        "GET",
        "/admin/disputes",
        token=admin_token,
        expected_status=200,
        description="使用正确的admin路径"
    )
    results.append(("P08 管理员获取纠纷列表", r))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_id, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_id}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n[OK] 所有权限测试通过！")
    else:
        print(f"\n[WARN] 有 {total - passed} 项测试失败，请检查")
    
    return passed == total

if __name__ == "__main__":
    main()
