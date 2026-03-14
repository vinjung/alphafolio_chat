import { db } from './db';
import { signupActivityLogs, userStatistics } from '@schema';
import { eq, and, count, sql } from 'drizzle-orm';
import { logger } from '@/lib/utils/logger';
import type { ActionType } from '@/lib/validation/signup-schemas';

const log = logger.child({ module: 'signup-analytics' });

// ===== 회원가입 로깅 기능 =====

/**
 * 회원가입 활동 로그 기록 + 실시간 통계 업데이트
 * @param userId - 회원가입한 사용자 ID
 * @param actionType - 액션 유형 ('signup' | 'login')
 * @param utmParams - UTM 파라미터들
 * @param userAgent - 브라우저 정보 (선택적)
 * @returns 로그 ID와 업데이트된 통계
 */
export async function logSignupActivity(
  userId: string,
  actionType: ActionType,
  utmParams: {
    utmSource?: string;
    utmMedium?: string;
    utmCampaign?: string;
    utmContent?: string;
  },
  userAgent?: string
): Promise<{
  logId: string;
  dailyCount: number;
  totalCount: number;
}> {
  const requestLog = log.child({
    function: 'logSignupActivity',
    actionType,
    userId: userId.slice(0, 8) + '...',
    hasUtmSource: !!utmParams.utmSource,
  });

  requestLog.info('회원가입 활동 로깅 시작');

  try {
    // 트랜잭션으로 로그 기록 + 통계 업데이트를 원자적으로 처리
    const result = await db.transaction(async (tx) => {
      // 1. 활동 로그 기록
      const [activityLog] = await tx
        .insert(signupActivityLogs)
        .values({
          userId,
          actionType,
          utmSource: utmParams.utmSource || null,
          utmMedium: utmParams.utmMedium || null,
          utmCampaign: utmParams.utmCampaign || null,
          utmContent: utmParams.utmContent || null,
          userAgent: userAgent || null,
          createdAt: new Date(),
        })
        .returning({ id: signupActivityLogs.id });

      if (!activityLog) {
        throw new Error('활동 로그 생성에 실패했습니다.');
      }

      // 2. 현재 날짜의 통계 UPSERT
      const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD 형식

      // 전체 누적 카운트 계산 (signup만 실제 가입자로 카운트)
      const [totalCountResult] = await tx
        .select({ count: count() })
        .from(signupActivityLogs)
        .where(eq(signupActivityLogs.actionType, 'signup'));

      const totalCount = totalCountResult?.count || 0;

      // userStatistics 테이블 UPSERT (signup만 통계에 반영)
      if (actionType === 'signup') {
        const [statsResult] = await tx
          .insert(userStatistics)
          .values({
            statDate: today,
            dailySignupCount: 1,
            totalSignupCount: totalCount,
            createdAt: new Date(),
            updatedAt: new Date(),
          })
          .onConflictDoUpdate({
            target: [userStatistics.statDate],
            set: {
              dailySignupCount: sql`${userStatistics.dailySignupCount} + 1`,
              totalSignupCount: totalCount,
              updatedAt: new Date(),
            },
          })
          .returning({
            dailyCount: userStatistics.dailySignupCount,
            totalCount: userStatistics.totalSignupCount,
          });

        return {
          logId: activityLog.id,
          dailyCount: statsResult?.dailyCount || 1,
          totalCount: statsResult?.totalCount || totalCount,
        };
      } else {
        // login은 로그만 남기고 통계는 업데이트하지 않음
        const [todayStatsResult] = await tx
          .select({
            dailyCount: userStatistics.dailySignupCount,
            totalCount: userStatistics.totalSignupCount,
          })
          .from(userStatistics)
          .where(eq(userStatistics.statDate, today));

        return {
          logId: activityLog.id,
          dailyCount: todayStatsResult?.dailyCount || 0,
          totalCount: todayStatsResult?.totalCount || totalCount,
        };
      }
    });

    requestLog.info('회원가입 활동 로깅 완료', {
      logId: result.logId,
      dailyCount: result.dailyCount,
      totalCount: result.totalCount,
    });

    return result;
  } catch (error) {
    requestLog.error('회원가입 활동 로깅 실패', error);
    throw new Error('회원가입 로깅 처리 중 오류가 발생했습니다.');
  }
}

// ===== 통계 조회 기능 =====

/**
 * 일별 회원가입 통계 조회
 * @param options - 조회 옵션
 * @returns 통계 데이터 배열
 */
export async function getSignupStatistics(
  options: {
    startDate?: string;
    endDate?: string;
    actionType?: ActionType;
    limit?: number;
  } = {}
): Promise<
  Array<{
    statDate: string;
    actionType: ActionType;
    dailySignupCount: number;
    totalSignupCount: number;
    createdAt: Date;
    updatedAt: Date;
  }>
