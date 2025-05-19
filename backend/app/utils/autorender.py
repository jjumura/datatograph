import matplotlib
matplotlib.use('Agg')  # GUI 없는 백엔드 설정 - 성능 향상

# 하위 호환성을 위한 임포트 (type annotation 용)
import matplotlib.pyplot as plt
import matplotlib.axes

import numpy as np
import pandas as pd
import uuid
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
import logging
import os
import re
import asyncio

logger = logging.getLogger(__name__)

# 폰트 경로 정의
FONT_FAMILY_NAME = "Pretendard"
FONT_PATH = "C:/Project_A/font/Pretendard-Regular.ttf"
FONT_PATH_EXTRABOLD = "C:/Project_A/font/Pretendard-ExtraBold.ttf"
FONT_PATH_SEMIBOLD = "C:/Project_A/font/Pretendard-SemiBold.ttf"
FONT_PATH_LIGHT = "C:/Project_A/font/Pretendard-Light.ttf"  # Light 폰트 추가

# 전역 폰트 변수 정의
font_prop = None
font_prop_extrabold = None
font_prop_semibold = None
font_prop_light = None  # Light 폰트 변수 추가

# 폰트 초기화 여부 추적
fonts_initialized = False

# 폰트 초기화 함수 - 지연 로딩 구현
def initialize_fonts():
    global fonts_initialized, FONT_FAMILY_NAME, font_prop, font_prop_extrabold, font_prop_semibold, font_prop_light
    
    if fonts_initialized:
        return
    
    # matplotlib의 font_manager 지연 임포트
    import matplotlib.font_manager as fm
    import matplotlib.pyplot as plt
    
    try:
        expected_font_path = FONT_PATH
        logger.info(f"폰트 초기화 시작: {expected_font_path}")
        
        if os.path.isfile(expected_font_path):
            logger.info(f"폰트 파일 '{expected_font_path}' 존재 확인됨.")
            font_prop = fm.FontProperties(fname=expected_font_path)
            
            # 폰트 매니저에 폰트 추가
            fm.fontManager.addfont(expected_font_path)
            
            # ExtraBold 폰트 추가
            if os.path.isfile(FONT_PATH_EXTRABOLD):
                fm.fontManager.addfont(FONT_PATH_EXTRABOLD)
                font_prop_extrabold = fm.FontProperties(fname=FONT_PATH_EXTRABOLD)
            else:
                logger.warning(f"ExtraBold 폰트 파일 없음: {FONT_PATH_EXTRABOLD}")
                font_prop_extrabold = None
                
            # SemiBold 폰트 추가
            if os.path.isfile(FONT_PATH_SEMIBOLD):
                fm.fontManager.addfont(FONT_PATH_SEMIBOLD)
                font_prop_semibold = fm.FontProperties(fname=FONT_PATH_SEMIBOLD)
            else:
                logger.warning(f"SemiBold 폰트 파일 없음: {FONT_PATH_SEMIBOLD}")
                font_prop_semibold = None
                
            # Light 폰트 추가
            if os.path.isfile(FONT_PATH_LIGHT):
                fm.fontManager.addfont(FONT_PATH_LIGHT)
                font_prop_light = fm.FontProperties(fname=FONT_PATH_LIGHT)
            else:
                logger.warning(f"Light 폰트 파일 없음: {FONT_PATH_LIGHT}")
                font_prop_light = None
            
            # 폰트 설정 적용
            plt.rcParams['font.family'] = [FONT_FAMILY_NAME]
            plt.rcParams['font.sans-serif'] = [FONT_FAMILY_NAME] + plt.rcParams['font.sans-serif']
            plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
        else:
            logger.warning(f"폰트 파일 '{expected_font_path}' 없음. 대체 폰트 사용.")
            FONT_FAMILY_NAME = "sans-serif"  # fallback
            font_prop_extrabold = None
            font_prop_semibold = None
            font_prop_light = None  # Light 폰트 초기화
    except Exception as e:
        logger.error(f"폰트 설정 중 오류 발생: {e}")
        FONT_FAMILY_NAME = "sans-serif"  # fallback
        font_prop_extrabold = None
        font_prop_semibold = None
        font_prop_light = None  # Light 폰트 초기화
    
    fonts_initialized = True
    logger.info("폰트 초기화 완료")

# 폰트가 필요할 때만 초기화 호출하는 함수
def ensure_fonts_initialized():
    if not fonts_initialized:
        initialize_fonts()

# --- Design Tokens (이미지 비율 참고) ---
COLOR_BACKGROUND_DARK = '#10131a'  # 배경색 더 어둡게
COLOR_TEXT_LIGHT = '#FFFFFF'  # 텍스트 완전 흰색으로
COLOR_TEXT_MUTED = '#CCCCCC'  # 연한 텍스트도 더 밝게
COLOR_GRID_VERY_LIGHT = '#2a2e36'  # 배경과 더 조화로운 그리드 색상
COLOR_SPINE_LIGHT = '#44485A'

# --- Elm Colormaps by Chart Type (https://package.elm-lang.org/packages/2mol/elm-colormaps/latest/) ---
# 더 밝고 명확한 대비의 색상으로 업데이트
ELM_BAR_COLORS = ['#6345FF', '#8C66FF', '#4091e0', '#33d1b5', '#c9f584', '#fcffa4']  # 더 밝게
ELM_LINE_COLORS = ['#2a0887', '#5221b0', '#9a26a6', '#d85189', '#ff7d67', '#ffc178']
ELM_SCATTER_COLORS = ['#4152d0', '#5189d5', '#8fc1e5', '#beebfa', '#e0f3f8', '#febd61']
ELM_PIE_COLORS = ['#5d01aa', '#5558c1', '#3aa7c0', '#52d6ab', '#a2ea7a', '#f7f959']

FONT_FAMILY_MAIN = FONT_FAMILY_NAME

# --- 기본 크기 및 비율 설정 ---
BASE_FIGURE_WIDTH = 12  # 기준 너비 증가 (10 -> 12)
BASE_FIGURE_HEIGHT = 8  # 기준 높이 증가 (7 -> 8)
BASE_DPI = 150          # 기준 DPI 증가 (100 -> 150)

