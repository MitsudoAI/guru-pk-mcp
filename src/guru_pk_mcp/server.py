"""
Guru-PK MCP 服务器
"""

import asyncio
from typing import Any

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import TextContent

from .custom_personas import CustomPersonaManager
from .models import PKSession
from .personas import (
    PERSONAS,
    format_persona_info,
    generate_round_prompt,
    get_available_personas,
)
from .session_manager import SessionManager


class GuruPKServer:
    """大神PK MCP服务器"""

    def __init__(self) -> None:
        self.server: Server = Server("guru-pk")  # type: ignore

        # 获取数据目录
        import os

        data_dir = os.environ.get("DATA_DIR")
        if data_dir and data_dir.startswith("~"):
            data_dir = os.path.expanduser(data_dir)

        self.session_manager = SessionManager(data_dir)
        self.custom_persona_manager = CustomPersonaManager(data_dir)
        self.current_session: PKSession | None = None
        self._register_tools()

    def _register_tools(self) -> None:
        """注册所有MCP工具"""

        # 注册工具列表处理器
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """返回可用工具列表"""
            return [
                types.Tool(
                    name="start_pk_session",
                    description="启动新的专家PK会话",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "要讨论的问题",
                            },
                            "personas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "参与讨论的三位专家名称（可选，默认为苏格拉底、埃隆马斯克、查理芒格）",
                            },
                        },
                        "required": ["question"],
                    },
                ),
                types.Tool(
                    name="guru_pk_help",
                    description="获取系统帮助和介绍",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="get_persona_prompt",
                    description="获取当前专家的角色提示",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="record_round_response",
                    description="记录当前轮次的回答",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "response": {
                                "type": "string",
                                "description": "专家的回答内容",
                            }
                        },
                        "required": ["response"],
                    },
                ),
                types.Tool(
                    name="get_session_status",
                    description="获取当前会话状态",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="list_available_personas",
                    description="列出所有可用的专家",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="recommend_personas",
                    description="根据问题类型智能推荐专家组合",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "要分析的问题",
                            }
                        },
                        "required": ["question"],
                    },
                ),
                types.Tool(
                    name="view_session_history",
                    description="查看会话历史",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "会话ID（可选，默认查看当前会话）",
                            }
                        },
                    },
                ),
                types.Tool(
                    name="get_usage_statistics",
                    description="获取使用统计和分析",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="export_session",
                    description="导出会话记录为Markdown文件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "会话ID（可选，默认导出当前会话）",
                            }
                        },
                    },
                ),
                types.Tool(
                    name="advance_to_next_round",
                    description="手动进入下一轮或下一个专家",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
            ]

        # 统一工具处理器
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[TextContent]:
            """统一处理所有工具调用"""

            if name == "start_pk_session":
                return await self._handle_start_pk_session(arguments)
            elif name == "guru_pk_help":
                return await self._handle_guru_pk_help(arguments)
            elif name == "get_persona_prompt":
                return await self._handle_get_persona_prompt(arguments)
            elif name == "record_round_response":
                return await self._handle_record_round_response(arguments)
            elif name == "get_session_status":
                return await self._handle_get_session_status(arguments)
            elif name == "list_available_personas":
                return await self._handle_list_available_personas(arguments)
            elif name == "recommend_personas":
                return await self._handle_recommend_personas(arguments)
            elif name == "view_session_history":
                return await self._handle_view_session_history(arguments)
            elif name == "export_session":
                return await self._handle_export_session(arguments)
            elif name == "advance_to_next_round":
                return await self._handle_advance_to_next_round(arguments)
            elif name == "get_usage_statistics":
                return await self._handle_get_usage_statistics(arguments)
            else:
                return [TextContent(type="text", text=f"❌ 未知工具: {name}")]

    async def _handle_start_pk_session(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """启动新的PK会话"""
        try:
            question = arguments.get("question", "").strip()
            personas = arguments.get("personas", [])

            if not question:
                return [
                    TextContent(
                        type="text",
                        text='❌ 请提供一个问题来启动PK会话。\n\n使用方法：start_pk_session({"question": "你的问题", "personas": ["苏格拉底", "埃隆马斯克", "查理芒格"]})',
                    )
                ]

            # 如果没有指定personas，使用默认的三位
            if not personas:
                personas = ["苏格拉底", "埃隆马斯克", "查理芒格"]

            # 验证personas（包括自定义的）
            all_personas = self.custom_persona_manager.get_all_personas(PERSONAS)
            valid_personas = []
            for persona in personas:
                if persona in all_personas:
                    valid_personas.append(persona)

            if len(valid_personas) < 3:
                available = ", ".join(all_personas.keys())
                return [
                    TextContent(
                        type="text",
                        text=f"❌ 需要选择3位思想家。可选择的思想家：{available}",
                    )
                ]

            # 创建新会话
            session = PKSession.create_new(question, valid_personas[:3])
            self.current_session = session
            self.session_manager.save_session(session)

            # 生成启动信息
            personas_info = "\n".join(
                [
                    f"{i+1}. {format_persona_info(p)}"
                    for i, p in enumerate(session.selected_personas)
                ]
            )

            result = f"""🎯 **专家PK会话已启动！**

**会话ID**: `{session.session_id}`
**问题**: {session.user_question}

**参与的三位专家**：
{personas_info}

📍 **当前状态**: 第1轮 - 独立思考阶段
👤 **即将发言**: {format_persona_info(session.get_current_persona())}

💡 **下一步**: 使用 `get_persona_prompt` 工具获取当前专家的角色提示，然后让我扮演该专家来回答您的问题。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 启动会话失败: {str(e)}")]

        # 工具2: 获取思想家角色prompt

    async def _handle_get_persona_prompt(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """获取当前思想家的角色prompt"""
        try:
            if not self.current_session:
                return [
                    TextContent(
                        type="text",
                        text="❌ 没有活跃的会话。请先使用 start_pk_session 启动一个会话。",
                    )
                ]

            session = self.current_session
            current_persona = session.get_current_persona()

            if not current_persona:
                return [TextContent(type="text", text="❌ 当前会话已完成所有轮次。")]

            # 准备上下文
            context = {"question": session.user_question}

            if session.current_round == 2:
                # 第2轮需要看到第1轮其他人的回答
                if 1 in session.responses:
                    context["my_previous_response"] = session.responses[1].get(
                        current_persona, ""
                    )
                    context["other_responses"] = {  # type: ignore
                        k: v
                        for k, v in session.responses[1].items()
                        if k != current_persona
                    }

            elif session.current_round == 3:
                # 第3轮需要看到前两轮的所有回答
                context["all_previous_responses"] = {  # type: ignore
                    k: v for k, v in session.responses.items() if k < 3
                }

            elif session.current_round == 4:
                # 第4轮需要看到第3轮的最终回答
                if 3 in session.responses:
                    context["final_responses"] = session.responses[3]  # type: ignore

            # 生成prompt
            prompt = generate_round_prompt(
                current_persona,
                session.current_round,
                context,
                self.custom_persona_manager.custom_personas,
            )

            # 返回格式化的prompt信息
            round_names = {
                1: "第1轮：独立思考",
                2: "第2轮：交叉辩论",
                3: "第3轮：最终立场",
                4: "第4轮：智慧综合",
            }

            result = f"""🎭 **角色扮演提示**

**会话**: {session.session_id}
**轮次**: {round_names.get(session.current_round, f"第{session.current_round}轮")}
**角色**: {format_persona_info(current_persona)}

---

**请现在扮演这个角色，使用以下指导来回答用户的问题：**

{prompt}

---

💡 **提示**: 完全进入角色，用该思想家的语言风格、思维方式来回答。回答完成后，请使用 `record_round_response` 工具记录你的回答。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取提示失败: {str(e)}")]

        # 工具3: 记录回答

    async def _handle_record_round_response(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """记录当前轮次的回答"""
        try:
            if not self.current_session:
                return [TextContent(type="text", text="❌ 没有活跃的会话。")]

            response = arguments.get("response", "").strip()
            if not response:
                return [
                    TextContent(
                        type="text",
                        text='❌ 请提供回答内容。\n\n使用方法：record_round_response({"response": "你的回答内容"})',
                    )
                ]

            session = self.current_session
            current_persona = session.get_current_persona()

            if not current_persona:
                return [TextContent(type="text", text="❌ 当前会话已完成。")]

            # 记录回答
            session.record_response(current_persona, response)

            # 检查是否是第4轮（综合分析）
            if session.current_round == 4:
                session.final_synthesis = response
                self.session_manager.save_session(session)

                return [
                    TextContent(
                        type="text",
                        text=f"""✅ **最终综合分析已完成！**

🎉 **会话 {session.session_id} 圆满结束**

📝 所有专家的智慧已经融合成最终方案。您可以使用 `view_session_history` 查看完整的讨论记录。

💡 **提示**: 您可以开始新的PK会话来探讨其他问题，或者查看这次讨论的完整历史。""",
                    )
                ]

            # 切换到下一个专家或下一轮
            has_next = session.advance_to_next_persona()
            self.session_manager.save_session(session)

            if not has_next:
                return [
                    TextContent(
                        type="text",
                        text=f"""✅ **所有轮次已完成！**

🎉 **三位专家的讨论已经结束**
📊 **最终统计**:
- 总回答数: {len([r for round_responses in session.responses.values() for r in round_responses.values()])}
- 参与专家: {', '.join(session.selected_personas)}

使用 `view_session_history` 查看完整讨论记录。""",
                    )
                ]

            # 准备下一步提示
            next_persona = session.get_current_persona()
            round_names = {
                1: "第1轮：独立思考",
                2: "第2轮：交叉辩论",
                3: "第3轮：最终立场",
                4: "第4轮：智慧综合",
            }

            result = f"""✅ **回答已记录！**

**{current_persona}** 的观点已保存。

📍 **下一步**:
- **轮次**: {round_names.get(session.current_round, f"第{session.current_round}轮")}
- **发言者**: {format_persona_info(next_persona)}

💡 使用 `get_persona_prompt` 获取下一位专家的角色提示。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 记录回答失败: {str(e)}")]

        # 工具4: 获取会话状态

    async def _handle_get_session_status(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """获取当前会话状态"""
        try:
            if not self.current_session:
                return [
                    TextContent(
                        type="text",
                        text="❌ 没有活跃的会话。请先使用 start_pk_session 启动一个会话。",
                    )
                ]

            status = self.current_session.get_session_status()

            # 计算进度
            total_expected = (
                len(self.current_session.selected_personas) * 3 + 1
            )  # 3轮*3人 + 1综合
            completed = status["completed_responses"]
            progress = f"{completed}/{total_expected}"

            result = f"""📊 **会话状态报告**

**会话ID**: `{status['session_id']}`
**问题**: {status['question']}

**当前进展**:
- 🎯 **当前轮次**: {status['round_name']}
- 👤 **当前发言者**: {format_persona_info(status['current_persona']) if status['current_persona'] else '已完成'}
- 📈 **完成进度**: {progress}

**参与专家**: {', '.join([format_persona_info(p) for p in status['personas']])}

**状态**: {'✅ 已完成' if status['is_completed'] else '🔄 进行中'}"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取状态失败: {str(e)}")]

        # 工具5: 列出可用思想家

    async def _handle_list_available_personas(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """列出所有可用的思想家"""
        try:
            # 内置思想家
            builtin_personas = get_available_personas()
            # 自定义思想家
            custom_personas = self.custom_persona_manager.list_custom_personas()

            result = "🎭 **可用的思想家专家**\n\n"

            # 内置思想家
            result += "## 📚 内置专家\n\n"
            for i, persona in enumerate(builtin_personas, 1):
                result += f"{i}. {persona['emoji']} **{persona['name']}**\n"
                result += f"   📝 {persona['description']}\n"
                result += f"   🔑 核心特质: {', '.join(persona['traits'])}\n\n"

            # 自定义思想家
            if custom_personas:
                result += "## 👤 自定义专家\n\n"
                for i, persona in enumerate(custom_personas, len(builtin_personas) + 1):
                    result += (
                        f"{i}. {persona['emoji']} **{persona['name']}** (自定义)\n"
                    )
                    result += f"   📝 {persona['description']}\n"
                    result += f"   🔑 核心特质: {', '.join(persona['traits'])}\n\n"
            else:
                result += "## 👤 自定义专家\n\n暂无自定义专家。使用 `create_custom_persona` 创建专属专家。\n\n"

            result += "💡 **使用提示**: 在 start_pk_session 中指定 personas 参数来选择专家组合。\n"
            result += '例如: `start_pk_session({"question": "你的问题", "personas": ["苏格拉底", "埃隆马斯克", "查理芒格"]})`'

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取思想家列表失败: {str(e)}")]

        # 工具6: 查看会话历史

    async def _handle_view_session_history(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """查看会话历史"""
        try:

            session_id = arguments.get("session_id")
            if session_id:
                # 查看指定会话
                session = self.session_manager.load_session(session_id)
                if not session:
                    return [
                        TextContent(type="text", text=f"❌ 未找到会话 {session_id}")
                    ]
            else:
                # 查看当前会话
                if not self.current_session:
                    return [
                        TextContent(
                            type="text",
                            text="❌ 没有活跃的会话。请提供 session_id 参数查看历史会话。",
                        )
                    ]
                session = self.current_session

            result = f"""📚 **会话讨论历史**

**会话ID**: `{session.session_id}`
**问题**: {session.user_question}
**创建时间**: {session.created_at}
**参与专家**: {', '.join([format_persona_info(p) for p in session.selected_personas])}

---

"""

            round_names = {
                1: "🤔 第1轮：独立思考",
                2: "💬 第2轮：交叉辩论",
                3: "🎯 第3轮：最终立场",
                4: "🧠 第4轮：智慧综合",
            }

            for round_num in sorted(session.responses.keys()):
                result += f"## {round_names.get(round_num, f'第{round_num}轮')}\n\n"

                for persona, response in session.responses[round_num].items():
                    result += f"### {format_persona_info(persona)}\n\n"
                    result += f"{response}\n\n---\n\n"

            if session.final_synthesis:
                result += f"## 🌟 最终综合方案\n\n{session.final_synthesis}\n\n"

            result += "📊 **统计信息**:\n"
            result += f"- 总发言数: {len([r for round_responses in session.responses.values() for r in round_responses.values()])}\n"
            result += f"- 字数统计: {sum(len(r) for round_responses in session.responses.values() for r in round_responses.values()):,} 字符\n"
            result += f"- 最后更新: {session.updated_at}"

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 查看历史失败: {str(e)}")]

        # 工具7: 进入下一轮

    async def _handle_advance_to_next_round(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """手动进入下一轮或下一个专家"""
        try:
            if not self.current_session:
                return [TextContent(type="text", text="❌ 没有活跃的会话。")]

            session = self.current_session
            current_persona = session.get_current_persona()

            if not current_persona:
                return [TextContent(type="text", text="✅ 会话已经完成了所有轮次。")]

            # 切换到下一个
            has_next = session.advance_to_next_persona()
            self.session_manager.save_session(session)

            if not has_next:
                return [TextContent(type="text", text="✅ 所有轮次已完成！")]

            next_persona = session.get_current_persona()
            round_names = {
                1: "第1轮：独立思考",
                2: "第2轮：交叉辩论",
                3: "第3轮：最终立场",
                4: "第4轮：智慧综合",
            }

            result = f"""⏭️ **已切换到下一位专家**

📍 **当前状态**:
- **轮次**: {round_names.get(session.current_round, f"第{session.current_round}轮")}
- **发言者**: {format_persona_info(next_persona)}

💡 使用 `get_persona_prompt` 获取角色提示。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 切换失败: {str(e)}")]

        # 工具8: 获取轮次上下文

    async def _handle_get_context_for_round(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """获取当前轮次的详细上下文信息"""
        try:
            if not self.current_session:
                return [TextContent(type="text", text="❌ 没有活跃的会话。")]

            session = self.current_session
            round_num = session.current_round
            current_persona = session.get_current_persona()

            result = f"""📋 **轮次上下文信息**

**会话**: {session.session_id}
**问题**: {session.user_question}
**当前轮次**: 第{round_num}轮
**当前专家**: {format_persona_info(current_persona) if current_persona else '已完成'}

---

"""

            if round_num == 1:
                result += "**第1轮要求**: 独立思考，不参考其他人观点，纯粹基于自己的思维风格分析问题。\n\n"

            elif round_num == 2:
                result += "**第2轮要求**: 交叉辩论，审视其他专家的观点，指出优劣，升华自己的方案。\n\n"
                if 1 in session.responses:
                    result += "**第1轮各专家观点**:\n"
                    for persona, response in session.responses[1].items():
                        result += f"- **{persona}**: {response[:100]}...\n"
                    result += "\n"

            elif round_num == 3:
                result += "**第3轮要求**: 最终立场，综合前两轮讨论，给出最完善的解决方案。\n\n"
                for r in [1, 2]:
                    if r in session.responses:
                        result += f"**第{r}轮回顾**:\n"
                        for persona, response in session.responses[r].items():
                            result += f"- **{persona}**: {response[:80]}...\n"
                        result += "\n"

            elif round_num == 4:
                result += "**第4轮要求**: 智慧综合，分析融合三位专家的最终方案。\n\n"
                if 3 in session.responses:
                    result += "**各专家最终方案**:\n"
                    for persona, response in session.responses[3].items():
                        result += f"- **{persona}**: {response[:100]}...\n"
                    result += "\n"

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取上下文失败: {str(e)}")]

        # 工具9: 综合最终答案

    async def _handle_synthesize_final_answer(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """生成最终综合答案（第4轮专用）"""
        try:
            if not self.current_session:
                return [TextContent(type="text", text="❌ 没有活跃的会话。")]

            session = self.current_session

            # 检查是否已经有三轮完整的讨论
            if session.current_round < 4 or 3 not in session.responses:
                return [
                    TextContent(
                        type="text",
                        text="❌ 需要先完成前三轮讨论才能进行最终综合。",
                    )
                ]

            if len(session.responses[3]) < 3:
                return [
                    TextContent(
                        type="text",
                        text="❌ 第3轮讨论尚未完成，需要所有专家都给出最终立场。",
                    )
                ]

            # 准备综合分析的上下文
            context = {
                "question": session.user_question,
                "final_responses": session.responses[3],
            }

            # 生成综合分析的prompt
            synthesis_prompt = generate_round_prompt(
                "综合大师", 4, context, self.custom_persona_manager.custom_personas
            )

            result = f"""🧠 **准备进行最终综合分析**

所有专家的讨论已经完成，现在需要将三位专家的智慧融合成终极方案。

**请使用以下指导进行综合分析**:

---

{synthesis_prompt}

---

💡 **提示**: 完成综合分析后，请使用 `record_round_response` 工具记录最终的综合方案。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 准备综合分析失败: {str(e)}")]

        # 新增工具: 列出历史会话

    async def _handle_list_sessions(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """列出所有历史会话"""
        try:
            sessions = self.session_manager.list_sessions()

            if not sessions:
                return [
                    TextContent(
                        type="text",
                        text="📝 暂无历史会话。使用 start_pk_session 创建第一个专家PK会话吧！",
                    )
                ]

            result = "📚 **历史会话列表**\n\n"

            for i, session in enumerate(sessions[:10], 1):  # 只显示最近10个
                status_icon = "✅" if session["is_completed"] else "🔄"
                result += f"{i}. {status_icon} **{session['session_id']}**\n"
                result += f"   📝 {session['question']}\n"
                result += f"   👥 专家: {', '.join(session['personas'])}\n"
                result += f"   📅 {session['created_at'][:19].replace('T', ' ')}\n\n"

            if len(sessions) > 10:
                result += f"... 还有 {len(sessions) - 10} 个历史会话\n\n"

            result += '💡 **提示**: 使用 `view_session_history({"session_id": "会话ID"})` 查看详细内容。'

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取会话列表失败: {str(e)}")]

        # 新增工具: 继续历史会话

    async def _handle_resume_session(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """继续一个历史会话"""
        try:
            session_id = arguments.get("session_id", "").strip()

            if not session_id:
                return [
                    TextContent(
                        type="text",
                        text='❌ 请提供会话ID。\n\n使用方法：resume_session({"session_id": "会话ID"})',
                    )
                ]

            session = self.session_manager.load_session(session_id)
            if not session:
                return [
                    TextContent(
                        type="text",
                        text=f"❌ 未找到会话 {session_id}。使用 list_sessions 查看可用会话。",
                    )
                ]

            self.current_session = session
            status = session.get_session_status()

            if status["is_completed"]:
                result = f"""✅ **会话已加载（已完成）**

**会话ID**: `{session.session_id}`
**问题**: {session.user_question}
**状态**: 已完成所有轮次

💡 使用 `view_session_history` 查看完整讨论记录，或 `start_pk_session` 开始新的讨论。"""
            else:
                current_persona = session.get_current_persona()
                round_names = {
                    1: "第1轮：独立思考",
                    2: "第2轮：交叉辩论",
                    3: "第3轮：最终立场",
                    4: "第4轮：智慧综合",
                }

                result = f"""🔄 **会话已恢复**

**会话ID**: `{session.session_id}`
**问题**: {session.user_question}

📍 **当前状态**:
- **轮次**: {round_names.get(session.current_round, f"第{session.current_round}轮")}
- **待发言**: {format_persona_info(current_persona)}
- **进度**: {status['completed_responses']}/{len(session.selected_personas) * 3 + 1}

💡 使用 `get_persona_prompt` 获取当前专家的角色提示。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 恢复会话失败: {str(e)}")]

        # Phase 3 工具: 创建自定义思想家

    async def _handle_create_custom_persona(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """创建自定义思想家"""
        try:
            # 检查必填字段
            persona_name = arguments.get("name", "")
            description = arguments.get("description", "")
            core_traits = arguments.get("core_traits", [])
            speaking_style = arguments.get("speaking_style", "")
            base_prompt = arguments.get("base_prompt", "")

            if (
                not persona_name
                or not description
                or not core_traits
                or not speaking_style
                or not base_prompt
            ):
                return [
                    TextContent(
                        type="text",
                        text="❌ 所有字段都是必填的\n\n必填字段: name, description, core_traits, speaking_style, base_prompt",
                    )
                ]

            # 检查名称冲突
            all_personas = self.custom_persona_manager.get_all_personas(PERSONAS)
            if persona_name in all_personas:
                return [
                    TextContent(
                        type="text",
                        text=f"❌ 思想家名称 '{persona_name}' 已存在。请使用不同的名称。",
                    )
                ]

            # 添加自定义思想家
            persona_data = {
                "name": persona_name,
                "description": description,
                "core_traits": core_traits,
                "speaking_style": speaking_style,
                "base_prompt": base_prompt,
            }
            success = self.custom_persona_manager.add_custom_persona(persona_data)

            if success:
                result = f"""✅ **自定义思想家创建成功！**

👤 **{persona_name}** 已添加到专家库

📝 **基本信息**:
- 描述: {description}
- 核心特质: {', '.join(core_traits)}
- 语言风格: {speaking_style}

💡 现在您可以在 start_pk_session 中使用这位专家了！"""

                return [TextContent(type="text", text=result)]
            else:
                return [
                    TextContent(type="text", text="❌ 创建失败，请检查输入数据格式。")
                ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 创建自定义思想家失败: {str(e)}")]

        # Phase 3 工具: 导出会话

    async def _handle_export_session(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """导出会话数据"""
        try:
            session_id = arguments.get("session_id")
            if session_id:
                session = self.session_manager.load_session(session_id)
                if not session:
                    return [
                        TextContent(type="text", text=f"❌ 未找到会话 {session_id}")
                    ]
            else:
                if not self.current_session:
                    return [
                        TextContent(
                            type="text",
                            text="❌ 没有活跃的会话。请提供 session_id 参数。",
                        )
                    ]
                session = self.current_session

            # 生成Markdown内容
            md_content = f"""# 专家PK讨论记录

**会话ID**: {session.session_id}
**问题**: {session.user_question}
**创建时间**: {session.created_at}
**参与专家**: {', '.join(session.selected_personas)}

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

            if session.final_synthesis:
                md_content += f"## 🌟 最终综合方案\n\n{session.final_synthesis}\n\n"

            md_content += f"""## 📊 统计信息

- **总发言数**: {len([r for round_responses in session.responses.values() for r in round_responses.values()])}
- **字数统计**: {sum(len(r) for round_responses in session.responses.values() for r in round_responses.values()):,} 字符
- **最后更新**: {session.updated_at}

---
*由 Guru-PK MCP 系统生成*"""

            # 保存到文件
            export_file = (
                self.session_manager.data_dir / f"export_{session.session_id}.md"
            )
            with open(export_file, "w", encoding="utf-8") as f:
                f.write(md_content)

            result = f"""📄 **会话导出成功！**

**文件路径**: `{export_file}`
**格式**: Markdown
**内容**: 完整的讨论记录和统计信息

💡 您可以用任何Markdown编辑器打开该文件，或者分享给他人查看。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 导出失败: {str(e)}")]

        # Phase 3 工具: 智能推荐思想家

    async def _handle_recommend_personas(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """根据问题类型智能推荐专家组合"""
        try:
            question = arguments.get("question", "").strip()
            if not question:
                return [
                    TextContent(
                        type="text",
                        text='❌ 请提供问题内容。\n\n使用方法：recommend_personas({"question": "你的问题"})',
                    )
                ]

            # 简单的关键词匹配推荐算法
            recommendations = []
            question_lower = question.lower()

            # 推荐规则
            if any(
                word in question_lower
                for word in ["创业", "商业", "投资", "经营", "企业", "生意"]
            ):
                recommendations = [
                    {
                        "combo": ["埃隆马斯克", "查理芒格", "稻盛和夫"],
                        "reason": "商业创新组合：第一性原理创新思维 + 投资智慧 + 经营哲学",
                        "score": 95,
                    },
                    {
                        "combo": ["史蒂夫乔布斯", "埃隆马斯克", "稻盛和夫"],
                        "reason": "产品创新组合：极致产品思维 + 颠覆式创新 + 匠人精神",
                        "score": 90,
                    },
                ]

            elif any(
                word in question_lower
                for word in ["人生", "成长", "学习", "认知", "思维", "心理"]
            ):
                recommendations = [
                    {
                        "combo": ["苏格拉底", "大卫伯恩斯", "吉杜克里希那穆提"],
                        "reason": "心理成长组合：哲学思辨 + CBT技巧 + 内在觉察",
                        "score": 95,
                    },
                    {
                        "combo": ["王阳明", "曾国藩", "稻盛和夫"],
                        "reason": "修身养性组合：知行合一 + 品格修养 + 人格典范",
                        "score": 90,
                    },
                ]

            elif any(
                word in question_lower
                for word in ["系统", "管理", "复杂", "问题", "解决", "策略"]
            ):
                recommendations = [
                    {
                        "combo": ["杰伊福雷斯特", "查理芒格", "苏格拉底"],
                        "reason": "系统分析组合：系统动力学 + 多元思维 + 批判思辨",
                        "score": 95,
                    },
                    {
                        "combo": ["杰伊福雷斯特", "埃隆马斯克", "王阳明"],
                        "reason": "创新解决组合：系统思维 + 创新突破 + 知行合一",
                        "score": 88,
                    },
                ]

            elif any(
                word in question_lower
                for word in ["产品", "设计", "用户", "体验", "技术"]
            ):
                recommendations = [
                    {
                        "combo": ["史蒂夫乔布斯", "埃隆马斯克", "孙子"],
                        "reason": "产品创新组合：极致体验 + 技术创新 + 战略思维",
                        "score": 92,
                    },
                    {
                        "combo": ["史蒂夫乔布斯", "稻盛和夫", "苏格拉底"],
                        "reason": "完美主义组合：产品极致 + 匠人精神 + 深度思考",
                        "score": 88,
                    },
                ]

            else:
                # 默认通用推荐
                recommendations = [
                    {
                        "combo": ["苏格拉底", "埃隆马斯克", "查理芒格"],
                        "reason": "经典全能组合：哲学思辨 + 创新思维 + 投资智慧",
                        "score": 90,
                    },
                    {
                        "combo": ["苏格拉底", "卡尔波普尔", "杰伊福雷斯特"],
                        "reason": "理性分析组合：批判思维 + 科学方法 + 系统思维",
                        "score": 85,
                    },
                ]

            # 检查推荐的专家是否都可用
            all_personas = self.custom_persona_manager.get_all_personas(PERSONAS)
            valid_recommendations = []

            for rec in recommendations:
                if all(persona in all_personas for persona in rec["combo"]):  # type: ignore
                    valid_recommendations.append(rec)

            if not valid_recommendations:
                return [
                    TextContent(
                        type="text", text="❌ 无法生成推荐，请检查可用专家列表。"
                    )
                ]

            result = f"""🎯 **智能专家推荐**

**问题**: {question}

**推荐组合**:\n\n"""

            for i, rec in enumerate(valid_recommendations[:3], 1):
                result += f"## {i}. 推荐指数: {rec['score']}/100\n\n"
                result += f"**专家组合**: {', '.join([format_persona_info(p) for p in rec['combo']])}\n\n"  # type: ignore
                result += f"**推荐理由**: {rec['reason']}\n\n"
                result += f"💡 使用命令: `start_pk_session({{\"question\": \"{question}\", \"personas\": {rec['combo']}}})`\n\n"
                result += "---\n\n"

            result += "💭 **提示**: 这些推荐基于问题关键词匹配。您也可以自由组合任意三位专家。"

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 生成推荐失败: {str(e)}")]

        # 工具2: 获取帮助信息

    async def _handle_guru_pk_help(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """获取系统帮助和介绍"""
        help_text = """# 🎭 Guru-PK MCP 专家辩论系统

欢迎使用Guru-PK！这是一个基于MCP协议的AI专家辩论系统，让您能够与13位顶级思想家进行多轮深度对话。

## 🌟 核心特色

- **🎭 13位内置专家**：涵盖哲学、经济学、心理学、战略学、创新思维等领域
- **🔄 4轮PK流程**：独立思考 → 交叉辩论 → 最终立场 → 智慧综合
- **🛠️ 自定义专家**：创建您专属的思想家角色
- **📚 会话管理**：保存、查看、导出、恢复讨论历史

## 📋 可用工具

### 核心功能
- `start_pk_session` - 启动专家PK会话
- `get_persona_prompt` - 获取当前专家角色提示
- `record_round_response` - 记录专家发言
- `get_session_status` - 查看会话状态

### 专家管理
- `list_available_personas` - 查看所有可用专家
- `recommend_personas` - 智能推荐专家组合

### 会话管理
- `view_session_history` - 查看会话历史
- `export_session` - 导出会话记录
- `advance_to_next_round` - 手动切换到下一轮/专家

### 高级功能
- `get_usage_statistics` - 查看使用统计
- `guru_pk_help` - 获取系统帮助（本工具）

## 🚀 快速开始

1. **启动PK会话**：
```
start_pk_session({
  "question": "如何在AI时代保持竞争力？",
  "personas": ["苏格拉底", "埃隆马斯克", "查理芒格"]
})
```

2. **获取智能推荐**：
```
recommend_personas({
  "question": "我想创业，但不知道选什么方向"
})
```

3. **查看可用专家**：
```
list_available_personas({})
```

## 🎭 内置专家阵容（13位）

### 哲学思辨
- **🧠 苏格拉底** - 古希腊哲学家，以思辨和质疑著称
- **☯️ 王阳明** - 明代心学大师，知行合一的倡导者
- **🧘 吉杜·克里希那穆提** - 觉察智慧导师，当下生活的哲学家

### 商业创新
- **🚀 埃隆·马斯克** - 现代创新教父，第一性原理思维大师
- **📚 查理·芒格** - 投资智慧大师，多元思维模型的倡导者
- **🍎 史蒂夫·乔布斯** - 产品完美主义者，用户体验至上的创新者
- **🌸 稻盛和夫** - 经营之圣，敬天爱人的经营哲学家

### 经济战略
- **💰 路德维希·冯·米塞斯** - 奥地利经济学派巨匠，人类行动学理论创始人
- **⚔️ 孙子** - 兵学圣祖，战略思维的绝对王者
- **📖 曾国藩** - 理学大师，中兴名臣，修身治国的典范

### 科学方法
- **🔬 卡尔·波普尔** - 科学哲学巨匠，可证伪性理论创立者
- **🔄 杰伊·福雷斯特** - 系统动力学之父，反馈环理论创建者
- **🧠 大卫·伯恩斯** - CBT心理学大师，《感受的事实》作者

## 🌟 热门专家组合推荐

- **投资决策组**：路德维希·冯·米塞斯 + 查理·芒格 + 埃隆·马斯克
- **心理成长组**：苏格拉底 + 大卫·伯恩斯 + 吉杜·克里希那穆提
- **战略决策组**：孙子 + 曾国藩 + 查理·芒格
- **科学理性组**：卡尔·波普尔 + 苏格拉底 + 杰伊·福雷斯特

## 🎯 典型对话流程

1. **启动会话** - 选择问题和三位专家
2. **第1轮：独立思考** - 每位专家独立分析问题
3. **第2轮：交叉辩论** - 专家互相批评和借鉴
4. **第3轮：最终立场** - 形成各自的最终方案
5. **第4轮：智慧综合** - 融合三者智慧的终极答案

💡 **提示**：直接提出您的问题，系统会自动推荐合适的专家组合！

---
*由 Guru-PK MCP 系统提供 - 让思想碰撞，让智慧闪光！*"""

        return [TextContent(type="text", text=help_text)]

        # Phase 3 工具: 统计分析

    async def _handle_get_usage_statistics(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """获取使用统计和分析"""
        try:
            sessions = self.session_manager.list_sessions()

            if not sessions:
                return [
                    TextContent(
                        type="text",
                        text="📊 暂无使用数据。创建一些PK会话后再来查看统计信息吧！",
                    )
                ]

            # 基础统计
            total_sessions = len(sessions)
            completed_sessions = len([s for s in sessions if s["is_completed"]])
            completion_rate = (
                (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
            )

            # 专家使用统计
            persona_usage: dict[str, int] = {}
            for session in sessions:
                for persona in session["personas"]:
                    persona_usage[persona] = persona_usage.get(persona, 0) + 1

            # 最受欢迎的专家
            popular_personas = sorted(
                persona_usage.items(), key=lambda x: x[1], reverse=True
            )[:5]

            # 时间分析
            from datetime import datetime

            now = datetime.now()
            recent_sessions = [
                s
                for s in sessions
                if (now - datetime.fromisoformat(s["created_at"])).days <= 7
            ]

            # 问题类型分析（简单关键词统计）
            question_keywords: dict[str, int] = {}
            for session in sessions:
                question = session["question"].lower()
                # 统计常见关键词
                for keyword in [
                    "创业",
                    "投资",
                    "人生",
                    "学习",
                    "产品",
                    "管理",
                    "系统",
                    "心理",
                ]:
                    if keyword in question:
                        question_keywords[keyword] = (
                            question_keywords.get(keyword, 0) + 1
                        )

            result = f"""📊 **使用统计分析**

## 📈 基础数据
- **总会话数**: {total_sessions}
- **已完成**: {completed_sessions} ({completion_rate:.1f}%)
- **最近7天**: {len(recent_sessions)} 个会话

## 🏆 热门专家排行
"""

            for i, (persona, count) in enumerate(popular_personas, 1):
                percentage = (count / total_sessions * 100) if total_sessions > 0 else 0
                result += f"{i}. {format_persona_info(persona)} - {count}次 ({percentage:.1f}%)\n"

            result += "\n## 🔍 问题领域分析\n"
            if question_keywords:
                for keyword, count in sorted(
                    question_keywords.items(), key=lambda x: x[1], reverse=True
                )[:5]:
                    percentage = (
                        (count / total_sessions * 100) if total_sessions > 0 else 0
                    )
                    result += f"- **{keyword}**: {count}次 ({percentage:.1f}%)\n"
            else:
                result += "暂无足够数据进行分析\n"

            # 详细会话信息
            if total_sessions > 0:
                # 计算平均字数
                total_chars = 0
                total_responses = 0

                for session in sessions:
                    if session["is_completed"]:
                        # 这里需要加载完整会话来计算字数
                        full_session = self.session_manager.load_session(
                            session["session_id"]
                        )
                        if full_session:
                            for round_responses in full_session.responses.values():
                                for response in round_responses.values():
                                    total_chars += len(response)
                                    total_responses += 1
                            if full_session.final_synthesis:
                                total_chars += len(full_session.final_synthesis)
                                total_responses += 1

                avg_chars = total_chars // total_responses if total_responses > 0 else 0

                result += f"""
## 💬 讨论质量
- **总发言数**: {total_responses}
- **平均每次发言**: {avg_chars:,} 字符
- **总讨论字数**: {total_chars:,} 字符

## 📅 活跃度
- **最近会话**: {sessions[0]['created_at'][:19].replace('T', ' ')}
- **本周会话**: {len(recent_sessions)}个"""

            result += """

## 🎯 使用建议
- 尝试不同的专家组合来获得多元化视角
- 完成更多会话以获得更深入的洞察
- 使用 `recommend_personas` 获得智能推荐"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取统计失败: {str(e)}")]

    async def run(self) -> None:
        """运行MCP服务器"""
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="guru-pk",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def async_main() -> None:
    """异步主函数"""
    guru_server = GuruPKServer()
    await guru_server.run()


def main() -> None:
    """同步入口点函数"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
