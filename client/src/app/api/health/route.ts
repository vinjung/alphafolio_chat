import { NextResponse } from 'next/server';

/**
 * GET /api/health
 * Railway 헬스체크용 간단한 엔드포인트
 *
 * Railway는 이 엔드포인트가 200을 반환하면 서비스가 정상이라고 판단합니다.
 */
export async function GET() {
  try {
    // 간단한 서버 상태 체크
    const timestamp = new Date().toISOString();

    return NextResponse.json(
      {
        status: 'healthy',
        timestamp,
        service: 'stock-client',
        environment: process.env.NODE_ENV || 'development',
      },
      {
        status: 200,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
        },
      }
    );
  } catch (error) {
    // 예상치 못한 오류 시 500 반환
    console.error('Health check failed:', error);

    return NextResponse.json(
      {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: 'Internal server error',
      },
      {
        status: 500,
      }
    );
  }
}
