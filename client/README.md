# DduckSang Client

DduckSang (떡상) 클라이언트는 AI 기반 한국 주식 분석 플랫폼의 프론트엔드 애플리케이션입니다. Next.js 15 App Router와 React 19를 사용하여 모바일 우선 설계로 개발된 PWA입니다.

## 🚀 빠른 시작

### 개발 서버 실행
```bash
pnpm dev          # 개발 서버 (Turbopack 사용)
pnpm build        # 프로덕션 빌드
pnpm start        # 프로덕션 서버
```

### 코드 품질 도구
```bash
pnpm lint         # ESLint 검사
pnpm lint:fix     # ESLint 자동 수정
pnpm format       # Prettier 포맷팅
pnpm format:check # 포맷팅 검사
```

### 데이터베이스 관리
```bash
pnpm db:pull      # 스키마 동기화 + date 타입 포맷팅 (drizzle-kit pull && ./drizzle/format.sh)
pnpm db:studio    # Drizzle Studio 실행 (읽기 전용 조회)
```

> **참고**: 
> - 테이블 생성/수정은 PgAdmin/Railway Console에서 직접 SQL로 관리
> - `db:pull` 실행 시 자동으로 `format.sh`가 실행되어 date 타입 처리 (`mode: 'string'` → `mode: 'date'`)
> - Drizzle은 스키마 타입 참조 전용

### 스크립트 및 최적화
```bash
pnpm images:optimize  # WebP 이미지 변환 (scripts/image-optimization/convert-to-webp.sh)
pnpm splash:optimize  # 스플래시 로고 최적화 (scripts/image-optimization/optimize-splash-logo.sh)
pnpm optimize:all     # 전체 최적화 (스플래시 + 이미지 + 빌드)
pnpm scripts:setup    # 스크립트 실행 권한 설정 (chmod +x scripts/**/*.sh)
pnpm build:check      # 배포 전 빌드 검증 (scripts/deployment/build-check.sh)
```

## 📁 프로젝트 구조

### Next.js App Router 구조
```
src/app/
├── layout.tsx                    # 🔧 루트 레이아웃
├── manifest.ts                   # 📱 PWA 매니페스트
├── robots.ts                     # 🤖 검색엔진 설정
├── sitemap.ts                    # 🗺️ 사이트맵 생성
│
├── (onboarding)/                 # 📋 온보딩 라우트 그룹
│   ├── page.tsx                 # 랜딩 페이지 (/)
│   └── _components/             # 🔒 온보딩 전용 컴포넌트
│       ├── carousel.tsx
│       └── social-login-button.tsx
│
├── (service)/                    # 🏠 서비스 라우트 그룹 (인증 필요)
│   ├── layout.tsx               # 서비스 레이아웃
│   ├── _components/             # 🔒 서비스 공통 컴포넌트
│   │   ├── bottom-navigation.tsx
│   │   └── navigation-guard.tsx
│   │
│   ├── (home)/                  # 📊 홈 중첩 라우트 그룹
│   │   ├── layout.tsx           # 홈 레이아웃
│   │   ├── error.tsx            # 에러 바운더리
│   │   ├── _actions/            # 🔒 서버 액션
│   │   │   └── onboarding.ts
│   │   ├── _components/         # 🔒 홈 전용 컴포넌트
│   │   │   ├── stock-card.tsx
│   │   │   ├── stock-info-modal.tsx
│   │   │   ├── country-selector.tsx
│   │   │   ├── share-button.tsx
│   │   │   └── auto-refresh.tsx
│   │   ├── today/               # /today 경로
│   │   │   └── page.tsx
│   │   └── future/              # /future 경로
│   │       └── page.tsx
│   │
│   ├── chat/                    # 💬 AI 채팅
│   │   ├── page.tsx            # /chat 메인
│   │   ├── _config/            # 🔒 설정 파일
│   │   │   └── models.ts       # AI 모델 설정
│   │   ├── _components/        # 🔒 채팅 전용 컴포넌트
│   │   │   ├── chat-interface.tsx
│   │   │   ├── message-input.tsx
│   │   │   ├── chat-header.tsx
│   │   │   ├── model-selector.tsx
│   │   │   └── chat-history-modal.tsx
│   │   └── [chatId]/           # 🎯 동적 라우트
│   │       └── page.tsx        # /chat/[chatId]
│   │
│   └── mypage/                  # 👤 사용자 프로필
│       ├── page.tsx
│       └── _components/         # 🔒 프로필 전용 컴포넌트
│           ├── profile-section.tsx
│           ├── menu-section.tsx
│           └── profile-edit-modal.tsx
│
└── api/                         # 🔌 API 라우트
    ├── auth/kakao/
    │   ├── route.ts            # OAuth 시작
    │   └── callback/route.ts   # OAuth 콜백
    ├── chat/
    │   ├── history/route.ts    # 채팅 히스토리
    │   ├── stream/route.ts     # 스트리밍
    │   └── messages/[sessionId]/route.ts  # 🎯 세션 메시지
    ├── health/route.ts         # 헬스체크
    ├── retention/route.ts      # 리텐션 추적
    ├── share/log/route.ts      # 공유 로깅
    └── signup/log/route.ts     # 가입 로깅
```

