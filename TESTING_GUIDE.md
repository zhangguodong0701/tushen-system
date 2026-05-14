# 图审云平台测试指南

> 基于测试金字塔理论，结合 FastAPI + Vue 3 技术栈的完整测试策略

## 目录

1. [测试金字塔](#测试金字塔)
2. [后端测试（FastAPI + pytest）](#后端测试)
3. [前端测试（Vue 3 + Playwright）](#前端测试)
4. [端到端测试](#端到端测试)
5. [CI/CD 集成](#cicd-集成)
6. [测试数据管理](#测试数据管理)

---

## 测试金字塔

```
        /\
       /E2E\      5-10%  端到端测试（Playwright）
      /______\
     /        \ 
    / Integration\  15-20%  集成测试（API测试）
   /__________\
  /            \
 /   Unit Tests  \  70-80%  单元测试（pytest）
/________________\
```

### 原则
- **单元测试**：最快、最稳定，覆盖核心业务逻辑
- **集成测试**：验证模块间交互（API端点、数据库操作）
- **E2E测试**：模拟真实用户操作，覆盖核心业务流程

---

## 后端测试

### 技术栈
- **pytest**：测试框架
- **httpx + TestClient**：FastAPI 官方测试客户端
- **pytest-cov**：测试覆盖率统计
- **unittest.mock**：模拟外部依赖

### 项目结构

```
backend/
├── routers/
│   ├── auth.py
│   ├── demands.py
│   └── ...
├── tests/
│   ├── conftest.py          # 共享 fixtures
│   ├── test_auth.py         # 认证模块测试
│   ├── test_demands.py     # 需求模块测试
│   ├── test_orders.py      # 订单模块测试
│   └── test_e2e.py        # 端到端流程测试
└── main.py
```

### 核心概念

#### 1. TestClient 使用

```python
# tests/conftest.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login():
    resp = client.post("/api/auth/login", data={
        "username": "13800000000",
        "password": "admin123"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()
```

#### 2. 依赖覆盖（Dependency Override）

```python
# 模拟数据库依赖
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
```

#### 3. 异步测试

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result is not None
```

### 测试覆盖率

```bash
# 运行测试并生成覆盖率报告
cd backend
python -m pytest tests/ -v --cov=. --cov-report=html

# 查看报告
open htmlcov/index.html
```

### 最佳实践

1. **每个测试独立**：使用 fixture 确保每个测试前重置数据库
2. **覆盖边界情况**：正常流程 + 异常处理 + 权限验证
3. **模拟外部依赖**：不要用真实短信/邮件服务
4. **命名清晰**：`test_<功能>_<场景>` 格式

---

## 前端测试

### 技术选型

| 工具 | 用途 | 推荐度 |
|------|------|--------|
| **Playwright** | E2E测试、组件测试 | ⭐⭐⭐⭐⭐ |
| **Vitest** | 单元测试（替代Jest） | ⭐⭐⭐⭐ |
| **Vue Test Utils** | 组件单元测试 | ⭐⭐⭐ |

### Playwright 配置

```bash
# 安装
cd vue-project
npm init playwright@latest

# 运行测试
npx playwright test

# 查看报告
npx playwright show-report
```

### 示例：登录流程测试

```typescript
// tests/e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test('甲方用户登录', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // 填写登录表单
  await page.fill('[name="username"]', '19900000001');
  await page.fill('[name="password"]', 'test1234');
  await page.click('button[type="submit"]');
  
  // 验证登录成功
  await expect(page.locator('text=需求大厅')).toBeVisible();
});
```

---

## 端到端测试

### 核心业务流程

图审云平台的关键流程：

```
1. 用户注册 → 实名认证 → 审核通过
2. 甲方发布需求 → 乙方报价 → 甲方选标
3. 托管付款 → 乙方上传图纸 → 甲方验收
4. 分期付款 → 验收通过 → 自动放款
```

### E2E 测试清单

| 流程 | 优先级 | 覆盖点 |
|------|--------|--------|
| 用户注册+审核 | P0 | 注册→登录→审核→状态变更 |
| 需求发布+报价 | P0 | 发布→报价→选标 |
| 订单支付+验收 | P0 | 托管→上传→验收→放款 |
| 纠纷处理 | P1 | 发起→上传证据→裁决 |
| 互评 | P1 | 完成后互评星级 |

### 远程 E2E 测试

```bash
# 使用项目内置的远程测试脚本
python .workbuddy/skills/tushen-deploy-test/scripts/remote_e2e_test.py
```

---

## CI/CD 集成

### GitHub Actions 配置

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd tushen-system/backend
          pip install -r requirements.txt
          pip install pytest pytest-cov httpx
      - name: Run tests
        run: |
          cd tushen-system/backend
          python -m pytest tests/ -v --cov=. --cov-report=xml

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install & Build
        run: |
          cd tushen-system/vue-project
          npm ci
          npm run build
```

---

## 测试数据管理

### 策略对比

| 策略 | 优点 | 缺点 |
|------|------|------|
| **工厂模式** | 数据一致、易维护 | 初期投入大 |
| **Fixture文件** | 简单直接 | 数据耦合高 |
| **API创建** | 真实流程 | 测试慢 |

### 推荐：工厂模式

```python
# tests/factories.py
import factory
from models import User

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    phone = factory.Sequence(lambda n: f"1380000{n:04d}")
    real_name = factory.Faker("name", locale="zh_CN")
    user_type = "owner"
    status = "通过"
```

### 测试数据清理

```python
# conftest.py
@pytest.fixture(autouse=True)
def cleanup_db():
    """每个测试后清理数据库"""
    yield
    db.query(User).delete()
    db.query(Demand).delete()
    db.commit()
```

---

## 常见问题排查

### 1. 测试数据库污染

**问题**：测试之间数据互相影响

**解决**：
```python
@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    yield session
    session.rollback()  # 回滚而非提交
    session.close()
```

### 2. 异步测试超时

**问题**：异步测试 hanging

**解决**：设置超时 + 使用 `asyncio.wait_for`

### 3. 前端测试元素定位失败

**问题**：元素未加载完成

**解决**：使用 `page.wait_for_selector()` 而非直接操作

---

## 测试指标

| 指标 | 目标 | 当前 |
|------|------|------|
| 单元测试覆盖率 | >80% | - |
| 集成测试覆盖率 | >60% | - |
| E2E测试通过率 | >95% | - |
| 测试执行时间 | <5分钟 | - |

---

## 下一步行动

- [ ] 补充后端单元测试（目标覆盖率80%）
- [ ] 配置 Playwright 前端 E2E 测试
- [ ] 完善 CI/CD 流水线
- [ ] 实现测试报告自动生成

---

*最后更新：2026-05-15*
