"""
会话管理器 - 负责会话的存储和加载
"""

import json
import sys
from pathlib import Path
from typing import Any

from .models import PKSession


class SessionManager:
    """会话管理器"""

    def __init__(self, data_dir: str | None = None):
        if data_dir is None:
            # 使用环境变量或默认到用户家目录
            import os

            data_dir = os.environ.get("DATA_DIR", os.path.expanduser("~/.guru-pk-data"))

        self.data_dir = Path(data_dir)
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            # 如果无法创建目录，回退到临时目录
            import tempfile

            self.data_dir = Path(tempfile.mkdtemp(prefix="guru-pk-"))
            print(
                f"Warning: Could not create data directory {data_dir}, using temporary directory {self.data_dir}",
                file=sys.stderr,
            )

    def save_session(self, session: PKSession) -> bool:
        """保存会话到JSON文件"""
        try:
            file_path = self.data_dir / f"{session.session_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存会话失败: {e}")
            return False

    def load_session(self, session_id: str) -> PKSession | None:
        """从文件加载会话"""
        try:
            file_path = self.data_dir / f"{session_id}.json"
            if file_path.exists():
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    return PKSession.from_dict(data)
        except Exception as e:
            print(f"加载会话失败: {e}")
        return None

    def list_sessions(self) -> list[dict[str, Any]]:
        """列出所有会话的基本信息"""
        sessions = []
        try:
            for file_path in self.data_dir.glob("*.json"):
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    sessions.append(
                        {
                            "session_id": data["session_id"],
                            "question": (
                                data["user_question"][:100] + "..."
                                if len(data["user_question"]) > 100
                                else data["user_question"]
                            ),
                            "personas": data["selected_personas"],
                            "created_at": data["created_at"],
                            "is_completed": data.get("final_synthesis") is not None,
                        }
                    )
        except Exception as e:
            print(f"列出会话失败: {e}")

        # 按创建时间倒序排列
        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            file_path = self.data_dir / f"{session_id}.json"
            if file_path.exists():
                file_path.unlink()
                return True
        except Exception as e:
            print(f"删除会话失败: {e}")
        return False

    def get_latest_session(self) -> PKSession | None:
        """获取最新的会话"""
        sessions = self.list_sessions()
        if sessions:
            return self.load_session(sessions[0]["session_id"])
        return None
