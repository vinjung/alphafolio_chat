'use client';

import { Modal } from '@/components/shared/modal';
import { Button } from '@/components/shared/button';
import { Text } from '@/components/shared/text';

interface NavigationGuardProps {
  isOpen: boolean;
  targetUrl: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export function NavigationGuard({
  isOpen,
  onConfirm,
  onCancel,
}: NavigationGuardProps) {
  return (
    <Modal
      isVisible={isOpen}
      onCloseAction={onCancel}
      variant="center"
      size="sm"
      showCloseButton={false}
    >
      <div className="flex flex-col items-center gap-6 p-6">
        {/* 제목과 설명 */}
        <div className="text-center space-y-2">
          <Text variant="t2" className="text-neutral-1100">
            잠깐! AI가 응답 중입니다 🤖
          </Text>
          <Text variant="b1" className="text-neutral-900">
            이 화면을 나가면 AI 응답이 중단되고
            <br />
            떡상 기회 1회가 차감됩니다.
          </Text>
        </div>

        {/* 버튼들 */}
        <div className="flex gap-3 w-full">
          <Button variant="default" onClick={onConfirm} className="flex-1/3">
            나가기
          </Button>
          <Button variant="gradient" onClick={onCancel} className="flex-2/3">
            머무르기
          </Button>
        </div>
      </div>
    </Modal>
  );
}
