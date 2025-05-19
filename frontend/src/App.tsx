import { useState, useCallback } from 'react';
import axios from 'axios';
import './index.css'; // App.tsx에 대한 CSS (기존 ExcelUploader.css 등)
import ExcelUploader, { ChartData } from './components/ExcelUploader'; // 기존 파일 업로더
import LoadingPage from './components/LoadingPage';
import PlotlyChart from './components/PlotlyChart'; // Plotly 차트 컴포넌트 추가

// App 상태 정의 (progress_view 상태 제거)
type AppState = 'idle' | 'processing' | 'results' | 'error';

// Plotly 차트 데이터 타입 정의
interface PlotlyChartData {
  sheet_name: string;
  original_file_name: string;
  chart_type: string;
  chart_json: string;
  columns: string[];
  numeric_columns: string[];
  rows_count: number;
  error?: string;
}

function App() {
  const [appState, setAppState] = useState<AppState>('idle');
  const [chartData, setChartData] = useState<ChartData[] | null>(null);
  const [plotlyChartData, setPlotlyChartData] = useState<PlotlyChartData[] | null>(null);
  const [useInteractive, setUseInteractive] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingMessage, setLoadingMessage] = useState<string>("데이터 분석 중...");

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
      
      // 사용자 설정에 따라 정적 차트 또는 인터랙티브 차트 요청
      if (useInteractive) {
        // Plotly 기반 차트 요청
        const response = await axios.post<PlotlyChartData[]>('/api/visualize/plotly/excel', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        setLoadingMessage("인터랙티브 차트 생성 완료!");
        setPlotlyChartData(response.data);
        setChartData(null);
      } else {
        // 기존 정적 차트 요청
        const response = await axios.post<ChartData[]>('/api/visualize/excel', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        if (response.data && response.data[0] && response.data[0].gemini_suggestion && response.data[0].gemini_suggestion.primary_chart_suggestion) {
          setLoadingMessage(`AI 추천 (${response.data[0].gemini_suggestion.primary_chart_suggestion.chart_type}) 분석 완료!`);
        } else {
          setLoadingMessage("분석 완료! 결과 준비 중...");
        }
        
        setChartData(response.data);
        setPlotlyChartData(null);
      }
      
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
      setPlotlyChartData(null);
      setAppState('error');
    }
  }, [useInteractive]);

  const handleReset = () => {
    setAppState('idle');
    setChartData(null);
    setPlotlyChartData(null);
    setError(null);
  };

  const toggleChartType = () => {
    setUseInteractive(!useInteractive);
  };

  return (
    <div className="App">
      {/* 로딩 페이지는 다른 모든 컨텐츠 위에 전체 화면으로 표시됩니다. */}
      {appState === 'processing' && <LoadingPage message={loadingMessage} />}

      <header className="App-header">
        <h1>AI 데이터 분석 및 시각화 도구</h1>
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
            <div className="chart-type-toggle">
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={useInteractive}
                  onChange={toggleChartType}
                  className="toggle-checkbox"
                />
                <span className="toggle-text">
                  {useInteractive ? '인터랙티브 차트 (Plotly)' : '정적 차트 (Matplotlib)'}
                </span>
              </label>
              <div className="toggle-description">
                {useInteractive ? 
                  '인터랙티브 차트는 확대/축소, 데이터 탐색이 가능합니다.' : 
                  '정적 차트는 기본적인 시각화와 AI 분석을 제공합니다.'}
              </div>
            </div>
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
          
          {/* 인터랙티브 Plotly 차트 결과 */}
          {plotlyChartData && (
            <div className="plotly-results">
              {plotlyChartData.map((data, index) => (
                <div key={index} className="chart-container">
                  <h3>{data.original_file_name} - {data.sheet_name}</h3>
                  {data.error ? (
                    <p className="chart-error">{data.error}</p>
                  ) : (
                    <div className="interactive-chart-container">
                      <PlotlyChart 
                        chartData={data.chart_json} 
                        title={`${data.original_file_name} - ${data.sheet_name}`}
                      />
                      
                      <div className="chart-metadata">
                        <p><strong>차트 유형:</strong> {data.chart_type}</p>
                        <p><strong>데이터 크기:</strong> {data.rows_count}행 × {data.columns.length}열</p>
                        <p><strong>숫자형 열:</strong> {data.numeric_columns.join(', ')}</p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          
          {/* 기존 정적 차트 결과 */}
          {chartData && (
            <div className="static-chart-results">
              {chartData.map((data, index) => (
                <div key={index} className="chart-container">
                  <h3>{data.original_file_name} - {data.sheet_name}</h3>
                  {data.gemini_suggestion && (
                    <div className="gemini-recommendation">
                      <p><strong>AI 분석 요약:</strong> {data.gemini_suggestion.data_characteristics || data.gemini_suggestion.request_summary}</p>
                      {data.gemini_suggestion.primary_chart_suggestion && (
                        <p>
                          <strong>추천 차트:</strong> {data.gemini_suggestion.primary_chart_suggestion.reason} 
                          (유형: {data.gemini_suggestion.primary_chart_suggestion.chart_type})
                        </p>
                      )}
                    </div>
                  )}
                  {data.chart_base64 ? (
                    <div className="chart-display">
                      <img src={`data:image/png;base64,${data.chart_base64}`} alt={`${data.sheet_name} 차트`} className="chart-image" />
                      {data.chart_svg_path && (
                        <div className="chart-actions">
                          <button 
                            className="svg-download-btn"
                            onClick={() => {
                              if (data.chart_svg_path) {
                                // SVG 파일 다운로드 처리
                                axios.get(`/api/visualize/download/${data.chart_svg_path}`, { responseType: 'blob' })
                                  .then(response => {
                                    const url = window.URL.createObjectURL(new Blob([response.data]));
                                    const link = document.createElement('a');
                                    link.href = url;
                                    link.setAttribute('download', `${data.sheet_name.replace(/[^a-zA-Z0-9가-힣]/g, '_')}.svg`);
                                    document.body.appendChild(link);
                                    link.click();
                                    window.URL.revokeObjectURL(url);
                                    document.body.removeChild(link);
                                  })
                                  .catch(error => {
                                    console.error('SVG 다운로드 오류:', error);
                                  });
                              }
                            }}
                          >
                            SVG 다운로드
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="chart-error">차트 생성에 실패했습니다.</p>
                  )}
                </div>
              ))}
            </div>
          )}
          
          <div className="action-buttons">
            <button onClick={handleReset} className="reset-button">다시 분석하기</button>
            <button onClick={handleReset} className="home-button">처음으로</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App; 