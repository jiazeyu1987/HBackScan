#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
契约测试示例
展示如何使用契约测试验证API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tests.test_contracts import ContractValidator, TestOpenAPISchema, TestResponseFormat
from fastapi.testclient import TestClient
from main import app

def demo_contract_validation():
    """演示契约验证"""
    print("🧪 契约测试示例演示")
    print("=" * 50)
    
    # 创建测试客户端
    client = TestClient(app)
    
    # 1. 创建契约验证器
    print("\n1️⃣ 创建契约验证器")
    validator = ContractValidator()
    print("✅ 契约验证器创建成功")
    
    # 2. 验证健康检查响应
    print("\n2️⃣ 验证健康检查响应")
    response = client.get("/health")
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"响应数据: {data}")
        
        # 验证响应格式
        if validator.validate_response_format(data):
            print("✅ 响应格式验证通过")
        else:
            print("❌ 响应格式验证失败")
        
        # 验证必要字段
        required_fields = ["code", "message", "data"]
        for field in required_fields:
            if field in data:
                print(f"✅ 字段 '{field}' 存在")
            else:
                print(f"❌ 字段 '{field}' 缺失")
    
    # 3. 验证任务状态
    print("\n3️⃣ 验证任务状态枚举")
    test_statuses = ["pending", "running", "succeeded", "failed", "invalid"]
    
    for status in test_statuses:
        if validator.validate_task_status(status):
            print(f"✅ '{status}' 是有效的任务状态")
        else:
            print(f"❌ '{status}' 是无效的任务状态")
    
    # 4. 测试错误处理
    print("\n4️⃣ 测试错误处理")
    error_response = client.get("/tasks/invalid-task")
    print(f"错误响应状态码: {error_response.status_code}")
    
    if error_response.status_code == 404:
        print("✅ 404错误处理正确")
        error_data = error_response.json()
        print(f"错误响应: {error_data}")
    else:
        print("❌ 错误处理异常")
    
    # 5. 测试数据一致性
    print("\n5️⃣ 测试数据一致性")
    provinces_response = client.get("/provinces")
    if provinces_response.status_code == 200:
        provinces_data = provinces_response.json()
        print(f"省份数据: {provinces_data}")
        
        if validator.validate_response_format(provinces_data):
            print("✅ 省份数据格式验证通过")
        else:
            print("❌ 省份数据格式验证失败")
    
    # 6. 测试OpenAPI Schema
    print("\n6️⃣ 测试OpenAPI Schema")
    openapi_schema = app.openapi()
    print(f"OpenAPI版本: {openapi_schema.get('openapi')}")
    print(f"API标题: {openapi_schema['info']['title']}")
    print(f"API版本: {openapi_schema['info']['version']}")
    print(f"端点数量: {len(openapi_schema['paths'])}")
    
    print("\n" + "=" * 50)
    print("🎉 契约验证演示完成！")
    
    return True

def run_specific_tests():
    """运行特定测试"""
    print("\n🔍 运行特定契约测试...")
    
    # 运行OpenAPI schema测试
    print("\n📋 OpenAPI Schema测试:")
    openapi_tests = TestOpenAPISchema()
    try:
        openapi_tests.test_openapi_schema_exists()
        print("  ✅ OpenAPI schema存在测试通过")
    except Exception as e:
        print(f"  ❌ OpenAPI schema存在测试失败: {e}")
    
    try:
        openapi_tests.test_openapi_info()
        print("  ✅ OpenAPI信息测试通过")
    except Exception as e:
        print(f"  ❌ OpenAPI信息测试失败: {e}")
    
    # 运行响应格式测试
    print("\n📋 响应格式测试:")
    response_tests = TestResponseFormat()
    try:
        response_tests.test_response_model_structure()
        print("  ✅ 响应模型结构测试通过")
    except Exception as e:
        print(f"  ❌ 响应模型结构测试失败: {e}")
    
    try:
        response_tests.test_success_response_format()
        print("  ✅ 成功响应格式测试通过")
    except Exception as e:
        print(f"  ❌ 成功响应格式测试失败: {e}")

if __name__ == "__main__":
    print("🎯 契约测试示例")
    print("这个示例展示了如何使用契约测试验证API")
    
    # 运行演示
    demo_contract_validation()
    
    # 运行特定测试
    run_specific_tests()
    
    print("\n📚 更多信息请查看:")
    print("  - CONTRACT_TESTS.md (详细文档)")
    print("  - CONTRACT_TESTS_SUMMARY.md (实现总结)")
    print("  - python run_contract_tests.py (运行所有测试)")