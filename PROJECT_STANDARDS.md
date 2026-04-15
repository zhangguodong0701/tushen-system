# 图审云平台开发规范（2026版）

> 本规范基于图审云平台（tushen-system）2026年4月大规模重构的经验总结。
> 所有土神平台开发者必须遵守，违者需提供充分理由。

---

## 一、架构准则

### 1.1 架构师模式（强制）

> **修改任何代码前，必须先扫描全局目录结构，理解模块间的引用关系。**

- 新增 API 端点 → 必须扫描前端所有 `.vue` 文件是否已引用
- 修改枚举值 → 必须扫描所有 routers 和前端组件
- 修改数据库 Schema → 必须全局搜索所有调用者
- 任何 "头痛医头" 的修复必须被回退

### 1.2 顺藤摸瓜（强制）

> **发现一个 Bug，必须交叉检查同类问题，一次性全部修复。**

- 修 `console.error` → 扫描全部 `.vue` 文件
- 修裸 `except:` → 扫描全部 `.py` router 文件
- 修 API 路径 → 同步更新前端 + 测试脚本
- 修枚举值 → 同步更新前后端所有引用

---

## 二、后端规范

### 2.1 状态枚举（强制）

所有业务状态必须定义在 `backend/constants.py`，禁止在 routers 中硬编码状态字符串。

**正确做法：**
```python
from constants import DisputeStatus, OrderStatus

@router.get("/disputes")
def list_disputes(status: Optional[str] = None, ...):
    if status:
        q = q.filter(Dispute.status == status)  # 直接用传入的字符串即可，枚举值已统一
```

**禁止做法：**
```python
# 禁止：硬编码状态字符串
if order.status not in ["进行中", "待验收"]:
    ...

# 禁止：在 routers 中创建局部枚举
class MyStatus(str, Enum):  # 应统一在 constants.py
    ...
```

**现有枚举清单：**
| 枚举类 | 用途 | 所在文件 |
|--------|------|----------|
| `UserStatus` | 用户状态 | constants.py |
| `DemandStatus` | 需求状态 | constants.py |
| `QuoteStatus` | 报价状态 | constants.py |
| `OrderStatus` | 订单状态 | constants.py |
| `PhaseStatus` | 订单阶段状态 | constants.py |
| `DisputeStatus` | 纠纷状态 | constants.py |
| `FeedbackStatus` | 反馈状态 | constants.py |

> **注意**：`PhaseStatus` 与 `OrderStatus` 是**不同语义**：`OrderStatus.completed = "已完成"`（订单完成），`PhaseStatus.completed = "已验收"`（阶段验收）。不可混用。

### 2.2 异常处理（强制）

禁止使用裸 `except:`，必须指定具体异常类型：

```python
# ✅ 正确
try:
    files = json.loads(dispute.evidence_files)
except (json.JSONDecodeError, TypeError, ValueError):
    pass

# ❌ 禁止
try:
    files = json.loads(dispute.evidence_files)
except:
    pass
```

### 2.3 日志规范

如需记录日志，使用 `backend/utils/logger.py`：

```python
from utils.logger import get_logger
logger = get_logger(__name__)

logger.info("用户登录: %s", phone)
logger.error("订单创建失败: %s", str(e))
```

**禁止在生产代码中使用 `print()`**（调试脚本除外）。

### 2.4 API 路径规范（RESTful）

| 规则 | 说明 | 示例 |
|------|------|------|
| 资源用单数名词 | `/api/feedback` | 不是 `/api/feedbacks` |
| 管理员子资源 | `/api/admin/feedback` | 管理员专属端点用 admin 前缀 |
| 动词用 HTTP 方法 | GET 查 / POST 增 / PUT 改 / DELETE 删 | - |
| ID 放路径参数 | `/api/demands/{id}` | 不是 query 参数 |

**已验证的 API 端点规范（防踩坑）：**
- 通知标记已读：`POST /api/notifications/{id}/read`（不是 PUT）
- 订单验收：`POST /api/orders/{id}/accept`（不是 `/complete`）
- 解除黑名单：`POST /api/admin/users/{id}/unblacklist`（不是 DELETE）
- 投诉反馈：`GET/POST /api/feedback`（单数，不是 feedbacks）
- 管理员反馈：`GET /api/admin/feedback`（单数，不是 feedbacks）
- 反馈回复：`POST /api/admin/feedback/{id}/reply`（不是 query 参数）

### 2.5 数据库 Schema 规则

- 新增字段需同步：`ALTER TABLE` 迁移脚本 + 后端 model 默认值
- 外键关系需明确注释
- `User` 模型**无** `username` 字段，登录标识为 `phone`
- 分阶段付款由甲方选标后**自动创建**订单和 `PaymentPhase` 记录
- `PaymentPhase` 有 `ratio`（比例）和 `phase_order`（序号）字段

---

## 三、前端规范

### 3.1 API 响应处理（强制）

后端 API 列表接口返回两种格式，**必须统一处理**：

```javascript
// ✅ 方式1：使用 safeGet（推荐新代码）
const { items, _raw } = await api.safeGet('/api/feedback')
feedbacks.value = items
const total = _raw.total  // 如需元数据

// ✅ 方式2：手动兜底（现有代码兼容）
feedbacks.value = data.items || data || []

// ❌ 禁止：假设某种格式存在
feedbacks.value = data.items  // data 可能直接是数组
feedbacks.value = data  // data 可能包含分页元数据
```

### 3.2 错误提示规范（强制）

**禁止**在生产代码中使用 `console.error()` 向控制台输出错误信息。

用户可见错误必须使用 `authStore.toast()`：

