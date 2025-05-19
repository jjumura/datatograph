from pydantic import BaseModel
from typing import Optional, List, Any

class PromptRequest(BaseModel):
    prompt: str

class GeminiSuggestion(BaseModel):
    data_characteristics: Optional[str] = None
    primary_chart_suggestion: Optional[dict] = None # 상세 구조는 Gemini 응답에 따름
    alternative_chart_suggestions: Optional[List[dict]] = None

class ChartResponse(BaseModel):
    sheet_name: str # 프롬프트의 경우 "Prompt Analysis" 등으로 설정 가능
    original_file_name: str # 프롬프트의 경우 프롬프트 텍스트 일부 또는 고정값
    chart_base64: Optional[str] = None
    columns: Optional[List[str]] = None
    numeric_columns: Optional[List[str]] = None
    rows_count: Optional[int] = None
    error: Optional[str] = None
    gemini_suggestion: Optional[GeminiSuggestion] = None 