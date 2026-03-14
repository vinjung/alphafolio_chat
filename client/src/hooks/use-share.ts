'use client';

import { useState } from 'react';
import { showGlobalSnackbar } from '@/components/shared/snackbar';

interface ShareData {
  title?: string;
  text?: string;
  url?: string;
}

interface UseWebShareOptions {
  fallbackMessage?: string;
}

export function useWebShare(options: UseWebShareOptions = {}) {
  const [isSharing, setIsSharing] = useState(false);

  const { fallbackMessage = '클립보드에 복사되었습니다!' } = options;

  const share = async (data: ShareData) => {
    if (isSharing) return;

    setIsSharing(true);

    try {
      // Web Share API 지원 확인
      if (navigator.share && navigator.canShare?.(data)) {
        await navigator.share(data);
        showGlobalSnackbar('공유 완료!', { position: 'top' });
      } else {
        // 폴백: 클립보드 복사
        const textToShare =
          `${data.title || ''}\n\n${data.text || ''}${data.url ? '\n\n' + data.url : ''}`.trim();

        await navigator.clipboard.writeText(textToShare);
        showGlobalSnackbar(fallbackMessage, { position: 'top' });
      }
    } catch (error) {
      // 사용자가 공유를 취소하거나 에러 발생
      if (error instanceof Error && error.name !== 'AbortError') {
        console.error('Share failed:', error);
        showGlobalSnackbar('공유에 실패했습니다.', { position: 'top' });
      }
    } finally {
      setIsSharing(false);
    }
  };

  const isSupported =
    typeof navigator !== 'undefined' &&
    (!!navigator.share || !!navigator.clipboard);

  return {
    share,
    isSharing,
    isSupported,
  };
}
