from __future__ import annotations

from fastapi import APIRouter

from schemas import KnowledgeTracingRequest, KnowledgeTracingResponse
from models import knowledge_tracking

router = APIRouter()


@router.post("", response_model=KnowledgeTracingResponse, summary="知识追踪")
def trace(payload: KnowledgeTracingRequest) -> KnowledgeTracingResponse:
    return knowledge_tracking.trace(payload)
