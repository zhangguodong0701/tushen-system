from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models import get_db, User
import hashlib
import secrets

SECRET_KEY = "tushen-secret-key-2026-very-secure"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password, hashed_password):
    """验证密码，支持 sha256$salt$hash 和 bcrypt ($2b$) 两种格式"""
    if not hashed_password:
        return False
    # bcrypt 格式 ($2b$)
    if hashed_password.startswith('$2'):
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    # SHA256 格式 sha256$salt$hash
    if hashed_password.startswith('sha256$'):
        try:
            _, salt, stored_hash = hashed_password.split('$', 2)
            hash_obj = hashlib.sha256((salt + plain_password).encode()).hexdigest()
            return hash_obj == stored_hash
        except Exception:
            return False
    return False

def get_password_hash(password):
    """使用 SHA256 生成密码哈希，无长度限制"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"sha256${salt}${hash_obj}"

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id_str)).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
