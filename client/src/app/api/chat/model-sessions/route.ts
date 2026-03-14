import { NextRequest, NextResponse } from 'next/server';
import { getCurrentSession } from '@/lib/server/session';
import { getLatestSessionByModel } from '@/lib/server/chat-history';
import { logger } from '@/lib/utils/logger';
import { globalPOSTRateLimit } from '@/lib/server/request';

const log = logger.child({ module: 'model-sessions-api' });

/**
 * POST /api/chat/model-sessions
 * 특정 모델의 최근 채팅 세션 조회
 *
 * Body:
 * - modelId: string (모델 ID)
 */
export async function POST(request: NextRequest) {
  try {
    // 🚦 Rate Limiting 체크
    if (!(await globalPOSTRateLimit())) {
      log.warn('모델별 세션 조회 Rate Limit 초과');
      return NextResponse.json(
        { error: 'Too many requests. Please try again later.' },
        {
          status: 429,
          headers: {
            'Retry-After': '60',
            'X-RateLimit-Reset': String(Math.floor(Date.now() / 1000) + 60),
          },
        }
      );
    }

    // 1. 사용자 인증 확인
    const { user } = await getCurrentSession();

    if (!user) {
      log.warn('인증되지 않은 사용자의 모델별 세션 조회 시도');
      return NextResponse.json(
        { error: '인증이 필요합니다.' },
        { status: 401 }
      );
    }

    // 2. 요청 본문 파싱
    let body;
    try {
      body = await request.json();
    } catch {
      return NextResponse.json(
        { error: '잘못된 요청 형식입니다.' },
        { status: 400 }
      );
    }

    const { modelId } = body;

    // 3. 요청 데이터 검증
    if (!modelId || typeof modelId !== 'string') {
      return NextResponse.json(
        { error: '모델 ID가 필요합니다.' },
        { status: 400 }
      );
    }

    // 4. 모델 ID 유효성 검증
    const validModelIds = ['stock-ai', 'brain-ai'];
    if (!validModelIds.includes(modelId)) {
      log.warn('잘못된 모델 ID', { modelId, validIds: validModelIds });
      return NextResponse.json(
        { error: '유효하지 않은 모델 ID입니다.' },
        { status: 400 }
      );
    }

    log.info('모델별 최근 세션 조회 시작', {
      userId: user.id,
      modelId,
    });

    // 5. 해당 모델의 최근 세션 조회
    const latestSession = await getLatestSessionByModel(user.id, modelId);

    if (latestSession) {
      log.info('모델별 최근 세션 조회 완료 - 세션 발견', {
        userId: user.id,
        modelId,
        sessionId: latestSession.id,
        sessionTitle: latestSession.title.slice(0, 30),
        updatedAt: latestSession.updatedAt,
      });

      return NextResponse.json({
        success: true,
        latestSession: {
          id: latestSession.id,
          title: latestSession.title,
          updatedAt: latestSession.updatedAt,
          messageCount: latestSession.messageCount,
        },
        message: `${modelId} 모델의 최근 세션을 찾았습니다.`,
      });
    } else {
      log.info('모델별 최근 세션 조회 완료 - 세션 없음', {
        userId: user.id,
        modelId,
      });

      return NextResponse.json({
        success: true,
        latestSession: null,
        message: `${modelId} 모델의 세션이 없습니다.`,
      });
    }
  } catch (error) {
    log.error('모델별 최근 세션 조회 실패', error);

    return NextResponse.json(
      { error: '서버 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}
