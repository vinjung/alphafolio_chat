'use client';

import React from 'react';
import { Modal } from '@/components/shared/modal';
import { Icon } from '@/components/icons';
import { Text } from '@/components/shared/text';

interface StockSource {
  id: number;
  url: string;
  title: string;
  content: string;
}

interface StockSourcesModalProps {
  isVisible: boolean;
  onCloseAction: () => void;
  sources: StockSource[];
}

export function StockSourcesModal({
  isVisible,
  onCloseAction,
  sources,
}: StockSourcesModalProps) {
  return (
    <Modal
      isVisible={isVisible}
      onCloseAction={onCloseAction}
      title="출처모음.zip"
      variant="fullscreen"
      disableAnimation
    >
      <div className="p-5 space-y-1">
        {sources.length > 0 ? (
          sources.map((source) => (
            <div
              key={source.id}
              className="border-b border-neutral-200 bg-neutral-0 flex-col flex gap-1.5 py-1.5"
            >
              {/* 번호와 제목 */}
              <div className="flex items-center gap-3">
                <Text
                  variant="b3"
                  as="span"
                  className="min-w-4.5 min-h-4.5 text-center bg-neutral-200 rounded-full"
                >
                  {source.id}
                </Text>
                <Text variant="s1" className="truncate">
                  {source.title}
                </Text>
              </div>

              {/* 내용 미리보기 */}
              {source.content && (
                <Text variant="b2" className="leading-relaxed">
                  {source.content}
                </Text>
              )}

              {/* 출처보기 링크 */}
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 hover:underline"
              >
                <Icon.link size={14} className="text-red-900" />
                <Text variant="b3" as="span" className="underline text-red-900">
                  출처보기
                </Text>
              </a>
            </div>
          ))
        ) : (
          <div className="flex flex-col items-center justify-center h-32 text-neutral-500">
            <Text variant="b1">출처 정보가 없습니다</Text>
          </div>
        )}
      </div>
    </Modal>
  );
}
