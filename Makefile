.PHONY: help install dev-install format lint test server build clean all lint-docs check fix-docs fix pages-preview pages-sync pages-clean-files pages-serve pages-build pages-clean pages-deploy

help:
	@echo "Guru-PK MCP 开发命令"
	@echo ""
	@echo "📦 项目管理:"
	@echo "  install     - 安装项目依赖"
	@echo "  dev-install - 安装开发依赖"
	@echo "  refresh-uvx - 刷新UVX缓存（本地开发）"
	@echo "  refresh-uvx-pypi - 刷新UVX缓存（PyPI安装）"
	@echo "  install-and-refresh - 安装并刷新UVX缓存"
	@echo ""
	@echo "🔧 代码质量:"
	@echo "  format      - 格式化代码"
	@echo "  lint        - 代码质量检查"
	@echo "  test        - 运行测试"
	@echo "  lint-docs   - 检查文档格式"
	@echo "  fix-docs    - 自动修复文档格式"
	@echo "  check       - 检查所有格式"
	@echo "  fix         - 修复所有格式问题"
	@echo ""
	@echo "🚀 构建发布:"
	@echo "  server      - 启动MCP服务器测试"
	@echo "  build       - 构建Python包"
	@echo "  clean       - 清理构建文件"
	@echo "  publish-test - 发布到测试PyPI"
	@echo "  publish     - 发布到正式PyPI"
	@echo "  all         - 运行完整的开发流程"
	@echo ""
	@echo "🌐 GitHub Pages:"
	@echo "  pages-preview    - 预览可同步的信息图文件"
	@echo "  pages-sync       - 同步信息图到GitHub Pages (自动清理删除的文件)"
	@echo "  pages-clean-files- 手动清理docs目录中不存在的信息图文件"
	@echo "  pages-serve      - 本地启动Pages开发服务器"
	@echo "  pages-build      - 构建GitHub Pages网站"
	@echo "  pages-clean      - 清理Pages构建文件"
	@echo "  pages-deploy     - 同步并准备部署到GitHub Pages"

install:
	uv pip install -e .

refresh-uvx:
	@echo "🔄 刷新UVX缓存（本地开发）..."
	uvx --refresh-package guru-pk-mcp --from . python -c "print('✅ UVX缓存已刷新')"

refresh-uvx-pypi:
	@echo "🔄 刷新UVX缓存（PyPI安装）..."
	uvx --refresh-package guru-pk-mcp --from guru-pk-mcp python -c "print('✅ UVX缓存已刷新')"

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

publish-test: clean build
	uv run twine upload --repository testpypi dist/*

publish: clean build
	uv run twine upload dist/*

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

all: format lint lint-docs test build

lint-docs:
	npx markdownlint-cli2 "README.md" "docs/**/*.md"

fix-docs:
	npx markdownlint-cli2 --fix "README.md" "docs/**/*.md"

check: lint lint-docs test
	@echo "✅ 所有检查通过"

fix: format fix-docs
	@echo "✅ 所有格式修复完成"

# GitHub Pages 相关命令
pages-preview:
	@echo "🔍 预览可同步的信息图文件..."
	@./scripts/sync.sh preview

pages-sync:
	@echo "🔄 同步信息图到GitHub Pages (包含自动清理)..."
	@./scripts/sync.sh
	@echo "✅ 同步完成! 文件已更新到 docs/ 目录"

pages-clean-files:
	@echo "🧹 清理docs目录中不存在的信息图文件..."
	@python3 scripts/clean_docs.py

pages-serve:
	@echo "🌐 启动本地GitHub Pages开发服务器..."
	@if command -v jekyll >/dev/null 2>&1; then \
		echo "使用 Jekyll 启动服务器..."; \
		cd docs && bundle exec jekyll serve --livereload; \
	elif command -v python3 >/dev/null 2>&1; then \
		echo "使用 Python HTTP 服务器启动..."; \
		echo "访问地址: http://localhost:8000"; \
		cd docs && python3 -m http.server 8000; \
	else \
		echo "❌ 错误: 需要安装 Jekyll 或 Python 3"; \
		exit 1; \
	fi

pages-build:
	@echo "🔨 构建GitHub Pages网站..."
	@$(MAKE) pages-sync
	@if command -v jekyll >/dev/null 2>&1; then \
		echo "使用 Jekyll 构建..."; \
		cd docs && bundle exec jekyll build; \
	else \
		echo "⚠️  警告: 未安装 Jekyll，跳过构建步骤"; \
		echo "网站文件已同步到 docs/ 目录，可直接用于 GitHub Pages"; \
	fi
	@echo "✅ 构建完成!"

pages-clean:
	@echo "🧹 清理GitHub Pages构建文件..."
	@rm -rf docs/_site/
	@rm -rf docs/.jekyll-cache/
	@rm -rf docs/.sass-cache/
	@echo "✅ 清理完成!"

pages-deploy: pages-clean pages-build
	@echo "🚀 准备部署到GitHub Pages..."
	@echo ""
	@echo "下一步操作:"
	@echo "1. 提交更改: git add docs/ && git commit -m 'Update GitHub Pages'"
	@echo "2. 推送到GitHub: git push origin main"
	@echo "3. 在GitHub仓库设置中启用Pages (使用docs/目录)"
	@echo "4. 访问你的GitHub Pages网站"
	@echo ""
	@if git status --porcelain docs/ 2>/dev/null | grep -q .; then \
		echo "📋 检测到docs/目录有未提交的更改"; \
		echo "运行以下命令提交更改:"; \
		echo "  git add docs/"; \
		echo "  git commit -m 'Update GitHub Pages with latest infographics'"; \
	else \
		echo "✅ docs/目录没有未提交的更改"; \
	fi

# 检查GitHub Pages依赖
check-pages-deps:
	@echo "🔍 检查GitHub Pages依赖..."
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "❌ 错误: 需要安装 Python 3"; \
		exit 1; \
	fi
	@if ! python3 -c "import bs4" >/dev/null 2>&1; then \
		echo "⚠️  警告: 未安装 beautifulsoup4，将自动安装..."; \
		pip3 install beautifulsoup4; \
	fi
	@echo "✅ 依赖检查完成!"