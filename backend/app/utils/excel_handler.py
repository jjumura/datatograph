import pandas as pd
from typing import List, Dict, Any, Optional, Union
import io
import numpy as np
from datetime import datetime


def read_excel_file(file_content: bytes, sheet_name: Optional[Union[str, int]] = 0) -> List[Dict[str, Any]]:
    """
    엑셀 파일의 내용을 읽어서 데이터를 반환합니다.
    
    Args:
        file_content: 파일 내용(bytes)
        sheet_name: 시트 이름 또는 인덱스
        
    Returns:
        List[Dict[str, Any]]: 엑셀 데이터를 딕셔너리 리스트로 변환한 결과
    """
    try:
        # 파일 내용을 바이트 스트림으로 읽기
        excel_data = io.BytesIO(file_content)
        
        # 엑셀 파일 읽기
        df = pd.read_excel(excel_data, sheet_name=sheet_name)
        
        # 데이터프레임의 행 수가 0인 경우(비어있는 경우)
        if len(df) == 0:
            return []
            
        # NaN 값을 None으로 변환
        df = df.replace({np.nan: None})
        
        # 날짜/시간 값을 ISO 형식 문자열로 변환
        for col in df.select_dtypes(include=['datetime64']).columns:
            df[col] = df[col].apply(lambda x: x.isoformat() if pd.notnull(x) else None)
            
        # 데이터프레임을 딕셔너리 리스트로 변환
        result = df.to_dict(orient='records')
        return result
    
    except Exception as e:
        # 에러 발생 시 빈 리스트 반환
        print(f"엑셀 파일 읽기 에러: {e}")
        return []


def analyze_excel_structure(file_content: bytes, sheet_name: Optional[Union[str, int]] = 0) -> Dict[str, Any]:
    """
    엑셀 파일의 구조를 분석하여 반환합니다.
    
    Args:
        file_content: 파일 내용(bytes)
        sheet_name: 시트 이름 또는 인덱스
        
    Returns:
        Dict[str, Any]: 엑셀 파일의 구조 정보
    """
    try:
        # 파일 내용을 바이트 스트림으로 읽기
        excel_data = io.BytesIO(file_content)
        
        # 엑셀 파일 읽기
        df = pd.read_excel(excel_data, sheet_name=sheet_name)
        
        # 구조 분석 결과
        structure = {
            "columns": df.columns.tolist(),
            "rows_count": len(df),
            "columns_count": len(df.columns),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
            "has_data": len(df) > 0,
            "missing_values": df.isnull().sum().to_dict()
        }
        
        return structure
    
    except Exception as e:
        print(f"엑셀 구조 분석 에러: {e}")
        return {
            "error": str(e),
            "columns": [],
            "rows_count": 0,
            "columns_count": 0,
            "dtypes": {},
            "has_data": False,
            "missing_values": {}
        }


def split_multiple_tables(file_content: bytes, sheet_name: Optional[Union[str, int]] = 0) -> List[Dict[str, Any]]:
    """
    하나의 시트에 여러 테이블이 있는 경우, 여러 테이블로 나눠서 반환합니다.
    
    Args:
        file_content: 파일 내용(bytes)
        sheet_name: 시트 이름 또는 인덱스
        
    Returns:
        List[Dict[str, Any]]: 여러 테이블 정보를 담은 리스트
    """
    try:
        # 파일 내용을 바이트 스트림으로 읽기
        excel_data = io.BytesIO(file_content)
        
        # 전체 시트를 읽기
        xl = pd.ExcelFile(excel_data)
        
        # 시트 이름이 문자열이면 해당 시트만 처리, 아니면 모든 시트 처리
        if isinstance(sheet_name, str):
            sheets_to_process = [sheet_name]
        else:
            sheets_to_process = xl.sheet_names
        
        tables = []
        
        for sheet in sheets_to_process:
            # 시트 내용 읽기
            df = pd.read_excel(excel_data, sheet_name=sheet)
            
            # NaN 값을 None으로 변환
            df = df.replace({np.nan: None})
            
            # 날짜/시간 값을 ISO 형식 문자열로 변환
            for col in df.select_dtypes(include=['datetime64']).columns:
                df[col] = df[col].apply(lambda x: x.isoformat() if pd.notnull(x) else None)
            
            # 비어있는 행을 기준으로 테이블 분할
            if len(df) == 0:
                # 엑셀 데이터가 빈 경우 처리
                continue
                
            # 연속된 NaN 행을 찾아 테이블 구분
            is_empty_row = df.isna().all(axis=1)
            table_breaks = list(is_empty_row[is_empty_row].index)
            
            # 테이블 시작과 끝 인덱스 설정
            table_indices = [(0, table_breaks[0])] if table_breaks else [(0, len(df))]
            
            for i in range(len(table_breaks)):
                start = table_breaks[i] + 1
                end = table_breaks[i+1] if i+1 < len(table_breaks) else len(df)
                if start < end:  # 빈 테이블 제외
                    table_indices.append((start, end))
            
            # 테이블 분할 및 저장
            for idx, (start, end) in enumerate(table_indices):
                if end > start:  # 빈 테이블 제외
                    table_df = df.iloc[start:end].reset_index(drop=True)
                    # 첫 행이 모두 NaN이 아니고 데이터가 존재하는 경우만 처리
                    if not table_df.empty and not table_df.iloc[0].isna().all():
                        # 첫 행을 새 헤더로 사용할지 결정
                        if table_df.iloc[0].notna().all() and all(isinstance(x, str) for x in table_df.iloc[0].tolist() if pd.notna(x)):
                            table_df.columns = table_df.iloc[0]
                            table_df = table_df.iloc[1:].reset_index(drop=True)
                            
                        # NaN 값을 None으로 변환
                        table_df = table_df.replace({np.nan: None})
                        
                        # 날짜/시간 값을 ISO 형식 문자열로 변환
                        for col in table_df.select_dtypes(include=['datetime64']).columns:
                            table_df[col] = table_df[col].apply(lambda x: x.isoformat() if pd.notnull(x) else None)
                            
                        tables.append({
                            "sheet_name": sheet,
                            "table_index": idx,
                            "start_row": int(start),
                            "end_row": int(end),
                            "columns": table_df.columns.tolist(),
                            "rows_count": len(table_df),
                            "data": table_df.to_dict(orient='records')
                        })
        
        return tables
    
    except Exception as e:
        print(f"테이블 분할 에러: {e}")
        return [{
            "error": str(e),
            "sheet_name": str(sheet_name),
            "table_index": 0,
            "start_row": 0,
            "end_row": 0,
            "columns": [],
            "rows_count": 0,
            "data": []
        }] 