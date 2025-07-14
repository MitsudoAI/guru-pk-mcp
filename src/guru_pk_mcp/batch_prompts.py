"""
批处理提示词模板系统 - 实现元提示词方案
"""

from typing import Any

from .models import BatchConfig


class BatchPromptGenerator:
    """批处理提示词生成器"""

    def __init__(self, config: BatchConfig | None = None):
        self.config = config or BatchConfig.create_default()

    def get_batch_prompt(
        self,
        round_type: str,
        personas: list[dict[str, Any]],
        question: str,
        previous_responses: dict[str, Any] | None = None,
        language_instruction: str = "请务必使用中文回答。",
    ) -> str:
        """获取批处理模式的提示词"""

        if round_type == "independent_thinking":
            return self._get_independent_thinking_prompt(
                personas, question, language_instruction
            )
        elif round_type == "cross_debate":
            return self._get_cross_debate_prompt(
                personas, question, previous_responses, language_instruction
            )
        elif round_type == "final_position":
            return self._get_final_position_prompt(
                personas, question, previous_responses, language_instruction
            )
        elif round_type == "synthesis":
            return self._get_synthesis_prompt(
                question, previous_responses, language_instruction
            )
        else:
            raise ValueError(f"未知的轮次类型: {round_type}")

    def _get_independent_thinking_prompt(
        self, personas: list[dict[str, Any]], question: str, language_instruction: str
    ) -> str:
        """获取独立思考阶段的批处理提示词"""

        expert_intro = self._format_expert_introductions(personas)

        base_prompt = f"""# 专家独立思考阶段（批处理模式）

## 任务说明
三位专家将对以下问题进行独立深度分析。**重要：每位专家都不知道其他人的观点，请严格保持独立性。**

**问题**：{question}

## 专家团队介绍
{expert_intro}

## 虚拟发言顺序（体现时序性）
为了模拟真实的轮流发言效果，请按以下顺序生成内容，每位专家的分析都应该基于其独特视角：

1. **{personas[0]['name']}** 首先发言 - 基于{self._get_thinking_approach(personas[0])}
2. **{personas[1]['name']}** 接着发言 - 基于{self._get_thinking_approach(personas[1])}
3. **{personas[2]['name']}** 最后发言 - 基于{self._get_thinking_approach(personas[2])}

## 输出格式要求
```
### {personas[0]['name']}的独立思考

[1800-2200字的深度分析，必须体现：
- 该专家的独特理论框架和方法论
- 具体案例或经验支撑
- 清晰的逻辑结构和论证链条
- 鲜明的个人风格和表达方式
- 从该专家视角出发的独到见解]

### {personas[1]['name']}的独立思考

[1800-2200字的深度分析，要求同上，但视角和方法论完全不同]

### {personas[2]['name']}的独立思考

[1800-2200字的深度分析，要求同上，形成第三种独特视角]
```

{language_instruction}

## 质量自检清单（生成后必须检查）
{self._get_quality_checklist('independent')}

{self._get_enhancement_instructions()}
"""

        return base_prompt

    def _get_cross_debate_prompt(
        self,
        personas: list[dict[str, Any]],
        question: str,
        previous_responses: dict[str, Any] | None,
        language_instruction: str,
    ) -> str:
        """获取交叉辩论阶段的批处理提示词"""

        round1_summary = (
            self._format_previous_summary(previous_responses)
            if previous_responses
            else ""
        )

        return f"""# 交叉辩论阶段（批处理模式）

## 背景说明
专家们已经听到了彼此在第一轮的独立观点，现在进入激烈的思想碰撞阶段。

**原问题**：{question}

## 第一轮观点回顾
{round1_summary}

## 辩论规则与要求
1. **必须具体引用**：准确引用其他专家的观点，使用引号标注原文
2. **真实的碰撞**：既要有认同，更要有质疑和批判
3. **建设性辩论**：指出问题的同时提供改进思路
4. **保持个性**：符合每位专家的理论框架和表达风格
5. **逻辑严密**：每个批判都要有充分的理由和依据

## 虚拟辩论时序（模拟连续对话）
想象三位专家坐在圆桌前，按照以下顺序进行辩论：

**第一轮发言顺序**：
- {personas[0]['name']} → {personas[1]['name']} → {personas[2]['name']}

每位专家都听到了前面专家的发言，并基于此进行回应。

## 输出格式要求
```
### {personas[0]['name']}回应其他专家

[1400-1800字，必须包含：
- 对{personas[1]['name']}核心观点的具体回应（引用原文并批判分析）
- 对{personas[2]['name']}核心观点的具体回应（引用原文并批判分析）
- 从自己的理论视角提出的反驳或补充
- 基于辩论产生的新洞察或观点修正]

### {personas[1]['name']}回应其他专家

[1400-1800字，结构要求同上，但角度和论证方式完全不同]

### {personas[2]['name']}回应其他专家

[1400-1800字，结构要求同上，形成第三种批判视角]
```

{language_instruction}

## 辩论深度检查（生成后必须自检）
{self._get_quality_checklist('debate')}

{self._get_enhancement_instructions()}
"""

    def _get_final_position_prompt(
        self,
        personas: list[dict[str, Any]],
        question: str,
        previous_responses: dict[str, Any] | None,
        language_instruction: str,
    ) -> str:
        """获取最终立场阶段的批处理提示词"""

        debate_summary = (
            self._extract_key_debates(previous_responses) if previous_responses else ""
        )

        return f"""# 最终立场阶段（批处理模式）

## 任务说明
经过独立思考和激烈辩论，专家们现在需要给出最终立场。这不是简单的总结，而是经过思想碰撞后的升华和成熟。

**原问题**：{question}

## 前两轮的核心交锋点
{debate_summary}

## 最终立场要求
1. **体现演进**：明确说明观点如何因辩论而深化或调整
2. **保持独特性**：在吸收他人观点的同时保持自己的核心立场
3. **提供方案**：不只是理论分析，要有具体可行的建议
4. **展望未来**：指出问题的长远影响和发展方向
5. **整合创新**：基于辩论产生的新思路和突破

## 虚拟最终陈述时序
模拟三位专家进行最终陈述的场景：

**陈述顺序**：{personas[0]['name']} → {personas[1]['name']} → {personas[2]['name']}

每位专家都充分考虑了前面所有讨论内容，给出自己最成熟的观点。

## 输出格式要求
```
### {personas[0]['name']}的最终立场

[2000-2500字，必须包含：
- **观点演进**：我的初始观点是...，经过辩论我认识到...，现在我的立场是...
- **核心观点**：基于以上分析，我坚持认为...，主要理由是...
- **具体方案**：针对这个问题，我的具体建议是...（包含可操作的步骤）
- **长远思考**：从更宏观的角度看，这个问题的意义在于...
- **回应质疑**：对于其他专家的质疑，我的回应是...]

### {personas[1]['name']}的最终立场

[2000-2500字，结构要求同上，但观点和方案完全不同]

### {personas[2]['name']}的最终立场

[2000-2500字，结构要求同上，形成第三种成熟方案]
```

{language_instruction}

## 最终质量把关（生成后必须检查）
{self._get_quality_checklist('final')}

{self._get_enhancement_instructions()}
"""

    def _get_synthesis_prompt(
        self,
        question: str,
        previous_responses: dict[str, Any] | None,
        language_instruction: str,
    ) -> str:
        """获取智慧综合阶段的提示词"""

        all_responses_summary = (
            self._format_all_responses(previous_responses) if previous_responses else ""
        )

        return f"""# 智慧综合阶段

## 任务说明
作为综合大师，你需要超越三位专家的个体局限，提炼出更高层次的洞察和解决方案。

**原问题**：{question}

## 三轮完整辩论回顾
{all_responses_summary}

## 综合任务要求
1. **超越个体**：发现专家们都没有看到的盲点和机会
2. **寻找共性**：找出深层的一致性和根本分歧
3. **构建框架**：创建一个能容纳所有观点的更大理论框架
4. **实践指导**：将理论洞察转化为可执行的行动方案
5. **价值创造**：产生比单一专家观点更有价值的综合方案

## 输出结构要求
```
### 1. 核心洞察提炼（500字）
- 三位专家观点的深层共识是什么？
- 关键分歧点及其根源在哪里？
- 他们共同忽视的重要维度有哪些？

### 2. 创新性综合框架（800字）
- 超越个体观点的新视角和新模型
- 整合三种方法论的创新理论框架
- 解决核心分歧的更高维度思路

### 3. 系统性行动方案（1000字）
- **短期措施**（3个月内）：立即可行的具体行动
- **中期计划**（1年内）：系统性改进和建设方案
- **长期战略**（3-5年）：根本性变革和愿景实现

### 4. 风险机遇分析（500字）
- 主要风险点及其应对策略
- 潜在机遇及其把握方式
- 成功实施的关键成功要素

### 5. 实施路径指导（300字）
- 优先级排序和实施步骤
- 资源配置和组织保障建议
- 效果评估和动态调整机制
```

{language_instruction}

## 综合质量标准（生成后必须自我评估）
{self._get_quality_checklist('synthesis')}

## 特别提醒
记住：你不是第四位专家，而是站在更高维度的智慧综合者。你的价值在于：
- 发现专家们之间的深层连接
- 构建超越个体局限的整体解决方案
- 提供具有实际指导意义的行动框架
- 创造出"1+1+1>3"的协同效应

{self._get_enhancement_instructions()}
"""

    def _format_expert_introductions(self, personas: list[dict[str, Any]]) -> str:
        """格式化专家介绍"""
        intros = []
        for i, persona in enumerate(personas, 1):
            intro = f"""{i}. **{persona['name']}** {persona.get('emoji', '🎭')}
   - 专业背景：{persona.get('description', '')}
   - 核心特质：{', '.join(persona.get('core_traits', []))}
   - 表达风格：{persona.get('speaking_style', '')}
   - 思维特点：{self._extract_thinking_style(persona)}"""
            intros.append(intro)
        return "\n\n".join(intros)

    def _get_thinking_approach(self, persona: dict[str, Any]) -> str:
        """获取专家的思维方式描述"""
        traits = persona.get("core_traits", [])
        if not traits:
            return "其独特的专业视角"
        return f"其{traits[0]}的特质和专业背景"

    def _extract_thinking_style(self, persona: dict[str, Any]) -> str:
        """从专家信息中提取思维风格"""
        base_prompt = persona.get("base_prompt", "")
        # 简单提取关键词
        if "理性" in base_prompt or "逻辑" in base_prompt:
            return "理性分析和逻辑推理"
        elif "实践" in base_prompt or "经验" in base_prompt:
            return "实践导向和经验总结"
        elif "创新" in base_prompt or "创造" in base_prompt:
            return "创新思维和突破性思考"
        else:
            return "独特的专业思维方式"

    def _format_previous_summary(
        self, previous_responses: dict[str, Any] | None
    ) -> str:
        """格式化前一轮的回答摘要"""
        if not previous_responses:
            return "暂无前序讨论内容"

        summary = "### 第一轮独立思考要点摘要\n\n"

        round1 = previous_responses.get("1", {}) if previous_responses else {}
        for persona, response in round1.items():
            # 提取核心观点（取前300字作为摘要）
            core_view = response[:300] + "..." if len(response) > 300 else response
            summary += f"**{persona}的核心观点**：\n{core_view}\n\n"

        return summary

    def _extract_key_debates(self, previous_responses: dict[str, Any] | None) -> str:
        """提取关键辩论点"""
        if not previous_responses:
            return "暂无辩论历史"

        summary = "### 前两轮讨论的核心交锋点\n\n"

        # 简化处理：列出各轮的主要观点
        for round_num in ["1", "2"]:
            if round_num in previous_responses:
                round_name = "独立思考" if round_num == "1" else "交叉辩论"
                summary += f"**第{round_num}轮 - {round_name}阶段**：\n"

                round_responses = previous_responses[round_num]
                for persona, response in round_responses.items():
                    # 提取关键点
                    key_point = (
                        response[:200] + "..." if len(response) > 200 else response
                    )
                    summary += f"- {persona}：{key_point}\n"
                summary += "\n"

        return summary

    def _format_all_responses(self, previous_responses: dict[str, Any] | None) -> str:
        """格式化所有轮次的回答"""
        if not previous_responses:
            return "暂无讨论历史"

        summary = "### 完整辩论历程回顾\n\n"

        round_names = {"1": "独立思考", "2": "交叉辩论", "3": "最终立场"}

        for round_num in sorted(previous_responses.keys()):
            round_name = round_names.get(round_num, f"第{round_num}轮")
            summary += f"## {round_name}阶段\n\n"

            round_responses = previous_responses[round_num]
            for persona, response in round_responses.items():
                # 提取核心内容
                core_content = (
                    response[:400] + "..." if len(response) > 400 else response
                )
                summary += f"**{persona}**：{core_content}\n\n"

        return summary

    def _get_quality_checklist(self, stage: str) -> str:
        """获取质量检查清单"""
        base_checks = [
            "✓ 每位专家的分析都达到规定字数要求（充分利用增加的字数空间展开深度思考）",
            "✓ 每位专家都体现了其独特的理论框架和背景",
            "✓ 语言风格符合每位专家的设定",
            "✓ 内容有理论深度，不是泛泛而谈",
            "✓ 字数增加转化为质量提升，而非冗余内容",
        ]

        if stage == "independent":
            specific_checks = [
                "✓ 没有出现专家之间的相互引用（他们还不知道彼此观点）",
                "✓ 每位专家都基于其背景给出了独特视角",
                "✓ 观点具有原创性和专业性",
                "✓ 充分利用1800-2200字的空间构建完整的理论体系",
            ]
        elif stage == "debate":
            specific_checks = [
                "✓ 每位专家都明确引用了其他人的具体观点",
                "✓ 有真正的思想碰撞而非表面认同",
                "✓ 产生了新的见解或视角",
                "✓ 辩论推进了对问题的理解",
                "✓ 充分利用1400-1800字展开深入的思想碰撞和理性辩驳",
            ]
        elif stage == "final":
            specific_checks = [
                "✓ 每位专家都清楚展示了观点的演进轨迹",
                "✓ 最终立场既有继承又有发展",
                "✓ 提出了可操作的具体建议",
                "✓ 三个立场形成了互补而非重复",
                "✓ 充分利用2000-2500字构建成熟、完整的最终立场和实施方案",
            ]
        elif stage == "synthesis":
            specific_checks = [
                "✓ 真正超越了三位专家的视角",
                "✓ 提出了专家们都没想到的新见解",
                "✓ 框架具有实际指导意义",
                "✓ 方案具体可执行",
            ]
        else:
            specific_checks = []

        all_checks = base_checks + specific_checks
        return (
            "\n".join(all_checks)
            + "\n\n**如果发现任何一项不满足，请立即改进相关内容。**"
        )

    def _get_enhancement_instructions(self) -> str:
        """获取增强指令"""
        if not self.config.enable_self_check:
            return ""

        return """
## 质量增强指令

如果生成的内容在任何方面不符合上述要求，请：

1. **立即识别问题**：明确指出哪些方面需要改进
2. **针对性修正**：重新生成不合格的部分
3. **整体检查**：确保修正后的内容与整体保持一致
4. **最终验证**：再次对照质量清单进行检查

**重要提醒**：只有在所有质量标准都得到满足后，才能输出最终版本。
"""


