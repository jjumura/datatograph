import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict, Any, List
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# Gemini API 키 가져오기
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# Gemini API 설정
genai.configure(api_key=GEMINI_API_KEY)

class GeminiHandler:
    """Gemini API를 사용하여 데이터 분석 및 인사이트를 생성하는 클래스"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def analyze_data(self, data: Dict[str, Any]) -> str:
        """
        데이터를 분석하고 인사이트를 생성합니다.
        
        Args:
            data: 분석할 데이터
            
        Returns:
            str: 생성된 분석 결과
        """
        try:
            prompt = f"""
            다음 데이터를 분석하고 주요 인사이트를 제공해주세요:
            {data}
            
            다음 형식으로 응답해주세요:
            1. 주요 트렌드
            2. 이상치 또는 특이사항
            3. 추천 사항
            """
            
            response = await self.model.generate_content_async(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"데이터 분석 중 오류 발생: {str(e)}")
            return f"데이터 분석 중 오류가 발생했습니다: {str(e)}"
    
    async def generate_chart_description(self, chart_type: str, data_summary: Dict[str, Any]) -> str:
        """
        차트와 데이터에 대한 설명을 생성합니다.
        
        Args:
            chart_type: 차트 유형
            data_summary: 데이터 요약 정보
            
        Returns:
            str: 생성된 차트 설명
        """
        try:
            prompt = f"""
            다음 차트와 데이터에 대한 설명을 생성해주세요:
            차트 유형: {chart_type}
            데이터 요약: {data_summary}
            
            다음을 포함하여 설명해주세요:
            1. 차트가 보여주는 주요 정보
            2. 데이터의 특징
            3. 시각화를 통해 얻을 수 있는 인사이트
            """
            
            response = await self.model.generate_content_async(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"차트 설명 생성 중 오류 발생: {str(e)}")
            return f"차트 설명 생성 중 오류가 발생했습니다: {str(e)}" 