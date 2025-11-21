#!/bin/bash
# 医院层级扫查系统 - 数据备份脚本

set -e

# 配置变量
PROJECT_NAME="hospital-scanner"
BACKUP_BASE_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$BACKUP_BASE_DIR/$TIMESTAMP"
RETENTION_DAYS=30

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

# 创建备份目录
create_backup_dir() {
    log_info "创建备份目录: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
}

# 备份数据库
backup_database() {
    log_info "备份数据库..."
    
    # 备份SQLite数据库
    if [ -f "data/hospitals.db" ]; then
        cp data/hospitals.db "$BACKUP_DIR/hospitals_$TIMESTAMP.db"
        log_info "SQLite数据库备份完成"
    else
        log_warn "未找到SQLite数据库文件"
    fi
    
    # 备份Docker容器中的数据库（如果存在）
    if docker ps --format '{{.Names}}' | grep -q "hospital-scanner"; then
        log_info "备份Docker容器中的数据库..."
        docker exec hospital-scanner tar -czf - /app/data/hospitals.db > "$BACKUP_DIR/docker_hospitals_$TIMESTAMP.db.tar.gz" || log_warn "Docker数据库备份失败"
    fi
}

# 备份应用数据
backup_app_data() {
    log_info "备份应用数据..."
    
    # 备份data目录
    if [ -d "data" ]; then
        tar -czf "$BACKUP_DIR/data_$TIMESTAMP.tar.gz" data/ || log_warn "data目录备份失败"
        log_info "data目录备份完成"
    fi
    
    # 备份uploads目录
    if [ -d "uploads" ]; then
        tar -czf "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz" uploads/ || log_warn "uploads目录备份失败"
        log_info "uploads目录备份完成"
    fi
}

# 备份日志文件
backup_logs() {
    log_info "备份日志文件..."
    
    if [ -d "logs" ]; then
        # 仅备份最近的日志文件（避免备份过大的历史文件）
        find logs/ -name "*.log" -mtime -7 -exec tar -czf "$BACKUP_DIR/logs_recent_$TIMESTAMP.tar.gz" {} + 2>/dev/null || log_warn "日志备份失败"
        log_info "最近7天日志备份完成"
    else
        log_warn "未找到logs目录"
    fi
}

# 备份配置文件
backup_configs() {
    log_info "备份配置文件..."
    
    # 备份环境文件
    if [ -f ".env" ]; then
        cp .env "$BACKUP_DIR/.env.dev" || log_warn ".env备份失败"
    fi
    
    if [ -f ".env.prod" ]; then
        cp .env.prod "$BACKUP_DIR/.env.prod" || log_warn ".env.prod备份失败"
    fi
    
    # 备份Docker配置
    if [ -f "docker-compose.yml" ]; then
        cp docker-compose.yml "$BACKUP_DIR/" || log_warn "docker-compose.yml备份失败"
    fi
    
    if [ -f "docker-compose.prod.yml" ]; then
        cp docker-compose.prod.yml "$BACKUP_DIR/" || log_warn "docker-compose.prod.yml备份失败"
    fi
    
    # 备份nginx配置
    if [ -d "nginx" ]; then
        cp -r nginx "$BACKUP_DIR/" || log_warn "nginx配置备份失败"
    fi
    
    # 备份其他配置
    for config_file in "logging.conf" "supervisord.conf" "nginx.conf"; do
        if [ -f "$config_file" ]; then
            cp "$config_file" "$BACKUP_DIR/" || log_warn "$config_file备份失败"
        fi
    done
    
    log_info "配置文件备份完成"
}

# 创建备份信息文件
create_backup_info() {
    log_info "创建备份信息文件..."
    
    cat > "$BACKUP_DIR/backup_info.txt" << EOF
医院层级扫查系统备份信息
========================

备份时间: $TIMESTAMP
备份目录: $BACKUP_DIR
项目名称: $PROJECT_NAME
主机名: $(hostname)
用户: $(whoami)
Docker版本: $(docker --version 2>/dev/null || echo "未安装")
Docker Compose版本: $(docker-compose --version 2>/dev/null || echo "未安装")

系统信息:
- 操作系统: $(uname -s)
- 内核版本: $(uname -r)
- 架构: $(uname -m)

备份内容:
EOF
    
    # 列出备份的文件
    find "$BACKUP_DIR" -type f -exec ls -lh {} \; | awk '{print "- " $9 " (" $5 ")"}' >> "$BACKUP_DIR/backup_info.txt"
    
    log_info "备份信息文件创建完成"
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理 $RETENTION_DAYS 天前的备份..."
    
    if [ -d "$BACKUP_BASE_DIR" ]; then
        find "$BACKUP_BASE_DIR" -type d -name "??????_??????" -mtime +$RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || log_warn "清理旧备份时出现错误"
        log_info "旧备份清理完成"
    fi
}

# 验证备份
verify_backup() {
    log_info "验证备份完整性..."
    
    local backup_files=$(find "$BACKUP_DIR" -type f | wc -l)
    
    if [ "$backup_files" -gt 0 ]; then
        log_info "备份验证通过，共备份 $backup_files 个文件"
        return 0
    else
        log_error "备份验证失败，未找到备份文件"
        return 1
    fi
}

# 压缩备份
compress_backup() {
    log_info "压缩备份文件..."
    
    cd "$BACKUP_BASE_DIR"
    tar -czf "${PROJECT_NAME}_backup_$TIMESTAMP.tar.gz" "$TIMESTAMP/" 2>/dev/null || log_warn "压缩备份失败"
    
    # 删除原始目录（保留压缩文件）
    rm -rf "$TIMESTAMP/" 2>/dev/null || log_warn "删除原始备份目录失败"
    
    log_info "备份压缩完成: ${PROJECT_NAME}_backup_$TIMESTAMP.tar.gz"
}

# 显示帮助
show_help() {
    echo "医院层级扫查系统备份脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示帮助信息"
    echo "  -d, --database          仅备份数据库"
    echo "  -a, --all               完整备份（默认）"
    echo "  -c, --compress          备份后压缩"
    echo "  -r, --retention DAYS    设置保留天数（默认: $RETENTION_DAYS）"
    echo "  --cleanup               清理旧备份"
    echo ""
}

# 主函数
main() {
    local backup_type="all"
    local compress=false
    local cleanup=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--database)
                backup_type="database"
                shift
                ;;
            -a|--all)
                backup_type="all"
                shift
                ;;
            -c|--compress)
                compress=true
                shift
                ;;
            -r|--retention)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            --cleanup)
                cleanup=true
                shift
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 执行备份流程
    create_backup_dir
    
    case $backup_type in
        "database")
            backup_database
            ;;
        "all")
            backup_database
            backup_app_data
            backup_logs
            backup_configs
            create_backup_info
            ;;
    esac
    
    # 验证备份
    verify_backup
    
    # 压缩备份
    if [ "$compress" = true ]; then
        compress_backup
    fi
    
    # 清理旧备份
    if [ "$cleanup" = true ]; then
        cleanup_old_backups
    fi
    
    log_info "备份完成！备份位置: $BACKUP_DIR"
}

# 执行主函数
main "$@"