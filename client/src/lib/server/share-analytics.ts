import { db } from './db';
import { shareActivityLogs, shareStatistics } from '@schema';
import { eq, and, count, sql, desc } from 'drizzle-orm';
import { logger } from '@/lib/utils/logger';
import type {
  // ShareActivityLog,
  // NewShareActivityLog,
  ShareStatistics,
  // NewShareStatistics,
} from './models';
import type { PageType, CountryCode } from '@/lib/validation/share-schemas';

const log = logger.child({ module: 'share-analytics' });

// ===== 공유 로깅 기능 =====

/**
 * 공유 활동 로그 기록 + 실시간 통계 업데이트
 * @param pageType - 페이지 타입 ('today' | 'future')
 * @param countryCode - 국가 코드 ('KR' | 'US')
 * @param userId - 사용자 ID (로그인한 경우)
 * @param userAgent - 브라우저 정보 (선택적)
 * @returns 로그 ID와 업데이트된 통계
 */
export async function logShareActivity(
  pageType: PageType,
  countryCode: CountryCode,
  userId?: string,
  userAgent?: string
): Promise<{
  logId: string;
  dailyCount: number;
  totalCount: number;
}> {
  const requestLog = log.child({
    function: 'logShareActivity',
    pageType,
    countryCode,
    userId: userId?.slice(0, 8) + '...' || 'anonymous',
  });

  requestLog.info('공유 활동 로깅 시작');

  try {
    // 트랜잭션으로 로그 기록 + 통계 업데이트를 원자적으로 처리
    const result = await db.transaction(async (tx) => {
      // 1. 활동 로그 기록
      const [activityLog] = await tx
        .insert(shareActivityLogs)
        .values({
          userId: userId || null,
          pageType,
          countryCode,
          userAgent: userAgent || null,
          createdAt: new Date(),
        })
        .returning({ id: shareActivityLogs.id });

      if (!activityLog) {
        throw new Error('활동 로그 생성에 실패했습니다.');
      }

      // 2. 현재 날짜의 통계 UPSERT
      const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD 형식

      // 전체 누적 카운트 계산
      const [totalCountResult] = await tx
        .select({ count: count() })
        .from(shareActivityLogs)
        .where(
          and(
            eq(shareActivityLogs.pageType, pageType),
            eq(shareActivityLogs.countryCode, countryCode)
          )
        );

      const totalCount = totalCountResult?.count || 0;

      // 통계 테이블 UPSERT
      const [statsResult] = await tx
        .insert(shareStatistics)
        .values({
          statDate: today,
          pageType,
          countryCode,
          dailyShareCount: 1,
          totalShareCount: totalCount,
          createdAt: new Date(),
          updatedAt: new Date(),
        })
        .onConflictDoUpdate({
          target: [
            shareStatistics.statDate,
            shareStatistics.pageType,
            shareStatistics.countryCode,
          ],
          set: {
            dailyShareCount: sql`${shareStatistics.dailyShareCount} + 1`,
            totalShareCount: totalCount,
            updatedAt: new Date(),
          },
        })
        .returning({
          dailyCount: shareStatistics.dailyShareCount,
          totalCount: shareStatistics.totalShareCount,
        });

      if (!statsResult) {
        throw new Error('통계 업데이트에 실패했습니다.');
      }

      return {
        logId: activityLog.id,
        dailyCount: statsResult.dailyCount,
        totalCount: statsResult.totalCount,
      };
    });

    requestLog.info('공유 활동 로깅 완료', {
      logId: result.logId,
      dailyCount: result.dailyCount,
      totalCount: result.totalCount,
    });

    return result;
  } catch (error) {
    requestLog.error('공유 활동 로깅 실패', error);
    throw new Error('공유 로깅 처리 중 오류가 발생했습니다.');
  }
}

// ===== 통계 조회 기능 =====

/**
 * 일별 공유 통계 조회
 * @param options - 조회 옵션
 * @returns 통계 데이터 배열
 */
