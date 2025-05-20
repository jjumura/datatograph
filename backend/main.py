from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import json
import pandas as pd
import io
import traceback

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 프론트엔드 도메인으로 제한해야 함
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# 엑셀 파일 분석 엔드포인트
@app.post("/excel/analyze")
async def analyze_excel(file: UploadFile = File(...), sheet_name: Optional[str] = Form("0")):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name)
        
        # 데이터프레임 분석
        columns = df.columns.tolist()
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        
        return {
            "sheet_name": sheet_name,
            "original_file_name": file.filename,
            "columns": columns,
            "numeric_columns": numeric_columns,
            "rows_count": len(df)
        }
    except Exception as e:
        print(f"Error analyzing Excel: {str(e)}")
        traceback.print_exc()
        return {"error": f"Excel 파일 분석 중 오류 발생: {str(e)}"}

# 엑셀 파일 읽기 엔드포인트
@app.post("/excel/read")
async def read_excel(file: UploadFile = File(...), sheet_name: Optional[str] = Form("0")):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name)
        
        # 데이터프레임을 JSON으로 변환
        data = df.values.tolist()
        columns = df.columns.tolist()
        
        return {
            "sheet_name": sheet_name,
            "original_file_name": file.filename,
            "columns": columns,
            "data": data
        }
    except Exception as e:
        print(f"Error reading Excel: {str(e)}")
        traceback.print_exc()
        return {"error": f"Excel 파일 읽기 중 오류 발생: {str(e)}"}

# 엑셀 테이블 분할 엔드포인트
@app.post("/excel/split-tables")
async def split_excel_tables(file: UploadFile = File(...), sheet_name: Optional[str] = Form("0")):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name)
        
        # 간단한 예시: 하나의 테이블만 반환
        data = df.values.tolist()
        
        return {
            "sheet_name": sheet_name,
            "original_file_name": file.filename,
            "tables": [
                {
                    "table_id": 1,
                    "columns": df.columns.tolist(),
                    "rows": data
                }
            ]
        }
    except Exception as e:
        print(f"Error splitting Excel tables: {str(e)}")
        traceback.print_exc()
        return {"error": f"Excel 테이블 분할 중 오류 발생: {str(e)}"}

# Plotly 시각화 엔드포인트
@app.post("/api/visualize/plotly/excel")
async def visualize_excel_plotly(file: UploadFile = File(...), sheet_name: Optional[str] = Form(None)):
    try:
        contents = await file.read()
        if sheet_name is None:
            sheet_name = "0"
            
        df = pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name)
        
        # 데이터프레임에서 적절한 차트 데이터 생성
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        if not numeric_columns:
            return [{"error": "수치형 데이터가 없습니다."}]
        
        charts = []
        for i, num_col in enumerate(numeric_columns[:3]):  # 최대 3개의 차트만 생성
            # X축은 첫 번째 열 또는 인덱스 사용
            x_column = df.columns[0] if len(df.columns) > 0 else df.index.name or "Index"
            x_data = df.iloc[:, 0].tolist() if len(df.columns) > 0 else list(range(len(df)))
            
            # 기본적인 막대 차트 데이터
            chart_data = {
                "data": [
                    {
                        "x": x_data,
                        "y": df[num_col].tolist(),
                        "type": "bar",
                        "name": num_col,
                        "marker": {"color": f"#{hash(num_col) % 0xffffff:06x}"}
                    }
                ],
                "layout": {
                    "title": f"{file.filename} - {num_col} 분석",
                    "xaxis": {"title": x_column},
                    "yaxis": {"title": num_col}
                },
                "dataframe": df.to_dict('list')
            }
            
            charts.append({
                "sheet_name": sheet_name,
                "original_file_name": file.filename,
                "chart_type": "bar",
                "chart_json": json.dumps(chart_data),
                "d3_data": json.dumps(chart_data),
                "columns": [x_column],
                "numeric_columns": [num_col],
                "rows_count": len(df)
            })
        
        if not charts:
            return [{"error": "차트를 생성할 수 없습니다."}]
            
        return charts
        
    except Exception as e:
        print(f"Error creating chart: {str(e)}")
        traceback.print_exc()
        return [{"error": f"차트 생성 중 오류 발생: {str(e)}"}]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 