"""
动态专家生成系统
"""

from typing import Any


def get_expert_selection_guidance(question: str) -> str:
    """为MCP Host端LLM提供专家选择的指导原则"""
    return f"""
# 专家选择指导原则

## 问题分析
用户问题：{question}

## 专家选择要求
请为这个问题选择3位最合适的专家，确保：

### 1. 专业相关性
- 每位专家都应与问题核心领域高度相关
- 专家的知识背景能为问题提供独特洞察

### 2. 视角多样性
- 三位专家应来自不同的思维框架和方法论
- 避免同质化思考，确保观点碰撞
- 理想组合：理论家+实践家+批判家

### 3. 互补性平衡
- 抽象思维 vs 具体实践
- 宏观视角 vs 微观分析
- 创新思维 vs 稳健审慎
- 东方智慧 vs 西方逻辑

### 4. 辩论价值
- 专家间可能存在观点分歧，产生有价值的思辨
- 每位专家都有独特的解决问题的方法
- 能够形成深度的多轮对话

## 专家定义要求
为每位专家提供：
- **name**: 专家姓名
- **emoji**: 代表性表情符号
- **description**: 一句话描述其特色
- **core_traits**: 3-5个核心特质
- **speaking_style**: 语言风格描述
- **base_prompt**: 详细的角色提示词（包含背景、思维特点、语言风格等）

## 质量标准
- 专家应该是该领域公认的顶尖专业人才
- 角色提示词应该生动具体，能指导高质量回答
- 确保专家的独特性和不可替代性
"""


def generate_round_prompt(
    persona_name: str,
    round_num: int,
    context: dict[str, Any],
    dynamic_personas: dict[str, Any] | None = None,
    language_instruction: str = "请务必使用中文回答。",
) -> str:
    """根据轮次和上下文动态生成prompt"""
    # 使用动态生成的专家
    if dynamic_personas and persona_name in dynamic_personas:
        persona = dynamic_personas[persona_name]
        base = persona["base_prompt"]
    else:
        return f"未知的专家: {persona_name}"

    question = context.get("question", "")

    if round_num == 1:
        # 第1轮：独立思考
        return f"""{base}

{language_instruction}

现在用户向你提出了一个问题：{question}

请以你独特的思维方式和哲学观点来深度分析这个问题。不要参考任何其他人的观点，完全基于你自己的思考给出见解。请保持你的个性化语言风格。"""

    elif round_num == 2:
        # 第2轮：交叉辩论
        my_previous = context.get("my_previous_response", "")
        others = context.get("other_responses", {})

        other_text = ""
        for name, response in others.items():
            if name != persona_name:
                other_text += f"\n\n**{name}的观点：**\n{response}"

        return f"""{base}

{language_instruction}

原问题：{question}

你在第一轮的观点：
{my_previous}

现在，其他专家也给出了他们的观点：{other_text}

请审视其他人的观点，指出你认为的优势和不足，然后基于这种批判性思考来升华和完善你自己的方案。保持你的个性化语言风格。"""

    elif round_num == 3:
        # 第3轮：最终立场
        all_previous = context.get("all_previous_responses", {})

        history_text = ""
        for round_num_key, round_responses in all_previous.items():
            history_text += f"\n\n**第{round_num_key}轮：**"
            for name, response in round_responses.items():
                history_text += (
                    f"\n{name}: {response[:200]}..."
                    if len(response) > 200
                    else f"\n{name}: {response}"
                )

        return f"""{base}

{language_instruction}

这是最后一轮发言机会。经过前两轮的深入思考和辩论，现在请给出你最终的、最完善的解决方案。

原问题：{question}

前两轮的完整讨论历史：{history_text}

请综合考虑所有信息，形成你最终的立场和建议。这应该是你最深思熟虑、最完整的答案。保持你的个性化语言风格。"""

    elif round_num == 4:
        # 第4轮：智慧综合（这轮不用个人persona，而是综合大师）
        all_final_responses = context.get("final_responses", {})

        responses_text = ""
        for name, response in all_final_responses.items():
            responses_text += f"\n\n**{name}的最终方案：**\n{response}"

        return f"""{language_instruction}

你现在是一位智慧的综合大师，需要分析和整合三位专家的最终方案。

原始问题：{question}

三位专家的最终方案：{responses_text}

请执行以下任务：
1. 深度分析每个方案的核心洞察和独特价值
2. 识别三个方案的互补性和协同点
3. 发现可能的盲点和改进空间
4. 创造一个融合三者精华的"终极解决方案"

你的综合方案应该：
- 比任何单一方案都更全面和深刻
- 具有实际的可操作性
- 体现创新性和突破性思维
- 为用户提供真正有价值的指导

💡 **提示**：这次精彩的专家辩论结束后，你可以使用 `export_enhanced_session` 功能将整个讨论过程导出为Markdown文件，方便保存和分享这些宝贵的思维碰撞！"""

    return f"无效的轮次: {round_num}"


def format_persona_info(
    persona_name: str, dynamic_personas: dict[str, Any] | None = None
) -> str:
    """格式化显示专家信息"""
    if dynamic_personas and persona_name in dynamic_personas:
        persona = dynamic_personas[persona_name]

        # 不再在MCP Server端判断真实人物，统一显示为专家
        person_type = "🎭 专家"

        # 使用字符串连接避免f-string中的花括号格式化问题
        return (
            str(persona["emoji"])
            + " **"
            + str(persona["name"])
            + "** ("
            + person_type
            + ") - "
            + str(persona["description"])
        )
    else:
        return "未知专家: " + str(persona_name)
