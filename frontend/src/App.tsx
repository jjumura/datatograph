import { useState, useCallback } from 'react';
import axios from 'axios';
import './index.css'; // App.tsx에 대한 CSS (기존 ExcelUploader.css 등)
import ExcelUploader, { ChartData } from './components/ExcelUploader'; // 기존 파일 업로더
import LoadingPage from './components/LoadingPage';
import D3Chart from './components/D3Chart'; // D3.js 차트 컴포넌트 추가

// Cloud Run에 배포된 백엔드 서버 URL
const API_URL = 'https://fastapi-backend-986535008493.asia-northeast3.run.app';

// App 상태 정의 (progress_view 상태 제거)
type AppState = 'idle' | 'processing' | 'results' | 'error';

// 차트 스타일 타입 정의
interface ChartStyle {
  fontFamily: string;
  fontSize: number;
  titleSize: number;
  axisColor: string;
  gridLines: boolean;
  barOpacity: number;
}

// D3 차트 데이터 타입 정의
interface D3ChartData {
  sheet_name: string;
  original_file_name: string;
  chart_type: string;
  d3_data: string;
  columns: string[];
  numeric_columns: string[];
  rows_count: number;
  custom_title?: string;
  error?: string;
}

// 파일명에서 확장자와 시트명 제거 함수 추가
const getCleanFileName = (fileName: string): string => {
  // 확장자 제거 (.xlsx, .csv 등)
  let cleanName = fileName.replace(/\.(xlsx|xls|csv|txt)$/i, '');
  // "- Sheet1" 같은 시트 이름 제거
  cleanName = cleanName.replace(/\s*-\s*Sheet\d+$/i, '');
  return cleanName;
};

