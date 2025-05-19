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

# 전역 모델 인스턴스
gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')

async def get_gemini_response(prompt: str) -> str:
    """
    Gemini API를 사용하여 프롬프트에 대한 응답을 생성합니다.
    
    Args:
        prompt: Gemini API에 전송할 프롬프트
        
    Returns:
        str: Gemini API가 생성한 응답 텍스트
    """
    try:
        response = await gemini_model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API 호출 중 오류 발생: {str(e)}")
        raise Exception(f"Gemini API 호출 실패: {str(e)}")

class GeminiHandler:
    """Gemini API를 사용하여 데이터 분석 및 인사이트를 생성하는 클래스"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
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
            """
            
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"데이터 분석 중 오류 발생: {str(e)}")
            return f"분석 실패: {str(e)}"

