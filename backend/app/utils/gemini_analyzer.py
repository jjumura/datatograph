import google.generativeai as genai
import os
import pandas as pd
import logging
import json
import re

logger = logging.getLogger(__name__)

# .env 파일에서 API 키 로드 (main.py나 설정 파일에서 로드한 것을 주입받는 것이 더 좋습니다.)
# 여기서는 간단하게 os.getenv를 사용합니다.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY가 환경 변수에 설정되어 있지 않습니다. Gemini 분석 기능이 제한될 수 있습니다.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Gemini API 설정 중 오류 발생: {e}")
        GEMINI_API_KEY = None # 오류 발생 시 API 키 사용 불가 처리

def get_data_summary_for_prompt(df: pd.DataFrame, max_unique_values_preview=10) -> dict:
    """DataFrame의 요약 정보를 프롬프트에 사용할 형태로 만듭니다."""
    try:
        column_info_str = []
        for col in df.columns:
            col_type = str(df[col].dtype)
            # 날짜/시간 타입 특별 처리
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                col_type = "datetime"
            elif pd.api.types.is_numeric_dtype(df[col]):
                col_type = "numeric"
            elif pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
                col_type = "categorical/string"
            column_info_str.append(f"- '{col}' (Type: {col_type})")
        
        column_info = "\n".join(column_info_str)
        
        # 데이터 샘플 문자열 (최대 길이 제한)
        data_head_str = df.head().to_string(max_colwidth=50) 
        
        data_describe_str = "수치형 데이터가 없습니다."
        numeric_df = df.select_dtypes(include=['number'])
        if not numeric_df.empty:
            data_describe_str = numeric_df.describe().to_string()
            
        unique_counts_str = []
        for col in df.columns:
            if df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(df[col]):
                nunique = df[col].nunique()
                if nunique <= max_unique_values_preview:
                    preview_values = df[col].unique()[:max_unique_values_preview]
                    unique_counts_str.append(f"- '{col}': {nunique} unique values (e.g., {', '.join(map(str, preview_values))})")
                else:
                    unique_counts_str.append(f"- '{col}': {nunique} unique values")

        unique_counts_info = "\n".join(unique_counts_str) if unique_counts_str else "카테고리형 데이터가 없거나 고유값이 많습니다."

        return {
            "column_info": column_info,
            "data_head": data_head_str,
            "data_describe": data_describe_str,
            "unique_counts_info": unique_counts_info,
            "num_rows": df.shape[0],
            "num_cols": df.shape[1]
        }
    except Exception as e:
        logger.error(f"DataFrame 요약 정보 생성 중 오류: {e}")
        return {
            "column_info": "Error generating column info.",
            "data_head": "Error generating data head.",
            "data_describe": "Error generating data describe.",
            "unique_counts_info": "Error generating unique counts info.",
            "num_rows": 0,
            "num_cols": 0,
            "error": str(e)
        }

def generate_chart_suggestion_prompt(df_summary: dict) -> str:
    """Gemini API에 전송할 프롬프트를 생성합니다."""
    
    prompt = f"""
당신은 숙련된 데이터 분석가이자 시각화 전문가입니다.
주어진 Pandas DataFrame (총 {df_summary.get('num_rows', 'N/A')}행, {df_summary.get('num_cols', 'N/A')}열)의 컬럼 정보와 일부 데이터를 바탕으로 다음 작업을 수행해주세요.

1. 데이터의 주요 특징을 1-2문장으로 간략하게 설명해주세요. (예: 시간에 따른 판매량 변화를 나타내는 시계열 데이터, 여러 제품 카테고리별 성과를 비교하는 데이터 등)
2. 이 데이터를 가장 효과적으로 시각화할 수 있는 **기본 차트 유형 하나**와, 가능하다면 **대안 차트 유형 한두 개**를 추천해주세요.
   - 추천 가능한 차트 유형: line, bar, horizontal_bar, pie, donut, scatter, histogram, area, boxplot. (이 외의 유형은 추천하지 마세요)
   - 각 차트 유형 선택 시 그 이유를 간략하게 설명해주세요.
3. 각 추천된 차트 유형을 그리기 위해 필요한 주요 컬럼(들)을 지정해주세요.
   - x_axis: x축으로 적합한 컬럼명 (날짜, 시간, 순서형 카테고리, 또는 분포를 볼 숫자형 컬럼). 단일 컬럼이어야 합니다.
   - y_axis: y축으로 적합한 컬럼명 또는 컬럼명 리스트 (측정값, 빈도수 등). 하나 이상의 컬럼일 수 있습니다.
   - group_by: 카테고리형 컬럼으로, 여러 그룹을 비교할 때 사용 (예: 막대 그래프에서 그룹별 막대, 꺾은선 그래프에서 여러 선). 단일 컬럼이거나 null.
   - value_column: 원형/도넛 차트에서 각 조각의 크기를 나타내는 수치형 컬럼. 단일 컬럼이어야 합니다.
   - 특정 역할에 적합한 컬럼이 없거나 해당 차트 유형에 필요 없다면 반드시 null 또는 빈 문자열로 표시해주세요.

결과는 반드시 다음 JSON 형식으로 반환해주세요. 다른 설명이나 추가 텍스트 없이 JSON 객체만 반환해야 합니다.
{{
  "data_characteristics": "데이터의 주요 특징 설명 (1-2 문장)",
  "primary_chart_suggestion": {{
    "chart_type": "추천 차트 유형 (예: line)",
    "reason": "차트 유형 선택 이유",
    "columns": {{
      "x_axis": "x축 컬럼명 또는 null",
      "y_axis": "y축 컬럼명 또는 [컬럼명1, 컬럼명2] 또는 null",
      "group_by": "그룹화 컬럼명 또는 null",
      "value_column": "값 컬럼명 (pie/donut 전용) 또는 null"
    }}
  }},
  "alternative_chart_suggestions": [
    {{
      "chart_type": "대안 차트 유형 1 (예: bar) 또는 null",
      "reason": "대안 차트 유형 1 선택 이유 또는 null",
      "columns": {{
        "x_axis": "x축 컬럼명 또는 null",
        "y_axis": "y축 컬럼명 또는 [컬럼명1, 컬럼명2] 또는 null",
        "group_by": "그룹화 컬럼명 또는 null",
        "value_column": "값 컬럼명 (pie/donut 전용) 또는 null"
      }}
    }}
  ]
}}

다음은 분석할 데이터의 정보입니다:

컬럼명 및 데이터 타입:
{df_summary.get('column_info', 'N/A')}

컬럼별 고유값 정보 (카테고리형 데이터 위주):
{df_summary.get('unique_counts_info', 'N/A')}

데이터 샘플 (처음 5행):
{df_summary.get('data_head', 'N/A')}

기술 통계 (수치형 컬럼):
{df_summary.get('data_describe', 'N/A')}

만약 제공된 정보로 차트 추천이 어렵다면, "error" 필드에 이유를 간단히 명시한 JSON을 반환해주세요. 예: {{"error": "데이터가 너무 적거나 분석에 부적합합니다."}}
"""
    return prompt

def parse_gemini_response(response_text: str) -> dict:
    """Gemini 응답 텍스트에서 JSON 부분을 추출하고 파싱합니다."""
    # 마크다운 코드 블록 ```json ... ``` 또는 ``` ... ``` 제거
    match = re.search(r"```(json)?\s*([\s\S]*?)\s*```", response_text)
    if match:
        cleaned_text = match.group(2)
    else:
        cleaned_text = response_text # 코드 블록이 없으면 원본 사용

    cleaned_text = cleaned_text.strip()
    
    try:
        suggestions = json.loads(cleaned_text)
        return suggestions
    except json.JSONDecodeError as e:
        logger.error(f"Gemini API 응답 JSON 파싱 오류: {e}")
        logger.error(f"파싱 시도한 텍스트 (클리닝 후): {cleaned_text}")
        logger.error(f"원본 API 응답: {response_text}") # 디버깅을 위해 원본 응답도 로깅
        # 부분적으로 유효한 JSON이 있는지 확인 시도 (예: 잘못된 후행 쉼표)
        try:
            # 후행 쉼표 제거 시도
            cleaned_text_no_trailing_comma = re.sub(r",\s*([\}\]])", r"\1", cleaned_text)
            suggestions = json.loads(cleaned_text_no_trailing_comma)
            logger.info("후행 쉼표 제거 후 파싱 성공")
            return suggestions
        except json.JSONDecodeError:
            logger.error("후행 쉼표 제거 후에도 파싱 실패")
            return {"error": "Gemini API 응답을 파싱하는 데 실패했습니다.", "raw_response_cleaned": cleaned_text, "original_response": response_text}


async def get_chart_suggestions_from_gemini(df: pd.DataFrame) -> dict:
    """
    DataFrame을 분석하여 Gemini API로부터 차트 추천을 받습니다.
    결과는 JSON 객체로 파싱하여 반환합니다.
    """
    if not GEMINI_API_KEY:
        logger.error("Gemini API 키가 설정되지 않아 차트 추천을 받을 수 없습니다.")
        return {"error": "Gemini API 키가 설정되지 않았습니다."}

    try:
        # 사용 가능한 모델 중 하나 선택 (예: gemini-1.5-flash-latest, gemini-pro)
        # gemini-1.5-flash-latest는 빠르고 비용 효율적일 수 있습니다.
        model = genai.GenerativeModel('gemini-1.5-flash-latest') 
        
        df_summary = get_data_summary_for_prompt(df)
        if "error" in df_summary: # 데이터 요약 생성 중 오류 발생 시
            logger.error(f"데이터 요약 생성 실패: {df_summary['error']}")
            return {"error": f"데이터 요약 생성에 실패했습니다: {df_summary['error']}"}

        prompt = generate_chart_suggestion_prompt(df_summary)
        
        logger.info("Gemini API에 차트 추천 요청 시작...")
        # logger.debug(f"Gemini API 요청 프롬프트:\n{prompt}") # 디버깅 시 프롬프트 내용 확인 (매우 길 수 있음)

        # generate_content_async 사용 시 주의: 이벤트 루프가 실행 중이어야 함
        response = await model.generate_content_async(prompt)
        
        logger.info("Gemini API로부터 응답 수신 완료.")
        # logger.debug(f"Gemini API 응답 (raw text): {response.text[:500]}...") # 응답이 길 수 있으므로 일부만 로깅

        suggestions = parse_gemini_response(response.text)
        
        if "error" not in suggestions: # 파싱 성공 시 추가 로깅
             logger.info(f"Gemini API 응답 파싱 성공: {json.dumps(suggestions, indent=2, ensure_ascii=False)}")

        return suggestions

    except Exception as e:
        logger.error(f"Gemini API 호출 또는 처리 중 예기치 않은 오류 발생: {e}", exc_info=True)
        return {"error": f"Gemini API 호출 중 예기치 않은 오류가 발생했습니다: {str(e)}"}

