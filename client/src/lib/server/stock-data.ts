import { db } from './db';
import { todayKr, futureKr, todayUs, futureUs } from '@schema';
import { desc, and, isNotNull, lte, sql } from 'drizzle-orm';
import type { InferSelectModel } from 'drizzle-orm';
import { logger, createTimer } from '@/lib/utils/logger';
import { unstable_cache } from 'next/cache';

// 기존 타입 정의
export type TodayStockItem = InferSelectModel<typeof todayKr>;
export type FutureStockItem = InferSelectModel<typeof futureKr>;
export type TodayUsStockItem = InferSelectModel<typeof todayUs> & {
  countryCode: string;
};
export type FutureUsStockItem = InferSelectModel<typeof futureUs> & {
  countryCode: string;
};
export type StockItem =
  | TodayStockItem
  | FutureStockItem
  | TodayUsStockItem
  | FutureUsStockItem;

// 🆕 메타정보 타입 정의
export interface StockDataMeta {
  dataLoadedAt: Date; // 실제 DB 조회 시점
  cacheCreatedAt: Date; // 캐시 생성 시점
  nextUpdateAt: Date; // 다음 업데이트 예정 시점 (캐시 TTL 기준)
  recordUpdatedAt?: Date; // DB 레코드 업데이트 시점 (첫 번째 데이터 기준)
}

// 🆕 메타정보를 포함한 결과 타입 정의
export interface StockDataWithMeta {
  stocks: StockItem[];
  meta: StockDataMeta;
}

// 환경별 캐시 TTL 설정
const getCacheTTL = () => {
  if (process.env.NODE_ENV === 'development') return 60;
  if (process.env.NODE_ENV === 'test') return 30;
  return 1800;
};

// 🆕 메타정보 생성 헬퍼 함수
function createStockDataMeta(
  stocks: StockItem[],
  cacheCreatedAt: Date = new Date()
): StockDataMeta {
  const ttl = getCacheTTL(); // 현재 캐시 TTL 값 (초)
  const nextUpdateAt = new Date(cacheCreatedAt.getTime() + ttl * 1000);

  // 첫 번째 주식 데이터의 recordUpdatedAt을 참조 (있는 경우)
  const firstStock = stocks[0];
  const recordUpdatedAt = firstStock?.recordUpdatedAt
    ? new Date(firstStock.recordUpdatedAt)
    : undefined;

  return {
    dataLoadedAt: cacheCreatedAt,
    cacheCreatedAt,
    nextUpdateAt,
    recordUpdatedAt,
  };
}

// 재시도 함수
async function withRetry<T>(
  fn: () => Promise<T>,
  maxAttempts: number = 3
): Promise<T> {
  let lastError: Error;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      if (attempt === maxAttempts) {
        throw lastError;
      }

      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }

  throw lastError!;
}

