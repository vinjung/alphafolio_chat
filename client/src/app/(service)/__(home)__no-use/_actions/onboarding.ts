'use server';

import { db } from '@/lib/server/db'; // Drizzle DB 인스턴스
import { users } from '@schema'; // users 스키마
import { eq } from 'drizzle-orm';
import { getCurrentSession } from '@/lib/server/session'; // 현재 세션 가져오기
import { revalidatePath } from 'next/cache'; // 페이지 캐시 갱신
import { logger } from '@/lib/utils/logger'; // 로거 임포트

const log = logger.child({ module: 'onboarding-action' }); // 모듈별 로거 인스턴스

/**
 * 사용자의 온보딩 완료 상태를 업데이트하는 서버 액션.
 * @returns {Promise<{ success: boolean; message?: string }>} 작업 성공 여부와 메시지
 */
export async function completeOnboardingAction(): Promise<{
  success: boolean;
  message?: string;
}> {
  log.info('completeOnboardingAction 시작');
  const { user } = await getCurrentSession();

  if (!user) {
    log.warn('인증되지 않은 사용자가 온보딩 완료 시도.');
    return { success: false, message: 'User not authenticated.' };
  }

  try {
    await db
      .update(users)
      .set({ hasCompletedOnboarding: true })
      .where(eq(users.id, user.id)); //

    log.info(`사용자 ${user.id} 온보딩 완료 상태 업데이트 성공.`);

    // 온보딩 완료 후 해당 페이지의 캐시를 갱신하여 MaskOverlay가 사라지도록 합니다.
    // HomeLayout이 적용되는 모든 경로를 revalidatePath하는 것이 안전합니다.
    revalidatePath('/today');
    revalidatePath('/future');

    return { success: true, message: 'Onboarding completed successfully.' };
  } catch (error) {
    log.error('온보딩 완료 상태 업데이트 실패:', error);
    return { success: false, message: 'Failed to update onboarding status.' };
  }
}
