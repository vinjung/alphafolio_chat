import { useState } from 'react';

export function useSnackbar() {
  const [isVisible, setIsVisible] = useState(false);
  const [message, setMessage] = useState('');

  const showSnackbar = (msg: string, duration = 3000) => {
    // 기존 스낵바가 있으면 즉시 닫고 새 스낵바 표시
    setIsVisible(false);

    setTimeout(() => {
      setMessage(msg);
      setIsVisible(true);

      setTimeout(() => {
        setIsVisible(false);
      }, duration);
    }, 10); // 약간의 딜레이로 부드러운 전환
  };

  const hideSnackbar = () => {
    setIsVisible(false);
  };

  return {
    showSnackbar,
    hideSnackbar,
    isVisible,
    message,
  };
}
