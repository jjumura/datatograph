from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from typing import List, Optional, Union
from app.utils.excel_handler import read_excel_file, analyze_excel_structure, split_multiple_tables

router = APIRouter(tags=["excel"])


@router.post("/analyze")
async def analyze_excel(
    file: UploadFile = File(...),
    sheet_name: Optional[Union[str, int]] = Query(0, description="시트 이름 또는 인덱스")
):
    """
    엑셀 파일의 구조를 분석하여 반환합니다.
    
    - **file**: 업로드할 엑셀 파일
    - **sheet_name**: 분석할 시트 이름 또는 인덱스 (기본값: 0)
    """
    # 파일 확장자 체크
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="엑셀 파일(.xls, .xlsx)만 업로드 가능합니다")
    
    # 파일 내용 읽기
    file_content = await file.read()
    
    # 파일 구조 분석
    structure = analyze_excel_structure(file_content, sheet_name)
    
    return {
        "filename": file.filename,
        "sheet_name": sheet_name,
        "structure": structure
    }


@router.post("/read")
async def read_excel(
    file: UploadFile = File(...),
    sheet_name: Optional[Union[str, int]] = Query(0, description="시트 이름 또는 인덱스")
):
    """
    엑셀 파일의 내용을 읽어서 데이터를 반환합니다.
    
    - **file**: 업로드할 엑셀 파일
    - **sheet_name**: 읽을 시트 이름 또는 인덱스 (기본값: 0)
    """
    # 파일 확장자 체크
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="엑셀 파일(.xls, .xlsx)만 업로드 가능합니다")
    
    # 파일 내용 읽기
    file_content = await file.read()
    
    # 엑셀 데이터 읽기
    data = read_excel_file(file_content, sheet_name)
    
    # 데이터가 비어있으면 여러 테이블로 나누기 시도
    if len(data) == 0:
        tables = split_multiple_tables(file_content, sheet_name)
        return {
            "filename": file.filename,
            "sheet_name": sheet_name,
            "is_empty": True,
            "multiple_tables": True,
            "tables": tables
        }
    
    return {
        "filename": file.filename,
        "sheet_name": sheet_name,
        "is_empty": len(data) == 0,
        "multiple_tables": False,
        "data": data
    }


@router.post("/split-tables")
async def split_tables(
    file: UploadFile = File(...),
    sheet_name: Optional[Union[str, int]] = Query(0, description="시트 이름 또는 인덱스")
):
    """
    엑셀 파일에서 여러 테이블을 분리하여 반환합니다.
    
    - **file**: 업로드할 엑셀 파일
    - **sheet_name**: 분석할 시트 이름 또는 인덱스 (기본값: 0)
    """
    # 파일 확장자 체크
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="엑셀 파일(.xls, .xlsx)만 업로드 가능합니다")
    
    # 파일 내용 읽기
    file_content = await file.read()
    
    # 여러 테이블로 분할
    tables = split_multiple_tables(file_content, sheet_name)
    
    return {
        "filename": file.filename,
        "sheet_name": sheet_name,
        "tables_count": len(tables),
        "tables": tables
    } 