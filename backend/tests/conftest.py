# pytest 配置和共享 fixtures
import os
import sys
import pytest
from fastapi.testclient import TestClient

# 确保 backend 目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试数据库路径
TEST_DB_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DB = os.path.join(TEST_DB_DIR, "test_tushen.db")


def _cleanup_db():
    """清理测试数据库文件"""
    import gc
    gc.collect()
    for suffix in ("", "-wal", "-shm"):
        try:
            p = TEST_DB + suffix
            if os.path.exists(p):
                os.remove(p)
        except (PermissionError, OSError):
            pass


def _reset_engine():
    """重新配置 engine 和 SessionLocal 指向测试数据库"""
    _cleanup_db()
    import models
    models.DATABASE_URL = f"sqlite:///{TEST_DB}"
    if hasattr(models, 'engine') and models.engine is not None:
        models.engine.dispose()
    new_engine = models.create_engine(
        models.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    models.engine = new_engine
    models.SessionLocal = models.sessionmaker(autocommit=False, autoflush=False, bind=new_engine)
    models.Base.metadata.create_all(bind=models.engine)


def _reset_rate_limit():
    """重置内存中的速率限制状态"""
    try:
        from main import _rate_limit_store
        _rate_limit_store.clear()
    except Exception:
        pass


@pytest.fixture(scope="function", autouse=True)
def reset_test_env():
    """每个测试前重置数据库和速率限制"""
    _reset_engine()
    _reset_rate_limit()
    yield


@pytest.fixture(scope="function")
def client():
    """返回 TestClient 和 Session"""
    import models
    session = models.SessionLocal()
    from main import app
    tc = TestClient(app)
    yield tc, session
    tc.close()
    session.close()
    models.engine.dispose()
    _reset_rate_limit()
    _cleanup_db()


@pytest.fixture
def admin_token(client):
    """创建管理员并返回 token"""
    tc, session = client
    from models import User
    from auth import get_password_hash, create_access_token

    admin = User(
        phone="13800000000",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        real_name="测试管理员",
        user_type="设计院",
        status="通过",
        is_admin=1,
        company_name="测试公司"
    )
    session.add(admin)
    session.commit()
    return create_access_token({"sub": str(admin.id)})


@pytest.fixture
def jia_user(client):
    """创建甲方用户"""
    tc, session = client
    from models import User
    from auth import get_password_hash, create_access_token

    user = User(
        phone="13900000001",
        email="jia@test.com",
        hashed_password=get_password_hash("test123"),
        real_name="甲方测试",
        user_type="业主",
        status="通过",
        company_name="甲方公司"
    )
    session.add(user)
    session.commit()
    token = create_access_token({"sub": str(user.id)})
    return {"user": user, "token": token}


@pytest.fixture
def yi_user(client):
    """创建乙方用户"""
    tc, session = client
    from models import User
    from auth import get_password_hash, create_access_token

    user = User(
        phone="13900000002",
        email="yi@test.com",
        hashed_password=get_password_hash("test123"),
        real_name="乙方测试",
        user_type="设计院",
        status="通过",
        company_name="乙方公司"
    )
    session.add(user)
    session.commit()
    token = create_access_token({"sub": str(user.id)})
    return {"user": user, "token": token}


@pytest.fixture
def jia_headers(jia_user):
    return {"Authorization": f"Bearer {jia_user['token']}"}


@pytest.fixture
def yi_headers(yi_user):
    return {"Authorization": f"Bearer {yi_user['token']}"}


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_headers(client):
    """返回登录后 header（直接用数据库创建已审核用户）"""
    tc, session = client
    from models import User
    from auth import get_password_hash, create_access_token

    user = User(
        phone="10000000000",
        email="user@test.com",
        hashed_password=get_password_hash("testpass123"),
        real_name="测试用户",
        user_type="业主",
        status="通过"
    )
    session.add(user)
    session.commit()
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}
