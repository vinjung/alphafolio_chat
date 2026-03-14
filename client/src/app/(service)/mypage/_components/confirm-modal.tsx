'use client';

import { useState } from 'react';
import { Modal } from '@/components/shared/modal';
import { Text } from '@/components/shared/text';
import { Button } from '@/components/shared/button';

interface ConfirmModalProps {
  isVisible: boolean;
  onCloseAction: () => void;
  title: string;
  description: string;
  confirmText: string;
  cancelText: string;
  onConfirmAction: () => Promise<void>;
  isDestructive?: boolean; // 위험한 액션인지 (빨간색 버튼)
}

export function ConfirmModal({
  isVisible,
  onCloseAction,
  title,
  description,
  confirmText,
  cancelText,
  onConfirmAction,
  isDestructive = false,
}: ConfirmModalProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      await onConfirmAction();
    } catch (error) {
      console.error('액션 실패:', error);
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isVisible={isVisible}
      onCloseAction={onCloseAction}
      variant="center"
      size="sm"
      showCloseButton={false}
    >
      <div className="flex justify-center items-center text-center flex-col gap-3 p-6">
        <Text variant="t2">{title}</Text>
        <Text
          variant="b1"
          className="text-neutral-600 mb-3 whitespace-pre-line"
        >
          {description}
        </Text>

        <div className="flex justify-between items-center w-full gap-3">
          <Button
            className="flex-2/5"
            variant="default"
            fullWidth
            onClick={onCloseAction}
            disabled={isLoading}
          >
            {cancelText}
          </Button>
          <Button
            className="flex-3/5"
            variant={isDestructive ? 'gradient' : 'gradient'}
            fullWidth
            onClick={handleConfirm}
            disabled={isLoading}
          >
            {isLoading ? '처리 중...' : confirmText}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
