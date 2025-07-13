"""
数据模型定义
"""

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class DebateMode(Enum):
    """辩论模式枚举"""

    QUICK_CONSULTATION = "quick"  # 快速咨询模式 (2轮)
    STANDARD_DEBATE = "standard"  # 标准辩论模式 (4轮)
    DEEP_EXPLORATION = "deep"  # 深度探讨模式 (6轮)
    FREE_DEBATE = "free"  # 自由辩论模式 (用户控制)
    BATCH_OPTIMIZED = "batch"  # 批处理优化模式 (4轮，但使用批处理提示词)


class QuestionComplexity(Enum):
    """问题复杂度枚举"""

    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"


class ProcessingMode(Enum):
    """处理模式枚举"""

    SEQUENTIAL = "sequential"  # 序列模式：逐个专家发言
    BATCH = "batch"  # 批处理模式：专家并发发言


@dataclass
class BatchConfig:
    """批处理模式配置"""

    enable_self_check: bool = True  # 启用自检机制
    emphasize_interaction: bool = True  # 强调专家互动
    use_virtual_timing: bool = True  # 使用虚拟时序
    quality_threshold: float = 0.7  # 质量阈值
    max_retry_attempts: int = 1  # 最大重试次数
    prompt_version: str = "v1"  # 提示词版本

    @classmethod
    def create_default(cls) -> "BatchConfig":
        """创建默认配置"""
        return cls()

    @classmethod
    def create_high_quality(cls) -> "BatchConfig":
        """创建高质量配置"""
        return cls(
            enable_self_check=True,
            emphasize_interaction=True,
            use_virtual_timing=True,
            quality_threshold=0.8,
            max_retry_attempts=2,
            prompt_version="v2",
        )


@dataclass
class ABTestResult:
    """A/B测试结果"""

    test_id: str
    question: str
    personas: list[str]

    # 序列模式结果
    sequential_result: dict[str, Any]
    sequential_time: float
    sequential_token_count: int
    sequential_quality_score: float

    # 批处理模式结果
    batch_result: dict[str, Any]
    batch_time: float
    batch_token_count: int
    batch_quality_score: float

    # 比较指标
    time_improvement: float  # 时间提升百分比
    token_efficiency: float  # Token效率
    quality_delta: float  # 质量差异

    # 元数据
    test_timestamp: str
    llm_model: str
    batch_config: BatchConfig

    @classmethod
    def create_test_result(
        cls,
        question: str,
        personas: list[str],
        sequential_data: dict[str, Any],
        batch_data: dict[str, Any],
        batch_config: BatchConfig,
    ) -> "ABTestResult":
        """创建测试结果"""

        seq_time = sequential_data.get("execution_time", 0.0)
        batch_time = batch_data.get("execution_time", 0.0)

        time_improvement = (
            ((seq_time - batch_time) / seq_time * 100) if seq_time > 0 else 0.0
        )

        seq_tokens = sequential_data.get("token_count", 0)
        batch_tokens = batch_data.get("token_count", 0)
        token_efficiency = (seq_tokens / batch_tokens) if batch_tokens > 0 else 1.0

        seq_quality = sequential_data.get("quality_score", 5.0)
        batch_quality = batch_data.get("quality_score", 5.0)
        quality_delta = batch_quality - seq_quality

        return cls(
            test_id=str(uuid.uuid4())[:8],
            question=question,
            personas=personas,
            sequential_result=sequential_data,
            sequential_time=seq_time,
            sequential_token_count=seq_tokens,
            sequential_quality_score=seq_quality,
            batch_result=batch_data,
            batch_time=batch_time,
            batch_token_count=batch_tokens,
            batch_quality_score=batch_quality,
            time_improvement=time_improvement,
            token_efficiency=token_efficiency,
            quality_delta=quality_delta,
            test_timestamp=datetime.now().isoformat(),
            llm_model=batch_data.get("model", "unknown"),
            batch_config=batch_config,
        )


