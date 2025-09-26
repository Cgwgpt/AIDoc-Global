#!/usr/bin/env python3
"""
测试用户编辑功能修复
验证保存按钮是否能正确修改用户为管理员
"""

import requests
import json
import time

# 配置
BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "secret-admin"

def test_user_edit_functionality():
    """测试用户编辑功能"""
    print("🧪 开始测试用户编辑功能...")
    
    # 1. 获取用户列表
    print("\n1. 获取用户列表...")
    response = requests.get(f"{BASE_URL}/api/admin/users", 
                          headers={"X-Admin-Token": ADMIN_TOKEN})
    
    if response.status_code != 200:
        print(f"❌ 获取用户列表失败: {response.status_code}")
        return False
    
    users = response.json()
    print(f"✅ 找到 {len(users)} 位用户")
    
    # 找到第一个非管理员用户进行测试
    test_user = None
    for user in users:
        if not user.get('is_admin', False):
            test_user = user
            break
    
    if not test_user:
        print("❌ 没有找到非管理员用户进行测试")
        return False
    
    print(f"📝 选择测试用户: {test_user['name']} ({test_user['email']})")
    print(f"   当前管理员状态: {test_user.get('is_admin', False)}")
    
    # 2. 修改用户为管理员
    print("\n2. 修改用户为管理员...")
    update_data = {
        "name": test_user['name'],
        "email": test_user['email'],
        "phone": test_user.get('phone'),
        "organization": test_user.get('organization'),
        "status": test_user.get('status', 'active'),
        "is_admin": True  # 修改为管理员
    }
    
    response = requests.patch(
        f"{BASE_URL}/api/admin/users/{test_user['id']}",
        headers={
            "X-Admin-Token": ADMIN_TOKEN,
            "Content-Type": "application/json"
        },
        json=update_data,
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ 更新用户失败: {response.status_code}")
        print(f"   错误信息: {response.text}")
        return False
    
    updated_user = response.json()
    print(f"✅ 用户更新成功!")
    print(f"   新管理员状态: {updated_user.get('is_admin', False)}")
    
    # 3. 验证更新是否生效
    print("\n3. 验证更新是否生效...")
    response = requests.get(f"{BASE_URL}/api/admin/users", 
                          headers={"X-Admin-Token": ADMIN_TOKEN})
    
    if response.status_code != 200:
        print(f"❌ 重新获取用户列表失败: {response.status_code}")
        return False
    
    users_after = response.json()
    updated_user_after = next((u for u in users_after if u['id'] == test_user['id']), None)
    
    if not updated_user_after:
        print("❌ 找不到更新后的用户")
        return False
    
    if updated_user_after.get('is_admin', False):
        print("✅ 用户已成功修改为管理员!")
        return True
    else:
        print("❌ 用户管理员状态未更新")
        return False

def test_user_edit_validation():
    """测试用户编辑验证功能"""
    print("\n🧪 测试用户编辑验证功能...")
    
    # 测试无效邮箱
    print("\n1. 测试无效邮箱验证...")
    invalid_data = {
        "name": "测试用户",
        "email": "invalid-email",  # 无效邮箱
        "is_admin": False
    }
    
    response = requests.patch(
        f"{BASE_URL}/api/admin/users/1",
        headers={
            "X-Admin-Token": ADMIN_TOKEN,
            "Content-Type": "application/json"
        },
        json=invalid_data
    )
    
    if response.status_code == 400:
        print("✅ 无效邮箱验证正常")
    else:
        print(f"⚠️ 无效邮箱验证异常: {response.status_code}")
    
    # 测试必填字段验证
    print("\n2. 测试必填字段验证...")
    empty_data = {
        "name": "",  # 空姓名
        "email": "",  # 空邮箱
        "is_admin": False
    }
    
    response = requests.patch(
        f"{BASE_URL}/api/admin/users/1",
        headers={
            "X-Admin-Token": ADMIN_TOKEN,
            "Content-Type": "application/json"
        },
        json=empty_data
    )
    
    if response.status_code == 400:
        print("✅ 必填字段验证正常")
    else:
        print(f"⚠️ 必填字段验证异常: {response.status_code}")

if __name__ == "__main__":
    print("🚀 开始测试用户编辑功能修复...")
    print("=" * 50)
    
    try:
        # 测试基本功能
        success = test_user_edit_functionality()
        
        # 测试验证功能
        test_user_edit_validation()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 用户编辑功能测试通过!")
            print("✅ 保存按钮功能已修复")
            print("✅ 管理员权限修改功能正常")
        else:
            print("❌ 用户编辑功能测试失败")
            
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
    
    print("\n📋 测试完成!")
