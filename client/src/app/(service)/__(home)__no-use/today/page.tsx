import { ScrollContainer } from '../_components/scroll-container';
import { CountrySelector } from '../_components/country-selector';
import { StocksList } from '../_components/stocks-list';
import { ShareButton } from '../_components/share-button';
import { getCurrentSession } from '@/lib/server/session';
import { Text } from '@/components/shared/text';
import { getCachedTodayStocksWithCTE } from '@/lib/server/stock-data';
import { DataTimestamp } from '../_components/data-timestamp';
import { User } from '@/lib/server/models';
import { Metadata } from 'next';

// ✅ Today 페이지 전용 SEO 최적화 메타데이터
export const metadata: Metadata = {
  title: '오늘의 떡상 - 실시간 급등주 AI 분석 | 떡상',
  description:
    '🔥 지금 이 시간 가장 뜨거운 급등주들! AI가 실시간으로 분석한 오늘의 떡상 종목을 확인하세요. 한국과 미국 시장의 급등주 정보를 매시간 업데이트.',

  keywords: [
    // 메인 타겟 키워드
    '오늘의 떡상',
    '오늘 떡상',
    '떡상 오늘',
    '떡상 종목 오늘',
    '오늘의 급등주',
    '오늘 급등주',
    '급등주 오늘',
    '급등 종목 오늘',

    // 실시간 관련 키워드
    '실시간 떡상',
    '실시간 급등주',
    '지금 떡상',
    '현재 떡상',
    '실시간 급등',
    '지금 급등',
    '현재 급등주',
    '실시간 주가',

    // AI 분석 관련
    'AI 떡상 분석',
    'AI 급등주',
    '떡상 AI',
    'AI 주식 분석',
    '인공지능 떡상',
    '인공지능 급등주',
    'AI 투자 분석',

    // 시장별 키워드
    '한국 떡상',
    '국내 떡상',
    '코스피 급등',
    '코스닥 급등',
    '미국 떡상',
    '해외 떡상',
    '미국 급등주',
    '해외 급등주',

    // 투자자 타겟
    '개미 오늘',
    '개미 떡상',
    '개미 급등주',
    '주린이 추천',
    '개인 투자자',
    '소액 투자',
    '투자 추천 오늘',

    // 상황별 키워드
    '상한가',
    '급상승',
    '폭등',
    '급등',
    '주가 급등',
    '종목 추천',
    '주식 추천',
    '투자 정보',
    '주식 정보',

    // 시간 관련
    '매시간 업데이트',
    '실시간 업데이트',
    '최신 정보',
    '따끈따끈',
    '방금 전',
    '지금 바로',
    '즉시 확인',
  ],

  openGraph: {
    title: '오늘의 떡상 🔥 실시간 급등주 AI 분석',
    description:
      '지금 이 시간 가장 뜨거운 급등주들! 매시간 업데이트되는 AI 분석 결과를 확인하세요',
    type: 'website',
    images: [
      {
        url: '/og-image-2.jpg', // ✅ 실제 존재하는 파일 사용
        width: 1200,
        height: 630,
        alt: '오늘의 떡상 - 실시간 급등주 AI 분석',
      },
    ],
    locale: 'ko_KR',
    siteName: '떡상',
  },

  twitter: {
    card: 'summary_large_image',
    title: '오늘의 떡상 🔥 실시간 급등주',
    description:
      '지금 가장 뜨거운 급등주들을 AI가 분석! #오늘의떡상 #급등주 #AI주식',
    images: ['/og-image-2.jpg'], // ✅ 실제 존재하는 파일 사용
  },

  alternates: {
    canonical:
      `${process.env.NEXT_PUBLIC_APP_URL}/today` ||
      'https://example.com/today',
  },

  other: {
    // Today 페이지 특화 메타 태그
    'page-topic': '오늘의 떡상, 실시간 급등주, AI 분석, 매시간 업데이트',
    'page-type': 'realtime-data, stock-analysis',
    'content-language': 'ko-KR',
    audience: '개미투자자, 주린이, 개인투자자, 실시간투자자',
    'page-subject': '오늘의 떡상 종목 실시간 AI 분석 페이지',
    'content-category': 'finance, investment, real-time-data',
    'update-schedule': 'hourly',

    // 데이터 특성
    'data-freshness': 'hourly',
    'data-source': 'ai-analysis, market-data',
    'market-coverage': 'korea, usa, kospi, kosdaq',

    // 사용자 의도
    'user-intent': 'investment-decision, market-monitoring, stock-research',
    'conversion-goal': 'engagement, retention, investment-action',

    // 콘텐츠 속성
    'content-depth': 'comprehensive',
    'analysis-type': 'ai-powered, real-time',
    'information-value': 'high, actionable',

    // 검색엔진 힌트
    'primary-keyword': '오늘의 떡상',
    'secondary-keywords': '실시간 급등주, AI 분석, 매시간 업데이트',
    'content-freshness': 'hourly',
    'update-frequency': 'hourly',
    'crawl-priority': 'high',

    // JSON-LD 구조화된 데이터 (프로덕션에서만)
    ...(process.env.NODE_ENV === 'production' && {
      'application/ld+json': JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebPage',
        name: '오늘의 떡상',
        description: '실시간 급등주 AI 분석 페이지',
        url:
          `${process.env.NEXT_PUBLIC_APP_URL}/today` ||
          'https://example.com/today',
        mainEntity: {
          '@type': 'Dataset',
          name: '오늘의 떡상 데이터',
          description: 'AI가 분석한 실시간 급등주 정보',
          temporalCoverage: 'R/P1D', // 매일 반복
          spatialCoverage: {
            '@type': 'Place',
            name: '대한민국, 미국 주식시장',
          },
          creator: {
            '@type': 'Organization',
            name: '떡상',
            url: process.env.NEXT_PUBLIC_APP_URL || 'https://example.com',
          },
          keywords: '떡상, 급등주, 실시간, AI 분석',
          license: 'https://creativecommons.org/licenses/by/4.0/',
          dateModified: new Date().toISOString(),
          updateFrequency: 'PT1H', // 매시간 업데이트
        },
        breadcrumb: {
          '@type': 'BreadcrumbList',
          itemListElement: [
            {
              '@type': 'ListItem',
              position: 1,
              name: '홈',
              item: process.env.NEXT_PUBLIC_APP_URL || 'https://example.com',
            },
            {
              '@type': 'ListItem',
              position: 2,
              name: '오늘의 떡상',
              item:
                `${process.env.NEXT_PUBLIC_APP_URL}/today` ||
                'https://example.com/today',
            },
          ],
        },
        potentialAction: {
          '@type': 'ViewAction',
          target: {
            '@type': 'EntryPoint',
            urlTemplate:
              `${process.env.NEXT_PUBLIC_APP_URL}/today` ||
              'https://example.com/today',
          },
          object: {
            '@type': 'WebPage',
            name: '오늘의 떡상',
          },
        },
      }),
    }),
  },
};

