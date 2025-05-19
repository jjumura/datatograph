import pandas as pd
import matplotlib.pyplot as plt
import io
from typing import List, Dict, Any, Optional, Tuple
import base64
from pathlib import Path
import uuid
import os
import shutil
from datetime import datetime, timedelta
import logging
from . import autorender
from app.utils.gemini_analyzer import get_chart_suggestions_from_gemini
import asyncio

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_temp_dir():
    """임시 디렉토리가 존재하는지 확인하고 없으면 생성합니다."""
    temp_dir = Path("temp_charts")
    temp_dir.mkdir(exist_ok=True)
    return temp_dir

def generate_chart(df: pd.DataFrame, chart_type: str = 'line', 
                  x_column: Optional[str] = None, 
                  y_columns: Optional[List[str]] = None,
                  title: str = '',
                  figsize: Tuple[int, int] = (10, 6)) -> str:
    """
    데이터프레임을 기반으로 차트를 생성하고 PNG 파일로 저장합니다.
    
    Args:
        df: 차트를 생성할 데이터프레임
        chart_type: 차트 유형 ('line', 'bar', 'scatter', 'pie')
        x_column: x축에 사용할 컬럼명
        y_columns: y축에 사용할 컬럼명 리스트
        title: 차트 제목
        figsize: 차트 크기 (가로, 세로)
        
    Returns:
        str: 생성된 이미지 파일의 경로
    """
    try:
        # 임시 디렉토리 확인
        img_dir = ensure_temp_dir()
        
        # 고유한 파일명 생성
        filename = f"chart_{uuid.uuid4().hex[:8]}.png"
        filepath = img_dir / filename
        
        plt.figure(figsize=figsize)
        
        # x축 컬럼이 지정되지 않은 경우 인덱스 사용
        if x_column is None:
            x_data = df.index
        else:
            x_data = df[x_column]
        
        # y축 컬럼이 지정되지 않은 경우 수치형 컬럼 모두 사용
        if y_columns is None:
            y_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            if x_column in y_columns:
                y_columns.remove(x_column)
        
        if chart_type == 'line':
            for col in y_columns:
                plt.plot(x_data, df[col], label=col, marker='o')
            plt.legend()
            
        elif chart_type == 'bar':
            if len(y_columns) == 1:
                plt.bar(x_data, df[y_columns[0]])
            else:
                df[y_columns].plot(kind='bar', x=x_data)
            plt.legend()
            
        elif chart_type == 'scatter':
            if len(y_columns) >= 2:
                plt.scatter(df[y_columns[0]], df[y_columns[1]])
                plt.xlabel(y_columns[0])
                plt.ylabel(y_columns[1])
            else:
                plt.scatter(x_data, df[y_columns[0]])
                
        elif chart_type == 'pie':
            if len(y_columns) == 1:
                plt.pie(df[y_columns[0]], labels=x_data, autopct='%1.1f%%')
        
        plt.title(title)
        plt.grid(True)
        plt.tight_layout()
        
        # 차트를 이미지 파일로 저장
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
        
    except Exception as e:
        logger.error(f"차트 생성 중 오류 발생: {str(e)}")
        plt.close()  # 에러 발생 시에도 figure를 닫아줌
        raise

def cleanup_old_charts(max_age_hours: int = 1):
    """
    오래된 차트 이미지 파일들을 정리합니다.
    
    Args:
        max_age_hours: 보관할 최대 시간 (시간 단위)
    """
    try:
        img_dir = Path("temp_charts")
        if not img_dir.exists():
            return
            
        current_time = datetime.now()
        max_age = timedelta(hours=max_age_hours)
        
        # 디렉토리 내의 모든 PNG 파일 검사
        for file in img_dir.glob("*.png"):
            try:
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                age = current_time - file_time
                
                if age > max_age:
                    file.unlink()
                    logger.info(f"오래된 차트 파일 삭제: {file}")
                    
            except Exception as e:
                logger.error(f"파일 {file} 처리 중 오류 발생: {e}")
                
        # 빈 디렉토리 정리 로직을 주석 처리하거나 삭제합니다.
        # if not any(img_dir.iterdir()):
        #     img_dir.rmdir()
        #     logger.info("빈 temp_charts 디렉토리 삭제")
            
    except Exception as e:
        logger.error(f"차트 정리 중 오류 발생: {e}")

