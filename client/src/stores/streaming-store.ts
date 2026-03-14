import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface StreamingState {
  // 스트리밍 상태
  isStreaming: boolean;
  currentStreamId: string | null;

  // 액션들
  setIsStreaming: (streaming: boolean, streamId?: string) => void;
  stopStreaming: () => void;
  resetStreamingState: () => void;
}

export const useStreamingStore = create<StreamingState>()(
  devtools(
    (set, _get) => ({
      // 초기 상태
      isStreaming: false,
      currentStreamId: null,

      // 스트리밍 시작/종료
      setIsStreaming: (streaming: boolean, streamId?: string) => {
        set(
          (state) => ({
            isStreaming: streaming,
            currentStreamId: streaming
              ? streamId || state.currentStreamId
              : null,
          }),
          false,
          'streaming/setIsStreaming'
        );
      },

      // 스트리밍 강제 중단
      stopStreaming: () => {
        set(
          {
            isStreaming: false,
            currentStreamId: null,
          },
          false,
          'streaming/stop'
        );
      },

      // 전체 상태 초기화
      resetStreamingState: () => {
        set(
          {
            isStreaming: false,
            currentStreamId: null,
          },
          false,
          'streaming/reset'
        );
      },
    }),
    {
      name: 'streaming-store',
      enabled: process.env.NODE_ENV === 'development', // 개발 모드에서만 활성화
    }
  )
);
