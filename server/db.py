from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Generator

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Date,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from sqlalchemy import inspect, text


# SQLite 数据库文件路径（位于项目根目录）
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DB_PATH = os.getenv("APP_DB_PATH", os.path.join(_project_root, "app.db"))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# SQLAlchemy 基础设施
engine = create_engine(
    f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()



# 多租户表
class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)
    organization = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    usage_quota = Column(Integer, nullable=True)  # None 表示不限
    usage_used = Column(Integer, nullable=False, default=0)
    role = Column(String(50), nullable=False, default="user")  # user/hospital_admin/admin
    # 管理扩展字段
    status = Column(String(50), nullable=False, default="active")  # active/disabled
    notes = Column(String(1024), nullable=True)
    daily_quota = Column(Integer, nullable=True)  # None 表示不限
    daily_used = Column(Integer, nullable=False, default=0)
    daily_reset_at = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    tenant = relationship("Tenant", back_populates="users")
    subscription = relationship(
        "Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan = Column(String(50), nullable=False, default="free")  # free/basic/pro
    status = Column(String(50), nullable=False, default="active")  # active/canceled
    auto_renew = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    user = relationship("User", back_populates="subscription")
    tenant = relationship("Tenant")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_subscriptions_user_id"),
    )


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False, default="generate")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    meta = Column(String(2048), nullable=True)

    user = relationship("User")
    tenant = relationship("Tenant")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_simple_migrations() -> None:
    """执行简单的SQLite列新增迁移，避免破坏已有数据文件。

    注意：仅用于开发/演示场景，生产建议使用Alembic。
    """
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    with engine.begin() as conn:
        # tenants
        if "tenants" not in tables:
            Base.metadata.tables["tenants"].create(bind=engine)
        # users
        if "users" in tables:
            existing_cols = {col["name"] for col in inspector.get_columns("users")}
            if "tenant_id" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN tenant_id INTEGER REFERENCES tenants(id) DEFAULT 1 NOT NULL"))
            # ...原有字段迁移...
            if "name" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR(100)"))
            if "organization" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN organization VARCHAR(255)"))
            if "phone" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(50)"))
            if "is_admin" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL"))
            if "usage_quota" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN usage_quota INTEGER"))
            if "usage_used" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN usage_used INTEGER DEFAULT 0 NOT NULL"))
            if "status" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR(50) DEFAULT 'active' NOT NULL"))
            if "notes" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN notes VARCHAR(1024)"))
            if "daily_quota" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN daily_quota INTEGER"))
            if "daily_used" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN daily_used INTEGER DEFAULT 0 NOT NULL"))
            if "daily_reset_at" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN daily_reset_at DATE"))
            if "role" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user' NOT NULL"))
        else:
            Base.metadata.tables["users"].create(bind=engine)
        # subscriptions
        if "subscriptions" in tables:
            existing_cols = {col["name"] for col in inspector.get_columns("subscriptions")}
            if "tenant_id" not in existing_cols:
                conn.execute(text("ALTER TABLE subscriptions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id) DEFAULT 1 NOT NULL"))
        else:
            Base.metadata.tables["subscriptions"].create(bind=engine)
        # usage_events
        if "usage_events" in tables:
            existing_cols = {col["name"] for col in inspector.get_columns("usage_events")}
            if "tenant_id" not in existing_cols:
                conn.execute(text("ALTER TABLE usage_events ADD COLUMN tenant_id INTEGER REFERENCES tenants(id) DEFAULT 1 NOT NULL"))
        else:
            Base.metadata.tables["usage_events"].create(bind=engine)


