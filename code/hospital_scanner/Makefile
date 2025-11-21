# 医院层级扫查微服务 Makefile

.PHONY: help install run test clean lint format docs build deploy

# 默认目标
help: ## 显示帮助信息
	@echo "医院层级扫查微服务 - 可用命令:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# 环境设置
install: ## 安装依赖包
	pip install -r requirements.txt

install-dev: ## 安装开发依赖包
	pip install -r requirements.txt
	pip install -e .

setup: install install-dev ## 初始化开发环境
	mkdir -p logs data
	cp .env.example .env
	@echo "请编辑 .env 文件配置必要的环境变量"

# 运行
run: ## 启动开发服务器
	python main.py

run-prod: ## 启动生产服务器
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

run-gunicorn: ## 使用Gunicorn启动
	gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

dev: ## 启动开发服务器（热重载）
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 测试
test: ## 运行所有测试
	pytest

test-cov: ## 运行测试并生成覆盖率报告
	pytest --cov=. --cov-report=html --cov-report=term

test-unit: ## 运行单元测试
	pytest tests/ -m unit

test-integration: ## 运行集成测试
	pytest tests/ -m integration

test-api: ## 运行API测试
	pytest tests/ -m api

test-db: ## 运行数据库测试
	pytest tests/ -m db

test-llm: ## 运行LLM测试
	pytest tests/ -m llm

# 代码质量
lint: ## 检查代码风格
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	black --check .
	isort --check-only .

format: ## 格式化代码
	black .
	isort .

format-check: ## 检查代码格式
	black --check .
	isort --check-only .

# 数据库操作
db-init: ## 初始化数据库
	python -c "from db import init_db; import asyncio; asyncio.run(init_db())"

db-reset: ## 重置数据库
	rm -f data/hospital_scanner.db
	python -c "from db import init_db; import asyncio; asyncio.run(init_db())"

db-migrate: ## 数据库迁移（预留）
	@echo "数据库迁移功能待实现"

# 日志
logs: ## 查看日志
	tail -f logs/scanner.log

logs-error: ## 查看错误日志
	tail -f logs/scanner.log | grep ERROR

logs-clean: ## 清理日志文件
	rm -f logs/*.log
	rm -rf logs/archive/

# 清理
clean: ## 清理生成的文件
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/

clean-db: ## 清理数据库文件
	rm -f data/*.db

clean-all: clean clean-db ## 清理所有生成的文件

# 构建和部署
build: ## 构建Docker镜像
	docker build -t hospital-scanner .

docker-run: ## 运行Docker容器
	docker run -p 8000:8000 hospital-scanner

docker-compose-up: ## 启动Docker Compose
	docker-compose up -d

docker-compose-down: ## 停止Docker Compose
	docker-compose down

# 文档
docs: ## 生成API文档
	mkdocs build

docs-serve: ## 启动文档服务器
	mkdocs serve

docs-deploy: ## 部署文档
	mkdocs gh-deploy

# 性能测试
perf-test: ## 运行性能测试
	locust -f tests/performance/test_load.py --host=http://localhost:8000

# 安全检查
security-check: ## 运行安全检查
	bandit -r . -x tests/

dependency-check: ## 检查依赖安全
	safety check

# 备份和恢复
backup: ## 备份数据库
	tar -czf backup/hospital_scanner_$(shell date +%Y%m%d_%H%M%S).tar.gz data/

# 开发工具
shell: ## 启动Python交互式shell
	python -c "from main import app; import asyncio; exec('import uvloop; uvloop.install()'); print('Hospital Scanner Shell Ready')"

debug: ## 启动调试模式
	python -m pdb main.py

profile: ## 代码性能分析
	python -m cProfile -o profile_output.prof main.py && snakeviz profile_output.prof

# 版本和发布
version: ## 显示版本信息
	@echo "Hospital Scanner v1.0.0"

tag: ## 创建Git标签
	git tag -a v1.0.0 -m "Release v1.0.0"
	git push origin v1.0.0

# 统计
stats: ## 显示项目统计
	@echo "项目文件统计:"
	@find . -name "*.py" | wc -l | xargs echo "Python文件数量:"
	@find . -name "*.md" | wc -l | xargs echo "Markdown文件数量:"
	@find . -name "*.txt" | wc -l | xargs echo "文本文件数量:"
	@wc -l *.py | tail -1 | xargs echo "总代码行数:"

# 健康检查
health: ## 检查服务健康状态
	curl -f http://localhost:8000/health || exit 1

health-detailed: ## 检查详细健康状态
	curl http://localhost:8000/health/detailed | python -m json.tool

# API测试
api-test: ## 运行API测试
	curl -X POST http://localhost:8000/scan \
		-H "Content-Type: application/json" \
		-d '{"hospital_name": "测试医院", "query": "获取层级结构"}' | python -m json.tool