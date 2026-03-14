import { z } from 'zod';

// ===== 공유 로깅 관련 스키마 =====

/**
 * 페이지 타입 검증
 */
export const pageTypeSchema = z.enum(['today', 'future'], {
  errorMap: () => ({ message: "'today' 또는 'future'만 허용됩니다." }),
});

/**
 * 국가 코드 검증
 */
export const countryCodeSchema = z.enum(['KR', 'US'], {
  errorMap: () => ({ message: "'KR' 또는 'US'만 허용됩니다." }),
});

/**
 * User Agent 검증 (선택적)
 */
export const userAgentSchema = z
  .string()
  .max(500, 'User Agent는 500자를 초과할 수 없습니다.')
  .optional();

/**
 * 공유 로깅 요청 검증
 */
export const shareLogRequestSchema = z.object({
  pageType: pageTypeSchema,
  countryCode: countryCodeSchema,
  userAgent: userAgentSchema,
});

/**
 * 공유 통계 조회 쿼리 파라미터 검증
 */
export const shareStatsQuerySchema = z
  .object({
    startDate: z
      .string()
      .regex(/^\d{4}-\d{2}-\d{2}$/, '날짜는 YYYY-MM-DD 형식이어야 합니다.')
      .optional(),
    endDate: z
      .string()
      .regex(/^\d{4}-\d{2}-\d{2}$/, '날짜는 YYYY-MM-DD 형식이어야 합니다.')
      .optional(),
    pageType: pageTypeSchema.optional(),
    countryCode: countryCodeSchema.optional(),
  })
  .refine(
    (data) => {
      if (data.startDate && data.endDate) {
        return new Date(data.startDate) <= new Date(data.endDate);
      }
      return true;
    },
    {
      message: '시작 날짜는 종료 날짜보다 늦을 수 없습니다.',
      path: ['startDate'],
    }
  );

// ===== 타입 추출 =====
export type PageType = z.infer<typeof pageTypeSchema>;
export type CountryCode = z.infer<typeof countryCodeSchema>;
export type ShareLogRequest = z.infer<typeof shareLogRequestSchema>;
export type ShareStatsQuery = z.infer<typeof shareStatsQuerySchema>;

// ===== 응답 타입 정의 =====
export interface ShareLogResponse {
  success: true;
  data: {
    logId: string;
    dailyCount: number;
    totalCount: number;
  };
}

export interface ShareStatsResponse {
  success: true;
  data: {
    dailyStats: Array<{
      statDate: string;
      pageType: PageType;
      countryCode: CountryCode;
      dailyShareCount: number;
      totalShareCount: number;
    }>;
    summary: {
      totalDays: number;
      totalShares: number;
      averagePerDay: number;
    };
  };
}

// ===== 에러 응답 타입 =====
export interface ShareErrorResponse {
  success: false;
  error: string;
  details?: Array<{ field: string; message: string }>;
}
