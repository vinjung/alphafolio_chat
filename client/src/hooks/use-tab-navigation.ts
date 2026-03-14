'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useCallback, useMemo } from 'react';

// Tab 타입 정의를 확장하여 동적 경로 패턴을 포함
export type Tab = {
  label: string;
  href: string;
  id?: string;
  iconKey?: string;
  activePaths?: string[];
  dynamicPatterns?: string[]; // 동적 경로 패턴 배열 추가
};

// 동적 경로 패턴 매칭 함수
function matchesDynamicPattern(pathname: string, pattern: string): boolean {
  // [chatId] 같은 동적 세그먼트를 정규식으로 변환
  const regexPattern = pattern.replace(/\[[\w]+\]/g, '[^/]+');
  const regex = new RegExp(`^${regexPattern}$`);
  return regex.test(pathname);
}

export function useTabNavigation(tabs: Tab[]) {
  const pathname = usePathname();
  const router = useRouter();

  const activeIndex = useMemo(
    () =>
      tabs.findIndex((tab) => {
        // 1. 정확한 경로 매칭 (기존 방식)
        if (tab.href === pathname) {
          return true;
        }

        // 2. activePaths 배열에서 매칭 확인
        if (tab.activePaths && tab.activePaths.includes(pathname)) {
          return true;
        }

        // 3. 동적 경로 패턴 매칭 (새로 추가)
        if (tab.dynamicPatterns) {
          return tab.dynamicPatterns.some((pattern) =>
            matchesDynamicPattern(pathname, pattern)
          );
        }

        return false;
      }),
    [pathname, tabs]
  );

  const onTabChange = useCallback(
    (href: string) => {
      router.push(href);
    },
    [router]
  );

  return { activeIndex, onTabChange };
}