@dataclass
class QuestionProfile:
    """问题分析档案"""

    question: str
    domains: list[str]  # 涉及的领域
    complexity: QuestionComplexity
    required_expertise: list[str]  # 需要的专业知识
    thinking_modes: list[str]  # 需要的思维模式
    debate_mode: DebateMode  # 推荐的辩论模式
    analysis_timestamp: str
    keywords: list[str]  # 关键词
    expected_rounds: int  # 预期轮数

    @classmethod
    def create_from_question(cls, question: str) -> "QuestionProfile":
        """从问题创建档案（简化版，实际会由智能分析生成）"""
        return cls(
            question=question,
            domains=["通用"],
            complexity=QuestionComplexity.STANDARD,
            required_expertise=[],
            thinking_modes=[],
            debate_mode=DebateMode.STANDARD_DEBATE,
            analysis_timestamp=datetime.now().isoformat(),
            keywords=[],
            expected_rounds=4,
        )


@dataclass
class ExpertProfile:
    """专家档案（动态生成）"""

    name: str
    emoji: str
    description: str
    background: str  # 专业背景
    thinking_style: str  # 思维特征
    debate_strategy: str  # 辩论策略
    knowledge_domains: list[str]  # 知识领域
    personality_traits: list[str]  # 个性特质
    potential_biases: list[str]  # 潜在偏见
    source: str  # 来源（"generated" - 动态生成）
    base_prompt: str  # 基础提示词
    generation_timestamp: str | None = None  # 生成时间戳
    relevance_score: float | None = None  # 与问题的相关性评分

    @classmethod
    def create_generated_expert(cls, expert_data: dict[str, Any]) -> "ExpertProfile":
        """创建智能生成的专家档案"""
        return cls(
            name=expert_data["name"],
            emoji=expert_data.get("emoji", "🤖"),
            description=expert_data["description"],
            background=expert_data["background"],
            thinking_style=expert_data["thinking_style"],
            debate_strategy=expert_data["debate_strategy"],
            knowledge_domains=expert_data["knowledge_domains"],
            personality_traits=expert_data["personality_traits"],
            potential_biases=expert_data["potential_biases"],
            source="generated",
            base_prompt=expert_data["base_prompt"],
            generation_timestamp=datetime.now().isoformat(),
            relevance_score=expert_data.get("relevance_score", 0.9),
        )


@dataclass
class ExpertRecommendation:
    """专家推荐结果"""

    experts: list[ExpertProfile]  # 推荐的专家列表（通常5个）
    recommendation_reason: str  # 推荐理由
    expected_perspectives: list[str]  # 预期视角
    question_profile: QuestionProfile  # 问题档案
    diversity_score: float  # 多样性评分
    relevance_score: float  # 相关性评分
    generation_timestamp: str

    @classmethod
    def create_recommendation(
        cls,
        experts: list[ExpertProfile],
        question_profile: QuestionProfile,
        reason: str = "",
        perspectives: list[str] | None = None,
    ) -> "ExpertRecommendation":
        """创建专家推荐"""
        if perspectives is None:
            perspectives = []

        return cls(
            experts=experts,
            recommendation_reason=reason,
            expected_perspectives=perspectives,
            question_profile=question_profile,
            diversity_score=cls._calculate_diversity_score(experts),
            relevance_score=cls._calculate_relevance_score(experts),
            generation_timestamp=datetime.now().isoformat(),
        )

    @staticmethod
    def _calculate_diversity_score(experts: list[ExpertProfile]) -> float:
        """计算专家组合的多样性评分"""
        if not experts:
            return 0.0

        # 基于不同知识领域和思维风格的多样性计算
        domains = {domain for expert in experts for domain in expert.knowledge_domains}
        thinking_styles = {expert.thinking_style for expert in experts}

        domain_diversity = min(len(domains) / len(experts), 1.0)
        style_diversity = len(thinking_styles) / len(experts)

        return (domain_diversity + style_diversity) / 2

    @staticmethod
    def _calculate_relevance_score(experts: list[ExpertProfile]) -> float:
        """计算专家组合的相关性评分"""
        if not experts:
            return 0.0

        scores = [expert.relevance_score or 0.5 for expert in experts]
        return sum(scores) / len(scores)


