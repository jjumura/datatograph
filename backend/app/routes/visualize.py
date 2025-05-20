from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, List, Dict, Any
from app.utils.visualize import process_excel_for_visualization, cleanup_old_charts
from app.utils.gemini_analyzer import analyze_text_prompt_with_gemini, generate_request_summary
from app.utils.autorender import render as render_chart_from_df
from app.utils.plotly_charts import render_plotly_chart  # Plotly 차트 렌더링 함수 추가
from app.schemas.visualization_schemas import PromptRequest, ChartResponse, GeminiSuggestion
import pandas as pd
import numpy as np
import os
from pathlib import Path
import logging
import base64
import re
import io
import json
import plotly.graph_objects as go

logger = logging.getLogger(__name__)
logger.info("visualize.py logger initialized and router about to be defined.")

router = APIRouter(tags=["visualize"])
logger.info("APIRouter for /visualize initialized.")

@router.post("/excel")
async def visualize_excel(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Query(None, description="시트 이름 (지정하지 않으면 모든 시트 처리)")
):
    logger.info(f"API /excel received file: {file.filename}, Sheet: {sheet_name}, Content-Type: {file.content_type}")

    file_name_lower = file.filename.lower()
    allowed_extensions = ('.xls', '.xlsx', '.csv')

    if not file_name_lower.endswith(allowed_extensions):
        logger.warning(f"Unsupported file extension: {file.filename}")
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다. (.xls, .xlsx, .csv 파일만 허용됩니다)")

    file_content = await file.read()
    logger.info(f"File content read, size: {len(file_content)} bytes for file: {file.filename}")

    cleanup_old_charts()

    try:
        results = await process_excel_for_visualization(file_content, file.filename, sheet_name, temp_dir=Path("temp_charts"))

        logger.info(f"RAW Data from process_excel_for_visualization for {file.filename}: {results}")
        logger.info(f"RAW Type of data from process_excel_for_visualization: {type(results)}")

        if isinstance(results, list) and results:
            first_item = results[0]
            if isinstance(first_item, dict):
                if "error" in first_item:
                    logger.error(f"Error explicitly returned from processing for {file.filename}: {first_item['error']}")
                    raise HTTPException(status_code=400, detail=first_item['error'])
                if "chart_base64" not in first_item:
                    logger.error(f"'chart_base64' key MISSING in the first item of results for {file.filename}. Item: {first_item}")
                    raise HTTPException(status_code=500, detail="서버 응답에 chart_base64가 없습니다.")
                    
                # 엑셀 데이터 처리 결과에서 타이틀 요약 추가
                for result in results:
                    if "sheet_name" in result and "original_file_name" in result:
                        original_title = f"{result['original_file_name']} - {result['sheet_name']}"
                        # 타이틀 요약 생성
                        try:
                            summarized_title = await generate_request_summary(original_title, max_length=15)
                            result["title"] = summarized_title
                        except Exception as title_error:
                            logger.warning(f"타이틀 요약 실패: {title_error}")
                            
                        # 타이틀 길이 제한 (최종 안전장치)
                        if "title" in result and result["title"]:
                            title = result["title"]
                            # 불완전한 타이틀 감지 및 수정 - 더 많은 패턴 추가
                            incomplete_endings = ["지역별 2022년과 2023", "지역별 2022년과", "지역별 2022년", "지역별 202"]
                            incomplete_patterns = ["2022년과 2023", "2022년과"]
                            
                            for incomplete in incomplete_endings:
                                if title == incomplete or title.startswith(incomplete):
                                    title = "지역별 매출 비교"
                                    break
                            
                            for pattern in incomplete_patterns:
                                if pattern in title:
                                    title = "지역별 매출 비교"
                                    break
                            # 불필요한 접두어 제거
                            prefixes_to_remove = ["Gemini 추천:", "추천:", "차트 제목:", "제목:", "타이틀:", "Sheet1 -", "Sheet2 -"]
                            for prefix in prefixes_to_remove:
                                if title.startswith(prefix):
                                    title = title[len(prefix):].strip()
                            # 최대 길이 제한
                            title = title[:15]
                            # 불필요한 접미사 제거
                            title = re.sub(r'[\.\,\:\;…]$', '', title)
                            result["title"] = title
                    
            else:
                logger.error(f"First item in results is not a dictionary for {file.filename}. Got: {type(first_item)}")
                raise HTTPException(status_code=500, detail="서버에서 반환된 데이터 형식이 올바르지 않습니다. (item not dict)")
        elif isinstance(results, dict) and "error" in results:
             logger.error(f"Single error object returned from processing for {file.filename}: {results['error']}")
             raise HTTPException(status_code=400, detail=results['error'])
        else:
            logger.warning(f"Results from process_excel_for_visualization is not a non-empty list with 'chart_base64' or is in unexpected format for {file.filename}. Results: {results}")
            raise HTTPException(status_code=500, detail="차트 데이터 생성에 실패했거나 반환 형식이 올바르지 않습니다.")

        return results

    except HTTPException as http_exc:
        logger.error(f"HTTPException during excel visualization for {file.filename}: {http_exc.detail}", exc_info=True)
        raise http_exc
    except Exception as e:
        logger.exception(f"Unexpected error during excel visualization for {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류 발생: {str(e)}")

