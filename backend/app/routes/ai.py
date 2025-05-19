from fastapi import APIRouter, HTTPException
from app.utils.gemini_handler import GeminiHandler
from typing import Dict, Any

router = APIRouter(tags=["ai"])
gemini = GeminiHandler()

@router.post("/analyze")
async def analyze_data(data: Dict[str, Any]):
    """데이터 분석 및 인사이트 생성"""
    try:
        result = await gemini.analyze_data(data)
        return {"analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chart-description")
async def generate_chart_description(chart_type: str, data_summary: Dict[str, Any]):
    """차트 설명 생성"""
    try:
        result = await gemini.generate_chart_description(chart_type, data_summary)
        return {"description": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 