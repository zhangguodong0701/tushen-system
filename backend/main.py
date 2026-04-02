# main.py - 图审云平台后端入口
# 加载 .env 环境变量（必须在其他模块之前）
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# 安全中间件
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """添加安全响应头"""
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        return response

# 速率限制
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    limiter = Limiter(key_func=get_remote_address)
    SLOWAPI_ENABLED = True
except ImportError:
    limiter = None
    SLOWAPI_ENABLED = False

from models import init_db, get_db, User
from auth import get_password_hash

# 速率限制存储（内存）
_rate_limit_store: dict = {}

def _check_rate_limit(ip: str, endpoint: str, limit: int = 10, window: int = 60) -> bool:
    """简单速率限制：每分钟最多 limit 次请求"""
    key = f"{ip}:{endpoint}"
    now = datetime.utcnow().timestamp()
    if key not in _rate_limit_store:
        _rate_limit_store[key] = []
    _rate_limit_store[key] = [t for t in _rate_limit_store[key] if now - t < window]
    if len(_rate_limit_store[key]) >= limit:
        return False
    _rate_limit_store[key].append(now)
    return True

# ========== FastAPI App ==========
app = FastAPI(title="图审系统API", version="1.0.0")

# 安全头中间件
app.add_middleware(SecurityHeadersMiddleware)

# CORS 配置
# 开发环境支持所有来源，生产环境请设置 CORS_ORIGINS 环境变量
_cors_env = os.environ.get("CORS_ORIGINS", "")
ALLOWED_ORIGINS = [o.strip() for o in _cors_env.split(",") if o.strip()] if _cors_env else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# 静态文件服务
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 注册速率限制器
if SLOWAPI_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ========== 注册路由模块 ==========
from routers import (
    auth_router,
    demands_router,
    orders_router,
    drawings_router,
    notifications_router,
    disputes_router,
    admin_router,
    feedback_router,
)

app.include_router(auth_router)
app.include_router(demands_router)
app.include_router(orders_router)
app.include_router(drawings_router)
app.include_router(notifications_router)
app.include_router(disputes_router)
app.include_router(admin_router)
app.include_router(feedback_router)

# ========== 启动事件 ==========
@app.on_event("startup")
def startup():
    init_db()
    db = next(get_db())
    admin = db.query(User).filter(User.is_admin == 1).first()
    if not admin:
        admin_user = User(
            phone="13800000000",
            email="admin@tushen.com",
            hashed_password=get_password_hash("admin123"),
            real_name="系统管理员",
            user_type="设计院",
            status="通过",
            is_admin=1,
            company_name="图审平台"
        )
        db.add(admin_user)
    reviewer = db.query(User).filter(User.is_reviewer == 1).first()
    if not reviewer:
        reviewer_user = User(
            phone="13900000000",
            email="reviewer@tushen.com",
            hashed_password=get_password_hash("reviewer123"),
            real_name="平台审核员",
            user_type="设计师",
            status="通过",
            is_reviewer=1,
            company_name="图审平台"
        )
        db.add(reviewer_user)
    db.commit()
    db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
