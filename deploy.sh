#!/bin/bash
# 医院层级扫查系统 - 自动化部署脚本

set -e

# 配置变量
PROJECT_NAME="hospital-scanner"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查部署依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi
    
    log_info "依赖检查完成"
}

# 检查环境文件
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_warn "环境文件 $ENV_FILE 不存在，创建模板..."
        cat > "$ENV_FILE" << EOF
# 生产环境配置
APP_PORT=8000
REDIS_PORT=6379
WORKERS=4
LOG_LEVEL=INFO

# API配置
DASHSCOPE_API_KEY=your_api_key_here
HTTP_PROXY=
HTTPS_PROXY=

# 数据库配置
DATABASE_URL=sqlite:///./data/hospitals.db

# 安全配置
SECRET_KEY=your_secret_key_here
EOF
        log_warn "请编辑 $ENV_FILE 文件配置相关参数"
        read -p "按Enter键继续..."
    fi
}

# 创建备份
create_backup() {
    log_info "创建应用备份..."
    mkdir -p "$BACKUP_DIR"
    
    # 备份数据
    if [ -d "./data" ]; then
        cp -r ./data "$BACKUP_DIR/"
        log_info "数据目录已备份到 $BACKUP_DIR/data"
    fi
    
    # 备份日志
    if [ -d "./logs" ]; then
        cp -r ./logs "$BACKUP_DIR/"
        log_info "日志目录已备份到 $BACKUP_DIR/logs"
    fi
    
    # 备份配置
    cp .env.prod "$BACKUP_DIR/" 2>/dev/null || true
    cp docker-compose.prod.yml "$BACKUP_DIR/" 2>/dev/null || true
    
    log_info "备份完成: $BACKUP_DIR"
}

# 停止服务
stop_services() {
    log_info "停止现有服务..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans
}

# 清理旧镜像
cleanup_images() {
    log_info "清理旧的Docker镜像..."
    docker image prune -f
}

# 构建和部署
deploy() {
    log_info "开始部署应用..."
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
    
    # 启动服务
    log_info "启动服务..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 健康检查
    health_check
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_info "服务健康检查通过"
            return 0
        fi
        
        log_warn "健康检查失败，重试中... ($attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    log_error "健康检查失败，服务可能未正常启动"
    show_logs
    exit 1
}

# 显示日志
show_logs() {
    log_info "显示最近的日志..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=50
}

# 清理
cleanup() {
    log_info "清理临时文件..."
    docker system prune -f
}

# 显示帮助
show_help() {
    echo "医院层级扫查系统部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -b, --backup-only   仅创建备份"
    echo "  -s, --stop          仅停止服务"
    echo "  -l, --logs          显示服务日志"
    echo "  --full-deploy       完整部署流程"
    echo ""
}

# 主函数
main() {
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -b|--backup-only)
            check_dependencies
            create_backup
            exit 0
            ;;
        -s|--stop)
            stop_services
            exit 0
            ;;
        -l|--logs)
            show_logs
            exit 0
            ;;
        --full-deploy)
            check_dependencies
            check_env_file
            create_backup
            stop_services
            cleanup_images
            deploy
            cleanup
            log_info "部署完成！"
            ;;
        "")
            # 默认完整部署
            check_dependencies
            check_env_file
            create_backup
            stop_services
            cleanup_images
            deploy
            cleanup
            log_info "部署完成！"
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"