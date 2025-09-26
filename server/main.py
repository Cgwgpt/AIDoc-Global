from typing import List, Optional, Dict, Any, Iterator
from datetime import date

import os
import json
import requests
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, RedirectResponse
from pydantic import BaseModel, Field, EmailStr
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from .db import Base, engine, get_db, User, Subscription, UsageEvent, run_simple_migrations
from .config import upstream_config
from sqlalchemy import func


# 使用配置管理系统获取上游服务URL和模型
UPSTREAM_BASE_URL = upstream_config.get_current_upstream()
DEFAULT_MODEL = upstream_config.get_current_model()

SYSTEM_PROMPT = (
    "你是一名专业的AI医疗助手，擅长医学影像与临床问答。"
    "基于可靠医学证据进行分析，回答需结构化、清晰、审慎。"
    "请声明：本回答仅供参考，不能替代专业医生的诊断或治疗建议。"
)

class GenerateRequest(BaseModel):
    model: str = Field(
        default=DEFAULT_MODEL,
        description="模型名称或路径",
    )
    prompt: str = Field(..., description="用户输入的提示")
    images: Optional[List[str]] = Field(
        default=None, description="可选：图像的base64数组(不带前缀)"
    )
    stream: bool = Field(default=False, description="是否流式返回")


def _upstream_headers() -> Dict[str, str]:
    return {"Content-Type": "application/json"}


def _stream_generate(payload: Dict[str, Any]) -> Iterator[bytes]:
    # 动态获取当前上游服务URL
    current_upstream = upstream_config.get_current_upstream()
    url = f"{current_upstream}/api/generate"
    with requests.post(url, headers=_upstream_headers(), json=payload, stream=True) as r:
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        # 兼容上游两种行为：SSE 或按行返回JSON片段
        for line in r.iter_lines():
            if not line:
                continue
            # 直接转发
            yield line + b"\n"


app = FastAPI(title="诊疗助手后端", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载前端静态资源
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
static_dir = os.path.join(base_dir, "static")
if os.path.isdir(static_dir):
    app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="static")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui/")


