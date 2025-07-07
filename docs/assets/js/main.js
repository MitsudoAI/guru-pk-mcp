// 专家辩论信息图展示系统 - 主要JavaScript文件
// 遵循塔夫特设计原则：功能性第一，装饰性最小

class InfographicsManager {
    constructor() {
        this.infographics = [];
        this.filteredInfographics = [];
        this.currentFilter = 'all';
        this.currentSearch = '';
        this.currentSort = 'date-desc';
        this.isLoading = false;
        
        this.init();
    }
    
    async init() {
        this.bindEvents();
        await this.loadInfographics();
        this.renderInfographics();
    }
    
    bindEvents() {
        // 搜索功能
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.currentSearch = e.target.value.toLowerCase();
                this.filterAndRender();
            }, 300));
            
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
        }
        
        // 过滤标签
        const filterTabs = document.querySelectorAll('.filter-tab');
        filterTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                filterTabs.forEach(t => t.classList.remove('active'));
                e.target.classList.add('active');
                this.currentFilter = e.target.dataset.filter;
                this.filterAndRender();
            });
        });
        
        // 排序功能
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.currentSort = e.target.value;
                this.sortInfographics();
                this.renderInfographics();
            });
        }
    }
    
    async loadInfographics() {
        this.showLoading();
        try {
            const response = await fetch('api/infographics.json');
            if (!response.ok) throw new Error('Failed to load infographics');
            
            const data = await response.json();
            this.infographics = data.infographics || [];
            this.filteredInfographics = [...this.infographics];
            
            // 更新统计信息
            this.updateStats(data.metadata);
            
        } catch (error) {
            console.error('Error loading infographics:', error);
            this.showError('加载信息图失败，请稍后重试');
        } finally {
            this.hideLoading();
        }
    }
    
    filterAndRender() {
        this.filteredInfographics = this.infographics.filter(item => {
            // 搜索过滤
            const matchesSearch = !this.currentSearch || 
                item.title.toLowerCase().includes(this.currentSearch) ||
                item.question.toLowerCase().includes(this.currentSearch) ||
                item.summary.toLowerCase().includes(this.currentSearch) ||
                item.tags.some(tag => tag.toLowerCase().includes(this.currentSearch)) ||
                item.experts.some(expert => expert.name.toLowerCase().includes(this.currentSearch));
            
            // 分类过滤
            const matchesFilter = this.currentFilter === 'all' || 
                item.category === this.currentFilter ||
                (this.currentFilter === 'recent' && this.isRecent(item.date));
            
            return matchesSearch && matchesFilter;
        });
        
        this.sortInfographics();
        this.renderInfographics();
    }
    
    sortInfographics() {
        this.filteredInfographics.sort((a, b) => {
            switch (this.currentSort) {
                case 'date-desc':
                    return new Date(b.date) - new Date(a.date);
                case 'date-asc':
                    return new Date(a.date) - new Date(b.date);
                case 'title-asc':
                    return a.title.localeCompare(b.title);
                case 'title-desc':
                    return b.title.localeCompare(a.title);
                default:
                    return 0;
            }
        });
    }
    
    renderInfographics() {
        const grid = document.getElementById('infographicsGrid');
        if (!grid) return;
        
        if (this.filteredInfographics.length === 0) {
            this.showEmptyState();
            return;
        }
        
        this.hideEmptyState();
        
        grid.innerHTML = this.filteredInfographics.map(item => 
            this.createInfographicCard(item)
        ).join('');
        
        // 绑定卡片点击事件
        this.bindCardEvents();
    }
    
    createInfographicCard(infographic) {
        const formattedDate = this.formatDate(infographic.date);
        const expertBadges = infographic.experts.map(expert => 
            `<div class="expert-badge">
                <span class="expert-emoji">${expert.emoji}</span>
                <span class="expert-name">${expert.name}</span>
            </div>`
        ).join('');
        
        const roundIndicators = Array.from({length: 4}, (_, i) => 
            `<div class="round-indicator ${i < infographic.rounds ? 'completed' : ''}"></div>`
        ).join('');
        
        const featuredBadge = infographic.featured ? 
            '<div class="featured-badge">⭐ 精选</div>' : '';
        
        return `
            <div class="infographic-card" data-id="${infographic.id}" data-path="${infographic.path}">
                <div class="card-header">
                    <div class="card-title">${infographic.title}</div>
                    <div class="card-date">${formattedDate}</div>
                </div>
                
                ${featuredBadge}
                
                <div class="card-experts">
                    ${expertBadges}
                </div>
                
                <div class="card-summary">
                    ${infographic.summary}
                </div>
                
                <div class="card-stats">
                    <div class="card-rounds">
                        ${roundIndicators}
                    </div>
                    <div class="card-wordcount">
                        ${infographic.wordCount.toLocaleString()} 字
                    </div>
                </div>
                
                <div class="card-tags">
                    ${infographic.tags.slice(0, 3).map(tag => 
                        `<span class="tag">${tag}</span>`
                    ).join('')}
                </div>
            </div>
        `;
    }
    
    bindCardEvents() {
        const cards = document.querySelectorAll('.infographic-card');
        cards.forEach(card => {
            card.addEventListener('click', (e) => {
                const path = card.dataset.path;
                if (path) {
                    // 在新窗口打开信息图
                    window.open(path, '_blank');
                }
            });
            
            // 键盘访问性
            card.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    card.click();
                }
            });
        });
    }
    
    performSearch() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            this.currentSearch = searchInput.value.toLowerCase();
            this.filterAndRender();
        }
    }
    
    showLoading() {
        const loading = document.getElementById('loading');
        if (loading) loading.style.display = 'block';
        this.isLoading = true;
    }
    
    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) loading.style.display = 'none';
        this.isLoading = false;
    }
    
    showEmptyState() {
        const emptyState = document.getElementById('emptyState');
        if (emptyState) emptyState.style.display = 'block';
    }
    
    hideEmptyState() {
        const emptyState = document.getElementById('emptyState');
        if (emptyState) emptyState.style.display = 'none';
    }
    
    showError(message) {
        const grid = document.getElementById('infographicsGrid');
        if (grid) {
            grid.innerHTML = `
                <div class="error-state">
                    <div class="error-icon">⚠️</div>
                    <div class="error-message">${message}</div>
                </div>
            `;
        }
    }
    
    updateStats(metadata) {
        const totalCount = document.getElementById('totalCount');
        if (totalCount && metadata) {
            totalCount.textContent = metadata.total || this.infographics.length;
        }
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) return '今天';
        if (diffDays === 2) return '昨天';
        if (diffDays <= 7) return `${diffDays}天前`;
        
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
    
    isRecent(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays <= 7;
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// 全局函数供外部调用
window.performSearch = function() {
    if (window.infographicsManager) {
        window.infographicsManager.performSearch();
    }
};

window.sortInfographicsBy = function(sortBy) {
    if (window.infographicsManager) {
        window.infographicsManager.currentSort = sortBy;
        window.infographicsManager.sortInfographics();
        window.infographicsManager.renderInfographics();
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    window.infographicsManager = new InfographicsManager();
    
    // 添加键盘快捷键
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K 聚焦搜索框
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });
    
    // 处理浏览器后退
    window.addEventListener('popstate', function(e) {
        if (e.state && e.state.filter) {
            window.infographicsManager.currentFilter = e.state.filter;
            window.infographicsManager.filterAndRender();
        }
    });
    
    // 添加一些CSS样式到现有的CSS中
    const additionalStyles = `
        .featured-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            background: #ff6b6b;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .card-tags {
            display: flex;
            gap: 0.25rem;
            flex-wrap: wrap;
            margin-top: 0.5rem;
        }
        
        .tag {
            background: #f0f0f0;
            color: #666;
            padding: 0.125rem 0.375rem;
            border-radius: 3px;
            font-size: 0.7rem;
        }
        
        .error-state {
            text-align: center;
            padding: 2rem;
            color: #e74c3c;
            grid-column: 1 / -1;
        }
        
        .error-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .error-message {
            font-size: 1rem;
        }
        
        .infographic-card {
            position: relative;
            outline: none;
            cursor: pointer;
        }
        
        .infographic-card:focus {
            box-shadow: 0 0 0 2px #667eea;
        }
        
        .left-controls,
        .right-controls {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .search-filter {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            gap: 1rem;
            flex-wrap: wrap;
        }
        
        @media (max-width: 768px) {
            .left-controls,
            .right-controls {
                flex-direction: column;
                align-items: stretch;
            }
            
            .search-filter {
                flex-direction: column;
                align-items: stretch;
            }
        }
    `;
    
    const style = document.createElement('style');
    style.textContent = additionalStyles;
    document.head.appendChild(style);
});

// 导出供其他脚本使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = InfographicsManager;
}