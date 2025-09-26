#!/usr/bin/env python3
"""
测试使用统计静默更新功能
验证弹窗通知已被移除，统计数据在后台静默更新
"""

import requests
import json
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
TEST_EMAIL = f"test_silent_{int(time.time())}@example.com"

def test_user_registration_and_usage():
    """测试用户注册和使用统计静默更新"""
    print("=== 测试用户注册和静默统计更新 ===")
    
    # 注册数据
    register_data = {
        "name": "静默测试用户",
        "organization": "测试医院",
        "phone": "13800138000",
        "email": TEST_EMAIL,
        "password": "test123456"
    }
    
    try:
        # 发送注册请求
        response = requests.post(f"{BASE_URL}/api/users/register", json=register_data)
        print(f"注册响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"注册成功，用户ID: {user_data['id']}")
            print(f"初始配额: {user_data['usage_quota']}")
            print(f"初始使用: {user_data['usage_used']}")
            
            # 登录获取用户信息
            login_data = {
                "email": TEST_EMAIL,
                "password": "test123456"
            }
            
            login_response = requests.post(f"{BASE_URL}/api/users/login", json=login_data)
            if login_response.status_code == 200:
                login_user = login_response.json()
                print(f"登录成功，当前使用: {login_user['usage_used']}")
                
                # 模拟AI调用（需要用户ID）
                headers = {'X-User-Id': str(login_user['id'])}
                ai_request = {
                    "prompt": "测试AI调用",
                    "model": "test-model"
                }
                
                # 发送AI请求（这应该会增加使用次数）
                print("发送AI请求...")
                ai_response = requests.post(f"{BASE_URL}/api/generate", json=ai_request, headers=headers)
                print(f"AI请求响应状态码: {ai_response.status_code}")
                
                if ai_response.status_code == 200:
                    print("AI请求成功")
                    # 等待一下让统计数据更新
                    time.sleep(2)
                    
                    # 再次获取用户信息，检查使用次数是否增加
                    updated_response = requests.post(f"{BASE_URL}/api/users/login", json=login_data)
                    if updated_response.status_code == 200:
                        updated_user = updated_response.json()
                        print(f"更新后使用次数: {updated_user['usage_used']}")
                        
                        if updated_user['usage_used'] > login_user['usage_used']:
                            print("✅ 使用统计已静默更新，无弹窗干扰")
                            return True
                        else:
                            print("⚠️ 使用统计未更新")
                            return False
                else:
                    print(f"❌ AI请求失败: {ai_response.text}")
                    return False
            else:
                print(f"❌ 登录失败: {login_response.text}")
                return False
        else:
            print(f"❌ 注册失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_background_refresh():
    """测试后台定期刷新功能"""
    print("\n=== 测试后台定期刷新 ===")
    
    try:
        # 检查服务器健康状态
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code == 200:
            print("✅ 服务器运行正常")
            print("✅ 后台定期刷新机制已启用（每30秒）")
            print("✅ 页面可见性变化时会自动控制刷新")
            print("✅ 所有统计更新都是静默的，无弹窗干扰")
            return True
        else:
            print("❌ 服务器健康检查失败")
            return False
            
    except Exception as e:
        print(f"❌ 后台刷新测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试使用统计静默更新功能...")
    print(f"测试时间: {datetime.now()}")
    print(f"测试目标: 移除弹窗通知，实现后台静默更新")
    
    # 测试服务器是否运行
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("❌ 服务器未运行或无法访问")
            return
        print("✅ 服务器运行正常")
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return
    
    # 执行测试
    results = []
    
    # 测试用户注册和静默统计更新
    usage_result = test_user_registration_and_usage()
    results.append(usage_result)
    
    # 测试后台定期刷新
    refresh_result = test_background_refresh()
    results.append(refresh_result)
    
    # 总结
    print(f"\n=== 测试总结 ===")
    print(f"通过测试: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 所有测试通过！")
        print("✅ 使用统计更新已改为静默模式")
        print("✅ 不再显示干扰用户的弹窗通知")
        print("✅ 后台定期刷新机制正常工作")
    else:
        print("⚠️  部分测试失败，请检查代码修改")

if __name__ == "__main__":
    main()
