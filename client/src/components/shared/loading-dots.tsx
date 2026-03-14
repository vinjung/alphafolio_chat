'use client';

import { motion } from 'motion/react';

interface LoadingDotsProps {
  className?: string;
}

export function LoadingDots({ className = '' }: LoadingDotsProps) {
  return (
    <div className={`flex items-center gap-1 ${className}`}>
      {[0, 1, 2].map((index) => (
        <motion.div
          key={index}
          className="w-2 h-2 bg-red-900 rounded-full"
          animate={{
            x:
              index === 0
                ? [0, 16, 0]
                : index === 1
                  ? [0, -8, 8, 0]
                  : [0, -16, 0],
            opacity: [0.3, 1, 0.3],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut',
            delay: index * 0.1,
          }}
        />
      ))}
    </div>
  );
}
