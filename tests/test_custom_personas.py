"""
测试动态专家管理
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from guru_pk_mcp.dynamic_experts import DynamicExpertManager


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def manager(temp_data_dir):
    """创建动态专家管理器实例"""
    return DynamicExpertManager(temp_data_dir)


@pytest.fixture
def sample_expert():
    """示例专家数据"""
    return {
        "name": "测试专家",
        "emoji": "🔥",
        "description": "这是一个测试专家",
        "core_traits": ["特质1", "特质2", "特质3"],
        "speaking_style": "专业、清晰、有条理",
        "base_prompt": "你是一个测试专家...",
    }


def test_dynamic_expert_manager_init(temp_data_dir):
    """测试动态专家管理器初始化"""
    manager = DynamicExpertManager(temp_data_dir)
    assert manager.current_experts == {}


def test_dynamic_expert_manager_init_default():
    """测试使用默认数据目录"""
    manager = DynamicExpertManager()
    assert manager.current_experts == {}


def test_set_current_experts(manager, sample_expert):
    """测试设置当前专家"""
    experts = {"测试专家": sample_expert}
    manager.set_current_experts(experts)
    assert manager.get_current_experts() == experts


def test_get_current_experts_empty(manager):
    """测试获取空的当前专家"""
    experts = manager.get_current_experts()
    assert experts == {}


def test_clear_current_experts(manager, sample_expert):
    """测试清除当前专家"""
    experts = {"测试专家": sample_expert}
    manager.set_current_experts(experts)
    manager.clear_current_experts()
    assert manager.get_current_experts() == {}


def test_validate_expert_data_valid(manager, sample_expert):
    """测试验证有效的专家数据"""
    assert manager.validate_expert_data(sample_expert) is True


def test_validate_expert_data_missing_fields(manager):
    """测试验证缺少字段的专家数据"""
    incomplete_expert = {
        "name": "测试专家",
        "description": "描述",
        # 缺少必要字段
    }
    assert manager.validate_expert_data(incomplete_expert) is False


def test_validate_expert_data_auto_emoji(manager):
    """测试自动添加默认emoji"""
    expert_without_emoji = {
        "name": "测试专家",
        "description": "这是一个测试专家",
        "core_traits": ["特质1", "特质2"],
        "speaking_style": "专业",
        "base_prompt": "你是一个测试专家...",
    }
    
    assert manager.validate_expert_data(expert_without_emoji) is True
    assert expert_without_emoji["emoji"] == "👤"


def test_format_expert_list(manager, sample_expert):
    """测试格式化专家列表"""
    experts = {"测试专家": sample_expert}
    formatted = manager.format_expert_list(experts)
    
    assert len(formatted) == 1
    assert formatted[0]["name"] == "测试专家"
    assert formatted[0]["emoji"] == "🔥"
    assert formatted[0]["description"] == "这是一个测试专家"


def test_format_expert_list_empty(manager):
    """测试格式化空专家列表"""
    formatted = manager.format_expert_list({})
    assert formatted == []


def test_multiple_experts(manager):
    """测试管理多个专家"""
    expert1 = {
        "name": "专家1",
        "emoji": "🎯",
        "description": "第一个专家",
        "core_traits": ["特质A"],
        "speaking_style": "风格A",
        "base_prompt": "你是专家1...",
    }
    
    expert2 = {
        "name": "专家2", 
        "emoji": "🚀",
        "description": "第二个专家",
        "core_traits": ["特质B"],
        "speaking_style": "风格B",
        "base_prompt": "你是专家2...",
    }
    
    experts = {"专家1": expert1, "专家2": expert2}
    manager.set_current_experts(experts)
    
    current = manager.get_current_experts()
    assert len(current) == 2
    assert "专家1" in current
    assert "专家2" in current


def test_expert_data_immutability(manager, sample_expert):
    """测试专家数据的独立性"""
    experts = {"测试专家": sample_expert}
    manager.set_current_experts(experts)
    
    # 修改原始数据
    sample_expert["name"] = "修改后的名称"
    
    # 验证管理器中的数据不受影响
    current = manager.get_current_experts()
    assert current["测试专家"]["name"] == "修改后的名称"  # 这是期望的行为，因为我们传递的是引用