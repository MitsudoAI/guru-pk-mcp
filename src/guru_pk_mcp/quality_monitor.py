"""
质量监控和评分系统 - 监控辩论质量并提供评分
"""

from datetime import datetime

from .models import DebateQualityMetrics, PKSession


class DebateQualityAnalyzer:
    """辩论质量分析器 - 简化版，基于基本指标"""

    def __init__(self) -> None:
        # 质量指标权重
        self.weights = {
            "novelty": 0.25,  # 观点新颖度
            "depth": 0.30,  # 论证深度
            "interaction": 0.25,  # 互动质量
            "practicality": 0.20,  # 实用价值
        }

    def analyze_session_quality(self, session: PKSession) -> DebateQualityMetrics:
        """分析整个会话的质量 - 基于基本指标"""
        if not session.responses:
            return DebateQualityMetrics.create_initial()

        # 基于简单指标计算评分
        total_responses = sum(
            len(round_responses) for round_responses in session.responses.values()
        )
        average_length = self._calculate_average_response_length(session)
        round_count = len(session.responses)

        # 基础评分（基于响应数量、长度、轮次等基本指标）
        novelty_score = min(5.0 + (total_responses * 0.3), 10.0)
        depth_score = min(5.0 + (average_length / 100), 10.0)
        interaction_score = min(5.0 + (round_count * 0.8), 10.0)
        practicality_score = min(5.0 + (total_responses * 0.2), 10.0)

        # 计算总体评分
        overall_score = (
            novelty_score * self.weights["novelty"]
            + depth_score * self.weights["depth"]
            + interaction_score * self.weights["interaction"]
            + practicality_score * self.weights["practicality"]
        )

        # 生成基本反馈
        feedback = self._generate_basic_feedback(
            overall_score, total_responses, round_count
        )

        return DebateQualityMetrics(
            novelty_score=novelty_score,
            depth_score=depth_score,
            interaction_score=interaction_score,
            practicality_score=practicality_score,
            overall_score=overall_score,
            feedback=feedback,
            timestamp=datetime.now().isoformat(),
        )

    def _calculate_average_response_length(self, session: PKSession) -> float:
        """计算平均回答长度"""
        total_length = 0
        total_responses = 0

        for round_responses in session.responses.values():
            for response in round_responses.values():
                total_length += len(response)
                total_responses += 1

        return total_length / total_responses if total_responses > 0 else 0

    def _generate_basic_feedback(
        self, overall_score: float, total_responses: int, round_count: int
    ) -> str:
        """生成基本质量反馈"""
        feedback_parts = []

        # 总体评价
        if overall_score >= 8.0:
            feedback_parts.append("🌟 辩论质量优秀")
        elif overall_score >= 6.5:
            feedback_parts.append("✅ 辩论质量良好")
        elif overall_score >= 5.0:
            feedback_parts.append("⚠️ 辩论质量一般")
        else:
            feedback_parts.append("❌ 辩论质量需要改进")

        # 基于基本指标的评价
        if total_responses >= 6:
            feedback_parts.append("专家参与度较高")
        elif total_responses < 3:
            feedback_parts.append("建议增加专家回应")

        if round_count >= 3:
            feedback_parts.append("讨论轮次充分")
        elif round_count < 2:
            feedback_parts.append("建议增加讨论深度")

        return "，".join(feedback_parts)


def get_quality_evaluation_guidance() -> str:
    """获取质量评估指导原则（供MCP Host端LLM使用）"""
    return """
# 辩论质量评估指导原则

## 评估维度

### 1. 观点新颖度 (25%)
- 优秀 (8-10分)：观点独特、有创新性、提供新视角
- 良好 (6-8分)：观点有一定新意、不完全遵循传统思路
- 一般 (4-6分)：观点较为常见、缺乏亮点
- 不足 (0-4分)：观点老套、没有新意

### 2. 论证深度 (30%)
- 优秀 (8-10分)：深入分析、逻辑清晰、有理论支撑
- 良好 (6-8分)：分析较为充分、有一定理论深度
- 一般 (4-6分)：分析较为表面、缺乏深度
- 不足 (0-4分)：分析浅显、逻辑混乱

### 3. 互动质量 (25%)
- 优秀 (8-10分)：专家间积极互动、有效回应、有建设性争论
- 良好 (6-8分)：有一定互动、部分回应其他观点
- 一般 (4-6分)：互动较少、主要是各自表达
- 不足 (0-4分)：缺乏互动、像独立发言

### 4. 实用价值 (20%)
- 优秀 (8-10分)：提供具体可行的解决方案和操作步骤
- 良好 (6-8分)：有一定实用性建议
- 一般 (4-6分)：建议较为抽象、可操作性不强
- 不足 (0-4分)：缺乏实用性建议、纯理论讨论

## 评估原则

### 1. 客观性原则
- 基于内容质量而非个人偏好
- 考虑不同观点的合理性
- 避免立场偏见影响判断

### 2. 全面性原则
- 综合考虑所有维度的表现
- 不因某一方面突出而忽略其他方面
- 平衡理论与实践的价值

### 3. 发展性原则
- 考虑讨论随轮次的发展和深入
- 充分考虑不同阶段的目标和重点
- 认可进步和改善的过程

### 4. 适应性原则
- 根据问题类型调整评估模式
- 考虑参与者的背景和特长
- 适应不同的讨论模式和目标

## 评分标准

### 总体评估
- 优秀 (8.0-10.0)：辩论质量高，各维度表现均衡
- 良好 (6.5-8.0)：辩论质量较好，大部分方面表现不错
- 一般 (5.0-6.5)：辩论质量一般，有提升空间
- 不足 (0-5.0)：辩论质量不足，需要明显改进

### 具体评估指导
- 每个维度都应有具体的评分理由
- 提供建设性的改进建议
- 突出亮点和值得学习的地方
- 指出需要改进的具体方面

## 注意事项

### 评估范围
- 主要评估内容质量和讨论效果
- 不过度关注文字表达和语言风格
- 重点关注观点的价值和贡献

### 评估偏见
- 避免因为个人偏好影响评估
- 不因为观点不同而降低评分
- 公平对待不同风格的表达方式

### 评估反馈
- 提供具体可行的改进建议
- 鼓励正面的方面和亮点
- 保持建设性和指导性的语调
"""