async def process_excel_for_visualization(file_content: bytes, 
                                 file_name: str,
                                 sheet_name: Optional[str] = None,
                                 temp_dir: Path = Path("temp_charts")) -> List[Dict[str, Any]]:
    """
    Excel 파일을 읽어서 시각화에 적합한 형태로 처리하고, Gemini API로 차트 추천을 받습니다.
    
    Args:
        file_content: Excel 파일 내용
        file_name: 원본 파일 이름
        sheet_name: 처리할 시트 이름 (지정하지 않으면 모든 시트 또는 첫 번째 시트)
        
    Returns:
        List[Dict[str, Any]]: 처리된 데이터와 생성된 차트 정보
    """
    all_sheets_results = []
    excel_data = io.BytesIO(file_content)
    
    try:
        if sheet_name:
            # 특정 시트만 처리
            try:
                df = pd.read_excel(excel_data, sheet_name=sheet_name)
            except ValueError: # 시트가 존재하지 않는 경우 등
                 logger.error(f"'{sheet_name}' 시트를 찾을 수 없거나 읽을 수 없습니다.")
                 return [{"error": f"'{sheet_name}' 시트를 찾을 수 없거나 읽을 수 없습니다."}]
            
            if df.empty:
                logger.info(f"'{sheet_name}' 시트가 비어있습니다.")
                all_sheets_results.append({
                    "sheet_name": sheet_name,
                    "original_file_name": file_name,
                    "error": "시트가 비어있습니다.",
                    "chart_base64": None,
                    "gemini_suggestion": None
                })
            else:
                logger.info(f"'{sheet_name}' 시트에 대해 Gemini API로 차트 추천 분석 시작...")
                gemini_suggestions = await get_chart_suggestions_from_gemini(df)
                logger.info(f"Gemini API 추천 결과 for '{sheet_name}': {gemini_suggestions}")
                
                # 여기서 gemini_suggestions를 사용하여 autorender.render의 context를 동적으로 구성
                # 우선은 기존 로직대로 차트 생성하고, gemini 결과는 로그로만 확인 및 결과에 포함
                sheet_results = await process_single_sheet(df, sheet_name, file_name, gemini_suggestions, temp_dir)
                all_sheets_results.extend(sheet_results)

        else:
            # 모든 시트 처리 (또는 첫 번째 시트만 Gemini 분석 - 선택 사항)
            xls = pd.ExcelFile(excel_data)
            sheet_names_in_file = xls.sheet_names
            
            if not sheet_names_in_file:
                return [{"error": "Excel 파일에 시트가 없습니다."}]

            # 예시: 첫 번째 시트에 대해서만 Gemini 분석 실행
            # 또는 모든 시트에 대해 실행하도록 로직 변경 가능
            first_sheet_to_analyze = sheet_names_in_file[0]
            df_first_sheet = pd.read_excel(xls, sheet_name=first_sheet_to_analyze)

            gemini_overall_suggestions = None
            if not df_first_sheet.empty:
                logger.info(f"파일 '{file_name}'의 첫 번째 시트 '{first_sheet_to_analyze}'에 대해 Gemini API 분석 시작...")
                gemini_overall_suggestions = await get_chart_suggestions_from_gemini(df_first_sheet)
                logger.info(f"Gemini API 전체 추천 결과 (첫 시트 기반) for '{file_name}': {gemini_overall_suggestions}")
            else:
                logger.info(f"파일 '{file_name}'의 첫 번째 시트 '{first_sheet_to_analyze}'가 비어있어 Gemini 분석을 건너뛰었습니다.")


            for s_name in sheet_names_in_file:
                df_current_sheet = pd.read_excel(xls, sheet_name=s_name)
                if df_current_sheet.empty:
                    logger.info(f"'{s_name}' 시트가 비어있습니다.")
                    all_sheets_results.append({
                        "sheet_name": s_name,
                        "original_file_name": file_name,
                        "error": "시트가 비어있습니다.",
                        "chart_base64": None,
                        "gemini_suggestion": None # 또는 gemini_overall_suggestions를 여기에 할당할 수도 있음
                    })
                    continue
                
                # 각 시트별로 Gemini 분석을 다시 호출할 수도 있고, 전체 분석 결과를 활용할 수도 있음
                # 현재는 첫 시트 분석 결과(gemini_overall_suggestions)를 각 시트에 전달하거나,
                # 각 시트별로 다시 호출하려면 여기서 await get_chart_suggestions_from_gemini(df_current_sheet) 필요
                current_sheet_gemini_suggestion = gemini_overall_suggestions # 일단 첫 시트 분석 결과를 재활용
                # 만약 시트별로 분석하고 싶다면:
                # current_sheet_gemini_suggestion = await get_chart_suggestions_from_gemini(df_current_sheet)
                # logger.info(f"Gemini API 추천 결과 for sheet '{s_name}': {current_sheet_gemini_suggestion}")

                sheet_results = await process_single_sheet(df_current_sheet, s_name, file_name, current_sheet_gemini_suggestion, temp_dir)
                all_sheets_results.extend(sheet_results)
            
        return all_sheets_results if all_sheets_results else [{
            "original_file_name": file_name,
            "error": "처리 가능한 데이터가 있는 시트가 없습니다."
        }]
            
    except Exception as e:
        logger.error(f"Excel 파일 '{file_name}' 처리 중 오류 발생: {e}", exc_info=True)
        return [{
            "original_file_name": file_name,
            "error": f"데이터 처리 중 오류 발생: {str(e)}"
        }]

