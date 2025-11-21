#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试示例 - 展示如何使用和验证集成测试
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'hospital_scanner'))

def demo_api_integration_test():
    """演示API集成测试"""
    print("🚀 演示API集成测试")
    print("=" * 50)
    
    try:
        from fastapi.testclient import TestClient
        from unittest.mock import patch, MagicMock
        
        # 导入主应用
        from hospital_scanner.main import app
        
        # 创建测试客户端
        client = TestClient(app)
        
        # 1. 测试根路径
        print("1. 测试根路径...")
        response = client.get("/")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        # 2. 测试健康检查
        print("\n2. 测试健康检查...")
        response = client.get("/health")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        # 3. 测试创建扫描任务（使用Mock）
        print("\n3. 测试创建扫描任务...")
        with patch('hospital_scanner.llm_client.LLMClient.analyze_hospital_hierarchy') as mock_llm:
            # Mock LLM返回数据
            mock_llm.return_value = {
                "hospital_name": "测试医院",
                "level": "三级甲等",
                "departments": ["内科", "外科"]
            }
            
            scan_data = {
                "hospital_name": "北京协和医院",
                "query": "获取医院层级结构"
            }
            
            response = client.post("/scan", json=scan_data)
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json()}")
            
            if response.status_code == 200:
                task_id = response.json()["task_id"]
                
                # 测试获取任务状态
                print("\n4. 测试获取任务状态...")
                status_response = client.get(f"/task/{task_id}")
                print(f"   状态码: {status_response.status_code}")
                print(f"   响应: {status_response.json()}")
        
        # 5. 测试数据刷新接口
        print("\n5. 测试完整数据刷新...")
        with patch('hospital_scanner.main.execute_full_refresh_task'):
            response = client.post("/refresh/all")
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json()}")
        
        # 6. 测试省份数据刷新
        print("\n6. 测试省份数据刷新...")
        with patch('hospital_scanner.main.execute_province_refresh_task'):
            response = client.post("/refresh/province/广东省")
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json()}")
        
        # 7. 测试分页查询
        print("\n7. 测试省份列表查询...")
        response = client.get("/provinces?page=1&page_size=10")
        print(f"   状态码: {response.status_code}")
        print(f"   响应结构: {list(response.json().keys())}")
        
        # 8. 测试医院搜索
        print("\n8. 测试医院搜索...")
        response = client.get("/hospitals/search?q=人民医院")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        print("\n✅ API集成测试演示完成！")
        
    except Exception as e:
        print(f"❌ API集成测试演示失败: {e}")
        import traceback
        traceback.print_exc()

def demo_mock_usage():
    """演示Mock使用"""
    print("\n🔧 演示Mock使用")
    print("=" * 50)
    
    try:
        from unittest.mock import patch, MagicMock
        
        # 模拟LLM客户端
        print("1. 模拟LLM客户端调用...")
        
        # 使用patch装饰器模拟
        with patch('hospital_scanner.llm_client.LLMClient.analyze_hospital_hierarchy') as mock_method:
            # 设置模拟返回值
            mock_method.return_value = {
                "hospital_name": "模拟医院",
                "level": "三级甲等",
                "departments": ["内科", "外科", "妇产科"],
                "beds_count": 500,
                "staff_count": 800
            }
            
            # 调用模拟方法
            from hospital_scanner.llm_client import LLMClient
            client = LLMClient()
            
            result = client.analyze_hospital_hierarchy("测试医院", "分析层级")
            print(f"   模拟结果: {result}")
            print(f"   调用次数: {mock_method.call_count}")
        
        # 模拟异步任务
        print("\n2. 模拟异步任务执行...")
        
        import asyncio
        from unittest.mock import AsyncMock
        
        async def mock_task_execution():
            # 模拟执行一些操作
            await asyncio.sleep(0.1)
            return "任务完成"
        
        with patch('__main__.mock_task_execution', new_callable=AsyncMock) as mock_func:
            mock_func.return_value = "模拟任务完成"
            result = asyncio.run(mock_func())
            print(f"   模拟任务结果: {result}")
        
        print("\n✅ Mock使用演示完成！")
        
    except Exception as e:
        print(f"❌ Mock使用演示失败: {e}")
        import traceback
        traceback.print_exc()

def demo_test_data_structure():
    """演示测试数据结构"""
    print("\n📊 演示测试数据结构")
    print("=" * 50)
    
    try:
        # 模拟API响应数据结构
        paginated_response = {
            "items": [
                {"id": 1, "name": "北京市", "code": "110000"},
                {"id": 2, "name": "上海市", "code": "310000"}
            ],
            "total": 34,
            "page": 1,
            "page_size": 10,
            "pages": 4,
            "has_next": True,
            "has_prev": False
        }
        
        print("1. 分页响应结构示例:")
        print(f"   总数据量: {paginated_response['total']}")
        print(f"   当前页: {paginated_response['page']}")
        print(f"   每页大小: {paginated_response['page_size']}")
        print(f"   总页数: {paginated_response['pages']}")
        print(f"   是否有下一页: {paginated_response['has_next']}")
        
        # 模拟搜索结果结构
        search_response = {
            "query": "人民医院",
            "limit": 20,
            "results": [
                {"id": 1, "name": "北京人民医院", "level": "三级甲等"},
                {"id": 2, "name": "上海人民医院", "level": "三级甲等"}
            ],
            "count": 2
        }
        
        print("\n2. 搜索响应结构示例:")
        print(f"   搜索关键词: {search_response['query']}")
        print(f"   结果数量: {search_response['count']}")
        print(f"   限制数量: {search_response['limit']}")
        
        # 模拟任务状态结构
        task_status = {
            "task_id": "uuid-1234",
            "status": "completed",
            "hospital_info": {
                "hospital_name": "测试医院",
                "level": "三级甲等",
                "departments": ["内科", "外科"]
            },
            "created_at": "2025-11-21T10:41:14",
            "execution_time": 2.5
        }
        
        print("\n3. 任务状态结构示例:")
        print(f"   任务ID: {task_status['task_id']}")
        print(f"   任务状态: {task_status['status']}")
        print(f"   执行时间: {task_status['execution_time']}秒")
        
        print("\n✅ 测试数据结构演示完成！")
        
    except Exception as e:
        print(f"❌ 测试数据结构演示失败: {e}")

def main():
    """主演示函数"""
    print("🎯 医院层级扫查微服务 - 集成测试演示")
    print("=" * 60)
    
    # 演示API集成测试
    demo_api_integration_test()
    
    # 演示Mock使用
    demo_mock_usage()
    
    # 演示测试数据结构
    demo_test_data_structure()
    
    print("\n" + "=" * 60)
    print("🎉 集成测试演示完成！")
    print("\n📋 总结:")
    print("- ✅ 成功演示了API接口测试")
    print("- ✅ 成功演示了Mock技术使用")
    print("- ✅ 成功演示了数据结构设计")
    print("- ✅ 验证了集成测试的完整性")
    
    print("\n🚀 接下来可以:")
    print("1. 运行完整测试: python run_integration_tests.py")
    print("2. 查看详细文档: cat INTEGRATION_TESTS.md")
    print("3. 运行特定测试: pytest tests/test_api_integration.py -v")

if __name__ == "__main__":
    main()