// 🆕 하이브리드 방식 - Today KR
export async function getTodayStocksWithCTE(
  countryCode: string = 'KR'
): Promise<TodayStockItem[]> {
  const timer = createTimer();
  const log = logger.child({
    module: 'stock-data-kr-today-hybrid',
    countryCode,
    operation: 'database_query',
  });

  log.info('KR today stocks hybrid query started', {
    table: 'today_kr',
    queryType: 'hybrid_cte',
    cacheLayer: 'none',
  });

  try {
    // 1단계: ORM으로 기본 필터링
    const initialFiltered = await db
      .select()
      .from(todayKr)
      .where(
        and(
          // ✅ 수정: CURRENT_DATE → 가장 최근 날짜
          sql`${todayKr.recordUpdatedAt}::date = (SELECT MAX(${todayKr.recordUpdatedAt}::date) FROM ${todayKr})`,
          isNotNull(todayKr.futurePrice),
          lte(todayKr.futurePercent, '1500'),
          isNotNull(todayKr.url1),
          isNotNull(todayKr.title1)
        )
      )
      .orderBy(desc(todayKr.changePercent))
      .limit(30);

    // 2단계: 애플리케이션 레벨에서 CASE 로직 처리
    const processedStocks = initialFiltered.map((stock) => ({
      ...stock,
      futureEarnings: null,
      // url_1, title1, content1 세트 처리
      url1: stock.content1 ? stock.url1 : null,
      title1: stock.content1 ? stock.title1 : null,
      content1: stock.content1 ? stock.content1 : null,

      // url_2, title2, content2 세트 처리
      url2: stock.url2 && stock.title2 && stock.content2 ? stock.url2 : null,
      title2:
        stock.url2 && stock.title2 && stock.content2 ? stock.title2 : null,
      content2:
        stock.url2 && stock.title2 && stock.content2 ? stock.content2 : null,

      // url_3, title3, content3 세트 처리
      url3: stock.url3 && stock.title3 && stock.content3 ? stock.url3 : null,
      title3:
        stock.url3 && stock.title3 && stock.content3 ? stock.title3 : null,
      content3:
        stock.url3 && stock.title3 && stock.content3 ? stock.content3 : null,

      // url_4, title4, content4 세트 처리
      url4: stock.url4 && stock.title4 && stock.content4 ? stock.url4 : null,
      title4:
        stock.url4 && stock.title4 && stock.content4 ? stock.title4 : null,
      content4:
        stock.url4 && stock.title4 && stock.content4 ? stock.content4 : null,

      // url_5, title5, content5 세트 처리
      url5: stock.url5 && stock.title5 && stock.content5 ? stock.url5 : null,
      title5:
        stock.url5 && stock.title5 && stock.content5 ? stock.title5 : null,
      content5:
        stock.url5 && stock.title5 && stock.content5 ? stock.content5 : null,
    }));

    log.info('KR today stocks hybrid query completed', {
      database: {
        table: 'today_kr',
        recordCount: processedStocks.length,
        executionTime: timer.duration(),
        queryExecuted: true,
      },
      performance: {
        category:
          timer.elapsed() < 100
            ? 'fast'
            : timer.elapsed() < 500
              ? 'normal'
              : 'slow',
      },
    });

    return processedStocks;
  } catch (error) {
    log.error('KR today stocks hybrid query failed', error, {
      table: 'today_kr',
      duration: timer.duration(),
    });
    return [];
  }
}

// 🆕 하이브리드 방식 - Today US
export async function getTodayUsStocksWithCTE(): Promise<
  (TodayUsStockItem & { countryCode: string })[]
> {
  const timer = createTimer();
  const log = logger.child({
    module: 'stock-data-us-today-hybrid',
    countryCode: 'US',
    operation: 'database_query',
  });

  log.info('US today stocks hybrid query started', {
    table: 'today_us',
    queryType: 'hybrid_cte',
    cacheLayer: 'none',
  });

  try {
    // 1단계: ORM으로 기본 필터링
    const initialFiltered = await db
      .select()
      .from(todayUs)
      .where(
        and(
          // ✅ 수정: CURRENT_DATE → 가장 최근 날짜
          sql`${todayUs.recordUpdatedAt}::date = (SELECT MAX(${todayUs.recordUpdatedAt}::date) FROM ${todayUs})`,
          isNotNull(todayUs.futurePrice),
          lte(todayUs.futurePercent, '1500'),
          isNotNull(todayUs.url1),
          isNotNull(todayUs.title1)
        )
      )
      .orderBy(desc(todayUs.changePercent))
      .limit(30);

    // 2단계: 애플리케이션 레벨에서 CASE 로직 처리 + countryCode 추가
    const processedStocks = initialFiltered.map((stock) => ({
      ...stock,
      futureEarnings: null,
      countryCode: 'US',

      // url_1, title1, content1 세트 처리
      url1: stock.content1 ? stock.url1 : null,
      title1: stock.content1 ? stock.title1 : null,
      content1: stock.content1 ? stock.content1 : null,

      // url_2, title2, content2 세트 처리
      url2: stock.url2 && stock.title2 && stock.content2 ? stock.url2 : null,
      title2:
        stock.url2 && stock.title2 && stock.content2 ? stock.title2 : null,
      content2:
        stock.url2 && stock.title2 && stock.content2 ? stock.content2 : null,

      // url_3, title3, content3 세트 처리
      url3: stock.url3 && stock.title3 && stock.content3 ? stock.url3 : null,
      title3:
        stock.url3 && stock.title3 && stock.content3 ? stock.title3 : null,
      content3:
        stock.url3 && stock.title3 && stock.content3 ? stock.content3 : null,

      // url_4, title4, content4 세트 처리
      url4: stock.url4 && stock.title4 && stock.content4 ? stock.url4 : null,
      title4:
        stock.url4 && stock.title4 && stock.content4 ? stock.title4 : null,
      content4:
        stock.url4 && stock.title4 && stock.content4 ? stock.content4 : null,

      // url_5, title5, content5 세트 처리
      url5: stock.url5 && stock.title5 && stock.content5 ? stock.url5 : null,
      title5:
        stock.url5 && stock.title5 && stock.content5 ? stock.title5 : null,
      content5:
        stock.url5 && stock.title5 && stock.content5 ? stock.content5 : null,
    }));

    log.info('US today stocks hybrid query completed', {
      database: {
        table: 'today_us',
        recordCount: processedStocks.length,
        executionTime: timer.duration(),
        queryExecuted: true,
      },
      performance: {
        category:
          timer.elapsed() < 100
            ? 'fast'
            : timer.elapsed() < 500
              ? 'normal'
              : 'slow',
      },
    });

    return processedStocks;
  } catch (error) {
    log.error('US today stocks hybrid query failed', error, {
      table: 'today_us',
      duration: timer.duration(),
    });
    return [];
  }
}