@app.post("/api/generate")
def proxy_generate(
    req: GenerateRequest,
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    payload: Dict[str, Any] = req.model_dump()

    # 模型校验与强制 - 使用当前配置的模型
    payload["model"] = upstream_config.get_current_model()

    # 注入系统提示到 prompt（非 chat 模式下）
    user_prompt: str = payload.get("prompt", "")
    if user_prompt:
        payload["prompt"] = f"[系统]\n{SYSTEM_PROMPT}\n\n[用户]\n{user_prompt}\n\n[助手]"

    # 用量限制（可选，由管理员为用户设置 usage_quota）
    if x_user_id is not None:
        user = db.query(User).filter(User.id == x_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户未找到")
        if user.status != "active":
            raise HTTPException(status_code=403, detail="用户已禁用")
        # 日配额重置：每日首次请求时
        from datetime import date
        today = date.today()
        if user.daily_reset_at != today:
            user.daily_reset_at = today
            user.daily_used = 0
            db.add(user)
            db.commit()
        if user.usage_quota is not None and user.usage_used >= user.usage_quota:
            raise HTTPException(status_code=429, detail="已达到总配额上限; 请联系商务电话: 18959650938,陈先生")
        if user.daily_quota is not None and user.daily_used >= user.daily_quota:
            raise HTTPException(status_code=429, detail="已达到日配额上限; 请联系商务电话: 18959650938,陈先生")

    # 直连上游
    if req.stream:
        resp = StreamingResponse(_stream_generate(payload), media_type="text/event-stream")
        # 流式响应暂不精确计数，按1次计
        if x_user_id is not None:
            user.usage_used += 1
            user.daily_used += 1
            db.add(user)
            db.commit()
            try:
                evt = UsageEvent(user_id=user.id, event_type="generate", tokens_used=None, latency_ms=None, meta=json.dumps({"stream": True}))
                db.add(evt)
                db.commit()
            except Exception:
                db.rollback()
        return resp

    # 动态获取当前上游服务URL
    current_upstream = upstream_config.get_current_upstream()
    url = f"{current_upstream}/api/generate"
    try:
        r = requests.post(url, headers=_upstream_headers(), json=payload, timeout=120)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=str(e))

    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    try:
        data = r.json()
        if x_user_id is not None:
            user.usage_used += 1
            user.daily_used += 1
            db.add(user)
            db.commit()
            try:
                latency_ms = None
                evt = UsageEvent(user_id=user.id, event_type="generate", tokens_used=None, latency_ms=latency_ms, meta=json.dumps({"stream": False}))
                db.add(evt)
                db.commit()
            except Exception:
                db.rollback()
        return data
    except json.JSONDecodeError:
        # 上游非JSON时回传原文
        return {"response": r.text}
# 管理员简单鉴权（演示用）：通过请求头 X-Admin-Token 与环境变量 ADMIN_TOKEN 比对
def require_admin(x_admin_token: Optional[str] = Header(default=None)) -> None:
    expected = os.getenv("ADMIN_TOKEN")
    if not expected:
        # 未设置 ADMIN_TOKEN 时，默认拒绝
        raise HTTPException(status_code=401, detail="未配置管理员令牌")
    if x_admin_token != expected:
        raise HTTPException(status_code=403, detail="管理员令牌无效")


# 多租户权限控制：获取当前用户并验证权限

def get_current_user(
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户"""
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="用户未登录")
    user = db.query(User).filter(User.id == x_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="账户已被禁用")
    return user

# 权限依赖
def require_system_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求系统管理员权限（全局最高权限）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要系统管理员权限")
    return current_user

def require_hospital_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求医院管理员权限（仅本租户）"""
    if current_user.role != "hospital_admin":
        raise HTTPException(status_code=403, detail="需要医院管理员权限")
    return current_user

def require_regular_user(current_user: User = Depends(get_current_user)) -> User:
    """要求普通用户权限"""
    if current_user.role != "user":
        raise HTTPException(status_code=403, detail="需要普通用户权限")
    return current_user

def require_hospital_admin_or_system_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求医院管理员或系统管理员权限"""
    if current_user.role not in ("admin", "hospital_admin"):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user

# 租户隔离依赖
def get_tenant_id(current_user: User = Depends(get_current_user)) -> int:
    """获取当前用户所属租户ID"""
    return current_user.tenant_id

def tenant_data_filter(query, tenant_id: int, model_cls):
    """对SQLAlchemy查询自动加租户隔离"""
    return query.filter(model_cls.tenant_id == tenant_id)


def require_system_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求系统管理员权限"""
    if not current_user.is_admin or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要系统管理员权限")
    return current_user


def require_hospital_admin_or_system_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求医院管理员或系统管理员权限"""
    if not (current_user.is_admin or current_user.role == "hospital_admin"):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


def get_organization_filter(current_user: User, organization: Optional[str] = None) -> str:
    """根据用户权限获取机构过滤条件（兼容老逻辑，建议新代码用tenant_id隔离）"""
    if current_user.role == "admin":
        return organization if organization else None
    else:
        return current_user.organization




# -----------------------------
# 用户与订阅：Schemas 与 Endpoints
# -----------------------------

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class UserRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    organization: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=5, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    organization: Optional[str] = None
    phone: Optional[str] = None
    is_admin: Optional[bool] = False
    usage_quota: Optional[int] = None
    usage_used: Optional[int] = 0
    daily_quota: Optional[int] = None
    daily_used: Optional[int] = 0
    daily_reset_at: Optional[date] = None
    status: Optional[str] = "active"
    role: Optional[str] = "user"

    class Config:
        from_attributes = True


class SubscriptionUpsertRequest(BaseModel):
    plan: str = Field(default="free")
    status: str = Field(default="active")
    auto_renew: bool = Field(default=True)


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    plan: str
    status: str
    auto_renew: bool

    class Config:
        from_attributes = True


def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)


@app.on_event("startup")
def on_startup() -> None:
    # 初始化表
    Base.metadata.create_all(bind=engine)
    # 运行简单迁移（为已有 users 表添加新增列）
    run_simple_migrations()


@app.post("/api/users/register", response_model=UserResponse)
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    # 唯一性检查
    exists = db.query(User).filter(User.email == req.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        name=req.name,
        organization=req.organization,
        phone=req.phone,
        usage_quota=6,  # 新注册用户默认配额为6
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 默认创建订阅记录
    sub = Subscription(user_id=user.id, plan="free", status="active", auto_renew=True)
    db.add(sub)
    db.commit()

    return user


@app.post("/api/users/login", response_model=UserResponse)
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    """
    用户登录API - 安全验证用户身份
    """
    # 查找用户
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    
    # 验证密码
    if not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    
    # 检查用户状态（如果有状态字段的话）
    if hasattr(user, 'status') and user.status == 'disabled':
        raise HTTPException(status_code=403, detail="账户已被禁用")
    
    # 返回用户信息（不包含敏感信息）
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        organization=user.organization,
        phone=user.phone,
        is_admin=user.is_admin or False,  # 确保管理员权限基于数据库字段
        usage_quota=user.usage_quota,
        usage_used=user.usage_used,
        daily_quota=user.daily_quota,
        daily_used=user.daily_used,
        daily_reset_at=user.daily_reset_at,
        status=user.status,
        role=user.role,
    )


class AdminUserUpsertRequest(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    organization: Optional[str] = None
    phone: Optional[str] = None
    is_admin: Optional[bool] = None
    usage_quota: Optional[int] = None
    daily_quota: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


@app.get("/api/admin/users", response_model=List[UserResponse])


def admin_list_users(
    x_user_id: Optional[int] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
):
    """列出用户 - 系统管理员可看所有，医院管理员仅看本租户。支持x_user_id和x_admin_token两种方式。"""
    # 优先支持ADMIN_TOKEN
    if x_admin_token:
        expected = os.getenv("ADMIN_TOKEN")
        if not expected or x_admin_token != expected:
            raise HTTPException(status_code=403, detail="管理员令牌无效")
        # 系统管理员：可看所有用户
        users = db.query(User).order_by(User.id.asc()).all()
        return users
    # 否则用x_user_id
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="用户未登录")
    current_user = get_current_user(x_user_id, db)
    query = db.query(User)
    if current_user.role == "admin":
        users = query.order_by(User.id.asc()).all()
        return users
    elif current_user.role == "hospital_admin":
        users = query.filter(User.tenant_id == current_user.tenant_id).order_by(User.id.asc()).all()
        return users
    else:
        raise HTTPException(status_code=403, detail="无权访问用户列表")


# 分页与排序

@app.get("/api/admin/users:paged", response_model=List[UserResponse])
def admin_list_users_paged(
    page: int = 1,
    size: int = 20,
    sort: str = "id",
    order: str = "asc",
    search: Optional[str] = None,
    current_user: User = Depends(require_hospital_admin_or_system_admin),
    db: Session = Depends(get_db),
):
    """分页列出用户 - 按租户隔离，支持搜索"""
    page = max(1, page)
    size = max(1, min(200, size))
    sort_field = getattr(User, sort, User.id)
    q = db.query(User)
    if current_user.role == "admin":
        pass
    elif current_user.role == "hospital_admin":
        q = q.filter(User.tenant_id == current_user.tenant_id)
    else:
        raise HTTPException(status_code=403, detail="无权访问用户列表")
    if search:
        like = f"%{search}%"
        q = q.filter((User.name.ilike(like)) | (User.email.ilike(like)) | (User.organization.ilike(like)))
    q = q.order_by(sort_field.asc() if order != "desc" else sort_field.desc())
    return q.offset((page - 1) * size).limit(size).all()


# 分页返回 items+total

@app.get("/api/admin/users:paged2")
def admin_list_users_paged2(
    page: int = 1,
    size: int = 20,
    sort: str = "id",
    order: str = "asc",
    search: Optional[str] = None,
    current_user: User = Depends(require_hospital_admin_or_system_admin),
    db: Session = Depends(get_db),
):
    """分页返回用户列表和总数 - 按租户隔离，支持搜索"""
    page = max(1, page)
    size = max(1, min(200, size))
    sort_field = getattr(User, sort, User.id)
    q = db.query(User)
    count_query = db.query(func.count(User.id))
    if current_user.role == "admin":
        pass
    elif current_user.role == "hospital_admin":
        q = q.filter(User.tenant_id == current_user.tenant_id)
        count_query = count_query.filter(User.tenant_id == current_user.tenant_id)
    else:
        raise HTTPException(status_code=403, detail="无权访问用户列表")
    if search:
        like = f"%{search}%"
        q = q.filter((User.name.ilike(like)) | (User.email.ilike(like)) | (User.organization.ilike(like)))
        count_query = count_query.filter((User.name.ilike(like)) | (User.email.ilike(like)) | (User.organization.ilike(like)))
    total = count_query.scalar() or 0
    q = q.order_by(sort_field.asc() if order != "desc" else sort_field.desc())
    items = q.offset((page - 1) * size).limit(size).all()
    return {"items": items, "total": total}


@app.post("/api/admin/users", response_model=UserResponse)
def admin_create_user(
    payload: UserRegisterRequest,
    x_admin_token: Optional[str] = Header(default=None),
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    """创建用户 - 支持多租户权限控制"""
    # 兼容旧的ADMIN_TOKEN方式和新的用户权限方式
    if x_admin_token:
        # 使用旧的ADMIN_TOKEN方式
        expected = os.getenv("ADMIN_TOKEN")
        if not expected or x_admin_token != expected:
            raise HTTPException(status_code=403, detail="管理员令牌无效")
        current_user = None  # 系统管理员，无机构限制
    elif x_user_id:
        # 使用新的用户权限方式
        current_user = get_current_user(x_user_id, db)
        if not current_user.is_admin and current_user.role != "hospital_admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
    else:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 医院管理员只能在自己机构和租户内创建用户，tenant_id强制为自己租户
    tenant_id = None
    if current_user and current_user.role == "hospital_admin":
        if payload.organization != current_user.organization:
            raise HTTPException(status_code=403, detail="只能在自己机构内创建用户")
        tenant_id = current_user.tenant_id
    elif current_user and current_user.role == "admin":
        # 系统管理员可指定租户，若未指定则默认1
        tenant_id = getattr(payload, "tenant_id", 1)
    else:
        tenant_id = 1

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        organization=payload.organization,
        phone=payload.phone,
        role="user",  # 新创建的用户默认为普通用户
        usage_quota=6,  # 新创建用户默认配额为6
        tenant_id=tenant_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.patch("/api/admin/users/{user_id}", response_model=UserResponse)
def admin_update_user(
    user_id: int,
    payload: AdminUserUpsertRequest,
    x_admin_token: Optional[str] = Header(default=None),
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    """更新用户信息 - 支持多租户权限控制"""
    # 兼容旧的ADMIN_TOKEN方式和新的用户权限方式
    if x_admin_token:
        # 使用旧的ADMIN_TOKEN方式
        expected = os.getenv("ADMIN_TOKEN")
        if not expected or x_admin_token != expected:
            raise HTTPException(status_code=403, detail="管理员令牌无效")
        current_user = None  # 系统管理员，无机构限制
    elif x_user_id:
        # 使用新的用户权限方式
        current_user = get_current_user(x_user_id, db)
        if not current_user.is_admin and current_user.role != "hospital_admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
    else:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")
    
    # 医院管理员只能修改自己机构的用户
    if current_user is not None:
        if current_user.role == "hospital_admin" and not current_user.is_admin:
            if user.organization != current_user.organization:
                raise HTTPException(status_code=403, detail="只能修改本机构用户")
    
    if payload.email is not None:
        # 检查邮箱唯一
        exists = db.query(User).filter(User.email == payload.email, User.id != user_id).first()
        if exists:
            raise HTTPException(status_code=400, detail="邮箱已被占用")
        user.email = payload.email
    if payload.name is not None:
        user.name = payload.name
    if payload.organization is not None:
        # 医院管理员不能修改用户所属机构
        if current_user is not None and current_user.role == "hospital_admin" and not current_user.is_admin:
            if payload.organization != current_user.organization:
                raise HTTPException(status_code=403, detail="不能修改用户所属机构")
        user.organization = payload.organization
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.is_admin is not None:
        # 只有系统管理员才能修改管理员权限
        if current_user is not None and not (current_user.role == "admin" or current_user.is_admin):
            raise HTTPException(status_code=403, detail="只有系统管理员才能修改管理员权限")
        user.is_admin = payload.is_admin
    if payload.usage_quota is not None:
        user.usage_quota = payload.usage_quota
    if payload.daily_quota is not None:
        user.daily_quota = payload.daily_quota
    if payload.status is not None:
        user.status = payload.status
    if payload.notes is not None:
        user.notes = payload.notes
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(
    user_id: int,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")
    db.delete(user)
    db.commit()
    return {"message": "已删除"}


# 管理员：搜索用户（email/name/phone 模糊匹配）
@app.get("/api/admin/users:search", response_model=List[UserResponse])
def admin_search_users(
    q: Optional[str] = None,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = db.query(User)
    if q:
        like = f"%{q}%"
        stmt = stmt.filter(
            (User.email.like(like)) | (User.name.like(like)) | (User.phone.like(like))
        )
    return stmt.order_by(User.id.asc()).all()


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=6, max_length=128)


@app.post("/api/admin/users/{user_id}:reset-password")
def admin_reset_password(
    user_id: int,
    payload: AdminResetPasswordRequest,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")
    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.commit()
    return {"message": "密码已重置"}


@app.post("/api/admin/users/{user_id}:reset-usage")
def admin_reset_usage(
    user_id: int,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")
    user.usage_used = 0
    user.daily_used = 0
    db.add(user)
    db.commit()
    return {"message": "用量已重置"}


# 简单CSV导出（所有用户）
from fastapi.responses import PlainTextResponse


@app.get("/api/admin/users:export-csv", response_class=PlainTextResponse)
def admin_export_csv(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(User).order_by(User.id.asc()).all()
    headers = [
        "id",
        "email",
        "name",
        "organization",
        "phone",
        "is_admin",
        "status",
        "usage_quota",
        "usage_used",
        "daily_quota",
        "daily_used",
    ]
    out = [";".join(headers)]
    for u in rows:
        out.append(
            ";".join(
                [
                    str(u.id),
                    u.email or "",
                    u.name or "",
                    u.organization or "",
                    u.phone or "",
                    "1" if u.is_admin else "0",
                    u.status or "",
                    "" if u.usage_quota is None else str(u.usage_quota),
                    str(u.usage_used or 0),
                    "" if u.daily_quota is None else str(u.daily_quota),
                    str(u.daily_used or 0),
                ]
            )
        )
    return "\n".join(out)


# CSV 导入（upsert by email）
from fastapi import UploadFile, File


@app.post("/api/admin/users:import-csv")
async def admin_import_users_csv(
    file: UploadFile = File(...),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return {"imported": 0}
    header = [h.strip() for h in lines[0].split(";")]
    idx = {name: i for i, name in enumerate(header)}
    cnt = 0
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(";")]
        email = parts[idx.get("email", -1)] if idx.get("email") is not None else None
        if not email:
            continue
        user = db.query(User).filter(User.email == email).first()
        def getv(key):
            i = idx.get(key)
            return parts[i] if (i is not None and i < len(parts)) else None
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password("changeme123"),
                name=getv("name") or None,
                organization=getv("organization") or None,
                phone=getv("phone") or None,
            )
            db.add(user)
        # upsert fields
        uq = getv("usage_quota")
        dq = getv("daily_quota")
        user.name = getv("name") or user.name
        user.organization = getv("organization") or user.organization
        user.phone = getv("phone") or user.phone
        user.status = getv("status") or user.status
        user.notes = getv("notes") or user.notes
        user.is_admin = (getv("is_admin") == "1") if getv("is_admin") is not None else user.is_admin
        user.usage_quota = int(uq) if (uq not in (None, "")) else user.usage_quota
        user.daily_quota = int(dq) if (dq not in (None, "")) else user.daily_quota
        cnt += 1
    db.commit()
    return {"imported": cnt}


# 用量汇总（按时间范围）
from datetime import datetime


@app.get("/api/admin/usage:summary")
def admin_usage_summary(
    start: Optional[str] = None,
    end: Optional[str] = None,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    # 仅统计事件数量
    q = db.query(UsageEvent)
    def parse_dt(s):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None
    sdt = parse_dt(start)
    edt = parse_dt(end)
    if sdt:
        q = q.filter(UsageEvent.created_at >= sdt)
    if edt:
        q = q.filter(UsageEvent.created_at <= edt)
    total = q.count()
    return {"total_events": total, "window": {"start": start, "end": end}}


@app.get("/api/admin/usage:by-user")
def admin_usage_by_user(
    start: Optional[str] = None,
    end: Optional[str] = None,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from datetime import datetime
    def parse_dt(s):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None
    sdt = parse_dt(start)
    edt = parse_dt(end)
    q = db.query(UsageEvent.user_id.label("user_id"), func.count(UsageEvent.id).label("count"))
    if sdt:
        q = q.filter(UsageEvent.created_at >= sdt)
    if edt:
        q = q.filter(UsageEvent.created_at <= edt)
    q = q.group_by(UsageEvent.user_id).order_by(func.count(UsageEvent.id).desc())
    rows = q.all()
    return [{"user_id": r.user_id, "count": r.count} for r in rows]


@app.get("/api/admin/usage:by-day")
def admin_usage_by_day(
    start: Optional[str] = None,
    end: Optional[str] = None,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from datetime import datetime
    def parse_dt(s):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None
    sdt = parse_dt(start)
    edt = parse_dt(end)
    # SQLite: 使用 date() 提取日期
    day_expr = func.date(UsageEvent.created_at)
    q = db.query(day_expr.label("day"), func.count(UsageEvent.id).label("count"))
    if sdt:
        q = q.filter(UsageEvent.created_at >= sdt)
    if edt:
        q = q.filter(UsageEvent.created_at <= edt)
    q = q.group_by(day_expr).order_by(day_expr.asc())
    rows = q.all()
    return [{"date": r.day, "count": r.count} for r in rows]


@app.get("/api/users/{user_id}/subscription", response_model=SubscriptionResponse)
def get_subscription(user_id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅未找到")
    return sub


class PasswordChangeRequest(BaseModel):
    old_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


@app.post("/api/users/{user_id}/password:change")
def change_password(user_id: int, req: PasswordChangeRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # 校验旧密码
    if not pwd_context.verify(req.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")

    user.password_hash = hash_password(req.new_password)
    db.add(user)
    db.commit()
    return {"message": "密码已更新"}


@app.put("/api/users/{user_id}/subscription", response_model=SubscriptionResponse)
def upsert_subscription(
    user_id: int,
    req: SubscriptionUpsertRequest,
    db: Session = Depends(get_db),
):
    # 确认用户存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if sub is None:
        sub = Subscription(
            user_id=user_id,
            plan=req.plan,
            status=req.status,
            auto_renew=req.auto_renew,
        )
        db.add(sub)
    else:
        sub.plan = req.plan
        sub.status = req.status
        sub.auto_renew = req.auto_renew

    db.commit()
    db.refresh(sub)
    return sub


# -----------------------------
# 上游服务配置管理API
# -----------------------------

class UpstreamServiceRequest(BaseModel):
    name: str = Field(..., description="服务名称")
    url: str = Field(..., description="服务URL")
    model: str = Field(default="hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M", description="模型名称")
    description: str = Field(default="", description="服务描述")
    enabled: bool = Field(default=True, description="是否启用")

class UpstreamServiceResponse(BaseModel):
    key: str
    name: str
    url: str
    model: str
    description: str
    enabled: bool
    is_current: bool = False

class SwitchUpstreamRequest(BaseModel):
    service_key: str = Field(..., description="要切换到的服务键名")

@app.get("/api/admin/upstream-services", response_model=List[UpstreamServiceResponse])
def admin_list_upstream_services(
    x_admin_token: Optional[str] = Header(default=None),
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    """列出所有上游服务配置"""
    # 兼容旧的ADMIN_TOKEN方式和新的用户权限方式（系统管理员）
    if x_admin_token:
        expected = os.getenv("ADMIN_TOKEN")
        if not expected or x_admin_token != expected:
            raise HTTPException(status_code=403, detail="管理员令牌无效")
    elif x_user_id:
        current_user = get_current_user(x_user_id, db)
        if not current_user.is_admin or current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要系统管理员权限")
    else:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    services = upstream_config.get_all_services()
    current_key = upstream_config.config.get("current_upstream", "default")
    
    result = []
    for key, service in services.items():
        result.append(UpstreamServiceResponse(
            key=key,
            name=service["name"],
            url=service["url"],
            model=service.get("model", "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M"),
            description=service.get("description", ""),
            enabled=service.get("enabled", True),
            is_current=(key == current_key)
        ))
    
    return result

@app.post("/api/admin/upstream-services", response_model=UpstreamServiceResponse)
def admin_add_upstream_service(
    service_key: str,
    request: UpstreamServiceRequest,
    x_admin_token: Optional[str] = Header(default=None),
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    """添加新的上游服务"""
    if x_admin_token:
        expected = os.getenv("ADMIN_TOKEN")
        if not expected or x_admin_token != expected:
            raise HTTPException(status_code=403, detail="管理员令牌无效")
    elif x_user_id:
        current_user = get_current_user(x_user_id, db)
        if not current_user.is_admin or current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要系统管理员权限")
    else:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    success = upstream_config.add_service(
        key=service_key,
        name=request.name,
        url=request.url,
        model=request.model,
        description=request.description,
        enabled=request.enabled
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="添加服务失败")
    
    service = upstream_config.get_service_info(service_key)
    current_key = upstream_config.config.get("current_upstream", "default")
    
    return UpstreamServiceResponse(
        key=service_key,
        name=service["name"],
        url=service["url"],
        model=service.get("model", "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M"),
        description=service.get("description", ""),
        enabled=service.get("enabled", True),
        is_current=(service_key == current_key)
    )

@app.put("/api/admin/upstream-services/{service_key}", response_model=UpstreamServiceResponse)
def admin_update_upstream_service(
    service_key: str,
    request: UpstreamServiceRequest,
    x_admin_token: Optional[str] = Header(default=None),
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    """更新上游服务配置"""
    if x_admin_token:
        expected = os.getenv("ADMIN_TOKEN")
        if not expected or x_admin_token != expected:
            raise HTTPException(status_code=403, detail="管理员令牌无效")
    elif x_user_id:
        current_user = get_current_user(x_user_id, db)
        if not current_user.is_admin or current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要系统管理员权限")
    else:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    success = upstream_config.update_service(
        key=service_key,
        name=request.name,
        url=request.url,
        model=request.model,
        description=request.description,
        enabled=request.enabled
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="服务不存在")
    
    service = upstream_config.get_service_info(service_key)
    current_key = upstream_config.config.get("current_upstream", "default")
    
    return UpstreamServiceResponse(
        key=service_key,
        name=service["name"],
        url=service["url"],
        model=service.get("model", "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M"),
        description=service.get("description", ""),
        enabled=service.get("enabled", True),
        is_current=(service_key == current_key)
    )

@app.delete("/api/admin/upstream-services/{service_key}")
def admin_delete_upstream_service(
    service_key: str,
    x_admin_token: Optional[str] = Header(default=None),
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    """删除上游服务"""
    if x_admin_token:
        expected = os.getenv("ADMIN_TOKEN")
        if not expected or x_admin_token != expected:
            raise HTTPException(status_code=403, detail="管理员令牌无效")
    elif x_user_id:
        current_user = get_current_user(x_user_id, db)
        if not current_user.is_admin or current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要系统管理员权限")
    else:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    if service_key == "default":
        raise HTTPException(status_code=400, detail="不能删除默认服务")
    
    success = upstream_config.delete_service(service_key)
    if not success:
        raise HTTPException(status_code=404, detail="服务不存在")
    
    return {"message": "服务已删除"}

@app.post("/api/admin/upstream-services/switch")
def admin_switch_upstream_service(
    request: SwitchUpstreamRequest,
    x_admin_token: Optional[str] = Header(default=None),
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    """切换当前使用的主上游服务"""
    if x_admin_token:
        expected = os.getenv("ADMIN_TOKEN")
        if not expected or x_admin_token != expected:
            raise HTTPException(status_code=403, detail="管理员令牌无效")
    elif x_user_id:
        current_user = get_current_user(x_user_id, db)
        if not current_user.is_admin or current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要系统管理员权限")
    else:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    success = upstream_config.set_current_upstream(request.service_key)
    if not success:
        raise HTTPException(status_code=400, detail="切换失败，服务不存在或未启用")
    
    service = upstream_config.get_service_info(request.service_key)
    return {
        "message": f"已切换到服务: {service['name']}",
        "current_service": request.service_key,
        "service_url": service["url"]
    }

@app.get("/api/admin/upstream-services/current")
def admin_get_current_upstream_service(
    x_admin_token: Optional[str] = Header(default=None),
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    """获取当前使用的主上游服务信息"""
    if x_admin_token:
        expected = os.getenv("ADMIN_TOKEN")
        if not expected or x_admin_token != expected:
            raise HTTPException(status_code=403, detail="管理员令牌无效")
    elif x_user_id:
        current_user = get_current_user(x_user_id, db)
        if not current_user.is_admin or current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要系统管理员权限")
    else:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    current_key = upstream_config.config.get("current_upstream", "default")
    service = upstream_config.get_service_info(current_key)
    
    if not service:
        raise HTTPException(status_code=404, detail="当前服务配置不存在")
    
    return {
        "key": current_key,
        "name": service["name"],
        "url": service["url"],
        "model": service.get("model", "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M"),
        "description": service.get("description", ""),
        "enabled": service.get("enabled", True)
    }

@app.get("/api/admin/upstream-services/health")
def admin_check_upstream_health(
    x_admin_token: Optional[str] = Header(default=None),
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    """检查所有上游服务的健康状态"""
    if x_admin_token:
        expected = os.getenv("ADMIN_TOKEN")
        if not expected or x_admin_token != expected:
            raise HTTPException(status_code=403, detail="管理员令牌无效")
    elif x_user_id:
        current_user = get_current_user(x_user_id, db)
        if not current_user.is_admin or current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要系统管理员权限")
    else:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    services = upstream_config.get_all_services()
    health_status = {}
    
    for key, service in services.items():
        if not service.get("enabled", True):
            health_status[key] = {"status": "disabled", "message": "服务已禁用"}
            continue
        
        try:
            url = f"{service['url']}/health"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                health_status[key] = {"status": "healthy", "message": "服务正常"}
            else:
                health_status[key] = {"status": "unhealthy", "message": f"HTTP {response.status_code}"}
        except requests.RequestException as e:
            health_status[key] = {"status": "unreachable", "message": str(e)}
    
    return health_status

# -----------------------------
# 机构管理API - 多租户支持
# -----------------------------

class OrganizationResponse(BaseModel):
    name: str
    user_count: int
    total_usage: int
    active_users: int
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


@app.get("/api/admin/organizations", response_model=List[OrganizationResponse])
def admin_list_organizations(
    x_admin_token: Optional[str] = Header(default=None),
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    """列出所有机构 - 仅系统管理员可访问"""
    # 兼容旧的ADMIN_TOKEN方式和新的用户权限方式
    if x_admin_token:
        # 使用旧的ADMIN_TOKEN方式
        expected = os.getenv("ADMIN_TOKEN")
        if not expected or x_admin_token != expected:
            raise HTTPException(status_code=403, detail="管理员令牌无效")
    elif x_user_id:
        # 使用新的用户权限方式
        current_user = get_current_user(x_user_id, db)
        if not current_user.is_admin or current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要系统管理员权限")
    else:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    # 查询所有机构及其统计信息（简化版本，避免SQLite兼容性问题）
    org_stats = db.query(
        User.organization.label("name"),
        func.count(User.id).label("user_count"),
        func.sum(User.usage_used).label("total_usage"),
        func.min(User.created_at).label("created_at")
    ).filter(
        User.organization.isnot(None)
    ).group_by(
        User.organization
    ).order_by(
        User.organization
    ).all()
    
    # 单独查询活跃用户数
    result = []
    for stat in org_stats:
        active_users = db.query(func.count(User.id)).filter(
            User.organization == stat.name,
            User.status == "active"
        ).scalar() or 0
        
        result.append(OrganizationResponse(
            name=stat.name,
            user_count=stat.user_count,
            total_usage=stat.total_usage or 0,
            active_users=active_users,
            created_at=stat.created_at.isoformat() if stat.created_at else None
        ))
    
    return result


@app.get("/api/admin/organizations/{org_name}/users", response_model=List[UserResponse])
def admin_list_organization_users(
    org_name: str,
    x_admin_token: Optional[str] = Header(default=None),
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    """列出指定机构的用户"""
    # 兼容旧的ADMIN_TOKEN方式和新的用户权限方式
    if x_admin_token:
        # 使用旧的ADMIN_TOKEN方式，系统管理员可以查看任何机构
        expected = os.getenv("ADMIN_TOKEN")
        if not expected or x_admin_token != expected:
            raise HTTPException(status_code=403, detail="管理员令牌无效")
    elif x_user_id:
        # 使用新的用户权限方式
        current_user = get_current_user(x_user_id, db)
        # 医院管理员只能查看自己机构
        if current_user.role == "hospital_admin" and not current_user.is_admin:
            if org_name != current_user.organization:
                raise HTTPException(status_code=403, detail="只能查看本机构用户")
    else:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    
    users = db.query(User).filter(
        User.organization == org_name
    ).order_by(User.id.asc()).all()
    
    return users


@app.get("/api/admin/organizations/{org_name}/stats")
def admin_get_organization_stats(
    org_name: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    x_admin_token: Optional[str] = Header(default=None),
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    """获取机构使用统计"""
    # 兼容旧的ADMIN_TOKEN方式和新的用户权限方式
    if x_admin_token:
        # 使用旧的ADMIN_TOKEN方式，系统管理员可以查看任何机构
        expected = os.getenv("ADMIN_TOKEN")
        if not expected or x_admin_token != expected:
            raise HTTPException(status_code=403, detail="管理员令牌无效")
    elif x_user_id:
        # 使用新的用户权限方式
        current_user = get_current_user(x_user_id, db)
        # 医院管理员只能查看自己机构
        if current_user.role == "hospital_admin" and not current_user.is_admin:
            if org_name != current_user.organization:
                raise HTTPException(status_code=403, detail="只能查看本机构统计")
    else:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    
    # 基础统计
    user_count = db.query(func.count(User.id)).filter(User.organization == org_name).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(
        User.organization == org_name,
        User.status == "active"
    ).scalar() or 0
    total_usage = db.query(func.sum(User.usage_used)).filter(User.organization == org_name).scalar() or 0
    
    # 使用事件统计
    def parse_dt(s):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None
    
    sdt = parse_dt(start)
    edt = parse_dt(end)
    
    usage_query = db.query(UsageEvent).join(User).filter(User.organization == org_name)
    if sdt:
        usage_query = usage_query.filter(UsageEvent.created_at >= sdt)
    if edt:
        usage_query = usage_query.filter(UsageEvent.created_at <= edt)
    
    event_count = usage_query.count()
    
    return {
        "organization": org_name,
        "user_count": user_count,
        "active_users": active_users,
        "total_usage": total_usage,
        "event_count": event_count,
        "window": {"start": start, "end": end}
    }


@app.post("/api/admin/organizations/{org_name}/users")
def admin_create_organization_user(
    org_name: str,
    payload: UserRegisterRequest,
    current_user: User = Depends(require_hospital_admin_or_system_admin),
    db: Session = Depends(get_db),
):
    """为指定机构创建用户"""
    # 医院管理员只能在自己的机构创建用户
    if current_user.role == "hospital_admin" and not current_user.is_admin:
        if org_name != current_user.organization:
            raise HTTPException(status_code=403, detail="只能在本机构创建用户")
    
    # 检查邮箱是否已存在
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 创建用户，强制设置机构
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        organization=org_name,  # 强制设置为指定机构
        phone=payload.phone,
        role="user",
        usage_quota=6,  # 新创建用户默认配额为6
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 创建默认订阅
    sub = Subscription(user_id=user.id, plan="free", status="active", auto_renew=True)
    db.add(sub)
    db.commit()
    
    return user


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )


