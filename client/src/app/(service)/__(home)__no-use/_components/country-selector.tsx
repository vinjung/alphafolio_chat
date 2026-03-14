'use client';

import { useRouter } from 'next/navigation';
import { useTransition } from 'react';
import Chip from '@/components/shared/chip';

interface CountrySelectorProps {
  currentCountry: string;
  currentPath: string;
}

const COUNTRIES = [
  { code: 'KR', emoji: '🇰🇷', name: '한국' },
  { code: 'US', emoji: '🇺🇸', name: '미국' },
];

export function CountrySelector({
  currentCountry,
  currentPath,
}: CountrySelectorProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const handleCountryChange = (countryCode: string) => {
    // 이미 선택된 국가면 아무것도 하지 않음
    if (countryCode === currentCountry) return;

    const newUrl =
      countryCode === 'KR'
        ? currentPath
        : `${currentPath}?country=${countryCode}`;

    // 스크롤 리셋 이벤트 발생
    const scrollResetEvent = new CustomEvent('scrollToTop');
    window.dispatchEvent(scrollResetEvent);

    // useTransition으로 부드러운 전환
    startTransition(() => {
      router.push(newUrl);
    });
  };

  return (
    <div className="flex gap-2 p-4">
      {COUNTRIES.map((country) => {
        const isActive = currentCountry === country.code;

        return (
          <button
            key={country.code}
            onClick={() => handleCountryChange(country.code)}
            disabled={isPending}
          >
            <Chip isActive={isActive} className="space-x-0.5 gap-1">
              {/* 폴리필 적용으로 직접 유니코드 이모지 사용 */}
              <span
                className="max-h-5"
                style={{
                  fontFamily:
                    '"Twemoji Country Flags", "font-pretendard", "Apple Color Emoji", sans-serif',
                  fontFeatureSettings: 'normal',
                }}
              >
                {country.emoji}
              </span>{' '}
              {country.name}
            </Chip>
          </button>
        );
      })}
    </div>
  );
}
