import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { AIModel } from '@/app/(service)/chat/_config/models';
import type { ChatHistoryItem } from '@/lib/server/chat-history';

interface AppState {
  // UI 상태
  isNavigationGuardEnabled: boolean;
  isDebugMode: boolean;

  // ✅ 모델 선택 상태
  selectedModelId: string | null;
  availableModels: AIModel[];
  preferredModel: string | null; // 호환성을 위해 유지

  // ✅ 채팅 관련 전역 상태 추가
  chatHistory: ChatHistoryItem[];
  presetMessage: string;
  hasSetPresetOnce: boolean; // ✅ 프리셋 설정 플래그 추가
  lastPresetKey: string; // ✅ 마지막 프리셋 키 (주식 변경 감지용)

  // 기본 액션들
  setNavigationGuard: (enabled: boolean) => void;
  setDebugMode: (enabled: boolean) => void;
  setPreferredModel: (modelId: string) => void;
  resetAppSettings: () => void;

  // 모델 관리 액션들
  setSelectedModel: (modelId: string) => void;
  setAvailableModels: (models: AIModel[]) => void;
  getSelectedModel: () => AIModel | null;
  resetModelSelection: () => void;

  // ✅ 채팅 관련 액션들 추가
  setChatHistory: (history: ChatHistoryItem[]) => void;
  addChatHistoryItem: (item: ChatHistoryItem) => void;
  setPresetMessage: (message: string) => void;
  clearPresetMessage: () => void;
  setHasSetPresetOnce: (hasSet: boolean) => void; // ✅ 플래그 설정 함수
  setLastPresetKey: (key: string) => void; // ✅ 프리셋 키 설정 함수
  resetPresetFlags: () => void; // ✅ 플래그 초기화 함수
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set, get) => ({
        // 초기 상태
        isNavigationGuardEnabled: true,
        isDebugMode: process.env.NODE_ENV === 'development',
        selectedModelId: null,
        availableModels: [],
        preferredModel: null,

        // ✅ 새로운 초기 상태들
        chatHistory: [],
        presetMessage: '',
        hasSetPresetOnce: false, // ✅ 초기값 false
        lastPresetKey: '', // ✅ 초기값 빈 문자열

        // 기존 액션들
        setNavigationGuard: (enabled: boolean) => {
          set(
            { isNavigationGuardEnabled: enabled },
            false,
            'app/setNavigationGuard'
          );
        },

        setDebugMode: (enabled: boolean) => {
          set({ isDebugMode: enabled }, false, 'app/setDebugMode');
        },

        setPreferredModel: (modelId: string) => {
          set(
            {
              preferredModel: modelId,
              selectedModelId: modelId,
            },
            false,
            'app/setPreferredModel'
          );
        },

        resetAppSettings: () => {
          set(
            {
              isNavigationGuardEnabled: true,
              isDebugMode: process.env.NODE_ENV === 'development',
              selectedModelId: null,
              preferredModel: null,
              chatHistory: [],
              presetMessage: '',
              hasSetPresetOnce: false, // ✅ 플래그도 초기화
              lastPresetKey: '', // ✅ 프리셋 키도 초기화
            },
            false,
            'app/reset'
          );
        },

        // 모델 관리 액션들
        setSelectedModel: (modelId: string) => {
          set(
            {
              selectedModelId: modelId,
              preferredModel: modelId,
            },
            false,
            'app/setSelectedModel'
          );
        },

        setAvailableModels: (models: AIModel[]) => {
          set(
            (state) => {
              const newState: Partial<AppState> = { availableModels: models };

              // 선택된 모델이 없거나 사용 가능한 모델 목록에 없으면 첫 번째 모델로 설정
              if (
                !state.selectedModelId ||
                !models.find((m) => m.id === state.selectedModelId)
              ) {
                if (models.length > 0) {
                  newState.selectedModelId = models[0].id;
                  newState.preferredModel = models[0].id;
                }
              }

              return newState;
            },
            false,
            'app/setAvailableModels'
          );
        },

        getSelectedModel: () => {
          const state = get();
          if (!state.selectedModelId || state.availableModels.length === 0) {
            return null;
          }
          return (
            state.availableModels.find((m) => m.id === state.selectedModelId) ||
            null
          );
        },

        resetModelSelection: () => {
          set(
            (state) => ({
              selectedModelId:
                state.availableModels.length > 0
                  ? state.availableModels[0].id
                  : null,
            }),
            false,
            'app/resetModelSelection'
          );
        },

        // ✅ 새로운 채팅 관련 액션들
        setChatHistory: (history: ChatHistoryItem[]) => {
          set({ chatHistory: history }, false, 'app/setChatHistory');
        },

        addChatHistoryItem: (item: ChatHistoryItem) => {
          set(
            (state) => ({
              chatHistory: [item, ...state.chatHistory],
            }),
            false,
            'app/addChatHistoryItem'
          );
        },

        setPresetMessage: (message: string) => {
          set(
            {
              presetMessage: message,
              hasSetPresetOnce: true, // ✅ 설정할 때 플래그도 true로
            },
            false,
            'app/setPresetMessage'
          );
        },

        clearPresetMessage: () => {
          set(
            {
              presetMessage: '',
              // ✅ 플래그는 유지 (사용자가 의도적으로 지웠으므로 재설정 방지)
            },
            false,
            'app/clearPresetMessage'
          );
        },

        // ✅ 새로운 플래그 관리 함수들
        setHasSetPresetOnce: (hasSet: boolean) => {
          set({ hasSetPresetOnce: hasSet }, false, 'app/setHasSetPresetOnce');
        },

        setLastPresetKey: (key: string) => {
          set({ lastPresetKey: key }, false, 'app/setLastPresetKey');
        },

        resetPresetFlags: () => {
          set(
            {
              presetMessage: '',
              hasSetPresetOnce: false,
              lastPresetKey: '',
            },
            false,
            'app/resetPresetFlags'
          );
        },
      }),
      {
        name: 'app-store',
        partialize: (state) => ({
          preferredModel: state.preferredModel,
          selectedModelId: state.selectedModelId,
          isNavigationGuardEnabled: state.isNavigationGuardEnabled,
          // ✅ presetMessage와 hasSetPresetOnce는 세션 간 유지하지 않음 (일회성이므로)
          // chatHistory는 서버에서 로드하므로 persist 하지 않음
        }),
      }
    ),
    {
      name: 'app-store',
      enabled: process.env.NODE_ENV === 'development',
    }
  )
);
