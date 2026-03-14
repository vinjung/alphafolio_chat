'use client';

import { Modal } from '@/components/shared/modal';
import { Text } from '@/components/shared/text';

interface ServiceSuspensionModalProps {
  isVisible: boolean;
  onCloseAction: () => void;
}

export function ServiceSuspensionModal({
  isVisible,
  onCloseAction,
}: ServiceSuspensionModalProps) {
  return (
    <Modal
      isVisible={isVisible}
      onCloseAction={onCloseAction}
      title="서비스 중단 안내"
      variant="center"
      size="md"
      showCloseButton={true}
      preventBackgroundClose={false}
    >
      <div className="px-6 pb-6 space-y-4 mt-4">
        <Text variant="b2" className="leading-relaxed text-neutral-700">
          안녕하세요.
          <br />
          보다 안정적이고 새로운 기능을 제공하기 위해 시스템 점검 및 업데이트를 진행하게 되어 잠시 서비스 이용이 중단될 예정입니다.
        </Text>
        
        <div className="bg-neutral-50 rounded-lg p-4 space-y-2">
          <div>
            <Text variant="s2" className="font-medium text-neutral-900">
              업데이트 기간:
            </Text>
            <Text variant="b2" className="text-neutral-700">
              2025년 9월 ~ 11월
            </Text>
          </div>
          
          <div>
            <Text variant="s2" className="font-medium text-neutral-900">
              업데이트 내용:
            </Text>
            <Text variant="b2" className="text-neutral-700">
              대규모 신규 기능 추가
            </Text>
          </div>
        </div>

        <Text variant="b2" className="leading-relaxed text-neutral-700">
          서비스 이용에 불편을 드려 죄송합니다. 개발이 완료되는 대로 빠르게 재개하여 더 나은 모습으로 찾아뵙겠습니다.
          <br />
          <br />
          이용해 주셔서 감사합니다.
        </Text>
      </div>
    </Modal>
  );
}