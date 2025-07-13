"""
会话管理器 - 负责会话的存储和加载
"""

import json
import sys
from pathlib import Path
from typing import Any

from .ab_testing import ABTestFramework
from .batch_prompts import BatchPromptGenerator
from .mode_selector import ModeRecommendationEngine
from .models import ABTestResult, BatchConfig, PKSession


class SessionManager:
    """简化版会话管理器 - 专注于会话存储和管理"""

    def __init__(self, data_dir: str | None = None, expert_manager: Any = None) -> None:
        if data_dir is None:
            # 使用环境变量或默认到用户家目录
            import os

            data_dir = os.environ.get("DATA_DIR", os.path.expanduser("~/.guru-pk-data"))

        self.data_dir = Path(data_dir)
        self.expert_manager = expert_manager

        # 初始化批处理相关组件
        self.batch_prompt_generator = BatchPromptGenerator()
        self.mode_recommendation_engine = ModeRecommendationEngine()
        self.ab_test_framework = ABTestFramework(str(self.data_dir))

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

    def create_session(
        self,
        question: str,
        personas: list[str],
        expert_profiles: dict[str, Any] | None = None,
        is_recommended_by_host: bool = False,
    ) -> PKSession:
        """创建新的会话"""
        session = PKSession.create_new(
            user_question=question,
            selected_personas=personas,
            is_recommended_by_host=is_recommended_by_host,
        )

        # 如果提供了专家详细信息，保存到会话中
        if expert_profiles:
            session.expert_profiles = expert_profiles

        # 保存会话
        self.save_session(session)
        return session

    async def export_session_as_infographic(self, session: PKSession) -> str:
        """导出会话为塔夫特风格的单页动态信息图"""

        # 生成Markdown内容（复用现有逻辑）
        md_content = self._generate_session_markdown(session)

        # 保存Markdown文件
        md_file = self.data_dir / f"export_{session.session_id}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        # 读取信息图prompt模板
        # 统一使用包内的模板文件
        try:
            from importlib import resources

            prompt_template = resources.read_text(
                "guru_pk_mcp.templates", "infographic_spa_prompt.md"
            )
        except (ImportError, FileNotFoundError) as e:
            raise FileNotFoundError(f"信息图prompt模板未找到: {e}") from e

        # 生成HTML信息图文件路径
        html_file = self.data_dir / f"infographic_{session.session_id}.html"

        # 构造完整的指令内容，直接返回给MCP Host端LLM处理
        full_prompt = f"""{prompt_template}

{md_content}

---

**重要指令**: 请根据上述塔夫特风格信息图生成指令和专家辩论内容，生成一个完整的HTML文件。HTML文件要求：

1. **单文件形式**: 所有CSS、JavaScript都内联到HTML中
2. **文件保存**: 【必须严格遵循】将生成的HTML内容保存到以下指定路径，不得更改：
   - 文件路径：`{html_file}`
   - 绝对路径：`{html_file.absolute()}`
   - 请确保保存到此路径，不要自动创建其他目录如docs/infographics/
3. **自动打开**: 保存完成后使用以下Python代码打开浏览器:
   ```python
   import webbrowser
   webbrowser.open("file://{html_file.absolute()}")
   ```
4. **遵循塔夫特原则**: 严格按照上述设计原则实现数据可视化
5. **响应式设计**: 确保在不同屏幕尺寸下都能正常显示

请立即开始生成HTML信息图文件，确保保存到指定的数据目录路径：{self.data_dir}"""

        return full_prompt

    def _generate_session_markdown(self, session: PKSession) -> str:
        """生成会话的Markdown内容（从export_session方法提取）"""
        md_content = f"""# 专家PK讨论记录

**会话ID**: {session.session_id}
**问题**: {session.user_question}
**创建时间**: {session.created_at}
**参与专家**: {", ".join(session.selected_personas)}

---

"""

        round_names = {
            1: "🤔 第1轮：独立思考",
            2: "💬 第2轮：交叉辩论",
            3: "🎯 第3轮：最终立场",
            4: "🧠 第4轮：智慧综合",
        }

        for round_num in sorted(session.responses.keys()):
            md_content += f"## {round_names.get(round_num, f'第{round_num}轮')}\n\n"

            for persona, response in session.responses[round_num].items():
                md_content += f"### {persona}\n\n"
                md_content += f"{response}\n\n---\n\n"

        # Only add final_synthesis if it's different from round 4 content
        if session.final_synthesis:
            # Check if final_synthesis is identical to any round 4 response
            round_4_responses = session.responses.get(4, {})
            is_duplicate = any(
                session.final_synthesis == response
                for response in round_4_responses.values()
            )

            if not is_duplicate:
                md_content += f"## 🌟 最终综合方案\n\n{session.final_synthesis}\n\n"

        md_content += f"""## 📊 统计信息

- **总发言数**: {len([r for round_responses in session.responses.values() for r in round_responses.values()])}
- **字数统计**: {sum(len(r) for round_responses in session.responses.values() for r in round_responses.values()):,} 字符
- **最后更新**: {session.updated_at}

---
*由 Guru-PK MCP 系统生成*"""

        return md_content

    # 批处理模式支持方法

    def get_batch_prompt(
        self,
        round_type: str,
        personas: list[dict[str, Any]],
        question: str,
        previous_responses: dict[str, Any] | None = None,
        batch_config: BatchConfig | None = None,
        language_instruction: str = "请务必使用中文回答。",
    ) -> str:
        """获取批处理模式的提示词"""
        if batch_config:
            self.batch_prompt_generator.config = batch_config

        return self.batch_prompt_generator.get_batch_prompt(
            round_type, personas, question, previous_responses, language_instruction
        )

    def get_mode_selection_guidance(
        self,
        question: str,
        personas: list[dict[str, Any]] | None = None,
        user_preference: str | None = None,
    ) -> str:
        """获取模式选择指导"""
        return self.mode_recommendation_engine.get_recommendation_prompt(
            question, personas, user_preference
        )

    def get_ab_test_guidance(
        self,
        question: str,
        personas: list[dict[str, Any]],
        batch_config: BatchConfig | None = None,
    ) -> str:
        """获取A/B测试指导"""
        return self.ab_test_framework.get_ab_test_guidance(
            question, personas, batch_config
        )

    def save_ab_test_result(self, result: ABTestResult) -> bool:
        """保存A/B测试结果"""
        return self.ab_test_framework.save_test_result(result)

    def get_ab_test_results(self) -> list[dict[str, Any]]:
        """获取所有A/B测试结果"""
        return self.ab_test_framework.load_test_results()

    def get_performance_summary(self) -> str:
        """获取性能总结报告"""
        return self.ab_test_framework.get_performance_summary()

    def create_batch_session(
        self,
        question: str,
        personas: list[str],
        expert_profiles: dict[str, Any] | None = None,
        batch_config: BatchConfig | None = None,
        is_recommended_by_host: bool = False,
    ) -> PKSession:
        """创建批处理模式的会话"""
        from .models import DebateMode

        session = PKSession.create_new(
            user_question=question,
            selected_personas=personas,
            debate_mode=DebateMode.BATCH_OPTIMIZED,
            is_recommended_by_host=is_recommended_by_host,
        )

        # 启用批处理模式
        session.enable_batch_mode(batch_config)

        # 如果提供了专家详细信息，保存到会话中
        if expert_profiles:
            session.expert_profiles = expert_profiles

        # 保存会话
        self.save_session(session)
        return session

    def optimize_batch_config(
        self,
        question: str,
        personas: list[dict[str, Any]],
        user_requirements: str | None = None,
    ) -> str:
        """获取批处理配置优化建议"""
        from .mode_selector import ModeSelector

        # 分析问题复杂度和专家多样性
        complexity, _ = ModeSelector.analyze_question_complexity(question)
        diversity, _ = ModeSelector.analyze_expert_diversity(personas)

        return ModeSelector.get_batch_config_guidance(
            complexity, diversity, user_requirements
        )

    def should_use_ab_testing(
        self,
        question: str,
        personas: list[dict[str, Any]],
        user_preference: str | None = None,
    ) -> str:
        """判断是否应该进行A/B测试的指导"""
        from .mode_selector import ModeSelector

        complexity, _ = ModeSelector.analyze_question_complexity(question)
        diversity, _ = ModeSelector.analyze_expert_diversity(personas)

        should_test, guidance = ModeSelector.should_use_ab_testing(
            complexity, diversity, user_preference
        )

        return guidance
