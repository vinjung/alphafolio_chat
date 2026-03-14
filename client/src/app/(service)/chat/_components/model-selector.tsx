'use client';

import { useState, useRef, useEffect } from 'react';
import { Icon } from '@/components/icons';
import { Text } from '@/components/shared/text';
import { Tooltip } from '@/components/shared/tooltip';
import type { AIModel } from '../_config/models';

interface ModelSelectorProps {
  selectedModel: AIModel;
  availableModels: AIModel[];
  onModelChangeAction: (model: AIModel) => void;
}

export function ModelSelector({
  selectedModel,
  availableModels,
  onModelChangeAction,
}: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleModelSelect = (model: AIModel) => {
    onModelChangeAction(model);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <Tooltip
        content="뇌절 AI 창의력으로 숨은 연관주 소환 👑"
        storageKey="model-selector-tooltip-shown"
        delay={1000}
        position="center"
        arrowPosition="center"
      >
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex gap-1.5 items-center"
          aria-expanded={isOpen}
          aria-haspopup="listbox"
        >
          <Text variant="brand">떡상</Text>
          <Text variant="b2" className="text-neutral-800">
            {selectedModel.name}
          </Text>
          <Icon.arrowRight
            className={`transition-transform duration-200 ${
              isOpen ? 'rotate-90' : 'rotate-90'
            }`}
            size={18}
          />
        </button>
      </Tooltip>

      {isOpen && (
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 w-64 bg-neutral-50 rounded-xl shadow-2xl z-50 overflow-hidden">
          {availableModels.map((model) => (
            <button
              key={model.id}
              onClick={() => handleModelSelect(model)}
              className={`first:border-b-1 first:border-b-neutral-300 w-full px-4 py-3 text-left hover:bg-neutral-50 transition-colors`}
              role="option"
              aria-selected={selectedModel.id === model.id}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <Text variant="s2" className="text-neutral-900">
                    {model.name}
                  </Text>
                  <Text variant="b3" className="text-neutral-600 mt-1">
                    {model.description}
                  </Text>
                </div>
                {selectedModel.id === model.id && (
                  <Icon.select size={26} className="text-red-500 ml-2" />
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
