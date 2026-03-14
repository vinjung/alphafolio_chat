import { getCurrentSession } from '@/lib/server/session';
import { Text } from '@/components/shared/text';
import { ProfileSection } from './_components/profile-section';
import { MenuSection } from './_components/menu-section';
import { redirect } from 'next/navigation';

export default async function MyPage() {
  const { user } = await getCurrentSession();

  // 비로그인 사용자는 루트로 리다이렉트
  if (!user) {
    redirect('/');
  }

  return (
    <>
      <header className="flex items-center justify-between w-full h-14 px-5 py-4 bg-neutral-0 ">
        <Text variant="brand">마이페이지</Text>
      </header>
      <div
        className="overflow-y-scroll"
        style={{ height: 'calc(100% - 6rem - 56px)' }}
      >
        <ProfileSection user={user} />
        <MenuSection />
      </div>
    </>
  );
}
