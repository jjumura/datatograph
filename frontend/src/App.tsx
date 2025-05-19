import React, { useState, useCallback, ChangeEvent, FormEvent } from 'react';
import axios from 'axios';
import './index.css'; // App.tsx에 대한 CSS (기존 ExcelUploader.css 등)
import ExcelUploader, { ChartData } from './components/ExcelUploader'; // 기존 파일 업로더
import LoadingPage from './components/LoadingPage';

// App 상태 정의
type AppState = 'idle' | 'processing' | 'results' | 'error';

function App() {
  const [appState, setAppState] = useState<AppState>('idle');
  const [chartData, setChartData] = useState<ChartData[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingMessage, setLoadingMessage] = useState<string>("데이터 분석 중...");
  const [textPrompt, setTextPrompt] = useState<string>("");

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
      setAppState('error');
    }
  }, []);

  const handleTextPromptChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setTextPrompt(event.target.value);
  };

  const handlePromptSubmit = useCallback(async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!textPrompt.trim()) {
      setError("분석할 내용을 입력해주세요.");
      return;
    }
    setAppState('processing');
    setLoadingMessage("프롬프트 분석 및 차트 생성 중...");
    setError(null);

    try {
      const response = await axios.post<ChartData[]>('/api/visualize/text-prompt', { prompt: textPrompt });
      
      if (response.data && response.data[0] && response.data[0].gemini_suggestion && response.data[0].gemini_suggestion.primary_chart_suggestion) {
        setLoadingMessage(`AI 추천 (${response.data[0].gemini_suggestion.primary_chart_suggestion.chart_type}) 분석 완료!`);
      } else if (response.data && response.data[0] && response.data[0].error) {
        setLoadingMessage("분석 중 오류 발생");
      } else {
        setLoadingMessage("분석 완료! 결과 준비 중...");
      }

      setChartData(response.data);
      if (response.data && response.data[0] && response.data[0].error) {
        setError(response.data[0].error);
        setAppState('error');
      } else {
        setAppState('results');
        setError(null);
      }

    } catch (err: any) {
      console.error("Text prompt submission error:", err);
      let errorMessage = "프롬프트 처리 중 오류가 발생했습니다.";
      if (err.response && err.response.data && err.response.data.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.response && err.response.data && Array.isArray(err.response.data) && err.response.data[0] && err.response.data[0].error) {
        errorMessage = err.response.data[0].error;
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      setChartData(null);
      setAppState('error');
    }
  }, [textPrompt]);

  const handleReset = () => {
    setAppState('idle');
    setChartData(null);
    setError(null);
    setTextPrompt("");
  };

  return (
    <div className="App">
      {/* 로딩 페이지는 다른 모든 컨텐츠 위에 전체 화면으로 표시됩니다. */}
      {appState === 'processing' && <LoadingPage message={loadingMessage} />}

      <header className="App-header">
        <h1>AI 데이터 분석 및 시각화 도구</h1>
      </header>

      {/* 현재 상태에 따라 다른 컴포넌트/내용 표시 */}
      {appState === 'idle' && (
        <main className="main-content">
          <div className="input-section prompt-input-section">
            <h2>텍스트 프롬프트 입력</h2>
            <form onSubmit={handlePromptSubmit} className="prompt-form">
              <textarea
                value={textPrompt}
                onChange={handleTextPromptChange}
                placeholder="예: 연도별 대한민국 영화 관객 수 추이 그래프 그려줘"
                rows={4}
                className="prompt-textarea"
                disabled={appState !== 'idle'}
              />
              <button type="submit" disabled={appState !== 'idle' || !textPrompt.trim()} className="prompt-submit-button">
                프롬프트로 생성
              </button>
            </form>
          </div>
          
          <div className="input-section file-upload-section">
            <h2>또는 파일 업로드</h2>
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

      {appState === 'results' && chartData && (
        <div className="results-section">
          <h2>분석 결과</h2>
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
                <img src={`data:image/png;base64,${data.chart_base64}`} alt={`${data.sheet_name} 차트`} className="chart-image" />
              ) : (
                <p className="no-chart-data">{data.error || "차트 데이터를 생성할 수 없습니다."}</p>
              )}
              <div className="data-summary">
                {data.columns && <p><strong>데이터 컬럼:</strong> {data.columns.join(', ')}</p>}
                {data.numeric_columns && <p><strong>수치형 컬럼:</strong> {data.numeric_columns.join(', ')}</p>}
                {data.rows_count !== null && <p><strong>데이터 행 수:</strong> {data.rows_count}</p>}
              </div>
            </div>
          ))}
          <button onClick={handleReset} className="reset-button">새 분석 시작</button>
        </div>
      )}
      
      <footer className="App-footer">
        <p>Project_A © 2025</p>
      </footer>
    </div>
  );
}

export default App; 