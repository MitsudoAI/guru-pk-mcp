"""
动态专家生成引擎 - 智能专家推荐和生成系统
"""

import re
from datetime import datetime
from typing import Any

from .models import (
    DebateMode,
    ExpertProfile,
    ExpertRecommendation,
    QuestionComplexity,
    QuestionProfile,
)
from .personas import PERSONAS


class QuestionAnalyzer:
    """问题分析器 - 分析问题特征和复杂度"""

    def __init__(self) -> None:
        # 领域关键词映射
        self.domain_keywords = {
            "哲学": [
                "哲学",
                "思辨",
                "本质",
                "存在",
                "真理",
                "伦理",
                "道德",
                "人生",
                "意义",
            ],
            "商业": [
                "商业",
                "创业",
                "投资",
                "经营",
                "企业",
                "管理",
                "商务",
                "市场",
                "营销",
            ],
            "技术": [
                "技术",
                "软件",
                "系统",
                "架构",
                "开发",
                "编程",
                "AI",
                "算法",
                "数据",
            ],
            "心理": [
                "心理",
                "情绪",
                "认知",
                "焦虑",
                "压力",
                "抑郁",
                "成长",
                "治疗",
                "咨询",
            ],
            "教育": [
                "教育",
                "学习",
                "教学",
                "学生",
                "课程",
                "培训",
                "知识",
                "技能",
                "成长",
            ],
            "科学": [
                "科学",
                "研究",
                "实验",
                "理论",
                "方法",
                "证据",
                "假设",
                "验证",
                "分析",
            ],
            "经济": [
                "经济",
                "金融",
                "货币",
                "通胀",
                "市场",
                "价格",
                "供需",
                "政策",
                "宏观",
            ],
            "战略": [
                "战略",
                "策略",
                "规划",
                "目标",
                "竞争",
                "优势",
                "资源",
                "布局",
                "决策",
            ],
            "创新": [
                "创新",
                "发明",
                "突破",
                "改进",
                "优化",
                "变革",
                "颠覆",
                "新颖",
                "原创",
            ],
            "系统": [
                "系统",
                "复杂",
                "关系",
                "结构",
                "网络",
                "整体",
                "协调",
                "平衡",
                "反馈",
            ],
        }

        # 复杂度关键词
        self.complexity_indicators = {
            "high": ["复杂", "系统性", "多维", "深层", "战略", "长期", "整体", "综合"],
            "low": ["简单", "直接", "明确", "具体", "基础", "入门", "快速", "立即"],
        }

        # 思维模式关键词
        self.thinking_modes = {
            "批判性思维": ["质疑", "分析", "批判", "逻辑", "推理", "论证"],
            "创新思维": ["创新", "创造", "突破", "颠覆", "新颖", "原创"],
            "系统思维": ["系统", "整体", "关系", "结构", "平衡", "协调"],
            "实用思维": ["实用", "实际", "可行", "操作", "具体", "实施"],
            "哲学思维": ["本质", "根本", "深层", "哲学", "思辨", "理性"],
        }

    def analyze_question(self, question: str) -> QuestionProfile:
        """分析问题，生成问题档案"""
        question_lower = question.lower()

        # 分析涉及的领域
        domains = self._extract_domains(question_lower)

        # 判断复杂度
        complexity = self._assess_complexity(question_lower)

        # 提取所需专业知识
        required_expertise = self._extract_required_expertise(question_lower, domains)

        # 识别所需思维模式
        thinking_modes = self._identify_thinking_modes(question_lower)

        # 推荐辩论模式
        debate_mode = self._recommend_debate_mode(complexity, len(domains))

        # 提取关键词
        keywords = self._extract_keywords(question)

        # 确定预期轮数
        expected_rounds = {
            DebateMode.QUICK_CONSULTATION: 2,
            DebateMode.STANDARD_DEBATE: 4,
            DebateMode.DEEP_EXPLORATION: 6,
            DebateMode.FREE_DEBATE: 4,
        }.get(debate_mode, 4)

        return QuestionProfile(
            question=question,
            domains=domains,
            complexity=complexity,
            required_expertise=required_expertise,
            thinking_modes=thinking_modes,
            debate_mode=debate_mode,
            analysis_timestamp=datetime.now().isoformat(),
            keywords=keywords,
            expected_rounds=expected_rounds,
        )

    def _extract_domains(self, question_lower: str) -> list[str]:
        """提取问题涉及的领域"""
        detected_domains = []

        for domain, keywords in self.domain_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                detected_domains.append(domain)

        # 如果没有检测到特定领域，标记为通用
        if not detected_domains:
            detected_domains = ["通用"]

        return detected_domains

    def _assess_complexity(self, question_lower: str) -> QuestionComplexity:
        """评估问题复杂度"""
        high_complexity_score = sum(
            1
            for keyword in self.complexity_indicators["high"]
            if keyword in question_lower
        )

        low_complexity_score = sum(
            1
            for keyword in self.complexity_indicators["low"]
            if keyword in question_lower
        )

        # 问题长度也是复杂度的指标
        length_complexity = len(question_lower) > 50

        # 问号数量（多个问题通常更复杂）
        question_marks = question_lower.count("?") + question_lower.count("？")

        if (
            high_complexity_score > low_complexity_score
            or length_complexity
            or question_marks > 1
        ):
            return QuestionComplexity.COMPLEX
        elif low_complexity_score > 0:
            return QuestionComplexity.SIMPLE
        else:
            return QuestionComplexity.STANDARD

    def _extract_required_expertise(
        self, question_lower: str, domains: list[str]
    ) -> list[str]:
        """根据领域和问题内容提取所需专业知识"""
        expertise = []

        # 基于检测到的领域添加相应专业知识
        domain_expertise_map = {
            "哲学": ["哲学思辨", "伦理学", "认识论"],
            "商业": ["商业战略", "企业管理", "市场营销"],
            "技术": ["系统架构", "软件工程", "技术创新"],
            "心理": ["心理学", "认知科学", "行为分析"],
            "教育": ["教育学", "学习理论", "教学方法"],
            "科学": ["科学方法", "研究方法", "实验设计"],
            "经济": ["经济学", "金融学", "市场分析"],
            "战略": ["战略规划", "竞争分析", "决策理论"],
            "创新": ["创新管理", "产品设计", "技术转化"],
            "系统": ["系统论", "复杂性科学", "系统工程"],
        }

        for domain in domains:
            if domain in domain_expertise_map:
                expertise.extend(domain_expertise_map[domain])

        return list(set(expertise))  # 去重

    def _identify_thinking_modes(self, question_lower: str) -> list[str]:
        """识别问题所需的思维模式"""
        detected_modes = []

        for mode, keywords in self.thinking_modes.items():
            if any(keyword in question_lower for keyword in keywords):
                detected_modes.append(mode)

        # 默认思维模式
        if not detected_modes:
            detected_modes = ["批判性思维", "实用思维"]

        return detected_modes

    def _recommend_debate_mode(
        self, complexity: QuestionComplexity, domain_count: int
    ) -> DebateMode:
        """推荐辩论模式"""
        if complexity == QuestionComplexity.SIMPLE and domain_count <= 1:
            return DebateMode.QUICK_CONSULTATION
        elif complexity == QuestionComplexity.COMPLEX or domain_count > 2:
            return DebateMode.DEEP_EXPLORATION
        else:
            return DebateMode.STANDARD_DEBATE

    def _extract_keywords(self, question: str) -> list[str]:
        """提取问题关键词"""
        # 简化的关键词提取：去除停用词，提取主要词汇
        stop_words = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "你",
            "他",
            "她",
            "它",
            "们",
            "这",
            "那",
            "和",
            "与",
            "或",
            "但",
            "而",
        }

        # 使用正则表达式提取中文词汇和英文单词
        words = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]+", question)

        keywords = [word for word in words if len(word) > 1 and word not in stop_words]

        return list(set(keywords))[:10]  # 最多返回10个关键词


