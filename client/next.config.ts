// client/next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // 🚀 운영환경에서 console.log 자동 제거
  compiler: {
    removeConsole:
      process.env.NODE_ENV === 'production'
        ? {
            exclude: ['error', 'warn', 'info'], // error, warn, info는 유지
          }
        : false,
  },

  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: '*.kakaocdn.net',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'http',
        hostname: 't1.kakaocdn.net',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'res.cloudinary.com',
        port: '',
        pathname: '/**',
      },
    ],
  },

  webpack(config, { isServer }) {
    const fileLoaderRule = config.module.rules.find((rule: any) =>
      rule.test?.test?.('.svg')
    );

    config.module.rules.push(
      // ?url 접미사가 있는 SVG는 파일로 처리
      {
        ...(fileLoaderRule as object),
        test: /\.svg$/i,
        resourceQuery: /url/,
      },
      // 일반 SVG import는 React 컴포넌트로 처리 (SVGR 옵션 추가)
      {
        test: /\.svg$/i,
        issuer: fileLoaderRule?.issuer,
        resourceQuery: {
          not: [...(fileLoaderRule?.resourceQuery?.not || []), /url/],
        },
        use: [
          {
            loader: '@svgr/webpack',
            options: {
              icon: true,
              svgoConfig: {
                plugins: [
                  {
                    name: 'preset-default',
                    params: {
                      overrides: {
                        removeViewBox: false,
                      },
                    },
                  },
                ],
              },
            },
          },
        ],
      }
    );

    (fileLoaderRule as any).exclude = /\.svg$/i;
    return config;
  },

  // Turbopack 설정 (개발 환경용)
  turbopack: {
    rules: {
      '*.svg': {
        loaders: [
          {
            loader: '@svgr/webpack',
            options: {
              icon: true,
              svgoConfig: {
                plugins: [
                  {
                    name: 'preset-default',
                    params: {
                      overrides: {
                        removeViewBox: false,
                      },
                    },
                  },
                ],
              },
            },
          },
        ],
        as: '*.js',
      },
    },
  },
};

export default nextConfig;
