import { getCurrentSession } from '@/lib/server/session';
import { Text } from '@/components/shared/text';
import { getCachedTodayStocksWithCTE } from '@/lib/server/stock-data';
import { User } from '@/lib/server/models';
import { Metadata } from 'next';
import { Button } from '@/components/shared/button';

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
        <Text variant="s1">나에게 딱 맞는 종목, 직접 발굴해 보세요!</Text>
        <Text variant="b1" className="text-neutral-800">
          ex. 거래량 많고, 배당 주는 착한 기업 뽑아볼래요!
        </Text>
        <Button variant="gradient" size="sm" className="mt-3" fullWidth>
          종목 발굴하러 가기
        </Button>
      </div>
    );
  };

  return (
    <div className="bg-neutral-100 h-full">
      {list.length > 0 ? <div>HELLO STOCK</div> : noList()}
    </div>
  );
}
