'use client';

import { Icon } from '@/components/icons';
import {
  formatTodayStocksForShare,
  formatFutureStocksForShare,
} from '@/lib/utils/stock-formatters';
import type { StockItem } from '@/lib/server/stock-data';
import { useWebShare } from '@/hooks/use-share';
import { showGlobalSnackbar } from '@/components/shared/snackbar';
import { Tooltip } from '@/components/shared/tooltip';

interface ShareButtonProps {
  stocks: StockItem[];
  pageType: 'today' | 'future';
  countryCode?: string;
}

// 🆕 공유 로깅 API 호출 함수
async function logShareActivity(
  pageType: 'today' | 'future',
  countryCode: string
): Promise<void> {
  try {
    const response = await fetch('/api/share/log', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pageType,
        countryCode,
      }),
    });

    if (!response.ok) {
      throw new Error(`로깅 실패: ${response.status}`);
    }

    const result = await response.json();
    console.log('📊 공유 로깅 성공:', {
      logId: result.data?.logId,
      dailyCount: result.data?.dailyCount,
      totalCount: result.data?.totalCount,
    });
  } catch (error) {
    // 로깅 실패는 사용자 경험에 영향주지 않도록 조용히 처리
    console.warn('📊 공유 로깅 실패 (기능에는 영향 없음):', error);
  }
}

export function ShareButton({
  stocks,
  pageType,
  countryCode = 'KR',
}: ShareButtonProps) {
  const { share, isSharing } = useWebShare();

  // 공유 가능한 상태인지 확인
  const hasShareableContent = stocks.length > 0;
  const isDisabled = isSharing || !hasShareableContent;

  const handleShare = async () => {
    if (!hasShareableContent) {
      showGlobalSnackbar('공유할 데이터가 없습니다', { position: 'top' });
      return;
    }

    const shareText =
      pageType === 'today'
        ? formatTodayStocksForShare(stocks, countryCode)
        : formatFutureStocksForShare(stocks, countryCode);

    const isToday = pageType === 'today';
    const title = isToday
      ? '🔥 [실시간 오늘의 떡상 대장주 TOP5] 🔥'
      : '🔥 [실시간 미래의 떡상 대장주 TOP5] 🔥';

    try {
      // 🎯 공유 실행
      await share({
        title,
        text: shareText,
      });

      // ✅ 공유 성공 시에만 로깅 API 호출
      await logShareActivity(pageType, countryCode);

      console.log('🎉 공유 완료 및 로깅 성공');
    } catch (error) {
      // 공유 실패 시에는 로깅하지 않음
      console.warn('🚫 공유 실패:', error);

      // 사용자가 공유를 취소한 경우가 아니라면 에러 표시
      if (error instanceof Error && error.name !== 'AbortError') {
        showGlobalSnackbar('공유에 실패했습니다.', { position: 'top' });
      }
    }
  };

  const getAriaLabel = () => {
    const pageLabel = pageType === 'today' ? '오늘의' : '미래의';

    if (isSharing) {
      return `${pageLabel} 떡상 정보 공유 중...`;
    }

    if (!hasShareableContent) {
      return `${pageLabel} 떡상 정보가 없어 공유할 수 없습니다`;
    }

    return `${pageLabel} 떡상 정보 공유하기`;
  };

  return (
    <Tooltip
      content="떡상 리스트 친구에게 공유해 보세요!"
      storageKey="share-tooltip-shown"
      position="bottom"
      arrowPosition="right"
      alignment="right"
    >
      <button
        onClick={handleShare}
        disabled={isDisabled}
        className={`w-10 h-10 ml-auto transition-opacity ${
          isDisabled
            ? 'opacity-30 cursor-not-allowed'
            : 'opacity-100 hover:opacity-70'
        }`}
        aria-label={getAriaLabel()}
      >
        <Icon.share className="m-auto" />
      </button>
    </Tooltip>
  );
}