// 🆕 하이브리드 방식 - Future KR
export async function getFutureStocksWithCTE(
  countryCode: string = 'KR'
): Promise<FutureStockItem[]> {
  const timer = createTimer();
  const log = logger.child({
    module: 'stock-data-kr-future-hybrid',
    countryCode,
    operation: 'database_query',
  });

  log.info('KR future stocks hybrid query started', {
    table: 'future_kr',
    queryType: 'hybrid_cte',
    cacheLayer: 'none',
  });

  try {
    // 1단계: ORM으로 기본 필터링 (future_percent로 정렬)
    const initialFiltered = await db
      .select()
      .from(futureKr)
      .where(
        and(
          // ✅ 수정: CURRENT_DATE → 가장 최근 날짜
          sql`${futureKr.recordUpdatedAt}::date = (SELECT MAX(${futureKr.recordUpdatedAt}::date) FROM ${futureKr})`,
          isNotNull(futureKr.futurePrice),
          lte(futureKr.futurePercent, '1000'),
          isNotNull(futureKr.url1),
          isNotNull(futureKr.title1)
        )
      )
      .orderBy(desc(futureKr.futurePercent))
      .limit(30);

    // 2단계: 애플리케이션 레벨에서 CASE 로직 처리
    const processedStocks = initialFiltered.map((stock) => ({
      ...stock,
      futureEarnings: null,
      // url_1, title1, content1 세트 처리
      url1: stock.content1 ? stock.url1 : null,
      title1: stock.content1 ? stock.title1 : null,
      content1: stock.content1 ? stock.content1 : null,

      // url_2, title2, content2 세트 처리
      url2: stock.url2 && stock.title2 && stock.content2 ? stock.url2 : null,
      title2:
        stock.url2 && stock.title2 && stock.content2 ? stock.title2 : null,
      content2:
        stock.url2 && stock.title2 && stock.content2 ? stock.content2 : null,

      // url_3, title3, content3 세트 처리
      url3: stock.url3 && stock.title3 && stock.content3 ? stock.url3 : null,
      title3:
        stock.url3 && stock.title3 && stock.content3 ? stock.title3 : null,
      content3:
        stock.url3 && stock.title3 && stock.content3 ? stock.content3 : null,

      // url_4, title4, content4 세트 처리
      url4: stock.url4 && stock.title4 && stock.content4 ? stock.url4 : null,
      title4:
        stock.url4 && stock.title4 && stock.content4 ? stock.title4 : null,
      content4:
        stock.url4 && stock.title4 && stock.content4 ? stock.content4 : null,

      // url_5, title5, content5 세트 처리
      url5: stock.url5 && stock.title5 && stock.content5 ? stock.url5 : null,
      title5:
        stock.url5 && stock.title5 && stock.content5 ? stock.title5 : null,
      content5:
        stock.url5 && stock.title5 && stock.content5 ? stock.content5 : null,
    }));

    log.info('KR future stocks hybrid query completed', {
      database: {
        table: 'future_kr',
        recordCount: processedStocks.length,
        executionTime: timer.duration(),
        queryExecuted: true,
      },
      performance: {
        category:
          timer.elapsed() < 100
            ? 'fast'
            : timer.elapsed() < 500
              ? 'normal'
              : 'slow',
      },
    });

    return processedStocks;
  } catch (error) {
    log.error('KR future stocks hybrid query failed', error, {
      table: 'future_kr',
      duration: timer.duration(),
    });
    return [];
  }
}

