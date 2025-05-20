import React, { useState, useRef, useEffect } from 'react';
import Plot from 'react-plotly.js';
import axios from 'axios';
import './PlotlyChart.css';

interface PlotlyChartProps {
  chartData: any;
  title?: string;
  d3Data?: string;
  onTitleChange?: (newTitle: string) => void;
  onColorChange?: (colorIndex: number, newColor: string) => void;
  onToggleD3View?: () => void;
  showD3?: boolean;
}

interface ColorSet {
  index: number;
  color: string;
  name: string;
}

const PlotlyChart: React.FC<PlotlyChartProps> = ({ 
  chartData, 
  title, 
  d3Data, 
  onTitleChange, 
  onColorChange,
  onToggleD3View,
  showD3 = false
}) => {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState<boolean>(false);
  const [currentTitle, setCurrentTitle] = useState<string>('');
  const [colors, setColors] = useState<ColorSet[]>([]);
  const [isEditingColors, setIsEditingColors] = useState<boolean>(false);
  
  const titleInputRef = useRef<HTMLInputElement>(null);
  const chartRef = useRef<any>(null);
  
  // 차트 데이터와 타이틀 처리를 위한 useEffect
  useEffect(() => {
    let parsedData = null;
    let layoutData = null;
    let chartTitle = '차트';

    try {
      if (typeof chartData === 'string') {
        parsedData = JSON.parse(chartData);
        layoutData = parsedData.layout || {};
      } else if (chartData && chartData.data) {
        parsedData = chartData;
        layoutData = chartData.layout || {};
      }
      
      // 타이틀 초기화
      chartTitle = title || (layoutData && layoutData.title ? 
        (typeof layoutData.title === 'object' ? layoutData.title.text : layoutData.title) 
        : '차트');
      
      // 타이틀 설정
      setCurrentTitle(chartTitle);
      
      // 색상 정보 추출
      const newColors: ColorSet[] = [];
      const plotData = parsedData && parsedData.data ? parsedData.data : [];
      
      if (plotData && Array.isArray(plotData)) {
        plotData.forEach((trace, index) => {
          let color = '';
          let name = trace.name || `시리즈 ${index + 1}`;
          
          if (trace.marker && trace.marker.color) {
            color = trace.marker.color;
          } else if (trace.line && trace.line.color) {
            color = trace.line.color;
          }
          
          if (color) {
            newColors.push({ index, color, name });
          }
        });
      }
      
      setColors(newColors);
    } catch (e) {
      console.error('차트 데이터 파싱 오류:', e);
      setError('차트 데이터를 파싱할 수 없습니다.');
      setIsLoading(false);
    }
  }, [chartData, title]);
  
  // chartData가 JSON 문자열인 경우 파싱
  let plotData;
  let layout;
  
  try {
    if (typeof chartData === 'string') {
      const parsedData = JSON.parse(chartData);
      plotData = parsedData.data || [];
      layout = parsedData.layout || {};
    } else if (chartData && chartData.data) {
      plotData = chartData.data;
      layout = chartData.layout || {};
    } else {
      throw new Error('유효하지 않은 차트 데이터 형식');
    }
    
  } catch (e) {
    console.error('차트 데이터 파싱 오류:', e);
    setError('차트 데이터를 파싱할 수 없습니다.');
    setIsLoading(false);
    return (
      <div className="plotly-chart-error">
        <p>차트 로딩 중 오류가 발생했습니다: {error}</p>
      </div>
    );
  }
  
  // 타이틀 클릭 처리
  const handleTitleClick = () => {
    if (onTitleChange) {
      setEditingTitle(true);
      // 약간의 지연을 두고 포커스 설정
      setTimeout(() => {
        if (titleInputRef.current) {
          titleInputRef.current.focus();
        }
      }, 50);
    }
  };
  
  // 타이틀 편집 완료 처리
  const handleTitleBlur = () => {
    setEditingTitle(false);
    if (onTitleChange) {
      onTitleChange(currentTitle);
    }
  };
  
  // 타이틀 키 입력 처리
  const handleTitleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleTitleBlur();
    }
  };
  
  // 색상 변경 처리
  const handleColorChange = (index: number, newColor: string) => {
    // 현재 색상 배열 업데이트
    const updatedColors = colors.map(item => 
      item.index === index ? { ...item, color: newColor } : item
    );
    setColors(updatedColors);
    
    // 부모 컴포넌트에 색상 변경 알림
    if (onColorChange) {
      onColorChange(index, newColor);
    }
  };
  
  // PNG 다운로드 처리
  const handleDownloadPNG = async () => {
    try {
      // 차트 데이터가 있는지 확인
      if (!chartData) {
        throw new Error('차트 데이터가 없습니다.');
      }

      // 백엔드 API를 사용한 PNG 다운로드 구현
      // 1. 차트 데이터를 서버로 전송
      // 2. 서버에서 생성된 PNG 이미지를 다운로드
      
      let chartJsonString = chartData;
      
      if (typeof chartData !== 'string') {
        // 이미 객체인 경우 문자열로 변환
        chartJsonString = JSON.stringify(chartData);
      }
      
      // URL 쿼리 파라미터 인코딩
      const params = new URLSearchParams({
        chart_json: chartJsonString
      });

      // 파일 다운로드 방식으로 요청
      try {
        const response = await axios.get(`/api/visualize/download-png?${params}`, {
          responseType: 'blob'
        });
        
        // Blob URL 생성 및 다운로드 링크 생성
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${currentTitle || 'chart'}.png`);
        document.body.appendChild(link);
        link.click();
        
        // 리소스 정리
        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);
      } catch (apiError) {
        console.error('백엔드 PNG 다운로드 API 오류:', apiError);
        
        // 백엔드 API 실패 시 클라이언트 측 방식으로 폴백
        alert('서버 PNG 다운로드에 실패했습니다. 클라이언트 측 다운로드를 시도합니다.');
        fallbackClientDownload();
      }
    } catch (error) {
      console.error('PNG 다운로드 오류:', error);
      alert('PNG 다운로드 중 오류가 발생했습니다.');
      // 오류 발생 시 클라이언트 측 방식 시도
      fallbackClientDownload();
    }
  };
  
  // 클라이언트 측 다운로드 폴백 메서드
  const fallbackClientDownload = async () => {
    try {
      if (chartRef.current) {
        try {
          const Plotly = await import("plotly.js-dist");
          const chartDiv = chartRef.current.el;
          if (chartDiv) {
            // plotly.js-dist 모듈 사용
            const dataUrl = await Plotly.toImage(chartDiv, {
              format: 'png',
              width: 1200,
              height: 800,
              scale: 2
            });
            
            // 데이터 URL을 사용하여 다운로드 링크 생성
            const link = document.createElement('a');
            link.href = dataUrl;
            link.download = `${currentTitle || 'chart'}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          } else {
            throw new Error('Plotly 차트 요소를 찾을 수 없습니다.');
          }
        } catch (err) {
          console.error('클라이언트 측 PNG 변환 오류:', err);
          alert('PNG 이미지 변환에 실패했습니다. 브라우저 개발자 도구에서 오류 확인 가능합니다.');
        }
      }
    } catch (error) {
      console.error('폴백 다운로드 오류:', error);
    }
  };
  
  // 로딩 상태 처리
  const handlePlotInitialized = () => {
    setIsLoading(false);
  };
  
  // 차트 크기 설정
  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    toImageButtonOptions: {
      format: 'png',
      filename: currentTitle || 'chart',
      scale: 2
    }
  };
  
  return (
    <div className="plotly-chart-container">
      {isLoading && (
        <div className="plotly-chart-loading">
          <div className="loading-spinner"></div>
          <p>차트 로딩 중...</p>
        </div>
      )}
      
      {!isLoading && (
        <div className="chart-title-container">
          {editingTitle ? (
            <input
              ref={titleInputRef}
              type="text"
              className="chart-title-edit"
              value={currentTitle}
              onChange={(e) => setCurrentTitle(e.target.value)}
              onBlur={handleTitleBlur}
              onKeyDown={handleTitleKeyDown}
            />
          ) : (
            <h3 
              className="chart-title"
              onClick={handleTitleClick}
              title={onTitleChange ? "클릭하여 제목 편집" : ""}
            >
              {currentTitle}
              {onTitleChange && <span className="edit-icon">✎</span>}
            </h3>
          )}
        </div>
      )}
      
      {error ? (
        <div className="plotly-chart-error">
          <p>차트 로딩 중 오류가 발생했습니다: {error}</p>
        </div>
      ) : (
        <div className="chart-view-container">
          <Plot
            data={plotData}
            layout={layout}
            config={config}
            onInitialized={handlePlotInitialized}
            onError={(err: Error) => {
              console.error('Plotly 렌더링 오류:', err);
              setError('차트를 렌더링할 수 없습니다.');
              setIsLoading(false);
            }}
            className="plotly-chart"
            ref={chartRef}
          />
          
          {!isLoading && (
            <div className="chart-actions">
              <div className="chart-action-buttons">
                <button 
                  className="download-png-btn"
                  onClick={handleDownloadPNG}
                >
                  PNG 다운로드
                </button>
                
                <button
                  className="color-edit-btn"
                  onClick={() => setIsEditingColors(!isEditingColors)}
                >
                  {isEditingColors ? '색상 편집 닫기' : '색상 편집'}
                </button>
              </div>
              
              {isEditingColors && (
                <div className="color-edit-panel">
                  <h4>차트 색상 커스터마이징</h4>
                  <div className="color-list">
                    {colors.map((colorItem) => (
                      <div key={colorItem.index} className="color-item">
                        <span className="color-name">{colorItem.name}</span>
                        <input
                          type="color"
                          value={colorItem.color}
                          onChange={(e) => handleColorChange(colorItem.index, e.target.value)}
                          className="color-picker"
                        />
                        <div 
                          className="color-preview" 
                          style={{ backgroundColor: colorItem.color }}
                        ></div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PlotlyChart; 