"""
测试动态专家生成系统 - 重构后版本
"""

import pytest
from guru_pk_mcp.dynamic_experts import (
    DynamicExpertManager,
    get_question_analysis_guidance,
    get_expert_recommendation_guidance,
)


def test_dynamic_expert_manager_basic():
    """测试动态专家管理器基本功能"""
    manager = DynamicExpertManager()
    
    # 测试初始状态
    assert manager.get_current_experts() == {}
    
    # 测试设置专家
    test_experts = {
        "专家1": {
            "name": "专家1",
            "emoji": "🎯",
            "description": "测试专家",
            "core_traits": ["特质1", "特质2"],
            "speaking_style": "测试风格",
            "base_prompt": "你是测试专家"
        }
    }
    
    manager.set_current_experts(test_experts)
    assert manager.get_current_experts() == test_experts
    
    # 测试清除专家
    manager.clear_current_experts()
    assert manager.get_current_experts() == {}


def test_validate_expert_data():
    """测试专家数据验证"""
    manager = DynamicExpertManager()
    
    # 测试完整的专家数据
    valid_expert = {
        "name": "测试专家",
        "description": "专家描述",
        "core_traits": ["特质1", "特质2"],
        "speaking_style": "表达风格",
        "base_prompt": "角色提示"
    }
    
    assert manager.validate_expert_data(valid_expert) is True
    assert "emoji" in valid_expert  # 应该自动添加默认emoji
    
    # 测试缺少必要字段的专家数据
    incomplete_expert = {
        "name": "测试专家",
        "description": "专家描述",
        # 缺少其他必要字段
    }
    
    assert manager.validate_expert_data(incomplete_expert) is False


def test_format_expert_list():
    """测试专家列表格式化"""
    manager = DynamicExpertManager()
    
    test_experts = {
        "专家1": {
            "name": "专家1",
            "emoji": "🎯",
            "description": "测试专家1",
            "core_traits": ["特质1", "特质2"],
            "speaking_style": "风格1",
            "base_prompt": "提示1"
        },
        "专家2": {
            "name": "专家2",
            "description": "测试专家2",  # 没有emoji，应该使用默认值
            "core_traits": ["特质3", "特质4"],
            "speaking_style": "风格2",
            "base_prompt": "提示2"
        }
    }
    
    formatted_list = manager.format_expert_list(test_experts)
    
    assert len(formatted_list) == 2
    assert all("name" in expert for expert in formatted_list)
    assert all("emoji" in expert for expert in formatted_list)
    assert all("description" in expert for expert in formatted_list)
    assert all("core_traits" in expert for expert in formatted_list)
    assert all("speaking_style" in expert for expert in formatted_list)
    
    # 检查默认emoji是否被正确添加
    expert2 = next(e for e in formatted_list if e["name"] == "专家2")
    assert expert2["emoji"] == "👤"


def test_get_question_analysis_guidance():
    """测试问题分析指导获取"""
    guidance = get_question_analysis_guidance()
    
    assert isinstance(guidance, str)
    assert len(guidance) > 0
    assert "问题分析指导原则" in guidance
    assert "分析维度" in guidance
    assert "问题复杂度" in guidance
    assert "问题类型" in guidance
    assert "领域识别" in guidance


def test_get_expert_recommendation_guidance():
    """测试专家推荐指导获取"""
    guidance = get_expert_recommendation_guidance()
    
    assert isinstance(guidance, str)
    assert len(guidance) > 0
    assert "专家推荐指导原则" in guidance
    assert "推荐策略" in guidance
    assert "多样性原则" in guidance
    assert "互补性原则" in guidance
    assert "针对性原则" in guidance
    assert "平衡性原则" in guidance



def test_guidance_content_structure():
    """测试指导内容的结构完整性"""
    # 测试问题分析指导的结构
    question_guidance = get_question_analysis_guidance()
    
    # 应该包含主要的分析维度
    expected_question_sections = [
        "分析维度",
        "问题复杂度", 
        "问题类型",
        "领域识别",
        "分析要求"
    ]
    
    for section in expected_question_sections:
        assert section in question_guidance, f"问题分析指导缺少 {section} 部分"
    
    # 测试专家推荐指导的结构
    expert_guidance = get_expert_recommendation_guidance()
    
    # 应该包含主要的推荐策略
    expected_expert_sections = [
        "推荐策略",
        "多样性原则",
        "互补性原则", 
        "针对性原则",
        "平衡性原则",
        "专家类型推荐",
        "质量检查"
    ]
    
    for section in expected_expert_sections:
        assert section in expert_guidance, f"专家推荐指导缺少 {section} 部分"


def test_edge_cases():
    """测试边缘情况"""
    manager = DynamicExpertManager()
    
    # 测试空专家数据验证
    empty_expert = {}
    assert manager.validate_expert_data(empty_expert) is False
    
    # 测试None值处理
    assert manager.validate_expert_data(None) is False
    
    # 测试空专家列表格式化
    empty_formatted = manager.format_expert_list({})
    assert empty_formatted == []
    


def test_manager_with_data_dir():
    """测试带数据目录的管理器"""
    # 测试不同的数据目录参数
    manager1 = DynamicExpertManager(None)
    manager2 = DynamicExpertManager("/tmp/test")
    
    # 两个管理器应该独立工作
    test_experts = {
        "专家A": {
            "name": "专家A",
            "description": "测试",
            "core_traits": ["特质"],
            "speaking_style": "风格",
            "base_prompt": "提示"
        }
    }
    
    manager1.set_current_experts(test_experts)
    assert manager1.get_current_experts() == test_experts
    assert manager2.get_current_experts() == {}