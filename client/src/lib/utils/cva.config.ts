import { defineConfig } from 'cva';
import { extendTailwindMerge } from 'tailwind-merge';

const twMerge = extendTailwindMerge({
  extend: {
    theme: {
      text: [
        'h1',
        'h2',
        'h3',
        't1',
        't2',
        's1',
        's2',
        's3',
        'b1',
        'b2',
        'b3',
        'b4',
      ],
    },
  },
});

export const { cva, cx, compose } = defineConfig({
  hooks: {
    onComplete: (className) => twMerge(className),
  },
});
