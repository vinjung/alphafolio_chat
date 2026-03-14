import { Text } from '@/components/shared/text';
import { StockCard } from './stock-card';
import type { StockItem } from '@/lib/server/stock-data';

interface StocksListProps {
  stocks: StockItem[];
  countryCode: string;
  pageType: 'today' | 'future';
}

export function StocksList({ stocks, countryCode, pageType }: StocksListProps) {
  if (stocks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-neutral-500">
        <Text className="text-4xl mb-4">
          {pageType === 'today' ? '🚀' : '🔮'}
        </Text>
        <div className="text-center">
          <Text variant="s1" className="text-neutral-700 mb-2">
            {countryCode === 'US' ? '미국' : '한국'}{' '}
            {pageType === 'today' ? '' : '미래 '}데이터를 준비중이에요
          </Text>
          <Text variant="b2" className="text-neutral-700">
            곧 최신 {pageType === 'today' ? '떡상' : '예측'} 정보를
            제공해드릴게요!
          </Text>
        </div>
      </div>
    );
  }

  return (
    <>
      {stocks.map((stock, index) => (
        <StockCard key={stock.tickerSymbol} stock={stock} index={index} />
      ))}
    </>
  );
}