interface TodayPageProps {
  searchParams: Promise<{ country?: string }>;
}

export default async function Today({ searchParams }: TodayPageProps) {
  const { user } = await getCurrentSession();
  const params = await searchParams;
  const countryCode = params.country || 'KR';

  const { stocks, meta } = await getCachedTodayStocksWithCTE(countryCode);

  const otherCountry = countryCode === 'KR' ? 'US' : 'KR';
  getCachedTodayStocksWithCTE(otherCountry).catch(() => {}); // 에러 무시, 결과 사용 안 함

  const getWelcomeMessage = (
    user?: User | null,
    countryCode: string = 'KR'
  ) => {
    const countryName = countryCode === 'US' ? '미국' : '한국';
    if (!user) {
      return (
        <>
          안녕하세요 고객님😊
          <br />
          오늘의 {countryName} 떡상은?
        </>
      );
    }
    return (
      <>
        안녕하세요. {user.nickname}님! 😊
        <br />
        오늘의 {countryName} 떡상은?
      </>
    );
  };

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <div className="flex-1">
          <CountrySelector currentCountry={countryCode} currentPath="/today" />
        </div>
        <div className="pr-4">
          <ShareButton
            stocks={stocks}
            pageType="today"
            countryCode={countryCode}
          />
        </div>
      </div>

      <div className="flex justify-between px-4">
        <Text variant="s1">{getWelcomeMessage(user, countryCode)}</Text>
        <DataTimestamp meta={meta} className="items-end" />
      </div>

      <ScrollContainer className="px-4 py-4">
        <StocksList
          stocks={stocks}
          countryCode={countryCode}
          pageType="today"
        />
      </ScrollContainer>
    </>
  );
}
