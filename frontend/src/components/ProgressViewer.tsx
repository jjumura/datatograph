import React, { useState } from 'react';
import axios from 'axios';
import './ProgressViewer.css';

interface ProgressData {
  [key: string]: number;
}

interface ProgressViewerProps {
  initialData?: ProgressData;
}

const ProgressViewer: React.FC<ProgressViewerProps> = ({ initialData }) => {
  const [progressData, setProgressData] = useState<ProgressData>(
    initialData || {
      '데이터 수집': 100,
      '데이터 전처리': 80,
      '모델 학습': 60,
      '결과 분석': 40,
      '보고서 작성': 10,
    }
  );
  const [animationUrl, setAnimationUrl] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // 새 작업 항목 추가를 위한 상태
  const [newTaskName, setNewTaskName] = useState<string>('');
  const [newTaskProgress, setNewTaskProgress] = useState<number>(0);

  const fetchProgressAnimation = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(
        'http://localhost:8000/api/simple-animation/progress',
        progressData,
        {
          responseType: 'blob',
        }
      );
      
      // Blob URL 생성
      const blob = new Blob([response.data], { type: 'image/gif' });
      const url = URL.createObjectURL(blob);
      setAnimationUrl(url);
    } catch (err) {
      console.error('진행 상황 애니메이션 생성 중 오류:', err);
      setError('애니메이션 생성에 실패했습니다. 서버 연결을 확인해주세요.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddTask = () => {
    if (!newTaskName.trim()) {
      setError('작업 이름을 입력해주세요.');
      return;
    }
    
    setProgressData({
      ...progressData,
      [newTaskName]: newTaskProgress,
    });
    
    // 입력 필드 초기화
    setNewTaskName('');
    setNewTaskProgress(0);
    setError(null);
  };

  const handleUpdateProgress = (task: string, value: number) => {
    setProgressData({
      ...progressData,
      [task]: value,
    });
  };

  const handleRemoveTask = (task: string) => {
    const newData = { ...progressData };
    delete newData[task];
    setProgressData(newData);
  };

  return (
    <div className="progress-viewer">
      <h2>작업 진행 상황 관리</h2>
      
      <div className="task-input">
        <div className="input-group">
          <label htmlFor="taskName">작업명:</label>
          <input
            id="taskName"
            type="text"
            value={newTaskName}
            onChange={(e) => setNewTaskName(e.target.value)}
            placeholder="새 작업 이름"
          />
        </div>
        
        <div className="input-group">
          <label htmlFor="taskProgress">진행률(%):</label>
          <input
            id="taskProgress"
            type="number"
            min="0"
            max="100"
            value={newTaskProgress}
            onChange={(e) => setNewTaskProgress(Number(e.target.value))}
          />
        </div>
        
        <button onClick={handleAddTask}>작업 추가</button>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="tasks-container">
        <h3>현재 작업 목록</h3>
        {Object.entries(progressData).length === 0 ? (
          <p>작업이 없습니다. 작업을 추가해주세요.</p>
        ) : (
          <ul className="tasks-list">
            {Object.entries(progressData).map(([task, progress]) => (
              <li key={task} className="task-item">
                <div className="task-details">
                  <span className="task-name">{task}</span>
                  <div className="task-controls">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={progress}
                      onChange={(e) => handleUpdateProgress(task, Number(e.target.value))}
                    />
                    <span className="progress-value">{progress}%</span>
                    <button 
                      className="remove-btn"
                      onClick={() => handleRemoveTask(task)}
                    >
                      삭제
                    </button>
                  </div>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
      
      <div className="animation-controls">
        <button 
          onClick={fetchProgressAnimation}
          disabled={loading || Object.keys(progressData).length === 0}
        >
          {loading ? '생성 중...' : '애니메이션 생성'}
        </button>
      </div>
      
      {animationUrl && (
        <div className="animation-container">
          <h3>진행 상황 애니메이션</h3>
          <img 
            src={animationUrl} 
            alt="진행 상황 애니메이션" 
            className="progress-animation"
          />
        </div>
      )}
    </div>
  );
};

export default ProgressViewer; 