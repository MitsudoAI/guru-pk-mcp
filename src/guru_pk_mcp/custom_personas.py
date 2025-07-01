"""
自定义Persona管理
"""

import json
import sys
from pathlib import Path
from typing import Any


class CustomPersonaManager:
    """自定义思想家管理器"""

    def __init__(self, data_dir: str | None = None):
        if data_dir is None:
            import os

            data_dir = os.environ.get("DATA_DIR", os.path.expanduser("~/.guru-pk-data"))

        self.data_dir = Path(data_dir)
        self.custom_personas_file = self.data_dir / "custom_personas.json"

        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            # 如果无法创建目录，回退到临时目录
            import tempfile

            self.data_dir = Path(tempfile.mkdtemp(prefix="guru-pk-personas-"))
            self.custom_personas_file = self.data_dir / "custom_personas.json"
            print(
                f"Warning: Could not create data directory, using temporary directory {self.data_dir}",
                file=sys.stderr,
            )

        self._load_custom_personas()

    def _load_custom_personas(self) -> None:
        """加载自定义思想家"""
        try:
            if self.custom_personas_file.exists():
                with open(self.custom_personas_file, encoding="utf-8") as f:
                    self.custom_personas = json.load(f)
            else:
                self.custom_personas = {}
        except Exception as e:
            print(f"加载自定义思想家失败: {e}")
            self.custom_personas = {}

    def _save_custom_personas(self) -> bool:
        """保存自定义思想家"""
        try:
            with open(self.custom_personas_file, "w", encoding="utf-8") as f:
                json.dump(self.custom_personas, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存自定义思想家失败: {e}")
            return False

    def add_custom_persona(self, persona_data: dict[str, Any]) -> bool:
        """添加自定义思想家"""
        required_fields = [
            "name",
            "description",
            "core_traits",
            "speaking_style",
            "base_prompt",
        ]

        # 验证必填字段
        for field in required_fields:
            if field not in persona_data or not persona_data[field]:
                return False

        # 添加默认emoji
        if "emoji" not in persona_data:
            persona_data["emoji"] = "👤"

        # 保存
        self.custom_personas[persona_data["name"]] = persona_data
        return self._save_custom_personas()

    def get_custom_persona(self, name: str) -> dict[str, Any] | None:
        """获取指定的自定义思想家"""
        result = self.custom_personas.get(name)
        return result if result is not None else None

    def list_custom_personas(self) -> list[dict[str, Any]]:
        """列出所有自定义思想家"""
        return [
            {
                "name": persona["name"],
                "emoji": persona.get("emoji", "👤"),
                "description": persona["description"],
                "core_traits": persona["core_traits"],
                "speaking_style": persona["speaking_style"],
                "base_prompt": persona["base_prompt"],
            }
            for persona in self.custom_personas.values()
        ]

    def delete_custom_persona(self, name: str) -> bool:
        """删除自定义思想家"""
        if name in self.custom_personas:
            del self.custom_personas[name]
            return self._save_custom_personas()
        return False

    def get_all_personas(self, builtin_personas: dict[str, Any]) -> dict[str, Any]:
        """获取所有思想家（内置+自定义）"""
        all_personas = builtin_personas.copy()
        all_personas.update(self.custom_personas)
        return all_personas