async def process_single_sheet(df: pd.DataFrame, 
                             sheet_name: str, 
                             file_name: str, 
                             gemini_suggestion: Optional[Dict] = None,
                             temp_dir: Path = Path("temp_charts")) -> List[Dict[str, Any]]:
    """단일 시트를 처리하고 차트를 생성합니다. Gemini 추천을 받을 수 있습니다."""
    try:
        # 수치형 컬럼 찾기 - 기존 로직 유지 또는 Gemini 추천 활용
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        # Gemini 추천이 있고, 유효한 컬럼 정보가 있다면 그것을 사용 시도
        chart_type_to_render = "line" # 기본값
        x_col_to_render = df.columns[0] if len(df.columns) > 0 else None
        y_cols_to_render = numeric_cols[:3] if numeric_cols else []
        title_to_render = f"{sheet_name} ({file_name}) 데이터 차트"

        if gemini_suggestion and not gemini_suggestion.get("error") and gemini_suggestion.get("primary_chart_suggestion"):
            primary_suggestion = gemini_suggestion["primary_chart_suggestion"]
            suggested_chart_type = primary_suggestion.get("chart_type")
            suggested_cols = primary_suggestion.get("columns")

            if suggested_chart_type and suggested_cols:
                # 여기서 추천된 컬럼들이 df에 실제로 존재하는지, 타입이 맞는지 등 추가 검증 필요
                # 간단히 사용 가능한 경우만 적용
                raw_x = suggested_cols.get("x_axis")
                raw_y = suggested_cols.get("y_axis")

                # 컬럼명 유효성 검사
                valid_x = raw_x if raw_x and raw_x in df.columns else None
                valid_y = []
                if isinstance(raw_y, list):
                    valid_y = [col for col in raw_y if col in df.columns]
                elif isinstance(raw_y, str) and raw_y in df.columns: # y_axis가 단일 문자열일 경우
                    valid_y = [raw_y]
                
                if suggested_chart_type == "pie" or suggested_chart_type == "donut":
                    raw_value_col = suggested_cols.get("value_column")
                    valid_value_col = raw_value_col if raw_value_col and raw_value_col in df.columns else None
                    if valid_x and valid_value_col: # 파이/도넛은 x(레이블), value(값) 필요
                        chart_type_to_render = suggested_chart_type
                        x_col_to_render = valid_x
                        y_cols_to_render = [valid_value_col] # 파이/도넛은 값 컬럼 하나를 y로 취급
                        title_to_render = f"Gemini 추천: {sheet_name} - {primary_suggestion.get('reason', suggested_chart_type)}"
                        logger.info(f"Gemini 추천 적용 (pie/donut): type={chart_type_to_render}, x='{x_col_to_render}', y='{y_cols_to_render}'")
                elif valid_x and valid_y:
                    chart_type_to_render = suggested_chart_type
                    x_col_to_render = valid_x
                    y_cols_to_render = valid_y
                    title_to_render = f"Gemini 추천: {sheet_name} - {primary_suggestion.get('reason', suggested_chart_type)}"
                    logger.info(f"Gemini 추천 적용: type={chart_type_to_render}, x='{x_col_to_render}', y='{y_cols_to_render}'")
                else:
                    logger.warning(f"Gemini 추천 컬럼 ('{raw_x}', '{raw_y}')이 유효하지 않아 기본 차트 생성.")
            else:
                logger.info("Gemini 추천에 차트 유형 또는 컬럼 정보가 충분하지 않아 기본 차트 생성.")
        elif not numeric_cols: # Gemini 추천도 없고, 수치형 데이터도 없으면
             return [{
                "sheet_name": sheet_name,
                "original_file_name": file_name,
                "error": "차트 생성을 위한 수치형 데이터를 찾을 수 없고 Gemini 추천도 유효하지 않습니다.",
                "chart_base64": None,
                "gemini_suggestion": gemini_suggestion
            }]


        if not x_col_to_render or not y_cols_to_render:
            logger.warning(f"'{sheet_name}' 시트에서 차트 생성을 위한 x 또는 y 컬럼을 결정할 수 없습니다. (x='{x_col_to_render}', y='{y_cols_to_render}')")
            return [{
                "sheet_name": sheet_name,
                "original_file_name": file_name,
                "error": "차트 생성을 위한 x 또는 y축 데이터를 결정할 수 없습니다.",
                "chart_base64": None,
                "gemini_suggestion": gemini_suggestion
            }]
            
        chart_context = {
            "chart_type": chart_type_to_render,
            "x_column": x_col_to_render,
            "y_columns": y_cols_to_render,
            "title": title_to_render
        }
        
        # 임시 디렉토리 확인
        ensure_temp_dir()
        
        # autorender를 사용하여 차트 생성
        chart_path = await autorender.render(df, chart_context, temp_dir=temp_dir)
        
        chart_base64 = None
        if chart_path:
            try:
                with open(chart_path, "rb") as image_file:
                    chart_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                # Base64 인코딩 후 원본 임시 파일 삭제 (선택 사항)
                # Path(chart_path).unlink(missing_ok=True) 
            except Exception as e:
                logger.error(f"차트 파일을 Base64로 인코딩 중 오류 발생: {e}")
                return [{
                    "sheet_name": sheet_name,
                    "original_file_name": file_name,
                    "error": f"차트 인코딩 오류: {str(e)}",
                    "chart_base64": None,
                    "gemini_suggestion": gemini_suggestion
                }]
        
        if not chart_base64:
             return [{
                "sheet_name": sheet_name,
                "original_file_name": file_name,
                "error": "차트 생성 또는 인코딩에 실패했습니다.",
                "chart_base64": None,
                "gemini_suggestion": gemini_suggestion
            }]

        return [{
            "sheet_name": sheet_name,
            "original_file_name": file_name,
            "chart_base64": chart_base64, # Base64 인코딩된 차트 데이터
            "columns": df.columns.tolist(),
            "numeric_columns": numeric_cols,
            "rows_count": len(df),
            "gemini_suggestion": gemini_suggestion
        }]
        
    except Exception as e:
        logger.error(f"시트 '{sheet_name}' 처리 중 오류 발생: {e}", exc_info=True)
        return [{
            "sheet_name": sheet_name,
            "original_file_name": file_name,
            "error": f"차트 생성 중 오류 발생: {str(e)}",
            "chart_base64": None,
            "gemini_suggestion": gemini_suggestion
        }] 