### 📁 App Router 규칙
- **`()`**: 라우트 그룹 (URL 경로에 영향 없음)
- **`_폴더`**: 라우트가 아닌 코로케이션 폴더 (🔒 표시)
- **`[param]`**: 동적 라우트 (🎯 표시)
- **`page.tsx`**: 페이지 컴포넌트
- **`layout.tsx`**: 레이아웃 컴포넌트 (🔧 표시)
- **`route.ts`**: API 핸들러

### 전체 프로젝트 구조
```
client/
├── src/                           # 소스 코드
│   ├── app/                       # Next.js App Router (상단 참조)
│
├── components/                    # 🌐 전역 재사용 컴포넌트
│   ├── shared/                   # UI 프리미티브
│   │   ├── badge.tsx            # 상태 배지
│   │   ├── button.tsx           # CVA 기반 버튼 시스템
│   │   ├── chip.tsx             # 선택 가능한 칩
│   │   ├── input.tsx            # 폼 입력 컴포넌트
│   │   ├── modal.tsx            # 모달 다이얼로그
│   │   ├── snackbar.tsx         # 토스트 알림
│   │   ├── tooltip.tsx          # 툴팁 컴포넌트
│   │   └── loading-dots.tsx     # 로딩 인디케이터
│   ├── icons/                   # SVG 아이콘 시스템
│   │   ├── copy/               # 복사 아이콘 (filled/outline)
│   │   ├── ipa/                # IPA 아이콘 변형
│   │   ├── profile/            # 프로필 아이콘 변형
│   │   ├── rocket/             # 로켓 아이콘 변형
│   │   ├── icon-wrapper.tsx    # 아이콘 래퍼 컴포넌트
│   │   └── index.ts            # 아이콘 내보내기
│   ├── country-flag-polyfill.tsx # 국가 플래그 폴리필
│   └── splash-screen.tsx        # 앱 시작 스플래시
│
├── hooks/                        # 🎣 커스텀 React 훅 (15개)
│   ├── use-chat-limit.ts        # 채팅 사용량 한도 관리
│   ├── use-chat-messages.ts     # 채팅 메시지 로딩/저장
│   ├── use-chat-model.ts        # AI 모델 선택 관리
│   ├── use-chat-navigation.ts   # 채팅 페이지 네비게이션
│   ├── use-chat-save.ts         # 채팅 세션 저장
│   ├── use-chat-session.ts      # 채팅 세션 상태 관리
│   ├── use-chat-status.ts       # 채팅 UI 상태 관리
│   ├── use-chat-stream.ts       # 실시간 스트리밍 채팅
│   ├── use-navigation-guard.ts  # 페이지 이동 가드
│   ├── use-pull-to-refresh.ts   # 풀투리프레시 제스처
│   ├── use-retention-tracker.ts # 사용자 리텐션 추적
│   ├── use-share.ts             # 콘텐츠 공유 기능
│   ├── use-snackbar.ts          # 토스트 알림 관리
│   ├── use-tab-navigation.ts    # 탭 네비게이션 상태
│   └── use-tooltip.ts           # 툴팁 상태 관리
│
├── lib/                          # 🔧 유틸리티 및 서버 함수
│   ├── server/                  # 서버 사이드 유틸리티
│   │   ├── actions/             # 서버 액션
│   │   │   ├── auth.ts         # 인증 액션
│   │   │   ├── user.ts         # 사용자 액션
│   │   │   └── index.ts        # 액션 내보내기
│   │   ├── api-config.ts       # API 및 Railway 설정
│   │   ├── chat-history.ts     # 채팅 히스토리 관리
│   │   ├── chat-limit.ts       # 채팅 한도 시스템
│   │   ├── db.ts               # Drizzle 데이터베이스 설정
│   │   ├── models.ts           # 데이터베이스 모델
│   │   ├── oauth.ts            # Kakao OAuth 설정
│   │   ├── rate-limit.ts       # API 레이트 리미팅
│   │   ├── redis.ts            # Redis 캐시 설정
│   │   ├── request.ts          # 요청 유틸리티
│   │   ├── retention-tracker.ts # 리텐션 분석
│   │   ├── session.ts          # 세션 관리
│   │   ├── share-analytics.ts  # 공유 분석
│   │   ├── signup-analytics.ts # 가입 분석
│   │   ├── signup-tracker.ts   # 가입 추적
│   │   ├── stock-data.ts       # 주식 데이터 처리
│   │   ├── user-limit-management.ts # 사용자 한도 관리
│   │   └── user.ts             # 사용자 관리
│   ├── utils/                  # 클라이언트 유틸리티
│   │   ├── cloudinary-upload.ts # Cloudinary 이미지 업로드
│   │   ├── cva.config.ts       # CVA 설정
│   │   ├── date-formatter.ts   # 날짜 포맷팅
│   │   ├── logger.ts           # 구조화된 로깅
│   │   └── stock-formatters.ts # 주식 데이터 포맷팅
│   └── validation/             # Zod 데이터 검증
│       ├── chat-schemas.ts     # 채팅 스키마
│       ├── common-schemas.ts   # 공통 스키마
│       ├── share-schemas.ts    # 공유 스키마
│       ├── signup-schemas.ts   # 가입 스키마
│       └── index.ts            # 스키마 내보내기
│
├── stores/                       # 🗂️ Zustand 상태 관리
│   ├── app-store.ts            # 글로벌 앱 상태
│   ├── chat-limit-store.ts     # 채팅 한도 관리
│   ├── chat-session-store.ts   # 채팅 세션 상태
│   ├── streaming-store.ts      # 실시간 스트리밍 상태
│   └── index.ts                # 스토어 내보내기
│
├── styles/                       # 🎨 스타일링
│   ├── globals.css             # 글로벌 스타일
│   ├── theme.css               # 테마 변수
│   └── fonts.ts                # 폰트 설정
│
│   └── types/                        # 📝 TypeScript 정의
│       ├── chat.d.ts               # 채팅 관련 타입
│       └── svg.d.ts                # SVG 모듈 선언
│
├── scripts/                        # 🛠️ 개발 및 배포 스크립트
│   ├── README.md                   # 스크립트 사용법
│   ├── deployment/                 # 배포 관련 스크립트
│   └── image-optimization/         # 이미지 최적화 도구
│       ├── convert-to-webp.sh     # WebP 변환 스크립트
│       └── optimize-splash-logo.sh # 스플래시 로고 최적화
│
├── drizzle/                        # 🗄️ 데이터베이스 스키마 (Drizzle 생성)
│   ├── schema.ts                   # TypeScript 스키마 정의
│   ├── relations.ts                # 테이블 관계 정의
│   ├── format.sh                   # date 타입 후처리 스크립트
│   ├── meta/                       # Drizzle 메타데이터
│   └── *.sql                       # SQL 마이그레이션 파일
│
├── package.json                    # 의존성 및 스크립트 정의
├── next.config.ts                  # Next.js 설정
├── tailwind.config.ts              # Tailwind CSS 설정
├── drizzle.config.ts               # Drizzle 설정
└── tsconfig.json                   # TypeScript 설정
```

