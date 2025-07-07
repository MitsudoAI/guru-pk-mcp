#!/bin/bash
# GitHub Pages 信息图同步脚本
# 使用方法: ./scripts/sync.sh

set -e

# 检查依赖
check_dependencies() {
    if ! command -v python3 &> /dev/null; then
        echo "错误: 需要安装 Python 3"
        exit 1
    fi
    
    # 检查并安装 beautifulsoup4
    if ! python3 -c "import bs4" &> /dev/null; then
        echo "正在安装 beautifulsoup4..."
        pip3 install beautifulsoup4
    fi
}

# 主函数
main() {
    echo "开始同步信息图到 GitHub Pages..."
    
    # 检查依赖
    check_dependencies
    
    # 获取项目根目录
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    echo "项目根目录: $PROJECT_ROOT"
    
    # 运行同步脚本
    echo "运行同步脚本..."
    python3 "$PROJECT_ROOT/scripts/sync_infographics.py" --project-root "$PROJECT_ROOT"
    
    if [ $? -eq 0 ]; then
        echo "✅ 同步完成!"
        echo "📁 文件位置: $PROJECT_ROOT/docs/"
        echo "🌐 GitHub Pages 配置: https://github.com/settings/pages"
        echo ""
        echo "下一步:"
        echo "1. 提交更改到 Git 仓库"
        echo "2. 在 GitHub 仓库设置中启用 Pages (使用 docs/ 目录)"
        echo "3. 访问你的 GitHub Pages 网站查看信息图"
    else
        echo "❌ 同步失败"
        exit 1
    fi
}

# 预览模式
preview() {
    echo "预览模式: 扫描可用的信息图文件..."
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    python3 "$PROJECT_ROOT/scripts/sync_infographics.py" --project-root "$PROJECT_ROOT" --dry-run
}

# 处理命令行参数
case "${1:-}" in
    "preview"|"--preview"|"-p")
        preview
        ;;
    "help"|"--help"|"-h")
        echo "GitHub Pages 信息图同步脚本"
        echo ""
        echo "使用方法:"
        echo "  $0           # 执行同步"
        echo "  $0 preview   # 预览模式"
        echo "  $0 help      # 显示帮助"
        ;;
    *)
        main
        ;;
esac