// 🆕 하이브리드 방식 - Future US
export async function getFutureUsStocksWithCTE(): Promise<
  (FutureUsStockItem & { countryCode: string })[]
> {
  const timer = createTimer();
  const log = logger.child({
    module: 'stock-data-us-future-hybrid',
    countryCode: 'US',
    operation: 'database_query',
  });

  log.info('US future stocks hybrid query started', {
    table: 'future_us',
    queryType: 'hybrid_cte',
    cacheLayer: 'none',
  });

  try {
    // 1단계: ORM으로 기본 필터링 (future_percent로 정렬)
    const initialFiltered = await db
      .select()
      .from(futureUs)
      .where(
        and(
          // ✅ 수정: CURRENT_DATE → 가장 최근 날짜
          sql`${futureUs.recordUpdatedAt}::date = (SELECT MAX(${futureUs.recordUpdatedAt}::date) FROM ${futureUs})`,
          isNotNull(futureUs.futurePrice),
          lte(futureUs.futurePercent, '1500'),
          isNotNull(futureUs.url1),
          isNotNull(futureUs.title1)
        )
      )
      .orderBy(desc(futureUs.futurePercent))
      .limit(30);

    // 2단계: 애플리케이션 레벨에서 CASE 로직 처리 + countryCode 추가
    const processedStocks = initialFiltered.map((stock) => ({
      ...stock,
      futureEarnings: null,
      countryCode: 'US',

      // url_1, title1, content1 세트 처리
      url1: stock.content1 ? stock.url1 : null,
      title1: stock.content1 ? stock.title1 : null,
      content1: stock.content1 ? stock.content1 : null,

      // url_2, title2, content2 세트 처리
      url2: stock.url2 && stock.title2 && stock.content2 ? stock.url2 : null,
      title2:
        stock.url2 && stock.title2 && stock.content2 ? stock.title2 : null,
      content2:
        stock.url2 && stock.title2 && stock.content2 ? stock.content2 : null,

      // url_3, title3, content3 세트 처리
      url3: stock.url3 && stock.title3 && stock.content3 ? stock.url3 : null,
      title3:
        stock.url3 && stock.title3 && stock.content3 ? stock.title3 : null,
      content3:
        stock.url3 && stock.title3 && stock.content3 ? stock.content3 : null,

      // url_4, title4, content4 세트 처리
      url4: stock.url4 && stock.title4 && stock.content4 ? stock.url4 : null,
      title4:
        stock.url4 && stock.title4 && stock.content4 ? stock.title4 : null,
      content4:
        stock.url4 && stock.title4 && stock.content4 ? stock.content4 : null,

      // url_5, title5, content5 세트 처리
      url5: stock.url5 && stock.title5 && stock.content5 ? stock.url5 : null,
      title5:
        stock.url5 && stock.title5 && stock.content5 ? stock.title5 : null,
      content5:
        stock.url5 && stock.title5 && stock.content5 ? stock.content5 : null,
    }));

    log.info('US future stocks hybrid query completed', {
      database: {
        table: 'future_us',
        recordCount: processedStocks.length,
        executionTime: timer.duration(),
        queryExecuted: true,
      },
      performance: {
        category:
          timer.elapsed() < 100
            ? 'fast'
            : timer.elapsed() < 500
              ? 'normal'
              : 'slow',
      },
    });

    return processedStocks;
  } catch (error) {
    log.error('US future stocks hybrid query failed', error, {
      table: 'future_us',
      duration: timer.duration(),
    });
    return [];
  }
}

