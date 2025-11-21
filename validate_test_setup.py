#!/usr/bin/env python3
"""
测试配置验证脚本
验证所有测试工具和配置是否正确设置
"""

import os
import sys
import subprocess
from pathlib import Path


def check_file_exists(file_path: str, description: str) -> bool:
    """检查文件是否存在"""
    if Path(file_path).exists():
        print(f"✓ {description}: {file_path}")
        return True
    else:
        print(f"✗ {description}未找到: {file_path}")
        return False


def check_directory_exists(dir_path: str, description: str) -> bool:
    """检查目录是否存在"""
    if Path(dir_path).exists():
        print(f"✓ {description}: {dir_path}")
        return True
    else:
        print(f"✗ {description}未找到: {dir_path}")
        return False


def run_command(command: str, description: str) -> bool:
    """运行命令并检查是否成功"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description}: 成功")
            return True
        else:
            print(f"✗ {description}: 失败")
            print(f"  错误: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ {description}: 异常 - {e}")
        return False


def main():
    """主检查函数"""
    print("=" * 60)
    print("测试工具配置验证")
    print("=" * 60)
    
    all_checks_passed = True
    
    # 检查项目结构
    print("\n1. 检查项目结构:")
    required_files = [
        ("tests/conftest.py", "Pytest配置文件"),
        ("tests/fixtures/__init__.py", "测试夹具包"),
        ("tests/fixtures/llm_responses.py", "LLM响应夹具"),
        ("tests/fixtures/sample_data.py", "样本数据夹具"),
        ("tests/fixtures/mock_json_responses.py", "模拟JSON响应"),
        ("tests/helpers.py", "测试辅助工具"),
        ("tests/test_examples.py", "示例测试文件"),
        ("pytest.ini", "pytest配置文件"),
        ("Makefile", "Makefile构建文件"),
        ("requirements.txt", "项目依赖"),
        ("requirements-dev.txt", "开发依赖"),
        ("tests/.env.test", "测试环境变量"),
        (".github/workflows/ci.yml", "GitHub Actions配置")
    ]
    
    for file_path, description in required_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # 检查目录结构
    print("\n2. 检查目录结构:")
    required_dirs = [
        ("tests", "测试目录"),
        ("tests/fixtures", "测试夹具目录"),
        ("tests/logs", "测试日志目录"),
        ("test-reports", "测试报告目录"),
        ("htmlcov", "覆盖率报告目录"),
        (".github/workflows", "GitHub工作流目录")
    ]
    
    for dir_path, description in required_dirs:
        if not check_directory_exists(dir_path, description):
            all_checks_passed = False
    
    # 检查Python环境
    print("\n3. 检查Python环境:")
    python_checks = [
        ("python3 --version", "Python版本"),
        ("python3 -m pytest --version", "Pytest版本"),
        ("python3 -c 'import fastapi'", "FastAPI安装"),
        ("python3 -c 'import requests'", "Requests安装"),
        ("python3 -c 'import pydantic'", "Pydantic安装")
    ]
    
    for command, description in python_checks:
        if not run_command(command, description):
            all_checks_passed = False
    
    # 检查测试工具
    print("\n4. 检查测试工具:")
    tool_checks = [
        ("python3 -m pytest --collect-only tests/ > /dev/null", "Pytest收集测试"),
        ("python3 -c 'from tests.helpers import TestDataFactory'", "测试工厂导入"),
        ("python3 -c 'from tests.fixtures.sample_data import SAMPLE_HOSPITALS'", "样本数据导入"),
        ("python3 -c 'from tests.conftest import *'", "配置文件导入")
    ]
    
    for command, description in tool_checks:
        if not run_command(command, description):
            all_checks_passed = False
    
    # 运行示例测试
    print("\n5. 运行示例测试:")
    if not run_command("python3 -m pytest tests/test_examples.py -v --tb=short", "示例测试执行"):
        all_checks_passed = False
    
    # 检查Make命令
    print("\n6. 检查Make命令:")
    make_checks = [
        ("make help", "Make帮助命令"),
        ("make test --dry-run", "测试命令语法"),
        ("make test-unit --dry-run", "单元测试命令"),
        ("make test-coverage --dry-run", "覆盖率命令")
    ]
    
    for command, description in make_checks:
        if not run_command(command, description):
            all_checks_passed = False
    
    # 总结
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✓ 所有检查通过！测试工具配置正确。")
        print("\n可以开始运行测试:")
        print("  make test          - 运行所有测试")
        print("  make test-unit     - 运行单元测试")
        print("  make test-coverage - 生成覆盖率报告")
        print("  make help          - 查看所有可用命令")
        return 0
    else:
        print("✗ 某些检查失败，请修复上述问题。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
