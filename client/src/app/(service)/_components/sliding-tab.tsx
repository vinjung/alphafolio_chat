'use client';

import { useRef, useEffect, useState } from 'react';
import Link from 'next/link';
import { useTabNavigation } from '@/hooks/use-tab-navigation';

// 탭 설정을 컴포넌트 내부로 직접 이동
export interface TabConfig {
  id: string;
  label: string;
  path: string;
  icon?: string;
}

// const PUBLIC_TABS: TabConfig[] = [
//   {
//     id: 'today',
//     label: '오늘의 떡상',
//     path: '/today',
//   },
//   {
//     id: 'future',
//     label: '미래의 떡상',
//     path: '/future',
//   },
// ];

interface SlidingTabsProps {
  className?: string;
  tabs: TabConfig[];
}

export const SlidingTabs = ({ className, tabs }: SlidingTabsProps) => {
  const [sliderStyle, setSliderStyle] = useState({ left: 0, width: 0 });
  const tabsRef = useRef<HTMLDivElement>(null);

  // useTabNavigation에 필요한 형태로 변환 (여기서는 바로 PUBLIC_TABS 사용)
  const navTabs = tabs.map((t) => ({ label: t.label, href: t.path })); //

  const { activeIndex } = useTabNavigation(navTabs); //

  // 활성 탭 변경 시 슬라이더 위치 업데이트
  useEffect(() => {
    if (tabsRef.current && activeIndex !== -1) {
      const activeTab = tabsRef.current.children[activeIndex] as HTMLElement;
      if (activeTab) {
        setSliderStyle({
          left: activeTab.offsetLeft,
          width: activeTab.offsetWidth,
        });
      }
    }
  }, [activeIndex]);

  return (
    <div
      className={`border-b border-neutral-200 bg-white px-4 ${className || ''}`}
    >
      <div ref={tabsRef} className="relative flex box-border gap-5">
        {tabs.map((tab, index) => {
          const isActive = index === activeIndex;

          return (
            <Link
              key={tab.id}
              href={tab.path}
              className={`flex items-center gap-2 py-4 transition-colors duration-200
                ${isActive ? 'text-neutral-1100' : 'text-neutral-500'}
              `}
            >
              <span className="text-t2">{tab.label}</span>
            </Link>
          );
        })}

        {/* 슬라이더 */}
        {activeIndex !== -1 && (
          <div
            className="absolute bottom-0 h-[2px] bg-neutral-1100 transition-all duration-300 ease-out"
            style={{
              left: `${sliderStyle.left}px`,
              width: `${sliderStyle.width}px`,
            }}
          />
        )}
      </div>
    </div>
  );
};