class ExpertGenerator:
    """专家生成器 - 生成专家推荐和创建动态专家"""

    def __init__(self, custom_persona_manager: Any = None) -> None:
        self.custom_persona_manager = custom_persona_manager
        self.question_analyzer = QuestionAnalyzer()

    def generate_expert_recommendation(
        self, question: str, num_experts: int = 5
    ) -> ExpertRecommendation:
        """生成专家推荐"""
        # 分析问题
        question_profile = self.question_analyzer.analyze_question(question)

        # 获取所有可用专家
        all_experts = self._get_all_available_experts()

        # 计算专家相关性评分
        scored_experts = self._score_experts_relevance(all_experts, question_profile)

        # 选择多样化的专家组合
        selected_experts = self._select_diverse_experts(scored_experts, num_experts)

        # 生成推荐理由和预期视角
        reason, perspectives = self._generate_recommendation_details(
            selected_experts, question_profile
        )

        return ExpertRecommendation.create_recommendation(
            experts=selected_experts,
            question_profile=question_profile,
            reason=reason,
            perspectives=perspectives,
        )

    def _get_all_available_experts(self) -> list[ExpertProfile]:
        """获取所有可用专家（内置+自定义）"""
        experts = []

        # 添加内置专家
        for persona_data in PERSONAS.values():
            expert = ExpertProfile.from_builtin_persona(persona_data)
            experts.append(expert)

        # 添加自定义专家
        if self.custom_persona_manager:
            custom_personas = self.custom_persona_manager.list_custom_personas()
            for persona_data in custom_personas:
                expert = ExpertProfile.from_custom_persona(persona_data)
                experts.append(expert)

        return experts

    def _score_experts_relevance(
        self, experts: list[ExpertProfile], question_profile: QuestionProfile
    ) -> list[tuple[ExpertProfile, float]]:
        """计算专家与问题的相关性评分"""
        scored_experts = []

        for expert in experts:
            score = self._calculate_relevance_score(expert, question_profile)
            expert.relevance_score = score
            scored_experts.append((expert, score))

        # 按相关性排序
        scored_experts.sort(key=lambda x: x[1], reverse=True)

        return scored_experts

    def _calculate_relevance_score(
        self, expert: ExpertProfile, question_profile: QuestionProfile
    ) -> float:
        """计算单个专家的相关性评分"""
        score = 0.0

        # 领域匹配分数 (权重: 0.4)
        domain_score = self._calculate_domain_score(expert, question_profile.domains)
        score += domain_score * 0.4

        # 关键词匹配分数 (权重: 0.3)
        keyword_score = self._calculate_keyword_score(expert, question_profile.keywords)
        score += keyword_score * 0.3

        # 思维模式匹配分数 (权重: 0.2)
        thinking_score = self._calculate_thinking_score(
            expert, question_profile.thinking_modes
        )
        score += thinking_score * 0.2

        # 基础相关性分数 (权重: 0.1)
        base_score = expert.relevance_score or 0.5
        score += base_score * 0.1

        return min(score, 1.0)  # 限制在0-1范围内

    def _calculate_domain_score(
        self, expert: ExpertProfile, question_domains: list[str]
    ) -> float:
        """计算领域匹配分数"""
        if not expert.knowledge_domains or not question_domains:
            return 0.3  # 默认分数

        # 检查直接匹配
        matches = len(set(expert.knowledge_domains) & set(question_domains))
        if matches > 0:
            return min(matches / len(question_domains), 1.0)

        # 检查相关领域
        related_domains = {
            "哲学": ["心理", "教育"],
            "商业": ["经济", "战略", "创新"],
            "技术": ["创新", "系统"],
            "心理": ["哲学", "教育"],
            "教育": ["心理", "哲学"],
            "科学": ["系统", "技术"],
            "经济": ["商业", "战略"],
            "战略": ["商业", "经济"],
            "创新": ["技术", "商业"],
            "系统": ["科学", "技术"],
        }

        for expert_domain in expert.knowledge_domains:
            for question_domain in question_domains:
                if question_domain in related_domains.get(expert_domain, []):
                    return 0.6

        return 0.1

    def _calculate_keyword_score(
        self, expert: ExpertProfile, question_keywords: list[str]
    ) -> float:
        """计算关键词匹配分数"""
        if not question_keywords:
            return 0.5

        expert_text = f"{expert.description} {expert.thinking_style} {' '.join(expert.personality_traits)}"
        expert_text_lower = expert_text.lower()

        matches = sum(
            1 for keyword in question_keywords if keyword.lower() in expert_text_lower
        )

        return min(matches / len(question_keywords), 1.0)

    def _calculate_thinking_score(
        self, expert: ExpertProfile, thinking_modes: list[str]
    ) -> float:
        """计算思维模式匹配分数"""
        if not thinking_modes:
            return 0.5

        expert_thinking = f"{expert.thinking_style} {expert.debate_strategy}".lower()

        mode_keywords = {
            "批判性思维": ["批判", "质疑", "分析", "逻辑"],
            "创新思维": ["创新", "创造", "突破", "颠覆"],
            "系统思维": ["系统", "整体", "关系", "结构"],
            "实用思维": ["实用", "实际", "可行", "操作"],
            "哲学思维": ["哲学", "思辨", "本质", "理性"],
        }

        matches = 0
        for mode in thinking_modes:
            if mode in mode_keywords:
                keywords = mode_keywords[mode]
                if any(keyword in expert_thinking for keyword in keywords):
                    matches += 1

        return min(matches / len(thinking_modes), 1.0) if thinking_modes else 0.5

    def _select_diverse_experts(
        self, scored_experts: list[tuple[ExpertProfile, float]], num_experts: int
    ) -> list[ExpertProfile]:
        """选择多样化的专家组合"""
        if len(scored_experts) <= num_experts:
            return [expert for expert, _ in scored_experts]

        selected = []
        remaining = scored_experts.copy()

        # 优先选择高分专家
        selected.append(remaining.pop(0)[0])

        # 选择剩余专家，保证多样性
        while len(selected) < num_experts and remaining:
            best_candidate = None
            best_diversity_score = -1.0
            best_index = -1

            for i, (candidate, relevance_score) in enumerate(remaining):
                diversity_score = self._calculate_diversity_score(selected, candidate)
                # 综合相关性和多样性
                combined_score = relevance_score * 0.6 + diversity_score * 0.4

                if combined_score > best_diversity_score:
                    best_diversity_score = float(combined_score)
                    best_candidate = candidate
                    best_index = i

            if best_candidate:
                selected.append(best_candidate)
                remaining.pop(best_index)

        return selected

    def _calculate_diversity_score(
        self, selected: list[ExpertProfile], candidate: ExpertProfile
    ) -> float:
        """计算候选专家与已选专家的多样性分数"""
        if not selected:
            return 1.0

        diversity_score = 0.0

        for expert in selected:
            # 来源多样性
            if expert.source != candidate.source:
                diversity_score += 0.3

            # 领域多样性
            common_domains = set(expert.knowledge_domains) & set(
                candidate.knowledge_domains
            )
            domain_diversity = 1.0 - (
                len(common_domains)
                / max(
                    len(expert.knowledge_domains), len(candidate.knowledge_domains), 1
                )
            )
            diversity_score += domain_diversity * 0.4

            # 特质多样性
            common_traits = set(expert.personality_traits) & set(
                candidate.personality_traits
            )
            trait_diversity = 1.0 - (
                len(common_traits)
                / max(
                    len(expert.personality_traits), len(candidate.personality_traits), 1
                )
            )
            diversity_score += trait_diversity * 0.3

        return diversity_score / len(selected)

    def _generate_recommendation_details(
        self, experts: list[ExpertProfile], question_profile: QuestionProfile
    ) -> tuple[str, list[str]]:
        """生成推荐理由和预期视角"""
        # 生成推荐理由
        domain_str = "、".join(question_profile.domains)
        complexity_str = {
            QuestionComplexity.SIMPLE: "简单",
            QuestionComplexity.STANDARD: "标准",
            QuestionComplexity.COMPLEX: "复杂",
        }.get(question_profile.complexity, "标准")

        reason = f"针对{domain_str}领域的{complexity_str}问题，推荐以下专家组合："

        # 分析专家来源分布
        sources = [expert.source for expert in experts]
        source_counts = {
            "builtin": sources.count("builtin"),
            "custom": sources.count("custom"),
            "generated": sources.count("generated"),
        }

        if source_counts["builtin"] > 0:
            reason += f" {source_counts['builtin']}位经典思想家"
        if source_counts["custom"] > 0:
            reason += f" {source_counts['custom']}位自定义专家"
        if source_counts["generated"] > 0:
            reason += f" {source_counts['generated']}位智能生成专家"

        reason += "，确保观点多样性和专业深度的最佳平衡。"

        # 生成预期视角
        perspectives = []
        for expert in experts:
            if expert.thinking_style:
                perspective = f"{expert.name}将从{expert.thinking_style}的角度分析问题"
                if expert.knowledge_domains:
                    main_domain = (
                        expert.knowledge_domains[0] if expert.knowledge_domains else ""
                    )
                    if main_domain:
                        perspective += f"，运用{main_domain}的专业知识"
                perspectives.append(perspective)

        return reason, perspectives