def generate_text_prompt_analysis_prompt(user_prompt: str) -> str:
    """텍스트 프롬프트 분석을 위해 Gemini API에 전송할 프롬프트를 생성합니다."""
    
    prompt = f"""
당신은 사용자의 자연어 요청을 이해하여 데이터 시각화 방법을 제안하는 AI 어시스턴트입니다.
사용자가 다음과 같은 요청을 했습니다: "{user_prompt}"

이 요청을 바탕으로 다음 정보를 JSON 형식으로 제공해주세요:

1.  `request_summary`: 사용자의 요청을 한 문장으로 명확하게 요약해주세요.
2.  `primary_chart_suggestion`:
    *   `chart_type`: 이 요청을 가장 잘 시각화할 수 있는 차트 유형을 하나 제안해주세요. (선택 가능: line, bar, horizontal_bar, pie, donut, scatter, histogram, area, map - 만약 지리적 데이터가 명시되었다면 'map'도 가능)
    *   `reason`: 해당 차트 유형을 선택한 이유를 간략히 설명해주세요.
    *   `data_structure_suggestion`:
        *   `x_axis_description`: x축에 어떤 종류의 데이터가 와야 하는지 설명해주세요. (예: "연도", "국가명", "제품 카테고리")
        *   `y_axis_description`: y축에 어떤 종류의 데이터가 와야 하는지 설명해주세요. (예: "인공위성 발사 수량", "매출액", "인구수") - 여러 개일 수 있습니다.
        *   `group_by_description` (선택적): 데이터를 그룹화할 기준이 있다면 설명해주세요. (예: "국가별로 비교", "제조사별로 구분") 없다면 null.
        *   `suggested_column_names`: 위 설명을 바탕으로, 만약 이 데이터를 테이블로 만든다면 적절할 컬럼명들을 제안해주세요. (예: ["Year", "Country", "LaunchCount"]) 이 컬럼명은 이후 목업 데이터 생성에 참고될 수 있습니다.
3.  `alternative_chart_suggestions` (선택적): 가능하다면 다른 관점에서 볼 수 있는 대안 차트 유형 한두 개를 간략히 제안해주세요. (위와 동일한 구조로)

출력은 반드시 JSON 형식이어야 하며, 다른 부가 설명 없이 JSON 객체만 반환해야 합니다.
만약 요청이 너무 모호하거나 데이터 시각화로 표현하기 어렵다면, `error` 필드에 이유를 명시한 JSON을 반환해주세요.
예: {{"error": "요청이 너무 모호하여 분석할 수 없습니다."}}

JSON 출력 예시:
{{
  "request_summary": "연도별, 국가별 인공위성 발사 수량을 보여주는 시각화를 요청함.",
  "primary_chart_suggestion": {{
    "chart_type": "bar",
    "reason": "여러 국가의 연도별 발사 수량을 비교하기에 적합합니다.",
    "data_structure_suggestion": {{
      "x_axis_description": "연도",
      "y_axis_description": "인공위성 발사 수량",
      "group_by_description": "국가명",
      "suggested_column_names": ["Year", "Country", "SatelliteLaunches"]
    }}
  }},
  "alternative_chart_suggestions": [
    {{
      "chart_type": "line",
      "reason": "시간에 따른 각 국가의 발사 수량 추세를 보기에 적합합니다.",
      "data_structure_suggestion": {{
        "x_axis_description": "연도",
        "y_axis_description": "인공위성 발사 수량",
        "group_by_description": "국가명",
        "suggested_column_names": ["Year", "Country", "SatelliteLaunches"]
      }}
    }}
  ]
}}
"""
    return prompt

async def analyze_text_prompt_with_gemini(user_prompt: str) -> dict:
    """
    사용자의 텍스트 프롬프트를 분석하여 Gemini API로부터 시각화 아이디어를 받습니다.
    결과는 JSON 객체로 파싱하여 반환합니다.
    """
    if not GEMINI_API_KEY:
        logger.error("Gemini API 키가 설정되지 않아 텍스트 프롬프트 분석을 할 수 없습니다.")
        return {"error": "Gemini API 키가 설정되지 않았습니다."}

    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt_for_gemini = generate_text_prompt_analysis_prompt(user_prompt)
        
        logger.info(f"Gemini API에 텍스트 프롬프트 분석 요청 시작: '{user_prompt[:100]}...'" ) 
        # logger.debug(f"Gemini API 요청 프롬프트 (텍스트 분석):\n{prompt_for_gemini}")

        response = await model.generate_content_async(prompt_for_gemini)
        
        logger.info("Gemini API로부터 텍스트 프롬프트 분석 응답 수신 완료.")
        # logger.debug(f"Gemini API 응답 (raw text, 텍스트 분석): {response.text[:500]}...")

        analysis_result = parse_gemini_response(response.text)
        
        if "error" not in analysis_result:
             logger.info(f"Gemini API 텍스트 프롬프트 분석 성공: {json.dumps(analysis_result, indent=2, ensure_ascii=False)}")
        else:
            logger.warning(f"Gemini API 텍스트 프롬프트 분석 실패 또는 파싱 오류: {analysis_result.get('error', '알 수 없는 오류')}, Raw: {analysis_result.get('original_response', response.text[:200])}")

        return analysis_result

    except Exception as e:
        logger.error(f"Gemini API 텍스트 프롬프트 분석 중 예기치 않은 오류 발생: {e}", exc_info=True)
        return {"error": f"Gemini API 텍스트 프롬프트 분석 중 예기치 않은 오류가 발생했습니다: {str(e)}"}
