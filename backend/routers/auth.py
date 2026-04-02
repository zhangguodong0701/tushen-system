# routers/auth.py - 认证相关 API
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import os, uuid

from models import get_db, User
from auth import verify_password, get_password_hash, create_access_token, get_current_user
from schemas import UserRegister, UserUpdate
from utils import user_to_dict, extract_notification_type

router = APIRouter(prefix="/api/auth", tags=["认证"])

# ========== 文件上传配置（复用 main.py 中的逻辑）==========
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".dwg", ".dxf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar"}


def _detect_mime(header_bytes: bytes) -> str:
    if header_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        return "image/png"
    if header_bytes.startswith(b'\xff\xd8\xff'):
        return "image/jpeg"
    if header_bytes.startswith(b'GIF87a') or header_bytes.startswith(b'GIF89a'):
        return "image/gif"
    if header_bytes.startswith(b'RIFF') and header_bytes[8:12] == b'WEBP':
        return "image/webp"
    if header_bytes.startswith(b'%PDF'):
        return "application/pdf"
    if header_bytes.startswith(b'PK\x03\x04'):
        return "application/zip"
    if header_bytes.startswith(b'Rar!\x1a\x07'):
        return "application/x-rar-compressed"
    if header_bytes[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
        return "application/vnd.ms-excel"
    return "application/octet-stream"


ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/zip", "application/x-rar-compressed",
    "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
}

MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", 50)) * 1024 * 1024


def secure_save_file(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"不支持的文件类型: {ext}")
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）")
    if len(content) == 0:
        raise HTTPException(400, "文件不能为空")
    mime_type = _detect_mime(content[:512])
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, f"文件实际类型不允许: {mime_type}")
    fname = f"{uuid.uuid4().hex}{ext}"
    fpath = os.path.join(UPLOAD_DIR, fname)
    with open(fpath, "wb") as f:
        f.write(content)
    return f"/uploads/{fname}"


def _check_rate_limit(ip: str, endpoint: str, limit: int = 10, window: int = 60) -> bool:
    """简单速率限制"""
    from main import _check_rate_limit as _check
    return _check(ip, endpoint, limit, window)


# ========== Auth API ==========
@router.post("/register")
def register(request: Request, data: UserRegister, db: Session = Depends(get_db)):
    from main import _check_rate_limit
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip, "register", limit=3, window=60):
        raise HTTPException(status_code=429, detail="注册过于频繁，请稍后再试")
    if data.phone:
        if db.query(User).filter(User.phone == data.phone).first():
            raise HTTPException(400, "手机号已注册")
    if data.email:
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(400, "邮箱已注册")
    user = User(
        phone=data.phone, email=data.email,
        hashed_password=get_password_hash(data.password),
        real_name=data.real_name, user_type=data.user_type,
        company_name=data.company_name, status="待审核",
        auth_type=data.auth_type or "个人"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "注册成功，等待审核", "user_id": user.id}


@router.post("/login")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    from main import _check_rate_limit
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip, "login", limit=5, window=60):
        raise HTTPException(status_code=429, detail="登录过于频繁，请稍后再试")
    user = db.query(User).filter(
        (User.phone == form_data.username) | (User.email == form_data.username)
    ).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="账号或密码错误")
    if user.status == "待审核":
        raise HTTPException(status_code=403, detail="您的账号正在等待审核，请耐心等待管理员处理")
    if user.status == "已驳回":
        raise HTTPException(status_code=403, detail="您的账号审核未通过，请完善资料后重新注册")
    if user.is_blacklisted == 1:
        raise HTTPException(status_code=403, detail="您的账号已被限制登录，如有疑问请联系客服")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user_to_dict(user)}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return user_to_dict(current_user)


@router.put("/me")
def update_me(data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(current_user, k, v)
    db.commit()
    return user_to_dict(current_user)


@router.post("/upload-cert")
def upload_cert(file: UploadFile = File(...), cert_type: str = Form("license"),
                current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    url = secure_save_file(file)
    if cert_type == "license":
        current_user.license_url = url
    elif cert_type == "id_card_front":
        current_user.id_card_front = url
    elif cert_type == "id_card_back":
        current_user.id_card_back = url
    elif cert_type == "business_license":
        current_user.business_license = url
    else:
        current_user.cert_url = url
    db.commit()
    return {"url": url}


@router.post("/certification")
def submit_certification(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.auth_type == "个人":
        if not current_user.id_card_front or not current_user.id_card_back:
            raise HTTPException(400, "请先上传完整的身份证照片")
    elif current_user.auth_type == "企业":
        if not current_user.business_license:
            raise HTTPException(400, "请先上传营业执照")
    else:
        if not any([current_user.id_card_front, current_user.id_card_back, current_user.business_license]):
            raise HTTPException(400, "请先上传认证资料")
    if current_user.status == "未认证":
        current_user.status = "待审核"
    db.commit()
    return {"message": "认证资料已提交，等待审核", "status": current_user.status}