# 폰트 크기 비율 정의 (figure 크기 대비) - 사용자 요청에 따라 크기 증가
TITLE_FONT_RATIO = 0.12      # 제목 폰트 크기 비율 더 증가 (0.1 -> 0.12)
LABEL_FONT_RATIO = 0.12     # 타이틀 크기와 값(%) 라벨 크기 동일하게 설정
AXIS_LABEL_FONT_RATIO = 0.064  # 축 라벨은 메인 라벨(타이틀)의 80% 크기로 조정
TICK_FONT_RATIO = 0.04      # 눈금 폰트 크기 비율 증가 (0.03 -> 0.04)
LEGEND_FONT_RATIO = 0.035   # 범례 폰트 크기 비율 증가 (0.022 -> 0.035)

# 폰트 크기 계산 함수
def calc_font_size(ratio, fig_width, fig_height):
    # 그림 대각선 길이를 기준으로 폰트 크기 계산하되, 가중치 증가
    diagonal = (fig_width**2 + fig_height**2)**0.5
    # 분모를 15에서 10으로 줄여 더 크게 만듦
    return ratio * diagonal * BASE_DPI / 10

# 기존 상수 값도 유지 (하위 호환성)
FONT_SIZE_BASE = 11
FONT_SIZE_TITLE = 18
FONT_SIZE_LABEL = 13
FONT_SIZE_TICK = 12
FONT_WEIGHT_NORMAL = 'normal'
FONT_WEIGHT_SEMIBOLD = 'semibold'  # 세미볼드 폰트 추가

FIGURE_SIZE_DEFAULT = (BASE_FIGURE_WIDTH, BASE_FIGURE_HEIGHT)
BAR_WIDTH_RATIO = 0.4  # 더 얇은 바 (0.5 -> 0.4)
TITLE_PAD = 35         # 타이틀 패딩 더 증가 (30→35)
LABEL_PAD = 25         # 라벨 패딩 더 증가 (18→25)
LEGEND_BBOX_Y = -0.25  # 범례 여백 더 증가 (-0.22→-0.25)
# --- End Design Tokens ---

class ChartQA:
    """차트 품질 검사를 위한 클래스"""

    @staticmethod
    def check_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
        """데이터 품질 검사를 수행합니다."""
        return {
            "missing_values": df.isnull().sum().to_dict(),
            "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object']).columns.tolist(),
            "row_count": len(df),
            "column_count": len(df.columns)
        }

    @staticmethod
    def validate_chart_params(df: pd.DataFrame, chart_type: str, x: str, y: List[str]) -> Tuple[bool, str]:
        """차트 파라미터의 유효성을 검사합니다."""
        if x not in df.columns:
            return False, f"X축 컬럼 '{x}'이(가) 데이터프레임에 없습니다."
        for col in y:
            if col not in df.columns:
                return False, f"Y축 컬럼 '{col}'이(가) 데이터프레임에 없습니다."
        if chart_type not in ["line", "bar", "scatter", "pie"]:
            return False, f"지원하지 않는 차트 타입입니다: {chart_type}"
        return True, "유효성 검사 통과"

