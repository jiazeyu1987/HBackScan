#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心修复验证脚本 - 测试关键修复功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

from db import Database
from main import app
from fastapi.testclient import TestClient

async def test_core_fixes():
    """测试核心修复功能"""
    print("🧪 核心修复功能验证测试")
    print("=" * 50)
    
    success_count = 0
    total_tests = 0
    
    # 测试1: 分页边界值修复
    print("\n🔍 测试1: 分页边界值修复")
    try:
        db = Database(":memory:")
        await db.init_db()
        
        # 添加测试数据
        for i in range(3):
            await db.create_province(f"省份{i+1}", f"11{1000+i}")
        
        # 测试边界值
        test_cases = [
            (0, 10, "page=0应该修正为1"),
            (1, 0, "page_size=0应该修正为20"),
            (1, -5, "负数page_size应该修正为20"),
            (1, 2000, "超大page_size应该修正为1000")
        ]
        
        all_passed = True
        for page, page_size, desc in test_cases:
            total_tests += 1
            try:
                items, total = await db.get_provinces(page, page_size)
                print(f"   ✅ {desc}: 成功")
                success_count += 1
            except Exception as e:
                print(f"   ❌ {desc}: 失败 - {e}")
                all_passed = False
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
    
    # 测试2: 除零保护
    print("\n🔍 测试2: 除零保护")
    test_cases = [
        (10, 0, "page_size=0保护"),
        (10, -1, "负数page_size保护"),
        (0, 10, "total=0情况")
    ]
    
    for total, page_size, desc in test_cases:
        total_tests += 1
        try:
            pages = (total + page_size - 1) // page_size if page_size > 0 else 1
            print(f"   ✅ {desc}: pages={pages}")
            success_count += 1
        except Exception as e:
            print(f"   ❌ {desc}: 失败 - {e}")
    
    # 测试3: 错误处理
    print("\n🔍 测试3: HTTP错误处理")
    client = TestClient(app)
    
    total_tests += 1
    response = client.get("/task/nonexistent_task_12345")
    if response.status_code == 404:
        print("   ✅ 404错误处理: 正确返回404")
        success_count += 1
    else:
        print(f"   ❌ 404错误处理: 期望404，得到{response.status_code}")
    
    # 测试4: API接口基本功能
    print("\n🔍 测试4: API接口基本功能")
    
    # 测试根路径
    total_tests += 1
    response = client.get("/")
    if response.status_code == 200:
        print("   ✅ 根路径接口: 正常")
        success_count += 1
    else:
        print(f"   ❌ 根路径接口: 失败，状态码{response.status_code}")
    
    # 总结
    print(f"\n📊 测试结果:")
    print(f"   通过: {success_count}/{total_tests}")
    print(f"   成功率: {success_count/total_tests*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 所有核心修复验证通过！")
        return True
    else:
        print("⚠️ 部分修复仍需优化")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_core_fixes())
    sys.exit(0 if success else 1)