'use client';

import { useState, useRef } from 'react';
import { Text } from '@/components/shared/text';
import { MenuItem } from './menu-item';
import { ConfirmModal } from './confirm-modal';
import Image from 'next/image';
import { Modal } from '@/components/shared/modal';
import { showGlobalSnackbar } from '@/components/shared/snackbar';
import { Button } from '@/components/shared/button';
import { Icon } from '@/components/icons';
import { deleteAccountAction, logoutAction } from '@/lib/server/actions';

type ModalType = 'logout' | 'delete' | 'help' | 'localStorage_cleared' | null;

export function MenuSection() {
  const [activeModal, setActiveModal] = useState<ModalType>(null);

  // ✅ 5초 터치 감지를 위한 상태
  const touchTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [isLongPressing, setIsLongPressing] = useState(false);

  const handleLogout = async () => {
    await logoutAction();
  };

  const handleDeleteAccount = async () => {
    await deleteAccountAction();
  };

  const handleCopyAccount = async () => {
    const accountNumber = '국민) 222-24-0376-494 정인호';
    try {
      await navigator.clipboard.writeText(accountNumber);
      showGlobalSnackbar('계좌번호가 복사되었습니다! 💝', { position: 'top' });
      setActiveModal(null);
    } catch {
      showGlobalSnackbar('복사에 실패했습니다 😅', { position: 'top' });
    }
  };

  const handleTermsAndPolicy = () => {
    window.open(
      'https://ddeoksang-ai.qshop.ai/privacy-policy-terms-of-use',
      '_blank'
    );
  };

  const handleSendFeedback = () => {
    const email = 'cleverage426@gmail.com';
    const subject = '[떡상] 문의/피드백';
    const body = `안녕하세요! 떡상 서비스에 문의드립니다.

📝 문의 유형을 선택해주세요:
□ 기능 개선 제안
□ 버그 신고
□ 사용법 문의
□ 주식 정보 오류
□ 계정/로그인 문제
□ 기타 문의

📋 문의 내용:
[구체적인 문의 내용을 작성해주세요]

🔍 문제 발생 상황 (해당시):
- 발생 페이지: (예: 오늘의 떡상, 미래 전망 등)
- 발생 시간:
- 오류 메시지:

💡 개선 제안 (해당시):
[어떤 기능이나 개선사항을 원하시는지 자세히 작성해주세요]

---
📱 기기 정보:
- 사용 기기: (예: iPhone, 안드로이드, PC 웹)
- 브라우저: (웹 사용시)
- 문의일: ${new Date().toLocaleDateString('ko-KR')}

떡상 팀이 빠르게 도움드리겠습니다! 🚀`;

    const mailtoUrl = `mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.location.href = mailtoUrl;
  };

  // ✅ 5초 터치 시작 핸들러
  const handleTouchStart = () => {
    setIsLongPressing(true);

    touchTimerRef.current = setTimeout(() => {
      // 5초 후 실행: 로컬 스토리지 즉시 클리어 + 완료 다이얼로그 표시
      try {
        localStorage.clear();
        setActiveModal('localStorage_cleared');
        setIsLongPressing(false);
        console.log('🧹 로컬 스토리지 초기화 완료 (이스터에그)');
      } catch (error) {
        console.error('로컬 스토리지 초기화 실패:', error);
        showGlobalSnackbar('초기화에 실패했습니다 😅', { position: 'top' });
        setIsLongPressing(false);
      }
    }, 5000); // 5초
  };

  // ✅ 터치 종료 핸들러
  const handleTouchEnd = () => {
    if (touchTimerRef.current) {
      clearTimeout(touchTimerRef.current);
      touchTimerRef.current = null;
    }

    // 5초 미만이면 기존 도움 모달 표시
    if (isLongPressing) {
      setActiveModal('help');
    }

    setIsLongPressing(false);
  };

  return (
    <>
      <div className="flex flex-col gap-5 px-4 py-8">
        <div className="space-y-2.5">
          <Text variant="b3" className="text-neutral-600 mb-3">
            도와주상
          </Text>
          {/* ✅ 5초 터치 감지가 적용된 도와주상 메뉴 */}
          <div
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
            onMouseDown={handleTouchStart} // 데스크톱 지원
            onMouseUp={handleTouchEnd}
            onMouseLeave={handleTouchEnd} // 마우스가 영역을 벗어날 때도 종료
            className="select-none" // 텍스트 선택 방지
          >
            <MenuItem
              title="떡 하나 주면 안 잡아 먹지~ᵔᴥᵔ"
              onPress={() => {}} // 실제 클릭은 터치 이벤트에서 처리
            />
          </div>
        </div>

        {/* 계정 섹션 */}
        <div className="">
          <Text variant="b3" className="text-neutral-600 mb-2.5">
            계정
          </Text>
          <MenuItem
            title="로그아웃"
            className="rounded-none rounded-t-lg"
            onPress={() => setActiveModal('logout')}
          />
          <MenuItem
            title="회원탈퇴"
            className="rounded-none rounded-b-lg -mt-[1px]"
            onPress={() => setActiveModal('delete')}
          />
        </div>

        {/* 피드백 섹션 */}
        <div className="">
          <Text variant="b3" className="text-neutral-600 mb-3">
            지원 & 정보
          </Text>
          <MenuItem
            className="rounded-none rounded-t-lg"
            title="약관 및 정책"
            onPress={handleTermsAndPolicy}
          />
          <MenuItem
            title="cleverage426@gmail.com"
            className="rounded-none rounded-b-lg -mt-[1px]"
            onPress={handleSendFeedback}
          />
        </div>
      </div>

      {/* 로그아웃 확인 모달 */}
      <ConfirmModal
        isVisible={activeModal === 'logout'}
        onCloseAction={() => setActiveModal(null)}
        title="정말 로그아웃할 거에요?"
        description={`떡상길 잠시 쉬는 거죠?
          언제든 다시 돌아와 주세요!`}
        confirmText="아-웃"
        cancelText="남는다"
        onConfirmAction={handleLogout}
      />

      {/* 회원탈퇴 확인 모달 */}
      <ConfirmModal
        isVisible={activeModal === 'delete'}
        onCloseAction={() => setActiveModal(null)}
        title="진짜 떠나시는 거에요?"
        description={`떡상길에서의 모험이 끝나네요😢
          다시 만날 날 기다릴게요!`}
        confirmText="난 간다"
        cancelText="취소"
        onConfirmAction={handleDeleteAccount}
        isDestructive={true}
      />

      {/* 기존 도움 모달 */}
      <Modal
        isVisible={activeModal === 'help'}
        onCloseAction={() => setActiveModal(null)}
        title="도와주십쇼🙇🏻"
        variant="center"
        size="md"
      >
        <div className="p-6 text-center space-y-4">
          <div className="w-full h-48 relative rounded-lg overflow-hidden bg-neutral-100">
            <Image
              src="/images/help.webp"
              alt="도와주상 고양이"
              fill
              className="object-cover"
            />
          </div>

          <Text
            variant="b1"
            className="text-neutral-800 text-start whitespace-pre-line"
          >
            여러분들의 도움은 저희의 꿈이자 미래를 이루는데 많은 도움이 될
            것입니다 ᵔᴥᵔ(뀨)
          </Text>

          <div className="space-y-3">
            <Text variant="s2" className="mr-auto text-start">
              [계좌번호]
            </Text>
            <Button
              variant="outline"
              onClick={handleCopyAccount}
              className="w-full justify-between p-4"
            >
              <Text variant="b1">국민) 222-24-0376-494 정인호</Text>
              <Icon.copy.outline size={20} />
            </Button>
          </div>

          <Text variant="b2" className="text-neutral-600">
            기왕이면 떡 두개😅
          </Text>
        </div>
      </Modal>

      {/* ✅ 로컬 스토리지 초기화 완료 다이얼로그 */}
      <Modal
        isVisible={activeModal === 'localStorage_cleared'}
        onCloseAction={() => setActiveModal(null)}
        title="로컬 스토리지 초기화"
        variant="center"
        size="sm"
        preventBackgroundClose={true}
      >
        <div className="p-6 text-center space-y-4">
          <Text variant="b1" className="text-neutral-600 mt-4">
            모든 로컬 데이터가 삭제되었습니다
          </Text>

          <Button
            variant="gradient"
            onClick={() => setActiveModal(null)}
            className="w-full mt-6"
          >
            확인
          </Button>
        </div>
      </Modal>
    </>
  );
}
