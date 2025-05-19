import React from 'react';
import './LoadingPage.css';

interface LoadingPageProps {
  message?: string;
}

const LoadingPage: React.FC<LoadingPageProps> = ({ message }) => {
  const messages = [
    "데이터 분석 중...",
    "최적의 차트를 탐색 중입니다...",
    "Gemini AI가 인사이트를 찾고 있습니다...",
    "시각화 생성 중...",
    "잠시만 기다려 주세요..."
  ];
  const [currentMessage, setCurrentMessage] = React.useState(message || messages[0]);
  const [currentMessageIndex, setCurrentMessageIndex] = React.useState(0);

  React.useEffect(() => {
    if (!message) {
      const intervalId = setInterval(() => {
        setCurrentMessageIndex(prevIndex => (prevIndex + 1) % messages.length);
      }, 2500); // 2.5초마다 메시지 변경

      return () => clearInterval(intervalId);
    }
  }, [messages, message]);

  React.useEffect(() => {
    if (!message) {
      setCurrentMessage(messages[currentMessageIndex]);
    } else {
      setCurrentMessage(message);
    }
  }, [currentMessageIndex, messages, message]);


  return (
    <div className="loading-page-container">
      <div className="loading-animation">
        {/* 간단한 CSS 기반 애니메이션 요소들 */}
        <div className="loading-dot dot1"></div>
        <div className="loading-dot dot2"></div>
        <div className="loading-dot dot3"></div>
        <div className="loading-line line1"></div>
        <div className="loading-line line2"></div>
        <div className="loading-line line3"></div>
      </div>
      <p className="loading-message">{currentMessage}</p>
      <p className="loading-subtext">Project_A Insight Analyzer</p>
    </div>
  );
};

export default LoadingPage; 