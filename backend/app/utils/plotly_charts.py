import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, List, Optional, Union
import uuid
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

# 색상 팔레트 정의
PLASMA_COLORS = ['#F44027', '#5402a3', '#8b0aa5', '#b83289', '#db5c68', '#f48849', '#febc2a', '#f0f921']
VIRIDIS_COLORS = ['#F44027', '#414487', '#2a788e', '#22a884', '#7ad151', '#fde725']

class PlotlyChartGenerator:
    """Plotly를 사용한 대화형 차트 생성 클래스"""
    
    def __init__(self):
        self.template = "plotly_dark"  # 다크 테마 기본 적용
        
    def _apply_common_styles(self, fig):
        """공통 스타일 적용"""
        fig.update_layout(
            template=self.template,
            font=dict(
                family="Pretendard, sans-serif",
                size=14
            ),
            margin=dict(l=50, r=30, t=50, b=50),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )
        
        # 그리드 스타일 조정
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(211, 211, 211, 0.2)'
        )
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(211, 211, 211, 0.2)'
        )
        
        return fig
    
    def generate_bar_chart(self, df: pd.DataFrame, x: str, y: Union[str, List[str]], title: str) -> go.Figure:
        """막대 차트 생성"""
        if isinstance(y, list) and len(y) > 1:
            # 여러 y 값에 대한 그룹화된 막대 차트
            fig = go.Figure()
            
            for i, y_col in enumerate(y):
                fig.add_trace(go.Bar(
                    x=df[x],
                    y=df[y_col],
                    name=y_col,
                    marker_color=VIRIDIS_COLORS[i % len(VIRIDIS_COLORS)]
                ))
                
            # 막대 모양 설정 - 여기서 모든 트레이스에 대해 한 번에 설정
            fig.update_traces(
                marker_line_width=0,  # 테두리 제거
                marker_line_color="rgba(0,0,0,0)",
                selector=dict(type="bar")
            )
            
            # Plotly 버전 확인 후 borderradius 적용
            try:
                fig.update_traces(
                    marker=dict(borderradius=5),  # 더 작은 값으로 시도
                    selector=dict(type="bar")
                )
            except Exception as e:
                print(f"모서리 라운드 적용 실패: {e}")
            
            fig.update_layout(
                barmode='group',
                title=title,
                xaxis_title=x,
                yaxis_title="값"
            )
        else:
            # 단일 y 값에 대한 막대 차트
            y_col = y[0] if isinstance(y, list) else y
            fig = px.bar(
                df, 
                x=x, 
                y=y_col,
                title=title,
                color_discrete_sequence=VIRIDIS_COLORS
            )
            
            # 막대 모양 설정 - try/except로 안전하게 처리
            try:
                fig.update_traces(
                    marker_line_width=0,
                    marker_line_color="rgba(0,0,0,0)",
                    marker=dict(borderradius=5),  # 더 작은 값으로 시도
                    selector=dict(type="bar")
                )
            except Exception as e:
                print(f"모서리 라운드 적용 실패: {e}")
                # 기본 스타일만 적용
                fig.update_traces(
                    marker_line_width=0,
                    marker_line_color="rgba(0,0,0,0)",
                    selector=dict(type="bar")
                )
            
        return self._apply_common_styles(fig)
    
    def generate_line_chart(self, df: pd.DataFrame, x: str, y: Union[str, List[str]], title: str) -> go.Figure:
        """선 차트 생성"""
        fig = px.line(
            df, 
            x=x, 
            y=y,
            title=title,
            color_discrete_sequence=PLASMA_COLORS
        )
        
        # 마커 추가
        for trace in fig.data:
            trace.update(mode='lines+markers')
            
        return self._apply_common_styles(fig)
    
    def generate_scatter_chart(self, df: pd.DataFrame, x: str, y: Union[str, List[str]], title: str) -> go.Figure:
        """산점도 생성"""
        if isinstance(y, list) and len(y) > 1:
            # 여러 y 값에 대한 여러 산점도
            fig = go.Figure()
            
            for i, y_col in enumerate(y):
                fig.add_trace(go.Scatter(
                    x=df[x],
                    y=df[y_col],
                    name=y_col,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=PLASMA_COLORS[i % len(PLASMA_COLORS)]
                    )
                ))
                
            fig.update_layout(
                title=title,
                xaxis_title=x,
                yaxis_title="값"
            )
        else:
            # 단일 y 값에 대한 산점도
            y_col = y[0] if isinstance(y, list) else y
            fig = px.scatter(
                df, 
                x=x, 
                y=y_col,
                title=title,
                color_discrete_sequence=PLASMA_COLORS
            )
            
            # 마커 크기 조정
            fig.update_traces(marker=dict(size=10))
            
        return self._apply_common_styles(fig)
    
    def generate_pie_chart(self, df: pd.DataFrame, labels: str, values: str, title: str) -> go.Figure:
        """파이 차트 생성"""
        fig = px.pie(
            df, 
            names=labels, 
            values=values,
            title=title,
            color_discrete_sequence=VIRIDIS_COLORS
        )
        
        # 파이 차트 특화 스타일링
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            textfont_size=12,
            marker=dict(line=dict(color='rgba(0,0,0,0.3)', width=1))
        )
        
        return self._apply_common_styles(fig)
    
    def generate_heatmap(self, df: pd.DataFrame, title: str) -> go.Figure:
        """히트맵 생성 - 숫자 데이터에 대한 상관관계 표시에 유용"""
        # 숫자형 컬럼만 선택
        numeric_df = df.select_dtypes(include=['number'])
        
        if numeric_df.empty:
            # 숫자형 데이터가 없는 경우 빈 히트맵 반환
            return self.generate_fallback_chart(df, title)
            
        # 상관관계 계산
        corr = numeric_df.corr()
        
        fig = px.imshow(
            corr,
            text_auto=True,
            aspect="auto",
            color_continuous_scale=px.colors.sequential.Plasma,
            title=title
        )
        
        return self._apply_common_styles(fig)
    
    def generate_fallback_chart(self, df: pd.DataFrame, title: str) -> go.Figure:
        """데이터를 표시할 적합한 차트가 없는 경우 기본 테이블 표시"""
        # 처음 10개 행만 선택
        sample_df = df.head(10)
        
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(sample_df.columns),
                fill_color='rgba(73, 80, 87, 0.8)',
                align='center',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=[sample_df[col] for col in sample_df.columns],
                fill_color='rgba(52, 58, 64, 0.5)',
                align='center',
                font=dict(color='white', size=11)
            )
        )])
        
        fig.update_layout(
            title=title,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        
        return fig

def render_plotly_chart(df: pd.DataFrame, chart_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plotly 차트를 JSON으로 렌더링
    
    Args:
        df: 데이터프레임
        chart_context: 차트 설정 (타입, x축, y축 등)
        
    Returns:
        Dict: 차트 JSON 및 관련 정보
    """
    chart_generator = PlotlyChartGenerator()
    
    chart_type = chart_context.get('chart_type', 'bar')
    x_column = chart_context.get('x_column')
    y_columns = chart_context.get('y_columns', [])
    title = chart_context.get('title', '차트')
    
    if isinstance(y_columns, str):
        y_columns = [y_columns]
    
    fig = None
    
    try:
        if chart_type == 'bar':
            fig = chart_generator.generate_bar_chart(df, x_column, y_columns, title)
        elif chart_type == 'line':
            fig = chart_generator.generate_line_chart(df, x_column, y_columns, title)
        elif chart_type == 'scatter':
            fig = chart_generator.generate_scatter_chart(df, x_column, y_columns, title)
        elif chart_type == 'pie' and len(y_columns) > 0:
            fig = chart_generator.generate_pie_chart(df, x_column, y_columns[0], title)
        elif chart_type == 'heatmap':
            fig = chart_generator.generate_heatmap(df, title)
        else:
            # 지원하지 않는 차트 타입이거나 데이터가 부적합한 경우
            fig = chart_generator.generate_fallback_chart(df, f"{title} (미리보기)")
            
        # Plotly 차트를 JSON으로 변환
        chart_json = fig.to_json()
        
        return {
            'chart_json': chart_json,
            'chart_type': chart_type,
            'title': title
        }
        
    except Exception as e:
        logger.error(f"Plotly 차트 생성 중 오류: {str(e)}")
        # 오류 발생 시 빈 차트 반환
        fig = go.Figure()
        fig.update_layout(
            title=f"차트 생성 오류: {str(e)}",
            annotations=[
                dict(
                    text="데이터를 시각화할 수 없습니다",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5
                )
            ]
        )
        return {
            'chart_json': fig.to_json(),
            'chart_type': 'error',
            'error': str(e)
        } 