'use client';

import { useEffect } from 'react';
import { useChatLimitStore } from '@/stores/chat-limit-store';

interface ChatLimitInfo {
  used: number;
  limit: number;
  remaining: number;
  canSend: boolean;
  resetTime: string;
}

interface UseChatLimitResult {
  limitInfo: ChatLimitInfo | null;
  isLoading: boolean;
  error: string | null;
  isGuest: boolean;
  refreshLimit: () => Promise<void>;
  decrementRemaining: () => void;
}

export function useChatLimit(): UseChatLimitResult {
  const {
    limitInfo,
    isLoading,
    error,
    isGuest,
    isInitialized,
    refreshLimit,
    decrementRemaining,
    initializeLimit,
  } = useChatLimitStore();

  // ✅ 한 번만 초기화
  useEffect(() => {
    if (!isInitialized) {
      initializeLimit();
    }
  }, [isInitialized, initializeLimit]);

  return {
    limitInfo,
    isLoading,
    error,
    isGuest,
    refreshLimit,
    decrementRemaining,
  };
}
