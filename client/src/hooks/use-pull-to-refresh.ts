'use client';

import { useState, useRef, useCallback } from 'react';

interface UsePullToRefreshOptions {
  showThreshold?: number;
  resistance?: number;
  snapBackDuration?: number;
}

interface PullToRefreshState {
  isPulling: boolean;
  pullDistance: number;
  isVisible: boolean;
}

export function usePullToRefresh(options: UsePullToRefreshOptions = {}) {
  const {
    showThreshold = 40,
    resistance = 0.4,
    snapBackDuration = 300,
  } = options;

  const [state, setState] = useState<PullToRefreshState>({
    isPulling: false,
    pullDistance: 0,
    isVisible: false,
  });

  const startY = useRef<number>(0);
  const scrollElement = useRef<HTMLElement | null>(null);
  const isPullingRef = useRef<boolean>(false); // ref로 상태 추적

  const updateState = useCallback((updates: Partial<PullToRefreshState>) => {
    setState((prev) => {
      const newState = { ...prev, ...updates };
      isPullingRef.current = newState.isPulling; // ref 동기화
      return newState;
    });
  }, []);

  const calculatePullDistance = useCallback(
    (deltaY: number) => {
      return deltaY * resistance;
    },
    [resistance]
  );

  const handleTouchStart = useCallback(
    (e: TouchEvent) => {
      if (!scrollElement.current) return;

      const scrollTop = scrollElement.current.scrollTop;

      if (scrollTop <= 0) {
        startY.current = e.touches[0].clientY;
        updateState({ isPulling: true });
      }
    },
    [updateState]
  );

  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (!isPullingRef.current || !scrollElement.current) return; // ref 사용

      const currentY = e.touches[0].clientY;
      const deltaY = currentY - startY.current;

      if (deltaY > 0) {
        e.preventDefault();

        const pullDistance = calculatePullDistance(deltaY);
        const isVisible = pullDistance > showThreshold;

        updateState({
          pullDistance,
          isVisible,
        });
      }
    },
    [calculatePullDistance, showThreshold, updateState] // state.isPulling 의존성 제거
  );

  const handleTouchEnd = useCallback(() => {
    if (!isPullingRef.current) return; // ref 사용

    updateState({
      isPulling: false,
      pullDistance: 0,
      isVisible: false,
    });
  }, [updateState]); // state.isPulling 의존성 제거

  const bindScrollElement = useCallback(
    (element: HTMLElement | null) => {
      // 기존 이벤트 리스너 제거
      if (scrollElement.current) {
        scrollElement.current.removeEventListener(
          'touchstart',
          handleTouchStart
        );
        scrollElement.current.removeEventListener('touchmove', handleTouchMove);
        scrollElement.current.removeEventListener('touchend', handleTouchEnd);
      }

      scrollElement.current = element;

      // 새 이벤트 리스너 추가
      if (element) {
        element.addEventListener('touchstart', handleTouchStart, {
          passive: false,
        });
        element.addEventListener('touchmove', handleTouchMove, {
          passive: false,
        });
        element.addEventListener('touchend', handleTouchEnd);
      }
    },
    [handleTouchStart, handleTouchMove, handleTouchEnd]
  );

  return {
    ...state,
    bindScrollElement,
    refreshContainerStyle: {
      transform: `translateY(${state.isVisible ? 0 : -100}%)`,
      transition: state.isPulling
        ? 'none'
        : `transform ${snapBackDuration}ms ease-out`,
    },
  };
}
