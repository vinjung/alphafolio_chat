import { SlidingTabs, TabConfig } from '../_components/sliding-tab';
import { Text } from '@/components/shared/text';
import { getCurrentSession } from '@/lib/server/session';
import Image from 'next/image';
import { cookies } from 'next/headers';
import { Icon } from '@/components/icons';

export default async function HomeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user } = await getCurrentSession();
  // const cookieStore = await cookies();
  // const hasSeenGuestOnboarding = cookieStore.get('hasSeenGuestOnboarding');

  // // 로그인된 사용자의 경우, hasCompletedOnboarding 플래그를 따름
  // const showOnboardingMaskForAuthenticated =
  //   user && !user.hasCompletedOnboarding;

  const HOME_TABS: TabConfig[] = [
    {
      id: 'home',
      label: '내 포트폴리오',
      path: '/home',
    },
    {
      id: 'stock',
      label: '관심 종목',
      path: '/stock',
    },
  ];

  return (
    <>
      <header className="flex items-center justify-between w-full h-14 px-4 bg-neutral-0 ">
        <Text variant="brand">떡상</Text>
        <>
          <button
            className="absolute right-4 p-2 rounded-lg transition-colors"
            aria-label="검색"
            type="button"
          >
            <Icon.search size={24} className="text-neutal-800" />
          </button>
        </>
      </header>
      <SlidingTabs tabs={HOME_TABS} />
      {children}
    </>
  );
}