> {
  const { startDate, endDate, actionType, limit = 30 } = options;

  const requestLog = log.child({
    function: 'getSignupStatistics',
    startDate,
    endDate,
    actionType,
    limit,
  });

  requestLog.info('회원가입 통계 조회 시작');

  try {
    // signupActivityLogs에서 집계해서 반환 (더 상세한 분석 가능)
    const whereConditions = [];

    if (startDate) {
      whereConditions.push(
        sql`DATE(${signupActivityLogs.createdAt}) >= ${startDate}`
      );
    }

    if (endDate) {
      whereConditions.push(
        sql`DATE(${signupActivityLogs.createdAt}) <= ${endDate}`
      );
    }

    if (actionType) {
      whereConditions.push(eq(signupActivityLogs.actionType, actionType));
    }

    const query = db
      .select({
        statDate: sql<string>`DATE(${signupActivityLogs.createdAt})`.as(
          'stat_date'
        ),
        actionType: signupActivityLogs.actionType,
        dailySignupCount: sql<number>`COUNT(*)`.as('daily_signup_count'),
        totalSignupCount: sql<number>`COUNT(*) OVER()`.as('total_signup_count'),
        createdAt: sql<Date>`MIN(${signupActivityLogs.createdAt})`.as(
          'created_at'
        ),
        updatedAt: sql<Date>`MAX(${signupActivityLogs.createdAt})`.as(
          'updated_at'
        ),
      })
      .from(signupActivityLogs)
      .groupBy(
        sql`DATE(${signupActivityLogs.createdAt})`,
        signupActivityLogs.actionType
      )
      .orderBy(sql`DATE(${signupActivityLogs.createdAt}) DESC`)
      .limit(limit);

    const results =
      whereConditions.length > 0
        ? await query.where(and(...whereConditions))
        : await query;

    // 🔧 타입 캐스팅으로 해결
    const typedResults = results.map((result) => ({
      ...result,
      actionType: result.actionType as ActionType,
    }));

    requestLog.info('회원가입 통계 조회 완료', {
      resultCount: typedResults.length,
    });

    return typedResults;
  } catch (error) {
    requestLog.error('회원가입 통계 조회 실패', error);
    throw new Error('통계 조회 중 오류가 발생했습니다.');
  }
}

/**
 * 회원가입 통계 요약 정보 조회
 * @param signupType - 회원가입 유형 (선택적)
 * @param countryCode - 국가 코드 (선택적)
 * @returns 요약 통계
 */
export async function getSignupSummary(actionType?: ActionType): Promise<{
  totalSignups: number;
  todaySignups: number;
  newUserSignups: number;
  existingUserLogins: number;
}> {
  const requestLog = log.child({
    function: 'getSignupSummary',
    actionType,
  });

  requestLog.info('회원가입 요약 통계 조회 시작');

  try {
    const today = new Date().toISOString().split('T')[0];

    // WHERE 조건 구성
    const whereConditions = [];

    if (actionType) {
      whereConditions.push(eq(signupActivityLogs.actionType, actionType));
    }

    // 전체 회원가입 수
    const [totalSignupsResult] = await db
      .select({ count: count() })
      .from(signupActivityLogs)
      .where(whereConditions.length > 0 ? and(...whereConditions) : undefined);

    // 오늘 회원가입 수
    const [todaySignupsResult] = await db
      .select({ count: count() })
      .from(signupActivityLogs)
      .where(
        and(
          sql`DATE(${signupActivityLogs.createdAt}) = ${today}`,
          ...(whereConditions.length > 0 ? whereConditions : [])
        )
      );

    // 신규 사용자 수 (signup 액션)
    const [newUserResult] = await db
      .select({ count: count() })
      .from(signupActivityLogs)
      .where(eq(signupActivityLogs.actionType, 'signup'));

    // 기존 사용자 로그인 수 (login 액션)
    const [existingUserResult] = await db
      .select({ count: count() })
      .from(signupActivityLogs)
      .where(eq(signupActivityLogs.actionType, 'login'));

    const summary = {
      totalSignups: totalSignupsResult?.count || 0,
      todaySignups: todaySignupsResult?.count || 0,
      newUserSignups: newUserResult?.count || 0,
      existingUserLogins: existingUserResult?.count || 0,
    };

    requestLog.info('회원가입 요약 통계 조회 완료', summary);

    return summary;
  } catch (error) {
    requestLog.error('회원가입 요약 통계 조회 실패', error);
    throw new Error('요약 통계 조회 중 오류가 발생했습니다.');
  }
}