// 🚀 캐싱된 함수들 - 하이브리드 방식 (기존 함수들 - 메타정보 미포함)
const getCachedTodayStocksKRWithCTE = unstable_cache(
  async (): Promise<TodayStockItem[]> => {
    const log = logger.child({
      module: 'stock-data-today-cache-kr-hybrid',
      operation: 'cache_miss_fallback',
    });

    log.info('Next.js cache MISS - executing KR today hybrid query', {
      cache: {
        key: 'today-stocks-kr-hybrid',
        status: 'miss',
        ttl: getCacheTTL(),
        provider: 'nextjs_unstable_cache',
      },
    });

    const stocks = await getTodayStocksWithCTE('KR');

    log.info('Cache fallback completed for KR today hybrid', {
      cache: {
        key: 'today-stocks-kr-hybrid',
        populated: true,
        recordCount: stocks.length,
      },
    });

    return stocks;
  },
  ['today-stocks-kr-hybrid'],
  {
    revalidate: getCacheTTL(),
    tags: ['stocks', 'today-stocks', 'today-kr', 'hybrid'],
  }
);

const getCachedTodayStocksUSWithCTE = unstable_cache(
  async (): Promise<TodayUsStockItem[]> => {
    const log = logger.child({
      module: 'stock-data-today-cache-us-hybrid',
      operation: 'cache_miss_fallback',
    });

    log.info('Next.js cache MISS - executing US today hybrid query', {
      cache: {
        key: 'today-stocks-us-hybrid',
        status: 'miss',
        ttl: getCacheTTL(),
        provider: 'nextjs_unstable_cache',
      },
    });

    const stocks = await getTodayUsStocksWithCTE();

    log.info('Cache fallback completed for US today hybrid', {
      cache: {
        key: 'today-stocks-us-hybrid',
        populated: true,
        recordCount: stocks.length,
      },
    });

    return stocks;
  },
  ['today-stocks-us-hybrid'],
  {
    revalidate: getCacheTTL(),
    tags: ['stocks', 'today-stocks', 'today-us', 'hybrid'],
  }
);

const getCachedFutureStocksKRWithCTE = unstable_cache(
  async (): Promise<FutureStockItem[]> => {
    const log = logger.child({
      module: 'stock-data-future-cache-kr-hybrid',
      operation: 'cache_miss_fallback',
    });

    log.info('Next.js cache MISS - executing KR future hybrid query', {
      cache: {
        key: 'future-stocks-kr-hybrid',
        status: 'miss',
        ttl: getCacheTTL(),
        provider: 'nextjs_unstable_cache',
      },
    });

    const stocks = await getFutureStocksWithCTE('KR');

    log.info('Cache fallback completed for KR future hybrid', {
      cache: {
        key: 'future-stocks-kr-hybrid',
        populated: true,
        recordCount: stocks.length,
      },
    });

    return stocks;
  },
  ['future-stocks-kr-hybrid'],
  {
    revalidate: getCacheTTL(),
    tags: ['stocks', 'future-stocks', 'future-kr', 'hybrid'],
  }
);

const getCachedFutureStocksUSWithCTE = unstable_cache(
  async (): Promise<FutureUsStockItem[]> => {
    const log = logger.child({
      module: 'stock-data-future-cache-us-hybrid',
      operation: 'cache_miss_fallback',
    });

    log.info('Next.js cache MISS - executing US future hybrid query', {
      cache: {
        key: 'future-stocks-us-hybrid',
        status: 'miss',
        ttl: getCacheTTL(),
        provider: 'nextjs_unstable_cache',
      },
    });

    const stocks = await getFutureUsStocksWithCTE();

    log.info('Cache fallback completed for US future hybrid', {
      cache: {
        key: 'future-stocks-us-hybrid',
        populated: true,
        recordCount: stocks.length,
      },
    });

    return stocks;
  },
  ['future-stocks-us-hybrid'],
  {
    revalidate: getCacheTTL(),
    tags: ['stocks', 'future-stocks', 'future-us', 'hybrid'],
  }
);

