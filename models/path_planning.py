"""路径规划模块（规则版），基于先修与掌握度推荐下一步。"""

from __future__ import annotations

from collections import deque
from typing import Dict, List

import json
from pathlib import Path

import database
from schemas import PathRequest, PathResponse

# 测度论与泛函分析知识点先修图（默认配置）
DEFAULT_ADJ: Dict[str, List[str]] = {
    # 测度论基础部分
    "集合论基础": ["外测度", "可测集"],
    "外测度": ["可测集", "测度"],
    "可测集": ["测度", "可测函数"],
    "测度": ["可测函数", "Lebesgue积分"],
    "可测函数": ["Lebesgue积分"],
    "Lebesgue积分": ["乘积测度", "Fubini定理", "Lp空间"],
    "乘积测度": ["Fubini定理"],
    "Fubini定理": [],
    "Lp空间": ["泛函分析基础"],
    # 泛函分析部分
    "度量空间": ["赋范空间", "Banach空间"],
    "赋范空间": ["Banach空间", "Hilbert空间"],
    "Banach空间": ["线性算子", "对偶空间"],
    "Hilbert空间": ["线性算子", "对偶空间"],
    "线性算子": ["紧算子", "谱理论"],
    "对偶空间": ["弱拓扑"],
    "弱拓扑": [],
    "紧算子": ["谱理论"],
    "谱理论": [],
    "泛函分析基础": ["度量空间"],
}


def load_adj() -> Dict[str, List[str]]:
    """
    优先从外部 JSON 配置加载先修图，文件不存在时回退到 DEFAULT_ADJ。

    JSON 文件示例（knowledge_graph.json）:
    {
        "集合论基础": ["外测度", "可测集"],
        "外测度": ["可测集", "测度"],
        "...": ["..."]
    }
    """
    cfg_path = Path("knowledge_graph.json")
    if cfg_path.exists():
        try:
            with cfg_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # 确保 value 全部是 list
            return {k: list(v) for k, v in data.items()}
        except Exception:
            # 若解析失败，退回默认配置，避免整个服务挂掉
            return DEFAULT_ADJ
    return DEFAULT_ADJ


ADJ: Dict[str, List[str]] = load_adj()


def plan(payload: PathRequest) -> PathResponse:
    indegree: Dict[str, int] = {k: 0 for k in ADJ}
    for prereq, next_list in ADJ.items():
        for nxt in next_list:
            indegree[nxt] = indegree.get(nxt, 0) + 1

    if payload.mastery:
        mastery = payload.mastery
    elif payload.student_id:
        mastery = database.dump_mastery(payload.student_id)
    else:
        mastery = {}
    queue = deque([k for k, deg in indegree.items() if deg == 0])
    recommended: List[str] = []
    visited = set()

    while queue and len(recommended) < payload.max_recommend:
        cur = queue.popleft()
        visited.add(cur)
        if mastery.get(cur, 0.0) < payload.threshold:
            recommended.append(cur)
            if len(recommended) >= payload.max_recommend:
                break
        for nxt in ADJ.get(cur, []):
            indegree[nxt] -= 1
            if indegree[nxt] == 0 and nxt not in visited:
                queue.append(nxt)

    return PathResponse(
        request_id=payload.request_id,
        recommended_path=recommended,
        model_version="rule-0.1",
    )
