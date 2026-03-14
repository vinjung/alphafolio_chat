import { Kakao } from 'arctic';

/**
 * Arctic Kakao OAuth2 클라이언트 인스턴스
 *
 * 이 클라이언트를 통해 카카오 로그인(Authorization Code Grant),
 * 토큰 교환, 토큰 갱신 등을 처리합니다.
 *
 * @constant
 * @type {Kakao}
 *
 * @see {@link https://arcticjs.dev/providers/kakao|Arctic Kakao Provider 문서}
 * @see {@link https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api|Kakao Login REST API}
 */
export const kakao: Kakao = new Kakao(
  process.env.KAKAO_CLIENT_ID ?? '', // REST API 키 (클라이언트 아이디)
  process.env.KAKAO_CLIENT_SECRET ?? '', // 앱 시크릿 (클라이언트 시크릿)
  process.env.KAKAO_LOGIN_REDIRECT_URI ?? '' // OAuth2 콜백 URI
);

/**
 * 카카오 OIDC ID 토큰 페이로드의 타입 정의.
 *
 * @see {@link https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api#oidc-get-id-token-info|Kakao Login OpenId Connect}
 */
export interface KakaoIdTokenClaims {
  /** 발급자(issuer). 항상 `https://kauth.kakao.com` */
  iss: string;

  /** Audience. 앱 키 */
  aud: string;

  /** Subject. 사용자 식별자 */
  sub: string;

  /** 발급 시각(Unix timestamp) */
  iat: number;

  /** 만료 시각(Unix timestamp) */
  exp: number;

  /** 요청 시 보낸 nonce 값(리플레이 방지) */
  nonce: string;

  /** 실제 인증 시각(Unix timestamp) */
  auth_time: number;
}
