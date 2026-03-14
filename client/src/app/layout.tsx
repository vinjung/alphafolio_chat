import '../styles/globals.css';
import { pretendard, recipekorea } from '@/styles/fonts';
import { SplashScreen } from '@/components/splash-screen';
import { CountryFlagPolyfill } from '@/components/country-flag-polyfill';
import type { Metadata, Viewport } from 'next';
import { GoogleTagManager } from '@next/third-parties/google';

const ogContentSets = [
  {
    image: '/og-image-1.jpg',
    title: '이걸 놓쳤다고..? 오늘 급등 종목 모음 🔥',
    description: '이 종목 실화냐 댓글 폭주중... 오늘 급등 종목 모아봤어요.',
    alt: '오늘 떡상 종목 모음 - 떡상',
  },
  {
    image: '/og-image-2.jpg',
    title: '개미도 웃었다... 오늘의 급등주 리스트 💹',
    description:
      '방금 전까지 조용하더니 떡상 시작🔥 지금 확인 안 하면 놓칩니다.',
    alt: '개미 투자자 필독 오늘의 떡상 정보 - 떡상',
  },
  {
    image: '/og-image-3.jpg',
    title: '이걸 놓쳤다고..? 오늘 급등 종목 모음 🔥',
    description: '이 종목 실화냐 댓글 폭주중... 오늘 급등 종목 모아봤어요.',
    alt: '오늘 떡상 종목 모음 - 떡상',
  },
];

function getTimeBasedOgContent() {
  const currentHour = new Date().getHours();
  const contentIndex = Math.floor(currentHour / 2) % ogContentSets.length;
  return ogContentSets[contentIndex];
}

// ✅ viewport 설정을 별도로 export
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1.0,
  maximumScale: 1.0,
  userScalable: false,
  viewportFit: 'cover',
};

export async function generateMetadata(): Promise<Metadata> {
  const selectedContent = getTimeBasedOgContent();
  const siteUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://example.com';

  return {
    title: {
      default: '떡상 - AI 주식 정보 서비스',
      template: '%s | 떡상',
    },
    description: selectedContent.description,
    keywords: ['주식', '투자', 'AI', '떡상', '주식정보', '급등주'],
    metadataBase: new URL(siteUrl),
    verification: {
      google: 'Cy7EcmVN30X847MUoZAv4IhPG05kfwl0QyLas1LWp1g',
    },
    other: {
      'naver-site-verification': 'c2d15e6a4204fb78ec6371ca62ef14f4a58d5602',
    },
    openGraph: {
      type: 'website',
      locale: 'ko_KR',
      url: siteUrl,
      title: selectedContent.title,
      description: selectedContent.description,
      siteName: '떡상',
      images: [
        {
          url: selectedContent.image,
          width: 1200,
          height: 630,
          alt: selectedContent.alt,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: selectedContent.title,
      description: selectedContent.description,
      images: [selectedContent.image],
    },
    // ✅ 검색엔진 크롤링 설정
    robots: {
      index: true,
      follow: true,
      googleBot: {
        index: true,
        follow: true,
        'max-image-preview': 'large',
        'max-snippet': -1,
      },
    },
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ko"
      className={`${pretendard.variable} ${recipekorea.variable}`}
    >
      <body className="overflow-hidden">
        {/* 🇰🇷 국가 이모지 폴리필 - npm 패키지 방식 */}
        <CountryFlagPolyfill />

        {/* 🎯 PC에서 모바일 크기 제한을 위한 래퍼 */}
        <div className="h-dvh flex justify-center overflow-hidden">
          <div
            id="mobile-container"
            className="mobile-container w-full max-w-[428px] bg-neutral-0 h-dvh flex flex-col relative overflow-hidden font-pretendard pt-safe-top"
            style={{ position: 'relative' }} // 🎯 명시적 relative positioning 추가
          >
            <SplashScreen />
            {children}
          </div>
        </div>
      </body>
      <GoogleTagManager gtmId={process.env.NEXT_PUBLIC_GTM_ID!} />
    </html>
  );
}
