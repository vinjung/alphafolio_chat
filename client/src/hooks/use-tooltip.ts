import { useState, useEffect } from 'react';

export function useTooltipState(storageKey: string = 'tooltip-shown') {
  const [hasShown, setHasShown] = useState(false);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
    // 실제 프로젝트에서는:
    const stored = localStorage.getItem(storageKey) === 'true';
    setHasShown(stored);
  }, [storageKey]);

  const markAsShown = () => {
    setHasShown(true);
    if (isClient) {
      // 실제 프로젝트에서는:
      localStorage.setItem(storageKey, 'true');
    }
  };

  return { hasShown, markAsShown, isClient };
}
