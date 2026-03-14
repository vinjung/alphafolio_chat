import type { NextRequest } from 'next/server';
import { createHash } from 'crypto';

interface LogData {
  [key: string]: unknown;
}

interface LogContext {
  correlationId?: string;
  userId?: string;
  sessionId?: string;
  [key: string]: unknown;
}

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

// 환경 감지 (더 명확하게)
const nodeEnv = process.env.NODE_ENV || 'development';
const isDevelopment = nodeEnv === 'development';
const isProduction = nodeEnv === 'production';
const isTest = nodeEnv === 'test';

// Railway 환경 감지
const isRailway = !!(
  process.env.RAILWAY_ENVIRONMENT || process.env.RAILWAY_SERVICE_NAME
);

// 로그 레벨 설정
const logLevel = process.env.LOG_LEVEL || (isDevelopment ? 'debug' : 'info');

// 로그 레벨 우선순위
const levels: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

const shouldLog = (level: LogLevel): boolean => {
  const currentLevel = levels[logLevel as LogLevel] ?? levels.info;
  return levels[level] >= currentLevel;
};

// 🎨 로컬 개발용 Next.js 스타일 포맷터
const formatLocal = (
  level: LogLevel,
  message: string,
  context: LogContext,
  data?: LogData
) => {
  // Next.js 스타일 심볼과 컬러
  const styles = {
    debug: { symbol: '◐', color: '\x1b[36m' }, // cyan
    info: { symbol: '○', color: '\x1b[32m' }, // green
    warn: { symbol: '⚠', color: '\x1b[33m' }, // yellow
    error: { symbol: '⨯', color: '\x1b[31m' }, // red
  };

  const reset = '\x1b[0m';
  const gray = '\x1b[90m';
  const { symbol, color } = styles[level];

  // Next.js 형태: ○ message
  let output = `${color}${symbol}${reset} ${message}`;

  // correlationId 추가
  if (context.correlationId) {
    output += ` ${gray}(${context.correlationId})${reset}`;
  }

  // userId 추가
  if (context.userId) {
    output += ` ${gray}[${context.userId}]${reset}`;
  }

  console.log(output);

  // 추가 데이터를 들여쓰기로 표시 (개발 환경에서만)
  if (isDevelopment) {
    const extraData = { ...context, ...data };
    delete extraData.correlationId;
    delete extraData.userId;
    delete extraData.sessionId;

    Object.entries(extraData).forEach(([key, value]) => {
      if (value === undefined || value === null) return;
      const formattedValue =
        typeof value === 'string' ? value : JSON.stringify(value);
      console.log(`  ${gray}${key}: ${formattedValue}${reset}`);
    });
  }
};

// 🚄 Railway/Production용 구조화된 JSON 포맷터
const formatProduction = (
  level: LogLevel,
  message: string,
  context: LogContext,
  data?: LogData
) => {
  const logEntry = {
    level,
    message,
    timestamp: new Date().toISOString(),
    service: process.env.RAILWAY_SERVICE_NAME || 'nextjs-app',
    environment: nodeEnv,
    ...(isRailway && {
      railway: {
        deploymentId: process.env.RAILWAY_DEPLOYMENT_ID,
        environmentName: process.env.RAILWAY_ENVIRONMENT,
        serviceName: process.env.RAILWAY_SERVICE_NAME,
      },
    }),
    ...context,
    ...data,
  };

  const json = JSON.stringify(logEntry);

  switch (level) {
    case 'error':
      console.error(json);
      break;
    case 'warn':
      console.warn(json);
      break;
    default:
      console.log(json);
  }
};

// 🧪 테스트용 간소화된 포맷터
const formatTest = (
  level: LogLevel,
  message: string,
  context: LogContext,
  data?: LogData
) => {
  const testEntry = {
    level,
    message,
    ...(context.correlationId && { correlationId: context.correlationId }),
    ...(data && Object.keys(data).length > 0 && { data }),
  };

  console.log(JSON.stringify(testEntry));
};

// 메인 로거 클래스
class Logger {
  private context: LogContext;

  constructor(context: LogContext = {}) {
    this.context = context;
  }

  child(context: LogContext): Logger {
    return new Logger({ ...this.context, ...context });
  }

  private log(level: LogLevel, message: string, data?: LogData): void {
    if (!shouldLog(level)) return;

    // 🎯 환경별 포맷터 선택 로직 개선
    if (isDevelopment) {
      formatLocal(level, message, this.context, data);
    } else if (isTest) {
      formatTest(level, message, this.context, data);
    } else {
      // production, staging, 기타 모든 환경
      formatProduction(level, message, this.context, data);
    }
  }

  debug(message: string, data?: LogData): void {
    this.log('debug', message, data);
  }

  info(message: string, data?: LogData): void {
    this.log('info', message, data);
  }

  warn(message: string, data?: LogData): void {
    this.log('warn', message, data);
  }

  error(message: string, error?: unknown, data?: LogData): void {
    let errorInfo: LogData = {};

    if (error instanceof Error) {
      errorInfo = {
        error: error.message,
        name: error.name,
        // 개발환경에서만 스택 트레이스 포함
        ...(isDevelopment && { stack: error.stack }),
        // 프로덕션에서는 스택 트레이스 해시만 포함 (디버깅용)
        ...(!isDevelopment &&
          error.stack && {
            stackHash: createHash('md5')
              .update(error.stack)
              .digest('hex')
              .substring(0, 8),
          }),
      };
    } else if (error) {
      errorInfo = { error: String(error) };
    }

    this.log('error', message, { ...errorInfo, ...data });
  }

  // 환경별 설정 정보 로깅 (초기화 시 유용)
  logEnvironmentInfo(): void {
    if (isDevelopment) {
      this.info('로거 환경 정보', {
        nodeEnv,
        isDevelopment,
        isProduction,
        isTest,
        isRailway,
        logLevel,
        ...(isRailway && {
          railwayInfo: {
            environment: process.env.RAILWAY_ENVIRONMENT,
            serviceName: process.env.RAILWAY_SERVICE_NAME,
            deploymentId: process.env.RAILWAY_DEPLOYMENT_ID,
          },
        }),
      });
    }
  }
}

// 유틸리티 함수들
export const createCorrelationId = (): string => {
  return Math.random().toString(36).substring(2, 12);
};

export const extractRequestMeta = (
  request: Request | NextRequest
): LogContext => {
  const url = new URL(request.url);
  return {
    method: request.method,
    host: request.headers.get('host'),
    path: url.pathname,
    query: url.search,
    userAgent: request.headers.get('user-agent')?.substring(0, 50) + '...',
    ip:
      request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ||
      request.headers.get('x-real-ip') ||
      'unknown',
    referer: request.headers.get('referer'),
  };
};

export const createTimer = () => {
  const start = Date.now();
  return {
    elapsed: () => Date.now() - start,
    duration: () => `${Date.now() - start}ms`,
    since: (timestamp: number) => `${Date.now() - timestamp}ms`,
  };
};

// 메인 로거 인스턴스
export const logger = new Logger();

// 환경 정보 자동 로깅 (개발 환경에서만)
if (typeof window === 'undefined' && isDevelopment) {
  // 서버 사이드 & 개발 환경에서만
  logger.logEnvironmentInfo();
}

// 타입 exports
export type { LogLevel, LogData, LogContext };

// 🎯 Railway 특화 헬퍼
export const createRailwayLogger = (serviceName: string) => {
  return logger.child({
    service: serviceName,
    railway: isRailway,
    deploymentId: process.env.RAILWAY_DEPLOYMENT_ID,
  });
};
