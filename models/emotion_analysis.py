"""情绪分析模块（规则占位，可换真实模型）。"""

from __future__ import annotations

from typing import Dict

import database
from schemas import AffectiveAnalysisRequest, AffectiveAnalysisResponse, AffectiveState, SentimentRequest, SentimentResponse

POSITIVE_WORDS = {"好", "满意", "喜欢", "清晰", "有趣", "赞", "棒"}
NEGATIVE_WORDS = {"差", "糟", "难", "晦涩", "失望", "生气", "不满", "不会", "不懂", "好难", "不知道"}


def _simple_score(text: str) -> Dict[str, float]:
    pos_hits = sum(word in text for word in POSITIVE_WORDS)
    neg_hits = sum(word in text for word in NEGATIVE_WORDS)
    total = pos_hits + neg_hits
    if total == 0:
        return {"负面": 0.2, "中性": 0.6, "正面": 0.2}
    pos_prob = pos_hits / total
    neg_prob = neg_hits / total
    return {
        "负面": round(0.1 + 0.8 * neg_prob, 3),
        "中性": 0.1,
        "正面": round(0.1 + 0.8 * pos_prob, 3),
    }


def analyze_sentiment(payload: SentimentRequest) -> SentimentResponse:
    prob_dict = _simple_score(payload.text)
    label = max(prob_dict.items(), key=lambda x: x[1])[0]
    return SentimentResponse(
        request_id=payload.request_id,
        probabilities=prob_dict,
        label=label,
        model_version="rule-0.1",
    )


def analyze_affective_state(payload: AffectiveAnalysisRequest) -> AffectiveAnalysisResponse:
    weights: Dict[str, float] = {}
    for sig in payload.affective_signals:
        weights[sig.emotion.lower()] = weights.get(sig.emotion.lower(), 0.0) + sig.intensity
    if not weights:
        dominant, confidence = "neutral", 0.2
    else:
        dominant, score = max(weights.items(), key=lambda item: item[1])
        total = sum(weights.values())
        confidence = score / total if total else 0.0

    if dominant in {"frustration", "anxious", "沮丧"}:
        message = f"检测到 {payload.student_id} 在「{payload.current_task}」中可能感到挫折。建议先处理最关键步骤。"
    elif dominant in {"bored", "disengaged"}:
        message = f"{payload.student_id} 的情绪趋于低唤醒，可尝试切换更具挑战性的子任务。"
    elif dominant in {"confident", "excited", "积极"}:
        message = f"{payload.student_id} 状态积极，可趁势加入举一反三的问题。"
    else:
        message = f"{payload.student_id} 情绪较为平稳，保持当前节奏并轻量检查理解情况。"

    if payload.recent_performance:
        message += f" 学习表现备注：{payload.recent_performance}。"

    database.log_emotion(payload.student_id, dominant, confidence, message)

    state = AffectiveState(
        dominant_emotion=dominant,
        confidence=round(confidence, 3),
        message=message,
        regulation_strategies=[
            "使用 1-2 句同理心话语回应学生感受。",
            f"根据情绪状态对「{payload.current_task}」调整脚手架层级。",
        ],
    )

    nudges = [
        "给出分步提示或降低任务难度。",
        "安排 2 分钟休息或切换轻量任务。",
    ]

    return AffectiveAnalysisResponse(
        request_id=payload.request_id,
        student_id=payload.student_id,
        state=state,
        nudges=nudges,
        model_version="rule-0.1",
    )