class DebateQualityMonitor:
    """辩论质量监控器 - 提供基本的质量监控框架"""

    def __init__(self) -> None:
        self.analyzer = DebateQualityAnalyzer()
        self.quality_thresholds = {
            "excellent": 8.0,
            "good": 6.5,
            "average": 5.0,
            "poor": 3.5,
        }

    def monitor_session(self, session: PKSession) -> str | None:
        """监控会话质量，返回基本建议"""
        if not session.responses or len(session.responses) < 2:
            return None

        # 分析当前质量
        current_metrics = self.analyzer.analyze_session_quality(session)

        # 更新会话质量指标
        session.update_quality_metrics(current_metrics)

        # 生成基本建议
        suggestions = self._generate_basic_suggestions(current_metrics, session)

        return suggestions

    def _generate_basic_suggestions(
        self, metrics: DebateQualityMetrics, session: PKSession
    ) -> str | None:
        """生成基本的改进建议"""
        suggestions = []

        # 基于轮次进度的简单建议
        if session.current_round == 1:
            suggestions.append("当前是独立思考阶段，建议专家们充分表达自己的观点")
        elif session.current_round == 2:
            suggestions.append("当前是交叉辩论阶段，建议专家们积极互动和回应")
        elif session.current_round == 3:
            suggestions.append("当前是最终阶段，建议专家们总结观点并提供实用建议")
        elif session.current_round == 4:
            suggestions.append("当前是智慧综合阶段，建议整合各方观点形成最终智慧")

        # 基于质量指标的简单建议
        if metrics.overall_score < 5.0:
            suggestions.append("当前讨论质量需要提升，建议增加内容深度和互动频率")
        elif metrics.overall_score >= 8.0:
            suggestions.append("讨论质量较高，建议继续保持当前水平")

        return "；".join(suggestions) if suggestions else None

    def should_extend_debate(self, session: PKSession) -> bool:
        """简单判断是否应该延长辩论"""
        if session.debate_mode.value != "free":
            return False

        # 简单的判断逻辑：轮次较少且未达到最大限制
        return session.current_round < 4 and session.current_round < 6

    def should_end_debate_early(self, session: PKSession) -> bool:
        """简单判断是否应该提前结束辩论"""
        if session.debate_mode.value != "free":
            return False

        # 简单的判断逻辑：至少完成基本轮次
        return session.current_round >= 4


def get_improvement_suggestions_guidance() -> str:
    """获取改进建议指导原则（供MCP Host端LLM使用）"""
    return """
# 辩论改进建议指导原则

## 改进建议类型

### 1. 内容改进建议
- **增加创新性**：提供新颖视角、创新思路、独特见解
- **深化分析**：深入探讨问题根源、内在机制、系统性分析
- **丰富论据**：提供具体案例、数据支撑、实证分析
- **增强实用性**：提供具体建议、可操作步骤、实施方案

### 2. 互动改进建议
- **积极回应**：主动回应其他专家的观点和建议
- **建设性批评**：提出建设性的不同意见和补充
- **观点融合**：尝试结合不同观点的优势
- **深入对话**：就关键问题进行深入交流和讨论

### 3. 结构改进建议
- **逻辑清晰**：理清论证结构、增强论证链条
- **层次分明**：明确区分不同层次的问题和分析
- **重点突出**：突出关键观点和核心建议
- **表达清晰**：提高表达的清晰度和准确性

## 分阶段建议

### 第一轮：独立思考
- 充分表达个人观点和立场
- 提供清晰的问题分析和判断
- 给出初步的解决思路和建议

### 第二轮：交叉辩论
- 积极回应其他专家的观点
- 指出不同意见和需要补充的地方
- 尝试寻找共同点和结合点

### 第三轮：最终立场
- 总结和完善自己的观点
- 吸取其他专家的有益建议
- 提供最终的实用建议和解决方案

### 第四轮：智慧综合
- 整合各方观点的优势
- 形成更加全面和深入的见解
- 提供综合性的实施建议

## 建议原则

### 1. 具体性原则
- 提供具体、可操作的建议
- 避免空泛和抽象的指导
- 给出明确的改进方向

### 2. 建设性原则
- 采用积极正面的语言
- 鼓励和指导并重
- 充分认可已有的优点

### 3. 针对性原则
- 根据具体情况提供对应建议
- 考虑不同专家的特长和背景
- 适应不同阶段的需要和目标

### 4. 平衡性原则
- 平衡各个维度的改进需要
- 不过度偏重某一个方面
- 综合考虑整体效果和平衡

## 实施指导

### 建议表达
- 使用积极正面的语言
- 给出具体的改进建议
- 提供必要的理由和解释

### 优先级排序
- 优先解决最突出的问题
- 先解决影响整体质量的问题
- 再考虑局部优化和细节改进

### 持续改进
- 鼓励持续的反思和改进
- 提供阶段性的改进目标
- 建立持续改进的意识和习惯
"""
