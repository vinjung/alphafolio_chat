'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useStreamingStore } from '@/stores';

interface ChatLimitInfo {
  used: number;
  limit: number;
  remaining: number;
  canSend: boolean;
  resetTime: string;
}

interface NavigationGuardOptions {
  isBlocked: boolean;
  limitInfo?: ChatLimitInfo | null; // 🔧 구체적인 타입으로 변경
  isGuest?: boolean;
  onNavigationAttempt?: (targetUrl: string) => void;
  onNavigationConfirm?: (targetUrl: string) => void;
  onNavigationCancel?: () => void;
}

interface NavigationGuardResult {
  isDialogOpen: boolean;
  targetUrl: string | null;
  closeDialog: () => void;
  confirmNavigation: () => void;
  cancelNavigation: () => void;
  guardedNavigate: (url: string) => void;
}

export function useNavigationGuard(
  options: NavigationGuardOptions
): NavigationGuardResult {
  const router = useRouter();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [targetUrl, setTargetUrl] = useState<string | null>(null);

  const { resetStreamingState } = useStreamingStore();


  const guardedNavigate = useCallback(
    (url: string) => {
      if (!options.isBlocked) {
        router.push(url);
        return;
      }

      setTargetUrl(url);
      setIsDialogOpen(true);
      options.onNavigationAttempt?.(url);
    },
    [options.isBlocked, options.onNavigationAttempt, options, router]
  );

  const confirmNavigation = useCallback(() => {
    if (targetUrl) {
      const urlToNavigate = targetUrl;

      setIsDialogOpen(false);
      setTargetUrl(null);
      resetStreamingState();

      router.push(urlToNavigate);
      options.onNavigationConfirm?.(urlToNavigate);
    }
  }, [targetUrl, router, resetStreamingState, options]);

  const cancelNavigation = useCallback(() => {
    setIsDialogOpen(false);
    setTargetUrl(null);
    options.onNavigationCancel?.();
  }, [options]);

  const closeDialog = useCallback(() => {
    setIsDialogOpen(false);
    setTargetUrl(null);
  }, []);

  return {
    isDialogOpen,
    targetUrl,
    closeDialog,
    confirmNavigation,
    cancelNavigation,
    guardedNavigate,
  };
}
