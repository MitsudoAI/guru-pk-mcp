"""
测试自定义专家管理
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from guru_pk_mcp.custom_personas import CustomPersonaManager
from guru_pk_mcp.personas import PERSONAS


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def manager(temp_data_dir):
    """创建自定义专家管理器实例"""
    return CustomPersonaManager(temp_data_dir)


@pytest.fixture
def sample_persona():
    """创建示例自定义专家"""
    return {
        "name": "测试专家",
        "emoji": "🔥",
        "description": "这是一个测试专家",
        "core_traits": ["特质1", "特质2", "特质3"],
        "speaking_style": "测试风格",
        "base_prompt": "你是一个测试专家..."
    }


def test_custom_persona_manager_init(temp_data_dir):
    """测试自定义专家管理器初始化"""
    manager = CustomPersonaManager(temp_data_dir)
    
    assert manager.data_dir == Path(temp_data_dir)
    assert manager.data_dir.exists()
    assert manager.custom_personas_file.name == "custom_personas.json"


def test_custom_persona_manager_init_default():
    """测试使用默认数据目录"""
    manager = CustomPersonaManager()
    
    assert manager.data_dir is not None


def test_add_custom_persona(manager, sample_persona):
    """测试添加自定义专家"""
    result = manager.add_custom_persona(sample_persona)
    assert result is True
    
    # 检查是否保存成功
    assert manager.custom_personas_file.exists()
    
    # 检查是否可以获取
    persona = manager.get_custom_persona("测试专家")
    assert persona is not None
    assert persona["name"] == "测试专家"
    assert persona["description"] == "这是一个测试专家"


def test_add_custom_persona_missing_fields(manager):
    """测试添加缺少必要字段的自定义专家"""
    incomplete_persona = {
        "name": "不完整专家",
        "description": "缺少其他字段"
        # 缺少必要字段
    }
    
    result = manager.add_custom_persona(incomplete_persona)
    assert result is False


def test_add_custom_persona_auto_emoji(manager):
    """测试自动添加默认emoji"""
    persona_without_emoji = {
        "name": "无emoji专家",
        "description": "没有emoji的专家",
        "core_traits": ["特质1"],
        "speaking_style": "风格",
        "base_prompt": "提示..."
    }
    
    result = manager.add_custom_persona(persona_without_emoji)
    assert result is True
    
    saved_persona = manager.get_custom_persona("无emoji专家")
    assert saved_persona is not None
    assert saved_persona["emoji"] == "👤"


def test_get_custom_persona_nonexistent(manager):
    """测试获取不存在的自定义专家"""
    persona = manager.get_custom_persona("不存在的专家")
    assert persona is None


def test_list_custom_personas(manager):
    """测试列出自定义专家"""
    # 初始状态应该为空
    personas = manager.list_custom_personas()
    assert len(personas) == 0
    
    # 添加几个专家
    persona1 = {
        "name": "专家1",
        "emoji": "🔥",
        "description": "描述1",
        "core_traits": ["特质1"],
        "speaking_style": "风格1",
        "base_prompt": "提示1"
    }
    
    persona2 = {
        "name": "专家2", 
        "emoji": "💡",
        "description": "描述2",
        "core_traits": ["特质2"],
        "speaking_style": "风格2",
        "base_prompt": "提示2"
    }
    
    manager.add_custom_persona(persona1)
    manager.add_custom_persona(persona2)
    
    # 列出专家
    personas = manager.list_custom_personas()
    assert len(personas) == 2
    
    # 检查返回的格式
    for persona in personas:
        assert "name" in persona
        assert "emoji" in persona
        assert "description" in persona
        assert "traits" in persona


def test_delete_custom_persona(manager, sample_persona):
    """测试删除自定义专家"""
    # 先添加专家
    manager.add_custom_persona(sample_persona)
    
    # 确认专家存在
    persona = manager.get_custom_persona("测试专家")
    assert persona is not None
    
    # 删除专家
    result = manager.delete_custom_persona("测试专家")
    assert result is True
    
    # 确认专家已删除
    persona = manager.get_custom_persona("测试专家")
    assert persona is None


def test_delete_nonexistent_persona(manager):
    """测试删除不存在的专家"""
    result = manager.delete_custom_persona("不存在的专家")
    assert result is False


def test_get_all_personas(manager, sample_persona):
    """测试获取所有专家（内置+自定义）"""
    # 只有内置专家
    all_personas = manager.get_all_personas(PERSONAS)
    assert len(all_personas) == len(PERSONAS)
    
    # 添加自定义专家
    manager.add_custom_persona(sample_persona)
    
    # 应该包含内置和自定义专家
    all_personas = manager.get_all_personas(PERSONAS)
    assert len(all_personas) == len(PERSONAS) + 1
    assert "测试专家" in all_personas
    assert "苏格拉底" in all_personas  # 内置专家应该还在


def test_custom_persona_persistence(temp_data_dir, sample_persona):
    """测试自定义专家的持久化"""
    # 创建管理器并添加专家
    manager1 = CustomPersonaManager(temp_data_dir)
    manager1.add_custom_persona(sample_persona)
    
    # 创建新的管理器实例（模拟重启）
    manager2 = CustomPersonaManager(temp_data_dir)
    
    # 应该能加载之前保存的专家
    persona = manager2.get_custom_persona("测试专家")
    assert persona is not None
    assert persona["name"] == "测试专家"


def test_file_corruption_handling(temp_data_dir):
    """测试文件损坏的处理"""
    manager = CustomPersonaManager(temp_data_dir)
    
    # 创建损坏的JSON文件
    with open(manager.custom_personas_file, "w") as f:
        f.write("invalid json content")
    
    # 创建新的管理器，应该能处理损坏的文件
    manager2 = CustomPersonaManager(temp_data_dir)
    assert manager2.custom_personas == {}
    
    # 应该能正常添加新的专家
    sample_persona = {
        "name": "测试专家",
        "description": "测试",
        "core_traits": ["特质"],
        "speaking_style": "风格",
        "base_prompt": "提示"
    }
    
    result = manager2.add_custom_persona(sample_persona)
    assert result is True