@router.post("/text-prompt", response_model=List[ChartResponse])
async def visualize_text_prompt(request: PromptRequest):
    logger.info(f"API /text-prompt received prompt: {request.prompt}")
    cleanup_old_charts()

    try:
        gemini_analysis = await analyze_text_prompt_with_gemini(request.prompt)

        if not gemini_analysis or "error" in gemini_analysis:
            error_msg = gemini_analysis.get("error", "Gemini 분석 중 오류 발생") if gemini_analysis else "Gemini 분석 결과 없음"
            logger.error(f"Gemini_analysis failed for prompt '{request.prompt}': {error_msg}")
            return [ChartResponse(                sheet_name="Error",                 original_file_name=request.prompt[:100],                error=error_msg,                chart_base64=None,                chart_svg_path=None,                gemini_suggestion=GeminiSuggestion(data_characteristics=error_msg) if isinstance(gemini_analysis, dict) else None            )]

        logger.info(f"Gemini analysis successful for prompt '{request.prompt}'. Analysis: {gemini_analysis}")

        # 요약된 타이틀 생성
        chart_title = await generate_request_summary(request.prompt)
        
        primary_suggestion = gemini_analysis.get("primary_chart_suggestion")
        if not primary_suggestion or not isinstance(primary_suggestion, dict):
            logger.error("Gemini_analysis did not return a valid primary_chart_suggestion.")
            return [ChartResponse(                sheet_name="Error",                 original_file_name=request.prompt[:100],                 error="Gemini 분석 결과에 주요 차트 제안이 없습니다.",                chart_base64=None,                chart_svg_path=None            )]

        data_structure = primary_suggestion.get("data_structure_suggestion")
        if not data_structure or not isinstance(data_structure, dict):
            logger.error("Gemini_analysis did not return a valid data_structure_suggestion.")
            return [ChartResponse(                sheet_name="Error",                 original_file_name=request.prompt[:100],                 error="Gemini 분석 결과에 데이터 구조 제안이 없습니다.",                chart_base64=None,                chart_svg_path=None            )]

        suggested_cols = data_structure.get("suggested_column_names")
        chart_type = primary_suggestion.get("chart_type", "bar")
        x_desc = data_structure.get("x_axis_description", "X-Axis")
        y_desc = data_structure.get("y_axis_description", "Y-Axis")
        group_desc = data_structure.get("group_by_description")

        mock_df = pd.DataFrame()
        num_rows = 10
        
        x_col_name = suggested_cols[0] if suggested_cols and len(suggested_cols) > 0 else "CategoryX"
        y_col_name = suggested_cols[1] if suggested_cols and len(suggested_cols) > 1 else "ValueY1"
        y_cols_for_chart = [y_col_name]
        group_col_name = None

        if suggested_cols and len(suggested_cols) > 0:
            mock_df[x_col_name] = [f"{x_desc}_{i+1}" for i in range(num_rows)]
            if "year" in x_desc.lower() or "연도" in x_desc.lower():
                 mock_df[x_col_name] = np.arange(2015, 2015 + num_rows)
            
            mock_df[y_col_name] = np.random.randint(50, 200, size=num_rows)

            if len(suggested_cols) > 2 and group_desc:
                group_col_name = suggested_cols[2]
                mock_df[group_col_name] = np.random.choice(["GroupA", "GroupB", "GroupC"], size=num_rows)
            elif len(suggested_cols) > 2 :
                y2_col_name = suggested_cols[2]
                mock_df[y2_col_name] = np.random.randint(30, 150, size=num_rows)
                y_cols_for_chart.append(y2_col_name)
        else:
            mock_df[x_col_name] = [f"Cat_{i}" for i in range(num_rows)]
            mock_df[y_col_name] = np.random.rand(num_rows) * 100
        
        logger.info(f"Generated mock DataFrame for prompt '{request.prompt}':\n{mock_df.head()}")

        render_context = {
            "chart_type": chart_type,
            "x_column": x_col_name,
            "y_columns": y_cols_for_chart,
            "title": chart_title,
            "group_by_column": group_col_name
        }

        # 차트 렌더링 직전에 타이틀 길이 재확인 및 필터링 (최종 안전장치)
        if "title" in render_context and render_context["title"]:
            title = render_context["title"]
            
            # 불완전한 타이틀 감지 및 수정 - 더 많은 패턴 추가
            incomplete_endings = ["지역별 2022년과 2023", "지역별 2022년과", "지역별 2022년", "지역별 202"]
            incomplete_patterns = ["2022년과 2023", "2022년과"]
            
            for incomplete in incomplete_endings:
                if title == incomplete or title.startswith(incomplete):
                    title = "지역별 매출 비교"
                    break
            
            for pattern in incomplete_patterns:
                if pattern in title:
                    title = "지역별 매출 비교"
                    break
            
            # 불필요한 접두어 제거
            prefixes_to_remove = ["Gemini 추천:", "추천:", "차트 제목:", "제목:", "타이틀:", "Sheet1 -", "Sheet2 -"]
            for prefix in prefixes_to_remove:
                if title.startswith(prefix):
                    title = title[len(prefix):].strip()
            
            # 최대 길이 제한 (15자)
            if len(title) > 15:
                title = title[:15]
                
            # 불필요한 접미사 제거
            title = re.sub(r'[\.\,\:\;…]$', '', title)
            
            render_context["title"] = title

        chart_result = await render_chart_from_df(mock_df, render_context, temp_dir=Path("temp_charts"))
        
        if not chart_result:
            logger.error(f"차트 렌더링 결과가 없음 - 프롬프트: '{request.prompt}'")
            return [ChartResponse(
                sheet_name="Error", 
                original_file_name=request.prompt[:100], 
                error="차트 이미지 생성에 실패했습니다.",
                chart_base64=None,
                chart_svg_path=None
            )]
            
        png_path = chart_result.get("png_path")
        svg_path = chart_result.get("svg_path")
        
        if not png_path or not os.path.exists(png_path):
            logger.error(f"PNG 파일을 찾을 수 없음 - 프롬프트: '{request.prompt}'. Path: {png_path}")
            return [ChartResponse(
                sheet_name="Error", 
                original_file_name=request.prompt[:100], 
                error="차트 이미지 생성에 실패했습니다.",
                chart_base64=None,
                chart_svg_path=None
            )]

        with open(png_path, "rb") as image_file:
            chart_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        
        # SVG 파일 경로 처리 (파일명만 추출)
        svg_path_name = Path(svg_path).name if svg_path else None
        
        response_data = ChartResponse(
            sheet_name=f"Prompt: {request.prompt[:50]}...",
            original_file_name=request.prompt[:100],
            chart_base64=chart_base64,
            chart_svg_path=svg_path_name,
            columns=mock_df.columns.tolist(),
            numeric_columns=mock_df.select_dtypes(include=np.number).columns.tolist(),
            rows_count=len(mock_df),
            gemini_suggestion=GeminiSuggestion(**gemini_analysis)
        )
        return [response_data]

    except HTTPException as http_exc:
        logger.error(f"HTTPException during text prompt visualization for '{request.prompt}': {http_exc.detail}", exc_info=True)
        return [ChartResponse(
            sheet_name="Error", 
            original_file_name=request.prompt[:100], 
            error=http_exc.detail,
            chart_base64=None,
            chart_svg_path=None
        )]
    except Exception as e:
        logger.exception(f"Unexpected error during text prompt visualization for '{request.prompt}': {str(e)}")
        return [ChartResponse(
            sheet_name="Error", 
            original_file_name=request.prompt[:100], 
            error=f"서버 내부 오류: {str(e)}",
            chart_base64=None,
            chart_svg_path=None
        )]

