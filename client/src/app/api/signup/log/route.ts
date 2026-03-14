import { NextRequest, NextResponse } from 'next/server';
import { getCurrentSession } from '@/lib/server/session';
import { logSignupActivity } from '@/lib/server/signup-analytics';
import { validateData, parseRequestBody } from '@/lib/validation';
import { signupLogRequestSchema } from '@/lib/validation/signup-schemas';
import {
  logger,
  createCorrelationId,
  extractRequestMeta,
} from '@/lib/utils/logger';
import type {
  SignupLogResponse,
  SignupErrorResponse,
} from '@/lib/validation/signup-schemas';

/**
 * POST /api/signup/log
 * 사용자의 회원가입/로그인을 트래킹하고 실시간 통계를 업데이트합니다.
 * 로그인한 사용자만 사용 가능합니다.
 */
export async function POST(
  request: NextRequest
): Promise<NextResponse<SignupLogResponse | SignupErrorResponse>> {
  // 상관관계 ID 및 요청 메타데이터 생성
  const correlationId = createCorrelationId();
  const requestMeta = extractRequestMeta(request);

  const requestLog = logger.child({
    correlationId,
    module: 'signup-log-api',
    ...requestMeta,
  });

  requestLog.info('회원가입 로깅 API 요청 시작');

  try {
    // 1. 사용자 인증 확인 (필수 - 로그인 사용자만 허용)
    const { user } = await getCurrentSession();

    if (!user) {
      requestLog.warn('인증되지 않은 사용자의 회원가입 로깅 시도');
      return NextResponse.json<SignupErrorResponse>(
        {
          success: false,
          error: '인증이 필요합니다.',
        },
        { status: 401 }
      );
    }

    // 2. 요청 본문 파싱
    const bodyResult = await parseRequestBody(request);
    if (!bodyResult.success) {
      requestLog.warn('요청 본문 파싱 실패', { error: bodyResult.error });
      return NextResponse.json(
        {
          success: false,
          error: bodyResult.error?.message || '잘못된 요청 형식입니다.',
        },
        { status: 400 }
      );
    }

    // 3. 요청 데이터 검증
    const validationResult = validateData(
      signupLogRequestSchema,
      bodyResult.data
    );

    if (!validationResult.success || !validationResult.data) {
      requestLog.warn('요청 데이터 검증 실패', {
        error: validationResult.error?.message,
        details: validationResult.error?.details,
      });

      return NextResponse.json<SignupErrorResponse>(
        {
          success: false,
          error: validationResult.error?.message || '검증 실패',
          details: validationResult.error?.details,
        },
        { status: 400 }
      );
    }

    const validatedData = validationResult.data;

    requestLog.info('요청 데이터 검증 완료', {
      actionType: validatedData.actionType,
      hasUtmSource: !!validatedData.utmSource,
      hasUserAgent: !!validatedData.userAgent,
      userId: user.id.slice(0, 8) + '...',
    });

    // 4. User Agent 추출
    const userAgent =
      validatedData.userAgent || request.headers.get('user-agent') || undefined;

    // 5. UTM 파라미터 추출
    const utmParams = {
      utmSource: validatedData.utmSource,
      utmMedium: validatedData.utmMedium,
      utmCampaign: validatedData.utmCampaign,
      utmContent: validatedData.utmContent,
    };

    // 6. 회원가입 활동 로깅 + 통계 업데이트
    const result = await logSignupActivity(
      user.id,
      validatedData.actionType,
      utmParams,
      userAgent
    );

    requestLog.info('회원가입 로깅 성공', {
      logId: result.logId,
      dailyCount: result.dailyCount,
      totalCount: result.totalCount,
      actionType: validatedData.actionType,
      userId: user.id.slice(0, 8) + '...',
    });

    // 7. 성공 응답
    return NextResponse.json<SignupLogResponse>(
      {
        success: true,
        data: {
          logId: result.logId,
          dailyCount: result.dailyCount,
          totalCount: result.totalCount,
        },
      },
      {
        status: 201,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
        },
      }
    );
  } catch (error) {
    requestLog.error('회원가입 로깅 API 처리 실패', error);

    // 상세한 에러 정보는 로그에만 남기고, 클라이언트에는 일반적인 메시지 반환
    return NextResponse.json<SignupErrorResponse>(
      {
        success: false,
        error: '회원가입 로깅 처리 중 오류가 발생했습니다.',
      },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/signup/log
 * CORS preflight 요청 처리
 */
export async function OPTIONS(): Promise<NextResponse> {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400', // 24시간
    },
  });
}
