'use client';

import React, { useState, useEffect, useRef } from 'react';
import { type VariantProps } from 'cva';
import { cva } from '@/lib/utils/cva.config';
import { useTooltipState } from '@/hooks/use-tooltip';
import { Icon } from '../icons';

/**
 * Tooltip variant styles using CVA (Class Variance Authority)
 * 
 * @variants
 * - **position**: Tooltip placement relative to trigger element
 *   - `top`: Above the trigger element with bottom margin
 *   - `bottom`: Below the trigger element with top margin
 *   - `left`: Left of the trigger element
 *   - `right`: Right of the trigger element  
 *   - `center`: Centered vertically with trigger element
 * 
 * - **alignment**: Horizontal alignment within position
 *   - `left`: Align to left edge
 *   - `center`: Center horizontally with transform
 *   - `right`: Align to right edge
 */
const tooltipVariants = cva({
  base: [
    'absolute',
    'z-[80]',
    'px-[7px]',
    'py-[5px]',
    'text-b2',
    'text-neutral-0',
    'bg-neutral-1100',
    'rounded-lg',
    'shadow-lg',
    'flex',
    'items-center',
    'gap-1',
    'whitespace-nowrap',
  ],
  variants: {
    position: {
      top: ['bottom-full', 'mb-2'],
      bottom: ['top-full', 'mt-2'],
      left: ['top-[70%]', 'mt-2'],
      right: ['top-[70%]', 'mt-2'],
      center: ['top-[70%]', 'mt-2'],
    },
    alignment: {
      left: ['left-0'],
      center: ['left-1/2', 'transform', '-translate-x-1/2'],
      right: ['right-0'],
    },
  },

  defaultVariants: {
    position: 'left',
    alignment: 'left',
  },
});

// 화살표 variants
const arrowVariants = cva({
  base: ['absolute', 'w-2.5', 'h-2.5', 'bg-neutral-1100', 'rotate-45'],
  variants: {
    position: {
      top: ['top-full', '-mt-0.5'],
      bottom: ['bottom-full', '-mb-2'],
      left: ['-top-0.5', '-mb-1'],
      right: ['-top-0.5', '-mb-1'],
      center: ['-top-0.5', '-mb-1'],
    },
    arrowAlignment: {
      left: ['left-4'],
      center: ['left-1/2', 'transform', '-translate-x-1/2'],
      right: ['right-4'],
    },
  },
  defaultVariants: {
    position: 'left',
    arrowAlignment: 'left',
  },
});

interface TooltipProps extends VariantProps<typeof tooltipVariants> {
  content: string;
  children: React.ReactNode;
  delay?: number;
  storageKey?: string;
  arrowPosition?: VariantProps<typeof arrowVariants>['arrowAlignment'];
  className?: string;
}

export function Tooltip({
  content,
  children,
  delay = 1000,
  storageKey = 'tooltip-shown',
  position = 'left',
  alignment = 'left',
  arrowPosition = 'left',
  className = '',
}: TooltipProps) {
  const { hasShown, markAsShown } = useTooltipState(storageKey);
  const [isVisible, setIsVisible] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // ✅ 자동 표시 타이머
  useEffect(() => {
    if (!hasShown) {
      const timer = setTimeout(() => setIsVisible(true), delay);
      return () => clearTimeout(timer);
    }
  }, [hasShown, delay]);

  // ✅ 명시적 닫기 (이벤트 전파 차단)
  const handleClose = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setIsVisible(false);
    markAsShown();
  };

  // 기존 center position을 alignment로 변환
  const finalAlignment = position === 'center' ? 'center' : alignment;
  const finalPosition = position === 'center' ? 'left' : position;

  if (hasShown) {
    return <>{children}</>;
  }

  return (
    <span className="relative inline-flex">
      {children}

      {isVisible && (
        <div
          ref={tooltipRef}
          className={tooltipVariants({
            position: finalPosition,
            alignment: finalAlignment,
            className,
          })}
        >
          {/* 화살표 */}
          <div
            className={arrowVariants({
              position: finalPosition,
              arrowAlignment: arrowPosition,
            })}
          />

          <span>{content}</span>

          {/* ✅ 명시적 닫기 버튼 */}
          <Icon.close
            onClick={handleClose}
            size={15}
            className="text-neutral-0 cursor-pointer hover:opacity-70"
          />
        </div>
      )}
    </span>
  );
}