```javascript
// ✅ 正确
} catch (e) {
  authStore.toast('加载失败，请重试', 'error')
}

// ✅ 非关键错误可静默（但需有充分理由）
} catch (e) {
  // 保存登录历史失败不影响登录，静默忽略
}
```

**非关键操作可静默**，但必须在注释中说明理由。

### 3.3 组件导入规范

所有 `.vue` 文件统一使用 `@` 路径别名：

```javascript
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api'
```

禁止使用相对路径 `../stores/auth`。

### 3.4 角色判断

前端根据 `user_type` + `is_admin` 判断用户角色：

```javascript
const isBuyer = computed(() => JIA_FANG_TYPES.includes(user.value?.user_type) && user.value?.is_admin !== 1)
const isSeller = computed(() => YI_FANG_TYPES.includes(user.value?.user_type) && user.value?.is_admin !== 1)
```

管理员和审核员**不参与**甲乙方分类。

---

## 四、测试规范

### 4.1 提交前必测

- 前端：`npm run build` 必须成功
- 后端：pytest 单元测试（如果有）
- 端到端：`python remote_e2e_test.py` 验证核心流程

### 4.2 API 测试脚本维护

测试脚本中的 API 路径必须与后端路由**严格一致**：

- 修改 `/api/admin/feedbacks` → `/api/admin/feedback` 后，**必须**同步更新 `test_system.py` 和 `test_full.py`
- 测试脚本也需处理分页格式（`data.items` vs `data`）
- 回复接口改用 `json_data={...}` 而非 `params={...}`

### 4.3 进化引擎

自进化测试系统记录问题特征库：
- 特征库位置：`~/.workbuddy/skills/tushen-deploy-test/test_history/issues.jsonl`
- 每次运行自动匹配历史并记录新问题
- 目标：同类问题第二次出现时，直接给出诊断结果

---

## 五、部署规范

### 5.1 发布流程

```bash
# 1. 本地提交
git add -A && git commit -m "描述" && git push

# 2. 服务器拉取
ssh root@60.205.220.62 "cd /home/admin/tushen-system && git pull"

# 3. 前端构建
cd vue-project && npm install && npm run build

# 4. 部署静态文件
cp -r dist/. /usr/share/nginx/html/

# 5. 重载 Nginx
docker exec tushen-frontend nginx -s reload
```

### 5.2 环境变量

| 变量 | 用途 | 生产建议 |
|------|------|----------|
| `DATABASE_URL` | MySQL 连接字符串 | 必须设置 |
| `DISABLE_RATE_LIMIT=1` | 关闭限流 | 仅测试环境 |
| `CORS_ORIGINS` | CORS 白名单 | 生产指定域名 |

### 5.3 Docker 部署

```bash
docker-compose up -d  # 后端 + MySQL
docker exec tushen-frontend nginx -s reload  # 前端更新后重载
```

---

## 六、已知坑点（持续积累）

### 6.1 后端

| 坑 | 原因 | 解决方案 |
|----|------|----------|
| N+1 查询 | 循环内查数据库 | `func.sum()` 聚合函数替代内存遍历 |
| 裸 `except:` | 吞掉所有异常 | 指定 `json.JSONDecodeError+TypeError+ValueError` |
| 硬编码状态字符串 | 前后端不联动 | 统一在 `constants.py`，模型 default 用 `.value` |
| 错误接口方法 | 记忆模糊 | 参见 2.4 API 路径规范表 |

### 6.2 前端

| 坑 | 原因 | 解决方案 |
|----|------|----------|
| `console.error` 残留 | 调试代码未清理 | 改用 `authStore.toast()` |
| API 响应格式不一致 | 分页 vs 直接数组 | 使用 `api.safeGet()` 或手动 `data.items \|\| data \|\| []` |
| 路径不一致 | 后端改了前端没改 | 顺藤摸瓜，测试脚本同步更新 |
| 双写 `getHeaders()` | 编辑器插入位置错误 | 避免手动拼接，先读完整文件再改 |

### 6.3 数据库

| 坑 | 原因 | 解决方案 |
|----|------|----------|
| SQLite 缺 `group_id` 列 | 本地 DB 版本不一致 | `ALTER TABLE drawings ADD COLUMN group_id INTEGER` |
| 旧数据库缺 `ratio` 列 | 分阶段付款功能新增 | `ALTER TABLE payment_phases ADD COLUMN ratio FLOAT` |

---

## 七、目录结构速查

```
tushen-system/
├── backend/
│   ├── main.py              # FastAPI 入口、安全头、CORS
│   ├── models.py            # SQLAlchemy 模型
│   ├── schemas.py           # Pydantic 请求/响应模型
│   ├── constants.py         # 状态枚举（必读！）
│   ├── utils.py             # 分页、加密等工具
│   └── utils/logger.py      # 统一日志模块
│       └── routers/
│           ├── auth.py      # 认证（限流开关在此）
│           ├── demands.py   # 需求
│           ├── orders.py    # 订单（含分阶段付款）
│           ├── drawings.py  # 图纸
│           ├── disputes.py  # 纠纷
│           ├── notifications.py
│           ├── feedback.py  # 投诉反馈
│           └── admin.py     # 管理员后台
├── vue-project/
│   └── src/
│       ├── api/index.js     # API 封装（含 safeGet）
│       ├── stores/auth.js   # Pinia store（含 toast）
│       ├── views/           # 页面组件
│       └── router/index.js  # 路由
└── docker-compose.yml
```

---

## 八、版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| v1.0 | 2026-04-15 | 初始版本，含 Phase 1-3 重构规范 |
