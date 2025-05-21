import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import './PlotlyChart.css'; // 기존 차트 스타일 재사용

interface ChartStyle {
  fontFamily?: string;
  fontSize?: number;
  titleSize?: number;
  axisColor?: string;
  gridLines?: boolean;
  barOpacity?: number;
  colors?: string[];
}

interface D3ChartProps {
  d3Data: string;
  title?: string;
  onTitleChange?: (newTitle: string) => void;
  onToggleD3View?: () => void;
  style?: ChartStyle;
  onStyleEditRequest?: () => void;
}

const defaultStyle: ChartStyle = {
  fontFamily: 'Pretendard, sans-serif',
  fontSize: 12,
  titleSize: 16,
  axisColor: 'white',
  gridLines: false,
  barOpacity: 0.9,
  colors: d3.schemeCategory10
};

const D3Chart: React.FC<D3ChartProps> = ({ d3Data, title, onTitleChange, onToggleD3View, style, onStyleEditRequest }) => {
  const d3Container = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);
  const [currentTitle, setCurrentTitle] = React.useState<string>(title || '차트');
  const [editingTitle, setEditingTitle] = React.useState<boolean>(false);
  const [chartStyle, setChartStyle] = useState<ChartStyle>({...defaultStyle, ...style});
  const [showStyleEditor, setShowStyleEditor] = useState<boolean>(false);
  const titleInputRef = useRef<HTMLInputElement>(null);

  // 스타일 변경 핸들러
  const handleStyleChange = (key: keyof ChartStyle, value: any) => {
    setChartStyle(prev => ({
      ...prev,
      [key]: value
    }));
  };

  useEffect(() => {
    // 타이틀 업데이트
    if (title) {
      setCurrentTitle(title);
    }
  }, [title]);

  useEffect(() => {
    // 외부에서 전달된 스타일이 변경되면 업데이트
    if (style) {
      setChartStyle(prev => ({...prev, ...style}));
    }
  }, [style]);

  // 타이틀 클릭 처리
  const handleTitleClick = () => {
    if (onTitleChange) {
      setEditingTitle(true);
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

  // PNG 다운로드 처리
  const handleDownloadPNG = () => {
    if (!d3Container.current) return;

    try {
      // SVG 요소 가져오기
      const svgElement = d3Container.current.querySelector("svg");
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
        link.download = `${currentTitle || 'chart'}.png`;
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

  useEffect(() => {
    if (!d3Container.current || !d3Data) return;

    setIsLoading(true);
    setError(null);

    try {
      // 기존 차트 삭제
      d3.select(d3Container.current).selectAll("*").remove();

      // D3 데이터 파싱
      const parsedData = typeof d3Data === 'string' ? JSON.parse(d3Data) : d3Data;
      const series = parsedData.data || [];
      const chartType = (series[0] && series[0].type) ? series[0].type : 'bar';

      console.log('파싱된 데이터:', parsedData);
      console.log('시리즈 데이터:', series);
      console.log('차트 타입:', chartType);

      // 마진 및 차트 크기 설정
      const margin = { top: 40, right: 30, bottom: 60, left: 60 };
      const width = d3Container.current.clientWidth - margin.left - margin.right;
      const height = 500 - margin.top - margin.bottom;

      // SVG 생성
      const svg = d3.select(d3Container.current)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

      // 차트 타입에 따른 렌더링
      if (chartType === 'bar') {
        renderBarChart(svg, width, height, series);
      } else if (chartType === 'line') {
        renderLineChart(svg, width, height, series);
      } else if (chartType === 'scatter') {
        renderScatterChart(svg, width, height, series);
      } else if (chartType === 'pie') {
        renderPieChart(svg, width, height, series);
      } else {
        // 기본 텍스트 표시
        svg.append("text")
          .attr("x", width / 2)
          .attr("y", height / 2)
          .attr("text-anchor", "middle")
          .style("fill", chartStyle.axisColor)
          .style("font-family", chartStyle.fontFamily)
          .style("font-size", `${chartStyle.fontSize}px`)
          .text("지원하지 않는 차트 타입입니다.");
      }

      // 타이틀 추가
      svg.append("text")
        .attr("x", width / 2)
        .attr("y", -10)
        .attr("text-anchor", "middle")
        .style("font-size", `${chartStyle.titleSize}px`)
        .style("fill", chartStyle.axisColor)
        .style("font-family", chartStyle.fontFamily)
        .text(currentTitle);

      setIsLoading(false);
    } catch (error) {
      console.error("D3 차트 렌더링 오류:", error);
      setError("차트를 렌더링할 수 없습니다.");
      setIsLoading(false);
    }
  }, [d3Data, currentTitle, chartStyle]);

  // 막대 차트 렌더링 함수
  const renderBarChart = (svg: any, width: number, height: number, series: any[]) => {
    if (!series.length || !series[0].x || !series[0].y) return;

    // 기존 툴팁 제거 후 다시 생성
    d3.select(d3Container.current).select(".d3-tooltip").remove();
    d3.select("body").select(".d3-tooltip").remove();
    
    // 툴팁 div 생성
    const tooltip = d3.select("body")  // body에 직접 추가
      .append("div")
      .attr("class", "d3-tooltip")
      .style("opacity", 0)
      .style("position", "absolute")
      .style("background-color", "rgba(40, 44, 52, 0.95)")
      .style("color", "white")
      .style("border-radius", "5px")
      .style("padding", "10px")
      .style("font-size", `${chartStyle.fontSize}px`)
      .style("font-family", chartStyle.fontFamily)
      .style("pointer-events", "none")
      .style("box-shadow", "0 0 10px rgba(0, 0, 0, 0.5)")
      .style("z-index", "10000")
      .style("min-width", "120px")
      .style("text-align", "center")
      .style("border", "1px solid rgba(255, 255, 255, 0.2)");

    // X 축 도메인 설정
    const x = d3.scaleBand()
      .domain(series[0].x)
      .range([0, width])
      .padding(0.2);

    // Y 축 도메인 설정 (모든 시리즈의 최대값 기준)
    const maxY = d3.max(series, d => d3.max(d.y || [])) || 0;
    const y = d3.scaleLinear()
      .domain([0, maxY * 1.1 as number]) // 10% 여유 공간 추가
      .range([height, 0]);

    // X 축 그리기
    svg.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .attr("transform", "translate(-10,0)rotate(-45)")
      .style("text-anchor", "end")
      .style("font-size", `${chartStyle.fontSize}px`)
      .style("font-family", chartStyle.fontFamily)
      .style("fill", chartStyle.axisColor);

    // Y 축 그리기
    svg.append("g")
      .call(d3.axisLeft(y))
      .selectAll("text")
      .style("font-size", `${chartStyle.fontSize}px`)
      .style("font-family", chartStyle.fontFamily)
      .style("fill", chartStyle.axisColor);

    // 그리드 라인 추가 (선택적)
    if (chartStyle.gridLines) {
      // Y축 그리드 라인
      svg.append("g")
        .attr("class", "grid")
        .call(
          d3.axisLeft(y)
            .tickSize(-width)
            .tickFormat(() => '')
        )
        .style("stroke", "rgba(255,255,255,0.1)")
        .style("stroke-dasharray", "3,3");
    }

    // 막대 그리기
    series.forEach((serie, i) => {
      const barWidth = x.bandwidth() / series.length;
      
      svg.selectAll(`.bar-${i}`)
        .data(serie.y)
        .enter()
        .append("rect")
        .attr("class", `bar-${i}`)
        .attr("x", (d: any, j: number) => {
          const xPos = x(serie.x[j]);
          return (xPos !== undefined ? xPos : 0) + i * barWidth;
        })
        .attr("y", (d: any) => y(d))
        .attr("width", barWidth)
        .attr("height", (d: any) => height - y(d))
        .attr("fill", serie.color || (chartStyle.colors ? chartStyle.colors[i % chartStyle.colors.length] : d3.schemeCategory10[i % 10]))
        .attr("rx", 3) // 모서리 둥글게
        .attr("ry", 3)
        .attr("opacity", chartStyle.barOpacity)
        .style("cursor", "pointer")
        .on("mouseover", function(this: SVGRectElement, event: MouseEvent, d: number) {
          const index = serie.y.indexOf(d);
          const xValue = serie.x[index];
          
          // 호버 효과
          d3.select(this)
            .transition()
            .duration(200)
            .attr("fill", d3.color(serie.color || (chartStyle.colors ? chartStyle.colors[i % chartStyle.colors.length] : d3.schemeCategory10[i % 10]))?.brighter(0.5)?.toString() || '');
          
          // 툴팁 표시
          tooltip.transition()
            .duration(100)
            .style("opacity", 1);
          
          tooltip.html(`
            <strong>${xValue}</strong>
            <div style="font-size: ${chartStyle.fontSize! + 6}px; font-weight: bold; margin: 5px 0; color: ${serie.color || (chartStyle.colors ? chartStyle.colors[i % chartStyle.colors.length] : d3.schemeCategory10[i % 10])};">${d}</div>
            <div style="font-size: ${chartStyle.fontSize}px; opacity: 0.8;">${serie.name || `시리즈 ${i+1}`}</div>
          `)
            .style("left", `${event.pageX + 15}px`)
            .style("top", `${event.pageY - 70}px`);
        })
        .on("mouseout", function(this: SVGRectElement) {
          // 호버 효과 제거
          d3.select(this)
            .transition()
            .duration(500)
            .attr("fill", serie.color || (chartStyle.colors ? chartStyle.colors[i % chartStyle.colors.length] : d3.schemeCategory10[i % 10]));
          
          // 툴팁 숨기기
          tooltip.transition()
            .duration(300)
            .style("opacity", 0);
        })
        .on("mousemove", function(event: MouseEvent) {
          // 마우스 움직임에 따라 툴팁 위치 업데이트
          tooltip
            .style("left", `${event.pageX + 15}px`)
            .style("top", `${event.pageY - 70}px`);
        });
    });

    // 범례 추가
    addLegend(svg, width, height, series);
  };

  // 선 차트 렌더링 함수
  const renderLineChart = (svg: any, width: number, height: number, series: any[]) => {
    if (!series.length || !series[0].x || !series[0].y) return;

    // 툴팁 div 생성
    d3.select("body").select(".d3-tooltip").remove();
    const tooltip = d3.select("body")
      .append("div")
      .attr("class", "d3-tooltip")
      .style("opacity", 0)
      .style("position", "absolute")
      .style("background-color", "rgba(40, 44, 52, 0.95)")
      .style("color", "white")
      .style("border-radius", "5px")
      .style("padding", "10px")
      .style("font-size", `${chartStyle.fontSize}px`)
      .style("font-family", chartStyle.fontFamily)
      .style("pointer-events", "none")
      .style("box-shadow", "0 0 10px rgba(0, 0, 0, 0.5)")
      .style("z-index", "10000")
      .style("min-width", "120px")
      .style("text-align", "center")
      .style("border", "1px solid rgba(255, 255, 255, 0.2)");

    // X 축 도메인 설정
    const xValues = series[0].x;
    const x = d3.scalePoint()
      .domain(xValues)
      .range([0, width]);

    // Y 축 도메인 설정 (모든 시리즈의 최대값 기준)
    const maxY = d3.max(series, d => d3.max(d.y || [])) || 0;
    const y = d3.scaleLinear()
      .domain([0, maxY * 1.1 as number]) // 10% 여유 공간 추가
      .range([height, 0]);

    // X 축 그리기
    svg.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .attr("transform", "translate(-10,0)rotate(-45)")
      .style("text-anchor", "end")
      .style("font-size", `${chartStyle.fontSize}px`)
      .style("font-family", chartStyle.fontFamily)
      .style("fill", chartStyle.axisColor);

    // Y 축 그리기
    svg.append("g")
      .call(d3.axisLeft(y))
      .selectAll("text")
      .style("font-size", `${chartStyle.fontSize}px`)
      .style("font-family", chartStyle.fontFamily)
      .style("fill", chartStyle.axisColor);

    // 그리드 라인 추가 (선택적)
    if (chartStyle.gridLines) {
      // Y축 그리드 라인
      svg.append("g")
        .attr("class", "grid")
        .call(
          d3.axisLeft(y)
            .tickSize(-width)
            .tickFormat(() => '')
        )
        .style("stroke", "rgba(255,255,255,0.1)")
        .style("stroke-dasharray", "3,3");
    }

    // 선 생성 함수
    const line = d3.line()
      .x((d: any, i: number) => x(xValues[i]) as number)
      .y((d: any) => y(d))
      .curve(d3.curveMonotoneX);

    // 선 그리기
    series.forEach((serie, i) => {
      // 선 그리기
      svg.append("path")
        .datum(serie.y)
        .attr("fill", "none")
        .attr("stroke", serie.color || d3.schemeCategory10[i % 10])
        .attr("stroke-width", 2.5)
        .attr("d", line);

      // 데이터 포인트 그리기
      svg.selectAll(`.point-${i}`)
        .data(serie.y)
        .enter()
        .append("circle")
        .attr("class", `point-${i}`)
        .attr("cx", (d: any, j: number) => {
          const xPos = x(serie.x[j]);
          return xPos !== undefined ? xPos : 0;
        })
        .attr("cy", (d: any) => y(d))
        .attr("r", 5)
        .attr("fill", serie.color || d3.schemeCategory10[i % 10])
        .style("cursor", "pointer")
        .on("mouseover", function(this: SVGCircleElement, event: MouseEvent, d: number) {
          const index = serie.y.indexOf(d);
          const xValue = serie.x[index];
          
          // 호버 효과
          d3.select(this)
            .transition()
            .duration(200)
            .attr("r", 8);
          
          // 툴팁 표시
          tooltip.transition()
            .duration(200)
            .style("opacity", 1);
          
          tooltip.html(`
            <strong>${xValue}</strong>
            <div class="value" style="color: ${serie.color || d3.schemeCategory10[i % 10]};">${d}</div>
            <div class="series-name">${serie.name || `시리즈 ${i+1}`}</div>
          `)
            .style("left", `${(event.pageX + 10)}px`)
            .style("top", `${(event.pageY - 80)}px`);
        })
        .on("mouseout", function(this: SVGCircleElement) {
          // 호버 효과 제거
          d3.select(this)
            .transition()
            .duration(500)
            .attr("r", 5);
          
          // 툴팁 숨기기
          tooltip.transition()
            .duration(500)
            .style("opacity", 0);
        });
    });

    // 범례 추가
    addLegend(svg, width, height, series);
  };

  // 산점도 렌더링 함수
  const renderScatterChart = (svg: any, width: number, height: number, series: any[]) => {
    if (!series.length || !series[0].x || !series[0].y) return;

    // X 축 도메인 설정
    const xValues = series[0].x;
    const x = d3.scalePoint()
      .domain(xValues)
      .range([0, width]);

    // Y 축 도메인 설정 (모든 시리즈의 최대값 기준)
    const maxY = d3.max(series, d => d3.max(d.y || [])) || 0;
    const y = d3.scaleLinear()
      .domain([0, maxY * 1.1 as number]) // 10% 여유 공간 추가
      .range([height, 0]);

    // X 축 그리기
    svg.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .attr("transform", "translate(-10,0)rotate(-45)")
      .style("text-anchor", "end")
      .style("font-size", `${chartStyle.fontSize}px`)
      .style("font-family", chartStyle.fontFamily)
      .style("fill", chartStyle.axisColor);

    // Y 축 그리기
    svg.append("g")
      .call(d3.axisLeft(y))
      .selectAll("text")
      .style("font-size", `${chartStyle.fontSize}px`)
      .style("font-family", chartStyle.fontFamily)
      .style("fill", chartStyle.axisColor);

    // 산점도 그리기
    series.forEach((serie, i) => {
      svg.selectAll(`.point-${i}`)
        .data(serie.y)
        .enter()
        .append("circle")
        .attr("class", `point-${i}`)
        .attr("cx", (d: any, j: number) => {
          const xPos = x(serie.x[j]);
          return xPos !== undefined ? xPos : 0;
        })
        .attr("cy", (d: any) => y(d))
        .attr("r", 8)
        .attr("fill", serie.color || d3.schemeCategory10[i % 10])
        .attr("stroke", "white")
        .attr("stroke-width", 1)
        .attr("opacity", 0.8);
    });

    // 범례 추가
    addLegend(svg, width, height, series);
  };

  // 파이 차트 렌더링 함수
  const renderPieChart = (svg: any, width: number, height: number, series: any[]) => {
    if (!series.length || !series[0].values || !series[0].labels) return;

    // 반지름 계산
    const radius = Math.min(width, height) / 2;

    // 중심점 이동
    svg.attr("transform", `translate(${width / 2},${height / 2})`);

    // 색상 설정
    const color = d3.scaleOrdinal()
      .domain(series[0].labels)
      .range(series[0].color ? [series[0].color] : d3.schemeCategory10);

    // 파이 생성기
    const pie = d3.pie<any>()
      .value((d: any) => d);

    // 아크 생성기
    const arc = d3.arc<any>()
      .innerRadius(0)
      .outerRadius(radius * 0.8);

    // 라벨용 아크
    const labelArc = d3.arc<any>()
      .innerRadius(radius * 0.6)
      .outerRadius(radius * 0.8);

    // 아크 그리기
    const arcs = svg.selectAll(".arc")
      .data(pie(series[0].values))
      .enter()
      .append("g")
      .attr("class", "arc");

    arcs.append("path")
      .attr("d", arc)
      .attr("fill", (d: any, i: number) => color(series[0].labels[i]))
      .attr("stroke", "white")
      .attr("stroke-width", 1);

    // 라벨 추가
    arcs.append("text")
      .attr("transform", (d: any) => `translate(${labelArc.centroid(d)})`)
      .attr("text-anchor", "middle")
      .attr("dy", ".35em")
      .text((d: any, i: number) => series[0].labels[i])
      .style("font-size", "12px")
      .style("fill", "white");

    // 값 라벨 추가
    arcs.append("text")
      .attr("transform", (d: any) => `translate(${arc.centroid(d)})`)
      .attr("text-anchor", "middle")
      .attr("dy", "0em")
      .text((d: any) => `${d.value}`)
      .style("font-size", "10px")
      .style("fill", "white")
      .style("font-weight", "bold");
  };

  // 범례 추가 함수
  const addLegend = (svg: any, width: number, height: number, series: any[]) => {
    const legend = svg.append("g")
      .attr("class", "legend")
      .attr("transform", `translate(0,${height + 30})`);

    series.forEach((serie, i) => {
      const legendRow = legend.append("g")
        .attr("transform", `translate(${i * 100}, 0)`);

      legendRow.append("rect")
        .attr("width", 15)
        .attr("height", 15)
        .attr("fill", serie.color || (chartStyle.colors ? chartStyle.colors[i % chartStyle.colors.length] : d3.schemeCategory10[i % 10]));

      legendRow.append("text")
        .attr("x", 20)
        .attr("y", 12)
        .text(serie.name || `시리즈 ${i + 1}`)
        .style("font-size", `${chartStyle.fontSize}px`)
        .style("font-family", chartStyle.fontFamily)
        .style("fill", chartStyle.axisColor);
    });
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
          <div
            className="d3-chart-container"
            ref={d3Container}
          ></div>

          {!isLoading && (
            <div className="chart-actions">
              <div className="chart-action-buttons">
                {onToggleD3View && (
                  <button
                    className="toggle-view-btn"
                    onClick={onToggleD3View}
                  >
                    Plotly 보기
                  </button>
                )}
              </div>
            </div>
          )}
          
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
                  value={chartStyle.axisColor === 'white' ? '#ffffff' : chartStyle.axisColor!}
                  onChange={(e) => handleStyleChange('axisColor', e.target.value)}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default D3Chart; 