"""
智能模式选择器 - 根据问题和专家组合智能推荐最佳辩论模式
"""

from typing import Any

from .models import QuestionComplexity


class ModeSelector:
    """智能模式选择器 - 为MCP Host端提供决策指导"""

    @staticmethod
    def get_mode_selection_guidance(
        question: str,
        personas: list[dict[str, Any]] | None = None,
        user_preference: str | None = None,
    ) -> str:
        """为MCP Host端LLM提供模式选择的指导原则"""

        return f"""
# 辩论模式选择指导原则

## 问题分析
用户问题：{question}
专家数量：{len(personas) if personas else "未指定"}
用户偏好：{user_preference or "无特别要求"}

## 模式选择决策框架

### 1. 问题复杂度评估
请分析问题的复杂度并选择对应模式：

**简单问题（SIMPLE）**：
- 问题明确，答案相对标准
- 不需要深度辩论
- **推荐模式**：QUICK_CONSULTATION (2轮) + BATCH处理

**标准问题（STANDARD）**：
- 有一定复杂性，需要多角度分析
- 专家间可能有不同观点
- **推荐模式**：STANDARD_DEBATE (4轮) + BATCH处理或SEQUENTIAL

**复杂问题（COMPLEX）**：
- 多层次、多维度的复杂问题
- 需要深度思辨和多轮交锋
- **推荐模式**：DEEP_EXPLORATION (6轮) + SEQUENTIAL处理

### 2. 专家组合分析
分析专家背景的多样性：

**低差异组合**（相似背景）：
- 专家来自相近领域或有相似观点
- **推荐**：BATCH模式（效率优先）

**中等差异组合**（互补背景）：
- 专家有不同但相关的背景
- **推荐**：BATCH模式 + 强化互动提示词

**高差异组合**（冲突背景）：
- 专家有根本性的方法论差异
- **推荐**：SEQUENTIAL模式（保证深度辩论）

### 3. 处理模式选择（BATCH vs SEQUENTIAL）

**优先选择BATCH模式的情况**：
- 问题复杂度为简单或标准
- 专家差异度低到中等
- 用户看重效率
- 问题不需要激烈的观点碰撞

**优先选择SEQUENTIAL模式的情况**：
- 问题复杂度为复杂
- 专家差异度很高，可能产生激烈辩论
- 用户明确要求高质量深度辩论
- 问题涉及重大伦理或价值观冲突

### 4. 综合推荐逻辑

请按以下步骤进行决策：

1. **评估问题复杂度**（简单/标准/复杂）
2. **分析专家差异性**（低/中/高）
3. **考虑用户偏好**（效率/质量/平衡）
4. **选择最佳组合**

## 输出格式
请按以下格式输出你的分析和推荐：

```json
{{
    "question_complexity": "simple/standard/complex",
    "expert_diversity": "low/medium/high",
    "recommended_debate_mode": "quick/standard/deep/batch",
    "recommended_processing_mode": "sequential/batch",
    "reasoning": "详细的推荐理由",
    "alternative_option": "备选方案",
    "confidence_score": 0.85
}}
```

## 质量保证原则
- 复杂问题优先保证质量，选择SEQUENTIAL
- 简单问题优先提高效率，选择BATCH
- 有疑虑时，建议进行A/B测试对比
"""

    @staticmethod
    def analyze_question_complexity(question: str) -> tuple[QuestionComplexity, str]:
        """分析问题复杂度（为Host端提供分析指导）"""

        guidance = f"""
# 问题复杂度分析指导

## 分析目标
对以下问题进行复杂度评估：{question}

## 评估维度

### 1. 领域复杂度
- **简单**：单一领域，概念清晰
- **标准**：跨领域但相关，概念中等复杂
- **复杂**：多领域交叉，概念高度抽象

### 2. 答案确定性
- **简单**：有相对标准或共识的答案
- **标准**：可能有几种合理方案
- **复杂**：答案高度主观，争议很大

### 3. 影响范围
- **简单**：局部影响，短期效应
- **标准**：中等范围影响，中期效应
- **复杂**：系统性影响，长期效应

### 4. 伦理层面
- **简单**：无明显伦理争议
- **标准**：涉及一定伦理考量
- **复杂**：涉及重大伦理冲突

## 分析方法
请逐项评估上述维度，并给出综合判断。

## 输出要求
```json
{{
    "complexity_level": "simple/standard/complex",
    "domain_complexity": "评估结果和理由",
    "answer_certainty": "评估结果和理由",
    "impact_scope": "评估结果和理由",
    "ethical_dimension": "评估结果和理由",
    "overall_reasoning": "综合分析理由"
}}
```
"""
        return QuestionComplexity.STANDARD, guidance

    @staticmethod
    def analyze_expert_diversity(personas: list[dict[str, Any]]) -> tuple[str, str]:
        """分析专家多样性（为Host端提供分析指导）"""

        if not personas or len(personas) < 2:
            return "low", "专家数量不足，无法分析多样性"

        guidance = f"""
# 专家组合多样性分析指导

## 分析目标
评估以下{len(personas)}位专家的组合多样性：

{chr(10).join([f"{i+1}. {p.get('name', '未知')} - {p.get('description', '无描述')}" for i, p in enumerate(personas)])}

## 评估维度

### 1. 知识领域多样性
分析专家的专业背景是否来自不同领域：
- **低**：专家来自同一或相近领域
- **中**：专家来自相关但不同的领域
- **高**：专家来自完全不同的领域

### 2. 方法论差异
分析专家的研究方法和思维方式：
- **低**：使用相似的分析方法
- **中**：方法有差异但可以互补
- **高**：方法论存在根本性差异

### 3. 价值观取向
分析专家的价值观和立场倾向：
- **低**：价值观基本一致
- **中**：有不同但不冲突的价值观
- **高**：存在价值观层面的根本分歧

### 4. 表达风格
分析专家的表达方式和沟通风格：
- **低**：风格相近，容易达成共识
- **中**：风格有差异但能有效沟通
- **高**：风格差异很大，可能产生误解

## 综合评估方法
1. 逐项评估各维度的多样性程度
2. 考虑多样性对辩论质量的影响
3. 给出总体多样性评级

## 输出要求
```json
{{
    "diversity_level": "low/medium/high",
    "domain_diversity": "评估结果和分析",
    "methodology_diversity": "评估结果和分析",
    "value_diversity": "评估结果和分析",
    "style_diversity": "评估结果和分析",
    "impact_on_debate": "多样性对辩论的预期影响",
    "recommendation": "基于多样性的模式推荐"
}}
```
"""
        return "medium", guidance

    @staticmethod
    def get_batch_config_guidance(
        complexity: QuestionComplexity,
        diversity: str,
        user_requirements: str | None = None,
    ) -> str:
        """获取批处理配置的指导原则"""

        return f"""
# 批处理配置优化指导

## 配置目标
基于问题复杂度（{complexity.value}）和专家多样性（{diversity}），优化批处理配置。

## 配置策略

### 1. 质量阈值设置
- **简单问题 + 低多样性**：质量阈值 0.6-0.7（宽松）
- **标准问题 + 中等多样性**：质量阈值 0.7-0.8（标准）
- **复杂问题 + 高多样性**：质量阈值 0.8-0.9（严格）

### 2. 自检机制强度
- **低复杂度**：启用基础自检
- **中等复杂度**：启用增强自检 + 互动检查
- **高复杂度**：启用全面自检 + 多轮验证

### 3. 重试策略
- **效率优先**：最大重试1次
- **平衡模式**：最大重试2次
- **质量优先**：最大重试3次

### 4. 提示词版本选择
- **v1**：基础版本，适合简单问题
- **v2**：增强版本，加强互动要求
- **v3**：高质量版本，最严格的自检要求

## 推荐配置

根据当前情况，推荐以下配置：

```json
{{
    "enable_self_check": true,
    "emphasize_interaction": {True if diversity in ['medium', 'high'] else False},
    "use_virtual_timing": true,
    "quality_threshold": {0.8 if complexity == QuestionComplexity.COMPLEX else 0.7},
    "max_retry_attempts": {3 if complexity == QuestionComplexity.COMPLEX else 2},
    "prompt_version": "{"v3" if complexity == QuestionComplexity.COMPLEX else "v2"}"
}}
```

## 用户需求考虑
{f"用户特殊要求：{user_requirements}" if user_requirements else "无特殊要求"}

## 配置说明
- **启用自检**：确保输出质量
- **强调互动**：适用于专家差异较大的情况
- **虚拟时序**：模拟真实的轮流发言效果
- **质量阈值**：控制输出质量的最低标准
- **重试次数**：平衡效率和质量
- **提示词版本**：匹配问题复杂度的要求
"""

    @staticmethod
    def should_use_ab_testing(
        question_complexity: QuestionComplexity,
        expert_diversity: str,
        user_preference: str | None = None,
    ) -> tuple[bool, str]:
        """判断是否应该进行A/B测试"""

        # 建议A/B测试的情况
        should_test = False
        reasons = []

        if question_complexity == QuestionComplexity.COMPLEX:
            should_test = True
            reasons.append("问题复杂度高，质量差异可能明显")

        if expert_diversity == "high":
            should_test = True
            reasons.append("专家差异度高，辩论深度可能不同")

        if user_preference and "质量" in user_preference:
            should_test = True
            reasons.append("用户明确关注质量")

        # 不建议A/B测试的情况
        if (
            question_complexity == QuestionComplexity.SIMPLE
            and expert_diversity == "low"
        ):
            should_test = False
            reasons = ["问题简单且专家同质性高，批处理模式优势明显"]

        recommendation = "建议进行A/B测试" if should_test else "建议直接使用批处理模式"
        reasoning = "；".join(reasons) if reasons else "无明确指向性"

        guidance = f"""
# A/B测试必要性评估

## 评估结果
**建议**: {recommendation}
**理由**: {reasoning}

## A/B测试指导原则

### 建议进行A/B测试的情况
- 问题复杂度为"复杂"
- 专家多样性为"高"
- 用户明确关注质量胜过效率
- 首次使用系统，需要建立baseline
- 存在较大不确定性

### 可以直接使用批处理的情况
- 问题复杂度为"简单"
- 专家同质性较高
- 用户明确关注效率
- 系统已有充分数据支撑

### A/B测试实施建议
如果决定进行A/B测试：
1. 并行运行序列模式和批处理模式
2. 收集详细的性能指标
3. 进行质量对比分析
4. 根据结果选择最佳模式

## 评估指标
- **时间效率**: 批处理模式预期节省60%时间
- **质量对比**: 重点关注论证深度和互动质量
- **用户满意度**: 最终的实用价值判断
"""

        return should_test, guidance


