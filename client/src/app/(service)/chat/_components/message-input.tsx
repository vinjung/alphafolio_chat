'use client';

import { useState, KeyboardEvent, useEffect, useRef } from 'react';
import { Icon } from '@/components/icons';
import { Button } from '@/components/shared/button';

interface MessageInputProps {
  onSendMessageAction: (message: string, clearInput: () => void) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  isStreaming?: boolean; // ✅ 스트리밍 상태 추가
  onStopStreaming?: () => void; // ✅ 스트리밍 중단 함수 추가
  presetMessage?: string;
  onPresetUsed?: () => void;
}

export function MessageInput({
  onSendMessageAction,
  disabled = false,
  placeholder = '떡상 정보, 질문만 하면 한눈에!',
  className,
  isStreaming = false, // ✅ 기본값 false
  onStopStreaming,
  presetMessage,
  onPresetUsed,
}: MessageInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (presetMessage && !message) {
      setMessage(presetMessage);
      console.log('🎯 프리셋 메시지 입력창에 설정:', presetMessage);
    }
  }, [presetMessage, message]);

  // ✅ 추가: 텍스트 높이 자동 조절
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      // 높이 초기화를 40px로 고정
      textarea.style.height = '40px';

      // 스크롤 높이 확인
      const scrollHeight = textarea.scrollHeight;

      // 40px보다 클 때만 늘어나도록
      if (scrollHeight > 40) {
        const baseHeight = 40; // 첫 줄 기준 높이
        const lineHeight = 20; // 추가 줄당 높이 (line-height: 1.25 × 16px = 20px)
        const maxHeight = baseHeight + lineHeight * 4; // 5줄 = 40 + 80 = 120px
        const newHeight = Math.min(scrollHeight, maxHeight);
        textarea.style.height = `${newHeight}px`;
      }
    }
  }, [message]);

  const handleSend = () => {
    if (!message.trim()) return;

    if (presetMessage && message === presetMessage && onPresetUsed) {
      onPresetUsed();
    }

    // 성공 시에만 클리어할 수 있도록 콜백 전달
    const clearInput = () => setMessage('');
    onSendMessageAction(message, clearInput);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    setMessage(newValue);

    // 사용자가 프리셋 메시지를 수정하거나 완전히 삭제하면 프리셋 클리어
    if (
      presetMessage &&
      (newValue !== presetMessage || newValue === '') &&
      onPresetUsed
    ) {
      console.log('🎯 프리셋 메시지 수정/삭제됨 - 프리셋 클리어');
      onPresetUsed();
    }
  };

  // ✅ 버튼 클릭 핸들러 - 스트리밍 상태에 따라 분기
  const handleButtonClick = () => {
    if (isStreaming && onStopStreaming) {
      onStopStreaming(); // 스트리밍 중단
    } else {
      handleSend(); // 메시지 전송 (handleSend에서 조건 체크)
    }
  };

  const showStopButton = isStreaming;

  // message-input.tsx - 기존 스타일 유지하면서 안전 영역만 추가

  return (
    <div className={`px-4 py-2 bg-neutral-0 pb-safe ${className || ''}`}>
      {/* 기존 내용 그대로 유지 */}
      <div className="flex gap-2.5 justify-between items-center">
        <div className="flex-1 relative flex items-center">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            spellCheck={false}
            className="w-full min-h-10 resize-none px-4 py-2.5 ring-1 ring-red-900 rounded-[20px] focus:ring-1 focus:outline-none bg-neutral-0 placeholder-neutral-600 text-neutral-1100 text-b1 disabled:ring-neutral-300 disabled:bg-neutral-200 disabled:text-neutral-600 overflow-hidden leading-tight"
          />
        </div>

        <Button
          variant="send"
          onClick={handleButtonClick}
          disabled={disabled && !isStreaming}
          className={`w-7 h-7 flex-shrink-0 ${
            disabled && !isStreaming
              ? 'bg-neutral-200'
              : 'bg-red-900 hover:bg-red-800'
          }`}
          aria-label={showStopButton ? '응답 중단' : '메시지 전송'}
        >
          {showStopButton ? (
            <Icon.stop className="text-neutral-0" size={16} />
          ) : (
            <Icon.send className="text-neutral-0" size={24} />
          )}
        </Button>
      </div>
    </div>
  );
}
