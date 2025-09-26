#!/usr/bin/env python3
"""
上游服务配置功能测试脚本
测试添加、编辑、删除、切换上游服务功能
"""

import requests
import json
import time

# 配置
BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "secret-admin"
USER_ID = 1

def test_upstream_config():
    """测试上游服务配置功能"""
    
    headers = {
        'X-Admin-Token': ADMIN_TOKEN,
        'X-User-Id': str(USER_ID),
        'Content-Type': 'application/json'
    }
    
    print("🧪 开始测试上游服务配置功能...")
    
    # 1. 列出当前服务
    print("\n1️⃣ 列出当前服务...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/upstream-services", headers=headers)
        if response.status_code == 200:
            services = response.json()
            print(f"✅ 当前配置了 {len(services)} 个服务:")
            for service in services:
                print(f"   - {service['key']}: {service['name']} ({service['url']})")
        else:
            print(f"❌ 获取服务列表失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 2. 添加测试服务
    print("\n2️⃣ 添加测试服务...")
    test_service = {
        "name": "测试服务",
        "url": "https://test-medgemma.example.com",
        "description": "用于测试的上游服务",
        "enabled": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/upstream-services?service_key=test_service",
            headers=headers,
            json=test_service
        )
        if response.status_code == 200:
            print("✅ 测试服务添加成功")
        else:
            print(f"❌ 添加测试服务失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 添加服务失败: {e}")
    
    # 3. 编辑测试服务
    print("\n3️⃣ 编辑测试服务...")
    updated_service = {
        "name": "测试服务（已更新）",
        "url": "https://test-medgemma-updated.example.com",
        "description": "更新后的测试服务",
        "enabled": True
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/admin/upstream-services/test_service",
            headers=headers,
            json=updated_service
        )
        if response.status_code == 200:
            print("✅ 测试服务编辑成功")
        else:
            print(f"❌ 编辑测试服务失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 编辑服务失败: {e}")
    
    # 4. 检查服务健康状态
    print("\n4️⃣ 检查服务健康状态...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/upstream-services/health", headers=headers)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ 健康检查结果:")
            for key, status in health_data.items():
                print(f"   - {key}: {status['status']} - {status['message']}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
    
    # 5. 切换服务（如果测试服务存在）
    print("\n5️⃣ 尝试切换到测试服务...")
    try:
        switch_data = {"service_key": "test_service"}
        response = requests.post(
            f"{BASE_URL}/api/admin/upstream-services/switch",
            headers=headers,
            json=switch_data
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 服务切换成功: {result['message']}")
        else:
            print(f"❌ 服务切换失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 切换服务失败: {e}")
    
    # 6. 切换回默认服务
    print("\n6️⃣ 切换回默认服务...")
    try:
        switch_data = {"service_key": "default"}
        response = requests.post(
            f"{BASE_URL}/api/admin/upstream-services/switch",
            headers=headers,
            json=switch_data
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 切换回默认服务成功: {result['message']}")
        else:
            print(f"❌ 切换回默认服务失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 切换回默认服务失败: {e}")
    
    # 7. 删除测试服务
    print("\n7️⃣ 删除测试服务...")
    try:
        response = requests.delete(
            f"{BASE_URL}/api/admin/upstream-services/test_service",
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 测试服务删除成功: {result['message']}")
        else:
            print(f"❌ 删除测试服务失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 删除服务失败: {e}")
    
    # 8. 最终状态检查
    print("\n8️⃣ 最终状态检查...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/upstream-services", headers=headers)
        if response.status_code == 200:
            services = response.json()
            print(f"✅ 最终配置了 {len(services)} 个服务:")
            for service in services:
                current_mark = " (当前)" if service['is_current'] else ""
                print(f"   - {service['key']}: {service['name']} ({service['url']}){current_mark}")
        else:
            print(f"❌ 获取最终状态失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 最终状态检查失败: {e}")
    
    print("\n🎉 上游服务配置功能测试完成！")

if __name__ == "__main__":
    test_upstream_config()