class ModeRecommendationEngine:
    """模式推荐引擎 - 提供智能推荐逻辑"""

    def __init__(self) -> None:
        self.selector = ModeSelector()

    def get_recommendation_prompt(
        self,
        question: str,
        personas: list[dict[str, Any]] | None = None,
        user_preference: str | None = None,
    ) -> str:
        """获取完整的推荐提示词，供Host端LLM使用"""

        base_guidance = self.selector.get_mode_selection_guidance(
            question, personas, user_preference
        )

        if personas:
            complexity_guidance = self.selector.analyze_question_complexity(question)[1]
            diversity_guidance = self.selector.analyze_expert_diversity(personas)[1]

            return f"""
{base_guidance}

---

{complexity_guidance}

---

{diversity_guidance}

---

## 最终决策流程

请按照以下步骤进行分析和决策：

1. **分析问题复杂度**：使用上述问题复杂度分析指导
2. **评估专家多样性**：使用上述专家多样性分析指导
3. **应用选择框架**：结合复杂度和多样性，使用决策框架
4. **考虑用户偏好**：整合用户的特殊要求
5. **生成最终推荐**：输出具体的模式选择建议

## 输出要求

请提供一个完整的JSON格式推荐报告，包含所有分析步骤和最终建议。
"""
        else:
            return base_guidance

    def create_fallback_recommendation(self) -> dict[str, Any]:
        """创建默认推荐（当无法智能分析时使用）"""
        return {
            "question_complexity": "standard",
            "expert_diversity": "medium",
            "recommended_debate_mode": "standard",
            "recommended_processing_mode": "batch",
            "reasoning": "缺乏足够信息进行详细分析，使用保守的标准配置",
            "alternative_option": "如果对质量有更高要求，可选择sequential模式",
            "confidence_score": 0.6,
            "batch_config": {
                "enable_self_check": True,
                "emphasize_interaction": True,
                "use_virtual_timing": True,
                "quality_threshold": 0.7,
                "max_retry_attempts": 2,
                "prompt_version": "v2",
            },
        }
