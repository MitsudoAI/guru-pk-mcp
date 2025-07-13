"""
A/B测试框架 - 对比序列模式和批处理模式的效果
"""

import json
from pathlib import Path
from typing import Any

from .models import ABTestResult, BatchConfig


class ABTestFramework:
    """A/B测试框架 - 为MCP Host端提供测试指导和结果分析"""

    def __init__(self, data_dir: str | None = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            import os

            self.data_dir = Path(
                os.environ.get("DATA_DIR", "~/.guru-pk-data")
            ).expanduser()

        self.test_results_dir = self.data_dir / "ab_tests"
        self.test_results_dir.mkdir(parents=True, exist_ok=True)

    def get_ab_test_guidance(
        self,
        question: str,
        personas: list[dict[str, Any]],
        batch_config: BatchConfig | None = None,
    ) -> str:
        """为MCP Host端提供A/B测试的完整指导"""

        config = batch_config or BatchConfig.create_default()

        return f"""
# A/B测试执行指导方案

## 测试目标
对比序列模式（SEQUENTIAL）和批处理模式（BATCH）在以下任务上的表现：

**问题**：{question}
**专家数量**：{len(personas)}
**批处理配置**：{config.__dict__}

## 测试方案设计

### 方案A：序列模式（对照组）
- **模式**：SEQUENTIAL
- **轮次**：4轮标准辩论
- **流程**：独立思考 → 交叉辩论 → 最终立场 → 智慧综合
- **特点**：逐个专家发言，真实的时序性

### 方案B：批处理模式（实验组）
- **模式**：BATCH
- **轮次**：4轮批处理辩论
- **流程**：批量独立思考 → 批量交叉辩论 → 批量最终立场 → 智慧综合
- **特点**：专家并发发言，元提示词质量控制

## 测试执行步骤

### 1. 准备阶段
```python
# 记录测试开始时间
test_start_time = time.time()

# 准备相同的输入参数
question = "{question}"
personas = {personas}
```

### 2. 序列模式测试
```python
# 执行序列模式
sequential_start = time.time()

# 使用传统的get_persona_prompt + record_round_response循环
# 记录每轮的token使用量和响应时间

sequential_end = time.time()
sequential_time = sequential_end - sequential_start
```

### 3. 批处理模式测试
```python
# 执行批处理模式
batch_start = time.time()

# 使用新的批处理提示词，一次性生成多个专家的回答
# 记录token使用量和响应时间

batch_end = time.time()
batch_time = batch_end - batch_start
```

### 4. 质量评估
对两种模式的输出进行质量评估：

#### 评估维度
1. **论证深度** (0-10分)
   - 理论框架的完整性
   - 逻辑推理的严密性
   - 案例支撑的充分性

2. **互动质量** (0-10分)
   - 专家间的有效回应
   - 观点碰撞的激烈程度
   - 引用的准确性

3. **观点演进** (0-10分)
   - 从独立思考到最终立场的发展
   - 因辩论产生的新洞察
   - 观点的成熟度提升

4. **实用价值** (0-10分)
   - 解决方案的可操作性
   - 对用户问题的针对性
   - 综合建议的实用性

#### 评估方法
```python
# 使用LLM进行质量评估
quality_prompt = '''
请对以下两个辩论结果进行详细的质量对比分析：

序列模式结果：
[插入序列模式的完整输出]

批处理模式结果：
[插入批处理模式的完整输出]

请从论证深度、互动质量、观点演进、实用价值四个维度，
分别给出0-10分的评分，并详细说明评分理由。

输出格式：
{{
    "sequential_scores": {{
        "depth": 分数,
        "interaction": 分数,
        "evolution": 分数,
        "practicality": 分数,
        "overall": 平均分,
        "reasoning": "详细评分理由"
    }},
    "batch_scores": {{
        "depth": 分数,
        "interaction": 分数,
        "evolution": 分数,
        "practicality": 分数,
        "overall": 平均分,
        "reasoning": "详细评分理由"
    }},
    "comparison": {{
        "winner": "sequential/batch/tie",
        "key_differences": ["主要差异点"],
        "recommendations": "改进建议"
    }}
}}
'''
```

## 性能指标收集

### 时间效率指标
- **总执行时间**：从开始到结束的时间
- **每轮平均时间**：总时间除以轮数
- **时间提升百分比**：(序列时间 - 批处理时间) / 序列时间 * 100%

### Token使用指标
- **总token消耗**：输入token + 输出token
- **每专家平均token**：总token除以专家数量
- **Token效率比**：序列模式token / 批处理模式token

### 质量指标
- **综合质量分**：四个维度的平均分
- **质量差异**：批处理质量分 - 序列质量分
- **质量保持率**：批处理质量分 / 序列质量分 * 100%

## 结果分析框架

### 成功标准
批处理模式被认为成功，当且仅当：
1. **时间效率提升** ≥ 50%
2. **质量保持率** ≥ 90%
3. **用户满意度** ≥ 90%

### 决策矩阵
| 时间提升 | 质量保持 | 推荐策略 |
|---------|---------|----------|
| >60% | >95% | 强烈推荐批处理 |
| 40-60% | 90-95% | 推荐批处理 |
| 20-40% | 80-90% | 谨慎推荐批处理 |
| <20% | <80% | 继续使用序列模式 |

## 输出要求

请执行上述A/B测试，并按以下格式输出测试报告：

```json
{{
    "test_metadata": {{
        "test_id": "唯一测试ID",
        "question": "测试问题",
        "personas": ["专家列表"],
        "test_timestamp": "测试时间",
        "llm_model": "使用的LLM模型"
    }},
    "performance_metrics": {{
        "sequential": {{
            "execution_time": 执行时间,
            "token_count": token数量,
            "rounds_completed": 完成轮数
        }},
        "batch": {{
            "execution_time": 执行时间,
            "token_count": token数量,
            "rounds_completed": 完成轮数
        }},
        "improvement": {{
            "time_saved_percentage": 时间节省百分比,
            "token_efficiency": token效率比,
            "efficiency_gain": 整体效率提升
        }}
    }},
    "quality_assessment": {{
        "sequential_quality": {{各项质量指标}},
        "batch_quality": {{各项质量指标}},
        "quality_comparison": {{对比分析}}
    }},
    "final_recommendation": {{
        "preferred_mode": "sequential/batch",
        "confidence_level": "high/medium/low",
        "reasoning": "详细推理",
        "conditions": "适用条件",
        "follow_up_actions": "后续建议"
    }}
}}
```

## 特别注意事项

1. **公平性保证**：确保两种模式使用相同的输入和评估标准
2. **随机性控制**：如果LLM支持，使用相同的随机种子
3. **多次测试**：建议进行3-5次重复测试取平均值
4. **环境一致性**：确保测试环境的一致性（同一时间段、同一设备等）

通过严格执行此A/B测试方案，我们可以获得批处理模式效果的客观评估。
"""

    def create_test_session_guidance(self) -> str:
        """创建测试会话的指导"""
        return """
# 测试会话创建指导

## 同时创建两个测试会话

### 会话A（序列模式）
```python
session_a = PKSession.create_new(
    user_question=question,
    selected_personas=persona_names,
    debate_mode=DebateMode.STANDARD_DEBATE,
    is_recommended_by_host=False
)
# 保持默认的SEQUENTIAL模式
```

### 会话B（批处理模式）
```python
session_b = PKSession.create_new(
    user_question=question,
    selected_personas=persona_names,
    debate_mode=DebateMode.BATCH_OPTIMIZED,
    is_recommended_by_host=False
)
# 启用批处理模式
session_b.enable_batch_mode(batch_config)
```

## 执行指导

1. **并行执行**：同时启动两个会话的辩论流程
2. **记录指标**：详细记录每个步骤的时间和token消耗
3. **保存结果**：将两个会话的完整结果保存下来
4. **质量对比**：使用标准化的评估程序进行质量对比

## 结果收集

确保收集以下数据：
- 执行时间戳
- Token使用统计
- 每轮响应内容
- 最终综合结果
- 用户体验反馈
"""

    def get_result_analysis_guidance(self) -> str:
        """获取结果分析指导"""
        return """
# A/B测试结果分析指导

## 数据预处理

### 1. 时间数据标准化
```python
# 计算标准化的时间指标
time_per_round_sequential = total_time_sequential / 4
time_per_round_batch = total_time_batch / 4
time_improvement = (time_per_round_sequential - time_per_round_batch) / time_per_round_sequential
```

### 2. Token数据分析
```python
# 计算token效率
token_per_expert_sequential = total_tokens_sequential / (3 * 4)  # 3专家 * 4轮
token_per_expert_batch = total_tokens_batch / (3 * 4)
token_efficiency = token_per_expert_sequential / token_per_expert_batch
```

## 质量评估方法

### 自动化评估
使用LLM进行标准化的质量评估：

```python
def evaluate_debate_quality(sequential_result, batch_result):
    evaluation_prompt = f'''
    请作为专业的辩论质量评估师，对以下两个辩论结果进行客观评估：

    评估标准：
    1. 论证深度（0-10）：理论深度、逻辑严密性、案例丰富度
    2. 互动质量（0-10）：专家回应质量、观点碰撞程度、引用准确性
    3. 观点演进（0-10）：思想发展轨迹、新洞察产生、成熟度提升
    4. 实用价值（0-10）：解决方案可操作性、针对性、综合性

    序列模式结果：
    {sequential_result}

    批处理模式结果：
    {batch_result}

    请提供详细的评分和分析。
    '''
    return llm.evaluate(evaluation_prompt)
```

### 人工评估（可选）
如果需要更高的可信度，可以考虑人工专家评估：
- 招募领域专家进行盲评
- 使用标准化的评估表格
- 多专家评估取平均值

## 统计分析

### 显著性测试
如果进行多次测试，使用t检验验证差异的统计显著性：

```python
from scipy import stats

# 假设进行了5次重复测试
sequential_scores = [8.2, 8.5, 8.1, 8.4, 8.3]
batch_scores = [7.8, 8.0, 7.9, 8.1, 7.7]

t_stat, p_value = stats.ttest_rel(sequential_scores, batch_scores)
```

### 效应量计算
计算Cohen's d来衡量实际效应的大小：

```python
def cohens_d(group1, group2):
    pooled_std = sqrt(((len(group1)-1)*std(group1)**2 + (len(group2)-1)*std(group2)**2) / (len(group1)+len(group2)-2))
    return (mean(group1) - mean(group2)) / pooled_std
```

## 决策建议框架

### 量化决策模型
```python
def make_recommendation(time_improvement, quality_retention, token_efficiency):
    # 加权评分模型
    efficiency_score = min(time_improvement * 100, 100)  # 时间提升，上限100分
    quality_score = quality_retention * 100  # 质量保持，百分比
    resource_score = min(token_efficiency * 50, 100)  # 资源效率，上限100分

    # 加权综合分 (质量权重最高)
    overall_score = (quality_score * 0.5 + efficiency_score * 0.3 + resource_score * 0.2)

    if overall_score >= 85:
        return "强烈推荐批处理模式"
    elif overall_score >= 70:
        return "推荐批处理模式"
    elif overall_score >= 60:
        return "谨慎推荐批处理模式，需要进一步测试"
    else:
        return "建议继续使用序列模式"
```

### 情境化建议
根据不同使用场景提供针对性建议：

- **效率优先场景**：时间提升权重更高
- **质量优先场景**：质量保持权重更高
- **资源受限场景**：token效率权重更高

## 结果报告模板

生成标准化的测试报告，包含：
1. 执行摘要
2. 详细数据分析
3. 质量对比结果
4. 决策建议
5. 改进方向
6. 后续测试计划
"""

    def save_test_result(self, result: ABTestResult) -> bool:
        """保存测试结果到本地文件"""
        try:
            file_path = self.test_results_dir / f"ab_test_{result.test_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                # 序列化ABTestResult
                result_dict = {
                    "test_id": result.test_id,
                    "question": result.question,
                    "personas": result.personas,
                    "sequential_result": result.sequential_result,
                    "sequential_time": result.sequential_time,
                    "sequential_token_count": result.sequential_token_count,
                    "sequential_quality_score": result.sequential_quality_score,
                    "batch_result": result.batch_result,
                    "batch_time": result.batch_time,
                    "batch_token_count": result.batch_token_count,
                    "batch_quality_score": result.batch_quality_score,
                    "time_improvement": result.time_improvement,
                    "token_efficiency": result.token_efficiency,
                    "quality_delta": result.quality_delta,
                    "test_timestamp": result.test_timestamp,
                    "llm_model": result.llm_model,
                    "batch_config": result.batch_config.__dict__,
                }
                json.dump(result_dict, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存测试结果失败: {e}")
            return False

    def load_test_results(self) -> list[dict[str, Any]]:
        """加载所有测试结果"""
        results = []
        try:
            for file_path in self.test_results_dir.glob("ab_test_*.json"):
                with open(file_path, encoding="utf-8") as f:
                    result = json.load(f)
                    results.append(result)
        except Exception as e:
            print(f"加载测试结果失败: {e}")

        return sorted(results, key=lambda x: x.get("test_timestamp", ""), reverse=True)

    def get_performance_summary(self) -> str:
        """获取性能总结报告"""
        results = self.load_test_results()

        if not results:
            return "暂无测试数据"

        # 计算统计指标
        time_improvements = [r.get("time_improvement", 0) for r in results]
        quality_deltas = [r.get("quality_delta", 0) for r in results]
        token_efficiencies = [r.get("token_efficiency", 1) for r in results]

        avg_time_improvement = sum(time_improvements) / len(time_improvements)
        avg_quality_delta = sum(quality_deltas) / len(quality_deltas)
        avg_token_efficiency = sum(token_efficiencies) / len(token_efficiencies)

        summary = f"""
# A/B测试性能总结报告

## 总体统计
- **测试次数**: {len(results)}
- **平均时间提升**: {avg_time_improvement:.1%}
- **平均质量差异**: {avg_quality_delta:+.2f}分
- **平均Token效率**: {avg_token_efficiency:.2f}x

## 关键发现
- **时间效率**: 批处理模式平均节省{avg_time_improvement:.0%}的时间
- **质量保持**: {"质量略有提升" if avg_quality_delta > 0 else "质量基本保持" if avg_quality_delta > -0.5 else "质量有所下降"}
- **资源效率**: Token使用效率提升{(avg_token_efficiency-1)*100:.0f}%

## 推荐策略
"""

        if avg_time_improvement > 0.5 and avg_quality_delta > -0.5:
            summary += "🎯 **强烈推荐使用批处理模式** - 效率大幅提升，质量保持良好"
        elif avg_time_improvement > 0.3 and avg_quality_delta > -1.0:
            summary += "✅ **推荐使用批处理模式** - 效率明显提升，质量可接受"
        elif avg_time_improvement > 0.2:
            summary += "⚠️ **谨慎推荐批处理模式** - 需要根据具体场景选择"
        else:
            summary += "❌ **建议继续使用序列模式** - 批处理优势不明显"

        return summary


class TestResultAnalyzer:
    """测试结果分析器"""

    @staticmethod
    def generate_comparison_report(result: ABTestResult) -> str:
        """生成详细的对比报告"""

        return f"""
# A/B测试详细对比报告

## 测试基本信息
- **测试ID**: {result.test_id}
- **测试时间**: {result.test_timestamp}
- **问题**: {result.question}
- **参与专家**: {', '.join(result.personas)}
- **LLM模型**: {result.llm_model}

## 性能对比分析

### 时间效率
- **序列模式用时**: {result.sequential_time:.2f}秒
- **批处理模式用时**: {result.batch_time:.2f}秒
- **时间节省**: {result.time_improvement:.1f}%
- **效率评级**: {TestResultAnalyzer._get_efficiency_rating(result.time_improvement)}

### 资源使用
- **序列模式Token**: {result.sequential_token_count:,}
- **批处理模式Token**: {result.batch_token_count:,}
- **Token效率**: {result.token_efficiency:.2f}x
- **资源评级**: {TestResultAnalyzer._get_resource_rating(result.token_efficiency)}

### 质量对比
- **序列模式质量分**: {result.sequential_quality_score:.2f}/10
- **批处理模式质量分**: {result.batch_quality_score:.2f}/10
- **质量差异**: {result.quality_delta:+.2f}分
- **质量评级**: {TestResultAnalyzer._get_quality_rating(result.quality_delta)}

## 综合评估

### 优势分析
{TestResultAnalyzer._analyze_advantages(result)}

### 劣势分析
{TestResultAnalyzer._analyze_disadvantages(result)}

### 适用场景
{TestResultAnalyzer._recommend_scenarios(result)}

## 改进建议
{TestResultAnalyzer._suggest_improvements(result)}
"""

    @staticmethod
    def _get_efficiency_rating(improvement: float) -> str:
        if improvement >= 60:
            return "⭐⭐⭐⭐⭐ 优秀"
        elif improvement >= 40:
            return "⭐⭐⭐⭐ 良好"
        elif improvement >= 20:
            return "⭐⭐⭐ 一般"
        elif improvement >= 10:
            return "⭐⭐ 较差"
        else:
            return "⭐ 差"

    @staticmethod
    def _get_resource_rating(efficiency: float) -> str:
        if efficiency >= 2.0:
            return "⭐⭐⭐⭐⭐ 优秀"
        elif efficiency >= 1.5:
            return "⭐⭐⭐⭐ 良好"
        elif efficiency >= 1.2:
            return "⭐⭐⭐ 一般"
        elif efficiency >= 1.0:
            return "⭐⭐ 较差"
        else:
            return "⭐ 差"

    @staticmethod
    def _get_quality_rating(delta: float) -> str:
        if delta >= 0.5:
            return "⭐⭐⭐⭐⭐ 质量提升"
        elif delta >= 0:
            return "⭐⭐⭐⭐ 质量保持"
        elif delta >= -0.5:
            return "⭐⭐⭐ 轻微下降"
        elif delta >= -1.0:
            return "⭐⭐ 明显下降"
        else:
            return "⭐ 显著下降"

    @staticmethod
    def _analyze_advantages(result: ABTestResult) -> str:
        advantages = []

        if result.time_improvement > 30:
            advantages.append("- 显著提高了执行效率，节省大量时间")

        if result.token_efficiency > 1.2:
            advantages.append("- 有效降低了资源消耗，提升成本效益")

        if result.quality_delta >= 0:
            advantages.append("- 保持或提升了输出质量")

        if not advantages:
            advantages.append("- 在当前测试中未发现明显优势")

        return "\n".join(advantages)

    @staticmethod
    def _analyze_disadvantages(result: ABTestResult) -> str:
        disadvantages = []

        if result.quality_delta < -0.5:
            disadvantages.append("- 输出质量有所下降，需要改进")

        if result.time_improvement < 20:
            disadvantages.append("- 时间效率提升不明显")

        if result.token_efficiency < 1.1:
            disadvantages.append("- 资源使用效率改善有限")

        if not disadvantages:
            disadvantages.append("- 在当前测试中未发现明显劣势")

        return "\n".join(disadvantages)

    @staticmethod
    def _recommend_scenarios(result: ABTestResult) -> str:
        scenarios = []

        if result.time_improvement > 40 and result.quality_delta > -0.5:
            scenarios.append("- 时间敏感的咨询场景")
            scenarios.append("- 大批量问题处理")
            scenarios.append("- 资源受限的环境")

        if result.quality_delta < -1.0:
            scenarios.append("- 不适合对质量要求极高的场景")

        if result.time_improvement < 20:
            scenarios.append("- 对于当前问题类型，建议继续使用序列模式")

        return "\n".join(scenarios) if scenarios else "- 需要更多测试数据来确定适用场景"

    @staticmethod
    def _suggest_improvements(result: ABTestResult) -> str:
        suggestions = []

        if result.quality_delta < 0:
            suggestions.append("- 优化批处理提示词，加强质量控制机制")
            suggestions.append("- 提高质量阈值设置")
            suggestions.append("- 增加自检轮次")

        if result.time_improvement < 30:
            suggestions.append("- 进一步优化提示词结构，减少冗余内容")
            suggestions.append("- 考虑更激进的批处理策略")

        if result.token_efficiency < 1.2:
            suggestions.append("- 优化提示词长度，减少不必要的指令")

        if not suggestions:
            suggestions.append("- 当前配置已较为优化，可以投入使用")

        return "\n".join(suggestions)
