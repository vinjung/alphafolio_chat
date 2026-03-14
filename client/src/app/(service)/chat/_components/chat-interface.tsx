'use client';

import { useEffect, useCallback, useMemo } from 'react';
import { ChatHeader } from './chat-header';
import { MessageList } from './message-list';
import { MessageInput } from './message-input';
import { ChatGuideMessage } from './chat-guide-message';
import { MessageAreaSkeleton } from './chat-skeleton';
import { useChatStream } from '@/hooks/use-chat-stream';
import { useChatSave } from '@/hooks/use-chat-save';
import { useChatLimit } from '@/hooks/use-chat-limit';
import { useChatModel } from '@/hooks/use-chat-model';
import { useChatSession } from '@/hooks/use-chat-session'; // ✅ 추가
import { useChatStatus } from '@/hooks/use-chat-status';
import { useStreamingStore, useChatSessionStore, useAppStore } from '@/stores';
import type { ChatMessage } from '@/types/chat';
import type { ChatHistoryItem } from '@/lib/server/chat-history';

// ✅ 상수 분리
const CONSTANTS = {
  MESSAGES: {
    NEW_CHAT_LOG: '🆕 새 채팅 - 로드 건너뜀',
    EXISTING_CHAT_LOG: '📂 기존 채팅 로드 시작:',
    WELCOME_RESET_LOG: '🆕 웰컴 모드 - 세션 리셋',
    CHAT_LIMIT_WARNING: '채팅 한도 초과',
    LOADING_MESSAGES_LOG: '📨 로드된 메시지:',
    API_CALL_LOG: '📡 API 호출:',
    API_RESPONSE_LOG: '📡 API 응답:',
    NEW_CHAT_NO_MESSAGES_LOG: '📂 새 채팅 - 메시지 없음',
    MESSAGE_LOAD_FAILED: '기존 메시지 로드 실패:',
  },
  PATHS: {
    STOCKS_PATH: '/today',
    WELCOME_PATH: 'welcome',
  },
  STYLES: {
    MAIN_CONTAINER: 'flex flex-col bg-neutral-0',
    FLEX_ONE: 'flex-1',
  },
  PARAMS: {
    NEW_CHAT_PARAM: 'new=true',
    CHAT_PREFIX: 'chat_',
    MIN_CHAT_ID_PARTS: 4,
  },
} as const;

interface ChatInterfaceProps {
  chatId: string;
  firstMessage?: string;
  isWelcomeMode?: boolean;
  userNickname: string;
  preloadedChatHistory?: ChatHistoryItem[];
}

