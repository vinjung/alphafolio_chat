import { NextRequest, NextResponse } from 'next/server';
import { getCurrentSession } from '@/lib/server/session';
import { db } from '@/lib/server/db';
import { redis } from '@/lib/server/redis';
import { dailyUserRetention } from '@schema';
import type { NewDailyUserRetention } from '@/lib/server/models';
import { logger } from '@/lib/utils/logger';

const log = logger.child({ module: 'retention-api' });

/**
 * 한국 시간(KST) 기준으로 당일 자정까지 남은 초를 계산
 */
function getSecondsUntilMidnightKST(): number {
  const now = new Date();
  const kstOffset = 9 * 60 * 60 * 1000;
  const kstNow = new Date(now.getTime() + kstOffset);

  const nextMidnight = new Date(kstNow);
  nextMidnight.setUTCHours(24, 0, 0, 0);

  const msUntilMidnight = nextMidnight.getTime() - kstNow.getTime();
  return Math.max(1, Math.ceil(msUntilMidnight / 1000));
}

/**
 * 한국 시간(KST) 기준으로 오늘 날짜 문자열 반환
 */
function getTodayKST(): string {
  const now = new Date();
  const kstOffset = 9 * 60 * 60 * 1000;
  const kstNow = new Date(now.getTime() + kstOffset);

  return kstNow.toISOString().split('T')[0];
}

/**
 * POST /api/retention
 * 단순화된 일일 리텐션 추적 API
 */
export async function POST(request: NextRequest) {
  try {
    // 1. 세션 체크 (회원만)
    const { user } = await getCurrentSession();
    if (!user) {
      return NextResponse.json(
        { error: '로그인이 필요합니다.' },
        { status: 401 }
      );
    }

    // 2. 요청 데이터 추출
    const body = await request.json();
    const page = body.page || 'app';
    const today = getTodayKST();
    const cacheKey = `retention:${user.id}:${today}`;

    // 3. Redis 캐시 체크
    const exists = await redis.exists(cacheKey);
    if (exists) {
      const remainingTTL = await redis.ttl(cacheKey);

      log.debug('오늘 이미 리텐션 기록됨', {
        userId: user.id,
        date: today,
        remainingTTL,
      });

      return NextResponse.json({
        success: true,
        message: '오늘 이미 기록됨',
        cached: true,
        ttlSeconds: remainingTTL > 0 ? remainingTTL : 0,
      });
    }

    // 4. 단순 리텐션 데이터 생성
    const retentionData: NewDailyUserRetention = {
      userId: user.id,
      activityDate: today,
      entryPage: page,
      visitTime: new Date(),
    };

    // 5. DB 삽입 (충돌 시 무시)
    await db
      .insert(dailyUserRetention)
      .values(retentionData)
      .onConflictDoNothing();

    // 6. 자정까지 캐시 설정
    const ttlSeconds = getSecondsUntilMidnightKST();
    await redis.setex(cacheKey, ttlSeconds, '1');

    log.info('일일 리텐션 기록 완료', {
      userId: user.id,
      date: today,
      entryPage: page,
      ttlSeconds,
    });

    return NextResponse.json({
      success: true,
      message: '리텐션 기록 완료',
      cached: false,
      ttlSeconds,
    });
  } catch (error) {
    log.error('리텐션 API 오류', error);

    return NextResponse.json(
      {
        error: '리텐션 기록 실패',
        success: false,
      },
      { status: 500 }
    );
  }
}
