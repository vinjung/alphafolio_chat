import { create } from 'zustand';

interface ChatLimitInfo {
  used: number;
  limit: number;
  remaining: number;
  canSend: boolean;
  resetTime: string;
}

interface ChatLimitState {
  // 상태
  limitInfo: ChatLimitInfo | null;
  isLoading: boolean;
  error: string | null;
  isGuest: boolean;

  // 플래그
  isInitialized: boolean; // 한 번 초기화되었는지 확인

  // 액션
  setLimitInfo: (limitInfo: ChatLimitInfo | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setIsGuest: (isGuest: boolean) => void;
  setInitialized: (initialized: boolean) => void;
  decrementRemaining: () => void;
  refreshLimit: () => Promise<void>;
  initializeLimit: () => Promise<void>; // 초기화 함수
  resetLimitState: () => void;
}

// ✅ 전역 요청 상태 (모듈 레벨)
let isGlobalFetching = false;
let globalAbortController: AbortController | null = null;

export const useChatLimitStore = create<ChatLimitState>((set, get) => ({
  // 초기 상태
  limitInfo: null,
  isLoading: false,
  error: null,
  isGuest: false,
  isInitialized: false,

  // 상태 설정 함수들
  setLimitInfo: (limitInfo) => set({ limitInfo }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  setIsGuest: (isGuest) => set({ isGuest }),
  setInitialized: (isInitialized) => set({ isInitialized }),

  // 한도 차감 (로컬 상태만 업데이트)
  decrementRemaining: () => {
    const { limitInfo } = get();
    if (!limitInfo) return;

    const newUsed = limitInfo.used + 1;
    const newRemaining = Math.max(0, limitInfo.limit - newUsed);

    set({
      limitInfo: {
        ...limitInfo,
        used: newUsed,
        remaining: newRemaining,
        canSend: newRemaining > 0,
      },
    });
  },

  // 한도 정보 조회 함수
  refreshLimit: async () => {
    const { setLoading, setError, setLimitInfo, setIsGuest } = get();

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/chat/limit');

      if (!response.ok) {
        if (response.status === 401) {
          setLimitInfo(null);
          setIsGuest(true);
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        setLimitInfo(result.data);
        setIsGuest(false);
      } else {
        throw new Error(result.error || '한도 조회 실패');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류');
      setIsGuest(false);
    } finally {
      setLoading(false);
    }
  },

  // 초기화 함수 (중복 방지 로직 포함)
  initializeLimit: async () => {
    const {
      isInitialized,
      setLoading,
      setError,
      setLimitInfo,
      setIsGuest,
      setInitialized,
    } = get();

    // 이미 초기화되었거나 현재 요청 중이면 중복 방지
    if (isInitialized || isGlobalFetching) {
      return;
    }

    try {
      // 이전 요청 취소
      if (globalAbortController) {
        globalAbortController.abort();
      }

      globalAbortController = new AbortController();
      isGlobalFetching = true;

      setLoading(true);
      setError(null);

      const response = await fetch('/api/chat/limit', {
        signal: globalAbortController.signal,
      });

      if (!response.ok) {
        if (response.status === 401) {
          setLimitInfo(null);
          setIsGuest(true);
          setInitialized(true);
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        setLimitInfo(result.data);
        setIsGuest(false);
        setInitialized(true);
      } else {
        throw new Error(result.error || '한도 조회 실패');
      }
    } catch (err) {
      // AbortError는 정상적인 취소
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }

      setError(err instanceof Error ? err.message : '알 수 없는 오류');
      setIsGuest(false);
      setInitialized(true); // 에러가 나도 초기화는 완료로 처리
    } finally {
      isGlobalFetching = false;
      setLoading(false);
    }
  },

  // 상태 리셋
  resetLimitState: () => {
    // 전역 요청도 정리
    if (globalAbortController) {
      globalAbortController.abort();
      globalAbortController = null;
    }
    isGlobalFetching = false;

    set({
      limitInfo: null,
      isLoading: false,
      error: null,
      isGuest: false,
      isInitialized: false,
    });
  },
}));
