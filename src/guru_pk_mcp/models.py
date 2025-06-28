"""
数据模型定义
"""

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass
class PKSession:
    """PK会话数据模型"""

    session_id: str
    user_question: str
    selected_personas: list[str]
    current_round: int  # 1-4 (独立思考、交叉辩论、最终立场、综合分析)
    current_persona_index: int
    responses: dict[int, dict[str, str]]  # {round: {persona: response}}
    final_synthesis: str | None
    created_at: str
    updated_at: str

    @classmethod
    def create_new(
        cls, user_question: str, selected_personas: list[str]
    ) -> "PKSession":
        """创建新的PK会话"""
        now = datetime.now().isoformat()
        return cls(
            session_id=str(uuid.uuid4())[:8],
            user_question=user_question,
            selected_personas=selected_personas,
            current_round=1,
            current_persona_index=0,
            responses={},
            final_synthesis=None,
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PKSession":
        """从字典创建实例"""
        # 处理JSON序列化后responses字典键从int变为str的问题
        if "responses" in data and data["responses"]:
            # 将字符串键转换回整数键
            responses = {}
            for key, value in data["responses"].items():
                responses[int(key)] = value
            data["responses"] = responses
        return cls(**data)

    def get_current_persona(self) -> str:
        """获取当前应该发言的思想家"""
        if self.current_persona_index < len(self.selected_personas):
            return self.selected_personas[self.current_persona_index]
        return ""

    def advance_to_next_persona(self) -> bool:
        """切换到下一个思想家，返回是否还有下一个"""
        self.current_persona_index += 1
        self.updated_at = datetime.now().isoformat()

        if self.current_persona_index >= len(self.selected_personas):
            # 当前轮次所有人都发言完毕，进入下一轮
            self.current_round += 1
            self.current_persona_index = 0
            return self.current_round <= 4
        return True

    def record_response(self, persona: str, response: str) -> None:
        """记录某个思想家的回答"""
        if self.current_round not in self.responses:
            self.responses[self.current_round] = {}

        self.responses[self.current_round][persona] = response
        self.updated_at = datetime.now().isoformat()

    def get_session_status(self) -> dict[str, Any]:
        """获取会话状态信息"""
        round_names = {
            1: "第1轮：独立思考",
            2: "第2轮：交叉辩论",
            3: "第3轮：最终立场",
            4: "第4轮：智慧综合",
        }

        current_persona = self.get_current_persona()

        return {
            "session_id": self.session_id,
            "question": self.user_question,
            "current_round": self.current_round,
            "round_name": round_names.get(self.current_round, "已完成"),
            "current_persona": current_persona,
            "personas": self.selected_personas,
            "completed_responses": len(
                [
                    r
                    for round_responses in self.responses.values()
                    for r in round_responses.values()
                ]
            ),
            "is_completed": self.current_round > 4 or self.final_synthesis is not None,
        }

    def get_round_description(self) -> str:
        """获取当前轮次的描述"""
        round_names = {
            1: "独立思考阶段",
            2: "交叉辩论阶段",
            3: "最终立场阶段",
            4: "智慧综合阶段",
        }
        return round_names.get(self.current_round, "已完成")

    def add_response(self, persona: str, response: str) -> None:
        """添加回应（新方法名，与record_response相同功能）"""
        self.record_response(persona, response)

    def advance_to_next(self) -> str | None:
        """推进到下一位专家，返回下一位专家名称，如果没有则返回None"""
        if self.advance_to_next_persona():
            return self.get_current_persona()
        return None

    @property
    def is_completed(self) -> bool:
        """检查会话是否已完成"""
        return self.current_round > 4 or self.final_synthesis is not None
