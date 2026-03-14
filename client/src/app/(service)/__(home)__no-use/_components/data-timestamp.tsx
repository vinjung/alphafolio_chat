'use client';

import { Text } from '@/components/shared/text';
import { StockDataMeta } from '@/lib/server/stock-data';

interface DataTimestampProps {
  meta: StockDataMeta;
  className?: string;
}

export function DataTimestamp({ meta, className = '' }: DataTimestampProps) {
  // 한국 시간으로 포맷팅
  const formatKoreanTime = (date: Date) => {
    const formatter = new Intl.DateTimeFormat('ko-KR', {
      timeZone: 'Asia/Seoul',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });

    const parts = formatter.formatToParts(date);
    const month = parts.find((part) => part.type === 'month')?.value || '';
    const day = parts.find((part) => part.type === 'day')?.value || '';
    const hour = parts.find((part) => part.type === 'hour')?.value || '';
    const minute = parts.find((part) => part.type === 'minute')?.value || '';

    return `${month}.${day} ${hour}:${minute}`;
  };

  // ✅ 간단하게 수정: 실제 데이터 업데이트 시점을 우선 사용
  const getTimeText = () => {
    if (meta.recordUpdatedAt) {
      return formatKoreanTime(meta.recordUpdatedAt);
    }
    return '데이터 없음';
  };

  const timeText = getTimeText();
  const hasData = meta.recordUpdatedAt !== undefined;

  return (
    <div className={`flex gap-2 ${className}`}>
      <Text
        variant="b3"
        className={hasData ? 'text-neutral-800' : 'text-neutral-400'}
      >
        {timeText}
        {hasData && ' 기준'}
      </Text>
    </div>
  );
}
