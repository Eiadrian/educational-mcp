from __future__ import annotations

from fastapi import APIRouter

from schemas import CognitiveDiagnosisRequest, CognitiveDiagnosisResponse
from models import cognitive_diagnosis

router = APIRouter()


@router.post("", response_model=CognitiveDiagnosisResponse, summary="认知诊断")
def diagnose(payload: CognitiveDiagnosisRequest) -> CognitiveDiagnosisResponse:
    return cognitive_diagnosis.diagnose(payload)
