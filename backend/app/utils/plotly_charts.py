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
            ),
            # 타이틀 설정
            title={
                'text': fig.layout.title.text,
                'font': {
                    'family': 'Pretendard, sans-serif',
                    'size': 18,
                    'color': 'white'
                },
                'xanchor': 'center',
                'x': 0.5,
                'yanchor': 'top',
                'y': 0.95,
            }
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
    
    def _prepare_d3_data(self, fig):
        """Plotly 차트 데이터를 D3.js에서 사용할 수 있는 형식으로 변환"""
        try:
            d3_data = {
                'type': fig.data[0].type if len(fig.data) > 0 else 'bar',
                'series': [],
                'layout': {
                    'title': fig.layout.title.text if hasattr(fig.layout.title, 'text') else '',
                    'xaxis': {
                        'title': fig.layout.xaxis.title.text if hasattr(fig.layout.xaxis, 'title') else '',
                    },
                    'yaxis': {
                        'title': fig.layout.yaxis.title.text if hasattr(fig.layout.yaxis, 'title') else '',
                    }
                }
            }
            
            # 차트 유형별로 데이터 변환
            for trace in fig.data:
                series = {
                    'name': trace.name if hasattr(trace, 'name') else '',
                    'color': trace.marker.color if hasattr(trace, 'marker') and hasattr(trace.marker, 'color') else None
                }
                
                # X, Y 데이터 추출 (차트 유형별로 다름)
                if hasattr(trace, 'x') and hasattr(trace, 'y'):
                    series['x'] = trace.x.tolist() if hasattr(trace.x, 'tolist') else trace.x
                    series['y'] = trace.y.tolist() if hasattr(trace.y, 'tolist') else trace.y
                elif hasattr(trace, 'values') and hasattr(trace, 'labels'):  # 파이 차트
                    series['values'] = trace.values.tolist() if hasattr(trace.values, 'tolist') else trace.values
                    series['labels'] = trace.labels.tolist() if hasattr(trace.labels, 'tolist') else trace.labels
                
                d3_data['series'].append(series)
            
            return json.dumps(d3_data)  # JSON 문자열로 변환
        except Exception as e:
            logger.error(f"D3 데이터 변환 오류: {str(e)}")
            return json.dumps({'error': '데이터 변환 실패'})
    
    def generate_bar_chart(self, df: pd.DataFrame, x: str, y: Union[str, List[str]], title: str, colors: List[str] = None) -> go.Figure:
        """막대 차트 생성"""
        # 사용자 정의 색상 사용 또는 기본 색상 사용
        chart_colors = colors if colors else VIRIDIS_COLORS
        
        if isinstance(y, list) and len(y) > 1:
            # 여러 y 값에 대한 그룹화된 막대 차트
            fig = go.Figure()
            
            for i, y_col in enumerate(y):
                fig.add_trace(go.Bar(
                    x=df[x],
                    y=df[y_col],
                    name=y_col,
                    marker_color=chart_colors[i % len(chart_colors)]
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
                color_discrete_sequence=chart_colors
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
    
    def generate_line_chart(self, df: pd.DataFrame, x: str, y: Union[str, List[str]], title: str, colors: List[str] = None) -> go.Figure:
        """선 차트 생성"""
        # 사용자 정의 색상 사용 또는 기본 색상 사용
        chart_colors = colors if colors else PLASMA_COLORS
        
        fig = px.line(
            df, 
            x=x, 
            y=y,
            title=title,
            color_discrete_sequence=chart_colors
        )
        
        # 마커 추가
        for trace in fig.data:
            trace.update(mode='lines+markers')
            
        return self._apply_common_styles(fig)
    
    def generate_scatter_chart(self, df: pd.DataFrame, x: str, y: Union[str, List[str]], title: str, colors: List[str] = None) -> go.Figure:
        """산점도 생성"""
        # 사용자 정의 색상 사용 또는 기본 색상 사용
        chart_colors = colors if colors else PLASMA_COLORS
        
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
                        color=chart_colors[i % len(chart_colors)]
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
                color_discrete_sequence=chart_colors
            )
            
            # 마커 크기 조정
            fig.update_traces(marker=dict(size=10))
            
        return self._apply_common_styles(fig)
    
    def generate_pie_chart(self, df: pd.DataFrame, labels: str, values: str, title: str, colors: List[str] = None) -> go.Figure:
        """파이 차트 생성"""
        # 사용자 정의 색상 사용 또는 기본 색상 사용
        chart_colors = colors if colors else VIRIDIS_COLORS
        
        fig = px.pie(
            df, 
            names=labels, 
            values=values,
            title=title,
            color_discrete_sequence=chart_colors
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
    """차트 컨텍스트 정보를 기반으로 Plotly 차트 생성"""
    try:
        chart_type = chart_context.get('chart_type', 'bar')
        title = chart_context.get('title', '차트')
        x_column = chart_context.get('x_column')
        y_columns = chart_context.get('y_columns', [])
        colors = chart_context.get('colors')
        
        # 로그 추가
        logger.info(f"차트 생성 시작: 타입={chart_type}, 제목={title}, X={x_column}, Y={y_columns}")
        
        # 입력 검증
        if not x_column or not y_columns:
            logger.error(f"차트 생성 실패: x_column={x_column}, y_columns={y_columns}")
            return {"error": "차트 생성에 필요한 x_column 또는 y_columns가 없습니다."}
        
        # DataFrame 검증
        if df is None or df.empty:
            logger.error("차트 생성 실패: DataFrame이 비어있거나 None입니다.")
            return {"error": "차트 생성에 필요한 데이터가 없습니다."}
            
        # 컬럼 존재 여부 확인
        if x_column not in df.columns:
            logger.error(f"차트 생성 실패: x_column '{x_column}'이 DataFrame에 존재하지 않습니다.")
            return {"error": f"지정한 X 컬럼({x_column})이 데이터에 존재하지 않습니다."}
            
        # y_columns 검증
        valid_y_columns = []
        for y_col in y_columns:
            if y_col in df.columns:
                valid_y_columns.append(y_col)
            else:
                logger.warning(f"Y 컬럼({y_col})이 DataFrame에 존재하지 않아 무시됩니다.")
                
        if not valid_y_columns:
            logger.error("차트 생성 실패: 유효한 Y 컬럼이 없습니다.")
            return {"error": "차트 생성에 필요한 유효한 Y 컬럼이 없습니다."}
        
        # y_columns 업데이트    
        y_columns = valid_y_columns
        
        # 차트 생성기 초기화
        chart_generator = PlotlyChartGenerator()
        
        # 차트 유형에 따라 적절한 생성 함수 호출
        if chart_type == 'bar':
            fig = chart_generator.generate_bar_chart(df, x_column, y_columns, title, colors)
        elif chart_type == 'line':
            fig = chart_generator.generate_line_chart(df, x_column, y_columns, title, colors)
        elif chart_type == 'scatter':
            fig = chart_generator.generate_scatter_chart(df, x_column, y_columns, title, colors)
        elif chart_type == 'pie' and len(y_columns) > 0:
            fig = chart_generator.generate_pie_chart(df, x_column, y_columns[0], title, colors)
        elif chart_type == 'heatmap':
            fig = chart_generator.generate_heatmap(df, title)
        else:
            # 지원하지 않는 차트 유형 또는 오류 상황에서 기본 차트 생성
            logger.warning(f"지원하지 않는 차트 유형: {chart_type}, 기본 차트로 대체합니다.")
            fig = chart_generator.generate_fallback_chart(df, f"{title} (지원하지 않는 차트 유형)")
        
        # 타이틀 처리 - 문자열 타입과 길이 확인
        if fig.layout.title and hasattr(fig.layout.title, 'text'):
            if fig.layout.title.text is None:
                fig.layout.title.text = "차트"  # 기본 타이틀 설정
            elif not isinstance(fig.layout.title.text, str):
                fig.layout.title.text = str(fig.layout.title.text)  # 문자열로 변환
            # 타이틀 길이 제한
            if len(fig.layout.title.text) > 50:
                fig.layout.title.text = fig.layout.title.text[:47] + "..."
                
        # JSON으로 변환 - 안전한 방식 사용
        try:
            # plotly.utils 사용 (권장)
            from plotly.utils import PlotlyJSONEncoder
            chart_data = json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)
            logger.info(f"차트 JSON 변환 성공 (PlotlyJSONEncoder 사용)")
        except Exception as e:
            logger.error(f"Plotly JSON 변환 오류 (to_dict): {str(e)}")
            # 대체 방법
            try:
                import plotly.io as pio
                chart_data = pio.to_json(fig)
                logger.info(f"차트 JSON 변환 성공 (pio.to_json 사용)")
            except Exception as e2:
                logger.error(f"Plotly JSON 변환 오류 (pio.to_json): {str(e2)}")
                return {"error": "차트 데이터를 JSON으로 변환할 수 없습니다."}
        
        # D3 데이터 별도 생성
        try:
            d3_data = chart_generator._prepare_d3_data(fig)
            logger.info(f"D3 데이터 변환 성공")
        except Exception as e:
            logger.error(f"D3 데이터 변환 오류: {str(e)}")
            d3_data = json.dumps({'error': 'D3 데이터 변환 실패'})
        
        # 결과 반환
        return {
            'chart_json': chart_data,
            'd3_data': d3_data,
            'config': json.dumps({
                'editable': True,
                'displayModeBar': True,
                'responsive': True
            })
        }
        
    except Exception as e:
        logger.error(f"차트 생성 중 오류 발생: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": f"차트 생성 중 오류 발생: {str(e)}"} 