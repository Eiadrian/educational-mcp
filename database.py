"""轻量级内存“数据库”，用于演示模块间数据共享。

真实部署可替换为 SQLAlchemy/Redis，这里保留相同接口便于平滑升级。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class KnowledgeState:
    concept: str
    mastery_level: int = 0


@dataclass
class EmotionLog:
    emotion: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Optional[str] = None


@dataclass
class Student:
    id: str
    name: str = ""
    knowledge_states: Dict[str, KnowledgeState] = field(default_factory=dict)
    emotion_logs: List[EmotionLog] = field(default_factory=list)


_STUDENTS: Dict[str, Student] = {}


def get_student(student_id: str) -> Student:
    if student_id not in _STUDENTS:
        _STUDENTS[student_id] = Student(id=student_id)
    return _STUDENTS[student_id]


def update_mastery(student_id: str, concept: str, delta: int) -> int:
    student = get_student(student_id)
    ks = student.knowledge_states.get(concept)
    if not ks:
        ks = KnowledgeState(concept=concept, mastery_level=0)
        student.knowledge_states[concept] = ks
    ks.mastery_level = max(0, min(100, ks.mastery_level + delta))
    return ks.mastery_level


def set_mastery(student_id: str, concept: str, value: float) -> int:
    student = get_student(student_id)
    ks = student.knowledge_states.get(concept)
    if not ks:
        ks = KnowledgeState(concept=concept, mastery_level=0)
        student.knowledge_states[concept] = ks
    ks.mastery_level = int(max(0, min(100, value * 100)))
    return ks.mastery_level


def latest_emotion(student_id: str) -> Optional[EmotionLog]:
    student = get_student(student_id)
    return student.emotion_logs[-1] if student.emotion_logs else None


def log_emotion(student_id: str, emotion: str, confidence: float, context: Optional[str] = None) -> None:
    student = get_student(student_id)
    student.emotion_logs.append(EmotionLog(emotion=emotion, confidence=confidence, context=context))


def dump_mastery(student_id: str) -> Dict[str, float]:
    student = get_student(student_id)
    return {c: ks.mastery_level / 100 for c, ks in student.knowledge_states.items()}
