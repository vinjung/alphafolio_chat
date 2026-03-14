import { z } from 'zod';

// ===== 기본 공통 스키마들 =====

/**
 * UUID v4 형식 검증
 * 예: "123e4567-e89b-12d3-a456-426614174000"
 */
export const uuidSchema = z.string().uuid('유효한 UUID 형식이 아닙니다.');

/**
 * 페이지네이션 파라미터 검증
 * limit: 1-100 범위
 * offset: 0 이상
 */
export const paginationSchema = z.object({
  limit: z
    .number()
    .int('정수여야 합니다.')
    .min(1, '최소 1개 이상이어야 합니다.')
    .max(100, '최대 100개까지 가능합니다.')
    .default(50),
  offset: z
    .number()
    .int('정수여야 합니다.')
    .min(0, '0 이상이어야 합니다.')
    .default(0),
});

/**
 * 일반적인 텍스트 입력 검증
 * 빈 문자열 방지, 앞뒤 공백 제거
 */
export const nonEmptyStringSchema = z
  .string()
  .trim()
  .min(1, '빈 문자열은 허용되지 않습니다.');

/**
 * 제목 검증 (채팅 세션 제목 등)
 * 1-200자 범위, 앞뒤 공백 제거
 */
export const titleSchema = z
  .string()
  .trim()
  .min(1, '제목이 비어있습니다.')
  .max(200, '제목은 200자를 초과할 수 없습니다.');

/**
 * URL 형식 검증
 * http:// 또는 https:// 프로토콜 필수
 */
export const urlSchema = z
  .string()
  .url('유효한 URL 형식이 아닙니다.')
  .refine(
    (url) => url.startsWith('http://') || url.startsWith('https://'),
    '프로토콜(http:// 또는 https://)이 필요합니다.'
  );

/**
 * 이메일 형식 검증
 */
export const emailSchema = z
  .string()
  .email('유효한 이메일 형식이 아닙니다.')
  .toLowerCase();

// ===== 타입 추출 =====
export type UUID = z.infer<typeof uuidSchema>;
export type Pagination = z.infer<typeof paginationSchema>;
export type NonEmptyString = z.infer<typeof nonEmptyStringSchema>;
export type Title = z.infer<typeof titleSchema>;
export type ValidUrl = z.infer<typeof urlSchema>;
export type Email = z.infer<typeof emailSchema>;
