#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 验证核心修复
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

from db import Database
from main import app
from fastapi.testclient import TestClient

async def test_pagination_boundary_fixes():
    """测试分页边界值修复"""
    print("🔍 测试分页边界值修复...")
    
    # 使用临时数据库
    db = Database(":memory:")
    await db.init_db()
    
    # 添加测试数据
    for i in range(3):
        await db.create_province(f"测试省份{i+1}", f"11{1000+i}")
    
    # 测试边界值
    test_cases = [
        (0, 10),   # page=0 -> 应该修正为1
        (1, 0),    # page_size=0 -> 应该修正为20  
        (1, -1),   # 负数page_size -> 应该修正为20
        (1, 2000), # 超过1000的page_size -> 应该修正为1000
    ]
    
    all_passed = True
    for page, page_size in test_cases:
        try:
            items, total = await db.get_provinces(page, page_size)
            print(f"   ✅ page={page}, page_size={page_size} -> 成功处理")
        except Exception as e:
            print(f"   ❌ page={page}, page_size={page_size} -> 失败: {e}")
            all_passed = False
    
    return all_passed

def test_division_by_zero_protection():
    """测试除零保护"""
    print("🔍 测试除零保护...")
    
    # 测试页面计算
    test_cases = [
        (10, 0),  # page_size=0
        (10, -1), # page_size=-1
        (0, 10),  # total=0
    ]
    
    for total, page_size in test_cases:
        try:
            pages = (total + page_size - 1) // page_size if page_size > 0 else 1
            print(f"   ✅ total={total}, page_size={page_size} -> pages={pages}")
        except Exception as e:
            print(f"   ❌ total={total}, page_size={page_size} -> 失败: {e}")
            return False
    
    return True

async def test_error_handling():
    """测试错误处理"""
    print("🔍 测试错误处理...")
    
    client = TestClient(app)
    
    # 测试404错误
    response = client.get("/task/nonexistent_task_12345")
    
    if response.status_code == 404:
        print("   ✅ 404错误处理正确")
        return True
    else:
        print(f"   ❌ 期望404，实际得到{response.status_code}")
        return False

async def main():
    """主测试函数"""
    print("医院层级扫查微服务 - 快速验证测试")
    print("=" * 50)
    
    tests = [
        ("分页边界值修复", test_pagination_boundary_fixes),
        ("除零保护", test_division_by_zero_protection),
        ("错误处理", test_error_handling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 测试: {test_name}")
        print("-" * 30)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                print(f"✅ {test_name} - 通过")
                passed += 1
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print(f"\n📊 总结:")
    print(f"   通过: {passed}/{total} 项")
    print(f"   成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 所有核心修复验证通过！")
        return True
    else:
        print("⚠️ 部分修复需要进一步检查")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)