export async function getShareStatistics(
  options: {
    startDate?: string;
    endDate?: string;
    pageType?: PageType;
    countryCode?: CountryCode;
    limit?: number;
  } = {}
): Promise<ShareStatistics[]> {
  const { startDate, endDate, pageType, countryCode, limit = 30 } = options;

  const requestLog = log.child({
    function: 'getShareStatistics',
    startDate,
    endDate,
    pageType,
    countryCode,
    limit,
  });

  requestLog.info('공유 통계 조회 시작');

  try {
    // WHERE 조건 구성
    const whereConditions = [];

    if (startDate) {
      whereConditions.push(sql`${shareStatistics.statDate} >= ${startDate}`);
    }

    if (endDate) {
      whereConditions.push(sql`${shareStatistics.statDate} <= ${endDate}`);
    }

    if (pageType) {
      whereConditions.push(eq(shareStatistics.pageType, pageType));
    }

    if (countryCode) {
      whereConditions.push(eq(shareStatistics.countryCode, countryCode));
    }

    // 쿼리 실행
    const query = db
      .select()
      .from(shareStatistics)
      .orderBy(desc(shareStatistics.statDate))
      .limit(limit);

    const results =
      whereConditions.length > 0
        ? await query.where(and(...whereConditions))
        : await query;

    requestLog.info('공유 통계 조회 완료', {
      resultCount: results.length,
    });

    return results;
  } catch (error) {
    requestLog.error('공유 통계 조회 실패', error);
    throw new Error('통계 조회 중 오류가 발생했습니다.');
  }
}

/**
 * 공유 통계 요약 정보 조회
 * @param pageType - 페이지 타입 (선택적)
 * @param countryCode - 국가 코드 (선택적)
 * @returns 요약 통계
 */
export async function getShareSummary(
  pageType?: PageType,
  countryCode?: CountryCode
): Promise<{
  totalShares: number;
  todayShares: number;
  activeUsers: number;
}> {
  const requestLog = log.child({
    function: 'getShareSummary',
    pageType,
    countryCode,
  });

  requestLog.info('공유 요약 통계 조회 시작');

  try {
    const today = new Date().toISOString().split('T')[0];

    // WHERE 조건 구성
    const logWhereConditions = [];
    const statsWhereConditions = [];

    if (pageType) {
      logWhereConditions.push(eq(shareActivityLogs.pageType, pageType));
      statsWhereConditions.push(eq(shareStatistics.pageType, pageType));
    }

    if (countryCode) {
      logWhereConditions.push(eq(shareActivityLogs.countryCode, countryCode));
      statsWhereConditions.push(eq(shareStatistics.countryCode, countryCode));
    }

    // 전체 공유 수
    const [totalSharesResult] = await db
      .select({ count: count() })
      .from(shareActivityLogs)
      .where(
        logWhereConditions.length > 0 ? and(...logWhereConditions) : undefined
      );

    // 오늘 공유 수
    const [todaySharesResult] = await db
      .select({ count: count() })
      .from(shareActivityLogs)
      .where(
        and(
          sql`DATE(${shareActivityLogs.createdAt}) = ${today}`,
          ...(logWhereConditions.length > 0 ? logWhereConditions : [])
        )
      );

    // 활성 사용자 수 (공유한 적 있는 로그인 사용자)
    const [activeUsersResult] = await db
      .select({ count: sql`COUNT(DISTINCT ${shareActivityLogs.userId})` })
      .from(shareActivityLogs)
      .where(
        and(
          sql`${shareActivityLogs.userId} IS NOT NULL`,
          ...(logWhereConditions.length > 0 ? logWhereConditions : [])
        )
      );

    const summary = {
      totalShares: totalSharesResult?.count || 0,
      todayShares: todaySharesResult?.count || 0,
      activeUsers: Number(activeUsersResult?.count) || 0,
    };

    requestLog.info('공유 요약 통계 조회 완료', summary);

    return summary;
  } catch (error) {
    requestLog.error('공유 요약 통계 조회 실패', error);
    throw new Error('요약 통계 조회 중 오류가 발생했습니다.');
  }
}
