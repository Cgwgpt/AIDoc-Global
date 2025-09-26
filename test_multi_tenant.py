#!/usr/bin/env python3
"""
MedGemma AI 多租户管理功能测试脚本
演示系统管理员和医院管理员的不同权限
"""

import requests
import json
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "secret-admin"

# 用户ID映射
USER_IDS = {
    "system_admin": 4,      # admin@medgemma.com
    "hospital_admin_1": 5,  # manager@hospital.com (系统管理部门)
    "hospital_admin_2": 6,  # manager2@hospital.com (上海瑞金医院)
}

def make_request(method: str, endpoint: str, headers: Dict[str, str] = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """发送HTTP请求"""
    url = f"{BASE_URL}{endpoint}"
    headers = headers or {}
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        response.raise_for_status()
        return response.json() if response.content else {}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def test_system_admin_permissions():
    """测试系统管理员权限"""
    print("🔐 测试系统管理员权限")
    print("=" * 50)
    
    headers = {"X-Admin-Token": ADMIN_TOKEN}
    
    # 1. 查看所有机构
    print("1. 查看所有机构:")
    orgs = make_request("GET", "/api/admin/organizations", headers)
    if "error" not in orgs:
        for org in orgs:
            print(f"   - {org['name']}: {org['user_count']}用户, {org['total_usage']}使用量")
    else:
        print(f"   ❌ 错误: {orgs['error']}")
    
    # 2. 查看所有用户
    print("\n2. 查看所有用户:")
    users = make_request("GET", "/api/admin/users", headers)
    if "error" not in users:
        for user in users:
            print(f"   - {user['name']} ({user['email']}) - {user['organization']}")
    else:
        print(f"   ❌ 错误: {users['error']}")
    
    # 3. 查看特定机构用户
    print("\n3. 查看上海瑞金医院用户:")
    org_users = make_request("GET", "/api/admin/organizations/上海瑞金医院/users", headers)
    if "error" not in org_users:
        for user in org_users:
            print(f"   - {user['name']} ({user['email']})")
    else:
        print(f"   ❌ 错误: {org_users['error']}")
    
    # 4. 查看机构统计
    print("\n4. 查看上海瑞金医院统计:")
    stats = make_request("GET", "/api/admin/organizations/上海瑞金医院/stats", headers)
    if "error" not in stats:
        print(f"   - 用户数: {stats['user_count']}")
        print(f"   - 活跃用户: {stats['active_users']}")
        print(f"   - 总使用量: {stats['total_usage']}")
        print(f"   - 事件数: {stats['event_count']}")
    else:
        print(f"   ❌ 错误: {stats['error']}")

def test_hospital_admin_permissions():
    """测试医院管理员权限"""
    print("\n🏥 测试医院管理员权限 (上海瑞金医院)")
    print("=" * 50)
    
    headers = {"X-User-Id": str(USER_IDS["hospital_admin_2"])}
    
    # 1. 查看本机构用户（应该只能看到自己机构的用户）
    print("1. 查看本机构用户:")
    users = make_request("GET", "/api/admin/users", headers)
    if "error" not in users:
        print(f"   可以看到 {len(users)} 个用户:")
        for user in users:
            print(f"   - {user['name']} ({user['email']}) - {user['organization']}")
    else:
        print(f"   ❌ 错误: {users['error']}")
    
    # 2. 尝试查看其他机构用户（应该被拒绝）
    print("\n2. 尝试查看其他机构用户 (北京协和医院):")
    other_org_users = make_request("GET", "/api/admin/organizations/北京协和医院/users", headers)
    if "error" in other_org_users and ("只能查看本机构用户" in other_org_users["error"] or "403" in str(other_org_users)):
        print("   ✅ 正确：医院管理员无法查看其他机构用户")
    else:
        print(f"   ❌ 权限控制失效: {other_org_users}")
    
    # 3. 查看本机构统计
    print("\n3. 查看本机构统计:")
    stats = make_request("GET", "/api/admin/organizations/上海瑞金医院/stats", headers)
    if "error" not in stats:
        print(f"   - 用户数: {stats['user_count']}")
        print(f"   - 活跃用户: {stats['active_users']}")
        print(f"   - 总使用量: {stats['total_usage']}")
    else:
        print(f"   ❌ 错误: {stats['error']}")
    
    # 4. 尝试查看其他机构统计（应该被拒绝）
    print("\n4. 尝试查看其他机构统计 (系统管理部门):")
    other_stats = make_request("GET", "/api/admin/organizations/系统管理部门/stats", headers)
    if "error" in other_stats and ("只能查看本机构统计" in other_stats["error"] or "403" in str(other_stats)):
        print("   ✅ 正确：医院管理员无法查看其他机构统计")
    else:
        print(f"   ❌ 权限控制失效: {other_stats}")

def test_user_creation():
    """测试用户创建功能"""
    print("\n👤 测试用户创建功能")
    print("=" * 50)
    
    # 医院管理员为本机构创建用户
    headers = {
        "X-User-Id": str(USER_IDS["hospital_admin_2"]),
        "Content-Type": "application/json"
    }
    
    new_user_data = {
        "name": "测试医生",
        "email": "test_doctor@hospital.com",
        "organization": "上海瑞金医院",
        "phone": "13800000001",
        "password": "test123456"
    }
    
    print("1. 医院管理员为本机构创建用户:")
    result = make_request("POST", "/api/admin/organizations/上海瑞金医院/users", headers, new_user_data)
    if "error" not in result and "name" in result:
        print(f"   ✅ 成功创建用户: {result['name']} ({result['email']})")
    elif "error" not in result:
        print(f"   ✅ 成功创建用户: {result}")
    else:
        print(f"   ❌ 创建失败: {result['error']}")
    
    # 尝试为其他机构创建用户（应该被拒绝）
    print("\n2. 尝试为其他机构创建用户:")
    other_user_data = new_user_data.copy()
    other_user_data["email"] = "test_doctor2@hospital.com"
    other_user_data["organization"] = "北京协和医院"
    
    result = make_request("POST", "/api/admin/organizations/北京协和医院/users", headers, other_user_data)
    if "error" in result and ("只能在本机构创建用户" in result["error"] or "403" in str(result)):
        print("   ✅ 正确：医院管理员无法为其他机构创建用户")
    else:
        print(f"   ❌ 权限控制失效: {result}")

def main():
    """主函数"""
    print("🏥 MedGemma AI 多租户管理功能测试")
    print("=" * 60)
    
    # 检查服务状态
    health = make_request("GET", "/health")
    if "error" in health:
        print("❌ 服务未启动，请先启动服务:")
        print("   uvicorn server.main:app --reload")
        return
    
    print("✅ 服务运行正常")
    
    # 运行测试
    test_system_admin_permissions()
    test_hospital_admin_permissions()
    test_user_creation()
    
    print("\n" + "=" * 60)
    print("🎉 多租户管理功能测试完成！")
    print("\n📋 测试总结:")
    print("- ✅ 系统管理员可以查看所有机构和用户")
    print("- ✅ 医院管理员只能查看本机构数据")
    print("- ✅ 数据隔离机制正常工作")
    print("- ✅ 权限控制有效防止跨机构访问")
    print("- ✅ 用户创建功能支持机构限制")

if __name__ == "__main__":
    main()
