"""
测试动态专家生成系统
"""

import pytest
from guru_pk_mcp.dynamic_experts import (
    analyze_question_profile,
    get_recommendation_strategy,
    validate_expert_selection
)


def test_analyze_question_profile_basic():
    """测试基本问题分析"""
    question = "如何提高工作效率？"
    profile = analyze_question_profile(question)
    
    assert isinstance(profile, dict)
    assert "question" in profile
    assert "word_count" in profile
    assert "char_count" in profile
    assert "complexity_score" in profile
    assert "identified_domains" in profile
    assert "question_types" in profile
    
    assert profile["question"] == question
    assert profile["word_count"] > 0
    assert profile["char_count"] > 0
    assert 1 <= profile["complexity_score"] <= 10


def test_analyze_question_profile_empty():
    """测试空问题分析"""
    profile = analyze_question_profile("")
    
    assert profile["question"] == ""
    assert profile["word_count"] == 0
    assert profile["char_count"] == 0
    assert profile["complexity_score"] == 1


def test_analyze_question_profile_complex():
    """测试复杂问题分析"""
    long_question = "在当今快速变化的商业环境中，如何通过创新技术、有效的团队管理、战略规划和客户关系管理来构建可持续的竞争优势，同时确保企业文化的传承和员工的持续发展？"
    profile = analyze_question_profile(long_question)
    
    assert profile["complexity_score"] >= 5
    assert profile["word_count"] >= 1  # 中文问题分词后可能只有1个词
    assert profile["char_count"] > 50


def test_analyze_question_domain_identification():
    """测试领域识别"""
    # 商业领域问题
    business_question = "如何提高企业的营销效果和投资回报率？"
    profile = analyze_question_profile(business_question)
    assert "商业" in profile["identified_domains"]
    
    # 科技领域问题
    tech_question = "人工智能和机器学习如何改变软件开发？"
    profile = analyze_question_profile(tech_question)
    assert "科技" in profile["identified_domains"]
    
    # 哲学领域问题
    philosophy_question = "什么是真理？我们如何理解存在的意义？"
    profile = analyze_question_profile(philosophy_question)
    assert "哲学" in profile["identified_domains"]


def test_analyze_question_type_identification():
    """测试问题类型识别"""
    # 方法咨询类
    how_question = "如何提高学习效率？"
    profile = analyze_question_profile(how_question)
    assert "方法咨询" in profile["question_types"]
    
    # 原因分析类
    why_question = "为什么有些人更容易成功？"
    profile = analyze_question_profile(why_question)
    assert "原因分析" in profile["question_types"]
    
    # 决策支持类
    choice_question = "应该选择哪种投资策略？"
    profile = analyze_question_profile(choice_question)
    assert "决策支持" in profile["question_types"]


def test_get_recommendation_strategy():
    """测试获取推荐策略"""
    question_profile = {
        "question": "如何提高团队效率？",
        "complexity_score": 6,
        "identified_domains": ["商业", "管理"],
        "question_types": ["方法咨询"]
    }
    
    strategy = get_recommendation_strategy(question_profile)
    
    assert isinstance(strategy, str)
    assert "专家推荐策略" in strategy
    assert "领域分析" in strategy
    assert "问题类型分析" in strategy
    assert "复杂度分析" in strategy


def test_get_recommendation_strategy_high_complexity():
    """测试高复杂度问题的推荐策略"""
    high_complexity_profile = {
        "question": "复杂问题",
        "complexity_score": 9,
        "identified_domains": ["哲学", "科技"],
        "question_types": ["原因分析", "趋势预测"]
    }
    
    strategy = get_recommendation_strategy(high_complexity_profile)
    assert "高复杂度问题" in strategy
    assert "理论深度强的专家" in strategy


def test_get_recommendation_strategy_low_complexity():
    """测试低复杂度问题的推荐策略"""
    low_complexity_profile = {
        "question": "简单问题",
        "complexity_score": 3,
        "identified_domains": ["教育"],
        "question_types": ["方法咨询"]
    }
    
    strategy = get_recommendation_strategy(low_complexity_profile)
    assert "相对简单问题" in strategy
    assert "实用性和可操作性" in strategy


