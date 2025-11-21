#!/usr/bin/env python3
"""
快速测试两个特定测试用例
"""

import subprocess
import sys
import os

# 切换到项目目录
os.chdir('/workspace/code/hospital_scanner')

def run_test():
    """运行特定测试"""
    try:
        # 运行test_list_tasks
        print("=== 运行 test_list_tasks ===")
        result1 = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/test_api_integration.py::TestAPIIntegration::test_list_tasks', 
            '-v', '-s', '--tb=short'
        ], capture_output=True, text=True, timeout=30)
        
        print("STDOUT:")
        print(result1.stdout)
        if result1.stderr:
            print("STDERR:")
            print(result1.stderr)
        print(f"Return code: {result1.returncode}")
        
        print("\n" + "="*50 + "\n")
        
        # 运行test_concurrent_requests  
        print("=== 运行 test_concurrent_requests ===")
        result2 = subprocess.run([
            sys.executable, '-m', 'pytest',
            'tests/test_api_integration.py::TestAPIIntegration::test_concurrent_requests',
            '-v', '-s', '--tb=short'
        ], capture_output=True, text=True, timeout=30)
        
        print("STDOUT:")
        print(result2.stdout)
        if result2.stderr:
            print("STDERR:")
            print(result2.stderr)
        print(f"Return code: {result2.returncode}")
        
        # 总结
        print("\n" + "="*50)
        print("测试结果总结:")
        print(f"test_list_tasks: {'PASS' if result1.returncode == 0 else 'FAIL'}")
        print(f"test_concurrent_requests: {'PASS' if result2.returncode == 0 else 'FAIL'}")
        
        if result1.returncode == 0 and result2.returncode == 0:
            print("🎉 所有测试通过！修复成功！")
        else:
            print("❌ 仍有测试失败，需要进一步调试")
            
    except subprocess.TimeoutExpired:
        print("测试超时")
    except Exception as e:
        print(f"运行测试时出错: {e}")

if __name__ == "__main__":
    run_test()