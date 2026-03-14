'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Text } from '@/components/shared/text';
import { cx } from '@/lib/utils/cva.config';

//  테스트용 설정
const TEST_MODE = process.env.NODE_ENV === 'development';
const TEST_SECONDS = 10;

let globalStartTime: Date | null = null;
let isGlobalRefreshing = false;

interface AutoRefreshProps {
  style?: React.CSSProperties;
  className?: string;
}

export function AutoRefresh({ style, className }: AutoRefreshProps) {
  const [timeLeft, setTimeLeft] = useState<string>('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const router = useRouter();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const formatTime = (totalSeconds: number) => {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const handleAutoRefresh = async () => {
    if (isGlobalRefreshing) return;

    console.log('[AutoRefresh] 정각 자동 새로고침 시작');
    isGlobalRefreshing = true;
    setIsRefreshing(true);

    try {
      router.refresh();
      globalStartTime = new Date();
      console.log('[AutoRefresh] 자동 새로고침 완료');
    } catch (error) {
      console.error('[AutoRefresh] 자동 새로고침 실패:', error);
    }

    setTimeout(() => {
      isGlobalRefreshing = false;
      setIsRefreshing(false);
    }, 1000);
  };

  const calculateTimeLeft = () => {
    const now = new Date();

    if (TEST_MODE) {
      if (!globalStartTime) {
        globalStartTime = new Date();
        return formatTime(TEST_SECONDS);
      }

      const elapsed = Math.floor(
        (now.getTime() - globalStartTime.getTime()) / 1000
      );
      const remaining = Math.max(0, TEST_SECONDS - elapsed);

      if (remaining === 0 && !isGlobalRefreshing) {
        handleAutoRefresh();
        return formatTime(TEST_SECONDS);
      }

      return formatTime(remaining);
    } else {
      const nextHour = new Date(now);
      nextHour.setHours(now.getHours() + 1, 0, 0, 0);
      const diff = nextHour.getTime() - now.getTime();

      if (diff <= 0 && !isGlobalRefreshing) {
        handleAutoRefresh();
        // 다음 시간까지 계산
        nextHour.setHours(nextHour.getHours() + 1);
        const newDiff = nextHour.getTime() - now.getTime();
        const totalSeconds = Math.floor(newDiff / 1000);
        return formatTime(totalSeconds);
      }

      const totalSeconds = Math.floor(diff / 1000);
      return formatTime(totalSeconds);
    }
  };

  useEffect(() => {
    setIsRefreshing(isGlobalRefreshing);

    const updateCountdown = () => {
      const time = calculateTimeLeft();
      setTimeLeft(time);
    };

    updateCountdown();
    intervalRef.current = setInterval(updateCountdown, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [calculateTimeLeft]);

  return (
    <div
      className={cx(
        'px-4 py-2 bg-neutral-50 border-b border-neutral-100',
        className
      )}
      style={style}
    >
      <div className="flex items-center justify-center gap-2">
        {isRefreshing ? (
          <>
            <div className="w-3 h-3 border border-red-900 border-t-transparent rounded-full animate-spin" />
            <Text variant="b3" className="text-red-900">
              업데이트 중...
            </Text>
          </>
        ) : (
          <Text variant="b3" className="text-neutral-600">
            다음 떡상 정보까지 {timeLeft}
          </Text>
        )}
      </div>
    </div>
  );
}
