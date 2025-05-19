export interface ExcelStructure {
  columns: string[];
  rows_count: number;
  columns_count: number;
  dtypes: Record<string, string>;
  has_data: boolean;
}

export interface ExcelTable {
  sheet_name: string;
  table_index: number;
  start_row: number;
  end_row: number;
  columns: string[];
  rows_count: number;
  data: Record<string, any>[];
}

export interface ExcelAnalysisResponse {
  filename: string;
  sheet_name: string | number;
  structure: ExcelStructure;
}

export interface ExcelReadResponse {
  filename: string;
  sheet_name: string | number;
  is_empty: boolean;
  multiple_tables: boolean;
  data?: Record<string, any>[];
  tables?: ExcelTable[];
}

export interface ExcelSplitTablesResponse {
  filename: string;
  sheet_name: string | number;
  tables_count: number;
  tables: ExcelTable[];
} 