'use client';

import { useState } from 'react';
import { Icon } from '@/components/icons';
import { ModelSelector } from './model-selector';
import { ChatHistoryModal } from './chat-history-modal';
import { useRouter } from 'next/navigation';
import type { AIModel } from '../_config/models';
import type { ChatHistoryItem } from '@/lib/server/chat-history';
import { Text } from '@/components/shared/text';

interface ChatHeaderProps {
  showNewChatButton?: boolean;
  selectedModel?: AIModel;
  availableModels?: AIModel[];
  onModelChange?: (model: AIModel) => void;
  showModelSelector?: boolean;
  preloadedChatHistory?: ChatHistoryItem[];
  isWelcomeMode?: boolean;
  onNewChat?: () => void;
  isStreaming?: boolean;
  hasMessages?: boolean;
}

export function ChatHeader({
  showNewChatButton = false,
  selectedModel,
  availableModels = [],
  onModelChange,
  showModelSelector = false,
  preloadedChatHistory = [],
  isWelcomeMode = false,
  onNewChat,
  isStreaming = false,
  hasMessages = false,
}: ChatHeaderProps) {
  const router = useRouter();
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);

  const handleNewChat = () => {
    // ✅ 스트리밍 중일 때는 새 채팅 방지
    if (isStreaming) {
      console.log('🚫 스트리밍 중 - 새 채팅 차단');
      return;
    }

    if (onNewChat) {
      onNewChat();
    } else if (isWelcomeMode) {
      window.location.reload();
    } else {
      // ✅ 유일한 수정: 일관된 새 채팅 URL
      router.push('/chat');
    }
  };

  const handleHistoryClick = () => {
    setIsHistoryModalOpen(true);
  };

  const handleHistoryModalClose = () => {
    setIsHistoryModalOpen(false);
  };

  // ✅ 상태별 스타일 계산
  const getNewChatButtonStyle = () => {
    if (!showNewChatButton) return 'text-neutral-700';

    if (isStreaming) {
      // 스트리밍 중: 비활성화 스타일
      return 'text-neutral-400 cursor-not-allowed';
    } else if (hasMessages) {
      // ✅ 수정: AI 응답이 있을 때만 강조 스타일
      return 'text-neutral-1100 cursor-pointer transition-colors';
    } else {
      // ✅ 새로 추가: 메시지가 없을 때는 기본 스타일
      return 'text-neutral-400 cursor-pointer';
    }
  };

  return (
    <>
      <header className="relative flex items-center w-full h-14 px-5 py-4 bg-neutral-0 ">
        {/* 왼쪽: 히스토리 버튼 - 절대좌표 */}
        <button
          onClick={handleHistoryClick}
          className="absolute left-5 flex items-center gap-2 py-1 px-1 -ml-1 rounded-lg hover:bg-neutral-50 transition-colors"
          aria-label="채팅 목록"
        >
          <Icon.arrowRight className="rotate-180 text-neutral-800" size={20} />
          <Text variant="s3" className="-ml-2 text-neutral-800">
            채팅목록
          </Text>
        </button>

        {/* 중앙: 모델 선택기 또는 로고 - flex 중앙정렬 */}
        <div className="flex justify-center items-center w-full">
          {showModelSelector && selectedModel && onModelChange && (
            <ModelSelector
              selectedModel={selectedModel}
              availableModels={availableModels}
              onModelChangeAction={onModelChange}
            />
          )}
        </div>

        {/* 오른쪽: 새 채팅 버튼 - 절대좌표 */}
        <div className="absolute right-5">
          {showNewChatButton ? (
            <Icon.newChat
              size={24}
              className={getNewChatButtonStyle()}
              onClick={handleNewChat}
            />
          ) : (
            <Icon.newChat size={24} className={getNewChatButtonStyle()} />
          )}
        </div>
      </header>

      {/* 채팅 히스토리 모달 */}
      <ChatHistoryModal
        isOpen={isHistoryModalOpen}
        onCloseAction={handleHistoryModalClose}
        preloadedHistory={preloadedChatHistory}
      />
    </>
  );
}
