"""
动态专家生成系统 - 提供专家推荐的原则性指导
"""

from typing import Any


class DynamicExpertManager:
    """动态专家管理器 - 管理当前会话的专家"""

    def __init__(self, data_dir: str | None = None):
        # 保留data_dir参数以兼容现有代码，但实际不使用
        self.current_experts: dict[str, Any] = {}

    def set_current_experts(self, experts: dict[str, Any]) -> None:
        """设置当前会话的专家"""
        self.current_experts = experts

    def get_current_experts(self) -> dict[str, Any]:
        """获取当前会话的专家"""
        return self.current_experts

    def clear_current_experts(self) -> None:
        """清除当前专家"""
        self.current_experts = {}

    def validate_expert_data(self, expert_data: dict[str, Any] | None) -> bool:
        """验证专家数据完整性"""
        if expert_data is None:
            return False

        required_fields = [
            "name",
            "description",
            "core_traits",
            "speaking_style",
            "base_prompt",
        ]

        for field in required_fields:
            if field not in expert_data or not expert_data[field]:
                return False

        # 添加默认emoji
        if "emoji" not in expert_data:
            expert_data["emoji"] = "👤"

        return True

    def format_expert_list(self, experts: dict[str, Any]) -> list[dict[str, Any]]:
        """格式化专家列表用于显示"""
        return [
            {
                "name": expert["name"],
                "emoji": expert.get("emoji", "👤"),
                "description": expert["description"],
                "core_traits": expert["core_traits"],
                "speaking_style": expert["speaking_style"],
            }
            for expert in experts.values()
        ]


def get_question_analysis_guidance() -> str:
    """获取问题分析指导原则（供MCP Host端LLM使用）"""
    return """
# 问题分析指导原则

## 分析维度
请从以下维度分析问题：

### 1. 问题复杂度
- 简单问题：表述清晰、答案相对明确
- 中等复杂度：涉及多个因素、需要权衡
- 高复杂度：多领域交叉、存在争议、需要深度思考

### 2. 问题类型
- 方法咨询："如何"、"怎么"类问题
- 原因分析："为什么"、"原因"类问题
- 决策支持："选择"、"决策"类问题
- 趋势预测："未来"、"趋势"类问题
- 对比分析："比较"、"对比"类问题

### 3. 领域识别
识别问题所涉及的主要领域：
- 商业管理：企业经营、投资、市场营销
- 科技创新：技术发展、人工智能、数字化
- 哲学思辨：价值观、道德伦理、存在意义
- 心理行为：情绪管理、认知偏差、人际关系
- 教育成长：学习方法、知识体系、能力培养
- 社会文化：制度设计、文化传承、公共政策
- 健康生活：身心健康、生活方式、养生保健
- 创新设计：创意思维、产品设计、用户体验
- 领导管理：团队建设、决策制定、沟通协调
- 战略规划：长期发展、竞争优势、资源配置

## 分析要求
- 准确识别问题的核心要素
- 判断问题的复杂程度和讨论深度需求
- 识别相关的知识领域和专业背景
- 考虑不同视角和观点的价值
"""


def get_expert_recommendation_guidance() -> str:
    """获取专家推荐指导原则（供MCP Host端LLM使用）"""
    return """
# 专家推荐指导原则

## 推荐策略

### 1. 多样性原则
- 确保专家背景多元化，避免观点单一
- 平衡理论专家与实践专家
- 考虑不同文化背景和思维方式

### 2. 互补性原则
- 选择能够相互补充的专家组合
- 确保覆盖问题的主要方面
- 避免专家之间过度重叠

### 3. 针对性原则
- 根据问题类型选择合适的专家
- 考虑问题的复杂度和深度需求
- 匹配专家的专业能力与问题需求

### 4. 平衡性原则
- 避免某一种观点过于主导
- 确保不同立场都有代表
- 维持讨论的客观性和公正性

## 专家类型推荐

### 按问题类型推荐
- **方法咨询**：实践型专家，具有丰富实操经验
- **原因分析**：分析型专家，善于深度思考和逻辑推理
- **决策支持**：决策型专家，具有丰富的决策经验和框架
- **趋势预测**：前瞻型专家，具有未来洞察力和预判能力
- **对比分析**：综合型专家，能够客观比较不同方案

### 按复杂度推荐
- **高复杂度**：理论深度强的专家，能够处理复杂问题
- **中等复杂度**：理论与实践并重的专家
- **低复杂度**：实用性强、表达清晰的专家

### 按领域推荐
- **商业管理**：企业家、投资人、管理学者
- **科技创新**：技术领袖、科学家、创新思想家
- **哲学思辨**：哲学家、思想家、伦理学者
- **心理行为**：心理学家、行为学家、认知专家
- **教育成长**：教育家、学习专家、发展心理学家
- **社会文化**：社会学家、文化学者、政策专家
- **健康生活**：医学专家、健康管理专家、生活方式专家
- **创新设计**：设计师、创意专家、用户体验专家
- **领导管理**：领导力专家、组织行为专家、沟通专家
- **战略规划**：战略专家、管理咨询专家、商业分析师

## 质量检查

### 必要条件
- 每位专家都有明确的专业背景
- 专家之间具有差异化的观点
- 专家组合能够覆盖问题的主要方面

### 优化建议
- 避免专家名称重复
- 确保专家特质的多样性
- 平衡不同思维方式和方法论
- 考虑性别、年龄、文化背景的多元化
"""