class ChartGenerator:
    """차트 생성을 담당하는 클래스"""

    def __init__(self, fig_width=BASE_FIGURE_WIDTH, fig_height=BASE_FIGURE_HEIGHT, dpi=BASE_DPI):
        # matplotlib 지연 로딩
        import matplotlib.pyplot as plt
        
        # 폰트가 필요할 때만 초기화
        ensure_fonts_initialized()
        
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # 해상도에 따른 폰트 크기 계산
        self.fig_width = fig_width
        self.fig_height = fig_height
        self.dpi = dpi * 2.5  # DPI 더 증가 (2배 -> 2.5배)
        
        # 폰트 크기 계산 - 타이틀과 값(%) 라벨 동일하게 설정
        title_font_size = calc_font_size(TITLE_FONT_RATIO, fig_width, fig_height)
        self.font_size_title = max(title_font_size, 56)  # 최소 56pt로 증가 (48 -> 56)
        self.font_size_percent = self.font_size_title  # 타이틀과 '값(%)' 라벨 동일 크기
        
        # x,y축 라벨은 타이틀(메인 라벨)의 80% 크기로 설정
        axis_label_size = calc_font_size(AXIS_LABEL_FONT_RATIO, fig_width, fig_height)
        self.font_size_label = max(axis_label_size, int(self.font_size_title * 0.8))
        
        # 기타 폰트 크기 계산
        self.font_size_tick = max(calc_font_size(TICK_FONT_RATIO, fig_width, fig_height), 32)
        self.font_size_legend = max(calc_font_size(LEGEND_FONT_RATIO, fig_width, fig_height), 28)
        
        logger.info(f"폰트 크기 설정: 제목/값(%)={self.font_size_title}, 축라벨={self.font_size_label}, "
                   f"눈금={self.font_size_tick}, 범례={self.font_size_legend}")
        
        plt.rcParams.update({
            'figure.facecolor': COLOR_BACKGROUND_DARK,
            'axes.facecolor': COLOR_BACKGROUND_DARK,
            'text.color': COLOR_TEXT_LIGHT,
            'axes.labelcolor': COLOR_TEXT_LIGHT,  # 모든 라벨 색상 밝게 변경 (MUTED -> LIGHT)
            'xtick.color': COLOR_TEXT_LIGHT,
            'ytick.color': COLOR_TEXT_LIGHT,
            'axes.edgecolor': COLOR_SPINE_LIGHT,
            'grid.color': COLOR_GRID_VERY_LIGHT,
            'legend.facecolor': COLOR_BACKGROUND_DARK,
            'legend.edgecolor': COLOR_BACKGROUND_DARK,
            'legend.labelcolor': COLOR_TEXT_LIGHT,
            'font.size': self.font_size_tick,  # 기본 폰트 크기
            'axes.titlesize': self.font_size_title,
            'axes.labelsize': self.font_size_label,
            'xtick.labelsize': self.font_size_tick,
            'ytick.labelsize': self.font_size_tick,
            'legend.fontsize': self.font_size_legend,
            'axes.titleweight': 'bold',  # 타이틀 weight 강화
            'axes.labelweight': 'bold',  # 라벨 weight 강화
            'font.family': FONT_FAMILY_MAIN,
            'figure.dpi': self.dpi,
        })
        if FONT_FAMILY_NAME:
            plt.rcParams['font.family'] = FONT_FAMILY_NAME
        # 축선 숨기기
        plt.rcParams['axes.spines.top'] = False
        plt.rcParams['axes.spines.right'] = False
        plt.rcParams['axes.spines.left'] = False
        plt.rcParams['axes.spines.bottom'] = False
        
        # 차트 타입별 Elm 컬러맵 설정
        self.color_palettes = {
            'bar': ELM_BAR_COLORS,
            'line': ELM_LINE_COLORS,
            'scatter': ELM_SCATTER_COLORS,
            'pie': ELM_PIE_COLORS
        }
        logger.info(f"차트 생성기 초기화 완료 (컬러맵 설정)")

    def _apply_common_styles(self, ax: Union[plt.Axes, matplotlib.axes.Axes], title: str, x_label: str, y_label: str, y_columns: list):
        # matplotlib 임포트 확인
        import matplotlib.pyplot as plt
        
        # 타이틀에 ExtraBold 폰트 적용 및 크기 증가 - 값(%) 라벨과 동일한 크기
        if font_prop_extrabold:
            ax.set_title(title, fontsize=self.font_size_title, color=COLOR_TEXT_LIGHT, 
                        pad=TITLE_PAD+5, fontproperties=font_prop_extrabold)  # 패딩 추가
        else:
            ax.set_title(title, fontsize=self.font_size_title, color=COLOR_TEXT_LIGHT, 
                       pad=TITLE_PAD+5, fontweight='bold')  # 패딩 추가
            
        # X축 라벨 - 타이틀의 80% 크기로 설정
        if x_label:
            ax.set_xlabel(x_label, fontsize=self.font_size_label, color=COLOR_TEXT_LIGHT, 
                         labelpad=LABEL_PAD, fontweight='bold')
                         
        # Y축 라벨 처리 강화
        if y_label == "값(%)" or "매출" in y_label:
            # 값(%) 라벨은 타이틀과 같은 크기로 표시 (사용자 요청)
            y_label_fontsize = self.font_size_percent  # 타이틀과 동일 크기
            y_label_color = COLOR_TEXT_LIGHT
            
            # Y축 라벨 위치 및 회전 조정 - 확실하게 보이도록
            ax.set_ylabel(y_label, fontsize=y_label_fontsize, color=y_label_color, 
                         labelpad=LABEL_PAD+10, fontweight='bold',  # 여백 더 추가
                         rotation=90, ha='center', va='center')  # 수직 정렬 및 정중앙 배치
            
            # 라벨 위치 확인 및 조정 - 더 여백 추가
            ax.yaxis.set_label_coords(-0.11, 0.5)  # X축 좌표를 더 왼쪽으로 (-0.09 -> -0.11)
        else:
            # 일반 Y축 라벨 - 타이틀의 80% 크기
            ax.set_ylabel(y_label, fontsize=self.font_size_label, color=COLOR_TEXT_LIGHT, 
                         labelpad=LABEL_PAD, fontweight='bold')
        
        # 그리드 스타일 개선 - 더 선명한 구분선
        ax.grid(True, axis='y', linestyle='-', alpha=0.15, color=COLOR_TEXT_LIGHT, linewidth=0.7)
        ax.grid(False, axis='x')
        
        # 범례 스타일 수정 - 여백 추가하여 겹침 방지
        if len(y_columns) > 0:
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                try:
                    # 범례 색상 막대기 높이에 맞춘 텍스트 크기 계산
                    # 기본 폰트 크기의 90%로 설정 (색상 막대기 비율에 맞게)
                    legend_text_size = self.font_size_legend * 0.9
                    
                    legend = ax.legend(
                        handles, labels,
                        loc='lower center',
                        bbox_to_anchor=(0.5, LEGEND_BBOX_Y),
                        ncol=min(len(y_columns), 4),
                        frameon=False,
                        fontsize=legend_text_size,  # 조정된 폰트 크기 적용
                        labelcolor=COLOR_TEXT_LIGHT,
                        labelspacing=1.3
                    )
                    
                    # 범례 텍스트 Light 폰트 적용 및 크기 조정
                    if legend and font_prop_light:
                        for text in legend.get_texts():
                            text.set_fontproperties(font_prop_light)  # Light 폰트 적용
                    # Light 폰트 없을 경우 굵기만 조정
                    elif legend:
                        for text in legend.get_texts():
                            text.set_fontweight('light')
                except Exception as e:
                    logger.warning(f"범례 설정 중 오류 발생: {e}")
                    # 오류 발생 시 더 간단한 범례 스타일 적용
                    try:
                        ax.legend(
                            handles, labels,
                            loc='lower center',
                            bbox_to_anchor=(0.5, LEGEND_BBOX_Y),
                            ncol=min(len(y_columns), 4),
                            frameon=False,
                            fontsize=self.font_size_legend
                        )
                    except Exception as e2:
                        logger.error(f"기본 범례 설정도 실패: {e2}")

    def generate_line_chart(self, df, x, y, title):
        # matplotlib 임포트
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(self.fig_width, self.fig_height), constrained_layout=True, dpi=self.dpi)
        colors = self.color_palettes['line']
        for i, col in enumerate(y):
            ax.plot(df[x], df[col], label=col, marker='o', color=colors[i % len(colors)])
        self._apply_common_styles(ax, title, x, "값", y)
        fig.tight_layout()
        logger.info(f"라인 차트 생성 완료 (Elm 컬러맵 적용: {colors})")
        return fig

    def generate_bar_chart(self, df, x, y, title):
        # matplotlib 임포트
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(self.fig_width, self.fig_height), constrained_layout=True, dpi=self.dpi)
        num_x_values = len(df[x])
        x_pos = np.arange(num_x_values)
        bottom_values = np.zeros(num_x_values)
        
        # 데이터 기반 막대 폭 동적 계산
        bar_width = self.calc_bar_width(num_x_values, self.fig_width)
        
        colors = self.color_palettes['bar']
        bars_list = []
        
        # 2022_매출과 2023_매출 같은 특정 패턴 감지를 위한 정규식
        year_pattern = re.compile(r'(\d{4})[\s_]*(매출|판매|실적)')
        
        # 연도별 데이터 자동 인식 및 색상 할당
        custom_colors = []
        year_matches = [year_pattern.search(col) for col in y]
        
        if len(y) == 2 and all(year_matches) and year_matches[0] and year_matches[1]:
            # 두 연도간 비교 데이터 감지됨 - 색상 커스터마이징
            year1, year2 = year_matches[0].group(1), year_matches[1].group(1)
            # 최신 연도와 이전 연도 판별
            if int(year1) > int(year2):
                custom_colors = ['#6550E0', '#2D1876']  # 최신(밝은색), 이전(어두운색)
            else:
                custom_colors = ['#2D1876', '#6550E0']  # 이전(어두운색), 최신(밝은색)
        
        for i, col in enumerate(y):
            # 커스텀 색상이 있으면 사용, 없으면 기본 색상 팔레트 사용
            color = custom_colors[i] if custom_colors else colors[i % len(colors)]
            
            # 막대 테두리 추가하여 대비 강화 
            bars = ax.bar(x_pos, df[col], bar_width, label=col, bottom=bottom_values, 
                   color=color, 
                   edgecolor='#000000',  # 검은색 테두리
                   linewidth=1.0,      # 테두리 두께 강화
                   alpha=0.95)          # 투명도 감소 (더 선명하게)
            bars_list.append(bars)
            bottom_values += df[col].fillna(0).values
        
        # 이미지 스타일 적용 - x축 레이블 회전
        if num_x_values > 5:
            # 많은 데이터 포인트일 때 45도 회전 (첨부된 이미지 스타일)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(df[x], rotation=45, ha="right", fontsize=self.font_size_tick)
        else:
            # 적은 데이터 포인트일 때 수직 표시
            ax.set_xticks(x_pos)
            ax.set_xticklabels(df[x], rotation=0, ha="center", fontsize=self.font_size_tick)
        
        # Y축 눈금 강조
        for label in ax.get_yticklabels():
            label.set_fontweight('bold')
            label.set_fontsize(self.font_size_tick)
        
        self._apply_common_styles(ax, title, "", "값(%)", y)
        
        # 차트에 격자선 추가
        ax.grid(True, axis='y', linestyle='-', alpha=0.15, color=COLOR_TEXT_LIGHT, linewidth=0.7)
        ax.grid(False, axis='x')
        
        # y축 범위 조정
        y_min, y_max = ax.get_ylim()
        if y_min < 0 and y_max > 0:  # 양수와 음수가 모두 있는 경우
            # 음수와 양수 데이터 모두 있을 때 균형 있게 표시
            max_abs = max(abs(y_min), abs(y_max))
            ax.set_ylim(-max_abs*1.2, max_abs*1.2)
        else:
            # 한쪽으로만 치우친 데이터일 때 여유 공간 추가
            if y_min >= 0:  # 모두 양수
                ax.set_ylim(0, y_max*1.2)  # 여유 공간 더 추가 (1.15 -> 1.2)
            else:  # 모두 음수
                ax.set_ylim(y_min*1.2, 0)  # 여유 공간 더 추가 (1.15 -> 1.2)
        
        # 차트 하단 범례 강화 - 겹침 방지 마진 추가
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            try:
                # 범례 색상 막대기 높이에 맞춘 텍스트 크기 계산
                legend_text_size = self.font_size_legend * 0.9
                
                legend = ax.legend(
                    handles, labels,
                    loc='lower center',
                    bbox_to_anchor=(0.5, LEGEND_BBOX_Y),
                    ncol=min(len(y), 4),
                    frameon=False,
                    fontsize=legend_text_size,  # 조정된 폰트 크기 적용
                    labelcolor=COLOR_TEXT_LIGHT,
                    labelspacing=1.3
                )
                
                # 범례 텍스트 Light 폰트 적용 및 크기 조정
                if legend and font_prop_light:
                    for text in legend.get_texts():
                        text.set_fontproperties(font_prop_light)  # Light 폰트 적용
                # Light 폰트 없을 경우 굵기만 조정
                elif legend:
                    for text in legend.get_texts():
                        text.set_fontweight('light')
            except Exception as e:
                logger.warning(f"범례 설정 중 오류 발생: {e}")
                # 오류 발생 시 더 간단한 범례 스타일 적용
                try:
                    ax.legend(
                        handles, labels,
                        loc='lower center',
                        bbox_to_anchor=(0.5, LEGEND_BBOX_Y),
                        ncol=min(len(y), 4),
                        frameon=False,
                        fontsize=self.font_size_legend
                    )
                except Exception as e2:
                    logger.error(f"기본 범례 설정도 실패: {e2}")
        
        fig.tight_layout()
        logger.info(f"막대 차트 생성 완료 (동적 막대 폭: {bar_width}, 데이터 포인트 수: {num_x_values})")
        return fig

    def generate_scatter_chart(self, df, x, y, title):
        # matplotlib 임포트
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(self.fig_width, self.fig_height), constrained_layout=True, dpi=self.dpi)
        colors = self.color_palettes['scatter']
        for i, col in enumerate(y):
            ax.scatter(df[x], df[col], label=col, alpha=0.7, color=colors[i % len(colors)])
        self._apply_common_styles(ax, title, x, "값", y)
        fig.tight_layout()
        logger.info(f"산점도 생성 완료 (Elm 컬러맵 적용: {colors})")
        return fig

    def generate_pie_chart(self, df, x, y, title):
        # matplotlib 임포트
        import matplotlib.pyplot as plt
        
        try:
            fig, ax = plt.subplots(figsize=(self.fig_width, self.fig_height), constrained_layout=True, dpi=self.dpi)
            y_col = y[0]
            colors = self.color_palettes['pie']
            color_list = [colors[i % len(colors)] for i in range(len(df[x]))]
            
            wedges, texts, autotexts = ax.pie(
                df[y_col],
                labels=None,
                autopct='%1.1f%%',
                startangle=90,
                colors=color_list,
                pctdistance=0.85,
                wedgeprops={'edgecolor': COLOR_BACKGROUND_DARK, 'linewidth': 1.5}
            )
            
            for autotext in autotexts:
                autotext.set_color(COLOR_TEXT_LIGHT)
                autotext.set_fontsize(self.font_size_tick)
                autotext.set_fontweight(FONT_WEIGHT_NORMAL)
            
            if font_prop_extrabold:
                ax.set_title(title, fontsize=self.font_size_title, color=COLOR_TEXT_LIGHT, 
                            pad=TITLE_PAD, fontproperties=font_prop_extrabold)
            else:
                ax.set_title(title, fontsize=self.font_size_title, color=COLOR_TEXT_LIGHT, 
                           pad=TITLE_PAD, fontweight='bold')
                
            # 범례 처리 부분 - try-except로 감싸서 오류 방지
            try:
                # 범례 색상 막대기 높이에 맞춘 텍스트 크기 계산
                legend_text_size = self.font_size_legend * 0.9
                
                legend = ax.legend(
                    wedges, df[x],
                    title=x,
                    loc="center left",
                    bbox_to_anchor=(1, 0, 0.5, 1),
                    fontsize=legend_text_size,
                    labelcolor=COLOR_TEXT_LIGHT
                )
                
                # 범례 텍스트에 Light 폰트 적용
                if legend:
                    # 범례 제목 스타일 설정 (있을 경우에만)
                    if legend.get_title():
                        legend.get_title().set_color(COLOR_TEXT_LIGHT)
                    
                    # 범례 텍스트에 Light 폰트 적용
                    if font_prop_light:
                        for text in legend.get_texts():
                            text.set_fontproperties(font_prop_light)
                    else:
                        for text in legend.get_texts():
                            text.set_fontweight('light')
            except Exception as e:
                logger.warning(f"파이 차트 범례 설정 중 오류 발생: {e}")
                # 간단한 범례 설정으로 재시도
                try:
                    ax.legend(
                        wedges, df[x],
                        loc="center left",
                        bbox_to_anchor=(1, 0, 0.5, 1),
                        fontsize=self.font_size_legend
                    )
                except Exception as e2:
                    logger.error(f"파이 차트 기본 범례 설정도 실패: {e2}")
            
            ax.axis('equal')
        except Exception as e:
            logger.error(f"파이 차트 생성 중 오류 발생: {e}")
            # 오류 발생 시 기본 텍스트 표시
            ax.text(0.5, 0.5, f"차트 생성 실패: {str(e)[:50]}...", 
                   ha='center', va='center', color=COLOR_TEXT_LIGHT,
                   fontsize=self.font_size_label)
            ax.axis('off')
            
        fig.tight_layout()
        logger.info(f"파이 차트 생성 완료 (Elm 컬러맵 적용: {colors})")
        return fig

    def generate_fallback_chart(self, df: pd.DataFrame, title: str = "데이터 미리보기") -> plt.Figure:
        # matplotlib 임포트
        import matplotlib.pyplot as plt
        
        try:
            # 간소화된 fallback 차트 (테이블 형태)
            fig, ax = plt.subplots(figsize=(10, max(4, len(df) * 0.5)), constrained_layout=True, dpi=self.dpi)
            ax.axis('off')
            ax.axis('tight')
            
            # 데이터 미리보기 준비
            table_data = []
            num_preview_rows = min(10, len(df))
            for i in range(num_preview_rows):
                table_data.append([str(x)[:30] for x in df.iloc[i]])
                
            # 테이블 생성
            try:
                table = ax.table(cellText=table_data,
                             colLabels=df.columns,
                             loc='center',
                             cellLoc='left')
                
                # 테이블 스타일 - 최소한의 스타일만 적용
                table.auto_set_font_size(False)
                table.set_fontsize(self.font_size_tick)
                table.scale(1.2, 1.2)
                
                # 셀 스타일링
                for key, cell in table.get_celld().items():
                    cell.set_edgecolor(COLOR_GRID_VERY_LIGHT)
                    if key[0] == 0:  # 헤더 행
                        cell.set_text_props(weight='bold', color=COLOR_TEXT_LIGHT)
                        cell.set_facecolor(COLOR_SPINE_LIGHT)
                    else:  # 데이터 행
                        cell.set_text_props(color=COLOR_TEXT_LIGHT)
                        cell.set_facecolor(COLOR_BACKGROUND_DARK)
            except Exception as table_error:
                logger.error(f"테이블 생성 중 오류 발생: {table_error}")
                # 테이블 생성 실패 시 텍스트만 표시
                ax.text(0.5, 0.5, f"데이터 미리보기 생성 실패\n[{len(df)} 행 x {len(df.columns)} 열]", 
                       ha='center', va='center', color=COLOR_TEXT_LIGHT,
                       fontsize=self.font_size_label)
            
            # 타이틀 설정
            title_text = f"{title}\n(처음 {num_preview_rows}행 미리보기)"
            if font_prop_extrabold:
                ax.set_title(title_text, fontsize=self.font_size_title-2,
                          color=COLOR_TEXT_LIGHT, pad=15,
                          fontproperties=font_prop_extrabold)
            else:
                ax.set_title(title_text, fontsize=self.font_size_title-2,
                          color=COLOR_TEXT_LIGHT, pad=15,
                          fontweight='bold')
            
            # 배경색 설정
            ax.set_facecolor(COLOR_BACKGROUND_DARK)
            fig.patch.set_facecolor(COLOR_BACKGROUND_DARK)
            
            return fig
            
        except Exception as e:
            logger.error(f"fallback 차트 생성 중 오류 발생: {e}")
            # 완전 기본 차트 생성
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f"데이터 미리보기 불가\n오류: {str(e)[:50]}...", 
                   ha='center', va='center', color=COLOR_TEXT_LIGHT,
                   fontsize=14)
            ax.axis('off')
            ax.set_facecolor(COLOR_BACKGROUND_DARK)
            fig.patch.set_facecolor(COLOR_BACKGROUND_DARK)
            return fig

    def calc_bar_width(self, data_points_count, fig_width):
        """
        데이터 포인트 수와 그래프 너비에 따라 적절한 막대 폭 계산
        첨부된 이미지 스타일에 맞게 조정 - 더 좁은 막대 너비 사용 (사용자 요청)
        """
        # 기본 너비 비율 (적은 데이터에서) - 더 좁은 값으로 조정
        base_ratio = 0.55  # 기존 0.7에서 감소
        
        # 데이터 포인트가 많을 때 조정
        if data_points_count <= 5:
            # 적은 데이터 포인트일 때 더 좁은 막대
            ratio = base_ratio * 0.8  # 더 좁게 변경 (기존 1.0에서 감소)
        elif data_points_count <= 10:
            # 중간 개수일 때 약간 줄임
            ratio = base_ratio * 0.7  # 더 좁게 변경 (기존 0.9에서 감소)
        elif data_points_count <= 15:
            # 첨부된 이미지와 비슷한 케이스(15개국)
            ratio = base_ratio * 0.6  # 더 좁게 변경 (기존 0.75에서 감소)
        else:
            # 많은 데이터 포인트일 때 더 좁게
            ratio = base_ratio * 0.5  # 더 좁게 변경 (기존 0.6에서 감소)
        
        # 그래프 너비에 따른 추가 조정
        if fig_width > 12:
            ratio *= 0.9  # 넓은 그래프에서도 막대 폭 줄임 (기존 1.1에서 변경)
        elif fig_width < 8:
            ratio *= 0.8  # 좁은 그래프에서 막대 폭 더 줄임 (기존 0.9에서 변경)
        
        return ratio

