'use client';

import { useState } from 'react';
import { Text } from '@/components/shared/text';
import { FormattedText } from './formatted-text';
import { LoadingDots } from '@/components/shared/loading-dots';
import { Icon } from '@/components/icons';
import { showGlobalSnackbar } from '@/components/shared/snackbar';
import { ChartRenderer } from './visualization';
import Image from 'next/image';
import type { VisualizationData } from '@/types/chart';

interface AIMessageProps {
  title?: string; // 웰컴메시지용 타이틀
  content: string; // 메시지 내용 (마크다운 지원)
  showTimestamp?: boolean;
  isStreaming?: boolean; // 스트리밍 상태 추가
  visualization?: VisualizationData; // 차트 시각화 데이터
}

export function AIMessage({
  title,
  content,
  isStreaming = false,
  visualization,
}: AIMessageProps) {
  const [imageError, setImageError] = useState(false);
  const [isCopying, setIsCopying] = useState(false);

  // 스트리밍 중이면서 내용이 비어있을 때 로딩 표시
  const showLoading = isStreaming && !content.trim();

  // 복사 가능한 상태 (내용이 있고 스트리밍 중이 아님)
  const canCopy = !showLoading && content.trim().length > 0;

  // 복사 버튼 클릭 핸들러
  const handleCopy = async () => {
    if (!canCopy || isCopying) return;

    setIsCopying(true);

    try {
      await navigator.clipboard.writeText(content.trim());
      showGlobalSnackbar('복사 완료됐상', { position: 'top' });
    } catch (error) {
      console.error('메시지 복사 실패:', error);
      showGlobalSnackbar('복사에 실패했습니다.', {
        variant: 'error',
        position: 'top',
      });
    } finally {
      setIsCopying(false);
    }
  };

  return (
    <div className="flex justify-start">
      <div className="flex flex-row gap-2 max-w-full">
        {/* AI 아바타 */}
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center overflow-hidden">
            {!imageError ? (
              <Image
                src="/images/brand-avatar.webp"
                alt="떡상 AI"
                width={18}
                height={14}
                className="w-[18px] h-[14px] object-contain"
                onError={() => setImageError(true)}
              />
            ) : (
              <Text variant="s1" className="text-white font-medium">
                떡
              </Text>
            )}
          </div>
        </div>

        {/* 이름 + 메시지 내용 */}
        <div className="flex flex-col items-start flex-1 min-w-0">
          {/* AI 이름 */}
          <Text variant="s1" className="text-red-900">
            떡상
          </Text>

          {/* 타이틀 (웰컴메시지용) */}
          {title && (
            <FormattedText className="text-neutral-900 text-sm font-medium mb-2">
              {title}
            </FormattedText>
          )}

          {/* 로딩 또는 메시지 내용 */}
          <div className="text-neutral-900 max-w-full">
            {showLoading ? (
              <div className="flex items-center gap-2 py-2">
                <LoadingDots />
              </div>
            ) : (
              <FormattedText className="text-neutral-900 text-sm leading-relaxed">
                {content}
              </FormattedText>
            )}
          </div>

          {/* 차트 시각화 */}
          {visualization && !showLoading && (
            <div className="mt-3 w-full">
              <ChartRenderer visualization={visualization} />
            </div>
          )}

          {/* 복사 버튼 - 메시지 하단에 위치 */}
          {canCopy && (
            <div className="flex justify-end mt-2">
              <button
                onClick={handleCopy}
                disabled={isCopying}
                className={` active:bg-neutral-100 rounded-md p-1.5
                  ${isCopying ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}
                `}
                aria-label="메시지 복사"
              >
                <Icon.copy.default
                  className={`w-4.5 h-4.5 text-neutral-600 ${isCopying ? 'animate-pulse' : ''}`}
                />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