def test_validate_expert_selection_valid():
    """测试验证有效的专家选择"""
    valid_experts = [
        {
            "name": "专家1",
            "emoji": "🎯",
            "description": "专业描述1",
            "core_traits": ["特质1", "特质2"],
            "speaking_style": "风格1",
            "base_prompt": "你是专家1..."
        },
        {
            "name": "专家2", 
            "emoji": "🚀",
            "description": "专业描述2",
            "core_traits": ["特质3", "特质4"],
            "speaking_style": "风格2",
            "base_prompt": "你是专家2..."
        },
        {
            "name": "专家3",
            "emoji": "💡",
            "description": "专业描述3", 
            "core_traits": ["特质5", "特质6"],
            "speaking_style": "风格3",
            "base_prompt": "你是专家3..."
        }
    ]
    
    result = validate_expert_selection(valid_experts)
    assert result["valid"] is True
    assert "质量良好" in result["reason"]


def test_validate_expert_selection_wrong_count():
    """测试验证错误数量的专家"""
    # 只有2个专家
    two_experts = [
        {
            "name": "专家1",
            "emoji": "🎯",
            "description": "描述1",
            "core_traits": ["特质1"],
            "speaking_style": "风格1",
            "base_prompt": "提示1"
        },
        {
            "name": "专家2",
            "emoji": "🚀", 
            "description": "描述2",
            "core_traits": ["特质2"],
            "speaking_style": "风格2",
            "base_prompt": "提示2"
        }
    ]
    
    result = validate_expert_selection(two_experts)
    assert result["valid"] is False
    assert "必须选择3位专家" in result["reason"]


def test_validate_expert_selection_missing_fields():
    """测试验证缺少字段的专家"""
    incomplete_experts = [
        {
            "name": "专家1",
            "emoji": "🎯",
            # 缺少description
            "core_traits": ["特质1"],
            "speaking_style": "风格1",
            "base_prompt": "提示1"
        },
        {
            "name": "专家2",
            "emoji": "🚀",
            "description": "描述2",
            "core_traits": ["特质2"],
            "speaking_style": "风格2",
            "base_prompt": "提示2"
        },
        {
            "name": "专家3",
            "emoji": "💡",
            "description": "描述3",
            "core_traits": ["特质3"],
            "speaking_style": "风格3",
            "base_prompt": "提示3"
        }
    ]
    
    result = validate_expert_selection(incomplete_experts)
    assert result["valid"] is False
    assert "缺少必要字段" in result["reason"]


def test_validate_expert_selection_duplicate_names():
    """测试验证重复名称的专家"""
    duplicate_experts = [
        {
            "name": "重复专家",
            "emoji": "🎯",
            "description": "描述1",
            "core_traits": ["特质1"],
            "speaking_style": "风格1",
            "base_prompt": "提示1"
        },
        {
            "name": "重复专家",  # 重复名称
            "emoji": "🚀",
            "description": "描述2",
            "core_traits": ["特质2"],
            "speaking_style": "风格2",
            "base_prompt": "提示2"
        },
        {
            "name": "专家3",
            "emoji": "💡",
            "description": "描述3",
            "core_traits": ["特质3"],
            "speaking_style": "风格3",
            "base_prompt": "提示3"
        }
    ]
    
    result = validate_expert_selection(duplicate_experts)
    assert result["valid"] is False
    assert "名称不能重复" in result["reason"]


def test_validate_expert_selection_low_diversity():
    """测试验证多样性不足的专家"""
    low_diversity_experts = [
        {
            "name": "专家1",
            "emoji": "🎯",
            "description": "描述1",
            "core_traits": ["相同特质", "另一特质"],
            "speaking_style": "风格1",
            "base_prompt": "提示1"
        },
        {
            "name": "专家2",
            "emoji": "🚀",
            "description": "描述2", 
            "core_traits": ["相同特质", "又一特质"],  # 重复特质过多
            "speaking_style": "风格2",
            "base_prompt": "提示2"
        },
        {
            "name": "专家3",
            "emoji": "💡",
            "description": "描述3",
            "core_traits": ["相同特质", "最后特质"],  # 重复特质过多
            "speaking_style": "风格3", 
            "base_prompt": "提示3"
        }
    ]
    
    result = validate_expert_selection(low_diversity_experts)
    assert result["valid"] is False
    assert "多样性" in result["reason"]


def test_edge_cases():
    """测试边缘情况"""
    # 测试None输入
    profile = analyze_question_profile(None)
    assert profile["question"] == ""
    
    # 测试特殊字符问题
    special_question = "如何解决AI在医疗、金融&教育领域的伦理问题？🤔"
    profile = analyze_question_profile(special_question)
    assert profile["complexity_score"] > 1
    assert len(profile["identified_domains"]) > 0