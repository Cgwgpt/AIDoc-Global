#!/usr/bin/env python3
"""
初始化管理员账户脚本
用于创建系统管理员账户，确保安全的权限管理
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from server.db import get_db, User, Base, engine
from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_admin_user(email: str, password: str, name: str = "系统管理员", role: str = "admin", organization: str = None):
    """创建管理员用户"""
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 检查管理员是否已存在
        existing_admin = db.query(User).filter(User.email == email).first()
        if existing_admin:
            if existing_admin.is_admin:
                print(f"✅ 管理员账户 {email} 已存在")
                return existing_admin
            else:
                # 将现有用户提升为管理员
                existing_admin.is_admin = (role == "admin")
                existing_admin.name = name
                existing_admin.role = role
                existing_admin.organization = organization or existing_admin.organization
                existing_admin.status = "active"
                db.commit()
                print(f"✅ 用户 {email} 已提升为{role}管理员")
                return existing_admin
        
        # 创建新的管理员用户
        admin_user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            organization=organization or "系统管理部门",
            phone="400-****-0000",
            is_admin=(role == "admin"),
            role=role,
            status="active",
            usage_quota=None,  # 管理员无限制
            daily_quota=None,  # 管理员无限制
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"🎉 管理员账户创建成功！")
        print(f"   邮箱: {email}")
        print(f"   密码: {password}")
        print(f"   用户ID: {admin_user.id}")
        print(f"   管理员权限: {'是' if admin_user.is_admin else '否'}")
        
        return admin_user
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建管理员账户失败: {e}")
        raise
    finally:
        db.close()

def main():
    """主函数"""
    print("🔐 MedGemma AI 管理员账户初始化")
    print("=" * 50)
    
    # 预设的管理员账户配置
    admin_accounts = [
        {
            "email": "admin@medgemma.com",
            "password": "SecureAdmin2024!",
            "name": "系统管理员",
            "role": "admin",
            "organization": "系统管理部门"
        },
        {
            "email": "manager@hospital.com", 
            "password": "HospitalManager123!",
            "name": "医院管理员",
            "role": "hospital_admin",
            "organization": "北京协和医院"
        },
        {
            "email": "manager2@hospital.com", 
            "password": "HospitalManager456!",
            "name": "医院管理员2",
            "role": "hospital_admin",
            "organization": "上海瑞金医院"
        }
    ]
    
    for admin_config in admin_accounts:
        try:
            create_admin_user(
                email=admin_config["email"],
                password=admin_config["password"],
                name=admin_config["name"],
                role=admin_config["role"],
                organization=admin_config["organization"]
            )
        except Exception as e:
            print(f"❌ 处理账户 {admin_config['email']} 时出错: {e}")
            continue
    
    print("\n" + "=" * 50)
    print("✅ 管理员账户初始化完成！")
    print("\n📝 使用说明:")
    print("1. 启动后端服务: uvicorn server.main:app --reload")
    print("2. 访问前端页面: http://localhost:8000/static/index.html")
    print("3. 使用管理员账户登录")
    print("4. 点击 ⚙️ 管理控制台按钮")
    print("5. 输入 ADMIN_TOKEN 进行验证")
    
    print("\n🔒 安全提醒:")
    print("- 请及时修改默认密码")
    print("- 设置强密码策略")
    print("- 定期审查管理员权限")
    print("- 启用操作日志记录")

if __name__ == "__main__":
    main()
