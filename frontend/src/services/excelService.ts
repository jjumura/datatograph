import axios from 'axios';
import { ExcelAnalysisResponse, ExcelReadResponse, ExcelSplitTablesResponse } from '../types/excel';

const API_URL = 'http://localhost:8000';

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