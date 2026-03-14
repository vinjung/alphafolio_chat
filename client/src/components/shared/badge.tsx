import React from 'react';
import { type VariantProps } from 'cva';
import { cva, cx } from '@/lib/utils/cva.config';

const badge = cva({
  base: [
    'w-fit',
    'inline-flex justify-center items-center',
    'rounded-full',
    'text-b3',
    'px-3 py-2',
    'box-border',
    'select-none',
    'leading-[24px]',
  ],
  variants: {
    variant: {
      default: [
        'text-neutral-1100',
        'bg-neutral-200',
        'px-[5px] py-[2.5px]',
        'align-top',
      ],
      link: [
        'ring-1 ring-red-900',
        'bg-neutral-0',
        'text-red-900',
        'gap-1',
        'cursor-pointer',
      ],
      up: ['bg-red-50', 'text-red-900', 'px-[5px] py-[2.5px]', 'align-top'],
      down: ['bg-blue-50', 'text-blue-900', 'px-[5px] py-[2.5px]', 'align-top'],
      hash: ['bg-neutral-0', 'ring-1 ring-neutral-200', 'text-neutral-900'],
    },
  },
});

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badge> {
  enableRipple?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  variant,
  className,
  children,
  enableRipple = false,
  ...props
}) => {
  const shouldEnableRipple = enableRipple || variant === 'link';

  return (
    <span
      className={cx(
        badge({ variant, className }),
        shouldEnableRipple ? 'ripple-effect' : ''
      )}
      {...props}
    >
      {children}
    </span>
  );
};

export default Badge;
