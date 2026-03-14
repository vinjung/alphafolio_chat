import { z } from 'zod';
import { NextResponse } from 'next/server';
import { logger } from '@/lib/utils/logger';
import { uuidSchema } from './common-schemas';

const log = logger.child({ module: 'validation' });

// ===== 검증 결과 타입 =====
export interface ValidationResult<T> {
  success: boolean;
  data?: T;
  error?: {
    message: string;
    details?: Array<{
      field: string;
      message: string;
    }>;
  };
}

// ===== 검증 유틸리티 함수들 =====

/**
 * Zod 스키마로 데이터를 안전하게 검증
 * @param schema - Zod 스키마
 * @param data - 검증할 데이터
 * @returns 검증 결과 객체
 */
export function validateData<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): ValidationResult<T> {
  try {
    const validatedData = schema.parse(data);
    return {
      success: true,
      data: validatedData,
    };
  } catch (error) {
    if (error instanceof z.ZodError) {
      log.warn('검증 실패', {
        errorCount: error.errors.length,
        errors: error.errors.map((err) => ({
          path: err.path.join('.'),
          message: err.message,
        })),
      });

      return {
        success: false,
        error: {
          message: '입력 데이터 검증에 실패했습니다.',
          details: error.errors.map((err) => ({
            field: err.path.join('.') || 'root',
            message: err.message,
          })),
        },
      };
    }

    // Zod 에러가 아닌 경우
    log.error('예상치 못한 검증 에러', error);
    return {
      success: false,
      error: {
        message: '검증 중 예상치 못한 오류가 발생했습니다.',
      },
    };
  }
}

// validateUUID 제거 - 사용되지 않음 (body 검증은 zod 스키마에서 처리)

/**
 * URL 파라미터에서 UUID 검증
 * @param params - Next.js params 객체
 * @param paramName - 파라미터명
 * @returns 검증 결과
 */
export async function validateUUIDParam(
  params: Promise<Record<string, string>>,
  paramName: string
): Promise<ValidationResult<string>> {
  try {
    const resolvedParams = await params;
    const value = resolvedParams[paramName];

    if (!value) {
      return {
        success: false,
        error: {
          message: `${paramName}가 필요합니다.`,
        },
      };
    }

    return validateData(uuidSchema, value);
  } catch (error) {
    log.error('파라미터 추출 실패', { paramName, error });
    return {
      success: false,
      error: {
        message: '파라미터 처리 중 오류가 발생했습니다.',
      },
    };
  }
}

/**
 * API 라우트에서 사용할 검증 응답 생성
 * @param validationResult - 검증 결과
 * @param successCallback - 검증 성공 시 실행할 콜백
 * @returns NextResponse 또는 콜백 결과
 */
export async function handleValidation<T, R>(
  validationResult: ValidationResult<T>,
  successCallback: (data: T) => Promise<R> | R
): Promise<NextResponse | R> {
  if (!validationResult.success) {
    log.warn('API 검증 실패', {
      message: validationResult.error?.message,
      detailCount: validationResult.error?.details?.length || 0,
    });

    return NextResponse.json(
      {
        error: validationResult.error?.message || '검증 실패',
        details: validationResult.error?.details,
      },
      { status: 400 }
    );
  }

  return successCallback(validationResult.data!);
}

/**
 * JSON 요청 본문을 안전하게 파싱
 * @param request - Next.js Request 객체
 * @returns 파싱된 데이터 또는 에러
 */
export async function parseRequestBody(
  request: Request
): Promise<ValidationResult<unknown>> {
  try {
    const body = await request.json();
    return {
      success: true,
      data: body,
    };
  } catch (error) {
    log.warn('JSON 파싱 실패', { error });
    return {
      success: false,
      error: {
        message: '잘못된 JSON 형식입니다.',
      },
    };
  }
}

/**
 * 쿼리 파라미터를 안전하게 추출
 * @param url - URL 객체
 * @param schema - 검증할 스키마
 * @returns 검증된 쿼리 파라미터
 */
export function validateSearchParams<T>(
  url: URL,
  schema: z.ZodSchema<T>
): ValidationResult<T> {
  try {
    // URLSearchParams를 일반 객체로 변환
    const params: Record<string, string> = {};
    url.searchParams.forEach((value, key) => {
      params[key] = value;
    });

    return validateData(schema, params);
  } catch (error) {
    log.warn('쿼리 파라미터 파싱 실패', { error });
    return {
      success: false,
      error: {
        message: '쿼리 파라미터 처리 중 오류가 발생했습니다.',
      },
    };
  }
}

/**
 * 빠른 검증 헬퍼 - 성공 시 데이터 반환, 실패 시 에러 throw
 * @param schema - Zod 스키마
 * @param data - 검증할 데이터
 * @returns 검증된 데이터
 * @throws ValidationError
 */
export function validateOrThrow<T>(schema: z.ZodSchema<T>, data: unknown): T {
  const result = validateData(schema, data);
  if (!result.success) {
    throw new ValidationError(
      result.error?.message || '검증 실패',
      result.error?.details
    );
  }
  return result.data!;
}

// ===== 커스텀 에러 클래스 =====
export class ValidationError extends Error {
  constructor(
    message: string,
    public details?: Array<{ field: string; message: string }>
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

// ===== 스키마 re-export =====
export * from './common-schemas';
export * from './chat-schemas';
