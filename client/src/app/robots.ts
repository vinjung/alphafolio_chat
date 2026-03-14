import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://example.com';

  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: [
          '/api/', // API 엔드포인트 크롤링 차단
          '/admin/', // 관리자 페이지 차단 (있다면)
          '/_next/', // Next.js 내부 파일 차단
          '/static/', // 정적 파일 차단
          '*.json', // JSON 파일 차단
          '/auth/', // 인증 관련 페이지 차단 (있다면)
        ],
      },
      // ✅ 구글봇 설정
      {
        userAgent: 'Googlebot',
        allow: '/',
        disallow: ['/api/', '/admin/'],
      },
      // ✅ 네이버봇(Yeti) 설정
      {
        userAgent: 'Yeti',
        allow: '/',
        disallow: ['/api/', '/admin/'],
      },
      // ✅ 빙봇 설정
      {
        userAgent: 'Bingbot',
        allow: '/',
        disallow: ['/api/', '/admin/'],
      },
      // ✅ 다음봇 설정
      {
        userAgent: 'Daum',
        allow: '/',
        disallow: ['/api/', '/admin/'],
      },
      // ✅ 기타 주요 검색엔진 봇들
      {
        userAgent: 'DuckDuckBot', // 덕덕고
        allow: '/',
        disallow: ['/api/', '/admin/'],
      },
      {
        userAgent: 'facebookexternalhit', // 페이스북
        allow: '/',
        disallow: ['/api/', '/admin/'],
      },
      {
        userAgent: 'Twitterbot', // 트위터
        allow: '/',
        disallow: ['/api/', '/admin/'],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
    host: baseUrl,
  };
}
