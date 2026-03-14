import { type NextRequest, NextResponse } from 'next/server';
import { kakao, KakaoIdTokenClaims } from '@/lib/server/oauth';
import { OAuth2RequestError, ArcticFetchError, decodeIdToken } from 'arctic';
import {
  createUser,
  getUserFromOauthId,
  getDeletedUserFromOauthId, // ✅ 추가
} from '@/lib/server/user';
import { createSession, generateSessionToken } from '@/lib/server/session';
import { createDefaultUserLimit } from '@/lib/server/chat-limit';
import { logSignupActivity } from '@/lib/server/signup-analytics';
import {
  logger,
  createCorrelationId,
  extractRequestMeta,
  createTimer,
} from '@/lib/utils/logger';
import { db } from '@/lib/server/db'; // ✅ 추가
import { users } from '@schema'; // ✅ 추가
import { eq } from 'drizzle-orm'; // ✅ 추가

export async function GET(request: NextRequest): Promise<Response> {
  // 🔗 상관관계 ID 생성 및 타이머 시작
  const correlationId = createCorrelationId();
  const timer = createTimer();

  // 📊 Request 메타데이터 추출
  const requestMeta = extractRequestMeta(request);

  // 🎯 로거 인스턴스 생성 (컨텍스트 포함)
  const log = logger.child({
    correlationId,
    flow: 'kakao_oauth_callback',
    ...requestMeta,
  });

  log.info('카카오 OAuth 콜백 요청 시작');

  // 📝 URL 파라미터 추출
  const url = request.nextUrl;
  const code = url.searchParams.get('code');
  const returnedState = url.searchParams.get('state');
  const storedState = request.cookies.get('kakao_oauth_state')?.value ?? null;
  const storedNonce = request.cookies.get('kakao_oauth_nonce')?.value ?? null;

  log.debug('OAuth 파라미터 추출 완료', {
    hasCode: !!code,
    hasReturnedState: !!returnedState,
    hasStoredState: !!storedState,
    hasStoredNonce: !!storedNonce,
  });

  // ❌ 유효성 검사
  if (!code) {
    log.warn('OAuth code 누락');
    return new Response('Missing code', { status: 400 });
  }

  if (!returnedState || returnedState !== storedState) {
    log.warn('OAuth state 불일치', {
      returnedState,
      storedState,
      matched: returnedState === storedState,
    });
    return new Response('Invalid state', { status: 400 });
  }

  log.info('OAuth 파라미터 검증 완료');

  try {
    // 🎫 카카오 토큰 교환
    log.info('카카오 토큰 교환 시작');
    const tokenTimer = createTimer();

    const tokens = await kakao.validateAuthorizationCode(code);

    log.info('카카오 토큰 교환 완료', {
      duration: tokenTimer.duration(),
    });

    // 🔐 ID 토큰 검증
    log.info('ID 토큰 검증 시작');
    const idToken = tokens.idToken();
    const claims = decodeIdToken(idToken) as KakaoIdTokenClaims;
    const now = Math.floor(Date.now() / 1000);

    log.debug('ID 토큰 클레임 추출 완료', {
      iss: claims.iss,
      aud: claims.aud?.substring(0, 8) + '...',
      sub: claims.sub?.substring(0, 8) + '...',
      exp: claims.exp,
      currentTime: now,
      timeToExpiry: claims.exp - now,
    });

    // ID 토큰 검증 로직들
    if (claims.nonce !== storedNonce) {
      log.error('ID 토큰 nonce 불일치', {
        claimsNonce: claims.nonce?.substring(0, 8) + '...',
        storedNonce: storedNonce?.substring(0, 8) + '...',
      });
      return new Response('Nonce mismatch in ID token', { status: 400 });
    }

    if (claims.iss !== 'https://kauth.kakao.com') {
      log.error('ID 토큰 발급자 불일치', {
        expected: 'https://kauth.kakao.com',
        actual: claims.iss,
      });
      return new Response('Invalid issuer', { status: 400 });
    }

    if (claims.aud !== process.env.KAKAO_CLIENT_ID) {
      log.error('ID 토큰 audience 불일치');
      return new Response('Invalid audience', { status: 400 });
    }

    if (claims.exp < now) {
      log.error('ID 토큰 만료', {
        expiryTime: claims.exp,
        currentTime: now,
        expiredBy: now - claims.exp,
      });
      return new Response('ID token expired', { status: 401 });
    }

    log.info('ID 토큰 검증 완료');

    // 👤 카카오 사용자 정보 조회
    log.info('카카오 사용자 정보 조회 시작');
    const userApiTimer = createTimer();

    const accessToken = tokens.accessToken();
    const userResponse = await fetch('https://kapi.kakao.com/v2/user/me', {
      headers: { Authorization: `Bearer ${accessToken}` },
      signal: AbortSignal.timeout(10000),
    });

    if (!userResponse.ok) {
      log.error('카카오 사용자 정보 조회 실패', {
        status: userResponse.status,
        statusText: userResponse.statusText,
        duration: userApiTimer.duration(),
      });
      return Response.json(
        {
          error: 'Failed to fetch user data from Kakao API',
          status: userResponse.status,
        },
        { status: 500 }
      );
    }

    const data = await userResponse.json();
    const kakaoAccount = data.kakao_account;

    log.info('카카오 사용자 정보 조회 완료', {
      kakaoUserId: data.id?.toString().substring(0, 8) + '...',
      hasEmail: !!kakaoAccount.email,
      hasNickname: !!kakaoAccount.profile?.nickname,
      hasPhoneNumber: !!kakaoAccount.phone_number,
      hasProfileImage: !!kakaoAccount.profile.profile_image_url,
      hasThumbnailImage: !!kakaoAccount.profile.thumbnail_image_url,
      duration: userApiTimer.duration(),
    });

    // 🔍 기존 사용자 조회 + 계정 복원 로직
    log.info('기존 사용자 조회 시작');
    const dbTimer = createTimer();

    let user = await getUserFromOauthId(data.id.toString(), 'kakao');
    let isNewUser = false;
    let isRestoredUser = false;

    // 🔄 탈퇴한 사용자 복원 로직
    if (!user) {
      log.info('탈퇴한 사용자 확인 시작');
      const deletedUser = await getDeletedUserFromOauthId(
        data.id.toString(),
        'kakao'
      );

      if (deletedUser) {
        log.info('탈퇴한 사용자 계정 복원 시작', {
          deletedUserId: deletedUser.id.substring(0, 8) + '...',
          email: deletedUser.email,
          deletedAt: deletedUser.deletedAt,
        });

        // ✅ 계정 복원 (deleted_at을 NULL로 설정)
        const [restoredUser] = await db
          .update(users)
          .set({
            deletedAt: null,
            updatedAt: new Date(),
            lastLoginAt: new Date(), // 로그인 시간 업데이트
          })
          .where(eq(users.id, deletedUser.id))
          .returning();

        user = restoredUser;
        isRestoredUser = true;

        log.info('탈퇴한 사용자 계정 복원 완료', {
          userId: user.id.substring(0, 8) + '...',
          email: user.email,
          nickname: user.nickname,
        });
      } else {
        isNewUser = true;
      }
    }

    log.info('기존 사용자 조회 완료', {
      isNewUser,
      isRestoredUser,
      duration: dbTimer.duration(),
    });

    // 👥 신규 사용자 생성
    if (isNewUser) {
      log.info('신규 사용자 생성 시작');
      const createUserTimer = createTimer();

      const userData = {
        oauthProvider: 'kakao' as const,
        oauthId: data.id.toString(),
        phoneNumber: kakaoAccount.phone_number ?? '010-1234-5678',
        ageRange: kakaoAccount.age_range,
        email: kakaoAccount.email,
        gender: kakaoAccount.gender ?? '미동의',
        profileImageUrl: kakaoAccount.profile.profile_image_url,
        thumbnailImageUrl: kakaoAccount.profile.thumbnail_image_url,
        nickname: kakaoAccount.profile?.nickname ?? 'no name',
      };

      try {
        user = await createUser(userData);
        await createDefaultUserLimit(user.id, 'custom');

        log.info('신규 사용자 등록 완료', {
          userId: user.id.substring(0, 8) + '...',
          email: user.email,
          nickname: user.nickname,
          limit: 5,
          duration: createUserTimer.duration(),
        });
      } catch (error) {
        log.error('신규 사용자 등록 실패', error, {
          email: userData.email,
          duration: createUserTimer.duration(),
        });

        return Response.json(
          {
            error: '사용자 등록에 실패했습니다.',
            message: '잠시 후 다시 시도해주세요.',
            correlationId,
          },
          { status: 500 }
        );
      }
    } else if (!isRestoredUser) {
      // 기존 사용자 로그인 (복원 사용자가 아닌 경우)
      log.info('기존 사용자 로그인 시간 업데이트');
      await db
        .update(users)
        .set({ lastLoginAt: new Date() })
        .where(eq(users.id, user!.id));
    }

    // 🎟️ 세션 생성
    log.info('사용자 세션 생성 시작');
    const sessionTimer = createTimer();

    const sessionToken = generateSessionToken();
    const session = await createSession(sessionToken, user!.id);

    log.info('사용자 세션 생성 완료', {
      userId: user!.id.substring(0, 8) + '...',
      sessionId: session.id.substring(0, 8) + '...',
      expiresAt: session.expiresAt.toISOString(),
      duration: sessionTimer.duration(),
    });

    // 🆕 DB 트래킹 로직 수정 (복원 사용자 구분)
    const actionType = isNewUser
      ? 'signup'
      : isRestoredUser
        ? 'restore'
        : 'login';

    try {
      await logSignupActivity(
        user!.id,
        actionType,
        {
          utmSource: 'kakao',
          utmMedium: 'login',
          utmCampaign: 'signup',
          utmContent: actionType,
        },
        request.headers.get('user-agent') || undefined
      );

      log.info('사용자 활동 트래킹 완료', {
        actionType,
        isNewUser,
        isRestoredUser,
      });
    } catch (trackingError) {
      log.warn('사용자 활동 트래킹 실패 (로그인은 정상 진행)', {
        error: trackingError,
        actionType,
      });
    }

    // 🆕 UTM 파라미터를 포함한 리다이렉트 URL 생성 (GA용)
    const baseRedirectUrl = process.env.NEXT_PUBLIC_APP_URL + '/today';
    const redirectUrl = new URL(baseRedirectUrl);

    // UTM 파라미터 추가 (GA 트래킹용)
    redirectUrl.searchParams.set('utm_source', 'kakao');
    redirectUrl.searchParams.set('utm_medium', 'login');
    redirectUrl.searchParams.set('utm_campaign', 'signup');
    redirectUrl.searchParams.set('utm_content', actionType);

    log.info('UTM 파라미터 포함 리다이렉트 URL 생성', {
      isNewUser,
      isRestoredUser,
      actionType,
      redirectTo: redirectUrl.toString(),
    });

    // 🔒 쿠키 설정 및 리다이렉트
    const response = NextResponse.redirect(redirectUrl, 302);

    response.cookies.set({
      name: 'session',
      value: sessionToken,
      httpOnly: true,
      path: '/',
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      expires: session.expiresAt,
    });

    response.cookies.delete('hasSeenGuestOnboarding');
    log.debug('비회원 온보딩 쿠키 삭제 완료');

    log.info('카카오 OAuth 콜백 처리 완료', {
      userId: user!.id.substring(0, 8) + '...',
      isNewUser,
      isRestoredUser,
      redirectTo: redirectUrl.pathname + redirectUrl.search,
      totalDuration: timer.duration(),
    });

    response.cookies.delete('kakao_oauth_state');
    response.cookies.delete('kakao_oauth_nonce');
    log.debug('OAuth 검증용 쿠키 삭제 완료');

    return response;
  } catch (e) {
    log.error('카카오 로그인 처리 중 오류 발생', e, {
      totalDuration: timer.duration(),
    });

    // 🚨 에러 타입별 세부 로깅
    if (e instanceof OAuth2RequestError) {
      log.error('OAuth2 요청 오류', e, {
        errorCode: e.code,
        errorMessage: e.message,
      });

      return Response.json(
        { error: 'OAuth 요청 오류', code: e.code, message: e.message },
        { status: 400 }
      );
    }

    if (e instanceof ArcticFetchError) {
      log.error('Arctic API 호출 실패', e, {
        errorMessage: e.message,
        cause: e.cause,
      });

      return Response.json(
        { error: 'API 호출 실패', message: e.message, cause: e.cause },
        { status: 500 }
      );
    }

    // 🔥 일반적인 예상치 못한 오류
    log.error('예상치 못한 오류', e);

    return Response.json(
      {
        error: '알 수 없는 오류',
        message: e instanceof Error ? e.message : 'Unknown error',
        correlationId, // 디버깅을 위해 상관관계 ID 포함
      },
      { status: 500 }
    );
  }
}
