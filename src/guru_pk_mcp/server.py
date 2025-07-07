"""
Guru-PK MCP 服务器
"""

import asyncio
from typing import Any

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import TextContent

from .config import ConfigManager
from .dynamic_experts import (
    DynamicExpertManager,
    get_expert_recommendation_guidance,
    get_question_analysis_guidance,
    should_trigger_smart_recommendation,
)
from .models import PKSession
from .personas import (
    format_persona_info,
    generate_round_prompt,
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

        self.expert_manager = DynamicExpertManager(data_dir)
        self.session_manager = SessionManager(data_dir, self.expert_manager)
        self.config_manager = ConfigManager(data_dir)
        self.current_session: PKSession | None = None
        self.pending_recommendation: dict[str, Any] | None = None
        self._register_tools()

    def _format_expert_info(self, expert_name: str) -> str:
        """格式化专家信息的辅助方法"""
        if not expert_name:
            return "无"
        current_experts = self.expert_manager.get_current_experts()
        return format_persona_info(expert_name, current_experts)

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
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "emoji": {"type": "string"},
                                        "description": {"type": "string"},
                                        "core_traits": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "speaking_style": {"type": "string"},
                                        "base_prompt": {"type": "string"},
                                    },
                                    "required": [
                                        "name",
                                        "emoji",
                                        "description",
                                        "core_traits",
                                        "speaking_style",
                                        "base_prompt",
                                    ],
                                },
                                "description": "参与讨论的三位专家完整数据（可选）。如果不提供，系统将基于问题内容和专家偏好自动推荐",
                                "minItems": 3,
                                "maxItems": 3,
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
                    description="获取专家推荐的原则性指导（MCP Host端LLM使用）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "要分析的问题内容",
                            },
                            "expert_preferences": {
                                "type": "string",
                                "description": "用户对专家的偏好描述（可选），例如：'我想要三名人工智能方面的顶级专家'、'希望有哲学家和科学家参与'等",
                            },
                        },
                        "required": ["question"],
                    },
                ),
                types.Tool(
                    name="analyze_question_profile",
                    description="获取问题分析的原则性指导（MCP Host端LLM使用）",
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
                    description="动态生成专家推荐（直接生成3位专家）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "要讨论的问题",
                            },
                        },
                        "required": ["question"],
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
                    name="export_session_as_infographic",
                    description="生成塔夫特风格单页动态信息图的完整LLM指令",
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
            elif name == "export_session_as_infographic":
                return await self._handle_export_session_as_infographic(arguments)
            elif name == "advance_to_next_round":
                return await self._handle_advance_to_next_round(arguments)
            elif name == "get_usage_statistics":
                return await self._handle_get_usage_statistics(arguments)
            elif name == "set_language":
                return await self._handle_set_language(arguments)
            elif name == "get_language_settings":
                return await self._handle_get_language_settings(arguments)
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
                        text='❌ 请提供一个问题来启动PK会话。\n\n📋 **使用方式**：\n\n**方式1: 自动专家推荐**\n```javascript\nstart_pk_session({"question": "如何在AI时代实现个人突破？请两位人工智能领域的专家和一位心理学方面的专家参与辩论"})\n```\n\n**方式2: 完整专家数据**\n```javascript\nstart_pk_session({"question": "你的问题", "personas": [专家数据1, 专家数据2, 专家数据3]})\n```\n\n💡 **说明**: 系统会自动检测问题中的专家偏好，智能推荐最合适的专家组合。',
                    )
                ]

            # 检查是否需要触发智能推荐
            if should_trigger_smart_recommendation(personas):
                # 触发智能专家推荐流程
                return await self._handle_smart_expert_recommendation(question)

            # 验证专家数据格式
            expert_dict = {}
            for i, persona in enumerate(personas):
                if isinstance(persona, dict):
                    # 验证专家数据完整性
                    if not self.expert_manager.validate_expert_data(persona):
                        return [
                            TextContent(
                                type="text", text=f"❌ 专家 {i + 1} 数据格式不完整"
                            )
                        ]
                    expert_dict[persona["name"]] = persona
                elif isinstance(persona, str):
                    # 如果是字符串，表示这是专家名称，需要MCP Host端提供完整数据
                    return [
                        TextContent(
                            type="text",
                            text=f"""❌ 接收到专家名称 "{persona}"，但缺少完整的专家数据。

🤖 **MCP Host端操作指引**:

请为每个专家名称生成完整的专家数据，然后重新调用 start_pk_session：

```javascript
start_pk_session({{
  "question": "{question}",
  "personas": [
    {{
      "name": "{persona}",
      "emoji": "🎯",
      "description": "专家描述...",
      "core_traits": ["特质1", "特质2", "特质3"],
      "speaking_style": "表达风格...",
      "base_prompt": "你是...的专家提示"
    }},
    // ... 其他两个专家
  ],
  "recommended_by_host": true
}})
```

💡 **提示**: 请确保每个专家都有独特的视角和专业背景，形成有价值的辩论组合。""",
                        )
                    ]
                else:
                    return [
                        TextContent(
                            type="text",
                            text=f"❌ 专家 {i + 1} 必须是包含完整专家信息的字典",
                        )
                    ]

            # 设置当前专家到专家管理器
            self.expert_manager.set_current_experts(expert_dict)

            # 创建新会话，保存专家信息
            session = self.session_manager.create_session(
                question=question,
                personas=list(expert_dict.keys()),
                expert_profiles=expert_dict,
                is_recommended_by_host=recommended_by_host,
            )
            self.current_session = session

            # 生成启动信息
            personas_info = "\n".join(
                [
                    f"{i + 1}. {format_persona_info(p, expert_dict)}"
                    for i, p in enumerate(session.selected_personas)
                ]
            )

            # 设置推荐理由
            recommended_reason = (
                "🤖 动态生成专家组合" if recommended_by_host else "👤 用户指定专家组合"
            )

            result = f"""🎯 **专家PK会话已启动！**

**会话ID**: `{session.session_id}`
**问题**: {session.user_question}
**专家组合**: {recommended_reason}

**参与的三位专家**：
{personas_info}

📍 **当前状态**: 第1轮 - 独立思考阶段
👤 **即将发言**: {format_persona_info(session.get_current_persona(), expert_dict)}

💡 **下一步**: 使用 `get_persona_prompt` 工具获取当前专家的角色提示，然后让我扮演该专家来回答您的问题。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 启动会话失败: {str(e)}")]

    async def _handle_smart_expert_recommendation(
        self, question: str
    ) -> list[TextContent]:
        """处理智能专家推荐流程"""
        try:
            # 生成专家推荐指导（让MCP Host端LLM做偏好分析）
            guidance = get_expert_recommendation_guidance(question)

            # 构建给MCP Host端LLM的消息
            recommendation_prompt = f"""
