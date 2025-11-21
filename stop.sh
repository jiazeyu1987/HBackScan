#!/bin/bash
# 医院层级扫查系统 - 服务停止脚本

set -e

# 配置变量
DOCKER_COMPOSE_FILE="docker-compose.yml"
DOCKER_COMPOSE_PROD_FILE="docker-compose.prod.yml"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

# 停止开发环境服务
stop_dev_services() {
    log_info "停止开发环境服务..."
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down
        log_info "开发环境服务已停止"
    else
        log_warn "开发环境配置文件不存在"
    fi
}

# 停止生产环境服务
stop_prod_services() {
    log_info "停止生产环境服务..."
    if [ -f "$DOCKER_COMPOSE_PROD_FILE" ]; then
        docker-compose -f "$DOCKER_COMPOSE_PROD_FILE" down
        log_info "生产环境服务已停止"
    else
        log_warn "生产环境配置文件不存在"
    fi
}

# 清理资源
cleanup_resources() {
    log_info "清理Docker资源..."
    
    # 清理未使用的容器
    docker container prune -f
    
    # 清理未使用的网络
    docker network prune -f
    
    # 清理未使用的镜像（可选）
    read -p "是否清理未使用的Docker镜像? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker image prune -f
        log_info "镜像清理完成"
    fi
    
    # 清理悬挂的构建缓存
    docker builder prune -f
    log_info "构建缓存清理完成"
}

# 显示状态
show_status() {
    log_info "Docker容器状态:"
    docker ps -a --filter "name=hospital-scanner" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
}

# 强制停止
force_stop() {
    log_warn "强制停止所有相关容器..."
    docker kill $(docker ps -q --filter "name=hospital-scanner") 2>/dev/null || true
    docker rm $(docker ps -aq --filter "name=hospital-scanner") 2>/dev/null || true
    log_info "强制停止完成"
}

# 显示帮助
show_help() {
    echo "医院层级扫查系统停止脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -d, --dev           仅停止开发环境服务"
    echo "  -p, --prod          仅停止生产环境服务"
    echo "  -a, --all           停止所有环境服务"
    echo "  -f, --force         强制停止"
    echo "  -c, --cleanup       停止并清理资源"
    echo "  -s, --status        显示容器状态"
    echo ""
}

# 主函数
main() {
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dev)
            stop_dev_services
            ;;
        -p|--prod)
            stop_prod_services
            ;;
        -a|--all)
            stop_dev_services
            stop_prod_services
            ;;
        -f|--force)
            force_stop
            ;;
        -c|--cleanup)
            stop_dev_services
            stop_prod_services
            cleanup_resources
            ;;
        -s|--status)
            show_status
            ;;
        "")
            # 默认停止开发环境
            stop_dev_services
            log_info "使用 -a 选项停止所有服务，-c 选项停止并清理"
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