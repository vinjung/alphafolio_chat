import MaskOverlay, {
  Hole,
} from '@/app/(service)/(home)/_components/mask-overlay';
import { SlidingTabs } from './_components/sliding-tab';
import { Text } from '@/components/shared/text';
import { getCurrentSession } from '@/lib/server/session';
import Image from 'next/image';
import { cookies } from 'next/headers';
import { ServiceSuspensionModalWrapper } from './_components/service-suspension-modal-wrapper';

export default async function HomeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user } = await getCurrentSession();
  const cookieStore = await cookies();
  const hasSeenGuestOnboarding = cookieStore.get('hasSeenGuestOnboarding');
  const thumbnailImageUrl =
    user?.thumbnailImageUrl || '/images/default-profile.webp';

  let showOnboardingMaskForGuest = false;

  // 비회원이고, 이전에 온보딩을 본 적이 없는 경우에만 마스크를 보여줌
  // 즉, user 객체가 없고 (비회원), hasSeenGuestOnboarding 쿠키가 없는 경우
  if (!user && !hasSeenGuestOnboarding) {
    showOnboardingMaskForGuest = true;
  }

  // 로그인된 사용자의 경우, hasCompletedOnboarding 플래그를 따름
  const showOnboardingMaskForAuthenticated =
    user && !user.hasCompletedOnboarding;

  // 최종적으로 마스크를 보여줄지 여부
  const showOverallOnboardingMask =
    showOnboardingMaskForGuest || showOnboardingMaskForAuthenticated;

  const maskHoles: Hole[] = [
    { shape: 'circle', right: 10, top: 128, w: 50, h: 50 }, // 공유 아이콘 위치
    { shape: 'rect', bottom: 28, w: 58, h: 58, rx: 10, ry: 10 }, // 프로필 아이콘 (하단 마이페이지 탭)

    {
      shape: 'rect',
      w: '90.26%',
      top: 300 + 64,
      h: 119,
      rx: 10,
      ry: 10,
    }, // 라운드 사각형 (떡상 AI 인사이트 영역 추정)
  ];

  const maskImages = [
    {
      src: '/images/guide-share.webp',
      fallback: '/images/guide-share.png',
      right: 35,
      top: 120,
      w: 256,
      h: 96,
    },
    {
      src: '/images/guide-insight.webp',
      fallback: '/images/guide-insight.png',
      w: 292.5,
      h: 52,
      top: 230 + 64,
      left: '4.87%',
    },
    {
      src: '/images/guide-ai.webp',
      fallback: '/images/guide-ai.png',
      w: 161.01,
      h: 88.27,
      bottom: 32,
      left: '8%',
    },
  ];

  return (
    <>
      <header className="flex items-center justify-between w-full h-14 px-4 bg-neutral-0 ">
        <Text variant="brand">떡상</Text>
        <Image
          src={thumbnailImageUrl}
          alt="프로필 이미지"
          width={25}
          height={25}
          className="w-6 h-6 rounded-full border-1 border-neutral-200"
          priority
        />
      </header>
      <SlidingTabs />
      {children}
      {showOverallOnboardingMask && (
        <MaskOverlay holes={maskHoles} images={maskImages} isGuest={!user} />
      )}
      <ServiceSuspensionModalWrapper />
    </>
  );
}
