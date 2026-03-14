'use client';

import { Text } from '@/components/shared/text';
import { AIMessage } from './ai-message';
import type { ChatMessage } from '@/types/chat';

interface MessageItemProps {
  message: ChatMessage;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';

  if (isUser) {
    // 유저 메시지: 회색 말풍선, 오른쪽 정렬
    return (
      <div className="flex justify-end">
        <div className="flex flex-col items-end max-w-[80%]">
          <div className="px-4 py-3 rounded-2xl bg-neutral-200 text-neutral-900">
            <Text variant="b2" className="text-neutral-900">
              {message.content}
            </Text>
          </div>
        </div>
      </div>
    );
  }

  // AI 메시지: 통합 컴포넌트 사용 (스트리밍 상태 전달)
  return (
    <AIMessage
      content={message.content}
      showTimestamp={true}
      isStreaming={message.isStreaming}
      visualization={message.visualization}
    />
  );
}
