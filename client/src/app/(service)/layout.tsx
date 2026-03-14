import { BottomNavigationBar } from './_components/bottom-navigation';

export default function ServiceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="relative flex-1 flex flex-col h-full">
      {/* 메인 콘텐츠 영역 - 바텀 네비 높이(64px) 제외 */}
      {children}
      {/* 스낵바 컨테이너 */}
      <div
        id="snackbar-container"
        className="absolute bottom-20 left-1/2 z-[10000] -translate-x-1/2 pointer-events-none"
      />

      {/* 바텀 네비게이션 - 고정 높이 */}
      <BottomNavigationBar />
    </main>
  );
}