### 🏗️ 네이밍 컨벤션
- **파일**: `kebab-case.tsx` (예: `social-login-button.tsx`)
- **컴포넌트**: `PascalCase` (예: `SocialLoginButton`)  
- **폴더**: `kebab-case` 또는 `_underscore-prefix`
- **훅**: `use-kebab-case.ts` (예: `use-chat-stream.ts`)
- **타입**: `PascalCase` 인터페이스, `camelCase` 속성

## 🏗️ 아키텍처 개요

### 상태 관리 (Zustand)
- **StreamingStore**: 실시간 AI 스트리밍 상태
- **AppStore**: 글로벌 앱 상태 (모델 선택, 프리셋 메시지)
- **ChatSessionStore**: 채팅 세션 및 메시지 관리  
- **ChatLimitStore**: 사용자 일일 채팅 한도 (기본 5회)

### AI 채팅 시스템
- **주식 AI (SKYROCKET)**: 데이터 기반 주식 분석
- **뇌절 AI (BRAIN_CRASH)**: 창의적 시장 분석
- **SSE 스트리밍**: 실시간 응답 스트리밍
- **중단 가능**: 사용자가 응답 중도 중단 가능
- **자동 저장**: 채팅 내역 자동 저장 및 세션 관리
- **에러 복구**: 네트워크 오류 시 재시도 메커니즘