class PromptOptimizer:
    """提示词优化器 - 根据问题类型和专家组合优化提示词"""

    @staticmethod
    def optimize_for_question_type(base_prompt: str, question: str) -> str:
        """根据问题类型优化提示词"""
        optimizations = []

        if any(keyword in question for keyword in ["技术", "算法", "系统", "架构"]):
            optimizations.append(
                """
## 技术问题特别要求
- 必须有具体的技术细节和实现方案
- 避免空泛的技术术语堆砌
- 要有实际案例、数据或代码示例支持
- 考虑技术可行性和实现成本
"""
            )

        if any(keyword in question for keyword in ["管理", "战略", "组织", "领导"]):
            optimizations.append(
                """
## 管理问题特别要求
- 结合具体的组织情境和管理实践
- 考虑人的因素和组织文化影响
- 提供可操作的管理工具和方法
- 分析风险和实施难点
"""
            )

        if any(
            keyword in question for keyword in ["伦理", "道德", "价值观", "社会责任"]
        ):
            optimizations.append(
                """
## 伦理问题特别要求
- 多维度考虑伦理影响和社会责任
- 平衡不同利益相关者的诉求
- 考虑长远的社会影响和价值观建设
- 提供伦理决策的原则和框架
"""
            )

        if optimizations:
            return base_prompt + "\n" + "\n".join(optimizations)

        return base_prompt

    @staticmethod
    def optimize_for_expert_diversity(
        base_prompt: str, personas: list[dict[str, Any]]
    ) -> str:
        """根据专家多样性优化提示词"""
        if len(personas) < 3:
            return base_prompt

        # 检查专家之间的差异程度
        domains = set()
        styles = set()

        for persona in personas:
            traits = persona.get("core_traits", [])
            if traits:
                domains.update(traits)

            style = persona.get("speaking_style", "")
            if style:
                styles.add(style)

        # 如果专家差异较大，强调冲突
        if len(domains) >= 6 or len(styles) >= 3:
            enhancement = """
## 高差异专家组合特别指令
由于专家背景差异显著，请特别注意：
- 充分体现不同理论框架的碰撞
- 强调方法论和价值观的差异
- 鼓励更激烈的观点交锋
- 寻找在差异中的创新融合点
"""
            return base_prompt + "\n" + enhancement

        return base_prompt
