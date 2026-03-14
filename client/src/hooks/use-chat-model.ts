'use client';

import { useEffect, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAppStore } from '@/stores';
import { createPersonalizedModels } from '@/app/(service)/chat/_config/models';
import type { AIModel } from '@/app/(service)/chat/_config/models';

interface UseChatModelProps {
  userNickname: string;
}

interface UseChatModelResult {
  // 모델 상태
  selectedModel: AIModel | null;
  availableModels: AIModel[];

  // 프리셋 메시지 (Zustand에서 관리)
  presetMessage: string;

  // 액션들
  handleModelChange: (model: AIModel) => void;
}

const createPresetMessage = (stockName: string, ticker: string): string => {
  return `${stockName}(${ticker}) 종합 투자 분석 보고서를 '매수', '매도', '중립' 의견과 함께 작성해 주세요.`;
};

export function useChatModel({
  userNickname,
}: UseChatModelProps): UseChatModelResult {
  const router = useRouter();
  const searchParams = useSearchParams();
  const presetStock = searchParams.get('preset');
  const presetTicker = searchParams.get('ticker');

  // ✅ Zustand 스토어에서 모든 상태 관리
  const {
    selectedModelId,
    availableModels,
    presetMessage,
    setSelectedModel,
    setAvailableModels,
    setPresetMessage,
    setHasSetPresetOnce,
    setLastPresetKey,
    resetPresetFlags,
    getSelectedModel,
  } = useAppStore();

  // 현재 선택된 모델
  const selectedModel = getSelectedModel();

  // ✅ 모델 초기화
  useEffect(() => {
    const AVAILABLE_MODELS = createPersonalizedModels(userNickname);
    setAvailableModels(AVAILABLE_MODELS);

    // 선택된 모델이 없으면 첫 번째 모델을 기본으로 설정
    if (!selectedModelId && AVAILABLE_MODELS.length > 0) {
      setSelectedModel(AVAILABLE_MODELS[0].id);
    }
  }, [userNickname, setAvailableModels, setSelectedModel, selectedModelId]);

  // URL 변경 즉시 감지하여 프리셋 상태 초기화
  useEffect(() => {
    // URL 파라미터가 변경되면 이전 상태는 무조건 리셋
    resetPresetFlags();

    // 새로운 프리셋이 있으면 설정
    if (presetStock && presetTicker) {
      const newPresetKey = `${presetStock}-${presetTicker}`;
      const newPresetMessage = createPresetMessage(presetStock, presetTicker);

      setPresetMessage(newPresetMessage);
      setHasSetPresetOnce(true);
      setLastPresetKey(newPresetKey);
    }
  }, [
    presetStock,
    presetTicker,
    resetPresetFlags,
    setPresetMessage,
    setHasSetPresetOnce,
    setLastPresetKey,
  ]);

  // 모델 변경 핸들러 (세션 이동 로직 구현)
  const handleModelChange = useCallback(
    async (newModel: AIModel) => {
      if (newModel.id === selectedModel?.id) {
        return;
      }

      // 모델 상태 먼저 업데이트
      setSelectedModel(newModel.id);

      // 현재 URL 및 상태 분석
      const currentUrl = window.location.pathname;
      const hasPresetParams = !!presetStock && !!presetTicker;

      const isActualNewChatPath =
        currentUrl === '/chat' ||
        currentUrl === '/chat/welcome' ||
        currentUrl === '/chat/new' ||
        currentUrl.includes('new=true') ||
        currentUrl.includes('chat_');

      const isNewChatMode =
        isActualNewChatPath || (hasPresetParams && isActualNewChatPath);

      if (isNewChatMode) {
        // 새 채팅/웰컴/프리셋 모드: 모델만 변경, 세션 이동 안함
        return;
      }

      // 기존 채팅에서 모델 변경: 해당 모델의 최근 세션으로 이동
      try {
        const response = await fetch('/api/chat/model-sessions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            modelId: newModel.id,
          }),
        });

        if (!response.ok) {
          return;
        }

        const result = await response.json();

        if (result.success && result.latestSession) {
          // 해당 모델의 최근 세션으로 이동
          const sessionId = result.latestSession.id;
          router.push(`/chat/${sessionId}`);
        } else {
          // 해당 모델의 세션이 없으면 새 채팅으로 이동
          router.push('/chat/welcome');
        }
      } catch (_error) {
        // 실패 시 새 채팅으로 이동
        router.push('/chat/welcome');
      }
    },
    [selectedModel, setSelectedModel, presetStock, presetTicker, router]
  );

  return {
    selectedModel,
    availableModels,
    presetMessage,
    handleModelChange,
  };
}