🤖 **智能专家推荐系统**

系统检测到您需要专家推荐。请根据以下指导原则，分析用户问题并生成最合适的专家组合。

---

## 📋 MCP Host端操作指引

{guidance}

---

## 🎯 下一步操作

请完成以下步骤：

1. **分析用户问题中的专家偏好**（按照上述第一步指导）
2. **选择3位最合适的专家**（优先真实人物）
3. **生成完整的专家数据**
4. **重新调用 start_pk_session**：

```javascript
start_pk_session({{
  "question": "{question}",
  "personas": [
    // 3位专家的完整数据，每个包含：name, emoji, description, core_traits, speaking_style, base_prompt
  ],
  "recommended_by_host": true
}})
```

💡 **关键提醒**:
- 首先从问题中提取专家偏好
- 优先选择真实历史人物和当代名人
- 确保专家组合多样化且能产生有价值的思辨
"""

            return [TextContent(type="text", text=recommendation_prompt)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 智能推荐失败: {str(e)}")]

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

            # 新架构中不再需要检查专家可用性（动态生成）
            return recommendations[0] if recommendations else None

        except Exception:
            return None

    async def _handle_get_smart_recommendation_guidance(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """获取专家推荐的原则性指导（MCP Host端LLM使用）"""
        try:
            question = arguments.get("question", "")
            expert_preferences = arguments.get("expert_preferences", "")

            if not question:
                return [TextContent(type="text", text="❌ 请提供要分析的问题")]

            # 返回原则性指导，包含用户的专家偏好，供MCP Host端LLM使用
            guidance = get_expert_recommendation_guidance(question, expert_preferences)

            return [TextContent(type="text", text=guidance)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取推荐指导失败: {str(e)}")]

        # 工具2: 获取专家角色prompt

    async def _handle_get_persona_prompt(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """获取当前专家的角色prompt"""
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

            # 生成prompt - 使用当前会话的专家信息
            current_experts = self.expert_manager.get_current_experts()
            prompt = generate_round_prompt(
                current_persona,
                session.current_round,
                context,
                current_experts,
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
**角色**: {self._format_expert_info(current_persona)}

💡 **提示**: 完全进入角色，用该专家的语言风格、思维方式来回答。回答完成后，请使用 `record_round_response` 工具记录你的回答。"""

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
- 参与专家: {", ".join(session.selected_personas)}

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
- **发言者**: {self._format_expert_info(next_persona)}

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

