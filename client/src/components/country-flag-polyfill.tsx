'use client';

import { useEffect } from 'react';
import { polyfillCountryFlagEmojis } from 'country-flag-emoji-polyfill';

/**
 * 국가 이모지 폴리필 컴포넌트
 */
export function CountryFlagPolyfill() {
  useEffect(() => {
    // 이미 적용되었는지 확인
    if (window.__countryFlagPolyfillApplied) {
      return;
    }

    try {
      // 폴리필 함수 호출
      polyfillCountryFlagEmojis();

      // 중복 실행 방지 플래그
      window.__countryFlagPolyfillApplied = true;
    } catch (error) {
      console.error('❌ 폴리필 적용 실패:', error);
    }
  }, []);

  return null;
}

// TypeScript 타입 확장
declare global {
  interface Window {
    __countryFlagPolyfillApplied?: boolean;
  }
}
