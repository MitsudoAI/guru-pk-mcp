.PHONY: help install dev-install format lint test server build clean all

help:
	@echo "Guru-PK MCP 开发命令"
	@echo ""
	@echo "可用命令:"
	@echo "  install     - 安装项目依赖"
	@echo "  dev-install - 安装开发依赖"
	@echo "  refresh-uvx - 刷新UVX缓存"
	@echo "  install-and-refresh - 安装并刷新UVX缓存"
	@echo "  format      - 格式化代码"
	@echo "  lint        - 代码质量检查"
	@echo "  test        - 运行测试"
	@echo "  server      - 启动MCP服务器测试"
	@echo "  build       - 构建Python包"
	@echo "  clean       - 清理构建文件"
	@echo "  publish-test - 发布到测试PyPI"
	@echo "  publish     - 发布到正式PyPI"
	@echo "  all         - 运行完整的开发流程"

install:
	uv pip install -e .

refresh-uvx:
	@echo "🔄 刷新UVX缓存..."
	uvx --refresh-package guru-pk-mcp --from . python -c "print('✅ UVX缓存已刷新')"

install-and-refresh: install refresh-uvx

dev-install:
	uv pip install -e ".[dev]"

format:
	uv run black src/
	uv run isort src/

lint:
	uv run ruff check src/
	uv run mypy src/

test:
	uv run pytest

server:
	uvx --from . guru-pk-mcp-server

build:
	uv build

publish-test:
	uv run twine upload --repository testpypi dist/*

publish:
	uv run twine upload dist/*

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

all: format lint test build