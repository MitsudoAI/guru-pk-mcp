"""
测试专家配置
"""

import pytest

from guru_pk_mcp.personas import (
    PERSONAS, 
    get_available_personas, 
    generate_round_prompt,
    format_persona_info
)


def test_personas_config():
    """测试专家配置完整性"""
    assert len(PERSONAS) > 0
    
    for name, persona in PERSONAS.items():
        # 检查必要字段
        assert "name" in persona
        assert "emoji" in persona
        assert "description" in persona
        assert "core_traits" in persona
        assert "speaking_style" in persona
        assert "base_prompt" in persona
        
        # 检查字段类型
        assert isinstance(persona["name"], str)
        assert isinstance(persona["emoji"], str)
        assert isinstance(persona["description"], str)
        assert isinstance(persona["core_traits"], list)
        assert isinstance(persona["speaking_style"], str)
        assert isinstance(persona["base_prompt"], str)
        
        # 检查内容不为空
        assert len(persona["name"]) > 0
        assert len(persona["description"]) > 0
        assert len(persona["core_traits"]) > 0
        assert len(persona["base_prompt"]) > 0


def test_get_available_personas():
    """测试获取可用专家列表"""
    personas = get_available_personas()
    
    assert isinstance(personas, list)
    assert len(personas) == len(PERSONAS)
    
    for persona in personas:
        assert "name" in persona
        assert "emoji" in persona
        assert "description" in persona
        assert "traits" in persona


def test_format_persona_info():
    """测试格式化专家信息"""
    # 测试有效专家
    info = format_persona_info("苏格拉底")
    assert "🧠" in info
    assert "苏格拉底" in info
    assert "古希腊哲学家" in info
    
    # 测试无效专家
    info = format_persona_info("不存在的专家")
    assert "未知思想家" in info


def test_generate_round_prompt():
    """测试生成轮次提示"""
    context = {
        "question": "测试问题",
        "my_previous_response": "我的前一轮回应",
        "other_responses": {"专家B": "专家B的回应"},
        "all_previous_responses": {1: {"专家A": "第1轮回应"}},
        "final_responses": {"专家A": "最终回应"}
    }
    
    # 测试第1轮（独立思考）
    prompt1 = generate_round_prompt("苏格拉底", 1, context)
    assert "测试问题" in prompt1
    assert "苏格拉底" in prompt1 or "古希腊" in prompt1
    
    # 测试第2轮（交叉辩论）
    prompt2 = generate_round_prompt("苏格拉底", 2, context)
    assert "测试问题" in prompt2
    assert "我的前一轮回应" in prompt2 or "专家B的回应" in prompt2
    
    # 测试第3轮（最终立场）
    prompt3 = generate_round_prompt("苏格拉底", 3, context)
    assert "测试问题" in prompt3
    assert "最后一轮" in prompt3 or "最终" in prompt3
    
    # 测试第4轮（智慧综合）
    prompt4 = generate_round_prompt("苏格拉底", 4, context)
    assert "测试问题" in prompt4
    assert "综合" in prompt4 or "整合" in prompt4
    
    # 测试无效轮次
    prompt_invalid = generate_round_prompt("苏格拉底", 5, context)
    assert "无效的轮次" in prompt_invalid


def test_generate_round_prompt_unknown_persona():
    """测试未知专家的提示生成"""
    context = {"question": "测试问题"}
    
    prompt = generate_round_prompt("未知专家", 1, context)
    assert "未知的思想家" in prompt


def test_generate_round_prompt_with_custom_personas():
    """测试使用自定义专家生成提示"""
    custom_personas = {
        "自定义专家": {
            "base_prompt": "你是一位自定义的思想家..."
        }
    }
    
    context = {"question": "测试问题"}
    
    prompt = generate_round_prompt("自定义专家", 1, context, custom_personas)
    assert "自定义的思想家" in prompt
    assert "测试问题" in prompt