import React from 'react';
import { type VariantProps } from 'cva';
import { cva, cx } from '@/lib/utils/cva.config';

const chip = cva({
  base: [
    'w-auto',
    'h-[38px]',
    'px-3 py-2',
    'inline-flex justify-center',
    'rounded-full',
    'cursor-pointer',
    'select-none', // 텍스트 선택 방지
  ],
  variants: {
    state: {
      default: [
        'bg-neutral-0',
        'border border-neutral-200',
        'text-s2 text-neutral-700',
      ],
      active: ['bg-red-900', 'text-s2 text-neutral-0'],
    },
  },
});

export interface ChipProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof chip> {
  isActive?: boolean;
}

export const Chip: React.FC<ChipProps> = ({
  state = 'default',
  isActive = false,
  className,
  children,
  ...props
}) => {
  const chipVariant = isActive ? 'active' : state || 'default';

  return (
    <span
      className={cx(
        chip({ state: chipVariant, className }),
        'ripple-effect',
        chipVariant === 'active' ? 'ripple-effect-dark' : ''
      )}
      {...props}
    >
      {children}
    </span>
  );
};

export default Chip;
