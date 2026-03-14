import Link from 'next/link';
import Carousel from './_components/carousel';
import { SocialLoginButton } from './_components/social-login-button';
import { Text } from '@/components/shared/text';
import { getCurrentSession } from '@/lib/server/session';
import { redirect } from 'next/navigation';
import { Metadata } from 'next';

// ✅ 온보딩 페이지 전용 SEO 최적화 메타데이터
export const metadata: Metadata = {
  title: '떡상 - 지금 급등 중인 종목들을 AI가 실시간 분석 🚀',
  description:
    '🔥 지금 떡상 중인 종목들을 놓치지 마세요! AI가 실시간으로 분석한 오늘의 급등주, 내일의 떡상 예측까지. 개미 투자자들이 가장 신뢰하는 떡상 정보 서비스입니다.',

  keywords: [
    // 메인 브랜드 키워드
    '떡상',
    '떡상주',
    '떡상종목',
    '떡상 분석',
    '떡상 예측',
    '떡상 서비스',

    // 급등주 관련 키워드
    '급등주',
    '오늘의 급등주',
    '실시간 급등주',
    '급등 종목',
    '상한가',
    '급등 예측',
    '급등주 추천',
    '급등주 리스트',
    '급등주 정보',

    // AI 관련 키워드
    'AI 떡상',
    'AI 급등주',
    '떡상 AI',
    'AI 주식',
    '인공지능 주식',
    'AI 주식 분석',
    'AI 투자',
    '주식 AI',
    '인공지능 투자',

    // 실시간 관련 키워드
    '실시간 떡상',
    '지금 떡상',
    '현재 떡상',
    '실시간 급등',
    '실시간 주가',
    '실시간 분석',
    '실시간 주식',
    '지금 급등',

    // 타겟 사용자 키워드
    '개미 투자',
    '개미 떡상',
    '개미 급등주',
    '주린이',
    '투자 초보',
    '소액 투자',
    '개인 투자자',
    '개미 추천주',
    '개미 주식',

    // 시장 관련 키워드
    '코스피 급등',
    '코스닥 급등',
    '한국 주식',
    '국내 주식',
    '미국 주식',
    '해외 주식',
    '주식 시장',
    '증권 정보',

    // 수익 관련 키워드
    '주식 수익',
    '투자 수익',
    '급등 수익',
    '떡상 수익',
    '단기 수익',
    '빠른 수익',
    '투자 성공',
    '주식 성공',

    // 정보 관련 키워드
    '주식 정보',
    '투자 정보',
    '급등 정보',
    '떡상 정보',
    '주식 뉴스',
    '급등 뉴스',
    '투자 뉴스',
    '경제 뉴스',

    // 분석 관련 키워드
    '주식 분석',
    '종목 분석',
    '기술적 분석',
    '투자 분석',
    '주가 분석',
    '차트 분석',
    '주식 전망',
    '투자 전망',
  ],

  openGraph: {
    title: '떡상 - 지금 급등 중인 종목들을 AI가 실시간 분석 🚀',
    description:
      '🔥 지금 떡상 중인 종목들을 놓치지 마세요! AI 실시간 분석으로 오늘의 급등주부터 내일의 떡상 예측까지 한 번에',
    type: 'website',
    images: [
      {
        url: '/og-image-3.jpg', // ✅ 실제 존재하는 파일로 수정
        width: 1200,
        height: 630,
        alt: '떡상 - 급등주 AI 실시간 분석 서비스 시작하기',
      },
    ],
    locale: 'ko_KR',
    siteName: '떡상',
  },

  twitter: {
    card: 'summary_large_image',
    title: '떡상 - 지금 급등 중인 종목들 🚀',
    description:
      '🔥 AI가 실시간 분석한 오늘의 떡상주 #떡상 #급등주 #AI주식 #개미투자',
    images: ['/og-image-3.jpg'], // ✅ 실제 존재하는 파일로 수정
  },

  alternates: {
    canonical: process.env.NEXT_PUBLIC_APP_URL || 'https://example.com',
  },

  other: {
    // 온보딩 페이지 특화 메타 태그
    'page-topic': '떡상, 급등주, AI 주식 분석, 투자 시작',
    'page-type': 'landing, onboarding',
    'content-language': 'ko-KR',
    audience: '개미투자자, 주린이, 개인투자자, 투자초보',
    'page-subject': '떡상 서비스 시작 페이지 - 급등주 AI 분석',
    'conversion-goal': 'signup, trial',
    'user-intent': 'information, signup, investment',

    // 구조화된 데이터 힌트
    'schema-type': 'WebApplication, FinancialService',
    'service-category': 'investment, stock-analysis, ai-service',
    'target-market': 'korea, retail-investors',

    // 소셜 미디어 최적화
    'social-share-title': '떡상 - AI가 찾은 오늘의 급등주 🔥',
    'social-share-description':
      '개미들이 가장 많이 보는 떡상 정보를 확인하세요',

    // 검색엔진 최적화 힌트
    'primary-keyword': '떡상',
    'secondary-keywords': '급등주, AI 주식, 개미 투자',
    'content-freshness': 'hourly',
    'update-frequency': 'hourly',

    // ✅ JSON-LD 구조화된 데이터 (프로덕션에서만)
    ...(process.env.NODE_ENV === 'production' && {
      'application/ld+json': JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebApplication',
        name: '떡상',
        alternateName: '떡상 급등주 분석',
        description: '떡상 종목을 AI로 실시간 분석하는 급등주 정보 서비스',
        url: process.env.NEXT_PUBLIC_APP_URL || 'https://example.com',
        applicationCategory: 'FinanceApplication',
        operatingSystem: 'Web, iOS, Android',
        offers: {
          '@type': 'Offer',
          price: '0',
          priceCurrency: 'KRW',
          description: '무료 급등주 정보 제공',
        },
        provider: {
          '@type': 'Organization',
          name: 'Cleverage',
          url: process.env.NEXT_PUBLIC_APP_URL || 'https://example.com',
        },
        audience: {
          '@type': 'Audience',
          audienceType: '개인투자자, 개미투자자, 주식초보자',
        },
        inLanguage: 'ko-KR',
        keywords: '떡상, 급등주, AI 주식 분석, 개미 투자, 실시간 급등',
        mainEntity: {
          '@type': 'Service',
          name: '떡상 급등주 AI 분석',
          description: 'AI 기술을 활용한 실시간 급등주 분석 및 예측 서비스',
          provider: {
            '@type': 'Organization',
            name: 'Cleverage',
          },
        },
      }),
    }),
  },
};