class ExpertRelationshipAnalyzer:
    """专家关系分析器 - 分析专家间的潜在关系和冲突点"""

    def analyze_expert_relationships(
        self, experts: list[ExpertProfile]
    ) -> dict[str, list[str]]:
        """分析专家关系图谱"""
        relationships: dict[str, list[str]] = {}

        for expert in experts:
            relationships[expert.name] = []

        # 分析两两关系
        for i, expert1 in enumerate(experts):
            for j, expert2 in enumerate(experts):
                if i >= j:  # 避免重复分析
                    continue

                # 简化关系分析 - 所有相关专家都添加到关系列表中
                relationships[expert1.name].append(expert2.name)
                relationships[expert2.name].append(expert1.name)

        return relationships

    def _analyze_pairwise_relationship(
        self, expert1: ExpertProfile, expert2: ExpertProfile
    ) -> str:
        """分析两个专家之间的关系类型"""
        # 基于领域相似性
        domain_overlap = len(
            set(expert1.knowledge_domains) & set(expert2.knowledge_domains)
        )
        domain_similarity = domain_overlap / max(
            len(expert1.knowledge_domains), len(expert2.knowledge_domains), 1
        )

        # 基于特质相似性
        trait_overlap = len(
            set(expert1.personality_traits) & set(expert2.personality_traits)
        )
        trait_similarity = trait_overlap / max(
            len(expert1.personality_traits), len(expert2.personality_traits), 1
        )

        # 基于思维风格分析
        thinking_compatibility = self._analyze_thinking_compatibility(expert1, expert2)

        # 综合判断
        if domain_similarity > 0.6 and trait_similarity > 0.5:
            return "ally"
        elif thinking_compatibility == "conflicting":
            return "opponent"
        else:
            return "complementary"

    def _analyze_thinking_compatibility(
        self, expert1: ExpertProfile, expert2: ExpertProfile
    ) -> str:
        """分析思维风格兼容性"""
        # 对立思维模式
        conflicting_styles = [
            ("理论", "实践"),
            ("保守", "激进"),
            ("直觉", "逻辑"),
            ("个人", "集体"),
            ("传统", "创新"),
        ]

        style1 = expert1.thinking_style.lower()
        style2 = expert2.thinking_style.lower()

        for style_a, style_b in conflicting_styles:
            if (style_a in style1 and style_b in style2) or (
                style_b in style1 and style_a in style2
            ):
                return "conflicting"

        return "compatible"
