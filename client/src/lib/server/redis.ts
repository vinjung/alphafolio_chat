import { Redis } from 'ioredis';
import { logger } from '@/lib/utils/logger';

const log = logger.child({ module: 'redis-client' });

// REDIS_URL 환경 변수 유효성 검사
const redisUrl = process.env.REDIS_URL;
if (!redisUrl) {
  log.error(
    'FATAL: REDIS_URL 환경 변수가 설정되지 않았습니다. Redis 연결이 불가능합니다.'
  );
  throw new Error('REDIS_URL environment variable is not set.');
}

const globalForRedis = globalThis as unknown as {
  redis?: Redis;
};

let redis: Redis;

const redisOptions = {
  lazyConnect: true,
  connectTimeout: 10000,
  enableOfflineQueue: false,
  maxRetriesPerRequest: 0,
};

if (process.env.NODE_ENV === 'production') {
  log.info('Production 환경 Redis 연결 시도...');
  // '?family=0' 제거 후 테스트
  redis = new Redis(redisUrl, redisOptions);

  redis.on('connect', () => log.info('Production Redis 연결 성공!'));
  redis.on('error', (err) => {
    log.error('Production Redis 연결 오류 발생!', {
      error_message: err.message,
      error_name: err.name,
      error_stack: err.stack,
      redis_url_prefix: redisUrl.substring(0, 20) + '...',
      connecting_to:
        new URL(redisUrl).protocol + '//' + new URL(redisUrl).hostname,
    });
  });
  redis.on('reconnecting', (delay: number) =>
    log.warn(`Production Redis 재연결 시도 중... (딜레이: ${delay}ms)`)
  );
  redis.on('end', () => log.info('Production Redis 연결 종료.'));
} else {
  if (!globalForRedis.redis) {
    log.info('Development 환경 Redis 연결 시도 (싱글톤)...');
    globalForRedis.redis = new Redis(redisUrl, redisOptions);
    globalForRedis.redis.on('connect', () =>
      log.info('Development Redis 연결 성공!')
    );
    globalForRedis.redis.on('error', (err) =>
      log.error('Development Redis 연결 오류 발생!', {
        error_message: err.message,
        error_name: err.name,
        error_stack: err.stack,
        redis_url_prefix: redisUrl.substring(0, 20) + '...',
        connecting_to:
          new URL(redisUrl).protocol + '//' + new URL(redisUrl).hostname,
      })
    );
    globalForRedis.redis.on('reconnecting', (delay: number) =>
      log.warn(`Development Redis 재연결 시도 중... (딜레이: ${delay}ms)`)
    );
    globalForRedis.redis.on('end', () =>
      log.info('Development Redis 연결 종료.')
    );
  }
  redis = globalForRedis.redis;
}

export { redis };
