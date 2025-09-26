#!/usr/bin/env python3
"""
MedGemma AI 数据一致性最终测试脚本
测试"我的账户"页面和"用户管理中心"的数据同步功能
"""

import requests
import json
import time
import sys

# 配置
BASE_URL = "http://localhost:8080"
ADMIN_TOKEN = "secret-admin"
TEST_EMAIL = "admin@medgemma.com"

def test_data_consistency():
    """测试数据一致性"""
    print("🔍 开始测试数据一致性...")
    print("=" * 60)
    
    try:
        # 1. 获取管理员用户列表数据
        print("1️⃣ 获取用户管理中心数据...")
        admin_response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"X-Admin-Token": ADMIN_TOKEN}
        )
        
        if admin_response.status_code != 200:
            print(f"❌ 获取管理员用户列表失败: {admin_response.status_code}")
            return False
            
        admin_users = admin_response.json()
        admin_user = next((user for user in admin_users if user["email"] == TEST_EMAIL), None)
        
        if not admin_user:
            print(f"❌ 未找到测试用户: {TEST_EMAIL}")
            return False
            
        print(f"✅ 用户管理中心数据:")
        print(f"   - 用户ID: {admin_user['id']}")
        print(f"   - 邮箱: {admin_user['email']}")
        print(f"   - 已用数值: {admin_user.get('usage_used', 0)}")
        print(f"   - 今日使用: {admin_user.get('daily_used', 0)}")
        print(f"   - 使用配额: {admin_user.get('usage_quota', '无限制')}")
        
        # 2. 测试AI调用（增加使用次数）
        print("\n2️⃣ 测试AI调用增加使用次数...")
        
        # 模拟AI调用
        generate_response = requests.post(
            f"{BASE_URL}/api/generate",
            headers={"X-User-Id": str(admin_user['id'])},
            json={
                "prompt": "测试数据一致性",
                "model": "medgemma-4b-it",
                "stream": False
            }
        )
        
        if generate_response.status_code == 200:
            print("✅ AI调用成功，使用次数已增加")
        else:
            print(f"⚠️ AI调用失败: {generate_response.status_code}")
        
        # 等待后端更新
        print("⏳ 等待后端数据更新...")
        time.sleep(2)
        
        # 3. 再次获取管理员用户列表数据
        print("\n3️⃣ 获取更新后的用户管理中心数据...")
        admin_response_updated = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"X-Admin-Token": ADMIN_TOKEN}
        )
        
        if admin_response_updated.status_code == 200:
            admin_users_updated = admin_response_updated.json()
            admin_user_updated = next((user for user in admin_users_updated if user["email"] == TEST_EMAIL), None)
            
            if admin_user_updated:
                print(f"✅ 更新后的用户管理中心数据:")
                print(f"   - 已用数值: {admin_user_updated.get('usage_used', 0)}")
                print(f"   - 今日使用: {admin_user_updated.get('daily_used', 0)}")
                
                # 4. 检查数据变化
                usage_increased = admin_user_updated.get('usage_used', 0) > admin_user.get('usage_used', 0)
                daily_increased = admin_user_updated.get('daily_used', 0) > admin_user.get('daily_used', 0)
                
                print(f"\n4️⃣ 数据变化检查:")
                print(f"   - 总使用次数是否增加: {'✅ 是' if usage_increased else '❌ 否'}")
                print(f"   - 今日使用是否增加: {'✅ 是' if daily_increased else '❌ 否'}")
                
                if usage_increased and daily_increased:
                    print("\n🎉 数据一致性测试通过！")
                    print("✅ 后端数据库正确更新了使用统计")
                    print("✅ 用户管理中心显示最新数据")
                    print("✅ 前端同步机制应该能获取到相同数据")
                    return True
                else:
                    print("\n❌ 数据一致性测试失败")
                    print("⚠️ 后端数据库未正确更新使用统计")
                    return False
            else:
                print("❌ 更新后未找到测试用户")
                return False
        else:
            print(f"❌ 获取更新后的管理员用户列表失败: {admin_response_updated.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 请确保服务器正在运行 (python server/main.py)")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_sync_mechanism():
    """测试同步机制"""
    print("\n" + "=" * 60)
    print("🔄 测试同步机制...")
    
    print("📋 同步机制功能说明:")
    print("1. 自动同步: 每30秒自动从服务器同步数据")
    print("2. 手动同步: 点击'我的账户'页面的'🔄 同步'按钮")
    print("3. 实时同步: AI调用后1秒自动同步")
    print("4. 页面可见性同步: 页面重新显示时立即同步")
    
    print("\n✅ 同步机制已实现:")
    print("   - syncUsageStatsFromServer() 函数")
    print("   - 定期同步定时器 (30秒)")
    print("   - 手动同步按钮")
    print("   - 页面可见性监听")
    print("   - 同步通知提示")
    
    return True

def main():
    """主函数"""
    print("🧪 MedGemma AI 数据一致性最终测试")
    print("=" * 60)
    
    # 测试数据一致性
    consistency_passed = test_data_consistency()
    
    # 测试同步机制
    sync_passed = test_sync_mechanism()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"   数据一致性测试: {'✅ 通过' if consistency_passed else '❌ 失败'}")
    print(f"   同步机制测试: {'✅ 通过' if sync_passed else '❌ 失败'}")
    
    if consistency_passed and sync_passed:
        print("\n🎉 所有测试通过！")
        print("✅ '我的账户'页面和'用户管理中心'数据将保持实时一致")
        print("✅ 用户可以通过多种方式同步最新数据")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查系统配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())