async def summarize_title_with_gemini(title: str, max_length: int = 25) -> str:
    """
    Gemini API를 사용하여 차트 타이틀을 핵심 키워드로 요약합니다.
    모든 타이틀에 대해 사용자가 명확하게 인식할 수 있는 짧은 타이틀로 변환합니다.
    """
    # 입력된 title이 None이면 기본값 반환
    if not title:
        return "데이터 시각화"
        
    # "Sheet1" 같은 기본 시트 이름 처리 - 데이터 내용 기반으로 의미 있는 제목 생성
    if title.startswith("Sheet") or title == "데이터 시각화":
        logger.info(f"기본 시트 이름 '{title}' 감지됨 - 의미 있는 제목으로 변환 시도")
        # 시트 이름 대신 현재 데이터 컬럼명에서 제목 유추 시도할 예정
        return "데이터 분석 결과"  # 기본값
        
    # 타이틀이 이미 매우 짧으면(15자 이하) 그대로 반환 - API 호출 절약
    if len(title) <= 15:
        return title
    
    # "지역별 매출 현황"이 포함된 타이틀인 경우 사용자 정의 타이틀 반환 (Gemini API 사용하지 않음)
    if "지역별 매출 현황" in title:
        return "지역별 매출 비교 (2022-2023)"
    
    try:
        # Gemini API 지연 임포트 - 필요할 때만 로드
        try:
            from app.utils.gemini_handler import get_gemini_response
        except ImportError:
            logger.warning("Gemini API 모듈을 임포트할 수 없습니다. 간단한 제목 처리만 수행합니다.")
            # 간단한 제목 처리로 폴백
            if len(title) > max_length:
                if ':' in title:
                    return title.split(':', 1)[0].strip()
                elif ' - ' in title:
                    return title.split(' - ', 1)[0].strip()
                return title[:max_length] + "..."
            return title
        
        prompt = f"""
다음 차트 제목을 분석하고 가장 중요한 핵심 정보만 포함한 간결한 제목으로 요약해주세요.
원본 제목: "{title}"

요구사항:
1. 최대 {max_length}자 이내로 요약
2. 핵심 정보(주제, 기간, 데이터 유형)를 유지
3. 불필요한 수식어나 부연 설명 제거
4. 사용자가 한눈에 인식할 수 있도록 명확하게 구성
5. 응답은 요약된 제목만 작성 (설명 없이)

예시:
- "2022년부터 2023년까지의 대한민국 서울지역 주요 아파트 매매가격 추이 분석" → "서울 아파트 매매가 추이 (2022-2023)"
- "다양한 연령대별 스마트폰 사용 시간에 관한 설문조사 결과 분석" → "연령대별 스마트폰 사용시간"
"""
        # Gemini API 호출 시도
        try:
            response = await get_gemini_response(prompt)
            
            # 응답 정제 (따옴표, 공백 등 제거)
            summarized = response.strip().strip('"\'').strip()
            
            # 최대 길이 제한
            if len(summarized) > max_length:
                summarized = summarized[:max_length]
            
            logger.info(f"Gemini API 타이틀 최적화: '{title}' → '{summarized}'")
            return summarized
        except Exception as api_error:
            logger.warning(f"Gemini API 호출 실패: {api_error} - 간단한 제목 처리로 전환")
            # API 호출 실패 시 간단한 제목 처리로 폴백
            if len(title) > max_length:
                if ':' in title:
                    return title.split(':', 1)[0].strip()
                elif ' - ' in title:
                    return title.split(' - ', 1)[0].strip()
                return title[:max_length] + "..."
            return title
            
    except Exception as e:
        logger.error(f"Gemini API 타이틀 요약 실패: {e}")
        # 오류 발생시 간단한 자체 요약 적용
        if len(title) > max_length:
            # 콜론(:) 기준으로 분리하여 첫 부분만 사용
            if ':' in title:
                return title.split(':', 1)[0].strip()
            # 대시(-) 기준으로 분리
            elif ' - ' in title:
                return title.split(' - ', 1)[0].strip()
            # 단순 절단
            return title[:max_length] + "..."
        return title

