import json
import os
from pathlib import Path
import matplotlib.colors as mcolors

def hex_to_rgb(hex_color):
    """HEX 색상 코드를 RGB 값으로 변환합니다."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))

def compile_tokens():
    """디자인 토큰을 matplotlib 스타일로 변환합니다."""
    # 프로젝트 루트 디렉토리 찾기
    project_root = Path(__file__).parent.parent
    tokens_path = project_root / "design-tokens" / "brand.json"
    style_dir = project_root / "styles"
    style_path = style_dir / "brand.mplstyle"

    # 디렉토리가 없으면 생성
    style_dir.mkdir(exist_ok=True)

    try:
        with open(tokens_path, 'r', encoding='utf-8') as f:
            tokens = json.load(f)

        # matplotlib 스타일 설정 생성
        style_settings = []

        # 색상 설정
        colors = tokens.get('colors', {})
        style_settings.extend([
            f"axes.facecolor: {colors.get('background', '#FFFFFF')}",
            f"figure.facecolor: {colors.get('background', '#FFFFFF')}",
            f"axes.edgecolor: {colors.get('text', '#212121')}",
            f"axes.labelcolor: {colors.get('text', '#212121')}",
            f"axes.grid.color: {colors.get('grid', '#E0E0E0')}",
            f"text.color: {colors.get('text', '#212121')}",
            f"xtick.color: {colors.get('text', '#212121')}",
            f"ytick.color: {colors.get('text', '#212121')}",
            f"grid.color: {colors.get('grid', '#E0E0E0')}",
            f"lines.color: {colors.get('primary', '#1E88E5')}",
            f"patch.facecolor: {colors.get('primary', '#1E88E5')}",
        ])

        # 타이포그래피 설정
        typography = tokens.get('typography', {})
        style_settings.extend([
            f"font.family: {typography.get('font_family', 'Arial')}",
            f"axes.titlesize: {typography.get('title_size', 16)}",
            f"axes.labelsize: {typography.get('label_size', 12)}",
            f"xtick.labelsize: {typography.get('tick_size', 10)}",
            f"ytick.labelsize: {typography.get('tick_size', 10)}",
        ])

        # 레이아웃 설정
        layout = tokens.get('layout', {})
        figure_size = layout.get('figure_size', {'width': 10, 'height': 6})
        style_settings.extend([
            f"figure.figsize: {figure_size['width']}, {figure_size['height']}",
            f"figure.dpi: {layout.get('dpi', 100)}",
            f"lines.linewidth: {layout.get('line_width', 2)}",
            f"lines.markersize: {layout.get('marker_size', 6)}",
            "axes.grid: True",
            "grid.linestyle: --",
        ])

        # 스타일 파일 저장
        with open(style_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(style_settings))

        print(f"스타일 파일이 생성되었습니다: {style_path}")
        return True

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    compile_tokens() 