@router.get("/download/{filename}")
async def download_file(filename: str):
    logger.info(f"Download request for file: {filename}")
    file_path = Path("temp_charts") / filename

    if not file_path.exists():
        logger.warning(f"File not found: {filename}")
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")

    # SVG/PNG 구분
    file_ext = file_path.suffix.lower()
    if file_ext == ".svg":
        media_type = "image/svg+xml"
    elif file_ext == ".png":
        media_type = "image/png"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        str(file_path), 
        media_type=media_type,
        filename=filename
    )

@router.get("/chart/{filename}")
async def get_chart(filename: str):
    logger.info(f"Request for chart: {filename}")
    file_path = Path("temp_charts") / filename

    if not file_path.exists():
        logger.warning(f"Chart file not found: {filename}")
        raise HTTPException(status_code=404, detail="차트 이미지를 찾을 수 없습니다")

    return FileResponse(str(file_path), media_type="image/png")

@router.post("/plotly/excel")
async def visualize_excel_plotly(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Query(None, description="시트 이름 (지정하지 않으면 모든 시트 처리)")
):
    logger.info(f"API /plotly/excel received file: {file.filename}, Sheet: {sheet_name}")

    file_name_lower = file.filename.lower()
    allowed_extensions = ('.xls', '.xlsx', '.csv')

    if not file_name_lower.endswith(allowed_extensions):
        logger.warning(f"Unsupported file extension: {file.filename}")
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다. (.xls, .xlsx, .csv 파일만 허용됩니다)")

    file_content = await file.read()
    logger.info(f"File content read, size: {len(file_content)} bytes for file: {file.filename}")

    try:
        # 엑셀/CSV 파일 처리
        if file_name_lower.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content))
            sheets = {'Sheet1': df}
        else:
            # 엑셀 파일 처리
            excel_file = pd.ExcelFile(io.BytesIO(file_content))
            
            if sheet_name:
                if sheet_name not in excel_file.sheet_names:
                    raise HTTPException(status_code=400, detail=f"시트 '{sheet_name}'를 찾을 수 없습니다.")
                sheets = {sheet_name: excel_file.parse(sheet_name)}
            else:
                sheets = {name: excel_file.parse(name) for name in excel_file.sheet_names}
        
        results = []
        
        for sheet_name, df in sheets.items():
            if df.empty:
                continue
                
            # 숫자형 컬럼 추출
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            
            if len(numeric_columns) == 0:
                logger.warning(f"No numeric columns in sheet {sheet_name}")
                continue
                
            # 차트 메타데이터 준비
            x_column = df.columns[0]  # 기본적으로 첫 번째 컬럼을 X축으로 사용
            y_columns = numeric_columns[:3]  # 최대 3개의 숫자형 컬럼을 Y축으로 사용
            
            # 시각화에 가장 적합한 차트 유형 결정
            chart_type = 'bar'  # 기본값
            
            # 데이터 특성에 따라 차트 유형 결정
            if len(df) > 10 and x_column in df.columns and pd.api.types.is_numeric_dtype(df[x_column]):
                chart_type = 'line'  # 많은 데이터 포인트가 있고 X축이 숫자인 경우 선 차트
            
            # 상관관계 히트맵이 유용한지 확인
            if len(numeric_columns) >= 5:
                # 많은 숫자형 열이 있는 경우 히트맵을 보조 차트로 추가
                heatmap_context = {
                    'chart_type': 'heatmap',
                    'title': f"{file.filename} - {sheet_name} 상관관계 히트맵"
                }
                heatmap_result = render_plotly_chart(df, heatmap_context)
                results.append({
                    'sheet_name': f"{sheet_name} (상관관계)",
                    'original_file_name': file.filename,
                    'chart_type': 'heatmap',
                    'chart_json': heatmap_result['chart_json'],
                    'd3_data': heatmap_result.get('d3_data', '{}'),
                    'columns': df.columns.tolist(),
                    'numeric_columns': numeric_columns,
                    'rows_count': len(df)
                })
            
            # 기본 차트 컨텍스트 생성
            chart_context = {
                'chart_type': chart_type,
                'x_column': x_column,
                'y_columns': y_columns,
                'title': f"{file.filename} - {sheet_name}"
            }
            
            # Plotly 차트 렌더링
            chart_result = render_plotly_chart(df, chart_context)
            
            # 오류 발생 확인
            if 'error' in chart_result:
                logger.error(f"차트 렌더링 오류: {chart_result['error']}")
                results.append({
                    'sheet_name': sheet_name,
                    'original_file_name': file.filename,
                    'chart_type': chart_type,
                    'error': chart_result['error'],
                    'columns': df.columns.tolist(),
                    'numeric_columns': numeric_columns,
                    'rows_count': len(df)
                })
                continue
                
            # 결과에 차트 JSON 추가
            chart_json = None
            if 'chart_json' in chart_result:
                chart_json = chart_result['chart_json']
            elif 'data' in chart_result:
                chart_json = chart_result['data']
                logger.warning("chart_result에 'chart_json' 대신 'data' 키가 사용되었습니다.")
            else:
                logger.error("차트 결과에 chart_json 또는 data 키가 없습니다")
                chart_json = "{}"
            
            results.append({
                'sheet_name': sheet_name,
                'original_file_name': file.filename,
                'chart_type': chart_type,
                'chart_json': chart_json,
                'd3_data': chart_result.get('d3_data', '{}'),
                'columns': df.columns.tolist(),
                'numeric_columns': numeric_columns,
                'rows_count': len(df)
            })
        
        if not results:
            raise HTTPException(status_code=400, detail="시각화할 데이터를 찾을 수 없습니다.")
            
        return results
    
    except pd.errors.EmptyDataError:
        logger.error(f"Empty data file: {file.filename}")
        raise HTTPException(status_code=400, detail="파일에 데이터가 없습니다.")
    except pd.errors.ParserError:
        logger.error(f"Parser error for file: {file.filename}")
        raise HTTPException(status_code=400, detail="파일 형식이 올바르지 않아 파싱할 수 없습니다.")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Unexpected error during plotly excel visualization for {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류 발생: {str(e)}")

@router.post("/update-chart-colors")
async def update_chart_colors(
    request: Dict[str, Any]
):
    """
    차트 색상을 업데이트하고 새로운 차트 JSON 생성
    
    Args:
        request: 색상 업데이트 요청 데이터
            - data_frame: 직렬화된 데이터프레임 (JSON 문자열)
            - chart_context: 차트 컨텍스트 정보
            - colors: 새로운 색상 목록
    """
    try:
        # 요청 데이터 추출
        data_json = request.get('data_frame')
        chart_context = request.get('chart_context', {})
        colors = request.get('colors', [])
        
        if not data_json:
            raise HTTPException(status_code=400, detail="데이터프레임이 제공되지 않았습니다")
            
        # JSON으로 직렬화된 데이터프레임 파싱
        try:
            df = pd.read_json(data_json)
        except Exception as e:
            logger.error(f"데이터프레임 파싱 오류: {e}")
            raise HTTPException(status_code=400, detail=f"데이터프레임을 파싱할 수 없습니다: {str(e)}")
            
        # 차트 컨텍스트에 색상 추가
        chart_context['colors'] = colors
        
        # 새로운 차트 렌더링
        result = render_plotly_chart(df, chart_context)
        
        # 에러 확인
        if 'error' in result:
            logger.error(f"차트 색상 업데이트 중 오류: {result['error']}")
            return {"error": result['error']}
        
        # chart_json 키 확인
        chart_json = None
        if 'chart_json' in result:
            chart_json = result['chart_json']
        elif 'data' in result:
            chart_json = result['data']
            logger.warning("result에 'chart_json' 대신 'data' 키가 사용되었습니다.")
        else:
            logger.error("차트 결과에 chart_json 또는 data 키가 없습니다")
            return {"error": "차트 JSON을 생성할 수 없습니다."}
        
        return {
            'chart_json': chart_json,
            'd3_data': result.get('d3_data', '{}'),
            'chart_type': chart_context.get('chart_type', 'bar')
        }
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"차트 색상 업데이트 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류 발생: {str(e)}")

