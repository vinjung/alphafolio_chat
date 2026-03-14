'use client';

import { useEffect, useState } from 'react';
import { Text } from '@/components/shared/text';

interface ChatLimitBadgeProps {
  remaining: number;
  limit: number;
  className?: string;
}

export function ChatLimitBadge({
  remaining,
  className = '',
}: ChatLimitBadgeProps) {
  const [displayRemaining, setDisplayRemaining] = useState(remaining);
  const [isAnimating, setIsAnimating] = useState(false);

  // 숫자 변경 시 애니메이션 트리거
  useEffect(() => {
    if (displayRemaining !== remaining) {
      setIsAnimating(true);

      const timer = setTimeout(() => {
        setDisplayRemaining(remaining);
        setIsAnimating(false);
      }, 150);

      return () => clearTimeout(timer);
    }
  }, [remaining, displayRemaining]);

  return (
    <div className={className}>
      <div
        className="
        relative inline-flex items-center gap-1.5 px-3 py-2 rounded-full
        bg-neutral-900 text-white shadow-lg
        transition-all duration-300 ease-in-out
        backdrop-blur-sm
      "
      >
        <Text variant="s3" as="span">
          🚀
        </Text>

        <Text variant="b2" as="span">
          오늘 남은 떡상 기회
        </Text>

        <span className="flex items-center">
          {/* 숫자 애니메이션 컨테이너 */}
          <div className="relative inline-flex items-center justify-center w-6 h-3 overflow-hidden">
            <Text
              variant="s2"
              as="span"
              className={`
                text-red-80
                absolute inset-0 flex items-center justify-center
                transition-all duration-300 ease-in-out
                ${isAnimating ? 'transform translate-y-full opacity-0' : 'transform translate-y-0 opacity-100'}
              `}
            >
              {displayRemaining}
            </Text>

            {/* 새로운 숫자 (아래에서 올라옴) */}
            {isAnimating && (
              <Text
                variant="s2"
                as="span"
                className="
                  absolute inset-0 flex items-center justify-center
                  transition-all duration-300 ease-in-out
                  transform -translate-y-full opacity-0
                "
                style={{
                  animation: isAnimating
                    ? 'slideUp 0.3s ease-in-out forwards'
                    : undefined,
                }}
              >
                {remaining}
              </Text>
            )}
          </div>

          <Text variant="s2" as="span" className="text-red-80">
            회
          </Text>
        </span>
      </div>

      {/* 인라인 스타일로 keyframes 정의 */}
      <style>{`
        @keyframes slideUp {
          0% {
            transform: translateY(100%);
            opacity: 0;
          }
          50% {
            opacity: 1;
          }
          100% {
            transform: translateY(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
}
