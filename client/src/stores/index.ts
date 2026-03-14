// 개별 스토어 export
export { useStreamingStore } from './streaming-store';
export { useAppStore } from './app-store';
export { useChatSessionStore } from './chat-session-store';
export { useChatLimitStore } from './chat-limit-store';

// 타입 import
import type { ChatMessage } from '@/types/chat';
import type { AIModel } from '@/app/(service)/chat/_config/models';

// 타입 export (필요한 경우)
export type StreamingState = {
  isStreaming: boolean;
  currentStreamId: string | null;
  setIsStreaming: (streaming: boolean, streamId?: string) => void;
  stopStreaming: () => void;
  resetStreamingState: () => void;
};

export type AppState = {
  isNavigationGuardEnabled: boolean;
  isDebugMode: boolean;
  selectedModelId: string | null;
  availableModels: AIModel[];
  preferredModel: string | null;
  setNavigationGuard: (enabled: boolean) => void;
  setDebugMode: (enabled: boolean) => void;
  setPreferredModel: (modelId: string) => void;
  resetAppSettings: () => void;
  setSelectedModel: (modelId: string) => void;
  setAvailableModels: (models: AIModel[]) => void;
  getSelectedModel: () => AIModel | null;
  resetModelSelection: () => void;
};

export type ChatSessionState = {
  currentSessionId: string | null;
  messages: ChatMessage[];
  isLoadingMessages: boolean;
  lastFailedMessage: string | null;
  isRetrying: boolean;
  isStreamInterrupted: boolean;
  setCurrentSession: (sessionId: string | null) => void;
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  updateMessage: (index: number, updates: Partial<ChatMessage>) => void;
  updateLastMessage: (updates: Partial<ChatMessage>) => void;
  setLoading: (loading: boolean) => void;
  setFailedMessage: (message: string | null) => void;
  setRetrying: (retrying: boolean) => void;
  setStreamInterrupted: (interrupted: boolean) => void;
  resetSession: () => void;
  clearMessages: () => void;
  clearErrors: () => void;
};