async def render(df: pd.DataFrame, chart_context: Dict[str, Any], temp_dir: Path) -> str:
    """
    주어진 DataFrame과 차트 컨텍스트를 사용하여 차트를 렌더링하고 임시 파일로 저장합니다.
    이 함수는 Gemini 분석 결과 등을 바탕으로 동적으로 차트 컨텍스트를 받아 사용합니다.
    """
    # matplotlib 지연 임포트 - 필요할 때만 로드
    import matplotlib.pyplot as plt
    
    try:
        output_dir = temp_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        chart_filename = f"chart_{uuid.uuid4().hex[:8]}.png"
        output_path = output_dir / chart_filename
        qa = ChartQA()
        data_quality = qa.check_data_quality(df)
        logger.info(f"데이터 품질 검사 결과 (render): {data_quality}")
        chart_type = chart_context.get("chart_type", "bar")
        x_column = chart_context.get("x_column")
        y_columns = chart_context.get("y_columns")
        title = chart_context.get("title", "데이터 시각화")
        
        # 차트 크기 및 해상도 설정 추가 - 여백 확보를 위해 크기 조정
        fig_width = chart_context.get("fig_width", BASE_FIGURE_WIDTH * 1.15)  # 15% 더 넓게
        fig_height = chart_context.get("fig_height", BASE_FIGURE_HEIGHT * 1.15)  # 15% 더 높게
        dpi = chart_context.get("dpi", BASE_DPI)
        
        # "Gemini 추천: " 접두사 제거
        if title and title.startswith("Gemini 추천:"):
            title = re.sub(r'^Gemini 추천:\s*', '', title)
            logger.info(f"'Gemini 추천:' 접두사 제거 후 제목: {title}")
        
        # 차트 컨텍스트에서 사용자 정의 타이틀 확인
        custom_title = chart_context.get("custom_title")
        if custom_title:
            title = custom_title
            logger.info(f"사용자 정의 타이틀 사용: '{title}'")
        
        # 연도 데이터가 있는 경우 타이틀에 연도 정보 포함
        years_in_columns = []
        if y_columns:
            for col in y_columns:
                if "_매출" in col:
                    year_match = re.search(r'(\d{4})_매출', col)
                    if year_match:
                        years_in_columns.append(year_match.group(1))
        
        # Sheet1 같은 기본 시트명이 있을 경우 데이터에서 의미 있는 제목 추출 시도
        if title.startswith("Sheet") or title == "데이터 시각화":
            # 데이터 컬럼에서 의미 있는 제목 추출 시도
            if x_column and y_columns and len(y_columns) > 0:
                if chart_type == "bar":
                    # 지역명 컬럼이 있고 매출 데이터가 있는 경우 - 지역별 매출 현황으로 타이틀 설정
                    if x_column in ["지역", "도시", "시도", "region", "city"] or "지역" in x_column:
                        if len(years_in_columns) >= 2:
                            # 연도 정보가 있으면 포함
                            years_str = "-".join(sorted(years_in_columns))
                            title = f"지역별 매출 비교 ({years_str})"
                        else:
                            title = "지역별 매출 현황"
                    # 두 연도 데이터 비교 차트
                    elif len(y_columns) == 2 and all("년" in col for col in y_columns):
                        years = [col.split("_")[0] if "_" in col else col for col in y_columns]
                        title = f"{x_column}별 {years[0]}-{years[1]} 비교"
                    elif any("매출" in col for col in y_columns) or any("판매" in col for col in y_columns):
                        # 매출/판매 관련 차트
                        title = f"{x_column}별 매출 현황"
                    else:
                        # 기본 데이터 비교
                        title = f"{x_column}별 {y_columns[0]} 분석"
                elif chart_type == "line":
                    # 선 그래프 - 추세/시계열 강조
                    if "년" in x_column or "월" in x_column or "일" in x_column:
                        title = f"{y_columns[0]} 추세 분석"
                    else:
                        title = f"{y_columns[0]} 변화 추이"
                elif chart_type == "pie":
                    # 파이 차트 - 비율/분포 강조
                    title = f"{x_column} 분포 현황"
                else:
                    # 기본 제목
                    title = f"{x_column}-{y_columns[0]} 데이터 분석"
                
                logger.info(f"데이터 기반 타이틀 생성: '{title}'")
        
        # 타이틀 최적화 (Gemini API) - 요약 실패 시 원본 타이틀로 폴백
        # 특정 경우 Gemini 최적화 건너뛰기 (지역별 매출 비교 등)
        if not ("지역별 매출" in title and "비교" in title):
            try:
                original_title = title
                title = await summarize_title_with_gemini(title)
                if title != original_title:
                    logger.info(f"타이틀 최적화 완료: '{original_title}' → '{title}'")
            except Exception as e:
                logger.error(f"타이틀 최적화 중 오류 발생: {e}")
                # 오류 시 원본 타이틀 유지

        # 사용자 정의 타이틀이 있으면 모든 자동 생성 타이틀 무시하고 사용
        if custom_title:
            title = custom_title
                
        # x_column 또는 y_columns가 None이거나 비어있는 경우 처리
        if not x_column or not y_columns:
            logger.warning(f"X축 또는 Y축 컬럼이 지정되지 않았습니다. X: {x_column}, Y: {y_columns}. 폴백 차트를 생성합니다.")
            generator = ChartGenerator(fig_width=fig_width, fig_height=fig_height, dpi=dpi)
            fig = generator.generate_fallback_chart(df, title)
            fig.savefig(output_path, 
                        dpi=dpi * 1.5,  # DPI 추가 증가
                        bbox_inches='tight', 
                        pad_inches=0.8,  # 여백 더 증가 
                        facecolor=fig.get_facecolor())
            plt.close(fig)
            return str(output_path)
            
        is_valid, message = qa.validate_chart_params(df, chart_type, x_column, y_columns)
        if not is_valid:
            logger.warning(f"차트 파라미터 검증 실패 (render): {message}. 폴백 차트를 생성합니다.")
            generator = ChartGenerator(fig_width=fig_width, fig_height=fig_height, dpi=dpi)
            fig = generator.generate_fallback_chart(df, title)
            fig.savefig(output_path, 
                        dpi=dpi * 1.5,  # DPI 추가 증가
                        bbox_inches='tight', 
                        pad_inches=0.8,  # 여백 더 증가 
                        facecolor=fig.get_facecolor())
            plt.close(fig)
            return str(output_path)
            
        generator = ChartGenerator(fig_width=fig_width, fig_height=fig_height, dpi=dpi)
        chart_methods = {
            "line": generator.generate_line_chart,
            "bar": generator.generate_bar_chart,
            "scatter": generator.generate_scatter_chart,
            "pie": generator.generate_pie_chart
        }
        chart_method = chart_methods.get(chart_type.lower())
        if chart_method:
            logger.info(f"차트 생성 시작: type={chart_type}, x={x_column}, y={y_columns}, title={title}")
            try:
                fig = chart_method(df, x_column, y_columns, title)
                try:
                    # 여백 확보를 위해 tight_layout 파라미터 조정
                    fig.tight_layout(pad=1.5)  # 여백 증가
                except Exception as e_layout:
                    logger.warning(f"fig.tight_layout() 적용 중 오류 발생: {e_layout}")
                # 여백을 확보하기 위해 bbox_inches 옵션 사용
                fig.savefig(output_path, 
                            dpi=dpi * 1.5,  # DPI 추가 증가
                            bbox_inches='tight', 
                            pad_inches=0.8,  # 여백 더 증가 
                            facecolor=fig.get_facecolor())
                plt.close(fig)
                logger.info(f"차트 생성 완료: {output_path}")
                return str(output_path)
            except Exception as chart_error:
                logger.error(f"차트 생성 중 오류 발생: {chart_error}")
                # 차트 생성 실패 시 오류 메시지가 포함된 간단한 에러 차트 생성
                fig, ax = plt.subplots(figsize=(fig_width, fig_height), constrained_layout=True, dpi=dpi)
                ax.text(0.5, 0.5, f"차트 생성 실패: {str(chart_error)[:50]}...", 
                       ha='center', va='center', color=COLOR_TEXT_LIGHT,
                       fontsize=generator.font_size_label)
                ax.set_facecolor(COLOR_BACKGROUND_DARK)
                ax.axis('off')
                fig.patch.set_facecolor(COLOR_BACKGROUND_DARK)
                fig.savefig(output_path, 
                           dpi=dpi * 1.5,
                           bbox_inches='tight',
                           pad_inches=0.8,
                           facecolor=COLOR_BACKGROUND_DARK)
                plt.close(fig)
                return str(output_path)
        else:
            logger.warning(f"지원하지 않는 차트 타입입니다: {chart_type}. 폴백 차트를 생성합니다.")
            fig = generator.generate_fallback_chart(df, title)
            try:
                fig.tight_layout(pad=1.5)  # 여백 증가
            except Exception as e_layout:
                logger.warning(f"폴백 차트 fig.tight_layout() 적용 중 오류 발생: {e_layout}")
            fig.savefig(output_path, 
                        dpi=dpi * 1.5,  # DPI 추가 증가
                        bbox_inches='tight', 
                        pad_inches=0.8,  # 여백 더 증가 
                        facecolor=fig.get_facecolor())
            plt.close(fig)
            return str(output_path)
    except Exception as e:
        logger.error(f"render 중 오류 발생: {str(e)}", exc_info=True)
        try:
            # 단순화된 오류 메시지 차트 생성
            output_dir = temp_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            chart_filename = f"error_chart_{uuid.uuid4().hex[:8]}.png"
            output_path = output_dir / chart_filename
            
            # 최소한의 matplotlib 기능으로 오류 메시지 표시
            fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
            ax.text(0.5, 0.5, f"Chart generation failed: {str(e)[:100]}...", 
                   ha='center', va='center', color='white',
                   fontsize=14)
            ax.set_facecolor(COLOR_BACKGROUND_DARK)
            ax.axis('off')
            fig.patch.set_facecolor(COLOR_BACKGROUND_DARK)
            
            # 최소한의 옵션으로 저장
            fig.savefig(output_path, facecolor=COLOR_BACKGROUND_DARK)
            plt.close(fig)
            return str(output_path)
        except Exception as fallback_e:
            logger.error(f"오류 폴백 차트 생성 실패: {fallback_e}", exc_info=True)
            # 더 이상 실패하면 예외를 발생시키는 대신 빈 이미지 경로 반환
            try:
                # 완전 기본 흰색 바탕 이미지 생성
                chart_filename = f"blank_error_{uuid.uuid4().hex[:8]}.png"
                output_path = output_dir / chart_filename
                fig, ax = plt.subplots(figsize=(6, 3), dpi=80)
                ax.axis('off')
                fig.savefig(output_path)
                plt.close(fig)
                return str(output_path)
            except:
                # 모든 시도 실패 시 경로만 반환
                return "error_generation_failed"