@router.post("/d3-export")
async def export_to_d3(
    request: Dict[str, Any]
):
    """
    Plotly 차트 데이터를 D3.js와 호환되는 형식으로 변환
    
    Args:
        request: 변환 요청 데이터
            - chart_json: Plotly 차트 JSON
            - chart_type: 차트 유형
    """
    try:
        chart_json = request.get('chart_json')
        
        if not chart_json:
            raise HTTPException(status_code=400, detail="차트 JSON이 제공되지 않았습니다")
            
        # Plotly 차트 파싱
        try:
            chart_data = json.loads(chart_json)
            
            # D3.js 호환 데이터 생성
            d3_data = {
                'type': request.get('chart_type', 'bar'),
                'layout': chart_data.get('layout', {}),
                'data': chart_data.get('data', [])
            }
            
            return {
                'd3_data': d3_data
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"차트 JSON 파싱 오류: {e}")
            raise HTTPException(status_code=400, detail="차트 JSON을 파싱할 수 없습니다")
            
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"D3.js 내보내기 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류 발생: {str(e)}")

@router.get("/download-png")
async def download_png(chart_json: str = Query(...)):
    """
    Plotly 차트를 PNG 이미지로 변환하여 다운로드
    
    Args:
        chart_json: Plotly 차트 JSON (URL 쿼리 파라미터)
    """
    try:
        import plotly.io as pio
        from io import BytesIO
        from fastapi.responses import StreamingResponse
        
        # 차트 JSON 파싱
        try:
            chart_data = json.loads(chart_json)
            fig = go.Figure(chart_data)
            
            # PNG로 변환
            img_bytes = BytesIO()
            fig.write_image(img_bytes, format='png', width=1200, height=800)
            img_bytes.seek(0)
            
            # 스트리밍 응답으로 반환
            return StreamingResponse(
                img_bytes, 
                media_type='image/png',
                headers={'Content-Disposition': 'attachment; filename="chart.png"'}
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"차트 JSON 파싱 오류: {e}")
            raise HTTPException(status_code=400, detail="차트 JSON을 파싱할 수 없습니다")
            
    except ImportError as e:
        logger.error(f"필요한 라이브러리가 설치되지 않았습니다: {e}")
        raise HTTPException(status_code=500, detail="PNG 내보내기에 필요한 라이브러리가 설치되지 않았습니다")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"PNG 다운로드 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류 발생: {str(e)}")