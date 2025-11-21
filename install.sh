#!/bin/bash
# 医院层级扫查系统 - 系统安装脚本

set -e

# 配置变量
APP_NAME="hospital-scanner"
APP_DIR="/opt/hospital-scanner"
SERVICE_FILE="/etc/systemd/system/hospital-scanner.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查root权限
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 检查系统要求
check_system() {
    log_step "检查系统要求..."
    
    # 检查操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        log_info "操作系统: $PRETTY_NAME"
    else
        log_warn "无法检测操作系统类型"
    fi
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装Docker"
        log_info "安装Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查磁盘空间（至少需要2GB）
    available_space=$(df /opt | awk 'NR==2 {print $4}')
    required_space=2097152  # 2GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        log_error "磁盘空间不足，至少需要2GB可用空间"
        exit 1
    fi
    
    log_info "系统要求检查通过"
}

# 安装依赖
install_dependencies() {
    log_step "安装系统依赖..."
    
    # 更新包列表
    apt-get update -qq
    
    # 安装必要工具
    apt-get install -y curl wget git ufw
    
    log_info "依赖安装完成"
}

# 创建应用目录
create_app_dir() {
    log_step "创建应用目录..."
    
    # 创建应用目录
    mkdir -p "$APP_DIR"
    
    # 复制应用文件
    cp -r "$SCRIPT_DIR"/* "$APP_DIR/"
    
    # 设置权限
    chown -R root:root "$APP_DIR"
    chmod +x "$APP_DIR"/*.sh
    
    log_info "应用目录创建完成: $APP_DIR"
}

# 创建系统服务
create_systemd_service() {
    log_step "创建systemd服务..."
    
    # 复制服务文件
    cp "$SCRIPT_DIR/hospital-scanner.service" "$SERVICE_FILE"
    
    # 重新加载systemd
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable hospital-scanner
    
    log_info "systemd服务创建完成"
}

# 配置防火墙
configure_firewall() {
    log_step "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        # 允许HTTP和HTTPS
        ufw allow 80/tcp
        ufw allow 443/tcp
        
        # 允许SSH（如果未开启）
        ufw allow ssh
        
        log_info "防火墙规则已添加"
    else
        log_warn "UFW未安装，跳过防火墙配置"
    fi
}

# 创建配置目录
create_config_dir() {
    log_step "创建配置目录..."
    
    mkdir -p "$APP_DIR"/{config,logs,data,uploads,backups}
    
    # 设置目录权限
    chown -R root:root "$APP_DIR"/{logs,data,uploads,backups}
    chmod 755 "$APP_DIR"/{logs,data,uploads,backups}
    
    log_info "配置目录创建完成"
}

# 创建环境配置
create_env_config() {
    log_step "创建环境配置..."
    
    if [ ! -f "$APP_DIR/.env.prod" ]; then
        cat > "$APP_DIR/.env.prod" << EOF
# 生产环境配置
APP_PORT=8000
REDIS_PORT=6379
WORKERS=4
LOG_LEVEL=INFO

# API配置（需要配置）
DASHSCOPE_API_KEY=your_api_key_here
HTTP_PROXY=
HTTPS_PROXY=

# 安全配置
SECRET_KEY=$(openssl rand -base64 32)

# 数据库配置
DATABASE_URL=sqlite:///$APP_DIR/data/hospitals.db
EOF
        
        log_warn "请编辑 $APP_DIR/.env.prod 文件配置API密钥"
    fi
}

# 测试安装
test_installation() {
    log_step "测试安装..."
    
    # 启动服务
    systemctl start hospital-scanner
    
    # 等待服务启动
    sleep 10
    
    # 检查服务状态
    if systemctl is-active --quiet hospital-scanner; then
        log_info "服务启动成功"
        
        # 健康检查
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_info "健康检查通过"
        else
            log_warn "健康检查失败，请检查服务日志"
        fi
    else
        log_error "服务启动失败"
        systemctl status hospital-scanner
        exit 1
    fi
}

# 显示安装信息
show_install_info() {
    echo ""
    echo "============================================"
    echo "  医院层级扫查系统安装完成！"
    echo "============================================"
    echo ""
    echo "应用目录: $APP_DIR"
    echo "服务状态: systemctl status hospital-scanner"
    echo "服务管理:"
    echo "  启动: systemctl start hospital-scanner"
    echo "  停止: systemctl stop hospital-scanner"
    echo "  重启: systemctl restart hospital-scanner"
    echo "  查看日志: journalctl -u hospital-scanner -f"
    echo ""
    echo "访问地址:"
    echo "  本地: http://localhost:8000"
    echo "  API文档: http://localhost:8000/docs"
    echo ""
    echo "配置文件: $APP_DIR/.env.prod"
    echo ""
    log_warn "请确保已配置API密钥和环境变量"
    echo "============================================"
}

# 卸载函数
uninstall() {
    log_step "卸载医院层级扫查系统..."
    
    # 停止并禁用服务
    systemctl stop hospital-scanner 2>/dev/null || true
    systemctl disable hospital-scanner 2>/dev/null || true
    
    # 删除服务文件
    rm -f "$SERVICE_FILE"
    
    # 重新加载systemd
    systemctl daemon-reload
    
    log_info "系统服务已移除"
}

# 显示帮助
show_help() {
    echo "医院层级扫查系统安装脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -u, --uninstall     卸载系统"
    echo "  --skip-test         跳过安装测试"
    echo ""
}

# 主函数
main() {
    local skip_test=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -u|--uninstall)
                check_root
                uninstall
                log_info "卸载完成"
                exit 0
                ;;
            --skip-test)
                skip_test=true
                shift
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 执行安装流程
    check_root
    check_system
    install_dependencies
    create_app_dir
    create_config_dir
    create_env_config
    create_systemd_service
    configure_firewall
    
    if [ "$skip_test" != true ]; then
        test_installation
    fi
    
    show_install_info
}

# 执行主函数
main "$@"