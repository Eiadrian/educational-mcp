from __future__ import annotations

from fastapi import APIRouter

from schemas import AffectiveAnalysisRequest, AffectiveAnalysisResponse, SentimentRequest, SentimentResponse
from models import emotion_analysis

router = APIRouter()


@router.post("", response_model=AffectiveAnalysisResponse, summary="情感状态识别")
def analyze_affective(payload: AffectiveAnalysisRequest) -> AffectiveAnalysisResponse:
    return emotion_analysis.analyze_affective_state(payload)


@router.post("/sentiment", response_model=SentimentResponse, summary="情感分类")
def analyze_sentiment(payload: SentimentRequest) -> SentimentResponse:
    return emotion_analysis.analyze_sentiment(payload)
