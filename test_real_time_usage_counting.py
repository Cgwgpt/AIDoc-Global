#!/usr/bin/env python3
"""
MedGemma AI 实时使用次数统计测试脚本
验证AI调用后使用次数能够实时更新
"""

import requests
import json
import time
import sys

# 配置
BASE_URL = "http://localhost:8080"
ADMIN_TOKEN = "secret-admin"
TEST_EMAIL = "admin@medgemma.com"

def get_user_usage_stats():
    """获取用户使用统计"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"X-Admin-Token": ADMIN_TOKEN}
        )
        
        if response.status_code == 200:
            users = response.json()
            user = next((u for u in users if u["email"] == TEST_EMAIL), None)
            if user:
                return {
                    'usage_used': user.get('usage_used', 0),
                    'daily_used': user.get('daily_used', 0),
                    'usage_quota': user.get('usage_quota'),
                    'daily_quota': user.get('daily_quota')
                }
        return None
    except Exception as e:
        print(f"获取用户统计失败: {e}")
        return None

def test_ai_call_with_user_id():
    """测试带用户ID的AI调用"""
    print("🧪 测试实时使用次数统计...")
    print("=" * 60)
    
    # 1. 获取初始使用统计
    print("1️⃣ 获取初始使用统计...")
    initial_stats = get_user_usage_stats()
    if not initial_stats:
        print("❌ 无法获取用户统计信息")
        return False
        
    print(f"✅ 初始统计:")
    print(f"   - 总使用次数: {initial_stats['usage_used']}")
    print(f"   - 今日使用: {initial_stats['daily_used']}")
    print(f"   - 使用配额: {initial_stats['usage_quota'] or '无限制'}")
    
    # 2. 进行AI调用
    print("\n2️⃣ 进行AI调用...")
    
    # 首先获取用户ID
    user_id = None
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"X-Admin-Token": ADMIN_TOKEN}
        )
        if response.status_code == 200:
            users = response.json()
            user = next((u for u in users if u["email"] == TEST_EMAIL), None)
            if user:
                user_id = user['id']
                print(f"   - 用户ID: {user_id}")
    except Exception as e:
        print(f"   ❌ 获取用户ID失败: {e}")
        return False
    
    if not user_id:
        print("   ❌ 无法获取用户ID")
        return False
    
    # 发送AI请求
    ai_request = {
        "model": "medgemma-4b-it",
        "prompt": "请简单介绍一下感冒的症状",
        "stream": False
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-User-Id': str(user_id)
    }
    
    print("   - 发送AI请求...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/generate",
            headers=headers,
            json=ai_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ AI调用成功")
            print(f"   - 响应长度: {len(result.get('response', ''))}")
        else:
            print(f"   ❌ AI调用失败: {response.status_code}")
            print(f"   - 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ AI调用异常: {e}")
        return False
    
    # 3. 等待数据库更新
    print("\n3️⃣ 等待数据库更新...")
    time.sleep(2)
    
    # 4. 获取更新后的使用统计
    print("\n4️⃣ 获取更新后的使用统计...")
    updated_stats = get_user_usage_stats()
    if not updated_stats:
        print("❌ 无法获取更新后的统计信息")
        return False
    
    print(f"✅ 更新后统计:")
    print(f"   - 总使用次数: {updated_stats['usage_used']}")
    print(f"   - 今日使用: {updated_stats['daily_used']}")
    
    # 5. 验证使用次数是否增加
    print("\n5️⃣ 验证使用次数变化...")
    
    usage_increased = updated_stats['usage_used'] > initial_stats['usage_used']
    daily_increased = updated_stats['daily_used'] > initial_stats['daily_used']
    
    print(f"   - 总使用次数是否增加: {'✅ 是' if usage_increased else '❌ 否'}")
    print(f"   - 今日使用是否增加: {'✅ 是' if daily_increased else '❌ 否'}")
    
    if usage_increased and daily_increased:
        print("\n🎉 实时使用次数统计测试通过！")
        print("✅ AI调用后使用次数正确增加")
        print("✅ 数据库正确更新了使用统计")
        print("✅ 前端应该能获取到最新的使用数据")
        return True
    else:
        print("\n❌ 实时使用次数统计测试失败")
        print("⚠️ AI调用后使用次数没有增加")
        return False

def test_multiple_ai_calls():
    """测试多次AI调用的累计统计"""
    print("\n" + "=" * 60)
    print("🔄 测试多次AI调用累计统计...")
    
    # 获取初始统计
    initial_stats = get_user_usage_stats()
    if not initial_stats:
        print("❌ 无法获取初始统计")
        return False
    
    print(f"初始统计: 总使用 {initial_stats['usage_used']}, 今日使用 {initial_stats['daily_used']}")
    
    # 进行3次AI调用
    user_id = None
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"X-Admin-Token": ADMIN_TOKEN}
        )
        if response.status_code == 200:
            users = response.json()
            user = next((u for u in users if u["email"] == TEST_EMAIL), None)
            if user:
                user_id = user['id']
    except:
        pass
    
    if not user_id:
        print("❌ 无法获取用户ID")
        return False
    
    for i in range(3):
        print(f"\n第 {i+1} 次AI调用...")
        
        ai_request = {
            "model": "medgemma-4b-it",
            "prompt": f"请简单介绍一下健康生活的第{i+1}个要点",
            "stream": False
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-User-Id': str(user_id)
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/generate",
                headers=headers,
                json=ai_request,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"   ✅ 第 {i+1} 次调用成功")
            else:
                print(f"   ❌ 第 {i+1} 次调用失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 第 {i+1} 次调用异常: {e}")
        
        time.sleep(1)
    
    # 获取最终统计
    time.sleep(2)
    final_stats = get_user_usage_stats()
    if not final_stats:
        print("❌ 无法获取最终统计")
        return False
    
    print(f"\n最终统计: 总使用 {final_stats['usage_used']}, 今日使用 {final_stats['daily_used']}")
    
    # 验证累计效果
    expected_total = initial_stats['usage_used'] + 3
    expected_daily = initial_stats['daily_used'] + 3
    
    total_correct = final_stats['usage_used'] == expected_total
    daily_correct = final_stats['daily_used'] == expected_daily
    
    print(f"验证累计效果:")
    print(f"   - 总使用次数正确: {'✅ 是' if total_correct else '❌ 否'} (期望: {expected_total}, 实际: {final_stats['usage_used']})")
    print(f"   - 今日使用正确: {'✅ 是' if daily_correct else '❌ 否'} (期望: {expected_daily}, 实际: {final_stats['daily_used']})")
    
    if total_correct and daily_correct:
        print("\n🎉 多次AI调用累计统计测试通过！")
        return True
    else:
        print("\n❌ 多次AI调用累计统计测试失败")
        return False

def main():
    """主函数"""
    print("🧪 MedGemma AI 实时使用次数统计测试")
    print("=" * 60)
    
    # 测试单次AI调用
    single_test_passed = test_ai_call_with_user_id()
    
    # 测试多次AI调用
    multiple_test_passed = test_multiple_ai_calls()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"   单次AI调用测试: {'✅ 通过' if single_test_passed else '❌ 失败'}")
    print(f"   多次AI调用测试: {'✅ 通过' if multiple_test_passed else '❌ 失败'}")
    
    if single_test_passed and multiple_test_passed:
        print("\n🎉 所有测试通过！")
        print("✅ 实时使用次数统计功能正常工作")
        print("✅ AI调用后使用次数正确增加")
        print("✅ 前端应该能显示最新的使用统计")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查系统配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())
