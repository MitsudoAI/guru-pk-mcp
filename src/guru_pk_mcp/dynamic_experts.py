"""
动态专家生成系统
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

    def validate_expert_data(self, expert_data: dict[str, Any]) -> bool:
        """验证专家数据完整性"""
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


def analyze_question_profile(question: str) -> dict[str, Any]:
    """分析问题特征和复杂度"""

    # 处理None输入
    if question is None:
        question = ""

    # 问题长度分析
    word_count = len(question.split())
    char_count = len(question)

    # 简单的复杂度评估 - 考虑中文文本特点
    base_score = 1
    # 对于中文，主要看字符数
    if char_count > 20:
        base_score += min(6, char_count // 15)
    # 英文看词数
    if word_count > 5:
        base_score += min(3, word_count // 3)
    complexity_score = min(10, base_score)

    # 领域识别关键词
    domains = {
        "商业": [
            "商业",
            "创业",
            "企业",
            "管理",
            "营销",
            "投资",
            "公司",
            "市场",
            "经营",
        ],
        "科技": ["科技", "技术", "AI", "人工智能", "软件", "互联网", "数据", "算法"],
        "哲学": ["哲学", "思维", "价值观", "道德", "伦理", "真理", "存在", "意义"],
        "心理": ["心理", "情绪", "行为", "认知", "感情", "压力", "焦虑", "自我"],
        "教育": ["教育", "学习", "教学", "知识", "成长", "培养", "发展"],
        "社会": ["社会", "文化", "政治", "制度", "法律", "公共", "社区"],
        "健康": ["健康", "医疗", "身体", "养生", "运动", "营养", "心理健康"],
        "创新": ["创新", "创造", "发明", "变革", "突破", "改进", "设计"],
        "领导": ["领导", "管理", "团队", "组织", "决策", "影响力", "沟通"],
        "战略": ["战略", "规划", "目标", "竞争", "优势", "布局", "发展"],
    }

    identified_domains = []
    for domain, keywords in domains.items():
        if any(keyword in question for keyword in keywords):
            identified_domains.append(domain)

    # 问题类型分析
    question_types = []
    if "如何" in question or "怎么" in question:
        question_types.append("方法咨询")
    if "为什么" in question or "原因" in question:
        question_types.append("原因分析")
    if "选择" in question or "决策" in question:
        question_types.append("决策支持")
    if "未来" in question or "趋势" in question:
        question_types.append("趋势预测")
    if "比较" in question or "对比" in question:
        question_types.append("对比分析")

    return {
        "question": question,
        "word_count": word_count,
        "char_count": char_count,
        "complexity_score": complexity_score,
        "identified_domains": identified_domains,
        "question_types": question_types,
        "analysis_timestamp": "2024-01-01T00:00:00Z",  # 实际应该使用真实时间
    }


def get_recommendation_strategy(question_profile: dict[str, Any]) -> str:
    """根据问题特征生成推荐策略"""

    domains = question_profile.get("identified_domains", [])
    question_types = question_profile.get("question_types", [])
    complexity = question_profile.get("complexity_score", 5)

    strategy = "# 专家推荐策略\n\n"

    # 基于领域的推荐
    if domains:
        strategy += f"## 领域分析\n识别到的相关领域：{', '.join(domains)}\n\n"

        if "商业" in domains:
            strategy += "- 建议包含商业实践专家（如企业家、投资人、管理大师）\n"
        if "哲学" in domains:
            strategy += "- 建议包含哲学思辨专家（如古代哲学家、现代专家）\n"
        if "科技" in domains:
            strategy += "- 建议包含科技创新专家（如技术领袖、科学家）\n"
        if "心理" in domains:
            strategy += "- 建议包含心理学专家（如心理学家、行为学家）\n"

    # 基于问题类型的推荐
    if question_types:
        strategy += (
            f"\n## 问题类型分析\n识别到的问题类型：{', '.join(question_types)}\n\n"
        )

        if "方法咨询" in question_types:
            strategy += "- 需要实践型专家，能提供具体可行的方法\n"
        if "原因分析" in question_types:
            strategy += "- 需要分析型专家，善于深度思考和因果分析\n"
        if "决策支持" in question_types:
            strategy += "- 需要决策型专家，具有丰富的决策经验\n"
        if "趋势预测" in question_types:
            strategy += "- 需要前瞻型专家，具有未来洞察力\n"

    # 基于复杂度的推荐
    strategy += f"\n## 复杂度分析\n问题复杂度：{complexity}/10\n\n"

    if complexity >= 8:
        strategy += "- 高复杂度问题，建议选择理论深度强的专家\n"
        strategy += "- 需要多元化视角，确保全面性\n"
    elif complexity >= 5:
        strategy += "- 中等复杂度问题，平衡理论与实践\n"
        strategy += "- 需要互补性强的专家组合\n"
    else:
        strategy += "- 相对简单问题，注重实用性和可操作性\n"
        strategy += "- 选择表达清晰、善于简化的专家\n"

    return strategy


def validate_expert_selection(experts: list[dict[str, Any]]) -> dict[str, Any]:
    """验证专家选择的质量"""

    if len(experts) != 3:
        return {"valid": False, "reason": "必须选择3位专家"}

    required_fields = [
        "name",
        "emoji",
        "description",
        "core_traits",
        "speaking_style",
        "base_prompt",
    ]

    for expert in experts:
        for field in required_fields:
            if field not in expert or not expert[field]:
                return {
                    "valid": False,
                    "reason": f"专家 {expert.get('name', '未知')} 缺少必要字段: {field}",
                }

    # 检查专家名称是否重复
    names = [expert["name"] for expert in experts]
    if len(set(names)) != len(names):
        return {"valid": False, "reason": "专家名称不能重复"}

    # 检查多样性（简单检查）
    all_traits = []
    for expert in experts:
        all_traits.extend(expert["core_traits"])

    if len(set(all_traits)) < len(all_traits) * 0.7:  # 70%的特质应该是独特的
        return {"valid": False, "reason": "专家特质重复度过高，缺乏多样性"}

    return {"valid": True, "reason": "专家选择质量良好"}
