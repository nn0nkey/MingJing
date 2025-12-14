#!/bin/bash

# MingJing 明镜 - 一键部署脚本
# 使用方法: ./deploy.sh [start|stop|restart|logs|status]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 和 Docker Compose
check_dependencies() {
    print_info "检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    print_info "依赖检查通过 ✓"
}

# 创建必要的目录
create_directories() {
    print_info "创建数据目录..."
    mkdir -p data/db data/logs
    print_info "目录创建完成 ✓"
}

# 复制环境配置
setup_env() {
    if [ ! -f .env ]; then
        print_info "创建环境配置文件..."
        cp .env.example .env
        print_info "请编辑 .env 文件配置环境变量"
    fi
}

# 启动服务
start_services() {
    print_info "启动 MingJing 服务..."
    docker-compose up -d --build
    
    print_info "等待服务启动..."
    sleep 5
    
    print_info "检查服务状态..."
    docker-compose ps
    
    echo ""
    print_info "========================================="
    print_info "MingJing 明镜已成功启动！"
    print_info "========================================="
    print_info "前端访问地址: http://localhost"
    print_info "后端 API 地址: http://localhost:8000"
    print_info "API 文档: http://localhost:8000/docs"
    print_info "========================================="
    echo ""
    print_info "查看日志: ./deploy.sh logs"
    print_info "停止服务: ./deploy.sh stop"
}

# 停止服务
stop_services() {
    print_info "停止 MingJing 服务..."
    docker-compose down
    print_info "服务已停止 ✓"
}

# 重启服务
restart_services() {
    print_info "重启 MingJing 服务..."
    docker-compose restart
    print_info "服务已重启 ✓"
}

# 查看日志
view_logs() {
    docker-compose logs -f --tail=100
}

# 查看状态
check_status() {
    print_info "服务状态:"
    docker-compose ps
    
    echo ""
    print_info "容器健康状态:"
    docker ps --filter "name=mingjing" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# 清理数据
clean_data() {
    read -p "确定要清理所有数据吗？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_warn "清理数据..."
        docker-compose down -v
        rm -rf data/db/* data/logs/*
        print_info "数据已清理 ✓"
    else
        print_info "取消清理"
    fi
}

# 备份数据
backup_data() {
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    print_info "备份数据到 $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"
    cp -r data/db "$BACKUP_DIR/"
    print_info "备份完成 ✓"
}

# 主函数
main() {
    case "${1:-start}" in
        start)
            check_dependencies
            create_directories
            setup_env
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            view_logs
            ;;
        status)
            check_status
            ;;
        clean)
            clean_data
            ;;
        backup)
            backup_data
            ;;
        *)
            echo "使用方法: $0 {start|stop|restart|logs|status|clean|backup}"
            echo ""
            echo "命令说明:"
            echo "  start   - 启动服务（默认）"
            echo "  stop    - 停止服务"
            echo "  restart - 重启服务"
            echo "  logs    - 查看日志"
            echo "  status  - 查看状态"
            echo "  clean   - 清理数据"
            echo "  backup  - 备份数据"
            exit 1
            ;;
    esac
}

main "$@"
