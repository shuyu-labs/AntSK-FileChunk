# Makefile for AntSK-FileChunk

.PHONY: help install test clean lint format docs dev-setup

# 默认目标
help:
	@echo "可用命令："
	@echo "  install     - 安装项目依赖"
	@echo "  dev-setup   - 设置开发环境"
	@echo "  test        - 运行测试"
	@echo "  lint        - 代码质量检查"
	@echo "  format      - 代码格式化"
	@echo "  clean       - 清理生成的文件"
	@echo "  docs        - 生成文档"
	@echo "  run-example - 运行示例"

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
