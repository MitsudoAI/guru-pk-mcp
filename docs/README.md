# 专家辩论信息图 GitHub Pages 网站

基于爱德华·塔夫特设计原则的AI智能体专家辩论信息图展示网站。

## 功能特点

- 🎨 **塔夫特设计原则**: 数据-墨水比例最大化，零装饰，视觉诚实
- 📱 **响应式设计**: 适配桌面、平板、手机等各种设备
- 🔍 **智能搜索**: 支持问题、专家、标签的快速搜索
- 🏷️ **分类过滤**: 按技术、商业、哲学等类别筛选
- 📊 **动态排序**: 支持按时间、标题等多种排序方式
- ♿ **无障碍设计**: 支持键盘导航和屏幕阅读器

## 网站结构

```
docs/
├── index.html              # 主页
├── infographics/          # 信息图目录
│   ├── index.html         # 信息图列表页
│   └── *.html            # 各个信息图文件
├── assets/               # 静态资源
│   ├── css/tufte.css     # 塔夫特风格样式
│   ├── js/main.js        # 主要交互逻辑
│   └── images/           # 图片资源
├── api/                  # 数据接口
│   └── infographics.json # 信息图元数据
└── _config.yml           # GitHub Pages 配置
```

## 使用方法

### 1. 启用 GitHub Pages

1. 在 GitHub 仓库设置中找到 "Pages" 选项
2. Source 选择 "Deploy from a branch"
3. Branch 选择 "main"，文件夹选择 "/docs"
4. 点击 "Save" 保存设置

### 2. 同步信息图

运行同步脚本将 `data/` 目录中的信息图文件同步到网站：

```bash
# 预览模式 - 查看可用的信息图文件
./scripts/sync.sh preview

# 执行同步
./scripts/sync.sh
```

### 3. 访问网站

GitHub Pages 会提供类似以下的访问地址：

```
https://[username].github.io/[repository-name]/
```

## 设计原则

本网站严格遵循爱德华·塔夫特的信息设计原则：

### 1. 数据-墨水比例 (Data-Ink Ratio)

- 每个视觉元素都承载信息价值
- 移除非必要的装饰性元素
- 最大化信息密度

### 2. 视觉诚实 (Visual Honesty)

- 视觉权重与信息重要性成正比
- 避免误导性的视觉表现
- 准确反映数据关系

### 3. 认知效率 (Cognitive Efficiency)

- 5秒内找到目标信息
- 直观的导航和搜索
- 渐进式信息披露

### 4. 零装饰原则 (Zero Decoration)

- 纯功能性设计
- 去除图表垃圾
- 简洁优雅的视觉表现

## 技术特性

- **纯静态网站**: 无服务器依赖，完全基于 GitHub Pages
- **渐进增强**: 基础功能在无 JavaScript 时仍可用
- **性能优化**: 延迟加载、资源压缩
- **SEO 友好**: 语义化 HTML，完善的 meta 标签
- **打印友好**: 塔夫特测试 - 打印后依然清晰

## 自动化

### 同步脚本功能

- 自动扫描 `data/` 目录中的信息图文件
- 智能提取元数据（标题、专家、分类等）
- 生成 API 数据文件
- 复制文件到网站目录

### 元数据提取

自动从 HTML 文件中提取：

- 标题和问题
- 专家信息（姓名、emoji、角色）
- 内容分类和标签
- 字数统计和创建时间

## 开发

本地开发服务器：

```bash
# 使用 Jekyll（推荐）
bundle exec jekyll serve

# 或使用 Python HTTP 服务器
cd docs && python3 -m http.server 8000
```

## 许可

本项目基于 [LICENSE](../LICENSE) 文件中的许可证。

---

*遵循塔夫特设计原则，追求卓越的信息可视化体验。*
