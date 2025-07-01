"""
会话管理器 - 负责会话的存储和加载
"""

import json
import sys
from pathlib import Path
from typing import Any

from .dynamic_expert_engine import ExpertGenerator, ExpertRelationshipAnalyzer
from .models import PKSession
from .quality_monitor import DebateQualityMonitor


class SessionManager:
    """增强型会话管理器 - 支持动态专家和自适应轮次"""

    def __init__(
        self, data_dir: str | None = None, custom_persona_manager: Any = None
    ) -> None:
        if data_dir is None:
            # 使用环境变量或默认到用户家目录
            import os

            data_dir = os.environ.get("DATA_DIR", os.path.expanduser("~/.guru-pk-data"))

        self.data_dir = Path(data_dir)
        self.custom_persona_manager = custom_persona_manager
        self.expert_generator = ExpertGenerator(custom_persona_manager)
        self.relationship_analyzer = ExpertRelationshipAnalyzer()
        self.quality_monitor = DebateQualityMonitor()
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

    def create_dynamic_session(
        self,
        question: str,
        selected_experts: list[str] | None = None,
        use_smart_recommendation: bool = True,
    ) -> PKSession:
        """创建动态专家会话"""
        if use_smart_recommendation and not selected_experts:
            # 使用智能推荐生成专家
            recommendation = self.expert_generator.generate_expert_recommendation(
                question
            )

            # 从推荐中选择前3个专家
            selected_experts = [expert.name for expert in recommendation.experts[:3]]

            # 创建会话
            session = PKSession.create_new(
                user_question=question,
                selected_personas=selected_experts,
                debate_mode=recommendation.question_profile.debate_mode,
                question_profile=recommendation.question_profile,
                expert_recommendation=recommendation,
                is_recommended_by_host=True,
            )

            # 设置专家档案
            expert_profiles = {
                expert.name: expert for expert in recommendation.experts[:3]
            }
            session.set_expert_profiles(expert_profiles)

            # 生成专家关系图谱
            relationships = self.relationship_analyzer.analyze_expert_relationships(
                list(expert_profiles.values())
            )
            session.set_expert_relationships(relationships)

        else:
            # 使用传统方式创建会话
            session = PKSession.create_new(
                user_question=question, selected_personas=selected_experts or []
            )

        # 保存会话
        self.save_session(session)
        return session

    def update_session_quality(self, session: PKSession) -> str | None:
        """更新会话质量并返回改进建议"""
        suggestions = self.quality_monitor.monitor_session(session)

        # 保存更新后的会话
        self.save_session(session)

        return suggestions

    def check_adaptive_flow(self, session: PKSession) -> dict[str, Any]:
        """检查自适应流程调整"""
        result = {
            "should_extend": False,
            "should_end_early": False,
            "quality_suggestions": [],
            "current_quality": 0.0,
        }

        if session.quality_metrics:
            result["current_quality"] = session.quality_metrics.overall_score

            # 检查是否需要调整流程
            if self.quality_monitor.should_extend_debate(session):
                result["should_extend"] = True
                session.adjust_max_rounds(session.max_rounds + 1)
                self.save_session(session)

            elif self.quality_monitor.should_end_debate_early(session):
                result["should_end_early"] = True

            # 获取质量改进建议
            suggestions = self.quality_monitor._generate_improvement_suggestions(
                session.quality_metrics, session
            )
            result["quality_suggestions"] = (
                suggestions if suggestions is not None else []
            )

        return result

    def get_expert_insights(self, session: PKSession) -> dict[str, Any]:
        """获取专家洞察信息"""
        insights: dict[str, Any] = {
            "expert_profiles": {},
            "relationships": session.expert_relationships or {},
            "recommendation_details": None,
            "diversity_score": 0.0,
            "relevance_score": 0.0,
        }

        # 专家档案信息
        if session.expert_profiles:
            for name, profile in session.expert_profiles.items():
                expert_profiles = insights.get("expert_profiles", {})
                if not isinstance(expert_profiles, dict):
                    expert_profiles = {}
                    insights["expert_profiles"] = expert_profiles
                expert_profiles[name] = {
                    "background": profile.background,
                    "thinking_style": profile.thinking_style,
                    "knowledge_domains": profile.knowledge_domains,
                    "personality_traits": profile.personality_traits,
                    "source": profile.source,
                    "relevance_score": profile.relevance_score or 0.0,
                }

        # 推荐详情
        if session.expert_recommendation:
            insights["recommendation_details"] = {
                "reason": session.expert_recommendation.recommendation_reason,
                "expected_perspectives": session.expert_recommendation.expected_perspectives,
                "diversity_score": float(
                    session.expert_recommendation.diversity_score or 0.0
                ),
                "relevance_score": float(
                    session.expert_recommendation.relevance_score or 0.0
                ),
            }
            insights["diversity_score"] = float(
                session.expert_recommendation.diversity_score or 0.0
            )
            insights["relevance_score"] = float(
                session.expert_recommendation.relevance_score or 0.0
            )

        return insights

    def generate_session_analytics(self, session: PKSession) -> dict[str, Any]:
        """生成会话分析报告"""
        analytics: dict[str, Any] = {
            "basic_info": {
                "session_id": session.session_id,
                "question": session.user_question,
                "debate_mode": session.debate_mode.value,
                "max_rounds": session.max_rounds,
                "current_round": session.current_round,
                "is_completed": session.is_completed,
                "is_recommended_by_host": session.is_recommended_by_host,
            },
            "quality_metrics": None,
            "expert_analysis": None,
            "interaction_analysis": {},
            "recommendations": [],
        }

        # 质量指标
        if session.quality_metrics:
            analytics["quality_metrics"] = {
                "overall_score": float(session.quality_metrics.overall_score or 0.0),
                "novelty_score": float(session.quality_metrics.novelty_score or 0.0),
                "depth_score": float(session.quality_metrics.depth_score or 0.0),
                "interaction_score": float(
                    session.quality_metrics.interaction_score or 0.0
                ),
                "practicality_score": float(
                    session.quality_metrics.practicality_score or 0.0
                ),
                "feedback": session.quality_metrics.feedback or "",
            }

        # 专家分析
        analytics["expert_analysis"] = self.get_expert_insights(session)

        # 互动分析
        analytics["interaction_analysis"] = self._analyze_expert_interactions(session)

        # 改进建议
        adaptive_check = self.check_adaptive_flow(session)
        if adaptive_check.get("quality_suggestions"):
            if "recommendations" not in analytics:
                analytics["recommendations"] = []
            analytics["recommendations"].append(adaptive_check["quality_suggestions"])

        return analytics

    def _analyze_expert_interactions(self, session: PKSession) -> dict[str, Any]:
        """分析专家互动模式"""
        interactions: dict[str, Any] = {
            "cross_references": {},
            "agreement_patterns": {},
            "conflict_points": {},
            "collaboration_score": 0.0,
        }

        if len(session.responses) < 2:
            return interactions

        personas = session.selected_personas

        # 初始化数据结构
        cross_refs: dict[str, list[dict[str, Any]]] = {}
        agreement_patterns: dict[str, list[int]] = {}
        conflict_points: dict[str, list[int]] = {}

        # 分析互相引用
        for persona in personas:
            cross_refs[persona] = []
            agreement_patterns[persona] = []
            conflict_points[persona] = []

        # 从第2轮开始分析互动
        for round_num in range(2, len(session.responses) + 1):
            if round_num in session.responses:
                round_responses = session.responses[round_num]

                for persona, response in round_responses.items():
                    # 检查是否引用了其他专家
                    for other_persona in personas:
                        if other_persona != persona and other_persona in str(response):
                            cross_refs[persona].append(
                                {
                                    "round": round_num,
                                    "referenced": other_persona,
                                    "context": str(response)[:100] + "...",
                                }
                            )

                    # 简单的情感分析（赞同/反对）
                    response_str = str(response).lower()
                    if any(
                        word in response_str
                        for word in ["同意", "赞同", "正确", "很好"]
                    ):
                        agreement_patterns[persona].append(round_num)

                    if any(
                        word in response_str
                        for word in ["不同意", "反对", "错误", "问题"]
                    ):
                        conflict_points[persona].append(round_num)

        # 设置结果
        interactions["cross_references"] = cross_refs
        interactions["agreement_patterns"] = agreement_patterns
        interactions["conflict_points"] = conflict_points

        # 计算协作评分
        total_references = sum(len(refs) for refs in cross_refs.values())
        total_possible = (
            len(personas) * (len(personas) - 1) * max(len(session.responses) - 1, 1)
        )
        interactions["collaboration_score"] = (
            min(total_references / total_possible, 1.0) if total_possible > 0 else 0.0
        )

        return interactions

    def export_enhanced_session(self, session: PKSession) -> str:
        """导出增强的会话报告"""
        analytics = self.generate_session_analytics(session)

        # 生成详细的Markdown报告
        md_content = f"""# 专家PK会话分析报告

**会话ID**: {session.session_id}
**问题**: {session.user_question}
**创建时间**: {session.created_at}
**辩论模式**: {session.debate_mode.value}
**是否智能推荐**: {'是' if session.is_recommended_by_host else '否'}

## 📊 质量分析
"""

        if analytics["quality_metrics"]:
            metrics = analytics["quality_metrics"]
            md_content += f"""- **总体评分**: {metrics['overall_score']:.1f}/10
- **新颖度**: {metrics['novelty_score']:.1f}/10
- **深度**: {metrics['depth_score']:.1f}/10
- **互动质量**: {metrics['interaction_score']:.1f}/10
- **实用性**: {metrics['practicality_score']:.1f}/10
- **评价**: {metrics['feedback']}

"""

        md_content += "## 👥 专家分析\n\n"

        if analytics["expert_analysis"]["expert_profiles"]:
            for name, profile in analytics["expert_analysis"][
                "expert_profiles"
            ].items():
                md_content += f"""### {name}
- **背景**: {profile['background']}
- **思维风格**: {profile['thinking_style']}
- **知识领域**: {', '.join(profile['knowledge_domains'])}
- **核心特质**: {', '.join(profile['personality_traits'])}
- **来源**: {profile['source']}
- **相关性评分**: {profile['relevance_score']:.2f}

"""

        # 添加原有的讨论记录
        md_content += "\n## 💬 讨论记录\n\n"

        round_names = session._get_round_names()
        for round_num in sorted(session.responses.keys()):
            md_content += f"### {round_names.get(round_num, f'第{round_num}轮')}\n\n"

            for persona, response in session.responses[round_num].items():
                md_content += f"#### {persona}\n\n{response}\n\n---\n\n"

        if session.final_synthesis:
            md_content += f"## 🌟 最终综合方案\n\n{session.final_synthesis}\n\n"

        # 添加分析总结
        if analytics["recommendations"]:
            md_content += "## 📈 改进建议\n\n"
            for rec in analytics["recommendations"]:
                md_content += f"- {rec}\n"

        from datetime import datetime

        md_content += f"\n---\n*由 Guru-PK MCP 动态专家系统生成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

        # 保存到文件
        export_file = self.data_dir / f"enhanced_export_{session.session_id}.md"
        with open(export_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        return str(export_file)
