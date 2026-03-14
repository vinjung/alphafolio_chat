// client/src/hooks/use-chat-navigation.ts
'use client';

import { useRouter } from 'next/navigation';
import { useTransition, useState, useCallback } from 'react';

interface NavigationOptions {
  onNavigationStart?: () => void;
  onNavigationComplete?: () => void;
  onNavigationError?: (error: Error) => void;
}

export function useChatNavigation(options: NavigationOptions = {}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [isNavigating, setIsNavigating] = useState(false);

  const navigateToNewChat = useCallback(
    (modelId: string, firstMessage?: string) => {
      try {
        // 즉시 네비게이션 시작 표시
        setIsNavigating(true);
        options.onNavigationStart?.();

        const newChatId = `chat_${modelId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        const params = new URLSearchParams({
          model: modelId,
          new: 'true',
        });

        if (firstMessage) {
          params.set('message', firstMessage);
        }

        // 부드러운 전환으로 페이지 이동
        startTransition(() => {
          router.push(`/chat/${newChatId}?${params.toString()}`);
        });
      } catch (error) {
        console.error('채팅 네비게이션 실패:', error);
        setIsNavigating(false);
        options.onNavigationError?.(error as Error);
      }
    },
    [router, startTransition, options]
  );

  const navigateToExistingChat = useCallback(
    (chatId: string) => {
      try {
        setIsNavigating(true);
        options.onNavigationStart?.();

        startTransition(() => {
          router.push(`/chat/${chatId}`);
        });
      } catch (error) {
        console.error('기존 채팅 이동 실패:', error);
        setIsNavigating(false);
        options.onNavigationError?.(error as Error);
      }
    },
    [router, startTransition, options]
  );

  // 네비게이션 완료 감지
  const resetNavigation = useCallback(() => {
    setIsNavigating(false);
    options.onNavigationComplete?.();
  }, [options]);

  return {
    navigateToNewChat,
    navigateToExistingChat,
    resetNavigation,
    isNavigating,
    isPending,
    isTransitioning: isNavigating || isPending,
  };
}