def cleanup_old_charts(temp_dir_str: str = "temp_charts", max_age_seconds: int = 3600):
    """오래된 차트 파일을 정리합니다."""
    temp_dir = Path(temp_dir_str)
    if not temp_dir.is_dir():
        logger.warning(f"임시 차트 디렉토리 '{temp_dir}'를 찾을 수 없거나 디렉토리가 아닙니다. 파일 정리를 건너뛰니다.")
        return
    try:
        for item in temp_dir.iterdir():
            if item.is_file() and item.name.startswith("chart_") and item.name.endswith(".png"):
                try:
                    file_age = time.time() - item.stat().st_mtime
                    if file_age > max_age_seconds:
                        item.unlink()
                        logger.info(f"오래된 차트 파일 삭제: {item}")
                except FileNotFoundError:
                    logger.info(f"파일 삭제 시도 중 찾을 수 없음 (이미 삭제됨 가능성): {item}")
                except Exception as e:
                    logger.error(f"오래된 차트 파일 {item} 삭제 중 오류: {e}")
            elif item.is_dir():
                pass
    except FileNotFoundError:
        logger.info(f"임시 차트 디렉토리 '{temp_dir}'를 찾을 수 없어 정리 작업을 건너뛰니다 (이미 삭제되었을 수 있습니다).")
    except Exception as e:
        logger.error(f"임시 차트 파일 정리 중 오류 발생: {e}")

# Matplotlib 캐시 디렉토리 확인용 (디버깅 시 필요할 수 있음)
# print(matplotlib.get_cachedir())
