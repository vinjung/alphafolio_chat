'use server';

import { getCurrentSession } from '@/lib/server/session';
import {
  deleteSessionTokenCookie,
  invalidateSession,
  invalidateAllSessions, // ✅ 추가
} from '@/lib/server/session';
import { redirect } from 'next/navigation';
import { softDeleteUser } from '@/lib/server/user'; // ✅ 변경: deleteUser → softDeleteUser
import { globalPOSTRateLimit } from '@/lib/server/request';
import { logger } from '@/lib/utils/logger'; // ✅ 추가

const log = logger.child({ module: 'auth-actions' }); // ✅ 추가

/**
 * 로그아웃 액션
 */
export async function logoutAction(): Promise<void> {
  if (!globalPOSTRateLimit()) {
    throw new Error('Too many request');
  }

  const { session } = await getCurrentSession();
  if (session === null) {
    throw new Error('Not authenticated');
  }

  invalidateSession(session.id);
  deleteSessionTokenCookie();
  return redirect('/');
}

/**
 * 회원탈퇴 액션 (소프트 삭제)
 * ✅ 실제 삭제 대신 deleted_at 설정으로 변경
 */
export async function deleteAccountAction(): Promise<void> {
  const { session, user } = await getCurrentSession();
  if (!session || !user) {
    throw new Error('Not authenticated');
  }

  log.info('회원탈퇴 처리 시작', {
    userId: user.id.substring(0, 8) + '...',
    email: user.email,
    nickname: user.nickname,
  });

  try {
    // 🔗 카카오 연동 해제
    const res = await fetch('https://kapi.kakao.com/v1/user/unlink', {
      method: 'POST',
      headers: {
        Authorization: `KakaoAK ${process.env.KAKAO_ADMIN_KEY}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        target_id_type: 'user_id',
        target_id: user.oauthId!,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      log.error('카카오 언링크 실패', err);
      throw new Error(`Failed to unlink: ${err.error_message || res.status}`);
    }

    log.info('카카오 연동 해제 완료');

    // ✅ 소프트 삭제 (기존 채팅 한도 유지)
    const deletedUser = await softDeleteUser(user.id);

    log.info('사용자 소프트 삭제 완료', {
      userId: deletedUser.id.substring(0, 8) + '...',
      deletedAt: deletedUser.deletedAt,
    });

    // 🔒 모든 세션 무효화
    await invalidateAllSessions(user.id);
    await deleteSessionTokenCookie();

    log.info('회원탈퇴 처리 완료', {
      userId: user.id.substring(0, 8) + '...',
    });
  } catch (error) {
    log.error('회원탈퇴 처리 실패', error);
    throw error; // 에러를 다시 throw하여 UI에서 처리할 수 있도록
  }

  redirect('/');
}
