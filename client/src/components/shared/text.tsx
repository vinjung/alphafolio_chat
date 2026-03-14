import React, { ElementType, ReactNode } from 'react';
import { cva, type VariantProps } from 'cva';

const text = cva({
  base: 'select-none font-pretendard',
  variants: {
    variant: {
      brand: [
        'font-recipekorea',
        'text-[1.375rem]',
        'text-red-900',
        '-tracking-[0.12em]',
      ],

      // Headline
      h1: 'text-h1',
      h2: 'text-h2',
      h3: 'text-h3',

      // Title
      t1: 'text-t1',
      t2: 'text-t2',

      // Subtitle
      s1: 'text-s1',
      s2: 'text-s2',
      s3: 'text-s3',

      // Body
      b1: 'text-b1',
      b2: 'text-b2',
      b3: 'text-b3',
      b4: 'text-b4',
    },
    tracking: {
      tighter: 'tracking-[-12%]',
      tight: 'tracking-[-5%]',
    },
  },
  defaultVariants: {
    variant: 'b1',
  },
});

export interface TextProps
  extends Omit<React.HTMLAttributes<HTMLElement>, 'as'>,
    VariantProps<typeof text> {
  as?: ElementType;
  children: ReactNode;
}

// 요소 매핑
type TextVariant = NonNullable<TextProps['variant']>;
const defaultElementMap: Record<TextVariant, ElementType> = {
  brand: 'h1',
  h1: 'h1',
  h2: 'h2',
  h3: 'h3',
  t1: 'h4',
  t2: 'h5',
  s1: 'h6',
  s2: 'p',
  s3: 'p',
  b1: 'p',
  b2: 'p',
  b3: 'p',
  b4: 'span',
};

export const Text: React.FC<TextProps> = ({
  variant = 'b1',
  as,
  className,
  children,
  ...props
}) => {
  const Component = as || defaultElementMap[variant as TextVariant];

  return (
    <Component className={text({ variant, className })} {...props}>
      {children}
    </Component>
  );
};
