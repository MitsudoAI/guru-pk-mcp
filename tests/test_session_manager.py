"""
测试会话管理器
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from guru_pk_mcp.session_manager import SessionManager
from guru_pk_mcp.models import PKSession


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def session_manager(temp_data_dir):
    """创建会话管理器实例"""
    return SessionManager(temp_data_dir)


@pytest.fixture
def sample_session():
    """创建示例会话"""
    return PKSession.create_new("测试问题", ["专家A", "专家B", "专家C"])


def test_session_manager_init(temp_data_dir):
    """测试会话管理器初始化"""
    manager = SessionManager(temp_data_dir)
    
    assert manager.data_dir == Path(temp_data_dir)
    assert manager.data_dir.exists()


def test_session_manager_init_default():
    """测试使用默认数据目录"""
    manager = SessionManager()
    
    assert manager.data_dir is not None
    # 应该使用环境变量或默认目录


def test_save_and_load_session(session_manager, sample_session):
    """测试保存和加载会话"""
    # 保存会话
    result = session_manager.save_session(sample_session)
    assert result is True
    
    # 检查文件是否存在
    file_path = session_manager.data_dir / f"{sample_session.session_id}.json"
    assert file_path.exists()
    
    # 加载会话
    loaded_session = session_manager.load_session(sample_session.session_id)
    assert loaded_session is not None
    assert loaded_session.session_id == sample_session.session_id
    assert loaded_session.user_question == sample_session.user_question
    assert loaded_session.selected_personas == sample_session.selected_personas


def test_load_nonexistent_session(session_manager):
    """测试加载不存在的会话"""
    result = session_manager.load_session("nonexistent_id")
    assert result is None


def test_list_sessions(session_manager, temp_data_dir):
    """测试列出会话"""
    # 初始状态应该为空
    sessions = session_manager.list_sessions()
    assert len(sessions) == 0
    
    # 创建几个会话
    session1 = PKSession.create_new("问题1", ["A", "B", "C"])
    session2 = PKSession.create_new("问题2", ["D", "E", "F"])
    
    session_manager.save_session(session1)
    session_manager.save_session(session2)
    
    # 列出会话
    sessions = session_manager.list_sessions()
    assert len(sessions) == 2
    
    # 检查会话信息
    session_ids = [s["session_id"] for s in sessions]
    assert session1.session_id in session_ids
    assert session2.session_id in session_ids
    
    # 检查问题信息
    for session_info in sessions:
        assert "session_id" in session_info
        assert "question" in session_info
        assert "created_at" in session_info
        assert "personas" in session_info


def test_delete_session(session_manager, sample_session):
    """测试删除会话"""
    # 先保存会话
    session_manager.save_session(sample_session)
    
    # 确认会话存在
    loaded = session_manager.load_session(sample_session.session_id)
    assert loaded is not None
    
    # 删除会话
    result = session_manager.delete_session(sample_session.session_id)
    assert result is True
    
    # 确认会话已删除
    loaded = session_manager.load_session(sample_session.session_id)
    assert loaded is None


def test_delete_nonexistent_session(session_manager):
    """测试删除不存在的会话"""
    result = session_manager.delete_session("nonexistent_id")
    assert result is False


def test_get_latest_session(session_manager):
    """测试获取最新会话"""
    # 初始状态应该为空
    latest = session_manager.get_latest_session()
    assert latest is None
    
    # 创建会话
    session1 = PKSession.create_new("问题1", ["A", "B", "C"])
    session2 = PKSession.create_new("问题2", ["D", "E", "F"])
    
    session_manager.save_session(session1)
    session_manager.save_session(session2)
    
    # 获取最新会话
    latest = session_manager.get_latest_session()
    assert latest is not None
    assert latest.session_id in [session1.session_id, session2.session_id]


def test_session_with_responses(session_manager):
    """测试包含回应的会话保存和加载"""
    session = PKSession.create_new("问题", ["A", "B", "C"])
    
    # 添加一些回应
    session.record_response("A", "专家A的回应")
    session.advance_to_next_persona()
    session.record_response("B", "专家B的回应")
    
    # 保存和加载
    session_manager.save_session(session)
    loaded = session_manager.load_session(session.session_id)
    
    assert loaded is not None
    assert loaded.responses == session.responses
    assert loaded.current_round == session.current_round
    assert loaded.current_persona_index == session.current_persona_index