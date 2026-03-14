import { getCurrentSession } from '@/lib/server/session';
import { Text } from '@/components/shared/text';
import { getCachedTodayStocksWithCTE } from '@/lib/server/stock-data';
import { User } from '@/lib/server/models';
import { Metadata } from 'next';
import { Button } from '@/components/shared/button';
import { ScrollContainer } from '../_components/scroll-container';
import Badge from '@/components/shared/badge';
import { Icon } from '@/components/icons';

interface HomePageProps {
  searchParams: Promise<{ country?: string }>;
}

export default async function Home({ searchParams }: HomePageProps) {
  const { user } = await getCurrentSession();
  const params = await searchParams;
  const list = [];

  const noList = function () {
    return (
      <div className="bg-white flex flex-col justify-center items-center px-4 py-5">
        <Text variant="s1">복잡한 종목 고민은 끝!</Text>
        <Text variant="b1" className="text-neutral-800">
          준비된 포트폴리에서 마음에 드는 걸 담아보세요.
        </Text>
        <Button variant="gradient" size="sm" className="mt-3" fullWidth>
          포트폴리오 추가하러 가기
        </Button>
      </div>
    );
  };

  const favoriteList = () => {
    return (
      <ScrollContainer className="px-4 py-4">
        <div className="bg-white flex flex-row justify-between items-center p-2.5 space-x-7 border-b border-neutral-200">
          <div className="flex flex-col justify-center items-start space-y-1.5">
            <div className="flex flex-row space-x-1.5">
              <Text variant="s1">코스피 이기는 스마트 포트폴리오</Text>
              <Badge variant="up">+22.2%</Badge>
            </div>
            <Text variant="b2">
              코스피 수익률을 능가하는 것을 목표로 한 능동적 투자
              포트폴리오입니다...
            </Text>
            <Text variant="b3">
              <span className="text-neutral-600">생성일 |</span>2025.07.22 15:30
            </Text>
          </div>
          <Icon.favorite.filled size={26} />
        </div>
      </ScrollContainer>
    );
  };

  return (
    <div className="bg-neutral-100 h-full">
      {/*{list.length > 0 ? favoriteList() : noList()}*/}
      {favoriteList()}
    </div>
  );
}
