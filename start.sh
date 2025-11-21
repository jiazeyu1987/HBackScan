#!/bin/bash
# 医院层级扫查系统 - 服务启动脚本

set -e

# 配置变量
PROJECT_NAME="hospital-scanner"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

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

# 检查依赖
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi
}

# 检查环境文件
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_warn "环境文件 $ENV_FILE 不存在，创建模板..."
        cat > "$ENV_FILE" << EOF
# 开发环境配置
APP_PORT=8000
DASHSCOPE_API_KEY=
HTTP_PROXY=
HTTPS_PROXY=
EOF
        log_warn "请编辑 $ENV_FILE 文件配置API密钥"
    fi
}

# 启动服务
start_services() {
    log_info "启动 $PROJECT_NAME 服务..."
    
    # 创建必要的目录
    mkdir -p logs data uploads
    
    # 构建并启动
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build
    
    log_info "等待服务启动..."
    sleep 5
    
    # 健康检查
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_info "服务启动成功！"
        log_info "服务地址: http://localhost:8000"
        log_info "API文档: http://localhost:8000/docs"
    else
        log_error "服务启动失败，请检查日志"
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs
        exit 1
    fi
}

# 显示状态
show_status() {
    log_info "服务状态:"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
}

# 显示日志
show_logs() {
    log_info "显示服务日志:"
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f
}

# 显示帮助
show_help() {
    echo "医院层级扫查系统启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -s, --status        显示服务状态"
    echo "  -l, --logs          显示服务日志"
    echo "  --no-build          启动时不重新构建镜像"
    echo ""
}

# 主函数
main() {
    local build_flag="--build"
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -s|--status)
                check_dependencies
                show_status
                exit 0
                ;;
            -l|--logs)
                check_dependencies
                show_logs
                exit 0
                ;;
            --no-build)
                build_flag=""
                shift
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 执行启动流程
    check_dependencies
    check_env_file
    start_services
}

# 执行主函数
main "$@"