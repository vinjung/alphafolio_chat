import React from 'react';
import { type VariantProps } from 'cva';
import { cva } from '@/lib/utils/cva.config';

const icon = cva({
  base: ['text-neutral-400'],
});

// 모든 아이콘이 공유하는 기본 props
export interface IconProps
  extends React.SVGProps<SVGSVGElement>,
    VariantProps<typeof icon> {
  size?: number;
  className?: string;
}

// 단일 아이콘 래퍼 함수
export function createIcon(
  SvgComponent: React.FC<React.SVGProps<SVGSVGElement>>
) {
  const IconComponent = ({
    size = 24,
    width,
    height,
    className,
    ...props
  }: IconProps) => {
    return (
      <SvgComponent
        width={width || size}
        height={height || size}
        className={icon({ className })}
        {...props}
      />
    );
  };

  return IconComponent;
}
