"""建議與改善項目資料模型"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Priority(str, Enum):
    """優先級"""

    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"

    @property
    def timeframe(self) -> str:
        """對應時間軸"""
        mapping = {
            Priority.HIGH: "立即",
            Priority.MEDIUM: "短期",
            Priority.LOW: "中期",
        }
        return mapping[self]


@dataclass
class Suggestion:
    """單一建議"""

    text: str
    priority: Priority = Priority.MEDIUM
    source: str = ""  # 來源(JSON / LLM / 樣板)


@dataclass
class ActionItem:
    """結構化的行動項目"""

    action: str  # 行動內容
    priority: Priority
    timeframe: str  # 立即/短期/中期/長期
    owner: Optional[str] = None  # 責任單位
    verification: Optional[str] = None  # 如何驗證完成

    def to_bullet(self) -> str:
        """轉為投影片 bullet 格式"""
        prefix = {
            Priority.HIGH: "⚡",
            Priority.MEDIUM: "📅",
            Priority.LOW: "📆",
        }[self.priority]
        return f"{prefix} {self.action}"


@dataclass
class Improvement:
    """改善項目(來自 JSON 的 improvements 陣列)"""

    priority: Priority
    item: str  # 項目分類
    suggestion: str  # 具體建議內容

    @classmethod
    def from_dict(cls, data: dict) -> "Improvement":
        """從 JSON dict 建立"""
        if isinstance(data, str):
            # 簡化格式:"[高] 項目: 建議"
            return cls.from_text(data)
        return cls(
            priority=Priority(data.get("priority", "中")),
            item=data.get("item", ""),
            suggestion=data.get("suggestion", ""),
        )

    @classmethod
    def from_text(cls, text: str) -> "Improvement":
        """從字串解析(支援 "[高] 項目: 建議" 格式)"""
        import re

        # "[高] 根因分析: ..."
        match = re.match(r"\[(高|中|低)\]\s*(.+?):\s*(.+)", text)
        if match:
            return cls(
                priority=Priority(match.group(1)),
                item=match.group(2).strip(),
                suggestion=match.group(3).strip(),
            )
        return cls(priority=Priority.MEDIUM, item="", suggestion=text)

    def to_action_item(self) -> ActionItem:
        """轉為結構化行動項目"""
        return ActionItem(
            action=self.suggestion,
            priority=self.priority,
            timeframe=self.priority.timeframe,
        )


# 為了向後相容,匯出舊名稱
SuggestionItem = Suggestion