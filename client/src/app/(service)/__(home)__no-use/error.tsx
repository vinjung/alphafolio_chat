'use client';

import { useEffect } from 'react';
import { Button } from '@/components/shared/button';
import { Text } from '@/components/shared/text';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function FutureError({ error, reset }: ErrorProps) {
  useEffect(() => {
    // 에러 로깅 (선택사항)
    console.error('Future page error:', error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center">
      <div className="text-[100px] mb-6">😶‍🌫️</div>

      <Text variant="t1" className="text-neutral-900 mb-14">
        페이지가 안 불러와져요… <br />
        좀만 이따가 다시 시도해 주세요.
      </Text>

      <Button variant="gradient" fullWidth className="max-w-xs" onClick={reset}>
        다시 시도하기
      </Button>
    </div>
  );
}
