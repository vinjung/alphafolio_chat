import { NextRequest, NextResponse } from 'next/server';
import { getCurrentSession } from '@/lib/server/session';
import { logShareActivity } from '@/lib/server/share-analytics';
import {
  validateData,
  // handleValidation,
  parseRequestBody,
} from '@/lib/validation';
import { shareLogRequestSchema } from '@/lib/validation/share-schemas';
import {
  logger,
  createCorrelationId,
  extractRequestMeta,
} from '@/lib/utils/logger';
import type {
  ShareLogResponse,
  ShareErrorResponse,
} from '@/lib/validation/share-schemas';

/**
 * POST /api/share/log
 * 사용자의 공유 버튼 클릭을 로깅하고 실시간 통계를 업데이트합니다.
 * 로그인하지 않은 사용자도 사용 가능합니다.
 */
export async function POST(
  request: NextRequest
): Promise<NextResponse<ShareLogResponse | ShareErrorResponse>> {
  // 상관관계 ID 및 요청 메타데이터 생성
  const correlationId = createCorrelationId();
  const requestMeta = extractRequestMeta(request);

  const requestLog = logger.child({
    correlationId,
    module: 'share-log-api',
    ...requestMeta,
  });

  requestLog.info('공유 로깅 API 요청 시작');

  try {
    // 1. 요청 본문 파싱
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

    // 2. 요청 데이터 검증
    const validationResult = validateData(
      shareLogRequestSchema,
      bodyResult.data
    );

    if (!validationResult.success || !validationResult.data) {
      requestLog.warn('요청 데이터 검증 실패', {
        error: validationResult.error?.message,
        details: validationResult.error?.details,
      });

      return NextResponse.json<ShareErrorResponse>(
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
      pageType: validatedData.pageType,
      countryCode: validatedData.countryCode,
      hasUserAgent: !!validatedData.userAgent,
    });

    // 3. 사용자 세션 확인 (선택적 - 비로그인도 허용)
    let userId: string | undefined;
    try {
      const { user } = await getCurrentSession();
      userId = user?.id;
      requestLog.debug('사용자 세션 확인', {
        isLoggedIn: !!userId,
        userId: userId?.slice(0, 8) + '...' || 'anonymous',
      });
    } catch (error) {
      // 세션 오류는 로그만 남기고 계속 진행 (비로그인 허용)
      requestLog.debug('세션 확인 실패 - 비로그인으로 처리', { error });
    }

    // 4. User Agent 추출
    const userAgent =
      validatedData.userAgent || request.headers.get('user-agent') || undefined;

    // 5. 공유 활동 로깅 + 통계 업데이트
    const result = await logShareActivity(
      validatedData.pageType,
      validatedData.countryCode,
      userId,
      userAgent
    );

    requestLog.info('공유 로깅 성공', {
      logId: result.logId,
      dailyCount: result.dailyCount,
      totalCount: result.totalCount,
      isLoggedIn: !!userId,
    });

    // 6. 성공 응답
    return NextResponse.json<ShareLogResponse>(
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
    requestLog.error('공유 로깅 API 처리 실패', error);

    // 상세한 에러 정보는 로그에만 남기고, 클라이언트에는 일반적인 메시지 반환
    return NextResponse.json<ShareErrorResponse>(
      {
        success: false,
        error: '공유 로깅 처리 중 오류가 발생했습니다.',
      },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/share/log
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
