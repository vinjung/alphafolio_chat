import { ScrollContainer } from '../_components/scroll-container';
import { CountrySelector } from '../_components/country-selector';
import { StocksList } from '../_components/stocks-list';
import { ShareButton } from '../_components/share-button';
import { getCurrentSession } from '@/lib/server/session';
import { Text } from '@/components/shared/text';
import { getCachedFutureStocksWithCTE } from '@/lib/server/stock-data';
import { DataTimestamp } from '../_components/data-timestamp';
import { User } from '@/lib/server/models';
import { Metadata } from 'next';

// ✅ Future 페이지 전용 SEO 최적화 메타데이터
export const metadata: Metadata = {
  title: '미래의 떡상 - AI 급등주 예측 분석 | 떡상',
  description:
    '🚀 내일 폭등할 종목을 미리 확인하세요! AI가 예측한 미래의 떡상 종목과 급등 가능성을 분석합니다. 한국과 미국 시장의 유망 종목을 매시간 업데이트.',

  keywords: [
    // 메인 타겟 키워드
    '미래의 떡상',
    '내일 떡상',
    '떡상 내일',
    '떡상 예측',
    '내일의 급등주',
    '내일 급등주',
    '급등주 예측',
    '급등주 내일',

    // 예측 관련 키워드
    '떡상 예측',
    '급등 예측',
    'AI 예측',
    '주가 예측',
    '폭등 예측',
    '상승 예측',
    '종목 예측',
    '투자 예측',

    // AI 분석 관련
    'AI 떡상 예측',
    'AI 급등주 예측',
    '인공지능 예측',
    'AI 주가 예측',
    '머신러닝 예측',
    'AI 투자 예측',

    // 미래 관련 키워드
    '미래 떡상',
    '앞으로 떡상',
    '곧 떡상',
    '예상 떡상',
    '미래 급등주',
    '앞으로 급등',
    '곧 급등',
    '예상 급등',

    // 투자 전략 관련
    '선제 투자',
    '미리 투자',
    '사전 투자',
    '예측 투자',
    '내일 투자',
    '미래 투자',
    '선점 투자',
    '기회 포착',

    // 시장별 키워드
    '한국 예측',
    '국내 예측',
    '코스피 예측',
    '코스닥 예측',
    '미국 예측',
    '해외 예측',
    '미국주식 예측',
    '해외주식 예측',

    // 투자자 타겟
    '개미 예측',
    '개미 내일',
    '주린이 예측',
    '개인투자자',
    '소액 투자자',
    '미래 수익',
    '선점 기회',

    // 상황별 키워드
    '상한가 예측',
    '급상승 예측',
    '폭등 예측',
    '대박 예측',
    '유망 종목',
    '추천 종목',
    '주목 종목',
    '기대 종목',

    // 시간 관련
    '미리 확인',
    '사전 준비',
    '선제 대응',
    '기회 발견',
    '내일 준비',
    '미래 준비',
    '투자 기회',
    '수익 기회',
  ],

  openGraph: {
    title: '미래의 떡상 🚀 AI 급등주 예측 분석',
    description:
      '내일 폭등할 종목을 미리 확인! AI가 예측한 미래의 떡상 종목과 급등 가능성 분석',
    type: 'website',
    images: [
      {
        url: '/og-image-3.jpg', // ✅ 실제 존재하는 파일 사용
        width: 1200,
        height: 630,
        alt: '미래의 떡상 - AI 급등주 예측 분석',
      },
    ],
    locale: 'ko_KR',
    siteName: '떡상',
  },

  twitter: {
    card: 'summary_large_image',
    title: '미래의 떡상 🚀 AI 급등주 예측',
    description:
      '내일 폭등할 종목을 미리 확인! #내일의떡상 #급등주예측 #AI예측',
    images: ['/og-image-3.jpg'], // ✅ 실제 존재하는 파일 사용
  },

  alternates: {
    canonical:
      `${process.env.NEXT_PUBLIC_APP_URL}/future` ||
      'https://example.com/future',
  },

  other: {
    // Future 페이지 특화 메타 태그
    'page-topic': '미래의 떡상, 급등주 예측, AI 예측, 투자 기회',
    'page-type': 'prediction-data, ai-analysis',
    'content-language': 'ko-KR',
    audience: '개미투자자, 주린이, 개인투자자, 선제투자자',
    'page-subject': '미래의 떡상 종목 AI 예측 분석 페이지',
    'content-category': 'finance, prediction, investment, ai-analysis',
    'prediction-horizon': '24hours',

    // 데이터 특성
    'data-freshness': 'hourly',
    'data-type': 'predictive, ai-generated',
    'analysis-method': 'machine-learning, ai-prediction',
    'market-coverage': 'korea, usa, kospi, kosdaq',

    // 사용자 의도
    'user-intent':
      'future-investment, opportunity-discovery, profit-maximization',
    'conversion-goal': 'early-investment, profit-opportunity',
    'investment-strategy': 'proactive, predictive',

    // 콘텐츠 속성
    'content-depth': 'predictive-analysis',
    'analysis-type': 'ai-prediction, future-oriented',
    'information-value': 'high-potential, opportunity',
    'risk-level': 'prediction-based',

    // 검색엔진 힌트
    'primary-keyword': '미래의 떡상',
    'secondary-keywords': '급등주 예측, AI 예측, 투자 기회',
    'content-freshness': 'hourly',
    'update-frequency': 'hourly',
    'crawl-priority': 'high',
    'prediction-accuracy': 'ai-powered',

    // JSON-LD 구조화된 데이터 (프로덕션에서만)
    ...(process.env.NODE_ENV === 'production' && {
      'application/ld+json': JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebPage',
        name: '미래의 떡상',
        description: 'AI 급등주 예측 분석 페이지',
        url:
          `${process.env.NEXT_PUBLIC_APP_URL}/future` ||
          'https://example.com/future',
        mainEntity: {
          '@type': 'Dataset',
          name: '미래의 떡상 예측 데이터',
          description: 'AI가 예측한 내일의 급등주 정보',
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
          keywords: '떡상, 급등주, 예측, AI 분석, 투자 기회',
          license: 'https://creativecommons.org/licenses/by/4.0/',
          dateModified: new Date().toISOString(),
          updateFrequency: 'PT1H', // 매시간 업데이트
          variableMeasured: {
            '@type': 'PropertyValue',
            name: '급등 가능성',
            description: 'AI 모델이 예측한 내일의 급등 확률',
          },
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
              name: '미래의 떡상',
              item:
                `${process.env.NEXT_PUBLIC_APP_URL}/future` ||
                'https://example.com/future',
            },
          ],
        },
        potentialAction: {
          '@type': 'ViewAction',
          target: {
            '@type': 'EntryPoint',
            urlTemplate:
              `${process.env.NEXT_PUBLIC_APP_URL}/future` ||
              'https://example.com/future',
          },
          object: {
            '@type': 'WebPage',
            name: '미래의 떡상',
          },
        },
        about: {
          '@type': 'Thing',
          name: '주식 투자 예측',
          description: 'AI 기술을 활용한 주식 급등 예측 서비스',
        },
      }),
    }),
  },
};

interface FuturePageProps {
  searchParams: Promise<{ country?: string }>;
}

export default async function Future({ searchParams }: FuturePageProps) {
  const { user } = await getCurrentSession();
  const params = await searchParams;
  const countryCode = params.country || 'KR';

  const { stocks, meta } = await getCachedFutureStocksWithCTE(countryCode);

  const otherCountry = countryCode === 'KR' ? 'US' : 'KR';
  getCachedFutureStocksWithCTE(otherCountry).catch(() => {});

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
          1년 후 미래의 {countryName} 떡상은?
        </>
      );
    }
    return (
      <>
        안녕하세요. {user.nickname}님! 😊
        <br />
        1년 후 미래의 {countryName} 떡상은?
      </>
    );
  };

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <div className="flex-1">
          <CountrySelector currentCountry={countryCode} currentPath="/future" />
        </div>
        <div className="pr-4">
          <ShareButton
            stocks={stocks}
            pageType="future"
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