// 🎯 메인 export 함수들 - 하이브리드 방식 (🆕 메타정보 포함)
export const getCachedTodayStocksWithCTE = async (
  countryCode: string = 'KR'
): Promise<StockDataWithMeta> => {
  const timer = createTimer();
  const log = logger.child({
    module: 'stock-data-today-router-hybrid',
    countryCode,
    operation: 'cache_or_fetch',
  });

  log.info('Today stocks hybrid request started', {
    countryCode,
    requestType: 'today_stocks_hybrid',
    cache: {
      expectedKey: `today-stocks-${countryCode.toLowerCase()}-hybrid`,
      ttl: getCacheTTL(),
    },
  });

  try {
    const cacheCreatedAt = new Date(); // 캐시 생성 시점 기록

    const stocks = await withRetry(async () => {
      return countryCode === 'US'
        ? await getCachedTodayStocksUSWithCTE()
        : await getCachedTodayStocksKRWithCTE();
    });

    const meta = createStockDataMeta(stocks, cacheCreatedAt);

    log.info('Today stocks hybrid request completed', {
      countryCode,
      cache: {
        key: `today-stocks-${countryCode.toLowerCase()}-hybrid`,
        populated: true,
        recordCount: stocks.length,
        ttl: getCacheTTL(),
      },
      performance: {
        duration: timer.duration(),
        category: timer.elapsed() < 500 ? 'fast' : 'slow',
      },
      meta: {
        dataLoadedAt: meta.dataLoadedAt.toISOString(),
        nextUpdateAt: meta.nextUpdateAt.toISOString(),
      },
    });

    return { stocks, meta };
  } catch (error) {
    log.error('Today stocks hybrid request failed', error, {
      countryCode,
      duration: timer.duration(),
    });

    // 에러 시에도 메타정보와 함께 빈 배열 반환
    return {
      stocks: [],
      meta: createStockDataMeta([]),
    };
  }
};

export const getCachedFutureStocksWithCTE = async (
  countryCode: string = 'KR'
): Promise<StockDataWithMeta> => {
  const timer = createTimer();
  const log = logger.child({
    module: 'stock-data-future-router-hybrid',
    countryCode,
    operation: 'cache_or_fetch',
  });

  log.info('Future stocks hybrid request started', {
    countryCode,
    requestType: 'future_stocks_hybrid',
    cache: {
      expectedKey: `future-stocks-${countryCode.toLowerCase()}-hybrid`,
      ttl: getCacheTTL(),
    },
  });

  try {
    const cacheCreatedAt = new Date(); // 캐시 생성 시점 기록

    const stocks = await withRetry(async () => {
      return countryCode === 'US'
        ? await getCachedFutureStocksUSWithCTE()
        : await getCachedFutureStocksKRWithCTE();
    });

    const meta = createStockDataMeta(stocks, cacheCreatedAt);

    log.info('Future stocks hybrid request completed', {
      countryCode,
      cache: {
        key: `future-stocks-${countryCode.toLowerCase()}-hybrid`,
        populated: true,
        recordCount: stocks.length,
        ttl: getCacheTTL(),
      },
      performance: {
        duration: timer.duration(),
        category: timer.elapsed() < 500 ? 'fast' : 'slow',
      },
      meta: {
        dataLoadedAt: meta.dataLoadedAt.toISOString(),
        nextUpdateAt: meta.nextUpdateAt.toISOString(),
      },
    });

    return { stocks, meta };
  } catch (error) {
    log.error('Future stocks hybrid request failed', error, {
      countryCode,
      duration: timer.duration(),
    });

    // 에러 시에도 메타정보와 함께 빈 배열 반환
    return {
      stocks: [],
      meta: createStockDataMeta([]),
    };
  }
};
