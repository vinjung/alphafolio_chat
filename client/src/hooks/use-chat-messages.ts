'use client';

import { useCallback, useReducer, useEffect, useRef } from 'react';
import { useChatSessionStore } from '@/stores';
import type { ChatMessage } from '@/types/chat';
import type { ChatHistoryItem } from '@/lib/server/chat-history';

// 상태 타입 정의
interface ChatMessagesState {
  isProcessing: boolean;
  isLoading: boolean;
  error: string | null;
  hasProcessedFirstMessage: boolean;
}

// 액션 타입 정의
type ChatMessagesAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_PROCESSING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'MARK_FIRST_MESSAGE_PROCESSED' }
  | { type: 'RESET' };

// Reducer
const chatMessagesReducer = (
  state: ChatMessagesState,
  action: ChatMessagesAction
): ChatMessagesState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_PROCESSING':
      return { ...state, isProcessing: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'MARK_FIRST_MESSAGE_PROCESSED':
      return { ...state, hasProcessedFirstMessage: true };
    case 'RESET':
      return {
        isProcessing: false,
        isLoading: false,
        error: null,
        hasProcessedFirstMessage: false,
      };
    default:
      return state;
  }
};

// 초기 상태
const initialState: ChatMessagesState = {
  isProcessing: false,
  isLoading: false,
  error: null,
  hasProcessedFirstMessage: false,
};

interface UseChatMessagesProps {
  chatId: string;
  isNewChat: boolean;
  currentSessionId: string | null;
  onSessionCreate?: (sessionId: string) => void;
  onHistoryUpdate?: (item: ChatHistoryItem) => void;
}

export function useChatMessages({
  chatId,
  isNewChat,
  currentSessionId,
  onSessionCreate,
  onHistoryUpdate,
}: UseChatMessagesProps) {
  const [state, dispatch] = useReducer(chatMessagesReducer, initialState);

  const {
    messages,
    setCurrentSession,
    setMessages,
    addMessage,
    updateLastMessage,
    setLoading: setStoreLoading,
  } = useChatSessionStore();

  const lastSavedMessageRef = useRef<{
    user: string;
    assistant: string;
  } | null>(null);

  // 기존 메시지 로드
  const loadExistingMessages = useCallback(
    async (targetChatId: string) => {
      try {
        dispatch({ type: 'SET_LOADING', payload: true });
        setStoreLoading(true);

        const response = await fetch(`/api/chat/messages/${targetChatId}`);
        if (!response.ok) throw new Error('메시지 로드 실패');

        const result = await response.json();

        let loadedMessages = [];
        if (result.success && result.data?.messages) {
          loadedMessages = result.data.messages;
        } else if (result.messages) {
          loadedMessages = result.messages;
        } else if (Array.isArray(result)) {
          loadedMessages = result;
        }

        setMessages(loadedMessages);
      } catch (_error) {
        dispatch({
          type: 'SET_ERROR',
          payload: '메시지를 불러올 수 없습니다.',
        });
        setMessages([]);
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
        setStoreLoading(false);
      }
    },
    [setMessages, setStoreLoading]
  );

  // 채팅 저장
  const saveChatToDatabase = useCallback(
    async (userMsg: string, assistantMsg: string) => {
      if (!userMsg?.trim() || !assistantMsg?.trim()) {
        return;
      }

      // 중복 저장 방지
      const messageKey = {
        user: userMsg.trim(),
        assistant: assistantMsg.trim(),
      };
      if (
        lastSavedMessageRef.current &&
        lastSavedMessageRef.current.user === messageKey.user &&
        lastSavedMessageRef.current.assistant === messageKey.assistant
      ) {
        return;
      }

      try {
        const requestBody = {
          sessionId: currentSessionId,
          userMessage: userMsg.trim(),
          assistantMessage: assistantMsg.trim(),
          title: !currentSessionId ? userMsg.slice(0, 50) : undefined,
        };

        const response = await fetch('/api/chat/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();

        // 새 세션 생성 처리
        if (result.sessionId && !currentSessionId) {
          setCurrentSession(result.sessionId);
          onSessionCreate?.(result.sessionId);

          // 히스토리 업데이트
          const newHistoryItem: ChatHistoryItem = {
            id: result.sessionId,
            title: userMsg.slice(0, 50),
            lastMessage: assistantMsg.slice(0, 100),
            createdAt: new Date(),
            updatedAt: new Date(),
          };
          onHistoryUpdate?.(newHistoryItem);

          // URL 업데이트
          if (chatId === 'welcome') {
            window.history.replaceState(null, '', `/chat/${result.sessionId}`);
          }
        }

        lastSavedMessageRef.current = messageKey;
      } catch (_error) {
        dispatch({ type: 'SET_ERROR', payload: '메시지 저장에 실패했습니다.' });
      }
    },
    [
      currentSessionId,
      chatId,
      setCurrentSession,
      onSessionCreate,
      onHistoryUpdate,
    ]
  );

  // 스트리밍 응답 처리
  const handleStreamingResponse = useCallback(
    (streamContent: string, isComplete: boolean) => {
      if (!streamContent) return;

      const lastMessage = messages[messages.length - 1];
      if (lastMessage?.role === 'assistant' && lastMessage.isStreaming) {
        updateLastMessage({
          content: streamContent,
          isStreaming: !isComplete,
        });

        // 스트리밍 완료 시 저장
        if (isComplete && streamContent.trim()) {
          const userMessage = messages[messages.length - 2];
          if (userMessage?.role === 'user' && userMessage.content.trim()) {
            saveChatToDatabase(userMessage.content, streamContent);
          }
        }
      }
    },
    [messages, updateLastMessage, saveChatToDatabase]
  );

  // 사용자 메시지 추가
  const addUserMessage = useCallback(
    (content: string) => {
      dispatch({ type: 'SET_PROCESSING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });

      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: content.trim(),
        createdAt: new Date(),
      };

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: '',
        createdAt: new Date(),
        isStreaming: true,
      };

      addMessage(userMessage);
      addMessage(assistantMessage);

      return userMessage;
    },
    [addMessage]
  );

  // 첫 메시지 처리
  const processFirstMessage = useCallback(
    (firstMessage: string) => {
      if (
        !state.hasProcessedFirstMessage &&
        messages.length === 0 &&
        !state.isLoading
      ) {
        dispatch({ type: 'MARK_FIRST_MESSAGE_PROCESSED' });
        return addUserMessage(firstMessage);
      }
      return null;
    },
    [
      state.hasProcessedFirstMessage,
      state.isLoading,
      messages.length,
      addUserMessage,
    ]
  );

  // 초기화 시 메시지 로드
  useEffect(() => {
    if (!isNewChat && chatId && chatId !== 'welcome') {
      setCurrentSession(chatId);
      loadExistingMessages(chatId);
    } else {
      dispatch({ type: 'SET_LOADING', payload: false });
      setStoreLoading(false);
    }
  }, [
    chatId,
    isNewChat,
    loadExistingMessages,
    setCurrentSession,
    setStoreLoading,
  ]);

  return {
    // 상태
    messages,
    isLoading: state.isLoading,
    isProcessing: state.isProcessing,
    error: state.error,

    // 액션
    addUserMessage,
    handleStreamingResponse,
    processFirstMessage,
    saveChatToDatabase,

    // 유틸리티
    clearError: () => dispatch({ type: 'SET_ERROR', payload: null }),
    reset: () => dispatch({ type: 'RESET' }),
  };
}
