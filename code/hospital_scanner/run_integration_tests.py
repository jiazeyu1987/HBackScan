#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务 - 集成测试运行脚本
"""

import os
import sys
import subprocess
import pytest

def run_integration_tests():
    """运行集成测试"""
    print("开始运行医院层级扫查微服务集成测试...")
    print("=" * 50)
    
    # 切换到项目目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # 安装测试依赖
    print("1. 安装测试依赖...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov"], check=True)
        print("✓ 依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"✗ 依赖安装失败: {e}")
        return False
    
    # 运行API集成测试
    print("\n2. 运行API集成测试...")
    try:
        result = pytest.main([
            "tests/test_api_integration.py",
            "-v",
            "--tb=short",
            "--disable-warnings"
        ])
        if result == 0:
            print("✓ API集成测试通过")
        else:
            print("✗ API集成测试失败")
            return False
    except Exception as e:
        print(f"✗ API集成测试运行失败: {e}")
        return False
    
    # 运行完整流程测试
    print("\n3. 运行完整流程测试...")
    try:
        result = pytest.main([
            "tests/test_complete_flow.py",
            "-v",
            "--tb=short",
            "--disable-warnings"
        ])
        if result == 0:
            print("✓ 完整流程测试通过")
        else:
            print("✗ 完整流程测试失败")
            return False
    except Exception as e:
        print(f"✗ 完整流程测试运行失败: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 所有集成测试通过！")
    return True

def run_specific_test(test_file, test_name=None):
    """运行特定测试"""
    print(f"运行特定测试: {test_file}")
    if test_name:
        print(f"测试名称: {test_name}")
    
    cmd = [sys.executable, "-m", "pytest", test_file, "-v"]
    if test_name:
        cmd.extend(["-k", test_name])
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"测试运行失败: {e}")
        return False

def show_test_summary():
    """显示测试总结"""
    print("\n" + "=" * 50)
    print("医院层级扫查微服务 - 集成测试说明")
    print("=" * 50)
    print()
    print("测试文件:")
    print("1. test_api_integration.py - API接口集成测试")
    print("   - 测试所有API端点")
    print("   - 使用Mock模拟LLM调用")
    print("   - 测试分页参数")
    print("   - 测试错误处理")
    print()
    print("2. test_complete_flow.py - 完整流程集成测试")
    print("   - 测试完整的数据刷新流程")
    print("   - 测试省级、市级、区县级、医院级数据处理")
    print("   - 验证数据一致性和完整性")
    print("   - 测试搜索功能")
    print("   - 测试负载下的性能")
    print()
    print("主要测试场景:")
    print("✓ POST /scan - 创建扫查任务")
    print("✓ POST /refresh/all - 完整数据刷新")
    print("✓ POST /refresh/province/{name} - 省份数据刷新")
    print("✓ GET /provinces - 获取省份列表（分页）")
    print("✓ GET /cities - 获取城市列表（分页）")
    print("✓ GET /districts - 获取区县列表（分页）")
    print("✓ GET /hospitals - 获取医院列表（分页）")
    print("✓ GET /hospitals/search?q= - 医院搜索")
    print("✓ GET /tasks/{task_id} - 任务状态查询")
    print("✓ GET /tasks - 任务列表")
    print("✓ GET /health - 健康检查")
    print()
    print("Mock使用:")
    print("- 使用unittest.mock.patch模拟LLM API调用")
    print("- 使用模拟响应避免真实的API调用")
    print("- 测试错误情况和边界情况")
    print()
    print("运行命令:")
    print("python run_integration_tests.py          # 运行所有测试")
    print("python run_integration_tests.py api      # 只运行API测试")
    print("python run_integration_tests.py flow     # 只运行流程测试")
    print("python run_integration_tests.py summary  # 显示测试说明")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "api":
            run_specific_test("tests/test_api_integration.py")
        elif command == "flow":
            run_specific_test("tests/test_complete_flow.py")
        elif command == "summary":
            show_test_summary()
        else:
            print(f"未知命令: {command}")
            show_test_summary()
    else:
        # 运行所有测试
        success = run_integration_tests()
        if not success:
            sys.exit(1)