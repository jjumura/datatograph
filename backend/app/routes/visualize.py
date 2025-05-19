from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
from app.utils.visualize import process_excel_for_visualization, cleanup_old_charts
from app.utils.gemini_analyzer import analyze_text_prompt_with_gemini
from app.utils.autorender import render as render_chart_from_df
from app.schemas.visualization_schemas import PromptRequest, ChartResponse, GeminiSuggestion
import pandas as pd
import numpy as np
import os
from pathlib import Path
import logging
import base64

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
            return [ChartResponse(
                sheet_name="Error", 
                original_file_name=request.prompt[:100],
                error=error_msg,
                gemini_suggestion=GeminiSuggestion(data_characteristics=error_msg) if isinstance(gemini_analysis, dict) else None
            )]

        logger.info(f"Gemini analysis successful for prompt '{request.prompt}'. Analysis: {gemini_analysis}")

        primary_suggestion = gemini_analysis.get("primary_chart_suggestion")
        if not primary_suggestion or not isinstance(primary_suggestion, dict):
            logger.error("Gemini_analysis did not return a valid primary_chart_suggestion.")
            return [ChartResponse(sheet_name="Error", original_file_name=request.prompt[:100], error="Gemini 분석 결과에 주요 차트 제안이 없습니다.")]

        data_structure = primary_suggestion.get("data_structure_suggestion")
        if not data_structure or not isinstance(data_structure, dict):
            logger.error("Gemini_analysis did not return a valid data_structure_suggestion.")
            return [ChartResponse(sheet_name="Error", original_file_name=request.prompt[:100], error="Gemini 분석 결과에 데이터 구조 제안이 없습니다.")]

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

        chart_title = gemini_analysis.get("request_summary", f"Chart for: {request.prompt[:30]}...")

        render_context = {
            "chart_type": chart_type,
            "x_column": x_col_name,
            "y_columns": y_cols_for_chart,
            "title": chart_title,
            "group_by_column": group_col_name
        }

        chart_file_path_str = await render_chart_from_df(mock_df, render_context, temp_dir=Path("temp_charts"))
        
        if not chart_file_path_str or not os.path.exists(chart_file_path_str):
            logger.error(f"Chart rendering failed or file not found for prompt '{request.prompt}'. Path: {chart_file_path_str}")
            return [ChartResponse(sheet_name="Error", original_file_name=request.prompt[:100], error="차트 이미지 생성에 실패했습니다.")]

        with open(chart_file_path_str, "rb") as image_file:
            chart_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        
        response_data = ChartResponse(
            sheet_name=f"Prompt: {request.prompt[:50]}...",
            original_file_name=request.prompt[:100],
            chart_base64=chart_base64,
            columns=mock_df.columns.tolist(),
            numeric_columns=mock_df.select_dtypes(include=np.number).columns.tolist(),
            rows_count=len(mock_df),
            gemini_suggestion=GeminiSuggestion(**gemini_analysis)
        )
        return [response_data]

    except HTTPException as http_exc:
        logger.error(f"HTTPException during text prompt visualization for '{request.prompt}': {http_exc.detail}", exc_info=True)
        return [ChartResponse(sheet_name="Error", original_file_name=request.prompt[:100], error=http_exc.detail)]
    except Exception as e:
        logger.exception(f"Unexpected error during text prompt visualization for '{request.prompt}': {str(e)}")
        return [ChartResponse(sheet_name="Error", original_file_name=request.prompt[:100], error=f"서버 내부 오류: {str(e)}")]

@router.get("/chart/{filename}")
async def get_chart(filename: str):
    logger.info(f"Request for chart: {filename}")
    file_path = Path("temp_charts") / filename

    if not file_path.exists():
        logger.warning(f"Chart file not found: {filename}")
        raise HTTPException(status_code=404, detail="차트 이미지를 찾을 수 없습니다")

    return FileResponse(str(file_path), media_type="image/png")