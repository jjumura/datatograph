import axios from 'axios';
import { ExcelAnalysisResponse, ExcelReadResponse, ExcelSplitTablesResponse } from '../types/excel';

// 로컬 개발환경에서는 localhost 사용
// const API_URL = 'http://localhost:8000'; 

// Cloud Run에 배포된 백엔드 서버 URL 사용
const API_URL = 'https://fastapi-backend-986535008493.asia-northeast3.run.app';  // 실제 Cloud Run URL로 교체

export const analyzeExcelFile = async (file: File, sheetName: string | number = 0): Promise<ExcelAnalysisResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post<ExcelAnalysisResponse>(
    `${API_URL}/excel/analyze`, 
    formData,
    {
      params: { sheet_name: sheetName },
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  
  return response.data;
};

export const readExcelFile = async (file: File, sheetName: string | number = 0): Promise<ExcelReadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post<ExcelReadResponse>(
    `${API_URL}/excel/read`, 
    formData,
    {
      params: { sheet_name: sheetName },
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  
  return response.data;
};

export const splitExcelTables = async (file: File, sheetName: string | number = 0): Promise<ExcelSplitTablesResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post<ExcelSplitTablesResponse>(
    `${API_URL}/excel/split-tables`, 
    formData,
    {
      params: { sheet_name: sheetName },
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  
  return response.data;
}; 