'use client';

import type { ActionType } from '@/lib/validation/signup-schemas';

/**
 * UTM 파라미터를 URL에서 추출하는 유틸리티 함수
 */
function extractUtmParams(): {
  utmSource?: string;
  utmMedium?: string;
  utmCampaign?: string;
  utmContent?: string;
} {
  if (typeof window === 'undefined') return {};

  const urlParams = new URLSearchParams(window.location.search);

  return {
    utmSource: urlParams.get('utm_source') || undefined,
    utmMedium: urlParams.get('utm_medium') || undefined,
    utmCampaign: urlParams.get('utm_campaign') || undefined,
    utmContent: urlParams.get('utm_content') || undefined,
  };
}

/**
 * 액션 유형을 UTM 파라미터에서 추출하는 함수
 */
function extractActionTypeFromUtm(): ActionType | null {
  const { utmContent } = extractUtmParams();

  if (utmContent === 'signup' || utmContent === 'login') {
    return utmContent as ActionType;
  }

  return null;
}

/**
 * 회원가입/로그인 트래킹 API 호출 함수
 */
export async function logSignupTracking(actionType: ActionType): Promise<void> {
  try {
    // UTM 파라미터 추출
    const utmParams = extractUtmParams();

    const response = await fetch('/api/signup/log', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        actionType,
        ...utmParams,
      }),
    });

    if (!response.ok) {
      throw new Error(`로깅 실패: ${response.status}`);
    }

    const result = await response.json();
    console.log('📊 회원가입 로깅 성공:', {
      logId: result.data?.logId,
      dailyCount: result.data?.dailyCount,
      totalCount: result.data?.totalCount,
      actionType,
      utmParams,
    });
  } catch (error) {
    // 로깅 실패는 사용자 경험에 영향주지 않도록 조용히 처리
    console.warn('📊 회원가입 로깅 실패 (기능에는 영향 없음):', error);
  }
}

/**
 * 페이지 로드 시 자동으로 UTM 파라미터를 기반으로 트래킹하는 함수
 * 카카오 로그인 리다이렉트 후 /today 페이지에서 호출하면 됨
 */
export function autoTrackSignupFromUtm(): void {
  if (typeof window === 'undefined') return;

  // 중복 트래킹 방지 - 세션스토리지 체크
  const trackingKey = 'signup_tracked_session';
  const alreadyTracked = sessionStorage.getItem(trackingKey);

  if (alreadyTracked) {
    console.log('📊 이번 세션에서 이미 트래킹됨 - 건너뜀');
    return;
  }

  // UTM 파라미터에서 액션 유형 추출
  const actionType = extractActionTypeFromUtm();

  if (!actionType) {
    console.log('📊 UTM 파라미터에서 액션 유형을 찾을 수 없음 - 트래킹 건너뜀');
    return;
  }

  // 트래킹 실행
  logSignupTracking(actionType);

  // 세션 동안 중복 방지 마킹
  sessionStorage.setItem(trackingKey, 'true');

  // 🚫 UTM 파라미터 제거 비활성화 (SSR 구조 보호 + GA 트래킹 유지)
  // const url = new URL(window.location.href);
  // url.searchParams.delete('utm_source');
  // url.searchParams.delete('utm_medium');
  // url.searchParams.delete('utm_campaign');
  // url.searchParams.delete('utm_content');
  // window.history.replaceState({}, '', url.toString());
}

/**
 * 수동으로 회원가입 트래킹을 호출하는 함수
 * 특정 이벤트나 액션에서 호출할 때 사용
 */
export function manualTrackSignup(actionType: ActionType): void {
  logSignupTracking(actionType);
}

/**
 * 디버깅용: 현재 UTM 파라미터 확인 함수
 */
export function debugUtmParams(): void {
  if (typeof window === 'undefined') return;

  const utmParams = extractUtmParams();
  const actionType = extractActionTypeFromUtm();

  console.log('🔍 현재 UTM 파라미터:', {
    ...utmParams,
    extractedActionType: actionType,
    currentUrl: window.location.href,
  });
}