### 데이터베이스 스키마 (PostgreSQL + Drizzle)
```
# 사용자 관리
├── users                 # OAuth 프로필 (soft delete 지원)
├── sessions              # 보안 세션 (30일 만료)
└── user_limits           # 일일 채팅 한도

# 채팅 시스템
├── chat_sessions         # 채팅 대화 (모델 추적)
└── chat_messages         # 개별 채팅 메시지

# 주식 데이터
├── today_kr/today_us     # 현재 트렌딩 주식
└── future_kr/future_us   # 미래 예측 및 인사이트

# 분석 데이터
├── share_activity_logs   # 공유 추적 (페이지/국가별)
├── signup_activity_logs  # UTM 추적 및 사용자 획득
├── daily_user_retention  # 사용자 활동 추적
└── user_statistics       # 일일/총 가입 수 통계
```

## 🔗 주요 API 엔드포인트

### 인증 관련
- `GET /api/auth/kakao` - 카카오 OAuth 시작
- `HEAD /api/auth/kakao` - OAuth 환경변수 검증
- `GET /api/auth/kakao/callback` - OAuth 콜백 처리

### 채팅 관련
- `POST /api/chat/stream` - AI 스트리밍 채팅
- `POST /api/chat/save` - 채팅 내역 저장
- `GET /api/chat/messages/[sessionId]` - 세션 메시지 조회
- `GET /api/chat/history` - 채팅 세션 목록 조회
- `DELETE /api/chat/history` - 채팅 세션 삭제
- `PATCH /api/chat/history` - 채팅 세션 제목 수정
- `GET /api/chat/limit` - 사용자 채팅 한도 조회
- `POST /api/chat/model-sessions` - 모델별 최근 세션 조회

### 분석 및 추적
- `POST /api/share/log` - 공유 활동 로깅
- `POST /api/signup/log` - 가입 활동 추적
- `POST /api/retention` - 사용자 리텐션 추적
- `GET /api/health` - 서비스 상태 확인

## 🌐 서버 사이드 렌더링

### 페이지별 렌더링 전략
- **랜딩 페이지 (`/`)**: Static Generation + 클라이언트 OAuth
- **주식 페이지 (`/today`, `/future`)**: ISR (5분 캐싱) + pull-to-refresh
- **채팅 페이지 (`/chat/[chatId]`)**: SSR (세션 기반 접근 제어)
- **마이페이지 (`/mypage`)**: SSR (사용자 정보 필요)
- **API 라우트**: 동적 처리 + 보안 미들웨어

### 성능 최적화
- **Turbopack**: 빠른 개발 빌드
- **이미지 최적화**: WebP 변환 + 다중 밀도 (@2x, @3x)
- **코드 분할**: 동적 import + 지연 로딩
- **폰트 최적화**: Pretendard, Recipe Korea + system font fallback

## 📱 PWA 및 모바일 기능

