#!/usr/bin/env python3
"""
测试用户编辑功能 - 专门测试修改管理员权限
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "secret-admin"

def test_edit_to_admin():
    """测试将用户修改为管理员"""
    print("🧪 测试用户编辑为管理员功能...")
    
    # 1. 获取用户列表
    print("\n1. 获取用户列表...")
    response = requests.get(f"{BASE_URL}/api/admin/users", 
                          headers={"X-Admin-Token": ADMIN_TOKEN})
    
    if response.status_code != 200:
        print(f"❌ 获取用户列表失败: {response.status_code}")
        return False
    
    users = response.json()
    print(f"✅ 找到 {len(users)} 位用户")
    
    # 找到第一个非管理员用户
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
    
    # 2. 修改用户为管理员（保持原邮箱）
    print("\n2. 修改用户为管理员...")
    update_data = {
        "name": test_user['name'],
        "email": test_user['email'],  # 保持原邮箱避免冲突
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
        json=update_data
    )
    
    print(f"   状态码: {response.status_code}")
    print(f"   响应内容: {response.text}")
    
    if response.status_code != 200:
        print(f"❌ 更新用户失败: {response.status_code}")
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

def test_edit_email_conflict():
    """测试邮箱冲突处理"""
    print("\n🧪 测试邮箱冲突处理...")
    
    # 获取两个不同的用户
    response = requests.get(f"{BASE_URL}/api/admin/users", 
                          headers={"X-Admin-Token": ADMIN_TOKEN})
    users = response.json()
    
    if len(users) < 2:
        print("❌ 用户数量不足，无法测试邮箱冲突")
        return False
    
    user1 = users[0]
    user2 = users[1]
    
    print(f"📝 测试用户1: {user1['name']} ({user1['email']})")
    print(f"📝 测试用户2: {user2['name']} ({user2['email']})")
    
    # 尝试将用户2的邮箱改为用户1的邮箱
    update_data = {
        "name": user2['name'],
        "email": user1['email'],  # 使用用户1的邮箱，应该冲突
        "is_admin": user2.get('is_admin', False)
    }
    
    response = requests.patch(
        f"{BASE_URL}/api/admin/users/{user2['id']}",
        headers={
            "X-Admin-Token": ADMIN_TOKEN,
            "Content-Type": "application/json"
        },
        json=update_data
    )
    
    print(f"   状态码: {response.status_code}")
    print(f"   响应内容: {response.text}")
    
    if response.status_code == 400 and "邮箱已被占用" in response.text:
        print("✅ 邮箱冲突检测正常")
        return True
    else:
        print("❌ 邮箱冲突检测异常")
        return False

if __name__ == "__main__":
    print("🚀 开始测试用户编辑功能...")
    print("=" * 50)
    
    try:
        # 测试基本功能
        success1 = test_edit_to_admin()
        
        # 测试邮箱冲突
        success2 = test_edit_email_conflict()
        
        print("\n" + "=" * 50)
        if success1 and success2:
            print("🎉 所有测试通过!")
            print("✅ 用户编辑为管理员功能正常")
            print("✅ 邮箱冲突检测正常")
        else:
            print("❌ 部分测试失败")
            
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
    
    print("\n📋 测试完成!")
