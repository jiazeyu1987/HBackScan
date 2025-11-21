# Makefile - 测试和开发命令

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
RED = \033[31m
GREEN = \033[32m
YELLOW = \033[33m
BLUE = \033[34m
NC = \033[0m # No Color

# 项目配置
PYTHON = python3
PIP = pip3
PYTEST = pytest
COVERAGE = coverage
MYPY = mypy
FLAKE8 = flake8
BLACK = black
ISORT = isort

# 测试配置
TEST_DIR = tests
COVERAGE_DIR = htmlcov
REPORT_DIR = reports
ACCEPTANCE_REPORT_DIR = reports/acceptance

.PHONY: help
help: ## 显示帮助信息
	@echo "$(BLUE)可用命令:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## 安装项目依赖
	@echo "$(GREEN)安装依赖...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

.PHONY: install-dev
install-dev: ## 安装开发依赖
	@echo "$(GREEN)安装开发依赖...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-cov pytest-xdist pytest-html pytest-timeout
	$(PIP) install black isort flake8 mypy coverage
	$(PIP) install httpx aioresponses

.PHONY: test
test: ## 运行所有测试
	@echo "$(GREEN)运行所有测试...$(NC)"
	@mkdir -p $(REPORT_DIR)
	$(PYTEST) $(TEST_DIR) -v \
		--html=$(REPORT_DIR)/report.html \
		--self-contained-html \
		--tb=short \
		--cov=. \
		--cov-report=html:$(COVERAGE_DIR) \
		--cov-report=term-missing \
		--cov-report=xml:$(COVERAGE_DIR)/coverage.xml \
		--junit-xml=$(REPORT_DIR)/junit.xml \
		--capture=no

.PHONY: test-unit
test-unit: ## 只运行单元测试
	@echo "$(GREEN)运行单元测试...$(NC)"
	$(PYTEST) $(TEST_DIR) -v -m "unit or not integration" --cov=. --cov-report=term-missing

.PHONY: test-integration
test-integration: ## 只运行集成测试
	@echo "$(GREEN)运行集成测试...$(NC)"
	$(PYTEST) $(TEST_DIR) -v -m "integration" --cov=. --cov-report=term-missing

.PHONY: test-fast
test-fast: ## 运行快速测试
	@echo "$(GREEN)运行快速测试...$(NC)"
	$(PYTEST) $(TEST_DIR) -v -m "fast" -x --disable-warnings

.PHONY: test-slow
test-slow: ## 运行慢速测试
	@echo "$(GREEN)运行慢速测试...$(NC)"
	$(PYTEST) $(TEST_DIR) -v -m "slow" --timeout=300

.PHONY: test-smoke
test-smoke: ## 运行冒烟测试
	@echo "$(GREEN)运行冒烟测试...$(NC)"
	$(PYTEST) $(TEST_DIR) -v -m "smoke" -x

.PHONY: test-acceptance
test-acceptance: ## 运行验收测试
	@echo "$(GREEN)运行验收测试...$(NC)"
	@mkdir -p $(ACCEPTANCE_REPORT_DIR)
	$(PYTEST) $(TEST_DIR) -v -m "acceptance" \
		--html=$(ACCEPTANCE_REPORT_DIR)/acceptance_test_report.html \
		--self-contained-html \
		--junit-xml=$(ACCEPTANCE_REPORT_DIR)/junit.xml \
		--cov=. \
		--cov-report=html:$(COVERAGE_DIR)/acceptance \
		--cov-report=term-missing \
		--cov-report=xml:$(ACCEPTANCE_REPORT_DIR)/coverage.xml \
		--cov-fail-under=75 \
		--tb=short \
		--capture=no \
		--timeout=300

.PHONY: test-acceptance-fast
test-acceptance-fast: ## 运行快速验收测试（跳过慢速测试）
	@echo "$(GREEN)运行快速验收测试...$(NC)"
	@mkdir -p $(ACCEPTANCE_REPORT_DIR)
	$(PYTEST) $(TEST_DIR) -v -m "acceptance and fast" \
		--html=$(ACCEPTANCE_REPORT_DIR)/acceptance_fast_report.html \
		--self-contained-html \
		--cov=. \
		--cov-report=term-missing \
		--tb=short \
		--capture=no \
		--timeout=60

.PHONY: test-acceptance-performance
test-acceptance-performance: ## 运行验收性能测试
	@echo "$(GREEN)运行验收性能测试...$(NC)"
	@mkdir -p $(ACCEPTANCE_REPORT_DIR)
	$(PYTEST) $(TEST_DIR) -v -m "acceptance and performance" \
		--html=$(ACCEPTANCE_REPORT_DIR)/acceptance_performance_report.html \
		--self-contained-html \
		--tb=short \
		--capture=no \
		--timeout=180

.PHONY: test-acceptance-workflow
test-acceptance-workflow: ## 运行验收工作流测试
	@echo "$(GREEN)运行验收工作流测试...$(NC)"
	@mkdir -p $(ACCEPTANCE_REPORT_DIR)
	$(PYTEST) $(TEST_DIR)/test_acceptance.py::TestAcceptanceScenarios::test_complete_refresh_workflow \
		-v \
		--html=$(ACCEPTANCE_REPORT_DIR)/workflow_report.html \
		--self-contained-html \
		--tb=long \
		--capture=no \
		--timeout=300

.PHONY: test-acceptance-report
test-acceptance-report: ## 生成验收测试报告
	@echo "$(GREEN)生成验收测试详细报告...$(NC)"
	@mkdir -p $(ACCEPTANCE_REPORT_DIR)
	$(PYTEST) $(TEST_DIR) -v -m "acceptance" \
		--html=$(ACCEPTANCE_REPORT_DIR)/detailed_acceptance_report.html \
		--self-contained-html \
		--junit-xml=$(ACCEPTANCE_REPORT_DIR)/junit_detailed.xml \
		--cov=. \
		--cov-report=html:$(COVERAGE_DIR)/acceptance_detailed \
		--cov-report=xml:$(ACCEPTANCE_REPORT_DIR)/coverage_detailed.xml \
		--report-log=$(ACCEPTANCE_REPORT_DIR)/pytest_detailed.log \
		--capture=no \
		--timeout=300

.PHONY: test-acceptance-coverage
test-acceptance-coverage: ## 生成验收测试覆盖率报告
	@echo "$(GREEN)生成验收测试覆盖率报告...$(NC)"
	@mkdir -p $(ACCEPTANCE_REPORT_DIR)
	$(COVERAGE) run -m pytest $(TEST_DIR) -m "acceptance"
	$(COVERAGE) report
	$(COVERAGE) html -d $(COVERAGE_DIR)/acceptance_coverage
	@echo "$(BLUE)验收测试覆盖率报告已生成: $(COVERAGE_DIR)/acceptance_coverage/index.html$(NC)"

.PHONY: test-acceptance-watch
test-acceptance-watch: ## 监视文件变化并自动运行验收测试
	@echo "$(GREEN)监视文件变化并运行验收测试...$(NC)"
	@which pytest-watch > /dev/null 2>&1 || (echo "$(RED)请安装 pytest-watch: pip install pytest-watch$(NC)" && exit 1)
	ptw $(TEST_DIR) -- -v -m "acceptance"

.PHONY: test-acceptance-parallel
test-acceptance-parallel: ## 并行运行验收测试
	@echo "$(GREEN)并行运行验收测试...$(NC)"
	@which pytest-xdist > /dev/null 2>&1 || (echo "$(RED)请安装 pytest-xdist: pip install pytest-xdist$(NC)" && exit 1)
	$(PYTEST) $(TEST_DIR) -n auto -m "acceptance" \
		--cov=. \
		--cov-report=term-missing \
		--tb=short \
		--timeout=300

.PHONY: test-acceptance-debug
test-acceptance-debug: ## 调试模式运行验收测试
	@echo "$(GREEN)调试模式运行验收测试...$(NC)"
	$(PYTEST) $(TEST_DIR) -v -m "acceptance" -s --capture=no --tb=long

.PHONY: test-acceptance-failed
test-acceptance-failed: ## 只运行失败的验收测试
	@echo "$(GREEN)运行失败的验收测试...$(NC)"
	$(PYTEST) $(TEST_DIR) -v -m "acceptance" --lf

.PHONY: test-acceptance-specific
test-acceptance-specific: ## 运行特定验收测试 (用法: make test-acceptance-specific NAME=test_complete_refresh_workflow)
	@echo "$(GREEN)运行特定验收测试: $(NAME)$(NC)"
	$(PYTEST) $(TEST_DIR) -k "$(NAME)" -v \
		--html=$(ACCEPTANCE_REPORT_DIR)/specific_test_report.html \
		--self-contained-html \
		--capture=no

.PHONY: test-acceptance-e2e
test-acceptance-e2e: ## 运行端到端验收测试
	@echo "$(GREEN)运行端到端验收测试...$(NC)"
	@mkdir -p $(ACCEPTANCE_REPORT_DIR)
	$(PYTEST) $(TEST_DIR) -v -m "acceptance or e2e" \
		--html=$(ACCEPTANCE_REPORT_DIR)/e2e_acceptance_report.html \
		--self-contained-html \
		--tb=short \
		--capture=no \
		--timeout=600

.PHONY: test-watch
test-watch: ## 监视文件变化并自动运行测试
	@echo "$(GREEN)监视文件变化...$(NC)"
	@which pytest-watch > /dev/null 2>&1 || (echo "$(RED)请安装 pytest-watch: pip install pytest-watch$(NC)" && exit 1)
	ptw $(TEST_DIR) -- -v

.PHONY: test-parallel
test-parallel: ## 并行运行测试
	@echo "$(GREEN)并行运行测试...$(NC)"
	@which pytest-xdist > /dev/null 2>&1 || (echo "$(RED)请安装 pytest-xdist: pip install pytest-xdist$(NC)" && exit 1)
	$(PYTEST) $(TEST_DIR) -n auto --cov=. --cov-report=term-missing

.PHONY: test-coverage
test-coverage: ## 生成覆盖率报告
	@echo "$(GREEN)生成覆盖率报告...$(NC)"
	@mkdir -p $(COVERAGE_DIR)
	$(COVERAGE) run -m pytest $(TEST_DIR)
	$(COVERAGE) report
	$(COVERAGE) html
	@echo "$(BLUE)覆盖率报告已生成: $(COVERAGE_DIR)/index.html$(NC)"

.PHONY: test-report
test-report: ## 生成详细测试报告
	@echo "$(GREEN)生成详细测试报告...$(NC)"
	@mkdir -p $(REPORT_DIR)
	$(PYTEST) $(TEST_DIR) \
		--html=$(REPORT_DIR)/detailed-report.html \
		--self-contained-html \
		--cov=. \
		--cov-report=html:$(COVERAGE_DIR) \
		--junit-xml=$(REPORT_DIR)/junit.xml \
		--report-log=$(REPORT_DIR)/pytest.log

.PHONY: test-debug
test-debug: ## 调试模式运行测试（显示所有输出）
	@echo "$(GREEN)调试模式运行测试...$(NC)"
	$(PYTEST) $(TEST_DIR) -v -s --capture=no --tb=long

.PHONY: test-failed
test-failed: ## 只运行失败的测试
	@echo "$(GREEN)运行失败的测试...$(NC)"
	$(PYTEST) $(TEST_DIR) -v --lf

.PHONY: test-mark
test-mark: ## 按标记运行测试 (用法: make test-mark MARK=unit)
	@echo "$(GREEN)按标记运行测试: $(MARK)$(NC)"
	$(PYTEST) $(TEST_DIR) -v -m "$(MARK)"

.PHONY: test-specific
test-specific: ## 运行特定测试文件 (用法: make test-specific FILE=test_main.py)
	@echo "$(GREEN)运行特定测试文件: $(FILE)$(NC)"
	$(PYTEST) $(TEST_DIR)/$(FILE) -v

# 代码质量检查
.PHONY: lint
lint: ## 运行代码质量检查
	@echo "$(GREEN)运行代码质量检查...$(NC)"
	$(FLAKE8) . --count --select=E9,F63,F7,F82 --show-source --statistics
	$(FLAKE8) . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

.PHONY: format
format: ## 格式化代码
	@echo "$(GREEN)格式化代码...$(NC)"
	$(BLACK) . --line-length=127
	$(ISORT) . --profile=black

.PHONY: format-check
format-check: ## 检查代码格式
	@echo "$(GREEN)检查代码格式...$(NC)"
	$(BLACK) . --line-length=127 --check
	$(ISORT) . --profile=black --check-only

.PHONY: type-check
type-check: ## 运行类型检查
	@echo "$(GREEN)运行类型检查...$(NC)"
	$(MYPY) . --ignore-missing-imports

.PHONY: security
security: ## 运行安全检查
	@echo "$(GREEN)运行安全检查...$(NC)"
	@which bandit > /dev/null 2>&1 || (echo "$(RED)请安装 bandit: pip install bandit$(NC)" && exit 1)
	bandit -r . -f json -o $(REPORT_DIR)/security-report.json

# 数据库相关
.PHONY: db-init
db-init: ## 初始化测试数据库
	@echo "$(GREEN)初始化测试数据库...$(NC)"
	$(PYTHON) -c "from tests.helpers import init_test_db; init_test_db()"

.PHONY: db-reset
db-reset: ## 重置测试数据库
	@echo "$(YELLOW)重置测试数据库...$(NC)"
	rm -f test_*.db
	$(MAKE) db-init

.PHONY: db-migrate
db-migrate: ## 运行数据库迁移
	@echo "$(GREEN)运行数据库迁移...$(NC)"
	$(PYTHON) -c "from tests.helpers import migrate_test_db; migrate_test_db()"

# 清理
.PHONY: clean
clean: ## 清理生成的文件
	@echo "$(GREEN)清理生成的文件...$(NC)"
	rm -rf $(COVERAGE_DIR)/
	rm -rf $(REPORT_DIR)/
	rm -rf htmlcov/
	rm -rf reports/
	rm -f .coverage
	rm -f *.db
	rm -f *.log
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

.PHONY: clean-all
clean-all: clean ## 清理所有生成的文件和缓存
	@echo "$(GREEN)清理所有文件...$(NC)"
	rm -rf .pytest_cache/
	rm -rf .tox/
	rm -rf .mypy_cache/
	rm -rf node_modules/ 2>/dev/null || true
	rm -rf build/ 2>/dev/null || true
	rm -rf dist/ 2>/dev/null || true
	rm -rf *.egg-info/ 2>/dev/null || true

# 性能测试
.PHONY: benchmark
benchmark: ## 运行性能基准测试
	@echo "$(GREEN)运行性能基准测试...$(NC)"
	$(PYTEST) $(TEST_DIR) -m "performance" --benchmark-only

# 并发测试
.PHONY: load-test
load-test: ## 运行负载测试
	@echo "$(GREEN)运行负载测试...$(NC)"
	$(PYTEST) $(TEST_DIR) -m "load_test" --tb=short

# 持续集成
.PHONY: ci
ci: clean lint type-check test-unit test-integration test-coverage ## CI完整流程
	@echo "$(GREEN)CI流程完成!$(NC)"

# 开发环境设置
.PHONY: dev-setup
dev-setup: install-dev db-init ## 设置开发环境
	@echo "$(GREEN)开发环境设置完成!$(NC)"
	@echo "$(BLUE)现在可以运行 'make test' 来执行测试$(NC)"

# 帮助和文档
.PHONY: docs
docs: ## 生成文档
	@echo "$(GREEN)生成文档...$(NC)"
	@which sphinx-build > /dev/null 2>&1 || (echo "$(RED)请安装 sphinx: pip install sphinx$(NC)" && exit 1)
	sphinx-build -b html docs/ docs/_build/html

.PHONY: validate
validate: ## 验证项目配置
	@echo "$(GREEN)验证项目配置...$(NC)"
	@echo "Python版本: $(shell $(PYTHON) --version)"
	@echo "Pytest版本: $(shell $(PYTEST) --version)"
	@echo "项目结构检查..."
	@test -f "main.py" || echo "$(RED)缺少 main.py$(NC)"
	@test -f "requirements.txt" || echo "$(RED)缺少 requirements.txt$(NC)"
	@test -d "$(TEST_DIR)" || echo "$(RED)缺少 tests 目录$(NC)"
	@test -f "$(TEST_DIR)/conftest.py" || echo "$(RED)缺少 conftest.py$(NC)"

# 快速开始
.PHONY: quickstart
quickstart: dev-setup test-smoke ## 快速开始（设置环境并运行冒烟测试）
	@echo "$(GREEN)快速开始完成!$(NC)"

# 版本信息
.PHONY: version
version: ## 显示版本信息
	@echo "$(BLUE)项目版本信息:$(NC)"
	@$(PYTHON) -c "import main; print('主程序版本:', getattr(main, '__version__', '1.0.0'))"
	@echo "Python版本: $(shell $(PYTHON) --version)"
	@echo "Pytest版本: $(shell $(PYTEST) --version)"

# ================================
# 部署相关命令
# ================================

.PHONY: deploy
deploy: ## 完整部署（开发环境）
	@echo "$(GREEN)开始部署开发环境...$(NC)"
	@./deploy.sh

.PHONY: deploy-prod
deploy-prod: ## 完整部署（生产环境）
	@echo "$(GREEN)开始部署生产环境...$(NC)"
	@./deploy.sh --full-deploy

.PHONY: start
start: ## 启动开发服务
	@echo "$(GREEN)启动开发服务...$(NC)"
	@./start.sh

.PHONY: start-prod
start-prod: ## 启动生产服务
	@echo "$(GREEN)启动生产服务...$(NC)"
	@docker-compose -f docker-compose.prod.yml up -d

.PHONY: stop
stop: ## 停止开发服务
	@echo "$(GREEN)停止开发服务...$(NC)"
	@./stop.sh

.PHONY: stop-prod
stop-prod: ## 停止生产服务
	@echo "$(GREEN)停止生产服务...$(NC)"
	@./stop.sh --prod

.PHONY: restart
restart: ## 重启服务
	@echo "$(GREEN)重启服务...$(NC)"
	@./stop.sh && sleep 5 && ./start.sh

.PHONY: restart-prod
restart-prod: ## 重启生产服务
	@echo "$(GREEN)重启生产服务...$(NC)"
	@docker-compose -f docker-compose.prod.yml restart

.PHONY: logs
logs: ## 查看服务日志
	@echo "$(GREEN)查看服务日志...$(NC)"
	@docker-compose logs -f

.PHONY: logs-prod
logs-prod: ## 查看生产服务日志
	@echo "$(GREEN)查看生产服务日志...$(NC)"
	@docker-compose -f docker-compose.prod.yml logs -f

.PHONY: backup
backup: ## 备份数据
	@echo "$(GREEN)备份数据...$(NC)"
	@./backup.sh --all

.PHONY: backup-compressed
backup-compressed: ## 备份数据并压缩
	@echo "$(GREEN)备份数据并压缩...$(NC)"
	@./backup.sh --all --compress

.PHONY: status
status: ## 查看服务状态
	@echo "$(GREEN)查看服务状态...$(NC)"
	@docker-compose ps

.PHONY: status-prod
status-prod: ## 查看生产服务状态
	@echo "$(GREEN)查看生产服务状态...$(NC)"
	@docker-compose -f docker-compose.prod.yml ps

.PHONY: health
health: ## 健康检查
	@echo "$(GREEN)执行健康检查...$(NC)"
	@curl -f http://localhost:8000/health && echo "✅ 健康检查通过" || echo "❌ 健康检查失败"

.PHONY: health-prod
health-prod: ## 生产环境健康检查
	@echo "$(GREEN)执行生产环境健康检查...$(NC)"
	@docker-compose -f docker-compose.prod.yml ps

.PHONY: shell
shell: ## 进入应用容器
	@echo "$(GREEN)进入应用容器...$(NC)"
	@docker-compose exec hospital-scanner bash || docker exec -it hospital-scanner bash

.PHONY: shell-prod
shell-prod: ## 进入生产应用容器
	@echo "$(GREEN)进入生产应用容器...$(NC)"
	@docker-compose -f docker-compose.prod.yml exec hospital-scanner bash

.PHONY: db-shell
db-shell: ## 进入数据库容器
	@echo "$(GREEN)进入数据库容器...$(NC)"
	@docker-compose exec redis redis-cli || echo "Redis未运行"

.PHONY: build
build: ## 构建Docker镜像
	@echo "$(GREEN)构建Docker镜像...$(NC)"
	@docker-compose build

.PHONY: build-prod
build-prod: ## 构建生产Docker镜像
	@echo "$(GREEN)构建生产Docker镜像...$(NC)"
	@docker-compose -f docker-compose.prod.yml build --no-cache

.PHONY: clean-containers
clean-containers: ## 清理容器
	@echo "$(GREEN)清理容器...$(NC)"
	@docker-compose down --remove-orphans

.PHONY: clean-containers-prod
clean-containers-prod: ## 清理生产容器
	@echo "$(GREEN)清理生产容器...$(NC)"
	@docker-compose -f docker-compose.prod.yml down --remove-orphans

.PHONY: clean-images
clean-images: ## 清理镜像
	@echo "$(GREEN)清理镜像...$(NC)"
	@docker image prune -f

.PHONY: clean-volumes
clean-volumes: ## 清理数据卷
	@echo "$(YELLOW)警告：这将删除所有数据！$(NC)"
	@read -p "确认删除所有数据卷？ [y/N]: " confirm && [ "$$confirm" = "y" ]
	@docker-compose down -v
	@docker volume prune -f

.PHONY: install-system
install-system: ## 系统安装
	@echo "$(GREEN)系统安装...$(NC)"
	@sudo ./install.sh

.PHONY: uninstall-system
uninstall-system: ## 系统卸载
	@echo "$(YELLOW)卸载系统服务...$(NC)"
	@sudo ./install.sh --uninstall

.PHONY: config-check
config-check: ## 检查配置
	@echo "$(GREEN)检查配置...$(NC)"
	@echo "检查Docker Compose配置..."
	@docker-compose config
	@echo ""
	@echo "检查生产Docker Compose配置..."
	@docker-compose -f docker-compose.prod.yml config || echo "生产配置未找到"

.PHONY: env-check
env-check: ## 检查环境变量
	@echo "$(GREEN)检查环境变量...$(NC)"
	@echo "DASHSCOPE_API_KEY: $(if $(DASHSCOPE_API_KEY),已设置,未设置)"
	@echo "HTTP_PROXY: $(if $(HTTP_PROXY),$(HTTP_PROXY),未设置)"
	@echo "HTTPS_PROXY: $(if $(HTTPS_PROXY),$(HTTPS_PROXY),未设置)"

.PHONY: system-info
system-info: ## 显示系统信息
	@echo "$(GREEN)系统信息:$(NC)"
	@echo "Docker版本: $(shell docker --version 2>/dev/null || echo '未安装')"
	@echo "Docker Compose版本: $(shell docker-compose --version 2>/dev/null || echo '未安装')"
	@echo "操作系统: $(shell uname -s)"
	@echo "内核版本: $(shell uname -r)"
	@echo "磁盘空间: $(shell df -h / | awk 'NR==2 {print $$4}')"
	@echo "内存使用: $(shell free -h | awk 'NR==2 {print $$3 "/" $$2}')"

.PHONY: monitor
monitor: ## 实时监控
	@echo "$(GREEN)启动实时监控...$(NC)"
	@./docs/scripts/monitor.sh || echo "监控脚本未找到"

.PHONY: performance-test
performance-test: ## 运行性能测试
	@echo "$(GREEN)运行性能测试...$(NC)"
	@which ab > /dev/null 2>&1 || (echo "$(RED)请安装 apache2-utils: sudo apt install apache2-utils$(NC)" && exit 1)
	@echo "测试健康检查端点..."
	@ab -n 100 -c 10 http://localhost:8000/health

.PHONY: troubleshoot
troubleshoot: ## 故障排除工具
	@echo "$(GREEN)运行故障排除...$(NC)"
	@./docs/scripts/diagnose.sh || echo "诊断脚本未找到"

# 快速部署命令
.PHONY: quick-deploy
quick-deploy: stop build start health ## 快速部署（停止->构建->启动->检查）
	@echo "$(GREEN)快速部署完成！$(NC)"

.PHONY: quick-deploy-prod
quick-deploy-prod: stop-prod build-prod start-prod health-prod ## 快速部署生产环境
	@echo "$(GREEN)生产环境快速部署完成！$(NC)"

# 完整环境清理和重新部署
.PHONY: redeploy
redeploy: clean-all clean-containers clean-images install build start ## 重新部署（完全重建）
	@echo "$(GREEN)重新部署完成！$(NC)"

.PHONY: redeploy-prod
redeploy-prod: clean-containers-prod clean-images install-system build-prod start-prod ## 重新部署生产环境
	@echo "$(GREEN)生产环境重新部署完成！$(NC)"
