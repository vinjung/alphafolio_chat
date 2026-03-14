import React from 'react';
import { type VariantProps } from 'cva';
import { cva } from '@/lib/utils/cva.config';

/**
 * Button variant styles using CVA (Class Variance Authority)
 * 
 * @variants
 * - **variant**: Button appearance style
 *   - `default`: Standard neutral button with gray background
 *   - `gradient`: Premium gradient button with brand colors
 *   - `outline`: Minimal outlined button with border
 *   - `send`: Circular send button for message input
 * 
 * - **size**: Button dimensions
 *   - `xs`: Extra small (40px height)
 *   - `sm`: Small (48px height)  
 *   - `md`: Medium (50px height)
 *   - `lg`: Large (56px height)
 * 
 * - **fullWidth**: Width behavior
 *   - `true`: Full container width
 *   - `false`: Auto width based on content
 * 
 * - **disabled**: Disabled state styling
 *   - `true`: Disabled appearance with reduced opacity
 *   - `false`: Normal interactive state
 */
const button = cva({
  base: [
    'rounded-xl',
    'text-b1',
    'box-border',
    'inline-flex justify-center items-center',
    'p-4',
    'cursor-pointer',
    'select-none',
  ],
  variants: {
    variant: {
      default: ['bg-neutral-100', 'text-neutral-800'],
      gradient: [
        'text-s1',
        'bg-(image:--gradient-primary)',
        'text-neutral-0',
      ],
      outline: [
        'rounded-sm',
        'p-2',
        'border-1 border-neutral-200',
        'ripple-effect',
      ],
      send: ['min-w-7 min-h-7', 'rounded-full', 'bg-red-900', 'flex', 'p-0'],
    },
    intent: {},
    disabled: {
      true: 'bg-neutral-300',
      false: '',
    },
    size: {
      xs: 'h-10',
      sm: 'h-12',
      md: 'h-[50px]',
      lg: 'h-14',
    },
    fullWidth: {
      true: 'w-full',
      false: 'w-auto',
    },
  },
  defaultVariants: {
    variant: 'default',
  },
});

/**
 * Button component props extending HTML button attributes with CVA variants
 * 
 * @interface ButtonProps
 * @extends React.ButtonHTMLAttributes<HTMLButtonElement>
 * @extends VariantProps<typeof button>
 */
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof button> {}

/**
 * Reusable Button component with multiple style variants
 * 
 * @param {ButtonProps} props - Button component props
 * @returns {React.ReactElement} Rendered button element
 * 
 * @example
 * // Default button
 * <Button>Click me</Button>
 * 
 * // Gradient button with large size
 * <Button variant="gradient" size="lg">
 *   Premium Action
 * </Button>
 * 
 * // Full width outline button
 * <Button variant="outline" fullWidth>
 *   Submit Form
 * </Button>
 * 
 * // Send button for chat input
 * <Button variant="send" onClick={handleSend}>
 *   <SendIcon />
 * </Button>
 */
export const Button: React.FC<ButtonProps> = ({
  variant,
  size,
  fullWidth,
  className,
  disabled,
  children,
  ...props
}) => {
  return (
    <button
      className={button({ variant, size, disabled, fullWidth, className })}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};
