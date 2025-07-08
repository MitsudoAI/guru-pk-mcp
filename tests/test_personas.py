"""
测试动态专家配置
"""

import pytest

from guru_pk_mcp.personas import (
    generate_round_prompt,
    format_persona_info,
    get_expert_selection_guidance
)


def test_get_expert_selection_guidance():
    """测试获取专家选择指导"""
    question = "如何提高工作效率？"
    guidance = get_expert_selection_guidance(question)
    
    assert isinstance(guidance, str)
    assert "专家选择指导原则" in guidance
    assert question in guidance
    assert "专业相关性" in guidance
    assert "视角多样性" in guidance


def test_get_expert_selection_guidance_empty():
    """测试空问题的专家选择指导"""
    guidance = get_expert_selection_guidance("")
    
    assert isinstance(guidance, str)
    assert "专家选择指导原则" in guidance


def test_format_persona_info_with_experts():
    """测试格式化专家信息（有专家数据）"""
    dynamic_experts = {
        "测试专家": {
            "name": "测试专家",
            "emoji": "🧠",
            "description": "一位测试专家"
        }
    }
    
    info = format_persona_info("测试专家", dynamic_experts)
    assert "🧠" in info
    assert "测试专家" in info
    assert "一位测试专家" in info


def test_format_persona_info_no_experts():
    """测试格式化专家信息（无专家数据）"""
    info = format_persona_info("未知专家", None)
    assert "未知专家: 未知专家" in info


def test_format_persona_info_expert_not_found():
    """测试格式化不存在的专家信息"""
    dynamic_experts = {
        "存在的专家": {
            "name": "存在的专家",
            "emoji": "✅",
            "description": "存在的专家"
        }
    }
    
    info = format_persona_info("不存在的专家", dynamic_experts)
    assert "未知专家: 不存在的专家" in info


def test_generate_round_prompt_round1():
    """测试生成第1轮提示"""
    dynamic_experts = {
        "测试专家": {
            "name": "测试专家",
            "base_prompt": "你是一个测试专家，专注于软件测试。"
        }
    }
    
    context = {
        "question": "如何提高软件质量？",
    }
    
    prompt = generate_round_prompt("测试专家", 1, context, dynamic_experts)
    assert "你是一个测试专家" in prompt
    assert "如何提高软件质量？" in prompt
    assert "独特的思维方式" in prompt


def test_generate_round_prompt_round2():
    """测试生成第2轮提示"""
    dynamic_experts = {
        "测试专家": {
            "name": "测试专家",
            "base_prompt": "你是一个测试专家。"
        }
    }
    
    context = {
        "question": "测试问题",
        "my_previous_response": "我的前一轮回应",
        "other_responses": {"专家B": "专家B的回应"}
    }
    
    prompt = generate_round_prompt("测试专家", 2, context, dynamic_experts)
    assert "你是一个测试专家" in prompt
    assert "测试问题" in prompt
    assert "我的前一轮回应" in prompt
    assert "专家B的回应" in prompt
    assert "批判性思考" in prompt


def test_generate_round_prompt_round3():
    """测试生成第3轮提示"""
    dynamic_experts = {
        "测试专家": {
            "name": "测试专家",
            "base_prompt": "你是一个测试专家。"
        }
    }
    
    context = {
        "question": "测试问题",
        "all_previous_responses": {
            1: {"专家A": "第1轮回应A", "专家B": "第1轮回应B"},
            2: {"专家A": "第2轮回应A", "专家B": "第2轮回应B"}
        }
    }
    
    prompt = generate_round_prompt("测试专家", 3, context, dynamic_experts)
    assert "你是一个测试专家" in prompt
    assert "测试问题" in prompt
    assert "最终的、最完善的解决方案" in prompt
    assert "第1轮" in prompt
    assert "第2轮" in prompt


def test_generate_round_prompt_round4():
    """测试生成第4轮提示（智慧综合）"""
    dynamic_experts = {
        "综合大师": {
            "name": "综合大师",
            "base_prompt": "你是综合分析专家。"
        }
    }
    
    context = {
        "question": "测试问题",
        "final_responses": {
            "专家A": "专家A的最终方案",
            "专家B": "专家B的最终方案",
            "专家C": "专家C的最终方案"
        }
    }
    
    prompt = generate_round_prompt("综合大师", 4, context, dynamic_experts)
    assert "智慧的综合大师" in prompt
    assert "测试问题" in prompt
    assert "专家A的最终方案" in prompt
    assert "专家B的最终方案" in prompt
    assert "专家C的最终方案" in prompt
    assert "终极解决方案" in prompt
    assert "export_enhanced_session" in prompt


def test_generate_round_prompt_unknown_expert():
    """测试生成未知专家的提示"""
    prompt = generate_round_prompt("未知专家", 1, {"question": "测试"}, None)
    assert "未知的专家: 未知专家" in prompt


def test_generate_round_prompt_invalid_round():
    """测试生成无效轮次的提示"""
    dynamic_experts = {
        "测试专家": {
            "name": "测试专家",
            "base_prompt": "你是一个测试专家。"
        }
    }
    
    prompt = generate_round_prompt("测试专家", 5, {"question": "测试"}, dynamic_experts)
    assert "无效的轮次: 5" in prompt


def test_generate_round_prompt_with_language():
    """测试生成带语言指令的提示"""
    dynamic_experts = {
        "测试专家": {
            "name": "测试专家",
            "base_prompt": "你是一个测试专家。"
        }
    }
    
    context = {"question": "测试问题"}
    language_instruction = "请使用英文回答。"
    
    prompt = generate_round_prompt("测试专家", 1, context, dynamic_experts, language_instruction)
    assert "你是一个测试专家" in prompt
    assert "请使用英文回答。" in prompt
    assert "测试问题" in prompt


def test_guidance_contains_key_elements():
    """测试指导包含关键要素"""
    question = "如何进行有效的团队管理？"
    guidance = get_expert_selection_guidance(question)
    
    # 检查是否包含关键要素
    key_elements = [
        "专业相关性",
        "视角多样性", 
        "互补性平衡",
        "辩论价值",
        "name",
        "emoji", 
        "description",
        "core_traits",
        "speaking_style",
        "base_prompt"
    ]
    
    for element in key_elements:
        assert element in guidance, f"指导中缺少关键要素: {element}"


def test_context_handling():
    """测试上下文处理"""
    dynamic_experts = {
        "专家A": {
            "name": "专家A",
            "base_prompt": "你是专家A。"
        }
    }
    
    # 测试空上下文
    empty_context = {}
    prompt = generate_round_prompt("专家A", 1, empty_context, dynamic_experts)
    assert "你是专家A" in prompt
    
    # 测试缺少question的上下文
    context_no_question = {"other_field": "value"}
    prompt = generate_round_prompt("专家A", 1, context_no_question, dynamic_experts)
    assert "你是专家A" in prompt