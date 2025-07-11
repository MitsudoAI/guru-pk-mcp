#!/usr/bin/env python3
"""
自动化同步信息图到GitHub Pages
从data目录扫描信息图文件，提取元数据，更新API文件，复制文件到docs目录
"""

import os
import re
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

class InfographicsSyncer:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.data_dir = self.project_root / "data"
        self.docs_dir = self.project_root / "docs"
        self.infographics_dir = self.docs_dir / "infographics"
        self.api_file = self.docs_dir / "api" / "infographics.json"
        
        # 确保目录存在
        self.infographics_dir.mkdir(parents=True, exist_ok=True)
        self.api_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 专家分类映射
        self.expert_categories = {
            "技术": "tech",
            "商业": "business", 
            "哲学": "philosophy",
            "科学": "science",
            "设计": "design",
            "经济": "economics"
        }
        
        # 关键词到分类的映射
        self.keyword_to_category = {
            "ai": "tech",
            "开发": "tech",
            "程序": "tech",
            "软件": "tech",
            "算法": "tech",
            "数据": "tech",
            "企业": "business",
            "商业": "business",
            "管理": "business",
            "战略": "business",
            "营销": "business",
            "哲学": "philosophy",
            "思维": "philosophy",
            "认知": "philosophy",
            "伦理": "philosophy",
            "设计": "design",
            "用户体验": "design",
            "界面": "design",
            "可视化": "design"
        }
    
    def sync_all(self) -> bool:
        """同步所有信息图"""
        print("开始同步信息图...")
        
        try:
            # 1. 扫描data目录中的信息图文件
            infographic_files = self.scan_infographic_files()
            print(f"发现 {len(infographic_files)} 个信息图文件")
            
            # 2. 处理每个文件
            infographics_data = []
            for file_path in infographic_files:
                try:
                    infographic_data = self.process_infographic_file(file_path)
                    if infographic_data:
                        infographics_data.append(infographic_data)
                        print(f"处理完成: {file_path.name}")
                except Exception as e:
                    print(f"处理文件 {file_path.name} 时出错: {e}")
                    continue
            
            # 3. 更新API文件
            self.update_api_file(infographics_data)
            print(f"更新API文件: {self.api_file}")
            
            # 4. 复制文件到docs目录
            self.copy_infographic_files(infographic_files)
            print("复制文件完成")
            
            print(f"同步完成! 共处理 {len(infographics_data)} 个信息图")
            return True
            
        except Exception as e:
            print(f"同步过程中出错: {e}")
            return False
    
    def scan_infographic_files(self) -> List[Path]:
        """扫描data目录中的信息图HTML文件"""
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data目录不存在: {self.data_dir}")
        
        files = []
        for file_path in self.data_dir.glob("*.html"):
            # 只处理信息图文件
            if ("infographic" in file_path.name.lower() or 
                "expert_debate" in file_path.name.lower()):
                files.append(file_path)
        
        return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def process_infographic_file(self, file_path: Path) -> Optional[Dict]:
        """处理单个信息图文件，提取元数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # 提取基本信息
            title = self.extract_title(soup, file_path)
            question = self.extract_question(soup)
            experts = self.extract_experts(soup)
            
            # 生成ID
            infographic_id = self.generate_id(file_path)
            
            # 获取文件时间
            file_stat = file_path.stat()
            created_time = datetime.fromtimestamp(file_stat.st_ctime)
            updated_time = datetime.fromtimestamp(file_stat.st_mtime)
            
            # 分析内容
            summary = self.generate_summary(title, question, experts)
            category = self.determine_category(title, question, experts)
            tags = self.extract_tags(title, question, content)
            word_count = self.count_words(content)
            
            return {
                "id": infographic_id,
                "title": title,
                "question": question,
                "date": created_time.strftime("%Y-%m-%d"),
                "created": created_time.isoformat() + "Z",
                "updated": updated_time.isoformat() + "Z",
                "filename": file_path.name,
                "path": f"infographics/{file_path.name}",
                "experts": experts,
                "summary": summary,
                "category": category,
                "tags": tags,
                "rounds": 4,  # 默认4轮
                "wordCount": word_count,
                "status": "completed",
                "featured": self.is_featured(file_path)
            }
            
        except Exception as e:
            print(f"处理文件 {file_path.name} 时出错: {e}")
            return None
    
    def extract_title(self, soup: BeautifulSoup, file_path: Path) -> str:
        """提取标题"""
        # 尝试从title标签提取
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
            # 清理标题
            title = re.sub(r'\s*-\s*.*$', '', title)  # 移除副标题
            if title and title != "专家辩论信息图":
                return title
        
        # 尝试从h1标签提取
        h1_tag = soup.find('h1')
        if h1_tag:
            title = h1_tag.get_text().strip()
            if title:
                return title
        
        # 尝试从.question类提取
        question_div = soup.find(class_='question')
        if question_div:
            question = question_div.get_text().strip()
            if question:
                return question
        
        # 从文件名生成
        return self.generate_title_from_filename(file_path)
    
    def extract_question(self, soup: BeautifulSoup) -> str:
        """提取问题"""
        # 查找问题相关的元素
        question_selectors = [
            '.question',
            '.header .question',
            'h1',
            '.title'
        ]
        
        for selector in question_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().strip()
                if text and '?' in text:
                    return text
        
        return "专家辩论问题"
    
    def extract_experts(self, soup: BeautifulSoup) -> List[Dict]:
        """提取专家信息"""
        experts = []
        
        # 查找专家相关的元素
        expert_elements = soup.select('.expert, .expert-name, .persona')
        
        for element in expert_elements:
            # 尝试提取专家名称和emoji
            name_elem = element.find(class_='expert-name') or element
            emoji_elem = element.find(class_='expert-emoji') or element
            
            if name_elem:
                name = name_elem.get_text().strip()
                emoji = "🧠"  # 默认emoji
                
                # 尝试提取emoji
                if emoji_elem:
                    emoji_text = emoji_elem.get_text().strip()
                    emoji_match = re.search(r'([🧠💡🎯🏗️⚛️💻📊🎨📈🔍💭🤖🎓])', emoji_text)
                    if emoji_match:
                        emoji = emoji_match.group(1)
                
                if name and name not in [e['name'] for e in experts]:
                    experts.append({
                        "name": name,
                        "emoji": emoji,
                        "role": self.determine_expert_role(name),
                        "category": self.determine_expert_category(name)
                    })
        
        # 如果没有找到专家，添加默认专家
        if not experts:
            experts = [
                {"name": "专家A", "emoji": "🧠", "role": "领域专家", "category": "tech"},
                {"name": "专家B", "emoji": "💡", "role": "思想家", "category": "philosophy"},
                {"name": "专家C", "emoji": "🎯", "role": "实践者", "category": "business"}
            ]
        
        return experts[:3]  # 最多3个专家
    
    def determine_expert_role(self, name: str) -> str:
        """根据专家名称确定角色"""
        role_mapping = {
            "马丁·福勒": "软件架构师",
            "丹·阿布拉莫夫": "前端专家",
            "杰夫·阿特伍德": "软件工程师",
            "迈克尔·波特": "战略管理专家",
            "克里斯滕森": "创新理论家",
            "安迪·格鲁夫": "企业管理专家",
            "爱德华·塔夫特": "信息设计大师",
            "唐纳德·诺曼": "设计心理学家",
            "阿尔贝托·开罗": "数据可视化专家"
        }
        
        return role_mapping.get(name, "领域专家")
    
    def determine_expert_category(self, name: str) -> str:
        """根据专家名称确定分类"""
        category_mapping = {
            "马丁·福勒": "tech",
            "丹·阿布拉莫夫": "tech",
            "杰夫·阿特伍德": "tech",
            "迈克尔·波特": "business",
            "克里斯滕森": "business",
            "安迪·格鲁夫": "business",
            "爱德华·塔夫特": "design",
            "唐纳德·诺曼": "design",
            "阿尔贝托·开罗": "design"
        }
        
        return category_mapping.get(name, "philosophy")
    
    def generate_summary(self, title: str, question: str, experts: List[Dict]) -> str:
        """生成摘要"""
        expert_names = [e['name'] for e in experts]
        if len(expert_names) > 2:
            expert_str = f"{expert_names[0]}、{expert_names[1]}等{len(expert_names)}位专家"
        else:
            expert_str = "、".join(expert_names)
        
        return f"{expert_str}就{title}展开深入讨论，探讨相关领域的核心问题与解决方案。"
    
    def determine_category(self, title: str, question: str, experts: List[Dict]) -> str:
        """确定分类"""
        text = f"{title} {question}".lower()
        
        # 统计专家分类
        expert_categories = [e['category'] for e in experts]
        if expert_categories:
            # 返回专家中最常见的分类
            from collections import Counter
            category_counter = Counter(expert_categories)
            return category_counter.most_common(1)[0][0]
        
        # 基于关键词确定分类
        for keyword, category in self.keyword_to_category.items():
            if keyword in text:
                return category
        
        return "philosophy"  # 默认分类
    
    def extract_tags(self, title: str, question: str, content: str) -> List[str]:
        """提取标签"""
        tags = set()
        text = f"{title} {question}".lower()
        
        # 建筑与设计相关标签
        architecture_keywords = {
            "建筑": "建筑",
            "设计": "设计", 
            "展馆": "展馆",
            "万博": "万博",
            "空间": "空间设计",
            "美学": "美学",
            "艺术": "艺术"
        }
        for keyword, tag in architecture_keywords.items():
            if keyword in text:
                tags.add(tag)
        
        # 技术相关标签
        tech_keywords = {
            "ai": "AI",
            "人工智能": "AI",
            "开发": "开发",
            "软件": "软件",
            "程序": "编程",
            "算法": "算法",
            "数据": "数据",
            "技术": "技术",
            "架构": "软件架构",
            "码农": "程序员"
        }
        for keyword, tag in tech_keywords.items():
            if keyword in text:
                tags.add(tag)
        
        # 商业相关标签
        business_keywords = {
            "企业": "企业",
            "商业": "商业",
            "管理": "管理",
            "战略": "战略",
            "营销": "营销",
            "数字化": "数字化",
            "转型": "转型"
        }
        for keyword, tag in business_keywords.items():
            if keyword in text:
                tags.add(tag)
        
        # 文化与地域标签
        culture_keywords = {
            "日本": "日本",
            "大阪": "大阪",
            "中国": "中国",
            "文化": "文化",
            "传统": "传统",
            "现代": "现代"
        }
        for keyword, tag in culture_keywords.items():
            if keyword in text:
                tags.add(tag)
        
        # 其他专业领域标签
        other_keywords = {
            "哲学": "哲学",
            "心理": "心理学",
            "经济": "经济",
            "科学": "科学",
            "教育": "教育",
            "创新": "创新"
        }
        for keyword, tag in other_keywords.items():
            if keyword in text:
                tags.add(tag)
        
        # 如果没有找到任何标签，根据问题类型添加默认标签
        if not tags:
            if "?" in question or "？" in question:
                tags.add("专家辩论")
        
        # 限制标签数量并排序
        return sorted(list(tags))[:8]
    
    def count_words(self, content: str) -> int:
        """统计字数"""
        # 移除HTML标签
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # 计算中文字符数
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        return len(chinese_chars)
    
    def is_featured(self, file_path: Path) -> bool:
        """判断是否为精选"""
        # 可以根据文件大小、创建时间等判断
        return "sample" in file_path.name.lower()
    
    def generate_id(self, file_path: Path) -> str:
        """生成信息图ID"""
        # 尝试从文件名提取ID
        name = file_path.stem
        if "_" in name:
            parts = name.split("_")
            if len(parts) > 1:
                return parts[-1]
        
        # 生成基于文件名的ID
        return name.replace("infographic_", "").replace("expert_debate_", "")
    
    def generate_title_from_filename(self, file_path: Path) -> str:
        """从文件名生成标题"""
        name = file_path.stem
        
        # 移除常见前缀
        name = name.replace("infographic_", "").replace("expert_debate_", "")
        
        # 处理特殊名称
        if "sample" in name.lower():
            return "专家辩论信息图样例"
        elif "gemini" in name.lower():
            return "AI模型能力对比分析"
        elif "sonet" in name.lower():
            return "AI推理能力发展趋势"
        
        return f"专家辩论: {name}"
    
    def update_api_file(self, infographics_data: List[Dict]) -> None:
        """更新API文件"""
        # 生成元数据
        categories = {}
        all_tags = set()
        experts_count = 0
        
        for item in infographics_data:
            # 统计分类
            category = item['category']
            categories[category] = categories.get(category, 0) + 1
            
            # 收集标签
            all_tags.update(item['tags'])
            
            # 统计专家
            experts_count += len(item['experts'])
        
        metadata = {
            "total": len(infographics_data),
            "lastUpdated": datetime.now().isoformat() + "Z",
            "categories": categories,
            "experts": {
                "total": experts_count,
                "unique": len(set(e['name'] for item in infographics_data for e in item['experts']))
            },
            "tags": sorted(list(all_tags))
        }
        
        # 构建API数据
        api_data = {
            "infographics": infographics_data,
            "metadata": metadata
        }
        
        # 写入文件
        with open(self.api_file, 'w', encoding='utf-8') as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)
    
    def copy_infographic_files(self, file_paths: List[Path]) -> None:
        """复制信息图文件到docs目录，并清理不存在的文件"""
        # 获取当前存在的文件名
        current_files = {file_path.name for file_path in file_paths}
        
        # 清理docs目录中不再存在的HTML文件
        self.cleanup_removed_files(current_files)
        
        # 复制当前文件
        for file_path in file_paths:
            dest_path = self.infographics_dir / file_path.name
            shutil.copy2(file_path, dest_path)
            print(f"复制文件: {file_path.name} -> {dest_path}")
    
    def cleanup_removed_files(self, current_files: set) -> None:
        """清理docs目录中不再存在的信息图文件"""
        if not self.infographics_dir.exists():
            return
        
        # 扫描docs/infographics目录中的HTML文件
        existing_files = []
        for file_path in self.infographics_dir.glob("*.html"):
            # 跳过index.html等非信息图文件
            if file_path.name != "index.html":
                existing_files.append(file_path)
        
        # 找出需要删除的文件
        files_to_remove = []
        for file_path in existing_files:
            if file_path.name not in current_files:
                files_to_remove.append(file_path)
        
        # 删除不再存在的文件
        for file_path in files_to_remove:
            try:
                file_path.unlink()
                print(f"删除文件: {file_path.name} (源文件已不存在)")
            except Exception as e:
                print(f"删除文件 {file_path.name} 时出错: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='同步信息图到GitHub Pages')
    parser.add_argument('--project-root', default='.', help='项目根目录')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际执行')
    
    args = parser.parse_args()
    
    syncer = InfographicsSyncer(args.project_root)
    
    if args.dry_run:
        print("预览模式：")
        files = syncer.scan_infographic_files()
        for file_path in files:
            print(f"  - {file_path.name}")
    else:
        success = syncer.sync_all()
        exit(0 if success else 1)

if __name__ == "__main__":
    main()