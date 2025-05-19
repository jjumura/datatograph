import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
import numpy as np
import uuid
from pathlib import Path

def create_simple_animation(data, filename="animation.gif"):
    """
    가장 기본적인 애니메이션 생성 함수
    """
    # 아주 기본적인 애니메이션만 구현
    fig, ax = plt.subplots()
    
    x = np.linspace(0, 10, 100)
    line, = ax.plot([], [])
    
    def init():
        line.set_data([], [])
        return line,
    
    def animate(i):
        y = np.sin(x - 0.1 * i)
        line.set_data(x[:i], y[:i])
        return line,
    
    ax.set_xlim(0, 10)
    ax.set_ylim(-1.1, 1.1)
    
    anim = FuncAnimation(fig, animate, init_func=init, 
                         frames=100, interval=50, blit=True)
    
    # 파일 저장
    temp_path = Path("temp_charts") / filename
    anim.save(temp_path, writer='pillow', fps=20)
    plt.close(fig)
    
    return str(temp_path)

def create_progress_animation(progress_data=None, filename=None):
    """
    작업 진행 상황을 시각화하는 애니메이션 생성 함수
    
    Args:
        progress_data (dict, optional): 
            {'단계명': 진행률(0-100)} 형태의 딕셔너리. 
            None인 경우 샘플 데이터로 대체됨.
        filename (str, optional): 저장할 파일명.
            None인 경우 자동 생성됨.
    
    Returns:
        str: 생성된 애니메이션 파일 경로
    """
    if filename is None:
        filename = f"progress_{uuid.uuid4().hex[:6]}.gif"
        
    if progress_data is None:
        # 샘플 데이터 생성
        progress_data = {
            '데이터 수집': 100,
            '데이터 전처리': 80,
            '모델 학습': 60,
            '결과 분석': 40,
            '보고서 작성': 10
        }
    
    # 그래프 설정
    fig, ax = plt.subplots(figsize=(8, 6))
    plt.style.use('ggplot')
    
    categories = list(progress_data.keys())
    values = list(progress_data.values())
    y_pos = np.arange(len(categories))
    
    colors = plt.cm.viridis(np.array(values) / 100)
    
    def init():
        ax.set_ylim(-0.5, len(categories) - 0.5)
        ax.set_xlim(0, 105)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories)
        ax.set_xlabel('진행률 (%)')
        ax.set_title('현재 작업 진행 상황')
        ax.grid(axis='x')
        return []
    
    def animate(i):
        ax.clear()
        current_values = [min(v * (i / 50), v) for v in values]
        bars = ax.barh(y_pos, current_values, align='center', color=colors)
        
        # 진행률 텍스트 추가
        for j, (bar, value) in enumerate(zip(bars, current_values)):
            width = bar.get_width()
            ax.text(min(width + 3, 105), bar.get_y() + bar.get_height()/2,
                   f'{value:.1f}%', ha='left', va='center')
        
        ax.set_ylim(-0.5, len(categories) - 0.5)
        ax.set_xlim(0, 105)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories)
        ax.set_xlabel('진행률 (%)')
        ax.set_title('현재 작업 진행 상황')
        ax.grid(axis='x')
        return bars
    
    anim = FuncAnimation(fig, animate, init_func=init, 
                        frames=60, interval=50, blit=True)
    
    # 파일 저장
    temp_path = Path("temp_charts") / filename
    anim.save(temp_path, writer='pillow', fps=15)
    plt.close(fig)
    
    return str(temp_path)
