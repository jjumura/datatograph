import React, { useState, useRef, DragEvent, useCallback } from 'react';
import './ExcelUploader.css';

// App.tsx와 일치하도록 ChartData 타입 정의 및 export
export interface ChartData {
  sheet_name: string;
  original_file_name: string; // 추가됨
  chart_base64: string | null; // 백엔드에서 에러 시 null일 수 있음
  chart_svg_path: string | null; // SVG 파일 경로 추가
  columns: string[] | null;
  numeric_columns: string[] | null;
  rows_count: number | null;
  error?: string | null; // 에러 메시지 필드
  gemini_suggestion?: any | null; // Gemini 분석 결과 (타입은 필요에 따라 더 구체화)
}

interface ExcelUploaderProps {
  onFileUpload: (file: File, sheetName?: string) => Promise<void>; // App.tsx로부터 받을 콜백
  disabled: boolean; // App.tsx로부터 받을 비활성화 상태
  // sheetName 입력을 받는다면, 해당 prop도 추가할 수 있습니다.
  // onSheetNameChange?: (name: string) => void;
}

const ExcelUploader: React.FC<ExcelUploaderProps> = ({ onFileUpload, disabled }) => {
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // sheetName을 위한 상태 (만약 ExcelUploader 내에서 관리한다면)
  // const [sheetNameInput, setSheetNameInput] = useState<string>('');

  // processFile 로직은 onFileUpload 콜백을 호출하도록 변경
  const handleProcessFile = useCallback(async (file: File) => {
    const allowedMimeTypes = [
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/csv'
    ];
    const allowedExtensions = ['.xls', '.xlsx', '.csv'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

    // 파일 유효성 검사는 App.tsx의 onFileUpload 콜백 내부 또는 여기서도 수행 가능
    // 여기서는 간단히 콜백만 호출합니다.
    if (!allowedMimeTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
      // App.tsx에서 에러 처리하므로 여기서는 간단히 알리거나, App.tsx의 콜백이 에러를 throw 하도록 유도
      // alert('지원하지 않는 파일 형식입니다. (.xls, .xlsx, .csv 파일만 허용됩니다)');
      // return;
    }
    
    // sheetNameInput이 있다면 함께 전달
    // await onFileUpload(file, sheetNameInput);
    await onFileUpload(file); // 현재는 sheetName 입력 UI가 없으므로 파일만 전달

  }, [onFileUpload]); // sheetNameInput을 사용한다면 의존성 배열에 추가

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    if (e.target.files?.length) {
      handleProcessFile(e.target.files[0]);
    }
    if(e.target) {
      e.target.value = ''; // 같은 파일 재업로드 가능하도록 초기화
    }
  };

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDraggingOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    // e.relatedTarget이 currentTarget 외부를 가리킬 때만 false로 설정
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
        setIsDraggingOver(false);
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation(); 
    if (!disabled && !isDraggingOver) setIsDraggingOver(true);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(false);
    
    if (!disabled && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleProcessFile(e.dataTransfer.files[0]);
      e.dataTransfer.clearData();
    }
  };

  const handleAreaClick = () => {
    if (!disabled && fileInputRef.current) {
       fileInputRef.current.click();
    }
  };

  // sheetName 입력 필드 (선택 사항)
  /*
  const handleSheetNameInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSheetNameInput(e.target.value);
  };
  */

  return (
    <div className={`excel-uploader-container excel-uploader ${disabled ? 'uploader-disabled' : ''}`}>
      {/* 시트 이름 입력 필드 - 필요시 주석 해제하고 스타일링 */}
      {/* 
      <div className="sheet-name-input-container">
        <label htmlFor="sheetName">시트 이름 (선택 사항):</label>
        <input 
          type="text" 
          id="sheetName" 
          value={sheetNameInput} 
          onChange={handleSheetNameInputChange} 
          placeholder="특정 시트만 분석하려면 입력"
          disabled={disabled}
        />
      </div>
      */}
      <div 
        className={`upload-area ${isDraggingOver ? 'drag-over' : ''} ${disabled ? 'uploading' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleAreaClick}
        role="button"
        tabIndex={disabled ? -1 : 0}
        onKeyPress={(e) => { if (!disabled && (e.key === 'Enter' || e.key === ' ')) handleAreaClick(); }}
        aria-disabled={disabled}
        aria-label="Excel 또는 CSV 파일 업로드 영역"
      >
        <input 
          ref={fileInputRef}
          type="file" 
          onChange={handleFileChange}
          accept=".xlsx,.xls,.csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          className="file-input"
          disabled={disabled}
        />
        <div className="upload-icon">📊</div>
        <p className="upload-text">여기에 파일을 드래그하거나 <br />클릭하여 업로드하세요.</p>
        <p className="file-types">(.xls, .xlsx, .csv 파일만 지원)</p>
      </div>
      
      {/* 로딩, 에러, 차트 표시는 App.tsx에서 하므로 여기서는 제거 */}
    </div>
  );
};

export default ExcelUploader; 