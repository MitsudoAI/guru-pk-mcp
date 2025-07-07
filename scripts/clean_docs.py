#!/usr/bin/env python3
"""
清理docs目录中不存在的信息图文件
"""

from pathlib import Path

def main():
    # 获取data目录中的信息图文件
    data_dir = Path('data')
    if not data_dir.exists():
        print("❌ data目录不存在")
        return
    
    data_files = set(data_dir.glob('*.html'))
    data_names = {
        f.name for f in data_files 
        if 'infographic' in f.name.lower() or 'expert_debate' in f.name.lower()
    }
    
    # 获取docs/infographics目录中的文件
    docs_dir = Path('docs/infographics')
    if not docs_dir.exists():
        print("✅ docs/infographics目录不存在，无需清理")
        return
    
    docs_files = list(docs_dir.glob('*.html'))
    removed_count = 0
    
    for f in docs_files:
        if f.name != 'index.html' and f.name not in data_names:
            print(f"删除文件: {f.name}")
            f.unlink()
            removed_count += 1
    
    if removed_count > 0:
        print(f"✅ 清理完成! 删除了 {removed_count} 个文件")
    else:
        print("✅ 没有需要清理的文件")

if __name__ == "__main__":
    main()