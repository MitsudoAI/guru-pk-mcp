"""
Guru-PK MCP 配置管理
"""

import json
import sys
from pathlib import Path
from typing import Any


class ConfigManager:
    """配置管理器"""

    def __init__(self, data_dir: str | None = None):
        if data_dir is None:
            import os

            data_dir = os.environ.get("DATA_DIR", os.path.expanduser("~/.guru-pk-data"))

        self.data_dir = Path(data_dir)
        self.config_file = self.data_dir / "config.json"

        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            # 如果无法创建目录，回退到临时目录
            import tempfile

            self.data_dir = Path(tempfile.mkdtemp(prefix="guru-pk-config-"))
            self.config_file = self.data_dir / "config.json"
            print(
                f"Warning: Could not create config directory, using temporary directory {self.data_dir}",
                file=sys.stderr,
            )

        self._load_config()

    def _load_config(self) -> None:
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, encoding="utf-8") as f:
                    self.config = json.load(f)
            else:
                self.config = self._get_default_config()
                self._save_config()
        except Exception as e:
            print(f"加载配置失败: {e}")
            self.config = self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置"""
        return {
            "language": "chinese",  # 默认中文
            "language_instructions": {
                "chinese": "请务必使用中文回答。",
                "english": "Please respond in English only.",
                "japanese": "日本語で回答してください。",
                "korean": "한국어로 답변해 주세요.",
                "french": "Veuillez répondre en français uniquement.",
                "german": "Bitte antworten Sie nur auf Deutsch.",
                "spanish": "Por favor, responde solo en español.",
            },
            "version": "1.0.0",
        }

    def _save_config(self) -> bool:
        """保存配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def get_language(self) -> str:
        """获取当前语言设置"""
        return str(self.config.get("language", "chinese"))

    def set_language(self, language: str) -> bool:
        """设置语言"""
        supported_languages = list(self.config["language_instructions"].keys())
        if language not in supported_languages:
            return False

        self.config["language"] = language
        return self._save_config()

    def get_language_instruction(self) -> str:
        """获取当前语言的指令"""
        language = self.get_language()
        return str(
            self.config["language_instructions"].get(
                language, self.config["language_instructions"]["chinese"]
            )
        )

    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        return list(self.config["language_instructions"].keys())

    def get_language_display_name(self, language: str) -> str:
        """获取语言的显示名称"""
        display_names = {
            "chinese": "中文",
            "english": "English",
            "japanese": "日本語",
            "korean": "한국어",
            "french": "Français",
            "german": "Deutsch",
            "spanish": "Español",
        }
        return display_names.get(language, language)
