import React from 'react';
import { type VariantProps } from 'cva';
import { cva } from '@/lib/utils/cva.config';

const input = cva({
  base: [
    'w-full',
    'px-4 py-[10px]',
    'box-border',
    'focus:ring-1 focus:outline-none',
    'bg-neutral-0',
    'placeholder-neutral-600',
    'text-neutral-1100',
    'text-b1',
  ],
  variants: {
    variant: {
      default: ['ring-1 ring-neutral-300', 'rounded-lg', 'h-12'],
      chat: ['ring-1 ring-red-900', 'rounded-full', 'h-10'],
    },
    intent: {
      default: '',
      disabled: '',
    },
    disabled: {
      true: ['ring-neutral-300 ', 'bg-neutral-200', 'text-neutral-600'],
      false: '',
    },
  },
  defaultVariants: {
    intent: 'default',
    variant: 'default',
  },
});

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement>,
    VariantProps<typeof input> {
  placeholder?: string;
}

export const Input: React.FC<InputProps> = ({
  placeholder = '떡상 정보, 질문만 하면 한눈에!',
  intent,
  disabled,
  className,
  ...props
}) => {
  return (
    <input
      className={input({ intent, disabled, className })}
      placeholder={placeholder}
      disabled={disabled}
      {...props}
    />
  );
};

export default Input;
