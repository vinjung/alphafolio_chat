'use client';

import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { logger } from '@/lib/utils/logger';

const log = logger.child({ module: 'retention-tracker-hook' });

interface UseRetentionTrackerOptions {
  /** 리텐션 체크를 활성화할지 여부 */
  enabled?: boolean;
  /** 특정 경로만 추적할지 여부 (기본값: 모든 경로) */
  trackablePaths?: string[];
}

/**
 * URL 변경을 감지하여 일일 리텐션을 체크하는 훅
 * 바텀 네비게이션에서 사용하여 모든 페이지 이동을 통합 관리
 */
export function useRetentionTracker(options: UseRetentionTrackerOptions = {}) {
  const { enabled = true, trackablePaths } = options;
  const pathname = usePathname();
  const lastTrackedPath = useRef<string>('');
  const isTracking = useRef(false);
  const dailyTracked = useRef(false);

  /**
   * 경로를 페이지 식별자로 변환
   */
  const getPageIdentifier = (path: string): string => {
    // 동적 라우트 처리
    if (path.startsWith('/chat/') && path !== '/chat') {
      return 'chat'; // /chat/[chatId] → 'chat'
    }

    // 기본 경로들
    const pathMap: Record<string, string> = {
      '/today': 'today',
      '/future': 'future',
      '/chat': 'chat',
      '/mypage': 'mypage',
    };

    return pathMap[path] || path.replace('/', '') || 'home';
  };

  /**
   * 추적 가능한 경로인지 확인
   */
  const isTrackablePath = (path: string): boolean => {
    if (!trackablePaths) return true;

    return trackablePaths.some((trackablePath) => {
      if (trackablePath.includes('[') && trackablePath.includes(']')) {
        const pattern = trackablePath.replace(/\[[\w]+\]/g, '[^/]+');
        const regex = new RegExp(`^${pattern}$`);
        return regex.test(path);
      }
      return path === trackablePath || path.startsWith(trackablePath);
    });
  };

  /**
   * 일일 리텐션 API 호출
   */
  const trackRetention = async (page: string) => {
    if (isTracking.current || dailyTracked.current) {
      return;
    }

    isTracking.current = true;

    try {
      log.info('일일 리텐션 체크 시작', { page, pathname });

      const response = await fetch('/api/retention', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ page }),
      });

      const data = await response.json();

      if (response.ok) {
        // 성공 시 당일 추적 완료로 마킹
        if (!data.cached) {
          dailyTracked.current = true;
        }

        log.info('일일 리텐션 체크 완료', {
          page,
          pathname,
          cached: data.cached,
          ttlSeconds: data.ttlSeconds,
        });

        // 개발 환경에서만 콘솔 출력
        if (process.env.NODE_ENV === 'development') {
          console.log('📊 일일 리텐션:', {
            페이지: page,
            경로: pathname,
            상태: data.cached ? '이미기록됨' : '새로기록',
            자정까지: data.ttlSeconds
              ? `${Math.floor(data.ttlSeconds / 3600)}시간`
              : 'N/A',
          });
        }
      } else {
        if (response.status === 401) {
          log.debug('리텐션 체크 건너뛰기 (비로그인 상태)', { page, pathname });
        } else {
          log.warn('리텐션 체크 실패', {
            page,
            pathname,
            status: response.status,
            error: data.error,
          });
        }
      }
    } catch (error) {
      log.warn('리텐션 체크 네트워크 오류', { page, pathname, error });

      if (process.env.NODE_ENV === 'development') {
        console.warn('📊 리텐션 체크 실패:', { page, pathname, error });
      }
    } finally {
      isTracking.current = false;
    }
  };

  // URL 변경 감지 및 리텐션 체크
  useEffect(() => {
    if (!enabled || !pathname) return;

    // 추적 불가능한 경로면 건너뛰기
    if (!isTrackablePath(pathname)) {
      return;
    }

    // 🎯 하루 한 번만 체크하므로 중복 방지는 서버에서 처리
    // 클라이언트에서는 페이지 변경마다 체크 시도 (서버가 중복 판단)
    const pageId = getPageIdentifier(pathname);

    // 약간의 지연 후 리텐션 체크
    const timeoutId = setTimeout(() => {
      trackRetention(pageId);
    }, 100);

    return () => {
      clearTimeout(timeoutId);
    };
  }, [pathname, enabled, trackablePaths, isTrackablePath, trackRetention]);

  // 자정 지나면 일일 추적 플래그 리셋
  useEffect(() => {
    const resetDailyFlag = () => {
      dailyTracked.current = false;
      log.info('일일 리텐션 플래그 리셋');
    };

    const now = new Date();
    const kstOffset = 9 * 60 * 60 * 1000;
    const kstNow = new Date(now.getTime() + kstOffset);
    const nextMidnight = new Date(kstNow);
    nextMidnight.setUTCHours(24, 0, 0, 0);
    const msUntilMidnight = nextMidnight.getTime() - kstNow.getTime();

    const timeoutId = setTimeout(resetDailyFlag, msUntilMidnight);
    return () => clearTimeout(timeoutId);
  }, []);

  return {
    /** 현재 추적 중인지 여부 */
    isTracking: isTracking.current,
    /** 오늘 이미 추적했는지 여부 */
    dailyTracked: dailyTracked.current,
    /** 마지막 추적한 경로 */
    lastTrackedPath: lastTrackedPath.current,
  };
}