### PWA 지원
- ✅ **앱 매니페스트**: 한국어 브랜딩, 독립형 앱 모드
- ✅ **앱 아이콘**: Android Chrome 최적화 (192x192, 512x512, maskable)
- ✅ **앱 단축키**: "오늘의 떡상" 빠른 접근
- ✅ **브랜드 테마**: 떡상 빨강 (#FF2233)
- ❌ **서비스 워커**: 미구현 (오프라인 지원 없음)
- ❌ **푸시 알림**: 미구현
- ❌ **설치 프롬프트**: 미구현

### 모바일 우선 설계
- **터치 최적화**: Pull-to-refresh, 스와이프 네비게이션
- **세이프 에어리어**: iOS 지원
- **반응형 디자인**: Tailwind CSS 모바일 퍼스트
- **하단 네비게이션**: 활성 상태 표시
- **스플래시 스크린**: 세션 기반 표시

## 🔐 인증 및 보안

### OAuth 2.0 (Kakao)
- **Arctic 3.7.0**: OAuth2 클라이언트 라이브러리
- **Oslo Crypto**: 안전한 세션 토큰 생성
- **30일 세션**: 자동 만료 및 갱신
- **Soft Delete**: 사용자 데이터 보존

### 보안 헤더
- **CSP**: Content Security Policy
- **CSRF 보호**: 동일 출처 정책
- **보안 쿠키**: HttpOnly, Secure, SameSite

## 🔧 기술 스택

### 핵심 기술
- **Next.js 15.3.2** (App Router, Turbopack)
- **React 19.1.0** + **React DOM 19.1.0**
- **TypeScript 5.8.3**
- **Tailwind CSS 4.1.11** + **PostCSS**
- **Drizzle ORM 0.43.1** + **PostgreSQL** (타입 참조 전용)

### 상태 관리 & 데이터
- **Zustand 5.0.6** (DevTools 포함)
- **React Markdown 10.1.0** (채팅 포맷팅)
- **Country Flag Emoji Polyfill** (국가 플래그 지원)

### UI/UX 라이브러리
- **CVA 1.0.0-beta.4** (컴포넌트 변형)
- **Motion 12.19.2** (애니메이션)
- **SVGR** (SVG 컴포넌트 변환)

### 개발 도구
- **ESLint** + **Prettier** (코드 품질)
- **@types/node** (TypeScript 지원)
- **Drizzle Studio** (데이터베이스 관리)

### 배포 및 인프라
- **Railway** (클라우드 배포 플랫폼)
  - PostgreSQL 데이터베이스 호스팅
  - 자동 배포 및 스케일링
  - 환경 변수 관리
- **PgAdmin/Railway Console** (데이터베이스 관리)
- **Cloudinary** (이미지 최적화 및 CDN)
- **UTM 추적** (마케팅 분석)

## 📊 분석 및 추적

### 사용자 분석
- **가입 추적**: UTM 파라미터 기반 사용자 획득 분석
- **리텐션 추적**: 일일 사용자 활동 분석
- **공유 분석**: 페이지별/국가별 공유 활동 추적
- **사용 패턴**: AI 모델별 사용 통계

### 데이터 대시보드
- Drizzle Studio를 통한 실시간 데이터 모니터링
- 사용자 통계 및 트렌드 분석
- 채팅 한도 및 사용량 추적

## 🗄️ 데이터베이스 워크플로우

### 스키마 관리 원칙
- **SQL 우선**: 모든 테이블 생성/수정은 SQL로 직접 수행
- **Drizzle 역할**: TypeScript 타입 안전성만 제공
- **워크플로우**: SQL 변경 → `pnpm db:pull` → 타입 동기화

### 스키마 변경 프로세스
1. **PgAdmin/Railway Console**에서 SQL로 테이블 변경
2. `pnpm db:pull` 실행 → 자동으로 다음 작업 수행:
   - `drizzle-kit pull`: 스키마를 TypeScript로 동기화
   - `./drizzle/format.sh`: date 컬럼의 `mode: 'string'`을 `mode: 'date'`로 자동 변경
3. 애플리케이션 코드에서 새 타입 사용
4. 테스트 후 배포

> **중요**: 
> - `db:push`, `db:generate` 명령어는 사용하지 않음
> - PostgreSQL date 타입은 자동으로 올바른 TypeScript 타입으로 변환됨
> - 스키마는 항상 SQL 우선으로 관리

## 📚 추가 리소스

- [CLAUDE.md](../CLAUDE.md) - 전체 모노레포 가이드
- [Next.js 15 문서](https://nextjs.org/docs)
- [Drizzle ORM 문서](https://orm.drizzle.team/)
- [Arctic OAuth 문서](https://arctic.js.org/)
- [Tailwind CSS 문서](https://tailwindcss.com/docs)

## 🤝 기여하기

1. 프로젝트를 포크합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/new-feature`)
3. 변경 사항을 커밋합니다 (`git commit -m 'Add new feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/new-feature`)
5. Pull Request를 생성합니다

## 📋 개발 환경 요구사항

- **Node.js**: 18+ (권장: 20.x)
- **pnpm**: 8+
- **PostgreSQL**: 14+ 
- **환경 변수**: OAuth, 데이터베이스, Cloudinary 설정 필요

---

**한국 핀테크 × AI 플랫폼** | Built with ❤️ for 떡상