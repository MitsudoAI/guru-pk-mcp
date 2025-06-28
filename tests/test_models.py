"""
测试数据模型
"""

import pytest
from datetime import datetime

from guru_pk_mcp.models import PKSession


def test_pk_session_creation():
    """测试PK会话创建"""
    question = "测试问题"
    personas = ["苏格拉底", "埃隆马斯克", "查理芒格"]
    
    session = PKSession.create_new(question, personas)
    
    assert session.user_question == question
    assert session.selected_personas == personas
    assert session.current_round == 1
    assert session.current_persona_index == 0
    assert session.responses == {}
    assert session.final_synthesis is None
    assert len(session.session_id) == 8


def test_get_current_persona():
    """测试获取当前专家"""
    session = PKSession.create_new("test", ["A", "B", "C"])
    
    assert session.get_current_persona() == "A"
    
    session.current_persona_index = 1
    assert session.get_current_persona() == "B"
    
    session.current_persona_index = 2
    assert session.get_current_persona() == "C"
    
    session.current_persona_index = 3
    assert session.get_current_persona() == ""


def test_record_response():
    """测试记录回应"""
    session = PKSession.create_new("test", ["A", "B", "C"])
    
    session.record_response("A", "回应A")
    
    assert session.responses[1]["A"] == "回应A"


def test_advance_to_next_persona():
    """测试推进到下一位专家"""
    session = PKSession.create_new("test", ["A", "B", "C"])
    
    # 第一轮
    assert session.current_round == 1
    assert session.current_persona_index == 0
    
    # A -> B
    result = session.advance_to_next_persona()
    assert result is True
    assert session.current_persona_index == 1
    assert session.current_round == 1
    
    # B -> C  
    result = session.advance_to_next_persona()
    assert result is True
    assert session.current_persona_index == 2
    assert session.current_round == 1
    
    # C -> 第2轮 A
    result = session.advance_to_next_persona()
    assert result is True
    assert session.current_persona_index == 0
    assert session.current_round == 2


def test_session_completion():
    """测试会话完成状态"""
    session = PKSession.create_new("test", ["A", "B", "C"])
    
    assert not session.is_completed
    
    # 模拟完成4轮
    session.current_round = 5
    assert session.is_completed
    
    # 或者有最终综合
    session.current_round = 3
    session.final_synthesis = "最终综合"
    assert session.is_completed


def test_to_dict_and_from_dict():
    """测试序列化和反序列化"""
    original = PKSession.create_new("test", ["A", "B", "C"])
    original.record_response("A", "测试回应")
    
    # 转换为字典
    data = original.to_dict()
    assert isinstance(data, dict)
    assert data["user_question"] == "test"
    
    # 从字典恢复
    restored = PKSession.from_dict(data)
    assert restored.user_question == original.user_question
    assert restored.selected_personas == original.selected_personas
    assert restored.responses == original.responses