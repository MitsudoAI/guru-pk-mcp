"""
Guru-PK MCP 服务器
"""

import asyncio
from datetime import datetime
from typing import Any

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import TextContent

from .config import ConfigManager
from .custom_personas import CustomPersonaManager
from .models import PKSession
from .personas import (
    PERSONAS,
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

        self.custom_persona_manager = CustomPersonaManager(data_dir)
        self.session_manager = SessionManager(data_dir, self.custom_persona_manager)
        self.config_manager = ConfigManager(data_dir)
        self.current_session: PKSession | None = None
        self.pending_recommendation: dict[str, Any] | None = None
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
                                "description": "参与讨论的三位专家名称（可选，如不提供将使用智能推荐）",
                            },
                            "recommended_by_host": {
                                "type": "boolean",
                                "description": "是否由MCP Host端智能推荐（内部使用）",
                            },
                        },
                        "required": ["question"],
                    },
                ),
                types.Tool(
                    name="get_smart_recommendation_guidance",
                    description="获取智能专家推荐指导（MCP Host端LLM使用）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "要分析的问题内容",
                            }
                        },
                        "required": ["question"],
                    },
                ),
                types.Tool(
                    name="analyze_question_profile",
                    description="深度分析问题特征和复杂度（新功能）",
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
                    name="generate_dynamic_experts",
                    description="动态生成专家推荐（5位候选专家）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "要讨论的问题",
                            },
                            "num_experts": {
                                "type": "integer",
                                "description": "推荐专家数量（默认5个）",
                                "default": 5,
                            },
                        },
                        "required": ["question"],
                    },
                ),
                types.Tool(
                    name="get_session_quality_analysis",
                    description="获取会话质量分析和改进建议",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "会话ID（可选，默认当前会话）",
                            }
                        },
                    },
                ),
                types.Tool(
                    name="get_expert_insights",
                    description="获取专家洞察和关系分析",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "会话ID（可选，默认当前会话）",
                            }
                        },
                    },
                ),
                types.Tool(
                    name="export_enhanced_session",
                    description="导出增强的会话分析报告",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "会话ID（可选，默认当前会话）",
                            }
                        },
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
                types.Tool(
                    name="create_custom_persona_from_description",
                    description="根据自然语言描述智能创建自定义专家（需要MCP Host端LLM生成完整专家数据）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "用自然语言描述想要创建的专家，例如：'我想要一个现代教育领域最顶尖的大师'",
                            }
                        },
                        "required": ["description"],
                    },
                ),
                types.Tool(
                    name="save_custom_persona",
                    description="保存由MCP Host端LLM生成的完整自定义专家数据",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "persona_data": {
                                "type": "object",
                                "description": "完整的专家数据对象",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "专家名称",
                                    },
                                    "emoji": {
                                        "type": "string",
                                        "description": "专家表情符号",
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "专家简介描述",
                                    },
                                    "core_traits": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "核心特质列表",
                                    },
                                    "speaking_style": {
                                        "type": "string",
                                        "description": "语言风格描述",
                                    },
                                    "base_prompt": {
                                        "type": "string",
                                        "description": "基础角色提示词",
                                    },
                                },
                                "required": [
                                    "name",
                                    "description",
                                    "core_traits",
                                    "speaking_style",
                                    "base_prompt",
                                ],
                            }
                        },
                        "required": ["persona_data"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="set_language",
                    description="设置专家回复使用的语言",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "language": {
                                "type": "string",
                                "enum": [
                                    "chinese",
                                    "english",
                                    "japanese",
                                    "korean",
                                    "french",
                                    "german",
                                    "spanish",
                                ],
                                "description": "语言代码：chinese(中文), english(英语), japanese(日语), korean(韩语), french(法语), german(德语), spanish(西语)",
                            }
                        },
                        "required": ["language"],
                    },
                ),
                types.Tool(
                    name="get_language_settings",
                    description="查看当前语言设置和支持的语言",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="select_experts_and_start_session",
                    description="从候选专家中选择3位并启动辩论会话",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selected_experts": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "选择的3位专家名称",
                                "minItems": 3,
                                "maxItems": 3,
                            }
                        },
                        "required": ["selected_experts"],
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
            elif name == "get_smart_recommendation_guidance":
                return await self._handle_get_smart_recommendation_guidance(arguments)
            elif name == "analyze_question_profile":
                return await self._handle_analyze_question_profile(arguments)
            elif name == "generate_dynamic_experts":
                return await self._handle_generate_dynamic_experts(arguments)
            elif name == "get_session_quality_analysis":
                return await self._handle_get_session_quality_analysis(arguments)
            elif name == "get_expert_insights":
                return await self._handle_get_expert_insights(arguments)
            elif name == "export_enhanced_session":
                return await self._handle_export_enhanced_session(arguments)
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
            elif name == "create_custom_persona_from_description":
                return await self._handle_create_custom_persona_from_description(
                    arguments
                )
            elif name == "save_custom_persona":
                return await self._handle_save_custom_persona(arguments)
            elif name == "set_language":
                return await self._handle_set_language(arguments)
            elif name == "get_language_settings":
                return await self._handle_get_language_settings(arguments)
            elif name == "select_experts_and_start_session":
                return await self._handle_select_experts_and_start_session(arguments)
            else:
                return [TextContent(type="text", text=f"❌ 未知工具: {name}")]

    async def _handle_start_pk_session(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """启动新的PK会话"""
        try:
            question = arguments.get("question", "").strip()
            personas = arguments.get("personas", [])
            recommended_by_host = arguments.get("recommended_by_host", False)

            if not question:
                return [
                    TextContent(
                        type="text",
                        text='❌ 请提供一个问题来启动PK会话。\n\n📋 **两种使用方式**：\n\n1️⃣ **智能推荐**（推荐）：\n```javascript\n// 步骤1: 获取推荐指导\nget_smart_recommendation_guidance({"question": "你的问题"})\n\n// 步骤2: 基于指导推荐专家，然后启动会话\nstart_pk_session({"question": "你的问题", "personas": ["推荐的专家1", "推荐的专家2", "推荐的专家3"], "recommended_by_host": true})\n```\n\n2️⃣ **手动指定**：\n```javascript\nstart_pk_session({"question": "你的问题", "personas": ["苏格拉底", "埃隆马斯克", "查理芒格"]})\n```',
                    )
                ]

            # 如果没有指定personas，生成候选专家供用户选择
            if not personas:
                try:
                    # 生成5个候选专家
                    recommendation = self.session_manager.expert_generator.generate_expert_recommendation(
                        question, num_experts=5
                    )

                    # 存储候选信息用于后续选择
                    self.pending_recommendation = {
                        "question": question,
                        "recommendation": recommendation,
                        "timestamp": datetime.now().isoformat(),
                    }

                    # 生成候选专家信息
                    candidates_info = "\n".join(
                        [
                            f"{i+1}. {expert.emoji} **{expert.name}** - {expert.description}"
                            for i, expert in enumerate(recommendation.experts)
                        ]
                    )

                    result = f"""🎯 **智能专家推荐系统 - 候选专家生成完成！**

**问题**: {question}
**推荐理由**: {recommendation.recommendation_reason}

**📋 五位候选专家**：
{candidates_info}

**🎯 下一步操作**：
请从上述5位专家中选择3位来参与辩论，使用以下命令：

```javascript
select_experts_and_start_session({{"selected_experts": ["专家1", "专家2", "专家3"]}})
```

💡 **建议**: 选择不同背景和观点的专家以获得更丰富的辩论视角。"""

                    return [TextContent(type="text", text=result)]

                except Exception as e:
                    # 如果动态推荐失败，显示手动输入提示
                    return [
                        TextContent(
                            type="text",
                            text=f'⚠️ **动态推荐失败，请手动指定专家**\n\n**错误**: {str(e)}\n\n**问题**: {question}\n\n📋 **手动指定方式**：\n```javascript\nstart_pk_session({{"question": "{question}", "personas": ["苏格拉底", "埃隆马斯克", "查理芒格"]}}\n```\n\n💡 **建议**: 使用 `list_available_personas` 查看所有可用专家。',
                        )
                    ]

            # 设置推荐理由
            if recommended_by_host:
                recommended_reason = "🤖 MCP Host端智能推荐组合"
            else:
                recommended_reason = "👤 用户手动指定组合"

            # 验证personas（包括自定义的）
            all_personas = self.custom_persona_manager.get_all_personas(PERSONAS)
            valid_personas = []
            invalid_personas = []

            for persona in personas:
                matched_persona = self._find_matching_persona(persona, all_personas)
                if matched_persona:
                    valid_personas.append(matched_persona)
                else:
                    invalid_personas.append(persona)

            if len(valid_personas) < 3:
                available = ", ".join(all_personas.keys())
                invalid_info = (
                    f"未找到的专家: {', '.join(invalid_personas)}"
                    if invalid_personas
                    else ""
                )
                error_msg = f"❌ 需要选择3位思想家。{invalid_info}\n\n可选择的思想家：{available}"
                return [
                    TextContent(
                        type="text",
                        text=error_msg,
                    )
                ]

            # 创建新会话（手动指定模式）
            session = self.session_manager.create_dynamic_session(
                question=question,
                selected_experts=valid_personas[:3],
                use_smart_recommendation=False,
            )
            self.current_session = session

            # 生成启动信息
            personas_info = "\n".join(
                [
                    f"{i+1}. {self._format_persona_info_with_custom(p)}"
                    for i, p in enumerate(session.selected_personas)
                ]
            )

            # 添加推荐原因
            recommendation_info = f"\n🎯 **专家组合**: {recommended_reason}\n"

            result = f"""🎯 **专家PK会话已启动！**

**会话ID**: `{session.session_id}`
**问题**: {session.user_question}
{recommendation_info}
**参与的三位专家**：
{personas_info}

📍 **当前状态**: 第1轮 - 独立思考阶段
👤 **即将发言**: {self._format_persona_info_with_custom(session.get_current_persona())}

💡 **下一步**: 使用 `get_persona_prompt` 工具获取当前专家的角色提示，然后让我扮演该专家来回答您的问题。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 启动会话失败: {str(e)}")]

    async def _handle_select_experts_and_start_session(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """从候选专家中选择3位并启动辩论会话"""
        try:
            selected_experts = arguments.get("selected_experts", [])

            if not selected_experts or len(selected_experts) != 3:
                return [
                    TextContent(
                        type="text",
                        text='❌ 请选择恰好3位专家。\n\n📋 **使用方式**：\n```javascript\nselect_experts_and_start_session({"selected_experts": ["专家1", "专家2", "专家3"]})\n```',
                    )
                ]

            # 检查是否有待选择的推荐
            if not self.pending_recommendation:
                return [
                    TextContent(
                        type="text",
                        text="❌ 没有待选择的专家推荐。请先调用 `start_pk_session` 生成候选专家。",
                    )
                ]

            recommendation = self.pending_recommendation["recommendation"]
            question = self.pending_recommendation["question"]

            # 验证选择的专家是否在候选列表中
            candidate_names = [expert.name for expert in recommendation.experts]
            invalid_experts = [
                name for name in selected_experts if name not in candidate_names
            ]

            if invalid_experts:
                return [
                    TextContent(
                        type="text",
                        text=f"❌ 以下专家不在候选列表中: {', '.join(invalid_experts)}\n\n**可选专家**: {', '.join(candidate_names)}",
                    )
                ]

            # 创建会话
            session = self.session_manager.create_dynamic_session(
                question=question,
                selected_experts=selected_experts,
                use_smart_recommendation=False,
            )
            self.current_session = session

            # 清除待选择的推荐
            self.pending_recommendation = None

            # 生成启动信息
            personas_info = "\n".join(
                [
                    f"{i+1}. {self._format_persona_info_with_custom(p)}"
                    for i, p in enumerate(session.selected_personas)
                ]
            )

            result = f"""🎯 **专家辩论会话已启动！**

**会话ID**: `{session.session_id}`
**问题**: {session.user_question}
**推荐理由**: 🤖 用户从智能推荐中选择

**选择的三位专家**：
{personas_info}

📍 **当前状态**: {session.get_round_description()}
👤 **即将发言**: {self._format_persona_info_with_custom(session.get_current_persona())}

💡 **下一步**: 使用 `get_persona_prompt` 工具获取当前专家的角色提示。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 选择专家失败: {str(e)}")]

    def _normalize_persona_name(self, name: str) -> str:
        """标准化专家名称，移除常见的差异字符"""
        # 移除中文标点符号和空格，统一为标准格式
        import re

        # 移除中文句号、英文句号、空格、全角空格等
        normalized = re.sub(r"[·\.\s\u3000]", "", name.strip())
        return normalized

    def _find_matching_persona(
        self, input_name: str, all_personas: dict[str, Any]
    ) -> str | None:
        """智能匹配专家名称，容忍常见的格式差异"""
        input_normalized = self._normalize_persona_name(input_name)

        # 首先尝试精确匹配
        if input_name in all_personas:
            return input_name

        # 然后尝试标准化匹配
        for persona_name in all_personas:
            if self._normalize_persona_name(persona_name) == input_normalized:
                return persona_name

        return None

    def _get_smart_recommendation(self, question: str) -> dict[str, Any] | None:
        """根据问题内容智能推荐专家组合"""
        try:
            question_lower = question.lower()
            recommendations: list[dict[str, Any]] = []

            # 教育学习类
            if any(
                word in question_lower
                for word in [
                    "教育",
                    "学习",
                    "英语",
                    "语言",
                    "学生",
                    "儿童",
                    "孩子",
                    "小学",
                    "中学",
                    "教学",
                    "学校",
                    "课程",
                ]
            ):
                recommendations = [
                    {
                        "combo": ["苏格拉底", "大卫伯恩斯", "王阳明"],
                        "reason": "教育智慧组合：苏格拉底式启发教学 + 认知心理学 + 知行合一的学习理念",
                        "score": 95,
                    },
                    {
                        "combo": ["苏格拉底", "吉杜克里希那穆提", "稻盛和夫"],
                        "reason": "成长启发组合：哲学思辨 + 觉察学习 + 匠人精神",
                        "score": 90,
                    },
                ]

            # 商业创业类
            elif any(
                word in question_lower
                for word in ["创业", "商业", "投资", "经营", "企业", "生意", "商务"]
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

            # 人生成长类
            elif any(
                word in question_lower
                for word in [
                    "人生",
                    "成长",
                    "认知",
                    "思维",
                    "心理",
                    "修养",
                    "品格",
                    "情感",
                    "压力",
                    "焦虑",
                ]
            ):
                recommendations = [
                    {
                        "combo": ["苏格拉底", "大卫伯恩斯", "吉杜克里希那穆提"],
                        "reason": "心理成长组合：哲学思辨 + CBT认知疗法 + 内在觉察智慧",
                        "score": 95,
                    },
                    {
                        "combo": ["王阳明", "曾国藩", "稻盛和夫"],
                        "reason": "修身养性组合：知行合一 + 品格修养 + 人格典范",
                        "score": 90,
                    },
                ]

            # 系统管理类
            elif any(
                word in question_lower
                for word in [
                    "系统",
                    "管理",
                    "复杂",
                    "问题",
                    "解决",
                    "策略",
                    "方法",
                    "流程",
                    "组织",
                ]
            ):
                recommendations = [
                    {
                        "combo": ["杰伊福雷斯特", "查理芒格", "苏格拉底"],
                        "reason": "系统分析组合：系统动力学 + 多元思维模型 + 批判思辨",
                        "score": 95,
                    },
                    {
                        "combo": ["杰伊福雷斯特", "埃隆马斯克", "王阳明"],
                        "reason": "创新解决组合：系统思维 + 创新突破 + 知行合一",
                        "score": 88,
                    },
                ]

            # 产品技术类
            elif any(
                word in question_lower
                for word in [
                    "产品",
                    "设计",
                    "用户",
                    "体验",
                    "技术",
                    "软件",
                    "开发",
                    "创新",
                ]
            ):
                recommendations = [
                    {
                        "combo": ["史蒂夫乔布斯", "埃隆马斯克", "孙子"],
                        "reason": "产品创新组合：极致用户体验 + 技术创新 + 战略思维",
                        "score": 92,
                    },
                    {
                        "combo": ["史蒂夫乔布斯", "稻盛和夫", "苏格拉底"],
                        "reason": "完美主义组合：产品极致 + 匠人精神 + 深度思考",
                        "score": 88,
                    },
                ]

            # 宗教精神类
            elif any(
                word in question_lower
                for word in [
                    "宗教",
                    "信仰",
                    "精神",
                    "圣经",
                    "教会",
                    "上帝",
                    "神",
                    "灵性",
                    "道德",
                    "伦理",
                ]
            ):
                recommendations = [
                    {
                        "combo": ["苏格拉底", "王阳明", "吉杜克里希那穆提"],
                        "reason": "精神哲学组合：理性思辨 + 心学智慧 + 灵性觉察",
                        "score": 95,
                    },
                    {
                        "combo": ["苏格拉底", "曾国藩", "稻盛和夫"],
                        "reason": "道德修养组合：哲学思辨 + 儒家修身 + 敬天爱人",
                        "score": 90,
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
                ]

            # 检查推荐的专家是否都可用
            all_personas = self.custom_persona_manager.get_all_personas(PERSONAS)
            for rec in recommendations:
                if all(persona in all_personas for persona in rec["combo"]):
                    return rec

            return None

        except Exception:
            return None

    async def _handle_get_smart_recommendation_guidance(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """获取智能专家推荐指导（MCP Host端LLM使用）"""
        try:
            question = arguments.get("question", "")
            if not question:
                return [TextContent(type="text", text="❌ 请提供要分析的问题")]

            # 获取所有可用专家（内置+自定义）
            all_personas = self.custom_persona_manager.get_all_personas(PERSONAS)

            # 构建专家信息列表
            persona_info = []
            for name, persona in all_personas.items():
                if hasattr(persona, "description"):
                    desc = persona.description
                elif hasattr(persona, "base_prompt"):
                    # 从base_prompt中提取简介
                    lines = persona.base_prompt.split("\n")
                    desc = next(
                        (line for line in lines if "是" in line and len(line) < 100),
                        name,
                    )
                else:
                    desc = name

                emoji = getattr(persona, "emoji", "👤")
                # Use actual display name from persona object, not dictionary key
                display_name = getattr(persona, "name", name)
                persona_info.append(f"{emoji} **{display_name}**: {desc}")

            # 构建指导内容
            guidance = f"""# 🎯 智能专家推荐指导

## 📋 任务说明
请根据以下问题分析，从可用专家中智能推荐3位最合适的专家组合：

**问题**: {question}

## 👥 可用专家列表
{chr(10).join(persona_info)}

## 🎨 推荐原则

### 1. 多元视角
- 选择来自不同领域/背景的专家，确保观点多样性
- 避免选择思维模式过于相似的专家组合

### 2. 问题相关性
- 优先选择与问题领域直接相关的专家
- 考虑跨领域专家可能带来的独特洞察

### 3. 思辨互补
- 选择能够形成有效对话和思辨的专家组合
- 包含不同立场/观点的专家，促进深度讨论

### 4. 智慧层次
- 结合理论专家（哲学家、思想家）
- 结合实践专家（企业家、科学家）
- 结合创新专家（突破常规思维）

## 📝 输出格式

请按以下JSON格式输出推荐结果：

```json
{{
  "recommended_personas": ["专家1", "专家2", "专家3"],
  "reason": "推荐理由：说明为什么这个组合最适合讨论该问题",
  "expected_perspectives": [
    "专家1将从X角度分析...",
    "专家2将从Y角度思考...",
    "专家3将从Z角度贡献..."
  ]
}}
```

## 💡 分析框架

1. **问题类型识别**:
   - 属于哪个主要领域？
   - 涉及哪些子领域？
   - 是理论问题还是实践问题？

2. **所需视角分析**:
   - 需要哪些专业视角？
   - 需要哪些思维方式？
   - 需要什么样的经验背景？

3. **专家匹配**:
   - 哪些专家最相关？
   - 如何组合才能产生最佳讨论效果？
   - 如何平衡不同观点？

现在请基于以上指导，为给定问题推荐最佳的3位专家组合。"""

            return [TextContent(type="text", text=guidance)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取推荐指导失败: {str(e)}")]

    def _format_persona_info_with_custom(self, persona_name: str) -> str:
        """格式化显示思想家信息（包含自定义专家）"""
        # 获取所有专家（内置+自定义）
        all_personas = self.custom_persona_manager.get_all_personas(PERSONAS)

        if persona_name not in all_personas:
            return f"未知思想家: {persona_name}"

        persona = all_personas[persona_name]

        # 检查是否有emoji和description属性
        emoji = getattr(persona, "emoji", "👤")

        if hasattr(persona, "description"):
            description = persona.description
        elif hasattr(persona, "base_prompt"):
            # 从base_prompt中提取简介
            lines = persona.base_prompt.split("\n")
            description = next(
                (line for line in lines if "是" in line and len(line) < 100),
                f"{persona_name}专家",
            )
        else:
            # 如果是内置专家（字典格式）
            if isinstance(persona, dict):
                emoji = persona.get("emoji", "👤")
                description = persona.get("description", f"{persona_name}专家")
            else:
                description = f"{persona_name}专家"

        return f"{emoji} **{persona_name}** - {description}"

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
                self.config_manager.get_language_instruction(),
            )

            # 返回格式化的prompt信息
            round_names = {
                1: "第1轮：独立思考",
                2: "第2轮：交叉辩论",
                3: "第3轮：最终立场",
                4: "第4轮：智慧综合",
            }

            result = f"""{prompt}

---

🎭 **角色扮演提示**

**会话**: {session.session_id}
**轮次**: {round_names.get(session.current_round, f"第{session.current_round}轮")}
**角色**: {self._format_persona_info_with_custom(current_persona)}

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
            # 获取语言设置
            config = ConfigManager()
            language_instruction = config.get_language_instruction()

            if not self.current_session:
                return [
                    TextContent(
                        type="text",
                        text=f"{language_instruction}\n\n❌ 没有活跃的会话。",
                    )
                ]

            response = arguments.get("response", "").strip()
            if not response:
                return [
                    TextContent(
                        type="text",
                        text=f'{language_instruction}\n\n❌ 请提供回答内容。\n\n使用方法：record_round_response({{"response": "你的回答内容"}})',
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
                        text=f"""{language_instruction}

✅ **最终综合分析已完成！**

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
                        text=f"""{language_instruction}

✅ **所有轮次已完成！**

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

            result = f"""{language_instruction}

✅ **回答已记录！**

**{current_persona}** 的观点已保存。

📍 **下一步**:
- **轮次**: {round_names.get(session.current_round, f"第{session.current_round}轮")}
- **发言者**: {self._format_persona_info_with_custom(next_persona)}

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
            # 获取语言设置
            config = ConfigManager()
            language_instruction = config.get_language_instruction()

            if not self.current_session:
                return [
                    TextContent(
                        type="text",
                        text=f"{language_instruction}\n\n❌ 没有活跃的会话。请先使用 start_pk_session 启动一个会话。",
                    )
                ]

            status = self.current_session.get_session_status()

            # 计算进度
            total_expected = (
                len(self.current_session.selected_personas) * 3 + 1
            )  # 3轮*3人 + 1综合
            completed = status["completed_responses"]
            progress = f"{completed}/{total_expected}"

            result = f"""{language_instruction}

📊 **会话状态报告**

**会话ID**: `{status['session_id']}`
**问题**: {status['question']}

**当前进展**:
- 🎯 **当前轮次**: {status['round_name']}
- 👤 **当前发言者**: {self._format_persona_info_with_custom(status['current_persona']) if status['current_persona'] else '已完成'}
- 📈 **完成进度**: {progress}

**参与专家**: {', '.join([self._format_persona_info_with_custom(p) for p in status['personas']])}

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
            # 获取语言设置
            config = ConfigManager()
            language_instruction = config.get_language_instruction()

            # 内置思想家
            builtin_personas = get_available_personas()
            # 自定义思想家
            custom_personas = self.custom_persona_manager.list_custom_personas()

            # 在开头添加语言指示
            result = f"{language_instruction}\n\n🎭 **可用的思想家专家**\n\n"

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

            result += "💡 **使用提示**: 直接提问即可自动获得智能专家推荐！\n\n"
            result += "🤖 **智能推荐** (推荐): 直接提问，系统自动推荐最佳专家组合\n"
            result += '```\nstart_pk_session({"question": "你的问题"})\n```\n\n'
            result += "🔄 **手动选择**: 如需指定特定专家组合\n"
            result += '```\nstart_pk_session({"question": "你的问题", "personas": ["苏格拉底", "埃隆马斯克", "查理芒格"]})\n```'

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取思想家列表失败: {str(e)}")]

        # 工具6: 查看会话历史

    async def _handle_view_session_history(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """查看会话历史"""
        try:
            # 获取语言设置
            config = ConfigManager()
            language_instruction = config.get_language_instruction()

            session_id = arguments.get("session_id")
            if session_id:
                # 查看指定会话
                session = self.session_manager.load_session(session_id)
                if not session:
                    return [
                        TextContent(
                            type="text",
                            text=f"{language_instruction}\n\n❌ 未找到会话 {session_id}",
                        )
                    ]
            else:
                # 查看当前会话
                if not self.current_session:
                    return [
                        TextContent(
                            type="text",
                            text=f"{language_instruction}\n\n❌ 没有活跃的会话。请提供 session_id 参数查看历史会话。",
                        )
                    ]
                session = self.current_session

            result = f"""{language_instruction}

📚 **会话讨论历史**

**会话ID**: `{session.session_id}`
**问题**: {session.user_question}
**创建时间**: {session.created_at}
**参与专家**: {', '.join([self._format_persona_info_with_custom(p) for p in session.selected_personas])}

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
                    result += (
                        f"### {self._format_persona_info_with_custom(persona)}\n\n"
                    )
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
- **发言者**: {self._format_persona_info_with_custom(next_persona)}

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
**当前专家**: {self._format_persona_info_with_custom(current_persona) if current_persona else '已完成'}

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
                "综合大师",
                4,
                context,
                self.custom_persona_manager.custom_personas,
                self.config_manager.get_language_instruction(),
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
- **待发言**: {self._format_persona_info_with_custom(current_persona)}
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
        """智能专家推荐（建议使用MCP Host端推荐）"""
        try:
            question = arguments.get("question", "").strip()
            if not question:
                return [
                    TextContent(
                        type="text",
                        text='❌ 请提供问题内容。\n\n使用方法：recommend_personas({"question": "你的问题"})',
                    )
                ]

            return [
                TextContent(
                    type="text",
                    text=f"""🎯 **专家推荐服务**

**问题**: {question}

## 🤖 **推荐使用智能推荐（推荐）**

新的智能推荐系统使用**MCP Host端LLM智能生成**，能够：
- ✅ 真正理解问题语义和深层需求
- ✅ 动态匹配所有可用专家（包括您的自定义专家）
- ✅ 根据问题特点生成最佳专家组合
- ✅ 提供详细的推荐理由和预期视角

### 📋 **智能推荐使用方法**：

```javascript
// 步骤1: 获取智能推荐指导
get_smart_recommendation_guidance({{"question": "{question}"}})

// 步骤2: 基于指导推荐专家，然后启动会话
// start_pk_session({{"question": "{question}", "personas": ["推荐专家1", "推荐专家2", "推荐专家3"], "recommended_by_host": true}})
```

## 🔄 **传统推荐（备选）**

如果您希望使用传统的关键词匹配推荐，可以直接启动会话：

```javascript
start_pk_session({{"question": "{question}"}})
```

---

💡 **建议**: 优先使用智能推荐，获得更精准和个性化的专家组合！""",
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 生成推荐失败: {str(e)}")]

        # 工具2: 获取帮助信息

    async def _handle_guru_pk_help(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """获取系统帮助和介绍"""
        # 获取语言设置
        config = ConfigManager()
        language_instruction = config.get_language_instruction()

        help_text = f"""{language_instruction}

# 🎭 Guru-PK MCP 专家辩论系统

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
- `create_custom_persona_from_description` - 🌟 自然语言创建自定义专家

### 会话管理
- `view_session_history` - 查看会话历史
- `export_session` - 导出会话记录
- `advance_to_next_round` - 手动切换到下一轮/专家

### 高级功能
- `get_usage_statistics` - 查看使用统计
- `set_language` - 🌍 设置专家回复语言
- `get_language_settings` - 查看语言设置
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
list_available_personas()
```

4. **🌟 自然语言创建专家**：
```
create_custom_persona_from_description({
  "description": "我想要一个现代教育领域最顶尖的大师"
})
```

5. **🌍 设置回复语言**：
```
set_language({"language": "english"})
```

## 🎭 内置专家阵容（13位）

### 哲学思辨
- **🧠 苏格拉底** - 古希腊哲学家，以思辨和质疑著称
- **☯️ 王阳明** - 明代心学大师，知行合一的倡导者
- **🧘 吉杜克里希那穆提** - 觉察智慧导师，当下生活的哲学家

### 商业创新
- **🚀 埃隆马斯克** - 现代创新教父，第一性原理思维大师
- **📚 查理芒格** - 投资智慧大师，多元思维模型的倡导者
- **🍎 史蒂夫乔布斯** - 产品完美主义者，用户体验至上的创新者
- **🌸 稻盛和夫** - 经营之圣，敬天爱人的经营哲学家

### 经济战略
- **💰 路德维希·冯·米塞斯** - 奥地利经济学派巨匠，人类行动学理论创始人
- **⚔️ 孙子** - 兵学圣祖，战略思维的绝对王者
- **📖 曾国藩** - 理学大师，中兴名臣，修身治国的典范

### 科学方法
- **🔬 卡尔·波普尔** - 科学哲学巨匠，可证伪性理论创立者
- **🔄 杰伊福雷斯特** - 系统动力学之父，反馈环理论创建者
- **🧠 大卫·伯恩斯** - CBT心理学大师，《感受的事实》作者

## 🌟 热门专家组合推荐

- **投资决策组**：路德维希·冯·米塞斯 + 查理芒格 + 埃隆马斯克
- **心理成长组**：苏格拉底 + 大卫·伯恩斯 + 吉杜克里希那穆提
- **战略决策组**：孙子 + 曾国藩 + 查理芒格
- **科学理性组**：卡尔·波普尔 + 苏格拉底 + 杰伊福雷斯特

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
                result += f"{i}. {self._format_persona_info_with_custom(persona)} - {count}次 ({percentage:.1f}%)\n"

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

    async def _handle_create_custom_persona_from_description(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """根据自然语言描述提供智能创建自定义专家的指导"""
        try:
            description = arguments.get("description", "").strip()
            if not description:
                return [
                    TextContent(
                        type="text",
                        text='❌ 请提供专家描述。\n\n使用方法：create_custom_persona_from_description({"description": "我想要一个现代教育领域最顶尖的大师"})',
                    )
                ]

            # 获取语言设置
            language_instruction = self.config_manager.get_language_instruction()

            # 返回创建指导和模板
            result = f"""🤖 **智能专家创建指导**

📝 **您的需求**: {description}

🎯 **下一步操作**: 请让我（MCP Host端的LLM）根据您的描述生成完整的专家数据，然后使用 `save_custom_persona` 工具保存。

## 📋 专家数据模板

请根据描述 "{description}" 生成以下格式的专家数据：

```json
{{
  "name": "专家姓名（如：阿尔伯特·爱因斯坦）",
  "emoji": "代表性表情符号（如：🧠、🎓、💡等）",
  "description": "简洁的专家介绍（1-2句话）",
  "core_traits": ["核心特质1", "核心特质2", "核心特质3"],
  "speaking_style": "语言风格描述（如：深入浅出，富有哲理）",
  "base_prompt": "{language_instruction}\n\n你是[专家姓名]，[详细的角色设定和背景]。\n\n你的特点：\n- [特点1]\n- [特点2]\n- [特点3]\n- 语言风格：[具体的语言风格描述]"
}}
```

## 🎨 创建要点

1. **选择合适的历史人物或虚构专家**：根据需求领域选择最具代表性的专家
2. **核心特质要具体**：避免泛泛而谈，要体现专业领域特色
3. **语言风格要鲜明**：让专家有独特的表达方式
4. **base_prompt要详细**：包含足够的背景信息和行为指导

## 💡 示例领域专家推荐

- **历史学**: 汤因比、黄仁宇、钱穆
- **物理学**: 爱因斯坦、费曼、霍金
- **文学**: 莎士比亚、鲁迅、村上春树
- **艺术**: 达芬奇、毕加索、宫崎骏
- **经济学**: 亚当·斯密、凯恩斯、张五常

🚀 **完成后请调用**: `save_custom_persona({{"persona_data": [生成的专家数据]}})` 来保存专家。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取创建指导失败: {str(e)}")]

    async def _handle_save_custom_persona(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """保存由MCP Host端LLM生成的完整自定义专家数据"""
        try:
            persona_data = arguments.get("persona_data")
            if not persona_data:
                return [
                    TextContent(
                        type="text",
                        text='❌ 请提供完整的专家数据。\n\n使用方法：save_custom_persona({"persona_data": {"name": "专家名", ...}})',
                    )
                ]

            # 验证必填字段
            required_fields = [
                "name",
                "description",
                "core_traits",
                "speaking_style",
                "base_prompt",
            ]
            missing_fields = []
            for field in required_fields:
                if field not in persona_data or not persona_data[field]:
                    missing_fields.append(field)

            if missing_fields:
                return [
                    TextContent(
                        type="text",
                        text=f"❌ 缺少必填字段: {', '.join(missing_fields)}\n\n必填字段: {', '.join(required_fields)}",
                    )
                ]

            # 验证数据类型
            if not isinstance(persona_data["core_traits"], list):
                return [
                    TextContent(
                        type="text",
                        text="❌ core_traits 必须是字符串数组",
                    )
                ]

            # 检查名称冲突
            all_personas = self.custom_persona_manager.get_all_personas(PERSONAS)
            original_name = persona_data["name"]
            if original_name in all_personas:
                # 如果冲突，在名称后添加标识
                persona_data["name"] = f"{original_name}（自定义）"

            # 添加默认emoji（如果没有提供）
            if "emoji" not in persona_data or not persona_data["emoji"]:
                persona_data["emoji"] = "👤"

            # 保存专家
            success = self.custom_persona_manager.add_custom_persona(persona_data)

            if success:
                persona_name = persona_data["name"]
                name_change_note = ""
                if persona_name != original_name:
                    name_change_note = f"\n\n⚠️ **名称调整**: 由于 '{original_name}' 已存在，已自动调整为 '{persona_name}'"

                result = f"""✅ **自定义专家创建成功！**

👤 **{persona_name}** 已添加到专家库{name_change_note}

📝 **专家信息**:
- 🎭 表情: {persona_data['emoji']}
- 📖 描述: {persona_data['description']}
- 🔥 核心特质: {', '.join(persona_data['core_traits'])}
- 💬 语言风格: {persona_data['speaking_style']}

💡 **立即可用**: 现在您可以在 `start_pk_session` 中使用这位专家了！

🚀 **使用示例**:
```
start_pk_session({{
  "question": "您的问题",
  "personas": ["{persona_name}", "苏格拉底", "查理芒格"]
}})
```

📁 **存储位置**: 专家数据已保存到 `config/custom_personas.json`"""

                return [TextContent(type="text", text=result)]
            else:
                return [
                    TextContent(
                        type="text", text="❌ 专家保存失败，请检查数据格式或稍后重试。"
                    )
                ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 保存专家失败: {str(e)}")]

    async def _handle_set_language(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """设置专家回复使用的语言"""
        try:
            language = arguments.get("language", "").strip()
            if not language:
                return [
                    TextContent(
                        type="text",
                        text='❌ 请提供语言代码。\n\n使用方法：set_language({"language": "chinese"})',
                    )
                ]

            supported_languages = self.config_manager.get_supported_languages()
            if language not in supported_languages:
                supported_list = ", ".join(supported_languages)
                return [
                    TextContent(
                        type="text",
                        text=f"❌ 不支持的语言: {language}\n\n支持的语言: {supported_list}",
                    )
                ]

            success = self.config_manager.set_language(language)
            if success:
                display_name = self.config_manager.get_language_display_name(language)
                language_instruction = self.config_manager.get_language_instruction()

                result = f"""✅ **语言设置已更新**

**当前语言**: {display_name} ({language})
**语言指令**: {language_instruction}

💡 **说明**: 所有专家在生成角色提示时都会收到明确的语言指令，确保回复使用指定语言。

🔄 **生效范围**:
- 新启动的PK会话
- 获取专家角色提示
- 综合分析阶段

⚠️ **注意**: 已进行中的会话不会受到影响，需要重新启动会话才能使用新的语言设置。"""

                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text="❌ 语言设置保存失败")]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 设置语言失败: {str(e)}")]

    async def _handle_get_language_settings(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """查看当前语言设置和支持的语言"""
        try:
            current_language = self.config_manager.get_language()
            current_display = self.config_manager.get_language_display_name(
                current_language
            )
            current_instruction = self.config_manager.get_language_instruction()
            supported_languages = self.config_manager.get_supported_languages()

            result = f"""🌍 **语言设置**

**当前语言**: {current_display} ({current_language})
**语言指令**: {current_instruction}

## 🗣️ 支持的语言

"""

            for lang in supported_languages:
                display_name = self.config_manager.get_language_display_name(lang)
                is_current = "✅" if lang == current_language else "  "
                result += f"{is_current} **{display_name}** ({lang})\n"

            result += """
## 🔧 使用方法

**设置语言**:
```
set_language({"language": "english"})
```

**支持的语言代码**:
- `chinese` - 中文（默认）
- `english` - English
- `japanese` - 日本語
- `korean` - 한국어
- `french` - Français
- `german` - Deutsch
- `spanish` - Español

💡 **提示**: 语言设置会影响所有专家的回复语言，确保获得一致的语言体验。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取语言设置失败: {str(e)}")]

    async def _handle_analyze_question_profile(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """深度分析问题特征和复杂度"""
        try:
            question = arguments.get("question", "").strip()
            if not question:
                return [TextContent(type="text", text="❌ 请提供要分析的问题")]

            # 使用问题分析器
            from .dynamic_expert_engine import QuestionAnalyzer

            analyzer = QuestionAnalyzer()
            profile = analyzer.analyze_question(question)

            result = f"""📊 **问题特征分析报告**

**问题**: {profile.question}

## 🎯 基本特征
- **涉及领域**: {', '.join(profile.domains)}
- **复杂度**: {profile.complexity.value}
- **推荐辩论模式**: {profile.debate_mode.value}
- **预期轮次**: {profile.expected_rounds}

## 🧠 所需专业知识
{chr(10).join(['- ' + expertise for expertise in profile.required_expertise]) if profile.required_expertise else '- 通用知识'}

## 🤔 所需思维模式
{chr(10).join(['- ' + mode for mode in profile.thinking_modes]) if profile.thinking_modes else '- 批判性思维'}

## 🔑 关键词
{', '.join(profile.keywords) if profile.keywords else '无特定关键词'}

## 💡 建议
基于分析结果，建议使用 `generate_dynamic_experts` 工具生成专门的专家推荐。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 问题分析失败: {str(e)}")]

    async def _handle_generate_dynamic_experts(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """动态生成专家推荐"""
        try:
            question = arguments.get("question", "").strip()
            num_experts = arguments.get("num_experts", 5)

            if not question:
                return [TextContent(type="text", text="❌ 请提供要讨论的问题")]

            # 生成专家推荐
            recommendation = (
                self.session_manager.expert_generator.generate_expert_recommendation(
                    question, num_experts
                )
            )

            # 格式化专家信息
            experts_info = []
            for i, expert in enumerate(recommendation.experts, 1):
                source_icon = {"builtin": "📚", "custom": "👤", "generated": "🤖"}.get(
                    expert.source, "❓"
                )

                experts_info.append(
                    f"""{i}. {source_icon} **{expert.name}** ({expert.source})
   📝 {expert.description}
   🎯 相关度: {expert.relevance_score:.2f}
   🧠 思维风格: {expert.thinking_style}
   📚 知识领域: {', '.join(expert.knowledge_domains[:3])}"""
                )

            result = f"""🎯 **动态专家推荐结果**

**问题**: {question}

## 🤖 推荐理由
{recommendation.recommendation_reason}

## 👥 候选专家 ({len(recommendation.experts)}位)

{chr(10).join(experts_info)}

## 📊 推荐质量
- **多样性评分**: {recommendation.diversity_score:.2f}/1.0
- **相关性评分**: {recommendation.relevance_score:.2f}/1.0

## 🔮 预期视角
{chr(10).join(['- ' + perspective for perspective in recommendation.expected_perspectives]) if recommendation.expected_perspectives else '- 多元化专业视角'}

## 🚀 使用建议
选择其中3位专家启动辩论：
```javascript
start_pk_session({{
  "question": "{question}",
  "personas": ["专家1", "专家2", "专家3"],
  "recommended_by_host": true
}})
```"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 专家推荐生成失败: {str(e)}")]

    async def _handle_get_session_quality_analysis(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """获取会话质量分析"""
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

            # 更新质量分析
            suggestions = self.session_manager.update_session_quality(session)

            # 检查自适应流程
            adaptive_check = self.session_manager.check_adaptive_flow(session)

            if not session.quality_metrics:
                return [
                    TextContent(
                        type="text", text="📊 当前会话暂无足够数据进行质量分析。"
                    )
                ]

            metrics = session.quality_metrics
            result = f"""📊 **会话质量分析报告**

**会话ID**: `{session.session_id}`
**问题**: {session.user_question}
**当前轮次**: {session.current_round}/{session.max_rounds}

## 🎯 质量指标

- **📈 总体评分**: {metrics.overall_score:.1f}/10 - {self._get_score_level(metrics.overall_score)}
- **💡 新颖度**: {metrics.novelty_score:.1f}/10
- **🔍 深度**: {metrics.depth_score:.1f}/10
- **🤝 互动质量**: {metrics.interaction_score:.1f}/10
- **⚡ 实用性**: {metrics.practicality_score:.1f}/10

## 💬 质量反馈
{metrics.feedback}

## 🔄 自适应建议"""

            if adaptive_check["should_extend"]:
                result += "\n- ⏯️ **建议延长**: 当前质量不足，已自动增加1轮讨论"
            elif adaptive_check["should_end_early"]:
                result += "\n- ⏭️ **可提前结束**: 讨论质量已达到优秀水平"
            else:
                result += "\n- ✅ **正常进行**: 保持当前讨论节奏"

            if suggestions:
                result += f"\n\n## 📈 改进建议\n{suggestions}"

            result += f"\n\n## 📊 统计信息\n- **质量检测时间**: {metrics.timestamp[:19].replace('T', ' ')}"

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 质量分析失败: {str(e)}")]

    def _get_score_level(self, score: float) -> str:
        """获取评分等级"""
        if score >= 8.5:
            return "🌟 优秀"
        elif score >= 7.0:
            return "✅ 良好"
        elif score >= 5.5:
            return "⚠️ 一般"
        else:
            return "❌ 需改进"

    async def _handle_get_expert_insights(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """获取专家洞察和关系分析"""
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
                    return [TextContent(type="text", text="❌ 没有活跃的会话。")]
                session = self.current_session

            insights = self.session_manager.get_expert_insights(session)

            result = f"""🔍 **专家洞察分析**

**会话ID**: `{session.session_id}`

## 👥 专家档案"""

            if insights["expert_profiles"]:
                for name, profile in insights["expert_profiles"].items():
                    result += f"""

### {name}
- **专业背景**: {profile['background']}
- **思维风格**: {profile['thinking_style']}
- **知识领域**: {', '.join(profile['knowledge_domains'])}
- **核心特质**: {', '.join(profile['personality_traits'])}
- **来源**: {profile['source']}
- **相关度**: {profile['relevance_score']:.2f}"""
            else:
                result += "\n暂无专家档案信息。"

            # 推荐详情
            if insights["recommendation_details"]:
                details = insights["recommendation_details"]
                result += f"""

## 🎯 推荐分析
- **推荐理由**: {details['reason']}
- **多样性评分**: {details['diversity_score']:.2f}
- **相关性评分**: {details['relevance_score']:.2f}

### 🔮 预期视角
{chr(10).join(['- ' + p for p in details['expected_perspectives']]) if details['expected_perspectives'] else '- 暂无预期视角信息'}"""

            # 专家关系
            if insights["relationships"]:
                result += "\n\n## 🕸️ 专家关系图谱"
                for expert, relations in insights["relationships"].items():
                    if (
                        relations.get("potential_allies")
                        or relations.get("potential_opponents")
                        or relations.get("complementary")
                    ):
                        result += f"\n\n### {expert}"
                        if relations.get("potential_allies"):
                            result += f"\n- 🤝 **潜在盟友**: {', '.join(relations['potential_allies'])}"
                        if relations.get("potential_opponents"):
                            result += f"\n- ⚔️ **观点对手**: {', '.join(relations['potential_opponents'])}"
                        if relations.get("complementary"):
                            result += f"\n- 🔄 **互补关系**: {', '.join(relations['complementary'])}"

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 专家洞察分析失败: {str(e)}")]

    async def _handle_export_enhanced_session(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """导出增强的会话分析报告"""
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
                    return [TextContent(type="text", text="❌ 没有活跃的会话。")]
                session = self.current_session

            # 导出增强报告
            export_file = self.session_manager.export_enhanced_session(session)

            result = f"""📄 **增强会话报告导出成功！**

**文件路径**: `{export_file}`
**格式**: Enhanced Markdown Report
**会话ID**: {session.session_id}

## 📊 报告内容
- ✅ 完整讨论记录
- ✅ 质量分析指标
- ✅ 专家档案信息
- ✅ 关系图谱分析
- ✅ 推荐详情记录
- ✅ 互动模式分析
- ✅ 改进建议总结

## 💡 使用说明
该报告包含比标准导出更丰富的分析信息，适合深度复盘和研究使用。

🔗 **对比**: 使用 `export_session` 获取标准格式报告。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 增强报告导出失败: {str(e)}")]

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
