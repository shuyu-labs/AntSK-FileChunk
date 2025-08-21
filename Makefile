# Makefile for AntSK-FileChunk

.PHONY: help install test clean lint format docs dev-setup docker-build docker-run docker-dev docker-stop docker-logs docker-shell

# 默认目标
help:
	@echo "🚀 AntSK-FileChunk 项目命令"
	@echo ""
	@echo "📦 基础命令："
	@echo "  install     - 安装项目依赖"
	@echo "  dev-setup   - 设置开发环境"
	@echo "  test        - 运行测试"
	@echo "  lint        - 代码质量检查"
	@echo "  format      - 代码格式化"
	@echo "  clean       - 清理生成的文件"
	@echo "  docs        - 生成文档"
	@echo "  run-example - 运行示例"
	@echo ""
	@echo "🐳 Docker 命令："
	@echo "  docker-build    - 构建 Docker 镜像"
	@echo "  docker-run      - 运行生产环境容器"
	@echo "  docker-dev      - 运行开发环境容器"
	@echo "  docker-stop     - 停止所有容器"
	@echo "  docker-logs     - 查看容器日志"
	@echo "  docker-shell    - 进入容器 shell"
	@echo "  docker-clean    - 清理 Docker 资源"
	@echo ""
	@echo "⚡ 快捷命令："
	@echo "  start          - 启动本地开发服务器"
	@echo "  start-docker   - 使用 Docker 启动服务"

# 安装依赖
install:
	pip install -r requirements.txt
	python -m nltk.downloader punkt stopwords

# 设置开发环境
dev-setup:
	python scripts/setup_dev.py

# 运行测试
test:
	python -m pytest tests/ -v

# 代码质量检查
lint:
	flake8 src/ tests/ --max-line-length=100
	mypy src/

# 代码格式化
format:
	black src/ tests/ scripts/
	isort src/ tests/ scripts/

# 清理生成的文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -delete
	rm -rf build/ dist/ .coverage htmlcov/

# 生成文档
docs:
	@echo "生成API文档..."
	# 这里可以添加文档生成命令

# 运行示例
run-example:
	python examples/demo.py

# 构建包
build:
	python setup.py sdist bdist_wheel

# 安装本地包（开发模式）
install-dev:
	pip install -e .[dev]

# ========== Docker 相关命令 ==========

# 构建 Docker 镜像
docker-build:
	@echo "🔨 构建 Docker 镜像..."
	docker build -t antsk/filechunk:latest .
	@echo "✅ 镜像构建完成！"

# 运行生产环境容器
docker-run:
	@echo "🚀 启动生产环境容器..."
	docker-compose up -d
	@echo "✅ 服务已启动！访问: http://localhost:8000"

# 运行开发环境容器
docker-dev:
	@echo "🔧 启动开发环境容器..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ 开发环境已启动！访问: http://localhost:8000"

# 停止所有容器
docker-stop:
	@echo "🛑 停止所有容器..."
	docker-compose down
	docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
	@echo "✅ 容器已停止！"

# 查看容器日志
docker-logs:
	@echo "📋 查看容器日志..."
	docker-compose logs -f

# 查看开发环境日志
docker-logs-dev:
	@echo "📋 查看开发环境日志..."
	docker-compose -f docker-compose.dev.yml logs -f

# 进入容器 shell
docker-shell:
	@echo "🐚 进入容器 shell..."
	docker exec -it antsk-filechunk bash

# 进入开发容器 shell
docker-shell-dev:
	@echo "🐚 进入开发容器 shell..."
	docker exec -it antsk-filechunk-dev bash

# 清理 Docker 资源
docker-clean:
	@echo "🧹 清理 Docker 资源..."
	docker-compose down -v --remove-orphans
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans 2>/dev/null || true
	docker system prune -f
	@echo "✅ 清理完成！"

# 重建并启动
docker-rebuild:
	@echo "🔄 重建并启动容器..."
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "✅ 重建完成！访问: http://localhost:8000"

# 查看 Docker 状态
docker-status:
	@echo "📊 Docker 容器状态："
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "📊 Docker 镜像："
	docker images antsk/filechunk --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# ========== 快捷命令 ==========

# 启动本地开发服务器
start:
	@echo "🔥 启动本地开发服务器..."
	python api_server.py

# 使用 Docker 启动服务
start-docker: docker-build docker-run

# 完整测试（包括 Docker）
test-all: test docker-build
	@echo "🧪 运行 Docker 集成测试..."
	docker-compose up -d
	sleep 10
	curl -f http://localhost:8000/health || (echo "❌ 健康检查失败" && exit 1)
	docker-compose down
	@echo "✅ 所有测试通过！"

# 生产部署
deploy-prod:
	@echo "🚀 准备生产部署..."
	docker-compose --profile production up -d
	@echo "✅ 生产环境已启动！"

# 备份数据
backup:
	@echo "💾 备份数据..."
	mkdir -p backup/$$(date +%Y%m%d_%H%M%S)
	docker cp antsk-filechunk:/app/logs backup/$$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
	docker cp antsk-filechunk:/app/config backup/$$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
	@echo "✅ 备份完成！"
