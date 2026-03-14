import { StockItem } from '@/lib/server/stock-data';

export interface ChangeInfo {
  isPositive: boolean;
  isNegative: boolean;
  num: number;
}

/**
 * 숫자 값 파싱 및 변동 방향 계산
 */
export function getChangeInfo(value: string | null): ChangeInfo {
  if (!value) return { isPositive: false, isNegative: false, num: 0 };
  const num = parseFloat(value);
  return {
    isPositive: num > 0,
    isNegative: num < 0,
    num,
  };
}

/**
 * 가격 포맷팅 (국가별 통화 단위 포함)
 */
export function formatPrice(
  price: string | null,
  countryCode?: string | null
): string {
  if (!price) return '-';
  const num = parseFloat(price);
  const formattedNumber = num.toLocaleString('ko-KR');

  switch (countryCode) {
    case 'US':
      return `${formattedNumber} 달러`;
    case 'KR':
    default:
      return `${formattedNumber} 원`;
  }
}

/**
 * 퍼센트 포맷팅 (부호 포함)
 */
export function formatPercent(percent: string | null): string {
  if (!percent) return '-';
  const num = parseFloat(percent);
  const sign = num > 0 ? '+' : '';
  return `${sign}${num.toFixed(2)}%`;
}

/**
 * 수익 포맷팅 (부호 포함, 국가별 통화)
 */
export function formatEarnings(
  earnings: string | null,
  countryCode?: string | null
): string {
  if (!earnings) return '-';
  const num = parseFloat(earnings);
  const sign = num > 0 ? '+' : '-';
  const formattedNumber = Math.abs(num).toLocaleString('ko-KR');

  const currency = countryCode === 'US' ? '달러' : '원';
  return `${sign}${formattedNumber} ${currency}`;
}

/**
 * Badge variant 결정
 */
export function getBadgeVariant(
  isPositive: boolean,
  isNegative: boolean
): 'up' | 'down' | 'default' {
  if (isPositive) return 'up';
  if (isNegative) return 'down';
  return 'default';
}

/**
 * 주식 데이터에서 모든 변동 정보 계산
 */
export function getStockChangeData(stock: StockItem) {
  return {
    current: getChangeInfo(stock.changePercent),
    future: getChangeInfo(stock.futurePercent),
    earnings: getChangeInfo(stock.futureEarnings),
  };
}

/**
 * 주식 AI 인사이트 존재 여부 확인
 */
export function hasAIInsight(stock: StockItem): boolean {
  return !!(stock.insight && stock.insight.trim().length > 0);
}

// ==================== 공유 기능 ====================

interface ShareFormatOptions {
  pageType: 'today' | 'future';
  countryCode?: string;
  maxItems?: number;
}

/**
 * 주식 데이터를 공유용 텍스트로 포맷팅
 */
export function formatStocksForShare(
  stocks: StockItem[],
  options: ShareFormatOptions
): string {
  const { pageType, countryCode = 'KR', maxItems = 5 } = options;

  // 헤더 설정
  const isToday = pageType === 'today';

  const subTitle =
    countryCode === 'US'
      ? `🇺🇸 ${isToday ? '오늘의' : '미래의'} 미국 떡상은?`
      : `🇰🇷 ${isToday ? '오늘의' : '미래의'} 한국 떡상은?`;

  // 통화 단위
  const currency = countryCode === 'US' ? '달러' : '원';

  const selectedStocks = stocks.slice(0, maxItems);

  const stockList = selectedStocks
    .map((stock, index) => {
      const rank = index + 1;

      // 가격 포맷팅
      const currentPrice = stock.currentPrice
        ? parseFloat(stock.currentPrice).toLocaleString()
        : '0';
      const changePercent = stock.changePercent
        ? parseFloat(stock.changePercent)
        : 0;
      const changeSign = changePercent >= 0 ? '+' : '';

      const futurePrice = stock.futurePrice
        ? parseFloat(stock.futurePrice).toLocaleString()
        : '0';
      const futurePercent = stock.futurePercent
        ? parseFloat(stock.futurePercent)
        : 0;
      const futureSign = futurePercent >= 0 ? '+' : '';

      const aiInsight = stock.insight || '';

      // ✅ 티커 포함한 주식명 포맷: [주식명 (티커)]
      return `${rank}위: [${stock.stockName} (${stock.tickerSymbol})]
- 지금가격은: ${currentPrice}${currency} ${changeSign}${changePercent.toFixed(2)}%
- 미래가격전망: ${futurePrice}${currency} ${futureSign}${futurePercent.toFixed(2)}%
- 떡상 AI: ${aiInsight}`;
    })
    .join('\n\n');

  // 푸터
  const footer = `사이트를 방문하시고 더 많은 정보를 확인하세요!`;

  return `${subTitle}\n\n${stockList}\n\n${footer}`;
}

/**
 * 오늘의 떡상 공유용 포맷팅
 */
export function formatTodayStocksForShare(
  stocks: StockItem[],
  countryCode: string = 'KR'
): string {
  return formatStocksForShare(stocks, {
    pageType: 'today',
    countryCode,
  });
}

/**
 * 미래의 떡상 공유용 포맷팅
 */
export function formatFutureStocksForShare(
  stocks: StockItem[],
  countryCode: string = 'KR'
): string {
  return formatStocksForShare(stocks, {
    pageType: 'future',
    countryCode,
  });
}
