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

def _level_from_mastery(mastery: float) -> str:
    if mastery >= 0.85:
        return "稳定掌握"
    if mastery >= 0.65:
        return "发展中"
    return "高风险"

def _priority(m: float) -> int:
    """数值越大表示越优先推荐"""
    if m < 0.65:     # 高风险
        return 3
    if m < 0.85:     # 发展中
        return 2
    return 1         # 稳定掌握，只偶尔复习


def plan(payload: PathRequest) -> PathResponse:
    """
    在拓扑排序的基础上，按“风险优先”选择推荐知识点：

    - 仍然用先修图 ADJ 做拓扑遍历（保证不会越级学习）；
    - 在每一层可学习的节点中：
        * 先按风险等级优先级排序（高风险 > 发展中 > 稳定掌握）；
        * 同等级内按掌握度缺口排序（越不会越优先）；
    - 只有 mastery < payload.threshold 的节点才会被加入推荐列表。
    """
    # 1. 计算入度（拓扑排序用）
    indegree: Dict[str, int] = {k: 0 for k in ADJ}
    for prereq, next_list in ADJ.items():
        for nxt in next_list:
            indegree[nxt] = indegree.get(nxt, 0) + 1

    # 2. 获取掌握度：优先用请求里给的，其次用 student_id 从“数据库”里取
    if payload.mastery:
        mastery = payload.mastery
    elif payload.student_id:
        mastery = database.dump_mastery(payload.student_id)
    else:
        mastery = {}

    def get_mastery(name: str) -> float:
        return float(mastery.get(name, 0.0))

    # 3. 初始化：所有入度为 0 的点作为起点
    queue = deque([k for k, deg in indegree.items() if deg == 0])
    visited: set[str] = set()
    recommended: List[str] = []

    # 4. 分层拓扑 + 风险优先
    while queue and len(recommended) < payload.max_recommend:
        # 当前这一层的所有可处理节点
        current_layer = list(queue)
        queue.clear()

        # 对当前层打分：(priority, gap, name)
        scored_layer = []
        for node in current_layer:
            if node in visited:
                continue
            m = get_mastery(node)
            priority = _priority(m)     # 高风险 3 > 发展中 2 > 稳定掌握 1
            gap = 1.0 - m               # 掌握度缺口，越大说明越不会
            scored_layer.append((priority, gap, node))

        # 按优先级从高到低、缺口从大到小排序
        scored_layer.sort(key=lambda x: (-x[0], -x[1]))

        next_queue = deque()

        # 依次处理这一层的节点
        for priority, gap, node in scored_layer:
            if node in visited:
                continue
            visited.add(node)

            m = get_mastery(node)
            # 是否加入推荐：仍然用 threshold 控制“需要学/复习”的点
            if m < payload.threshold and len(recommended) < payload.max_recommend:
                recommended.append(node)

            # 不管推没推荐，都视为前置已处理，推进后继节点的入度
            for nxt in ADJ.get(node, []):
                indegree[nxt] -= 1
                if indegree[nxt] == 0 and nxt not in visited:
                    next_queue.append(nxt)

            if len(recommended) >= payload.max_recommend:
                break

        # 下一轮从 next_queue 开始
        queue = next_queue

    return PathResponse(
        request_id=payload.request_id,
        recommended_path=recommended,
        model_version="rule-0.2-risk-first",
    )
