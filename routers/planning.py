from __future__ import annotations

from fastapi import APIRouter

from schemas import PathRequest, PathResponse
from models import path_planning

router = APIRouter()


@router.post("", response_model=PathResponse, summary="学习路径规划")
def recommend_path(payload: PathRequest) -> PathResponse:
    return path_planning.plan(payload)
