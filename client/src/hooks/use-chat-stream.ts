'use client';

import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import type { ModelApiConfig } from '@/app/(service)/chat/_config/models';
import type { VisualizationData } from '@/types/chart';

interface StreamEventData {
  type: 'chunk' | 'complete' | 'error';
  content?: string;
  full_response?: string;
  error?: string;
  visualization?: VisualizationData;
}

interface UseChatStreamResult {
  response: string;
  isStreaming: boolean;
  error: string | null;
  visualization: VisualizationData | null;
  sendMessage: (message: string, modelConfig?: ModelApiConfig) => Promise<void>;
  disconnect: () => void;
}

export function useChatStream(): UseChatStreamResult {
  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [visualization, setVisualization] = useState<VisualizationData | null>(null);

  const router = useRouter();
  const abortControllerRef = useRef<AbortController | null>(null);
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(
    null
  );

  const disconnect = useCallback(() => {
    // Reader 중단
    if (readerRef.current) {
      try {
        readerRef.current.cancel();
        readerRef.current = null;
      } catch (_error) {
        // Reader 중단 실패는 무시
      }
    }

    // AbortController로 fetch 중단
    if (abortControllerRef.current) {
      try {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      } catch (_error) {
        // AbortController 중단 실패는 무시
      }
    }

    // 상태 즉시 업데이트
    setIsStreaming(false);
    setError(null);
  }, []);

  const sendMessage = useCallback(
    async (message: string, modelConfig?: ModelApiConfig) => {
      // 이전 요청이 있다면 중단
      if (isStreaming) {
        disconnect();
        // 잠시 대기해서 이전 요청이 완전히 정리되도록
        await new Promise((resolve) => setTimeout(resolve, 100));
      }

      setError(null);
      setResponse('');
      setVisualization(null);
      setIsStreaming(true);

      // 새로운 AbortController 생성
      abortControllerRef.current = new AbortController();

      try {
        const response = await fetch('/api/chat/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message,
            modelConfig: modelConfig || undefined,
          }),
          signal: abortControllerRef.current.signal,
        });

        // 401 에러 처리 - 비회원 감지 시 루트로 리다이렉트
        if (response.status === 401) {
          router.push('/');
          return;
        }

        // 에러 응답 처리
        if (!response.ok) {
          const errorText = await response.text();

          if (response.status === 429) {
            const errorData = JSON.parse(errorText);
            const limitInfo = errorData.limit || {};
            const errorMessage = `일일 채팅 한도(${limitInfo.limit || 5}회)를 초과했습니다.`;
            throw new Error(errorMessage);
          }

          // 500 에러 등을 명시적으로 throw
          const networkError = new Error(
            `네트워크 오류 (${response.status})`
          ) as Error & { isNetworkError: boolean };
          networkError.isNetworkError = true;
          throw networkError;
        }

        if (!response.body) {
          throw new Error('응답 본문이 없습니다');
        }

        const reader = response.body.getReader();
        readerRef.current = reader;
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          // 새로운 청크 디코딩
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;

          // SSE 메시지들 처리
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // 마지막 불완전한 줄은 버퍼에 유지

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);

              if (data.trim() === '') continue;

              try {
                const parsed: StreamEventData = JSON.parse(data);

                if (parsed.type === 'chunk' && parsed.content) {
                  setResponse((prev) => prev + parsed.content);
                } else if (parsed.type === 'complete') {
                  // Capture visualization data from complete event
                  if (parsed.visualization) {
                    setVisualization(parsed.visualization);
                  }

                  setResponse((currentResponse) => {

                    // 응답 완전성 검증
                    if (parsed.full_response) {
                      // 길이 차이가 크거나 현재 응답이 비어있으면 full_response 사용
                      const lengthDiff = Math.abs(
                        parsed.full_response.length - currentResponse.length
                      );
                      const shouldUseFullResponse =
                        currentResponse.length === 0 ||
                        lengthDiff > currentResponse.length * 0.1; // 10% 이상 차이

                      if (shouldUseFullResponse) {
                        return parsed.full_response;
                      } else {
                        return currentResponse;
                      }
                    }

                    // 빈 응답 감지 로직
                    const finalResponse =
                      currentResponse || parsed.full_response || '';

                    // 응답이 빈 문자열이거나 공백만 있는 경우
                    if (!finalResponse || finalResponse.trim().length === 0) {
                      throw new Error(
                        '서버에서 빈 응답을 받았습니다. 다시 시도해주세요.'
                      );
                    }

                    // 응답이 너무 짧은 경우 (5자 미만)
                    if (finalResponse.trim().length < 5) {
                      throw new Error(
                        '응답이 불완전합니다. 다시 시도해주세요.'
                      );
                    }

                    return finalResponse;
                  });
                  break;
                } else if (parsed.type === 'error') {
                  // 서버 에러 처리
                  const errorMessage =
                    parsed.error || '서버 처리 중 오류가 발생했습니다.';
                  throw new Error(errorMessage);
                }
              } catch (parseError) {
                // 파싱 오류 처리
                if (
                  parseError instanceof Error &&
                  (parseError.message.includes('서버 처리 중 오류') ||
                    parseError.message.includes('빈 응답') ||
                    parseError.message.includes('불완전'))
                ) {
                  // 이미 처리된 에러는 다시 throw
                  throw parseError;
                } else {
                  // 파싱 오류는 일반 에러로 throw
                  throw new Error('스트리밍 처리 중 오류 발생');
                }
              }
            }
          }
        }
      } catch (err) {

        // AbortController로 중단된 경우는 에러로 처리하지 않음
        if (abortControllerRef.current?.signal.aborted) {
          return;
        }

        // 실제 에러인 경우에만 throw
        if (err instanceof Error) {
          setError(err.message);
          throw err;
        } else {
          const unknownError = new Error('알 수 없는 오류가 발생했습니다.');
          setError(unknownError.message);
          throw unknownError;
        }
      } finally {
        // 스트리밍 상태 정리
        setIsStreaming(false);
        readerRef.current = null;
        abortControllerRef.current = null;
      }
    },
    [isStreaming, disconnect, router]
  );

  return {
    response,
    isStreaming,
    error,
    visualization,
    sendMessage,
    disconnect,
  };
}
