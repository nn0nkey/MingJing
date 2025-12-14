.PHONY: help start stop restart logs status clean backup build

help:
	@echo "MingJing 明镜 - 快捷命令"
	@echo ""
	@echo "使用方法: make [命令]"
	@echo ""
	@echo "可用命令:"
	@echo "  start     - 启动服务"
	@echo "  stop      - 停止服务"
	@echo "  restart   - 重启服务"
	@echo "  logs      - 查看日志"
	@echo "  status    - 查看状态"
	@echo "  clean     - 清理数据"
	@echo "  backup    - 备份数据"
	@echo "  build     - 重新构建"
	@echo "  help      - 显示帮助"

start:
	@./deploy.sh start

stop:
	@./deploy.sh stop

restart:
	@./deploy.sh restart

logs:
	@./deploy.sh logs

status:
	@./deploy.sh status

clean:
	@./deploy.sh clean

backup:
	@./deploy.sh backup

build:
	@docker-compose build --no-cache
	@docker-compose up -d