@dataclass
class DebateQualityMetrics:
    """辩论质量指标"""

    novelty_score: float  # 观点新颖度 (0-10)
    depth_score: float  # 论证深度 (0-10)
    interaction_score: float  # 互动质量 (0-10)
    practicality_score: float  # 实用价值 (0-10)
    overall_score: float  # 总体评分 (0-10)
    feedback: str  # 质量反馈
    timestamp: str

    @classmethod
    def create_initial(cls) -> "DebateQualityMetrics":
        """创建初始质量指标"""
        return cls(
            novelty_score=5.0,
            depth_score=5.0,
            interaction_score=5.0,
            practicality_score=5.0,
            overall_score=5.0,
            feedback="辩论刚开始，暂无评分",
            timestamp=datetime.now().isoformat(),
        )


@dataclass
class PKSession:
    """PK会话数据模型"""

    session_id: str
    user_question: str
    selected_personas: list[str]
    current_round: int
    current_persona_index: int
    responses: dict[int, dict[str, str]]  # {round: {persona: response}}
    final_synthesis: str | None
    created_at: str
    updated_at: str

    # 新增字段：支持动态专家系统
    question_profile: QuestionProfile | None = None
    expert_profiles: dict[str, ExpertProfile] | None = None  # {persona_name: profile}
    expert_recommendation: ExpertRecommendation | None = None
    debate_mode: DebateMode = DebateMode.STANDARD_DEBATE
    max_rounds: int = 4
    quality_metrics: DebateQualityMetrics | None = None
    is_recommended_by_host: bool = False  # 是否由Host端智能推荐
    expert_relationships: dict[str, list[str]] | None = None  # 专家关系图谱

    # 批处理模式支持
    processing_mode: ProcessingMode = ProcessingMode.SEQUENTIAL
    batch_config: BatchConfig | None = None
    ab_test_result: ABTestResult | None = None

    @classmethod
    def create_new(
        cls,
        user_question: str,
        selected_personas: list[str],
        debate_mode: DebateMode = DebateMode.STANDARD_DEBATE,
        question_profile: QuestionProfile | None = None,
        expert_recommendation: ExpertRecommendation | None = None,
        is_recommended_by_host: bool = False,
    ) -> "PKSession":
        """创建新的PK会话"""
        now = datetime.now().isoformat()
        max_rounds = {
            DebateMode.QUICK_CONSULTATION: 2,
            DebateMode.STANDARD_DEBATE: 4,
            DebateMode.DEEP_EXPLORATION: 6,
            DebateMode.FREE_DEBATE: 4,  # 默认4轮，可动态调整
            DebateMode.BATCH_OPTIMIZED: 4,  # 批处理模式也是4轮
        }.get(debate_mode, 4)

        return cls(
            session_id=str(uuid.uuid4())[:8],
            user_question=user_question,
            selected_personas=selected_personas,
            current_round=1,
            current_persona_index=0,
            responses={},
            final_synthesis=None,
            created_at=now,
            updated_at=now,
            question_profile=question_profile,
            expert_profiles=None,
            expert_recommendation=expert_recommendation,
            debate_mode=debate_mode,
            max_rounds=max_rounds,
            quality_metrics=DebateQualityMetrics.create_initial(),
            is_recommended_by_host=is_recommended_by_host,
            expert_relationships=None,
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = asdict(self)

        # 处理枚举类型序列化
        if "debate_mode" in result and hasattr(result["debate_mode"], "value"):
            result["debate_mode"] = result["debate_mode"].value
        if "processing_mode" in result and hasattr(result["processing_mode"], "value"):
            result["processing_mode"] = result["processing_mode"].value

        # 处理其他可能的复杂对象
        if "question_profile" in result and result["question_profile"]:
            if hasattr(result["question_profile"], "complexity") and hasattr(
                result["question_profile"]["complexity"], "value"
            ):
                result["question_profile"]["complexity"] = result["question_profile"][
                    "complexity"
                ].value
            if hasattr(result["question_profile"], "debate_mode") and hasattr(
                result["question_profile"]["debate_mode"], "value"
            ):
                result["question_profile"]["debate_mode"] = result["question_profile"][
                    "debate_mode"
                ].value

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PKSession":
        """从字典创建实例"""
        # 处理JSON序列化后responses字典键从int变为str的问题
        if "responses" in data and data["responses"]:
            # 将字符串键转换回整数键
            responses = {}
            for key, value in data["responses"].items():
                responses[int(key)] = value
            data["responses"] = responses

        # 处理枚举类型反序列化
        if "debate_mode" in data and isinstance(data["debate_mode"], str):
            data["debate_mode"] = DebateMode(data["debate_mode"])
        if "processing_mode" in data and isinstance(data["processing_mode"], str):
            data["processing_mode"] = ProcessingMode(data["processing_mode"])

        # 处理问题档案中的枚举
        if "question_profile" in data and data["question_profile"]:
            if "complexity" in data["question_profile"] and isinstance(
                data["question_profile"]["complexity"], str
            ):
                data["question_profile"]["complexity"] = QuestionComplexity(
                    data["question_profile"]["complexity"]
                )
            if "debate_mode" in data["question_profile"] and isinstance(
                data["question_profile"]["debate_mode"], str
            ):
                data["question_profile"]["debate_mode"] = DebateMode(
                    data["question_profile"]["debate_mode"]
                )

        return cls(**data)

    def get_current_persona(self) -> str:
        """获取当前应该发言的专家"""
        if self.current_persona_index < len(self.selected_personas):
            return self.selected_personas[self.current_persona_index]
        return ""

    def advance_to_next_persona(self) -> bool:
        """切换到下一个专家，返回是否还有下一个"""
        self.current_persona_index += 1
        self.updated_at = datetime.now().isoformat()

        if self.current_persona_index >= len(self.selected_personas):
            # 当前轮次所有人都发言完毕，进入下一轮
            self.current_round += 1
            self.current_persona_index = 0
            return self.current_round <= self.max_rounds
        return True

    def record_response(self, persona: str, response: str) -> None:
        """记录某个专家的回答"""
        if self.current_round not in self.responses:
            self.responses[self.current_round] = {}

        self.responses[self.current_round][persona] = response
        self.updated_at = datetime.now().isoformat()

    def get_session_status(self) -> dict[str, Any]:
        """获取会话状态信息"""
        round_names = self._get_round_names()

        current_persona = self.get_current_persona()

        return {
            "session_id": self.session_id,
            "question": self.user_question,
            "current_round": self.current_round,
            "round_name": round_names.get(self.current_round, "已完成"),
            "current_persona": current_persona,
            "personas": self.selected_personas,
            "completed_responses": len(
                [
                    r
                    for round_responses in self.responses.values()
                    for r in round_responses.values()
                ]
            ),
            "is_completed": self.current_round > self.max_rounds
            or self.final_synthesis is not None,
            "debate_mode": self.debate_mode.value,
            "max_rounds": self.max_rounds,
            "quality_score": (
                self.quality_metrics.overall_score if self.quality_metrics else 0.0
            ),
            "is_recommended_by_host": self.is_recommended_by_host,
        }

    def get_round_description(self) -> str:
        """获取当前轮次的描述"""
        round_descriptions = self._get_round_descriptions()
        return round_descriptions.get(self.current_round, "已完成")

    def _get_round_names(self) -> dict[int, str]:
        """根据辩论模式获取轮次名称"""
        if self.debate_mode == DebateMode.QUICK_CONSULTATION:
            return {
                1: "第1轮：快速洞察",
                2: "第2轮：行动建议",
            }
        elif self.debate_mode == DebateMode.DEEP_EXPLORATION:
            return {
                1: "第1轮：独立思考",
                2: "第2轮：交叉辩论",
                3: "第3轮：方案细化",
                4: "第4轮：风险评估",
                5: "第5轮：最终立场",
                6: "第6轮：智慧综合",
            }
        else:  # STANDARD_DEBATE 或 FREE_DEBATE
            return {
                1: "第1轮：独立思考",
                2: "第2轮：交叉辩论",
                3: "第3轮：最终立场",
                4: "第4轮：智慧综合",
            }

    def _get_round_descriptions(self) -> dict[int, str]:
        """根据辩论模式获取轮次描述"""
        if self.debate_mode == DebateMode.QUICK_CONSULTATION:
            return {
                1: "快速洞察阶段",
                2: "行动建议阶段",
            }
        elif self.debate_mode == DebateMode.DEEP_EXPLORATION:
            return {
                1: "独立思考阶段",
                2: "交叉辩论阶段",
                3: "方案细化阶段",
                4: "风险评估阶段",
                5: "最终立场阶段",
                6: "智慧综合阶段",
            }
        else:
            return {
                1: "独立思考阶段",
                2: "交叉辩论阶段",
                3: "最终立场阶段",
                4: "智慧综合阶段",
            }

    def add_response(self, persona: str, response: str) -> None:
        """添加回应（新方法名，与record_response相同功能）"""
        self.record_response(persona, response)

    def advance_to_next(self) -> str | None:
        """推进到下一位专家，返回下一位专家名称，如果没有则返回None"""
        if self.advance_to_next_persona():
            return self.get_current_persona()
        return None

    @property
    def is_completed(self) -> bool:
        """检查会话是否已完成"""
        return self.current_round > self.max_rounds or self.final_synthesis is not None

    def update_quality_metrics(self, metrics: DebateQualityMetrics) -> None:
        """更新质量指标"""
        self.quality_metrics = metrics
        self.updated_at = datetime.now().isoformat()

    def set_expert_profiles(self, profiles: dict[str, ExpertProfile]) -> None:
        """设置专家档案"""
        self.expert_profiles = profiles
        self.updated_at = datetime.now().isoformat()

    def get_expert_profile(self, persona_name: str) -> ExpertProfile | None:
        """获取指定专家的档案"""
        if self.expert_profiles:
            return self.expert_profiles.get(persona_name)
        return None

    def adjust_max_rounds(self, new_max_rounds: int) -> None:
        """动态调整最大轮数（自由辩论模式）"""
        if self.debate_mode == DebateMode.FREE_DEBATE:
            self.max_rounds = new_max_rounds
            self.updated_at = datetime.now().isoformat()

    def set_expert_relationships(self, relationships: dict[str, list[str]]) -> None:
        """设置专家关系图谱"""
        self.expert_relationships = relationships
        self.updated_at = datetime.now().isoformat()

    def enable_batch_mode(self, config: BatchConfig | None = None) -> None:
        """启用批处理模式"""
        self.processing_mode = ProcessingMode.BATCH
        self.batch_config = config or BatchConfig.create_default()
        if self.debate_mode == DebateMode.STANDARD_DEBATE:
            self.debate_mode = DebateMode.BATCH_OPTIMIZED
        self.updated_at = datetime.now().isoformat()

    def disable_batch_mode(self) -> None:
        """禁用批处理模式"""
        self.processing_mode = ProcessingMode.SEQUENTIAL
        self.batch_config = None
        if self.debate_mode == DebateMode.BATCH_OPTIMIZED:
            self.debate_mode = DebateMode.STANDARD_DEBATE
        self.updated_at = datetime.now().isoformat()

    def is_batch_mode(self) -> bool:
        """检查是否为批处理模式"""
        return self.processing_mode == ProcessingMode.BATCH

    def set_ab_test_result(self, result: ABTestResult) -> None:
        """设置A/B测试结果"""
        self.ab_test_result = result
        self.updated_at = datetime.now().isoformat()

    def get_batch_config(self) -> BatchConfig:
        """获取批处理配置"""
        return self.batch_config or BatchConfig.create_default()
