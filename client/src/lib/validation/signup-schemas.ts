import { z } from 'zod';

// ===== 회원가입 트래킹 관련 스키마 =====

/**
 * 액션 유형 검증 (회원가입, 로그인, 계정 복원)
 */
export const actionTypeSchema = z.enum(['signup', 'login', 'restore'], {
  errorMap: () => ({
    message: "'signup', 'login', 또는 'restore'만 허용됩니다.",
  }),
});

/**
 * UTM 파라미터 검증 (선택적)
 */
export const utmSourceSchema = z
  .string()
  .max(50, 'UTM Source는 50자를 초과할 수 없습니다.')
  .optional();

export const utmMediumSchema = z
  .string()
  .max(50, 'UTM Medium은 50자를 초과할 수 없습니다.')
  .optional();

export const utmCampaignSchema = z
  .string()
  .max(50, 'UTM Campaign은 50자를 초과할 수 없습니다.')
  .optional();

export const utmContentSchema = z
  .string()
  .max(50, 'UTM Content는 50자를 초과할 수 없습니다.')
  .optional();

/**
 * User Agent 검증 (선택적)
 */
export const userAgentSchema = z
  .string()
  .max(500, 'User Agent는 500자를 초과할 수 없습니다.')
  .optional();

/**
 * 회원가입 트래킹 요청 검증
 */
export const signupLogRequestSchema = z.object({
  actionType: actionTypeSchema,
  utmSource: utmSourceSchema,
  utmMedium: utmMediumSchema,
  utmCampaign: utmCampaignSchema,
  utmContent: utmContentSchema,
  userAgent: userAgentSchema,
});

/**
 * 회원가입 통계 조회 쿼리 파라미터 검증
 */
export const signupStatsQuerySchema = z
  .object({
    startDate: z
      .string()
      .regex(/^\d{4}-\d{2}-\d{2}$/, '날짜는 YYYY-MM-DD 형식이어야 합니다.')
      .optional(),
    endDate: z
      .string()
      .regex(/^\d{4}-\d{2}-\d{2}$/, '날짜는 YYYY-MM-DD 형식이어야 합니다.')
      .optional(),
    actionType: actionTypeSchema.optional(),
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
export type ActionType = z.infer<typeof actionTypeSchema>;
export type SignupLogRequest = z.infer<typeof signupLogRequestSchema>;
export type SignupStatsQuery = z.infer<typeof signupStatsQuerySchema>;

// ===== 응답 타입 정의 =====
export interface SignupLogResponse {
  success: true;
  data: {
    logId: string;
    dailyCount: number;
    totalCount: number;
  };
}

export interface SignupStatsResponse {
  success: true;
  data: {
    dailyStats: Array<{
      statDate: string;
      actionType: ActionType;
      dailySignupCount: number;
      totalSignupCount: number;
    }>;
    summary: {
      totalDays: number;
      totalSignups: number;
      averagePerDay: number;
    };
  };
}

// ===== 에러 응답 타입 =====
export interface SignupErrorResponse {
  success: false;
  error: string;
  details?: Array<{ field: string; message: string }>;
}
