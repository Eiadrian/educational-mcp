"""知识追踪模块（规则版占位），可替换为 DKVMN/AKT。"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

import database
from schemas import KnowledgeTracingRequest, KnowledgeTracingResponse, SkillInteraction, SkillProgress


def _update_probability(prob: float, interaction: SkillInteraction) -> float:
    prob = max(min(prob, 0.999), 0.001)
    learning_rate = 0.3
    forgetting = 0.4

    if interaction.correct:
        prob = prob + (1 - prob) * learning_rate
    else:
        prob = prob * forgetting

    if interaction.confidence is not None:
        prob = 0.7 * prob + 0.3 * interaction.confidence

    if interaction.time_spent_seconds and interaction.time_spent_seconds > 120:
        prob -= 0.05

    return max(min(prob, 1.0), 0.0)


def trace(payload: KnowledgeTracingRequest) -> KnowledgeTracingResponse:
    prob_map: Dict[str, float] = defaultdict(lambda: 0.5)
    prob_map.update(payload.prior_mastery)
    history: Dict[str, List[bool]] = defaultdict(list)

    for interaction in payload.interactions:
        prev = prob_map[interaction.skill]
        updated = _update_probability(prev, interaction)
        prob_map[interaction.skill] = updated
        history[interaction.skill].append(interaction.correct)

    skills: List[SkillProgress] = []
    for skill, probability in prob_map.items():
        recent = history.get(skill, [])
        if len(recent) >= 2 and recent[-2:] == [True, True]:
            trend = "上升"
        elif recent and not recent[-1]:
            trend = "下降"
        else:
            trend = "平稳"

        if probability >= 0.85:
            action = "安排挑战题巩固迁移。"
        elif probability >= 0.6:
            action = "保持混合题训练，关注错误类型。"
        else:
            action = "回到基础例题，配合讲解反馈。"

        database.set_mastery(payload.student_id, skill, probability)
        skills.append(
            SkillProgress(
                skill=skill,
                probability_mastery=round(probability, 3),
                trend=trend,
                next_action=action,
            )
        )

    recommended_sequence = [item.skill for item in sorted(skills, key=lambda s: s.probability_mastery)]

    return KnowledgeTracingResponse(
        request_id=payload.request_id,
        student_id=payload.student_id,
        skills=skills,
        recommended_sequence=recommended_sequence,
        model_version="rule-0.1",
    )
