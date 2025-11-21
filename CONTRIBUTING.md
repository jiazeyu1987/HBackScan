# 贡献指南

欢迎为医院层级扫查微服务项目贡献代码、报告问题或提出改进建议！本指南将帮助你了解如何有效地参与项目开发。

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [测试指南](#测试指南)
- [文档贡献](#文档贡献)
- [问题报告](#问题报告)
- [功能请求](#功能请求)
- [代码审查](#代码审查)

## 行为准则

我们致力于创造一个友好、包容的社区环境。所有参与者都应该遵守以下原则：

### 我们的承诺

为了营造一个开放和友好的环境，我们作为贡献者和维护者保证，无论年龄、体型、残疾、民族、性别认同和表达、经验水平、教育背景、社会经济地位、国籍、个人外表、种族、宗教信仰或性认同和性取向，我们都不会因为参加本项目而受到骚扰。

### 我们的标准

有助于创造积极环境的行为包括：

- ✅ 使用友好和包容的语言
- ✅ 尊重不同的观点和经验
- ✅ 优雅地接受建设性批评
- ✅ 关注对社区最有利的事情
- ✅ 对其他社区成员表示同理心

不可接受的行为包括：

- ❌ 使用性化的语言或图像，以及不受欢迎的性关注或搭讪
- ❌ 恶意评论、人身攻击或政治攻击
- ❌ 公开或私下的骚扰
- ❌ 未经明确许可，发布他人的私人信息，如物理或电子地址
- ❌ 在专业环境中可能被合理认为不适当的其他行为

## 如何贡献

我们欢迎以下形式的贡献：

### 🐛 报告Bug
如果你发现了Bug，请创建[问题报告](#问题报告)。

### 💡 提出新功能
如果你有改进建议或新功能想法，请创建[功能请求](#功能请求)。

### 📝 改进文档
我们欢迎改进文档、示例和教程。

### 🔧 提交代码修复
修复Bug或实现新功能。

### 💬 参与讨论
参与GitHub Discussions的讨论。

## 开发环境设置

### 前置要求

- Python 3.8 或更高版本
- Git
- Docker 和 Docker Compose（可选）
- 代码编辑器（推荐 VS Code）

### 克隆仓库

```bash
# Fork 项目后克隆你的 fork
git clone https://github.com/YOUR-USERNAME/hospital-scanner.git
cd hospital-scanner

# 添加上游仓库
git remote add upstream https://github.com/original-org/hospital-scanner.git
```

### 环境配置

#### 方法1: 本地开发环境

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. 安装pre-commit hooks
pre-commit install

# 5. 复制环境变量模板
cp .env.example .env
# 编辑 .env 文件，设置你的配置
```

#### 方法2: Docker开发环境

```bash
# 1. 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 2. 进入容器
docker-compose exec app bash

# 3. 安装依赖（在容器内）
pip install -r requirements-dev.txt
```

### 开发工具配置

#### VS Code配置
创建 `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### 推荐的VS Code扩展
- Python
- Black Formatter
- Pylance
- GitLens
- Docker
- YAML

## 开发流程

### 分支策略

我们采用以下分支策略：

- `main`: 生产环境分支
- `develop`: 开发环境分支
- `feature/功能名称`: 功能开发分支
- `bugfix/问题描述`: Bug修复分支
- `hotfix/问题描述`: 热修复分支
- `release/版本号`: 发布分支

### 工作流程

#### 1. 创建功能分支

```bash
# 切换到develop分支
git checkout develop
git pull upstream develop

# 创建功能分支
git checkout -b feature/your-feature-name

# 或者修复bug
git checkout -b bugfix/issue-description
```

#### 2. 开发工作

```bash
# 开发你的功能
# ... 进行代码修改 ...

# 运行测试确保没有破坏现有功能
make test

# 运行代码质量检查
make lint

# 格式化代码
make format
```

#### 3. 提交变更

```bash
# 添加变更的文件
git add .

# 提交变更（使用语义化的提交消息）
git commit -m "feat: 添加医院数据模糊搜索功能"
```

#### 4. 推送分支

```bash
# 推送你的分支
git push origin feature/your-feature-name
```

#### 5. 创建Pull Request

1. 在GitHub上创建Pull Request
2. 填写PR模板
3. 等待代码审查

### 提交消息规范

我们使用[Conventional Commits](https://www.conventionalcommits.org/)规范：

```
<type>[可选范围]: <描述>

[可选正文]

[可选脚注]
```

#### 类型（type）
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更改
- `style`: 代码格式化
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

#### 示例
```bash
feat: 添加医院数据刷新任务管理功能
fix: 修复LLM客户端超时处理问题
docs: 更新API文档中的搜索接口说明
test: 添加任务管理模块的单元测试
refactor: 重构数据库查询优化性能
chore: 更新Docker镜像构建配置
```

## 代码规范

### Python代码规范

我们遵循PEP 8标准，并使用以下工具：

#### 代码格式化
```bash
# 使用Black格式化代码
black .

# 使用isort排序import
isort .

# 检查代码格式
black --check .
isort --check-only .
```

#### 代码检查
```bash
# 使用flake8检查代码风格
flake8 .

# 使用pylint进行深度检查
pylint main.py db.py llm_client.py tasks.py schemas.py

# 使用mypy进行类型检查
mypy .
```

#### 预提交钩子

我们使用pre-commit来确保代码质量：

```bash
# 安装pre-commit钩子
pre-commit install

# 手动运行所有钩子
pre-commit run --all-files
```

### 命名规范

#### 函数和变量
```python
# 使用snake_case命名
def get_provinces_list():
    pass

def create_refresh_task():
    pass

hospital_data = []
province_name = "广东省"
```

#### 类名
```python
# 使用PascalCase命名
class DatabaseManager:
    pass

class TaskManager:
    pass

class LLMClient:
    pass
```

#### 常量
```python
# 使用UPPER_SNAKE_CASE命名
MAX_CONCURRENT_TASKS = 5
DEFAULT_PAGE_SIZE = 10
API_TIMEOUT = 30.0
```

### 代码结构

#### 模块组织
```python
"""
模块文档字符串

详细描述模块的功能和用法
"""

# 标准库导入
import asyncio
import logging
from typing import Dict, List, Optional

# 第三方库导入
import fastapi
import pydantic

# 本地导入
from .models import DatabaseModel
from .utils import helper_function
```

#### 函数文档
```python
async def get_provinces(page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """
    获取省份列表
    
    Args:
        page: 页码，从1开始
        page_size: 每页数量，默认10条
    
    Returns:
        包含省份列表和分页信息的字典
        
    Raises:
        ValidationError: 当page或page_size无效时
        DatabaseError: 当数据库操作失败时
        
    Example:
        >>> result = await get_provinces(page=1, page_size=20)
        >>> print(result['total'])
        34
    """
    pass
```

## 测试指南

### 测试策略

我们采用三层测试策略：

1. **单元测试**：测试独立的函数和方法
2. **集成测试**：测试模块间的协作
3. **端到端测试**：测试完整的用户场景

### 运行测试

```bash
# 运行所有测试
make test

# 运行特定类型的测试
pytest -m unit           # 只运行单元测试
pytest -m integration    # 只运行集成测试
pytest -m e2e           # 只运行端到端测试

# 运行特定测试文件
pytest tests/test_llm_client.py

# 运行特定测试函数
pytest tests/test_llm_client.py::test_get_provinces_success

# 生成覆盖率报告
make test-coverage

# 详细输出
pytest -v -s
```

### 编写测试

#### 单元测试示例
```python
import pytest
from unittest.mock import AsyncMock, patch

from llm_client import LLMClient

@pytest.mark.unit
class TestLLMClient:
    """LLM客户端单元测试"""
    
    @pytest.fixture
    def client(self):
        return LLMClient(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_get_provinces_success(self, client):
        """测试获取省份成功"""
        # Mock HTTP响应
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "output": {
                "text": '{"items": [{"name": "北京市", "code": null}]}'
            }
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await client.get_provinces()
            
            assert "items" in result
            assert len(result["items"]) == 1
            assert result["items"][0]["name"] == "北京市"
```

#### 测试最佳实践

1. **使用描述性的测试名称**
```python
# 好的测试名称
async def test_get_provinces_with_empty_database():
    """测试空数据库时的省份获取"""
    pass

# 避免模糊的测试名称
async def test_get_provinces():
    """❌ 太简单，没有描述场景"""
    pass
```

2. **测试边界条件**
```python
async def test_create_task_with_invalid_province_name():
    """测试无效省份名称的任务创建"""
    with pytest.raises(ValidationError):
        await task_manager.create_province_refresh_task("")
    
    with pytest.raises(ValidationError):
        await task_manager.create_province_refresh_task(None)
```

3. **使用Mock隔离外部依赖**
```python
@pytest.mark.asyncio
async def test_database_operation_without_real_db():
    """测试不依赖真实数据库的数据库操作"""
    mock_db = AsyncMock()
    result = await some_database_function(mock_db)
    
    mock_db.create_province.assert_called_once()
    assert result is not None
```

### 测试覆盖率要求

- **单元测试覆盖率**: ≥ 95%
- **集成测试覆盖率**: ≥ 80%
- **关键路径覆盖率**: 100%

```bash
# 检查覆盖率
pytest --cov=code/hospital_scanner --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

## 文档贡献

### 文档类型

我们维护以下类型的文档：

1. **API文档** - OpenAPI/Swagger自动生成
2. **用户指南** - 使用说明和示例
3. **开发者文档** - 代码结构和开发指南
4. **部署指南** - 安装和配置说明

### 文档位置

- **API文档**: 在代码中通过docstring自动生成
- **用户指南**: `docs/user-guide/`
- **开发者文档**: `docs/dev-guide/`
- **README**: 项目根目录

### 编写文档

#### API文档
```python
async def get_hospitals(district_name: str, page: int = 1, page_size: int = 10):
    """
    根据区县名称获取医院列表
    
    获取指定区县下所有医院的基本信息，包括医院名称、官网地址和LLM置信度。
    
    Args:
        district_name (str): 区县名称，必须是非空字符串
        page (int, optional): 页码，从1开始。默认值为1
        page_size (int, optional): 每页显示数量，最大值为100。默认值为10
    
    Returns:
        dict: 包含医院列表和分页信息的字典
        
        成功响应格式:
        {
            "code": 200,
            "message": "获取医院列表成功",
            "data": {
                "items": [
                    {
                        "id": 123,
                        "name": "医院名称",
                        "website": "https://hospital.com",
                        "llm_confidence": 0.95
                    }
                ],
                "total": 156,
                "page": 1,
                "page_size": 10,
                "total_pages": 16
            }
        }
    
    Raises:
        HTTPException: 当区县名称为空或无效时
        ValidationError: 当分页参数无效时
    
    Example:
        获取越秀区的医院：
        >>> hospitals = await get_hospitals("越秀区", page=1, page_size=20)
        >>> print(f"找到 {hospitals['total']} 家医院")
        
        分页查询：
        >>> page1 = await get_hospitals("越秀区", page=1, page_size=50)
        >>> page2 = await get_hospitals("越秀区", page=2, page_size=50)
    """
    pass
```

#### 用户指南
```markdown
# 医院数据查询指南

## 概述

本指南介绍如何使用医院层级扫查微服务查询医院数据。

## 基础查询

### 按层级查询

1. 首先获取省份列表：
   ```python
   provinces = await client.get_provinces()
   ```

2. 根据省份获取城市：
   ```python
   cities = await client.get_cities("广东省")
   ```

3. 根据城市获取区县：
   ```python
   districts = await client.get_districts("广州市")
   ```

4. 根据区县获取医院：
   ```python
   hospitals = await client.get_hospitals("越秀区")
   ```

## 高级查询

### 模糊搜索

使用医院名称模糊搜索：
```python
results = await client.search_hospitals("协和")
```

## 错误处理

常见的错误情况及处理方法...

## 性能优化

查询性能优化建议...
```

## 问题报告

### 报告Bug

在报告Bug时请使用我们的问题模板：

**Bug报告模板：**

```markdown
## Bug描述
简要描述Bug的情况

## 复现步骤
1. 访问 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

## 期望行为
描述你期望发生什么

## 实际行为
描述实际发生了什么

## 截图
如果适用，添加截图

## 环境信息
- OS: [e.g. Ubuntu 20.04]
- Python版本: [e.g. 3.9.7]
- 项目版本: [e.g. 1.0.0]
- 依赖版本: [e.g. FastAPI 0.104.1]

## 额外信息
添加任何其他关于问题的信息
```

### 问题报告最佳实践

1. **搜索现有问题** - 在创建新问题前，先搜索是否已有类似问题

2. **提供详细信息** - 包含足够的信息帮助开发者复现问题

3. **提供复现步骤** - 清晰的步骤说明如何复现问题

4. **包含环境信息** - 操作系统、Python版本、依赖版本等

5. **附加日志** - 包含相关的错误日志和堆栈跟踪

## 功能请求

### 功能请求模板

```markdown
## 功能描述
简要描述你希望的功能

## 问题背景
这个功能解决了什么问题？

## 期望解决方案
你希望这个功能如何工作？

## 替代方案
考虑过的替代解决方案？

## 额外信息
添加任何其他关于功能请求的信息
```

### 功能请求指导

1. **检查现有功能** - 确认功能尚未存在

2. **明确价值** - 解释功能的价值和用途

3. **提供用例** - 具体的用例场景

4. **考虑复杂度** - 评估实现复杂度

## 代码审查

### Pull Request审查指南

#### 审查者指南

1. **功能性审查**
   - 代码是否实现了所需的功能？
   - 是否有边界情况处理？
   - 错误处理是否充分？

2. **代码质量审查**
   - 代码是否遵循项目规范？
   - 是否有不必要的复杂度？
   - 命名是否清晰？

3. **测试审查**
   - 是否有足够的测试覆盖？
   - 测试用例是否全面？
   - 测试是否通过？

4. **性能审查**
   - 是否有性能问题？
   - 算法选择是否合理？
   - 资源使用是否高效？

#### 提交者指南

1. **保持PR小而专注**
   - 一个PR只解决一个问题
   - 避免混合多个功能
   - 保持变更范围合理

2. **提供清晰的描述**
   - PR标题清晰简洁
   - 描述包含变更原因和内容
   - 包含截图或示例

3. **确保质量**
   - 运行所有测试
   - 通过代码质量检查
   - 更新相关文档

### PR审查流程

1. **自动检查** - CI/CD管道运行
2. **代码审查** - 至少一个维护者审查
3. **测试** - 所有测试通过
4. **合并** - 合并到目标分支

## 维护者指南

### 成为维护者

我们欢迎长期贡献者成为维护者：

- 持续贡献高质量代码
- 参与代码审查
- 帮助社区成员
- 维护项目健康

### 维护者责任

- 审查和合并PR
- 管理问题报告
- 发布新版本
- 维护项目文档
- 指导新贡献者

## 奖励和认可

我们通过以下方式认可贡献者：

- 在CHANGELOG中记录重要贡献
- 在项目文档中致谢
- GitHub贡献者统计
- 发布说明中的贡献者名单

## 联系方式

如有问题请联系：

- **项目维护者**: maintainers@hospital-scanner.com
- **社区论坛**: [GitHub Discussions](https://github.com/org/hospital-scanner/discussions)
- **实时讨论**: [Discord服务器](https://discord.gg/hospital-scanner)

## 感谢

感谢所有为项目做出贡献的开发者和用户！

---

再次感谢你的贡献！🙏
