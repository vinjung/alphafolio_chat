import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// 🛡️ 보안 헤더 추가 함수
function addSecurityHeaders(response: NextResponse): NextResponse {
  // 1. iframe 삽입 완전 차단 (Clickjacking 방지)
  response.headers.set('X-Frame-Options', 'DENY');

  // 2. MIME 타입 추측 차단 (파일 업로드 공격 방지)
  response.headers.set('X-Content-Type-Options', 'nosniff');

  // 3. 리퍼러 정보 최소화 (개인정보 보호)
  response.headers.set('Referrer-Policy', 'origin-when-cross-origin');

  // 4. XSS 방지 (구형 브라우저 지원)
  response.headers.set('X-XSS-Protection', '1; mode=block');

  // 5. HTTPS 강제 (프로덕션에서만)
  if (process.env.NODE_ENV === 'production') {
    response.headers.set(
      'Strict-Transport-Security',
      'max-age=31536000; includeSubDomains'
    );
  }

  // 6. Content Security Policy (떡상 프로젝트에 맞게 조정)
  const csp = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'", // Next.js 개발 모드 지원
    "style-src 'self' 'unsafe-inline'", // Tailwind CSS 지원
    "img-src 'self' data: https: *.kakaocdn.net res.cloudinary.com", // 카카오 프로필, Cloudinary 이미지
    "font-src 'self' data:",
    "connect-src 'self' https:", // FastAPI, 외부 API 허용
    "frame-ancestors 'none'", // iframe 삽입 차단
  ].join('; ');

  response.headers.set('Content-Security-Policy', csp);

  return response;
}

export async function middleware(request: NextRequest): Promise<NextResponse> {
  if (request.method === 'GET') {
    const response = NextResponse.next();
    const token = request.cookies.get('session')?.value ?? null;
    if (token !== null) {
      // Only extend cookie expiration on GET requests since we can be sure
      // a new session wasn't set when handling the request.
      response.cookies.set('session', token, {
        path: '/',
        maxAge: 60 * 60 * 24 * 30,
        sameSite: 'lax',
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
      });
    }

    // 🛡️ GET 요청에 보안 헤더 추가
    return addSecurityHeaders(response);
  }

  const originHeader = request.headers.get('Origin');
  // NOTE: You may need to use `X-Forwarded-Host` instead
  const hostHeader = request.headers.get('Host');
  if (originHeader === null || hostHeader === null) {
    return new NextResponse(null, {
      status: 403,
    });
  }
  let origin: URL;
  try {
    origin = new URL(originHeader);
  } catch {
    return new NextResponse(null, {
      status: 403,
    });
  }
  if (origin.host !== hostHeader) {
    return new NextResponse(null, {
      status: 403,
    });
  }

  // 🛡️ POST/PUT/DELETE 등 다른 요청에도 보안 헤더 추가
  const response = NextResponse.next();
  return addSecurityHeaders(response);
}
