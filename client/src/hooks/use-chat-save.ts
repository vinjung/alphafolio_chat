'use client';

import { useState, useCallback, useRef } from 'react';
import { useChatSessionStore, useAppStore } from '@/stores';
import type { ChatHistoryItem } from '@/lib/server/chat-history';
import type { ChatMessage } from '@/types/chat';

interface UseChatSaveProps {
  chatId: string;
  // 🚨 추가: 새 세션 생성 시 히스토리 업데이트 콜백
  onNewSessionCreated?: (item: ChatHistoryItem) => void;
}

interface UseChatSaveResult {
  // 상태
  isSaving: boolean;
  saveError: string | null;

  // 함수
  saveChatToDatabase: (userMsg: string, assistantMsg: string) => Promise<void>;
  handleStreamingComplete: (messages: ChatMessage[]) => void;
  clearSaveError: () => void;
}

export function useChatSave({
  chatId,
  onNewSessionCreated,
}: UseChatSaveProps): UseChatSaveResult {
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // ✅ 중복 저장 방지를 위한 ref
  const lastSavedMessageRef = useRef<string | null>(null);
  const isSavingRef = useRef(false);

  // 스토어 상태
  const { currentSessionId, setCurrentSession, updateLastMessage } =
    useChatSessionStore();
  const { selectedModelId, getSelectedModel } = useAppStore();

  // 채팅 저장 함수
  const saveChatToDatabase = useCallback(
    async (userMsg: string, assistantMsg: string) => {
      if (!userMsg?.trim() || !assistantMsg?.trim()) {
        return;
      }

      // ✅ 중복 저장 방지 체크
      const messageKey = `${userMsg.trim()}_${assistantMsg.trim()}`;
      if (lastSavedMessageRef.current === messageKey || isSavingRef.current) {
        return;
      }

      setIsSaving(true);
      setSaveError(null);
      isSavingRef.current = true; // ✅ 저장 중 플래그 설정

      try {
        // 모델 정보 확인
        const currentModel = getSelectedModel();
        const modelId = currentModel?.id || selectedModelId || 'stock-ai';

        // ✅ 핵심 수정: 'new', 'welcome' 등을 null로 변환
        const validSessionId =
          currentSessionId &&
          currentSessionId !== 'new' &&
          currentSessionId !== 'welcome' &&
          !currentSessionId.startsWith('chat_')
            ? currentSessionId
            : null;


        const requestBody = {
          sessionId: validSessionId, // ✅ null 또는 실제 UUID만 전달
          userMessage: userMsg.trim(),
          assistantMessage: assistantMsg.trim(),
          title: !validSessionId ? userMsg.slice(0, 50) : undefined, // 새 세션일 때만 제목 설정
          modelId,
        };


        const response = await fetch('/api/chat/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody),
        });


        if (!response.ok) {
          const _errorText = await response.text();
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        if (!result.success) {
          throw new Error(result.error || '채팅 저장 실패');
        }

        // ✅ 저장 성공 시 중복 방지 키 업데이트
        lastSavedMessageRef.current = messageKey;

        // 새 세션 생성 시 처리
        if (result.sessionId && !validSessionId) {

          setCurrentSession(result.sessionId);

          // 🚨 수정: 로컬 상태 히스토리 업데이트 (콜백 사용)
          const newHistoryItem: ChatHistoryItem = {
            id: result.sessionId,
            title: userMsg.slice(0, 50),
            lastMessage: assistantMsg.slice(0, 100),
            createdAt: new Date(),
            updatedAt: new Date(),
          };

          // 🚨 수정: addChatHistoryItem 대신 콜백 사용
          if (onNewSessionCreated) {
            onNewSessionCreated(newHistoryItem);
          }

          // URL 업데이트 (웰컴 모드에서 실제 세션 ID로)
          if (chatId === 'welcome' || chatId === 'new') {
            window.history.replaceState(null, '', `/chat/${result.sessionId}`);
          }
        }

      } catch (error) {
        setSaveError(
          error instanceof Error
            ? error.message
            : '알 수 없는 오류가 발생했습니다.'
        );
      } finally {
        setIsSaving(false);
        isSavingRef.current = false; // ✅ 저장 완료 플래그 해제
      }
    },
    [
      currentSessionId,
      chatId,
      getSelectedModel,
      selectedModelId,
      setCurrentSession,
      onNewSessionCreated, // 🚨 추가된 의존성
    ]
  );

  // 스트리밍 완료 처리
  const handleStreamingComplete = useCallback(
    (messages: ChatMessage[]) => {

      if (messages.length >= 2) {
        const userMessage = messages[messages.length - 2];
        const assistantMessage = messages[messages.length - 1];

        if (
          userMessage?.role === 'user' &&
          assistantMessage?.role === 'assistant' &&
          userMessage.content.trim() &&
          assistantMessage.content.trim()
        ) {

          // 스트리밍 상태 업데이트
          updateLastMessage({ isStreaming: false });

          // 🚨 수정: 지연 제거 (chat-interface에서 이미 충분히 지연됨)
          saveChatToDatabase(userMessage.content, assistantMessage.content);
        } else {
        }
      }
    },
    [saveChatToDatabase, updateLastMessage]
  );

  // 에러 클리어
  const clearSaveError = useCallback(() => {
    setSaveError(null);
  }, []);

  return {
    isSaving,
    saveError,
    saveChatToDatabase,
    handleStreamingComplete,
    clearSaveError,
  };
}