**会话ID**: `{status["session_id"]}`
**问题**: {status["question"]}

**当前进展**:
- 🎯 **当前轮次**: {status["round_name"]}
- 👤 **当前发言者**: {self._format_expert_info(status["current_persona"]) if status["current_persona"] else "已完成"}
- 📈 **完成进度**: {progress}

**参与专家**: {", ".join([self._format_expert_info(p) for p in status["personas"]])}

**状态**: {"✅ 已完成" if status["is_completed"] else "🔄 进行中"}"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取状态失败: {str(e)}")]

        # 工具5: 列出可用专家

    async def _handle_list_available_personas(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """列出所有可用的专家"""
        try:
            # 获取语言设置
            config = ConfigManager()
            language_instruction = config.get_language_instruction()

            # 在开头添加语言指示
            result = f"{language_instruction}\n\n🎭 **动态专家生成系统**\n\n"

            result += "## 🚀 新的专家系统\n\n"
            result += "新系统不再使用预定义的专家列表，而是根据您的问题动态生成最合适的专家！\n\n"

            result += "## 💡 使用方式\n\n"
            result += "**🤖 智能推荐**（推荐方式）：\n"
            result += "1. 使用 `get_smart_recommendation_guidance` 获取推荐指导\n"
            result += "2. MCP Host端LLM根据指导动态生成3位专家\n"
            result += "3. 使用 `start_pk_session` 启动专家辩论\n\n"

            result += "**🎯 优势**：\n"
            result += "- 每次都为问题定制最合适的专家\n"
            result += "- 保证专业度和多样性的最佳平衡\n"
            result += "- 无需维护专家列表，永远新鲜\n"

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取专家列表失败: {str(e)}")]

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
**参与专家**: {", ".join([self._format_expert_info(p) for p in session.selected_personas])}

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
                    result += f"### {self._format_expert_info(persona)}\n\n"
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
- **发言者**: {self._format_expert_info(next_persona)}

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
**当前专家**: {self._format_expert_info(current_persona) if current_persona else "已完成"}

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
                self.expert_manager.get_current_experts(),
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
- **待发言**: {self._format_expert_info(current_persona)}
- **进度**: {status["completed_responses"]}/{len(session.selected_personas) * 3 + 1}

💡 使用 `get_persona_prompt` 获取当前专家的角色提示。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 恢复会话失败: {str(e)}")]

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

    async def _handle_export_session_as_infographic(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """导出会话为塔夫特风格的单页动态信息图"""
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

            # 生成信息图内容
            result = await self.session_manager.export_session_as_infographic(session)
            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 信息图导出失败: {str(e)}")]

        # Phase 3 工具: 智能推荐专家

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
- ✅ 动态生成最适合问题的专家组合
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

# 🏭 Guru-PK MCP 智能专家辩论系统

欢迎使用Guru-PK！这是一个基于MCP协议的AI专家辩论系统，采用**动态专家生成架构**，根据您的问题智能创建最适合的专家组合进行多轮深度对话。

## 🌟 核心特色

- **🏭 动态专家生成**：完全问题驱动，每次生成专属专家组合
- **🤖 智能分工架构**：MCP Host端LLM负责智能分析，MCP Server端提供流程指导
- **🔄 多轮PK流程**：独立思考 → 交叉辩论 → 最终立场 → 智慧综合
- **🌟 无限专家池**：突破固定专家限制，支持任意领域的专家生成
- **📚 本地数据管理**：完全隐私保护，会话数据本地存储

## 🎯 智能专家生成流程

1. **直接提问** - 向系统提出任何话题的问题
2. **智能分析** - MCP Host端LLM深度分析问题特征和需求
3. **生成专家** - 动态创建3位最相关领域的专家
4. **开始辩论** - 启动4轮PK流程，获得深度洞察

## 📋 可用工具

### 🚀 核心功能
- `start_pk_session` - 智能生成专家并启动辩论会话
- `get_persona_prompt` - 获取当前专家的角色提示
- `record_round_response` - 记录专家发言
- `get_session_status` - 查看当前会话状态

### 🔧 专家管理
- `generate_dynamic_experts` - 动态生成专家候选
- `analyze_question_profile` - 深度分析问题特征

### 📊 会话管理
- `view_session_history` - 查看历史会话记录
- `export_session` - 导出会话为Markdown文件
- `export_session_as_infographic` - 生成塔夫特风格单页动态信息图的完整指令
- `export_enhanced_session` - 导出增强分析报告
- `advance_to_next_round` - 手动进入下一轮/专家

### ⚙️ 系统设置
- `get_usage_statistics` - 查看系统使用统计
- `set_language` - 🌍 设置专家回复语言
- `get_language_settings` - 查看当前语言设置
- `guru_pk_help` - 获取系统帮助（本工具）

## 🚀 使用方法

### 🎯 最简单方式：直接提问
```
start_pk_session: 如何在AI时代实现个人突破？
```

### 🎭 指定专家范围（可选）
```
start_pk_session: 生成AI的创业方向有哪些？请找两个AI技术专家和一个创业导师来讨论
```

### 🔍 深度分析问题
```
analyze_question_profile: 我想了解区块链技术的发展前景
```

### 🌍 设置回复语言
```
set_language: english
```

## 🎭 动态专家生成示例

系统可根据问题智能生成各领域专家，例如：

### 技术领域
- **AI架构专家** - 深度学习系统设计，模型优化
- **分布式系统专家** - 高可用架构，性能调优
- **网络安全专家** - 威胁分析，防护策略

### 商业管理
- **数据分析专家** - 商业智能，决策支持
- **组织管理专家** - 团队建设，文化塑造
- **产品战略专家** - 市场定位，用户体验

### 人文社科
- **认知心理学专家** - 思维模式，行为分析
- **教育学专家** - 学习理论，教学方法
- **政治学专家** - 治理理论，制度设计

*注：以上仅为示例，系统可根据任何问题动态生成相应领域的专家*

## 🔄 4轮辩论流程

1. **第1轮：独立思考** - 每位专家独立深度分析问题
2. **第2轮：交叉辩论** - 专家间互相质疑、批评和借鉴
3. **第3轮：最终立场** - 形成各自完善的解决方案
4. **第4轮：智慧综合** - 融合各方观点的终极答案

## 🎯 核心优势

- **问题驱动** - 专家完全服务于具体问题，不受预设限制
- **无限扩展** - 支持任意领域的专家创建和组合
- **智能匹配** - 确保专家组合的多样性和互补性
- **实时生成** - 每次辩论都是独特的专家组合
- **零成本** - 充分利用MCP Host端LLM能力，无API费用

## 💡 使用提示

🤖 **最佳实践**：直接提出您的问题，系统会自动生成最合适的专家组合

📊 **查看统计**：使用`get_usage_statistics`了解系统使用情况

📄 **导出记录**：使用`export_enhanced_session`获得完整的分析报告

🌍 **多语言支持**：使用`set_language`设置专家回复语言

---
*由 Guru-PK MCP 智能专家生成系统提供 - 让思想碰撞，让智慧闪光！*"""

        # 使用预格式化文本确保原始格式显示
        formatted_help = f"```\n{help_text}\n```"
        return [TextContent(type="text", text=formatted_help)]

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
                result += f"{i}. {self._format_expert_info(persona)} - {count}次 ({percentage:.1f}%)\n"

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
- **最近会话**: {sessions[0]["created_at"][:19].replace("T", " ")}
- **本周会话**: {len(recent_sessions)}个"""

            result += """

## 🎯 使用建议
- 尝试不同的专家组合来获得多元化视角
- 完成更多会话以获得更深入的洞察
- 使用 `recommend_personas` 获得智能推荐"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 获取统计失败: {str(e)}")]

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
        """获取问题分析的原则性指导"""
        try:
            question = arguments.get("question", "").strip()
            if not question:
                return [TextContent(type="text", text="❌ 请提供要分析的问题")]

            # 返回问题分析的原则性指导，供MCP Host端LLM使用
            guidance = get_question_analysis_guidance()

            result = f"""📊 **问题分析指导**

**待分析问题**: {question}

{guidance}

## 💡 建议
基于分析结果，建议使用 `generate_dynamic_experts` 工具生成专门的专家推荐。"""

            return [TextContent(type="text", text=result)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 问题分析失败: {str(e)}")]

    async def _handle_generate_dynamic_experts(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """动态生成专家推荐（指导MCP Host端LLM直接生成3位专家）"""
        try:
            question = arguments.get("question", "")

            if not question:
                return [
                    TextContent(
                        type="text",
                        text="❌ 请提供要讨论的问题",
                    )
                ]

            # 获取动态专家生成指导
            guidance = get_expert_recommendation_guidance()

            return [
                TextContent(
                    type="text",
                    text=f"""🤖 **动态专家生成指导**

**问题**: {question}

{guidance}

## 🎯 **MCP Host端LLM任务**

请根据以上指导原则，为这个问题直接生成 **3位专家**，然后立即调用 start_pk_session 启动辩论。

### 专家数据格式：
```json
{{
  "name": "专家姓名",
  "emoji": "🎯",
  "description": "一句话描述专家背景和特长",
  "core_traits": ["特质1", "特质2", "特质3"],
  "speaking_style": "描述专家的表达方式和风格",
  "base_prompt": "详细的角色设定提示词，包含专家背景、思维特点、分析方法等"
}}
```

### 专家设计要求：
1. **专业相关性** - 每位专家都应与问题核心领域高度相关
2. **视角多样性** - 确保不同的思维框架和方法论
3. **互补性平衡** - 理论vs实践、宏观vs微观、创新vs稳健
4. **辩论价值** - 专家间应有观点分歧，能产生有价值的思辨

## 📋 **立即执行**

生成3位专家后，直接调用：

```javascript
start_pk_session({{
  "question": "{question}",
  "personas": [
    {{"name": "专家1", "emoji": "🎯", "description": "...", "core_traits": [...], "speaking_style": "...", "base_prompt": "..."}},
    {{"name": "专家2", "emoji": "🧠", "description": "...", "core_traits": [...], "speaking_style": "...", "base_prompt": "..."}},
    {{"name": "专家3", "emoji": "📊", "description": "...", "core_traits": [...], "speaking_style": "...", "base_prompt": "..."}}
  ],
  "recommended_by_host": true
}})
```

💡 **提示**: 直接生成3位专家即可，无需多选一的中间步骤。确保每位专家的 base_prompt 足够详细和具体。""",
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 专家推荐生成失败: {str(e)}")]

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

            # 新架构中不支持此功能
            insights: dict[str, Any] = {
                "expert_profiles": {},
                "relationships": {},
                "recommendation_details": None,
            }

            result = f"""🔍 **专家洞察分析**

**会话ID**: `{session.session_id}`

## 👥 专家档案"""

            if insights["expert_profiles"]:
                for name, profile in insights["expert_profiles"].items():
                    result += f"""

### {name}
- **专业背景**: {profile["background"]}
- **思维风格**: {profile["thinking_style"]}
- **知识领域**: {", ".join(profile["knowledge_domains"])}
- **核心特质**: {", ".join(profile["personality_traits"])}
- **来源**: {profile["source"]}
- **相关度**: {profile["relevance_score"]:.2f}"""
            else:
                result += "\n暂无专家档案信息。"

            # 推荐详情
            if insights["recommendation_details"]:
                details = insights["recommendation_details"]
                result += f"""

## 🎯 推荐分析
- **推荐理由**: {details["reason"]}
- **多样性评分**: {details["diversity_score"]:.2f}
- **相关性评分**: {details["relevance_score"]:.2f}

### 🔮 预期视角
{chr(10).join(["- " + p for p in details["expected_perspectives"]]) if details["expected_perspectives"] else "- 暂无预期视角信息"}"""

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

            # 生成增强版Markdown内容
            md_content = f"""# 📊 专家PK讨论 - 增强分析报告

**会话ID**: {session.session_id}
**问题**: {session.user_question}
**创建时间**: {session.created_at}
**最后更新**: {session.updated_at}
**参与专家**: {", ".join(session.selected_personas)}

---

## 📈 会话概览

### 基本统计
- **总轮次**: {len(session.responses)} 轮
- **总发言数**: {len([r for round_responses in session.responses.values() for r in round_responses.values()])}
- **字数统计**: {sum(len(r) for round_responses in session.responses.values() for r in round_responses.values()):,} 字符
- **平均每轮发言**: {len([r for round_responses in session.responses.values() for r in round_responses.values()]) / len(session.responses) if session.responses else 0:.1f} 次

### 讨论结构
- **独立思考阶段**: {"✅" if 1 in session.responses else "❌"}
- **交叉辩论阶段**: {"✅" if 2 in session.responses else "❌"}
- **最终立场阶段**: {"✅" if 3 in session.responses else "❌"}
- **智慧综合阶段**: {"✅" if 4 in session.responses else "❌"}
- **最终综合方案**: {"✅" if session.final_synthesis else "❌"}

---

## 👥 专家档案分析

"""

            # 获取专家信息：优先使用会话中保存的，其次使用当前专家管理器的
            expert_profiles = (
                session.expert_profiles or self.expert_manager.get_current_experts()
            )

            for persona_name in session.selected_personas:
                md_content += f"### {persona_name}\n\n"

                if expert_profiles and persona_name in expert_profiles:
                    expert_info = expert_profiles[persona_name]

                    # 确保expert_info是字典类型（兼容ExpertProfile对象）
                    if hasattr(expert_info, "__dict__"):
                        # 如果是对象，转换为字典
                        expert_dict = (
                            expert_info.__dict__
                            if hasattr(expert_info, "__dict__")
                            else {}
                        )
                    else:
                        # 如果已经是字典，直接使用
                        expert_dict = expert_info

                    # 不再在MCP Server端判断真实人物，统一显示为专家
                    person_type = "🎭 专家"
                    md_content += f"**专家类型**: {person_type}\n"
                    md_content += (
                        f"**专业描述**: {expert_dict.get('description', '未知')}\n"
                    )

                    if "core_traits" in expert_dict:
                        md_content += (
                            f"**核心特质**: {', '.join(expert_dict['core_traits'])}\n"
                        )

                    if "speaking_style" in expert_dict:
                        md_content += f"**表达风格**: {expert_dict['speaking_style']}\n"

                    # 添加更多信息
                    if "base_prompt" in expert_dict:
                        # 从base_prompt中提取一些关键信息作为背景
                        prompt_preview = (
                            expert_dict["base_prompt"][:200] + "..."
                            if len(expert_dict["base_prompt"]) > 200
                            else expert_dict["base_prompt"]
                        )
                        md_content += f"**角色背景**: {prompt_preview}\n"
                else:
                    md_content += "**专家信息**: 暂无详细档案\n"

                # 统计该专家的发言情况
                total_words = 0
                total_rounds = 0
                for _round_num, round_responses in session.responses.items():
                    if persona_name in round_responses:
                        total_rounds += 1
                        total_words += len(round_responses[persona_name])

                md_content += f"**参与轮次**: {total_rounds}/{len(session.responses)}\n"
                md_content += f"**发言字数**: {total_words:,} 字符\n"
                md_content += f"**平均发言长度**: {total_words / total_rounds if total_rounds > 0 else 0:.0f} 字符/轮\n\n"

            md_content += """---

## 💬 完整讨论记录

"""

            round_names = {
                1: "🤔 第1轮：独立思考",
                2: "💬 第2轮：交叉辩论",
                3: "🎯 第3轮：最终立场",
                4: "🧠 第4轮：智慧综合",
            }

            round_descriptions = {
                1: "各专家基于自己的知识体系和思维方式，独立分析问题并提出初步观点。",
                2: "专家们审视其他人的观点，进行批判性思考，完善自己的方案。",
                3: "经过前两轮深入思考和辩论，专家们给出最终的、最完善的解决方案。",
                4: "综合大师整合三位专家的方案，形成融合各方精华的终极解决方案。",
            }

            for round_num in sorted(session.responses.keys()):
                md_content += f"## {round_names.get(round_num, f'第{round_num}轮')}\n\n"
                md_content += f"**阶段说明**: {round_descriptions.get(round_num, '该轮次的详细说明')}\n\n"

                round_responses = session.responses[round_num]
                md_content += f"**本轮参与**: {len(round_responses)} 位专家\n"
                md_content += f"**本轮字数**: {sum(len(r) for r in round_responses.values()):,} 字符\n\n"

                for persona, response in round_responses.items():
                    word_count = len(response)
                    md_content += f"### {persona} ({word_count:,} 字符)\n\n"
                    md_content += f"{response}\n\n---\n\n"

            # 添加最终综合方案（如果有且不重复）
            if session.final_synthesis:
                round_4_responses = session.responses.get(4, {})
                is_duplicate = any(
                    session.final_synthesis == response
                    for response in round_4_responses.values()
                )

                if not is_duplicate:
                    md_content += f"""## 🌟 最终综合方案

**字数**: {len(session.final_synthesis):,} 字符

{session.final_synthesis}

---

"""

            md_content += f"""## 📊 深度分析

### 讨论质量指标
- **讨论完整度**: {len(session.responses)}/4 轮次 ({len(session.responses)/4*100:.0f}%)
- **专家参与度**: {len([r for round_responses in session.responses.values() for r in round_responses.values()])/len(session.selected_personas)/len(session.responses)*100 if session.responses else 0:.0f}%
- **内容丰富度**: {sum(len(r) for round_responses in session.responses.values() for r in round_responses.values())/len(session.responses) if session.responses else 0:.0f} 字符/轮

### 专家贡献分析
"""

            # 分析每位专家的贡献
            for persona_name in session.selected_personas:
                total_words = 0
                total_rounds = 0
                rounds: list[str] = []

                for round_num, round_responses in session.responses.items():
                    if persona_name in round_responses:
                        words = len(round_responses[persona_name])
                        total_words += words
                        total_rounds += 1
                        rounds.append(f"第{round_num}轮({words}字)")

                participation_rate = (
                    total_rounds / len(session.responses) * 100
                    if session.responses
                    else 0
                )
                avg_words = total_words / total_rounds if total_rounds > 0 else 0
                md_content += f"- **{persona_name}**: 参与{total_rounds}轮 ({participation_rate:.0f}%), 贡献{total_words:,}字符, 平均{avg_words:.0f}字/轮\n"

            md_content += f"""

### 时间轴分析
- **创建时间**: {session.created_at}
- **最后更新**: {session.updated_at}
- **讨论时长**: 会话期间
- **完成状态**: {"✅ 已完成" if session.final_synthesis else "🔄 进行中"}

---

## 📈 改进建议

### 讨论优化建议
"""

            # 根据统计数据提供建议
            total_rounds = len(session.responses)
            if total_rounds < 4:
                md_content += (
                    "- 🔄 **完整性提升**: 建议完成全部4轮讨论，以获得更深入的思辨效果\n"
                )

            avg_words_per_response = (
                sum(
                    len(r)
                    for round_responses in session.responses.values()
                    for r in round_responses.values()
                )
                / len(
                    [
                        r
                        for round_responses in session.responses.values()
                        for r in round_responses.values()
                    ]
                )
                if session.responses
                else 0
            )

            if avg_words_per_response < 200:
                md_content += (
                    "- 📝 **深度增强**: 专家发言相对简短，可以鼓励更深入的分析和阐述\n"
                )
            elif avg_words_per_response > 800:
                md_content += "- ✂️ **精炼表达**: 专家发言较长，可以适当精炼核心观点\n"

            if not session.final_synthesis:
                md_content += (
                    "- 🎯 **综合完善**: 建议添加最终综合方案，整合各专家观点\n"
                )

            md_content += """
### 专家组合评估
- **多样性**: 专家背景和观点的多元化程度
- **互补性**: 专家知识结构的互补效果
- **权威性**: 专家在各自领域的认可度
- **思辨性**: 专家间观点碰撞的价值

---

## 🔗 相关工具

- 📄 **标准导出**: 使用 `export_session` 获取简化版报告
- 📊 **统计信息**: 使用 `get_usage_statistics` 查看系统使用统计
- 📋 **会话历史**: 使用 `view_session_history` 浏览历史会话

---

*📅 报告生成时间: {session.updated_at}*
*🤖 由 Guru-PK MCP 增强分析系统生成*
"""

            # 保存到文件
            export_file = (
                self.session_manager.data_dir
                / f"enhanced_export_{session.session_id}.md"
            )
            with open(export_file, "w", encoding="utf-8") as f:
                f.write(md_content)

            result = f"""📊 **增强会话报告导出成功！**

**文件路径**: `{export_file}`
**格式**: Enhanced Markdown Report
**会话ID**: {session.session_id}

## 📊 报告内容
- ✅ 完整讨论记录
- ✅ 专家档案分析
- ✅ 统计数据洞察
- ✅ 质量指标评估
- ✅ 贡献度分析
- ✅ 时间轴记录
- ✅ 改进建议总结

## 💡 使用说明
该增强报告包含详细的数据分析和专家档案信息，适合深度复盘和研究使用。

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
