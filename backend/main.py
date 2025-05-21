from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import json
import pandas as pd
import io
import traceback
import os

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dtv-five.vercel.app",  # 베셀 main
        "https://dtv-dpdps-projects.vercel.app",  # 베셀 1
        "https://dt-k8yd6y9bd-dpdps-projects.vercel.app",  # 베셀 2
        "http://localhost:3000",  # 개발용(로컬)
    ],
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

# ---- sheet_name 안전 변환 함수 ----
def get_actual_sheet_name(contents, sheet_name):
    excel_file = pd.ExcelFile(io.BytesIO(contents))
    sheet_names = excel_file.sheet_names
    if sheet_name in [None, 0, "0"]:
        return sheet_names[0]
    elif sheet_name in sheet_names:
        return sheet_name
    else:
        return sheet_names[0]
# ---------------------------------

# 엑셀 파일 분석 엔드포인트
@app.post("/excel/analyze")
async def analyze_excel(file: UploadFile = File(...), sheet_name: Optional[str] = Form("0")):
    try:
        contents = await file.read()
        actual_sheet = get_actual_sheet_name(contents, sheet_name)
        df = pd.read_excel(io.BytesIO(contents), sheet_name=actual_sheet)
        
        columns = df.columns.tolist()
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        
        return {
            "sheet_name": actual_sheet,
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
        actual_sheet = get_actual_sheet_name(contents, sheet_name)
        df = pd.read_excel(io.BytesIO(contents), sheet_name=actual_sheet)
        
        data = df.values.tolist()
        columns = df.columns.tolist()
        
        return {
            "sheet_name": actual_sheet,
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
        actual_sheet = get_actual_sheet_name(contents, sheet_name)
        df = pd.read_excel(io.BytesIO(contents), sheet_name=actual_sheet)
        
        data = df.values.tolist()
        
        return {
            "sheet_name": actual_sheet,
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

# D3 시각화 엔드포인트
@app.post("/api/visualize/d3/excel")
async def visualize_excel_d3(file: UploadFile = File(...), sheet_name: Optional[str] = Form(None)):
    try:
        contents = await file.read()
        actual_sheet = get_actual_sheet_name(contents, sheet_name)
        df = pd.read_excel(io.BytesIO(contents), sheet_name=actual_sheet)
        
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        if not numeric_columns:
            return [{"error": "수치형 데이터가 없습니다."}]
        
        charts = []
        for i, num_col in enumerate(numeric_columns[:3]):  # 최대 3개의 차트만 생성
            x_column = df.columns[0] if len(df.columns) > 0 else df.index.name or "Index"
            x_data = df.iloc[:, 0].tolist() if len(df.columns) > 0 else list(range(len(df)))
            
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
                "sheet_name": actual_sheet,
                "original_file_name": file.filename,
                "chart_type": "bar",
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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