function App() {
  const [appState, setAppState] = useState<AppState>('idle');
  const [chartData, setChartData] = useState<ChartData[] | null>(null);
  const [d3ChartData, setD3ChartData] = useState<D3ChartData[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingMessage, setLoadingMessage] = useState<string>("데이터 분석 중...");
  const [showStyleEditor, setShowStyleEditor] = useState<boolean>(false);
  const [chartStyle, setChartStyle] = useState<ChartStyle>({
    fontFamily: 'Pretendard, sans-serif',
    fontSize: 12,
    titleSize: 16,
    axisColor: '#ffffff',
    gridLines: false,
    barOpacity: 0.9
  });
  
  // 차트 타이틀 수정 처리
  const handleTitleChange = useCallback((chartIndex: number, newTitle: string) => {
    if (!d3ChartData) return;
    
    const updatedChartData = [...d3ChartData];
    updatedChartData[chartIndex] = {
      ...updatedChartData[chartIndex],
      custom_title: newTitle
    };
    
    setD3ChartData(updatedChartData);
  }, [d3ChartData]);
  
  const handleReset = () => {
    setAppState('idle');
    setChartData(null);
    setD3ChartData(null);
    setError(null);
  };

  const handleFileUpload = useCallback(async (file: File, sheetName?: string) => {
    setAppState('processing');
    setLoadingMessage("파일을 서버로 전송 중입니다...");
    const formData = new FormData();
    formData.append('file', file);
    if (sheetName) {
      formData.append('sheet_name', sheetName);
    }

    try {
      setLoadingMessage("데이터 처리 및 차트 생성 중...");
      
      const response = await axios.post<D3ChartData[]>(`${API_URL}/api/visualize/d3/excel`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setLoadingMessage("차트 생성 완료!");
      setD3ChartData(response.data);
      setChartData(null);
      
      setAppState('results');
      setError(null);

    } catch (err: any) {
      console.error("File upload error:", err);
      let errorMessage = "파일 업로드 또는 처리 중 오류가 발생했습니다.";
      if (err.response && err.response.data && err.response.data.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.response && err.response.data && Array.isArray(err.response.data) && err.response.data[0] && err.response.data[0].error) {
        errorMessage = err.response.data[0].error;
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      setChartData(null);
      setD3ChartData(null);
      setAppState('error');
    }
  }, []);

  // PNG 다운로드 처리
  const handleDownloadPNG = () => {
    if (!d3ChartData || d3ChartData.length === 0) return;
    
    try {
      // SVG 요소 가져오기
      const svgElement = document.querySelector(".d3-chart-container svg");
      if (!svgElement) {
        console.error("SVG 요소를 찾을 수 없습니다.");
        return;
      }

      // SVG를 캔버스로 변환
      const svgData = new XMLSerializer().serializeToString(svgElement);
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        console.error("2D 컨텍스트를 가져올 수 없습니다.");
        return;
      }

      // 캔버스 크기 설정
      canvas.width = svgElement.clientWidth * 2;
      canvas.height = svgElement.clientHeight * 2;
      ctx.scale(2, 2); // 고해상도를 위한 스케일링

      // 배경색 설정 (D3 차트의 배경과 일치)
      ctx.fillStyle = "#1e1e2f";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // SVG를 이미지로 변환
      const img = new Image();
      const blob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
      const url = URL.createObjectURL(blob);

      img.onload = () => {
        ctx.drawImage(img, 0, 0, svgElement.clientWidth, svgElement.clientHeight);
        URL.revokeObjectURL(url);

        // 다운로드 링크 생성
        const imgURL = canvas.toDataURL("image/png");
        const link = document.createElement("a");
        const currentData = d3ChartData[0];
        const filename = currentData.custom_title || `${currentData.original_file_name} - ${currentData.sheet_name}`;
        link.download = `${filename || 'chart'}.png`;
        link.href = imgURL;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      };

      img.src = url;
    } catch (error) {
      console.error("PNG 다운로드 오류:", error);
      alert("PNG 다운로드 중 오류가 발생했습니다.");
    }
  };

  // 스타일 편집 토글 처리
  const handleToggleStyleEditor = () => {
    setShowStyleEditor(!showStyleEditor);
  };

  // 차트 스타일 변경 처리
  const handleStyleChange = (key: keyof ChartStyle, value: any) => {
    setChartStyle(prev => ({
      ...prev,
      [key]: value
    }));
  };

  return (
    <div className="App">
      {/* 로딩 페이지는 다른 모든 컨텐츠 위에 전체 화면으로 표시됩니다. */}
      {appState === 'processing' && <LoadingPage message={loadingMessage} />}

      <header className="App-header">
        <h1>AI 딸깍 데이터 시각화 도구</h1>
        {appState === 'error' && (
          <button onClick={handleReset} className="back-button">
            처음으로
          </button>
        )}
      </header>

      {/* 현재 상태에 따라 다른 컴포넌트/내용 표시 */}
      {appState === 'idle' && (
        <main className="main-content">
          <div className="input-section file-upload-section">
            <h2>파일 업로드</h2>
            <ExcelUploader onFileUpload={handleFileUpload} disabled={appState !== 'idle'} />
          </div>
        </main>
      )}
      
      {appState === 'error' && (
        <div className="error-section">
          <h2>오류 발생</h2>
          <p>{error}</p>
          <button onClick={handleReset} className="reset-button">다시 시도</button>
        </div>
      )}

      {appState === 'results' && (
        <div className="results-section">
          <h2>분석 결과</h2>
          
          {/* 인터랙티브 D3 차트 결과 */}
          {d3ChartData && (
            <div className="d3-results">
              {d3ChartData.map((data, index) => (
                <div key={index} className="chart-container">
                  {data.error ? (
                    <p className="chart-error">{data.error}</p>
                  ) : (
                    <div className="interactive-chart-container">
                      <D3Chart
                        d3Data={data.d3_data}
                        title={data.custom_title || getCleanFileName(data.original_file_name)}
                        onTitleChange={(newTitle) => handleTitleChange(index, newTitle)}
                        onStyleEditRequest={handleToggleStyleEditor}
                        style={chartStyle}
                      />
                      {showStyleEditor && (
                        <div className="chart-style-editor">
                          <h4>차트 스타일 편집</h4>
                          <div className="style-option">
                            <label>폰트</label>
                            <select
                              value={chartStyle.fontFamily}
                              onChange={(e) => handleStyleChange('fontFamily', e.target.value)}
                            >
                              <option value="Pretendard, sans-serif">Pretendard</option>
                              <option value="Arial, sans-serif">Arial</option>
                              <option value="Helvetica, sans-serif">Helvetica</option>
                              <option value="'Noto Sans KR', sans-serif">Noto Sans KR</option>
                              <option value="'Malgun Gothic', sans-serif">맑은 고딕</option>
                            </select>
                          </div>
                          
                          <div className="style-option">
                            <label>글자 크기</label>
                            <input
                              type="range"
                              min="8"
                              max="16"
                              value={chartStyle.fontSize}
                              onChange={(e) => handleStyleChange('fontSize', parseInt(e.target.value))}
                            />
                            <span>{chartStyle.fontSize}px</span>
                          </div>
                          
                          <div className="style-option">
                            <label>제목 크기</label>
                            <input
                              type="range"
                              min="14"
                              max="24"
                              value={chartStyle.titleSize}
                              onChange={(e) => handleStyleChange('titleSize', parseInt(e.target.value))}
                            />
                            <span>{chartStyle.titleSize}px</span>
                          </div>
                          
                          <div className="style-option">
                            <label>바 투명도</label>
                            <input
                              type="range"
                              min="0.3"
                              max="1"
                              step="0.1"
                              value={chartStyle.barOpacity}
                              onChange={(e) => handleStyleChange('barOpacity', parseFloat(e.target.value))}
                            />
                            <span>{chartStyle.barOpacity}</span>
                          </div>
                          
                          <div className="style-option">
                            <label>그리드 라인</label>
                            <input
                              type="checkbox"
                              checked={chartStyle.gridLines}
                              onChange={(e) => handleStyleChange('gridLines', e.target.checked)}
                            />
                          </div>
                          
                          <div className="style-option">
                            <label>축 색상</label>
                            <input
                              type="color"
                              value={chartStyle.axisColor}
                              onChange={(e) => handleStyleChange('axisColor', e.target.value)}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          
          <div className="action-buttons">
            <button onClick={handleToggleStyleEditor} className="style-edit-btn">
              {showStyleEditor ? '스타일 편집 닫기' : '스타일 편집'}
            </button>
            <button onClick={handleDownloadPNG} className="download-png-btn">PNG 다운로드</button>
            <button onClick={handleReset} className="home-button">처음으로</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App; 