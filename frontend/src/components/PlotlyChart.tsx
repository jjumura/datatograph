import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import './PlotlyChart.css';

interface PlotlyChartProps {
  chartData: any;
  title?: string;
}

const PlotlyChart: React.FC<PlotlyChartProps> = ({ chartData, title }) => {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
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
    
    // 타이틀 오버라이드 (props에서 전달된 경우)
    if (title && layout) {
      layout.title = title;
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
  
  // 로딩 상태 처리
  const handlePlotInitialized = () => {
    setIsLoading(false);
  };
  
  // 차트 크기 설정
  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d']
  };
  
  return (
    <div className="plotly-chart-container">
      {isLoading && (
        <div className="plotly-chart-loading">
          <div className="loading-spinner"></div>
          <p>차트 로딩 중...</p>
        </div>
      )}
      
      {error ? (
        <div className="plotly-chart-error">
          <p>차트 로딩 중 오류가 발생했습니다: {error}</p>
        </div>
      ) : (
        <Plot
          data={plotData}
          layout={layout}
          config={config}
          onInitialized={handlePlotInitialized}
          onError={(err) => {
            console.error('Plotly 렌더링 오류:', err);
            setError('차트를 렌더링할 수 없습니다.');
            setIsLoading(false);
          }}
          className="plotly-chart"
        />
      )}
    </div>
  );
};

export default PlotlyChart; 