import React, { useState } from 'react';
import { Icon } from '@/components/icons';
import { Text } from '@/components/shared/text';

interface ToolCallSectionProps {
  children: React.ReactNode;
  toolCount?: number; // optional로 변경하되 사용하지 않음
}

export function ToolCallSection({ children }: ToolCallSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div className="mb-3 border border-neutral-200 rounded-lg overflow-hidden bg-neutral-50 max-w-full">
      {/* 헤더 - 클릭 가능한 토글 */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between p-2.5 hover:bg-neutral-100 transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <Text variant="b2" className="flex-shrink-0">
            🛠️
          </Text>
          <Text variant="b2" className="text-neutral-700 truncate">
            도구 호출
          </Text>
        </div>
        <Icon.arrowRight
          className={`rotate-90 w-3.5 h-3.5 text-neutral-600 transition-transform duration-200 flex-shrink-0 ml-2 ${
            isExpanded ? 'rotate-270' : ''
          }`}
        />
      </button>

      {/* 콘텐츠 - 접이식, 높이를 더 작게 */}
      {isExpanded && (
        <div className="bg-white border-t border-neutral-100">
          <div className="p-2.5 max-h-24 overflow-y-auto overflow-x-hidden">
            <ol className="space-y-0.5 text-xs text-neutral-600 list-decimal list-inside">
              {children}
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}
