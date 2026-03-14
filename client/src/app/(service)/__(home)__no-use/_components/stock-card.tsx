'use client';
import type { StockItem } from '@/lib/server/stock-data';
import { Badge } from '@/components/shared/badge';
import { Icon } from '@/components/icons';
import { Text } from '@/components/shared/text';
import {
  formatPrice,
  formatPercent,
  formatEarnings,
  getBadgeVariant,
  getStockChangeData,
  hasAIInsight,
} from '@/lib/utils/stock-formatters';
import { StockInfoModal } from './stock-info-modal';
import { StockSourcesModal } from './stock-sources-modal';
import { useState } from 'react';
import { Tooltip } from '@/components/shared/tooltip';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/stores'; // ✅ Zustand 스토어 추가

interface StockCardProps {
  stock: StockItem;
  index?: number;
}

export function StockCard({ stock, index = -1 }: StockCardProps) {
  const [showInfoModal, setShowInfoModal] = useState(false);
  const [showSourcesModal, setShowSourcesModal] = useState(false);
  const router = useRouter();

  // ✅ Zustand 스토어에서 모델 설정 함수 가져오기
  const { setSelectedModel } = useAppStore();

  const changeData = getStockChangeData(stock);
  const showAI = hasAIInsight(stock);

  const sources = [];
  for (let i = 1; i <= 5; i++) {
    const url = stock[`url${i}` as keyof typeof stock] as string;
    const title = stock[`title${i}` as keyof typeof stock] as string;
    const content = stock[`content${i}` as keyof typeof stock] as string;

    if (url && title) {
      sources.push({
        id: i,
        url,
        title,
        content: content || '',
      });
    }
  }
  const hasSources = sources.length > 0;

  const isFirstCard = index === 0;

  // ✅ AI 인사이트 클릭 핸들러 - stock-ai 모델 강제 설정 + 채팅 이동
  const handleInsightClick = () => {
    if (!stock.stockName || !stock.tickerSymbol) return;

    console.log('🎯 AI Insight 클릭:', {
      stockName: stock.stockName,
      ticker: stock.tickerSymbol,
      action: 'stock-ai 모델로 강제 설정',
    });

    // 1. ✅ stock-ai 모델로 강제 설정
    setSelectedModel('stock-ai');

    // 2. ✅ 프리셋과 함께 채팅 페이지로 이동
    router.push(
      `/chat/new?preset=${encodeURIComponent(stock.stockName)}&ticker=${encodeURIComponent(stock.tickerSymbol)}`
    );
  };

  return (
    <>
      <div className="w-full min-h-24 p-4 border border-neutral-200 rounded-xl bg-neutral-0 shadow-card flex flex-col gap-1.5 mb-4">
        {/* 헤더 */}
        <Text variant="s2">
          {stock.stockName} ({stock.tickerSymbol})
        </Text>

        <div className="flex flex-col gap-1">
          {/* 현재 가격 */}
          <div className="flex gap-1 items-center">
            <Text variant="b2" as="span" className="text-neutral-900">
              지금 가격은?
            </Text>
            <Text variant="b2" as="span" className="text-neutral-1100">
              {formatPrice(stock.currentPrice, stock.countryCode)}
            </Text>
            <Badge
              variant={getBadgeVariant(
                changeData.current.isPositive,
                changeData.current.isNegative
              )}
            >
              {formatPercent(stock.changePercent)}
            </Badge>
          </div>

          {/* 미래 가격 전망 */}
          {stock.futurePrice && stock.futurePercent && (
            <div className="flex gap-1 items-center">
              <Text variant="b2" as="span" className="text-neutral-900">
                미래가격전망
              </Text>
              <button
                onClick={() => setShowInfoModal(true)}
                aria-label="미래가격전망 안내"
              >
                <Icon.info size={15} />
              </button>
              <Text variant="b2" as="span" className="text-neutral-1100">
                {formatPrice(stock.futurePrice, stock.countryCode)}
              </Text>
              <Badge
                variant={getBadgeVariant(
                  changeData.future.isPositive,
                  changeData.future.isNegative
                )}
              >
                {formatPercent(stock.futurePercent)}
              </Badge>
            </div>
          )}

          {/* 주당 예상 수익 */}
          {stock.futureEarnings && (
            <div className="flex gap-1 items-center">
              <Text variant="b2" as="span" className="text-neutral-900">
                주당예상수익
              </Text>
              <Text
                variant="b2"
                as="span"
                className={`${
                  changeData.earnings.isPositive
                    ? 'text-red-900'
                    : changeData.earnings.isNegative
                      ? 'text-blue-900'
                      : 'text-neutral-1100'
                }`}
              >
                {formatEarnings(stock.futureEarnings, stock.countryCode)}
              </Text>
            </div>
          )}
        </div>

        {/* ✅ AI 인사이트 - 향상된 클릭 핸들러 */}
        {showAI && (
          <div
            className="flex flex-col gap-1.5 cursor-pointer"
            onClick={handleInsightClick}
          >
            <div className="flex gap-1.5 items-center">
              <Icon.rocket.filled size={15} />
              <Text variant="s2">떡상 AI</Text>
            </div>
            {isFirstCard ? (
              <Tooltip
                content="클릭으로 AI 비서 주식 분석을 시작해요"
                storageKey="insight-tooltip-shown"
                position="bottom"
                arrowPosition="left"
                alignment="left"
              >
                <div className="bg-neutral-100 w-full min-h-[76px] py-2 px-3 rounded-xl flex items-center hover:bg-neutral-200 transition-colors">
                  <Text variant="b2" className="text-neutral-700 line-clamp-2">
                    {stock.insight}
                  </Text>
                </div>
              </Tooltip>
            ) : (
              <div className="bg-neutral-100 w-full min-h-[76px] py-2 px-3 rounded-xl flex items-center hover:bg-neutral-200 transition-colors">
                <Text variant="b2" className="text-neutral-700 line-clamp-2">
                  {stock.insight}
                </Text>
              </div>
            )}
          </div>
        )}

        {/* 출처 영역 */}
        {hasSources && (
          <div className="flex items-center gap-2 mt-3.5">
            <button
              onClick={() => setShowSourcesModal(true)}
              aria-label="출처 모음 보기"
            >
              <Badge variant="link">
                <Icon.link size={16} className="text-red-900" />
                <Text variant="b3">출처모음.zip</Text>
              </Badge>
            </button>
          </div>
        )}
      </div>

      <StockInfoModal
        isVisible={showInfoModal}
        onCloseAction={() => setShowInfoModal(false)}
      />
      <StockSourcesModal
        isVisible={showSourcesModal}
        onCloseAction={() => setShowSourcesModal(false)}
        sources={sources}
      />
    </>
  );
}
