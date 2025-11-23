"""Pydantic schemas for the AI 教学智能体。

统一描述请求/响应结构，便于 FastAPI 路由与 LLM 工具编排。
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


# ---- 通用 ----


class BaseRequest(BaseModel):
    request_id: Optional[str] = Field(default=None, description="链路追踪 ID，可选")


class BaseResponse(BaseModel):
    request_id: Optional[str] = Field(default=None, description="透传请求 ID")
    mode: str = Field(default="rule", description="实现模式：mock/rule/trained")
    model_version: Optional[str] = Field(default=None, description="实现版本号")


# ---- 数据实体 ----


class KnowledgeStateSchema(BaseModel):
    concept: str
    mastery_level: int = Field(ge=0, le=100)


class EmotionLogSchema(BaseModel):
    emotion: str
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime
    context: Optional[str] = None


class StudentSchema(BaseModel):
    id: int
    name: str
    knowledge_states: List[KnowledgeStateSchema] = []
    emotion_logs: List[EmotionLogSchema] = []
    model_config = ConfigDict(from_attributes=True)


# ---- 认知诊断 ----


class ConceptSnapshot(BaseModel):
    concept_name: str
    attempts: int = Field(gt=0)
    correct: int = Field(ge=0)
    misconceptions: List[str] = []

    @property
    def mastery(self) -> float:
        return min(max(self.correct / self.attempts, 0.0), 1.0)


class CognitiveDiagnosisRequest(BaseRequest):
    student_id: str
    subject: str
    concept_snapshots: List[ConceptSnapshot]
    recent_behaviors: Optional[List[str]] = None


class ConceptDiagnosis(BaseModel):
    concept_name: str
    mastery: float
    level: str
    misconceptions: List[str]
    recommendation: str


class CognitiveDiagnosisResponse(BaseResponse):
    student_id: str
    subject: str
    overall_mastery: float
    strengths: List[str]
    risks: List[str]
    concepts: List[ConceptDiagnosis]
    summary: str


# ---- 知识追踪 ----


class SkillInteraction(BaseModel):
    skill: str
    correct: bool
    time_spent_seconds: Optional[int] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class KnowledgeTracingRequest(BaseRequest):
    student_id: str
    interactions: List[SkillInteraction]
    prior_mastery: Dict[str, float] = Field(default_factory=dict)


class SkillProgress(BaseModel):
    skill: str
    probability_mastery: float
    trend: str
    next_action: str


class KnowledgeTracingResponse(BaseResponse):
    student_id: str
    skills: List[SkillProgress]
    recommended_sequence: List[str]


# ---- 情感 ----


class AffectiveSignal(BaseModel):
    channel: str
    emotion: str
    intensity: float = Field(ge=0.0, le=1.0)
    evidence: Optional[str] = None


class AffectiveAnalysisRequest(BaseRequest):
    student_id: str
    current_task: str
    affective_signals: List[AffectiveSignal]
    recent_performance: Optional[str] = None


class AffectiveState(BaseModel):
    dominant_emotion: str
    confidence: float
    message: str
    regulation_strategies: List[str]


class AffectiveAnalysisResponse(BaseResponse):
    student_id: str
    state: AffectiveState
    nudges: List[str]


class SentimentRequest(BaseRequest):
    text: str


class SentimentResponse(BaseResponse):
    probabilities: Dict[str, float]
    label: str


# ---- 路径规划 ----


class PathRequest(BaseRequest):
    student_id: Optional[str] = None
    mastery: Dict[str, float]
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_recommend: int = Field(default=5, gt=0)


class PathResponse(BaseResponse):
    recommended_path: List[str]
