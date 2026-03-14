'use client';

import { useEffect, useRef } from 'react';
import { MessageItem } from './message-item';
import { AIMessage } from './ai-message';
import { ChatLimitBadge } from './chat-limit-badge';
import type { ChatMessage } from '@/types/chat';
import type { AIModel } from '../_config/models';

interface MessageListProps {
  messages: ChatMessage[];
  selectedModel: AIModel;
  showWelcome?: boolean;
  userNickname?: string;
  className?: string;
  limitInfo?: {
    remaining: number;
    limit: number;
    canSend: boolean;
  } | null;
  isGuest?: boolean; // ✅ 비회원 상태 추가
}

export function MessageList({
  messages,
  selectedModel,
  showWelcome = false,
  userNickname: _userNickname = '떡상러',
  className,
  limitInfo,
  isGuest = false, // ✅ 기본값 false
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 새 메시지가 추가될 때 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 웰컴 메시지 표시
  if (messages.length === 0 && showWelcome) {
    const welcomeMessage = selectedModel.welcomeMessage;

    return (
      <div
        className={`overflow-y-auto overscroll-none px-5 pt-1.5 pb-6 ${className || ''}`}
      >
        {/* ✅ 회원이고 한도 정보가 있을 때만 배지 표시 */}
        {!isGuest && limitInfo && (
          <div className="sticky top-0 z-10 flex justify-center mb-4">
            <ChatLimitBadge
              remaining={limitInfo.remaining}
              limit={limitInfo.limit}
            />
          </div>
        )}

        <AIMessage
          title={welcomeMessage.title}
          content={welcomeMessage.content}
        />
      </div>
    );
  }

  // 메시지 목록 표시
  return (
    <div
      className={`overflow-y-auto overscroll-none px-5 pt-1.5 pb-4 ${className || ''}`}
    >
      {/* ✅ 회원이고 한도 정보가 있을 때만 배지 표시 */}
      {!isGuest && limitInfo && (
        <div className="sticky top-0 z-10 flex justify-center mb-4">
          <ChatLimitBadge
            remaining={limitInfo.remaining}
            limit={limitInfo.limit}
          />
        </div>
      )}

      <div className="space-y-4 min-h-full">
        {messages.map((message) => (
          <MessageItem key={message.id} message={message} />
        ))}
      </div>
      <div ref={messagesEndRef} />
    </div>
  );
}
