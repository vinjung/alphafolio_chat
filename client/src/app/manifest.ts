import { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: '떡상 - AI 주식 정보 서비스',
    short_name: '떡상',
    description: '떡상이 알아서 핵심만 챙겨주는 AI 주식 정보 서비스',
    start_url: '/',
    display: 'standalone',
    background_color: '#ffffff',
    theme_color: '#FF2233',
    orientation: 'portrait',

    // ✅ 실제 public 폴더의 기존 파일들 참조
    icons: [
      {
        src: '/android-chrome-192x192.png', // public/android-chrome-192x192.png
        sizes: '192x192',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: '/android-chrome-512x512.png', // public/android-chrome-512x512.png
        sizes: '512x512',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: '/android-chrome-512x512.png', // 같은 파일을 maskable로도 사용
        sizes: '512x512',
        type: 'image/png',
        purpose: 'maskable',
      },
    ],

    categories: ['finance', 'business', 'productivity'],
    lang: 'ko-KR',

    shortcuts: [
      {
        name: '오늘의 떡상',
        short_name: '오늘',
        description: '오늘 주목할 종목 확인',
        url: '/today',
        icons: [
          {
            src: '/android-chrome-192x192.png', // public 폴더 파일 참조
            sizes: '192x192',
          },
        ],
      },
    ],
  };
}