export function ChatInterface({
  chatId,
  firstMessage,
  isWelcomeMode = false,
  userNickname,
  preloadedChatHistory = [],
}: ChatInterfaceProps) {
  // ✅ 리팩토링된 모델 훅 사용 (firstMessage 제거)
  const { selectedModel, availableModels, presetMessage, handleModelChange } =
    useChatModel({
      userNickname, // firstMessage 파라미터 제거됨
    });

  // ✅ 리팩토링된 세션 훅 사용 (모델 동기화 포함)
  const { chatHistory, setChatHistory, isLoadingMessages, addToChatHistory } =
    useChatSession({
      chatId,
      isWelcomeMode,
      preloadedChatHistory,
    });

  // 세션 상태 스토어
  const {
    currentSessionId,
    messages,
    hasProcessedFirstMessage,
    lastFailedMessage,
    isRetrying,
    isStreamInterrupted,
    addMessage,
    updateLastMessage,
    setHasProcessedFirstMessage,
    setFailedMessage,
    setRetrying,
    setStreamInterrupted,
    resetSession,
    clearErrors,
  } = useChatSessionStore();

  // 스트리밍 스토어
  const setGlobalStreaming = useStreamingStore((state) => state.setIsStreaming);
  const resetStreamingState = useStreamingStore(
    (state) => state.resetStreamingState
  );

  // 채팅 한도 관리
  const {
    limitInfo,
    isLoading: isLimitLoading,
    isGuest,
    decrementRemaining,
  } = useChatLimit();

  // 채팅 스트림 훅
  const {
    response: streamResponse,
    isStreaming,
    error: streamError,
    visualization: streamVisualization,
    sendMessage,
    disconnect,
  } = useChatStream();

  // 채팅 저장 훅
  const { saveError, handleStreamingComplete, clearSaveError } = useChatSave({
    chatId,
    onNewSessionCreated: addToChatHistory,
  });

  // 상태 관리 훅
  const chatStatus = useChatStatus({
    limitInfo,
    isLimitLoading,
    isGuest,
    lastFailedMessage,
    isRetrying,
    isStreamInterrupted,
    isStreaming,
    messagesError: null,
    streamError,
    saveError,
    isLoadingMessages,
    isProcessing: false,
  });

  const { placeholder, isInputDisabled } = chatStatus;

  // ✅ 성능 최적화: 계산된 값들 메모화
  const hasAssistantMessages = useMemo(
    () => messages.some((msg) => msg.role === 'assistant'),
    [messages]
  );

  const showWelcomeScreen = useMemo(
    () => isWelcomeMode || messages.length === 0,
    [isWelcomeMode, messages.length]
  );

  // ✅ 초기 채팅 히스토리 설정 (한 번만)
  useEffect(() => {
    if (preloadedChatHistory.length > 0 && chatHistory.length === 0) {
      setChatHistory(preloadedChatHistory);
    }
  }, [preloadedChatHistory, chatHistory.length, setChatHistory]);

  // 스트리밍 상태 동기화
  useEffect(() => {
    setGlobalStreaming(isStreaming, currentSessionId || undefined);
  }, [isStreaming, currentSessionId, setGlobalStreaming]);

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      resetStreamingState();
      // 페이지 이동 시 프리셋 메시지 클리어
      if (presetMessage) {
        const { clearPresetMessage } = useAppStore.getState();
        clearPresetMessage();
      }
    };
  }, [resetStreamingState, presetMessage]);

  // 스트리밍 응답 처리
  useEffect(() => {
    if (streamResponse && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (
        lastMessage.role === 'assistant' &&
        lastMessage.isStreaming
      ) {
        const updates: Partial<import('@/types/chat').ChatMessage> = {
          content: streamResponse,
          isStreaming: isStreaming,
        };
        // Attach visualization when streaming completes
        if (!isStreaming && streamVisualization) {
          updates.visualization = streamVisualization;
        }
        updateLastMessage(updates);
      }
    }
  }, [streamResponse, isStreaming, streamVisualization, updateLastMessage, messages]);

  // Visualization attachment - separate from content streaming
  useEffect(() => {
    if (!isStreaming && streamVisualization && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role === 'assistant' && !lastMessage.visualization) {
        updateLastMessage({ visualization: streamVisualization });
      }
    }
  }, [isStreaming, streamVisualization, messages, updateLastMessage]);

  useEffect(() => {
    // 🚨 핵심 수정: 에러가 없을 때만 완료로 처리
    if (!isStreaming && !streamError && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (
        lastMessage?.role === 'assistant' &&
        lastMessage.isStreaming &&
        lastMessage.content.trim()
      ) {
        // 스트리밍 완료 즉시 프리셋 메시지와 URL 파라미터 클리어
        if (presetMessage) {
          // 1. 프리셋 메시지 상태 클리어
          const { clearPresetMessage } = useAppStore.getState();
          clearPresetMessage();

          // 2. URL 파라미터 제거
          const currentPath = window.location.pathname;
          window.history.replaceState(null, '', currentPath);

          // 3. 프리셋 플래그 초기화
          const { resetPresetFlags } = useAppStore.getState();
          resetPresetFlags();
        }

        // 기존 로직: 응답 완료 시점에 한도 차감
        if (!isGuest) {
          decrementRemaining();
        }

        // 🚨 수정: 저장을 약간 지연시켜 렌더링 완료 후 저장
        handleStreamingComplete(messages);
      }
    } else if (streamError) {

      // 스트리밍 상태만 업데이트 (저장하지 않음)
      const lastMessage = messages[messages.length - 1];
      if (lastMessage?.role === 'assistant' && lastMessage.isStreaming) {
        updateLastMessage({ isStreaming: false });
      }
    }
  }, [
    isStreaming,
    streamError,
    messages,
    presetMessage, // 🚨 추가된 의존성
    handleStreamingComplete,
    isGuest,
    decrementRemaining,
    updateLastMessage,
  ]);

  // 웰컴 모드 세션 리셋
  useEffect(() => {
    if (isWelcomeMode) {
      resetSession();
      // 웰컴 모드에서 프리셋 메시지 클리어
      if (presetMessage) {
        const { clearPresetMessage } = useAppStore.getState();
        clearPresetMessage();
      }
    }
  }, [isWelcomeMode, resetSession, presetMessage]);

  // 첫 메시지 처리
  useEffect(() => {
    if (firstMessage && !hasProcessedFirstMessage && selectedModel) {
      setHasProcessedFirstMessage(true);
      handleSendMessage(firstMessage);
    }
  }, [
    firstMessage,
    hasProcessedFirstMessage,
    selectedModel,
    setHasProcessedFirstMessage,
  ]);

  // ✅ 유틸리티 함수: 메시지 생성
  const createUserMessage = useCallback((content: string): ChatMessage => {
    return {
      id: `user_${Date.now()}`,
      role: 'user',
      content: content.trim(),
      createdAt: new Date(),
    };
  }, []);

  const createAssistantMessage = useCallback((): ChatMessage => {
    return {
      id: `assistant_${Date.now()}`,
      role: 'assistant',
      content: '',
      createdAt: new Date(),
      isStreaming: true,
    };
  }, []);

  // ✅ 유틸리티 함수: 전송 가능 여부 확인
  const canSendMessage = useCallback(
    (content: string): boolean => {
      if (!selectedModel || isStreaming || !content.trim()) {
        return false;
      }
      if (limitInfo && !isGuest && limitInfo.remaining <= 0) {
        return false;
      }
      return true;
    },
    [selectedModel, isStreaming, limitInfo, isGuest]
  );

  // 메시지 전송 핸들러
  const handleSendMessage = useCallback(
    async (content: string, clearInput?: () => void) => {
      // 항상 프리셋 메시지 클리어 (재적용 방지)
      if (presetMessage) {
        const { clearPresetMessage } = useAppStore.getState();
        clearPresetMessage();
      }

      if (!canSendMessage(content)) {
        return;
      }

      clearErrors();

      const userMessage = createUserMessage(content);
      const assistantMessage = createAssistantMessage();

      addMessage(userMessage);
      addMessage(assistantMessage);

      // 메시지 추가 직후 바로 입력창 클리어
      clearInput?.();

      // 한도 차감은 응답 완료 시점으로 이동

      try {
        if (selectedModel) {
          await sendMessage(content.trim(), selectedModel.apiConfig);
        }
      } catch (_error) {
        setFailedMessage(content.trim());
      }
    },
    [
      presetMessage,
      canSendMessage,
      clearErrors,
      createUserMessage,
      createAssistantMessage,
      addMessage,
      sendMessage,
      setFailedMessage,
      selectedModel,
    ]
  );

  // 기타 핸들러들
  const handleStopStreaming = useCallback(() => {
    disconnect();
    setStreamInterrupted(true);
  }, [disconnect, setStreamInterrupted]);

  // ✅ 성능 최적화: 의존성 최적화
  const handleRetry = useCallback(() => {
    if (lastFailedMessage) {
      setRetrying(true);
      handleSendMessage(lastFailedMessage); // No clearInput callback for retry
      setFailedMessage(null);
      setRetrying(false);
    }
  }, [lastFailedMessage, handleSendMessage, setRetrying, setFailedMessage]);

  // ✅ 성능 최적화: 의존성 최적화
  const handleNewChat = useCallback(() => {
    if (isWelcomeMode) {
      resetSession();
      if (isStreaming) {
        disconnect();
      }
      // 새 채팅 시작 시 프리셋 메시지 클리어
      if (presetMessage) {
        const { clearPresetMessage } = useAppStore.getState();
        clearPresetMessage();
      }
    }
  }, [isWelcomeMode, resetSession, isStreaming, disconnect, presetMessage]);

  // ✅ 성능 최적화: 의존성이 없는 간단한 함수는 useCallback 불필요
  // ✅ 중복 제거: 상수 사용
  const handleNavigateToStocks = () => {
    window.location.href = CONSTANTS.PATHS.STOCKS_PATH;
  };

  // ✅ 성능 최적화: 입력 비활성화 조건 메모화
  const inputProps = useMemo(
    () => ({
      onSendMessageAction: handleSendMessage,
      isStreaming,
      onStopStreaming: handleStopStreaming,
      disabled: isInputDisabled,
      placeholder,
      presetMessage,
    }),
    [
      handleSendMessage,
      isStreaming,
      handleStopStreaming,
      isInputDisabled,
      placeholder,
      presetMessage,
    ]
  );

  // ✅ 성능 최적화: 프리셋 클리어 함수 메모화
  const handlePresetUsed = useCallback(() => {
    const { clearPresetMessage } = useAppStore.getState();
    clearPresetMessage();
  }, []);

  return (
    <div
      className={CONSTANTS.STYLES.MAIN_CONTAINER}
      style={{ height: 'calc(100% - 6rem)' }}
    >
      <ChatHeader
        // ✅ 수정: 항상 새채팅 버튼 표시 (웰컴모드와 관계없이)
        showNewChatButton={true}
        selectedModel={selectedModel || undefined}
        availableModels={availableModels}
        onModelChange={handleModelChange}
        showModelSelector={true}
        preloadedChatHistory={chatHistory}
        isWelcomeMode={isWelcomeMode}
        onNewChat={isWelcomeMode ? handleNewChat : undefined}
        hasMessages={hasAssistantMessages}
        isStreaming={isStreaming}
      />

      {selectedModel ? (
        isLoadingMessages ? (
          <MessageAreaSkeleton />
        ) : (
          <MessageList
            messages={messages}
            selectedModel={selectedModel}
            showWelcome={showWelcomeScreen}
            userNickname={userNickname}
            className={CONSTANTS.STYLES.FLEX_ONE}
            limitInfo={limitInfo}
            isGuest={isGuest}
          />
        )
      ) : (
        <MessageAreaSkeleton />
      )}

      {/* ✅ 단일 가이드 메시지 (우선순위 기반) */}
      {chatStatus.currentGuideMessage && (
        <ChatGuideMessage
          type={chatStatus.currentGuideMessage.type}
          guideMessageConfig={chatStatus.currentGuideMessage}
          onNavigateToStocks={
            chatStatus.currentGuideMessage.type === 'limit-reached'
              ? handleNavigateToStocks
              : undefined
          }
          onRetry={
            chatStatus.currentGuideMessage.type === 'request-failed'
              ? saveError
                ? clearSaveError
                : handleRetry
              : chatStatus.currentGuideMessage.type === 'stream-interrupted'
                ? () => {
                    setStreamInterrupted(false);
                    const lastUserMessage = messages
                      .slice()
                      .reverse()
                      .find((msg) => msg.role === 'user');
                    if (lastUserMessage) {
                      handleSendMessage(lastUserMessage.content);
                    }
                  }
                : undefined
          }
        />
      )}

      <MessageInput {...inputProps} onPresetUsed={handlePresetUsed} />
    </div>
  );
}
