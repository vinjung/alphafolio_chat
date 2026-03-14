import React from 'react';
import { type VariantProps } from 'cva';
import { cva } from '@/lib/utils/cva.config';
import { Icon } from '@/components/icons';

const tabItem = cva({
  base: 'flex flex-col items-center justify-center gap-1  rounded-lg w-20 h-12',
  variants: {
    state: {
      default: 'text-neutral-500',
      active: 'text-primary-500', // 또는 원하는 활성 색상
    },
  },
  defaultVariants: {
    state: 'default',
  },
});

const labelStyle = cva({
  base: 'text-s3',
  variants: {
    state: {
      default: 'text-neutral-500',
      active: 'text-red-900', // 또는 원하는 활성 색상
    },
  },
  defaultVariants: {},
});

export interface TabItemProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof tabItem> {
  iconKey: keyof typeof Icon;
  label?: string;
  isActive?: boolean;
}

export const TabItem: React.FC<TabItemProps> = ({
  iconKey,
  label,
  isActive = false,
  state: variant,
  className,
  ...props
}) => {
  // 아이콘이 variants를 가지고 있는지 확인
  const iconConfig = Icon[iconKey];
  const hasVariants =
    typeof iconConfig === 'object' &&
    'filled' in iconConfig &&
    'outline' in iconConfig;

  // 활성 상태에 따라 아이콘 선택
  const IconComponent = hasVariants
    ? isActive
      ? iconConfig.filled
      : iconConfig.outline
    : iconConfig;

  const buttonVariant = isActive ? 'active' : variant || 'default';

  return (
    <button className={tabItem({ state: buttonVariant, className })} {...props}>
      <IconComponent className="w-6 h-6" />
      {label && (
        <span className={labelStyle({ state: buttonVariant })}>{label}</span>
      )}
    </button>
  );
};
