import { NextRequest, NextResponse } from 'next/server';
import { getCurrentSession } from '@/lib/server/session';
import { checkDailyLimit } from '@/lib/server/chat-limit';
import { logger } from '@/lib/utils/logger';

const log = logger.child({ module: 'chat-limit-api' });

/**
 * GET /api/chat/limit
 * Retrieves user's daily chat limit information
 *
 * @param {NextRequest} _request - The incoming request object (unused)
 * @returns {Promise<NextResponse>} JSON response with chat limit data
 *
 * @example
 * GET /api/chat/limit
 * Response: {
 *   "success": true,
 *   "data": {
 *     "used": 5,
 *     "limit": 50,
 *     "remaining": 45,
 *     "canSend": true,
 *     "resetTime": "내일 오전 00:00"
 *   }
 * }
 * 
 * @throws {401} Unauthorized - User not authenticated
 * @throws {500} Internal Server Error - Server error
 */
export async function GET(_request: NextRequest) {
  try {
    // 1. 사용자 인증 확인
    const { user } = await getCurrentSession();

    if (!user) {
      log.warn('인증되지 않은 사용자의 한도 조회 시도');
      return NextResponse.json(
        { error: '인증이 필요합니다.' },
        { status: 401 }
      );
    }

    // 2. 일일 채팅 한도 확인
    const limitInfo = await checkDailyLimit(user.id);

    log.info('채팅 한도 조회 완료', {
      userId: user.id,
      used: limitInfo.used,
      limit: limitInfo.limit,
      remaining: limitInfo.remaining,
    });

    return NextResponse.json({
      success: true,
      data: {
        used: limitInfo.used,
        limit: limitInfo.limit,
        remaining: limitInfo.remaining,
        canSend: limitInfo.canSend,
        resetTime: '내일 오전 00:00', // 고정 메시지
      },
    });
  } catch (error) {
    log.error('채팅 한도 조회 실패', error);

    return NextResponse.json(
      { error: '서버 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}
