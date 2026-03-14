'use server';

import { getCurrentSession } from '@/lib/server/session';
import { db } from '@/lib/server/db';
import { users } from '@schema';
import { eq } from 'drizzle-orm';
import { revalidatePath } from 'next/cache';
import { globalPOSTRateLimit } from '@/lib/server/request';
import { logger } from '@/lib/utils/logger';
import { generateThumbnailUrl } from '@/lib/utils/cloudinary-upload';

const log = logger.child({ module: 'user-actions' });

interface UpdateProfileResult {
  success: boolean;
  message?: string;
  errors?: {
    nickname?: string;
  };
}

interface UpdateData {
  nickname?: string;
  profileImageUrl?: string;
  thumbnailImageUrl?: string;
  updatedAt: Date;
}

/**
 * 프로필 업데이트 액션
 */
export async function updateProfileAction(
  formData: FormData
): Promise<UpdateProfileResult> {
  log.info('프로필 업데이트 액션 시작');

  // Rate limiting
  if (!globalPOSTRateLimit()) {
    log.warn('Rate limit 초과');
    return { success: false, message: 'Too many requests' };
  }

  // 세션 체크
  const { user } = await getCurrentSession();
  if (!user) {
    log.warn('인증되지 않은 사용자');
    return { success: false, message: 'Not authenticated' };
  }

  // 폼 데이터 추출
  const nickname = formData.get('nickname') as string;
  const profileImageUrl = formData.get('profileImageUrl') as string;

  // 업데이트할 데이터 객체
  const updateData: UpdateData = {
    updatedAt: new Date(),
  };

  // 닉네임이 있으면 validation 후 추가
  if (nickname) {
    const validation = validateNickname(nickname);
    if (!validation.isValid) {
      log.warn('닉네임 validation 실패', {
        nickname,
        error: validation.message,
      });
      return {
        success: false,
        errors: { nickname: validation.message },
      };
    }
    updateData.nickname = nickname.trim();
  }

  // 프로필 이미지 URL이 있으면 썸네일 URL도 함께 생성
  if (profileImageUrl) {
    try {
      new URL(profileImageUrl);
      updateData.profileImageUrl = profileImageUrl;
      updateData.thumbnailImageUrl = generateThumbnailUrl(profileImageUrl);

      log.info('프로필 이미지 URL 업데이트', {
        originalUrl: profileImageUrl.substring(0, 50) + '...',
        thumbnailUrl: updateData.thumbnailImageUrl.substring(0, 50) + '...',
      });
    } catch {
      log.warn('잘못된 프로필 이미지 URL', { profileImageUrl });
      return { success: false, message: '잘못된 이미지 URL입니다.' };
    }
  }

  try {
    // DB 업데이트
    await db.update(users).set(updateData).where(eq(users.id, user.id));

    const updatedFields = Object.keys(updateData).filter(
      (key) => key !== 'updatedAt'
    );
    log.info('프로필 업데이트 성공', {
      userId: user.id.substring(0, 8) + '...',
      updatedFields,
    });

    // 캐시 무효화 (홈 레이아웃에서 썸네일 이미지 새로고침을 위해)
    revalidatePath('/mypage');
    revalidatePath('/today');
    revalidatePath('/future');

    return { success: true, message: '프로필이 업데이트되었습니다!' };
  } catch (dbError) {
    log.error('프로필 업데이트 실패', dbError);
    return { success: false, message: '프로필 업데이트에 실패했습니다.' };
  }
}

/**
 * 닉네임 validation 함수
 */
function validateNickname(nickname: string): {
  isValid: boolean;
  message: string;
} {
  if (!nickname || nickname.trim() === '') {
    return {
      isValid: false,
      message: '닉네임이 비어있어요! 전설의 그 이름 지어주세요!',
    };
  }

  const trimmed = nickname.trim();

  if (trimmed.length < 2) {
    return { isValid: false, message: '닉네임은 최소 2자 이상... 좀만 더...' };
  }

  if (trimmed.length > 8) {
    return {
      isValid: false,
      message: '닉네임은 최대 8자까지 가능! 너무 길면 기억못돼',
    };
  }

  // 한글, 영어, 숫자만 허용
  if (!/^[가-힣a-zA-Z0-9]+$/.test(trimmed)) {
    return {
      isValid: false,
      message: '특수문자는 안 돼상. 한글, 영어, 숫자만 써주세요!',
    };
  }

  return { isValid: true, message: '' };
}
