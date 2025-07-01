"""
质量监控和评分系统 - 监控辩论质量并提供评分
"""

import re
from datetime import datetime

from .models import DebateQualityMetrics, PKSession


class DebateQualityAnalyzer:
    """辩论质量分析器"""

    def __init__(self) -> None:
        # 质量指标权重
        self.weights = {
            "novelty": 0.25,  # 观点新颖度
            "depth": 0.30,  # 论证深度
            "interaction": 0.25,  # 互动质量
            "practicality": 0.20,  # 实用价值
        }

        # 新颖度关键词
        self.novelty_indicators = [
            "创新",
            "突破",
            "颠覆",
            "新颖",
            "独特",
            "原创",
            "前所未有",
            "革命性",
            "开创性",
            "与众不同",
            "别出心裁",
            "另辟蹊径",
        ]

        # 深度指标
        self.depth_indicators = [
            "深层",
            "本质",
            "根本",
            "核心",
            "内在",
            "深入",
            "透彻",
            "系统性",
            "全面",
            "详细",
            "具体",
            "深度",
            "深刻",
        ]

        # 互动指标
        self.interaction_indicators = [
            "回应",
            "批评",
            "质疑",
            "补充",
            "完善",
            "借鉴",
            "吸收",
            "反驳",
            "赞同",
            "结合",
            "融合",
            "对话",
            "交流",
        ]

        # 实用性指标
        self.practicality_indicators = [
            "实用",
            "可行",
            "具体",
            "操作",
            "实施",
            "执行",
            "应用",
            "方案",
            "步骤",
            "措施",
            "建议",
            "指导",
            "实际",
        ]

    def analyze_session_quality(self, session: PKSession) -> DebateQualityMetrics:
        """分析整个会话的质量"""
        if not session.responses:
            return DebateQualityMetrics.create_initial()

        # 分析各项指标
        novelty_score = self._analyze_novelty(session)
        depth_score = self._analyze_depth(session)
        interaction_score = self._analyze_interaction(session)
        practicality_score = self._analyze_practicality(session)

        # 计算总体评分
        overall_score = (
            novelty_score * self.weights["novelty"]
            + depth_score * self.weights["depth"]
            + interaction_score * self.weights["interaction"]
            + practicality_score * self.weights["practicality"]
        )

        # 生成反馈
        feedback = self._generate_quality_feedback(
            novelty_score, depth_score, interaction_score, practicality_score
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

    def _analyze_novelty(self, session: PKSession) -> float:
        """分析观点新颖度"""
        novelty_score = 0.0
        total_responses = 0

        for round_responses in session.responses.values():
            for response in round_responses.values():
                response_novelty = self._calculate_text_novelty(response)
                novelty_score += response_novelty
                total_responses += 1

        if total_responses == 0:
            return 5.0

        return min(novelty_score / total_responses, 10.0)

    def _calculate_text_novelty(self, text: str) -> float:
        """计算文本的新颖度评分"""
        text_lower = text.lower()

        # 基础评分
        score = 5.0

        # 检查新颖度关键词
        novelty_keywords_found = sum(
            1 for keyword in self.novelty_indicators if keyword in text_lower
        )
        score += min(novelty_keywords_found * 0.5, 2.0)

        # 检查独特表达
        unique_expressions = self._count_unique_expressions(text)
        score += min(unique_expressions * 0.3, 1.5)

        # 检查创新性思维模式
        if any(
            pattern in text_lower
            for pattern in ["第一性原理", "反向思考", "跨界思维", "系统重构"]
        ):
            score += 1.0

        # 检查具体案例和类比
        if re.search(r"比如|例如|类似|好比|就像", text):
            score += 0.5

        return min(score, 10.0)

    def _count_unique_expressions(self, text: str) -> int:
        """统计独特表达的数量"""
        unique_patterns = [
            r"换句话说",
            r"从另一个角度",
            r"不妨[想想|考虑|试试]",
            r"或许|也许|可能",
            r"突然想到",
            r"有趣的是",
            r"令人惊讶的是",
        ]

        count = 0
        for pattern in unique_patterns:
            if re.search(pattern, text):
                count += 1

        return count

    def _analyze_depth(self, session: PKSession) -> float:
        """分析论证深度"""
        depth_score = 0.0
        total_responses = 0

        for round_responses in session.responses.values():
            for response in round_responses.values():
                response_depth = self._calculate_text_depth(response)
                depth_score += response_depth
                total_responses += 1

        if total_responses == 0:
            return 5.0

        return min(depth_score / total_responses, 10.0)

    def _calculate_text_depth(self, text: str) -> float:
        """计算文本的深度评分"""
        text_lower = text.lower()

        # 基础评分
        score = 5.0

        # 检查深度关键词
        depth_keywords_found = sum(
            1 for keyword in self.depth_indicators if keyword in text_lower
        )
        score += min(depth_keywords_found * 0.4, 2.0)

        # 检查逻辑结构
        logical_structures = self._count_logical_structures(text)
        score += min(logical_structures * 0.5, 1.5)

        # 检查论证深度
        if self._has_multi_layer_reasoning(text):
            score += 1.0

        # 检查具体论据
        evidence_count = self._count_evidence(text)
        score += min(evidence_count * 0.3, 1.0)

        # 文本长度奖励（较长的回答通常更深入）
        length_bonus = min(len(text) / 500, 0.5)
        score += length_bonus

        return min(score, 10.0)

    def _count_logical_structures(self, text: str) -> int:
        """统计逻辑结构数量"""
        structures = [
            r"首先|第一",
            r"其次|第二|然后",
            r"最后|最终|总之",
            r"因为|由于|因此|所以",
            r"但是|然而|不过|可是",
            r"另一方面|与此同时",
            r"综合来看|整体而言",
        ]

        count = 0
        for pattern in structures:
            if re.search(pattern, text):
                count += 1

        return count

    def _has_multi_layer_reasoning(self, text: str) -> bool:
        """检查是否有多层次推理"""
        multi_layer_patterns = [
            r"进一步[说|讲|分析|思考]",
            r"深入[分析|探讨|思考]",
            r"更深层[次|面]的",
            r"背后的[原因|逻辑|机制]",
            r"根本[原因|问题|所在]",
        ]

        return any(re.search(pattern, text) for pattern in multi_layer_patterns)

    def _count_evidence(self, text: str) -> int:
        """统计论据数量"""
        evidence_patterns = [
            r"研究[表明|显示|发现]",
            r"数据[显示|表明]",
            r"例子|案例|实例",
            r"历史[上|经验|教训]",
            r"事实[是|上|证明]",
            r"调查[显示|表明]",
        ]

        count = 0
        for pattern in evidence_patterns:
            count += len(re.findall(pattern, text))

        return count

    def _analyze_interaction(self, session: PKSession) -> float:
        """分析互动质量"""
        if len(session.responses) <= 1:
            return 5.0  # 只有一轮，无法评估互动

        interaction_score = 0.0
        interaction_count = 0

        # 分析第2轮开始的互动质量
        for round_num in range(2, len(session.responses) + 1):
            if round_num in session.responses:
                round_score = self._analyze_round_interaction(session, round_num)
                interaction_score += round_score
                interaction_count += 1

        if interaction_count == 0:
            return 5.0

        return min(interaction_score / interaction_count, 10.0)

    def _analyze_round_interaction(self, session: PKSession, round_num: int) -> float:
        """分析特定轮次的互动质量"""
        current_round = session.responses.get(round_num, {})
        previous_round = session.responses.get(round_num - 1, {})

        if not current_round or not previous_round:
            return 5.0

        interaction_score = 0.0
        response_count = 0

        for persona, response in current_round.items():
            # 检查是否引用了其他专家的观点
            reference_score = self._calculate_reference_score(
                response, previous_round, persona
            )
            interaction_score += reference_score
            response_count += 1

        return interaction_score / response_count if response_count > 0 else 5.0

    def _calculate_reference_score(
        self, response: str, previous_round: dict[str, str], current_persona: str
    ) -> float:
        """计算回应的互动评分"""
        response_lower = response.lower()

        # 基础评分
        score = 5.0

        # 检查互动关键词
        interaction_keywords_found = sum(
            1 for keyword in self.interaction_indicators if keyword in response_lower
        )
        score += min(interaction_keywords_found * 0.5, 2.0)

        # 检查是否引用了其他专家
        other_personas = [
            name for name in previous_round.keys() if name != current_persona
        ]
        references = sum(1 for name in other_personas if name in response)
        score += min(references * 1.0, 2.0)

        # 检查批判性回应
        critical_patterns = [
            r"我认为.*不够",
            r"存在.*问题",
            r"需要.*补充",
            r"忽略了",
            r"过于.*化",
        ]
        critical_responses = sum(
            1 for pattern in critical_patterns if re.search(pattern, response)
        )
        score += min(critical_responses * 0.5, 1.0)

        return min(score, 10.0)

    def _analyze_practicality(self, session: PKSession) -> float:
        """分析实用价值"""
        practicality_score = 0.0
        total_responses = 0

        for round_responses in session.responses.values():
            for response in round_responses.values():
                response_practicality = self._calculate_text_practicality(response)
                practicality_score += response_practicality
                total_responses += 1

        if total_responses == 0:
            return 5.0

        return min(practicality_score / total_responses, 10.0)

    def _calculate_text_practicality(self, text: str) -> float:
        """计算文本的实用性评分"""
        text_lower = text.lower()

        # 基础评分
        score = 5.0

        # 检查实用性关键词
        practicality_keywords_found = sum(
            1 for keyword in self.practicality_indicators if keyword in text_lower
        )
        score += min(practicality_keywords_found * 0.4, 2.0)

        # 检查具体步骤
        steps = self._count_actionable_steps(text)
        score += min(steps * 0.5, 1.5)

        # 检查可操作性
        if self._has_actionable_advice(text):
            score += 1.0

        # 检查具体工具或方法
        tools_mentioned = self._count_tools_and_methods(text)
        score += min(tools_mentioned * 0.3, 1.0)

        return min(score, 10.0)

    def _count_actionable_steps(self, text: str) -> int:
        """统计可执行步骤数量"""
        step_patterns = [
            r"第[一二三四五六七八九十\d]+步",
            r"步骤[一二三四五六七八九十\d]+",
            r"首先.*[，。]",
            r"然后.*[，。]",
            r"接下来.*[，。]",
            r"最后.*[，。]",
        ]

        count = 0
        for pattern in step_patterns:
            count += len(re.findall(pattern, text))

        return count

    def _has_actionable_advice(self, text: str) -> bool:
        """检查是否包含可执行的建议"""
        actionable_patterns = [
            r"建议.*[进行|采用|使用|实施]",
            r"可以[尝试|试试|考虑|采用]",
            r"应该[立即|马上|尽快]",
            r"具体[做法|方法|操作]",
            r"实际[应用|操作|执行]",
        ]

        return any(re.search(pattern, text) for pattern in actionable_patterns)

    def _count_tools_and_methods(self, text: str) -> int:
        """统计提到的工具和方法数量"""
        tool_patterns = [
            r"[工具|方法|技术|系统|平台|软件]",
            r"使用.*[来|进行|实现]",
            r"通过.*[方式|手段|途径]",
            r"借助.*[实现|完成|解决]",
        ]

        count = 0
        for pattern in tool_patterns:
            count += len(re.findall(pattern, text))

        return min(count, 5)  # 限制最大数量

    def _generate_quality_feedback(
        self, novelty: float, depth: float, interaction: float, practicality: float
    ) -> str:
        """生成质量反馈"""
        feedback_parts = []

        # 总体评价
        overall = (novelty + depth + interaction + practicality) / 4
        if overall >= 8.0:
            feedback_parts.append("🌟 辩论质量优秀")
        elif overall >= 6.5:
            feedback_parts.append("✅ 辩论质量良好")
        elif overall >= 5.0:
            feedback_parts.append("⚠️ 辩论质量一般")
        else:
            feedback_parts.append("❌ 辩论质量需要改进")

        # 各项具体评价
        if novelty >= 7.5:
            feedback_parts.append("观点新颖独特")
        elif novelty < 5.0:
            feedback_parts.append("缺乏创新思维")

        if depth >= 7.5:
            feedback_parts.append("论证深入透彻")
        elif depth < 5.0:
            feedback_parts.append("分析深度不够")

        if interaction >= 7.5:
            feedback_parts.append("专家互动充分")
        elif interaction < 5.0:
            feedback_parts.append("缺乏有效互动")

        if practicality >= 7.5:
            feedback_parts.append("建议实用可行")
        elif practicality < 5.0:
            feedback_parts.append("实用性有待提升")

        return "，".join(feedback_parts)


class DebateQualityMonitor:
    """辩论质量监控器"""

    def __init__(self) -> None:
        self.analyzer = DebateQualityAnalyzer()
        self.quality_thresholds = {
            "excellent": 8.0,
            "good": 6.5,
            "average": 5.0,
            "poor": 3.5,
        }

    def monitor_session(self, session: PKSession) -> str | None:
        """监控会话质量，返回建议"""
        if not session.responses or len(session.responses) < 2:
            return None

        # 分析当前质量
        current_metrics = self.analyzer.analyze_session_quality(session)

        # 更新会话质量指标
        session.update_quality_metrics(current_metrics)

        # 生成改进建议
        suggestions = self._generate_improvement_suggestions(current_metrics, session)

        return suggestions

    def _generate_improvement_suggestions(
        self, metrics: DebateQualityMetrics, session: PKSession
    ) -> str | None:
        """生成改进建议"""
        suggestions = []

        # 基于当前质量指标生成建议
        if metrics.novelty_score < 6.0:
            suggestions.append("建议专家们提供更多创新性观点和独特见解")

        if metrics.depth_score < 6.0:
            suggestions.append("建议深入分析问题的根本原因和内在机制")

        if metrics.interaction_score < 6.0:
            suggestions.append("建议专家们更多地回应和批评其他人的观点")

        if metrics.practicality_score < 6.0:
            suggestions.append("建议提供更多具体可行的解决方案和操作步骤")

        # 基于轮次进度给出建议
        if session.current_round == 2 and metrics.interaction_score < 5.0:
            suggestions.append("当前是交叉辩论阶段，建议专家们积极回应其他人的观点")

        if (
            session.current_round == session.max_rounds - 1
            and metrics.practicality_score < 6.0
        ):
            suggestions.append("即将进入最终阶段，建议专家们提供更多实用性建议")

        # 动态轮次调整建议（自由辩论模式）
        if session.debate_mode.value == "free":
            if metrics.overall_score < 5.0 and session.current_round >= 3:
                suggestions.append("建议增加轮次，以提升讨论质量")
            elif metrics.overall_score >= 8.0 and session.current_round >= 2:
                suggestions.append("讨论质量已达到优秀水平，可考虑提前结束")

        return "；".join(suggestions) if suggestions else None

    def should_extend_debate(self, session: PKSession) -> bool:
        """判断是否应该延长辩论"""
        if session.debate_mode.value != "free":
            return False

        if not session.quality_metrics:
            return False

        # 质量不足且未达到最大轮数时，建议延长
        return session.quality_metrics.overall_score < 6.0 and session.current_round < 6

    def should_end_debate_early(self, session: PKSession) -> bool:
        """判断是否应该提前结束辩论"""
        if session.debate_mode.value != "free":
            return False

        if not session.quality_metrics:
            return False

        # 质量优秀且至少完成2轮时，可以提前结束
        return (
            session.quality_metrics.overall_score >= 8.5 and session.current_round >= 2
        )
