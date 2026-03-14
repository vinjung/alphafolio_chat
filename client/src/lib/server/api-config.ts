interface APIConfig {
  fastapi: {
    baseUrl: string;
    timeout: number;
    streamTimeout: number; // ✅ 스트리밍 전용 타임아웃 추가
  };
  environment: {
    type: 'development' | 'production' | 'test';
    platform: 'local' | 'railway' | 'unknown';
  };
}

function detectEnvironment() {
  // Railway 환경 감지
  const isRailway = !!(
    process.env.RAILWAY_ENVIRONMENT || process.env.RAILWAY_SERVICE_NAME
  );

  // 환경 타입 감지
  const nodeEnv = process.env.NODE_ENV || 'development';

  return {
    isRailway,
    isDevelopment: nodeEnv === 'development',
    isProduction: nodeEnv === 'production',
    railwayEnv: process.env.RAILWAY_ENVIRONMENT,
  };
}

function createAPIConfig(): APIConfig {
  const env = detectEnvironment();

  let fastApiBaseUrl: string;

  if (env.isRailway) {
    // Railway 환경 - 환경변수 우선순위 적용
    const rawUrl =
      process.env.FASTAPI_URL || // Railway 템플릿 변수 우선
      process.env.FASTAPI_INTERNAL_URL || // 수동 설정 URL
      'https://api-production-0e7f.up.railway.app'; // 기본값

    // URL에 프로토콜이 없으면 https:// 추가
    if (!rawUrl.startsWith('http://') && !rawUrl.startsWith('https://')) {
      fastApiBaseUrl = `https://${rawUrl}`;
    } else {
      fastApiBaseUrl = rawUrl;
    }
  } else {
    // 로컬 개발 환경
    fastApiBaseUrl =
      process.env.FASTAPI_URL || // .env 파일 설정이 있으면 사용
      'http://localhost:8000'; // 로컬 기본값
  }

  return {
    fastapi: {
      baseUrl: fastApiBaseUrl,
      // ✅ 일반 API 타임아웃 (기존)
      timeout: env.isProduction ? 60000 : 30000,
      // ✅ 스트리밍 전용 타임아웃 (충분히 길게 설정)
      streamTimeout: env.isProduction ? 300000 : 180000, // 프로덕션 5분, 개발 3분
    },
    environment: {
      type: env.isDevelopment ? 'development' : 'production',
      platform: env.isRailway ? 'railway' : 'local',
    },
  };
}

// 싱글톤 패턴으로 설정 캐시
let cachedConfig: APIConfig | null = null;

export function getAPIConfig(): APIConfig {
  if (!cachedConfig) {
    cachedConfig = createAPIConfig();
  }
  return cachedConfig;
}

// 디버깅용 헬퍼
export function logConfigDebug() {
  const config = getAPIConfig();
  const debugInfo = {
    fastApiBaseUrl: config.fastapi.baseUrl,
    timeout: config.fastapi.timeout,
    streamTimeout: config.fastapi.streamTimeout,
    environment: config.environment,
    envVars: {
      NODE_ENV: process.env.NODE_ENV,
      RAILWAY_ENVIRONMENT: process.env.RAILWAY_ENVIRONMENT,
      RAILWAY_SERVICE_NAME: process.env.RAILWAY_SERVICE_NAME,
      FASTAPI_URL: process.env.FASTAPI_URL ? 'SET' : 'UNSET',
    },
  };

  if (process.env.NODE_ENV === 'development') {
    console.log('[Config] Current configuration:', debugInfo);
  }
}