export default async function OnBoardingPage() {
  const { user } = await getCurrentSession();

  if (user) {
    redirect('/today');
  }

  return (
    <div className="bg-neutral-0 flex flex-col flex-1 justify-between items-center p-4">
      {/* ✅ SEO를 위한 숨겨진 제목 추가 */}
      <h1 className="sr-only">
        떡상 - AI가 실시간으로 분석하는 급등주 정보 서비스
      </h1>

      <div className="flex-grow flex flex-col justify-center items-center w-full">
        <Carousel />
      </div>

      <div className="w-full flex flex-col items-center">
        <SocialLoginButton className="mb-2" href="/api/auth/kakao" />
        <Link href="/today" className="w-full p-3 text-center">
          <Text variant="s2" className="text-neutral-700 underline">
            가입은 스킵! 바로 써볼래요
          </Text>
        </Link>
      </div>

      {/* ✅ SEO를 위한 숨겨진 콘텐츠 추가 */}
      <div className="sr-only">
        <h2>떡상 서비스 주요 기능</h2>
        <p>
          떡상은 AI 기술을 활용하여 실시간으로 급등주를 분석하고 예측하는
          서비스입니다. 오늘의 떡상 종목부터 내일의 급등 예측까지, 개미
          투자자들이 필요한 모든 주식 정보를 제공합니다.
        </p>
        <ul>
          <li>실시간 급등주 분석 및 추천</li>
          <li>AI 기반 떡상 종목 예측</li>
          <li>개미 투자자 맞춤형 정보</li>
          <li>한국 및 미국 주식 시장 커버</li>
        </ul>
      </div>
    </div>
  );
}
