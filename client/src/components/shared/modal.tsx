'use client';

import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
// ✅ 사용자님께서 알려주신 정확한 경로로 수정
import { motion, AnimatePresence } from 'motion/react';
// ✅ 사용자님께서 알려주신 정확한 경로로 수정
import { cva, type VariantProps } from 'cva';
import { Icon } from '@/components/icons';
import { Text } from '@/components/shared/text';

const modalVariants = cva({
  base: 'absolute inset-0 z-[9999]',
  variants: {
    variant: {
      center: 'flex items-center justify-center',
      fullscreen: '',
      slideLeft: 'overflow-hidden',
    },
  },
  defaultVariants: {
    variant: 'center',
  },
});

const contentVariants = cva({
  base: 'relative bg-white',
  variants: {
    variant: {
      center: 'rounded-2xl w-full max-h-[80vh] m-4 flex flex-col',
      fullscreen: 'absolute inset-0 flex flex-col h-full',
      slideLeft: 'absolute inset-0 flex flex-col h-full',
    },
    size: {
      sm: 'max-w-sm',
      md: 'max-w-lg',
      lg: 'max-w-2xl',
      full: 'max-w-none',
    },
  },
  defaultVariants: {
    variant: 'center',
    size: 'md',
  },
});

const headerVariants = cva({
  base: 'flex items-center justify-between flex-shrink-0',
  variants: {
    variant: {
      center: 'px-4 py-5 border-b border-neutral-200',
      fullscreen: 'px-4 py-3 justify-center relative',
      slideLeft: 'px-4 py-3 justify-center relative',
    },
  },
});

export interface ModalProps extends VariantProps<typeof modalVariants> {
  isVisible: boolean;
  onCloseAction: () => void;
  title?: string;
  children: React.ReactNode;
  showCloseButton?: boolean;
  preventBackgroundClose?: boolean;
  size?: VariantProps<typeof contentVariants>['size'];
  disableAnimation?: boolean;
}

export function Modal({
  isVisible,
  onCloseAction,
  title,
  children,
  variant = 'center',
  size = 'md',
  showCloseButton = true,
  preventBackgroundClose = false,
  disableAnimation = false,
}: ModalProps) {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCloseAction();
    };

    if (isVisible) {
      document.addEventListener('keydown', handleEsc);
      const mobileContainer = document.getElementById('mobile-container');
      if (mobileContainer) {
        mobileContainer.style.overflow = 'hidden';
      }
      return () => {
        document.removeEventListener('keydown', handleEsc);
        if (mobileContainer) {
          mobileContainer.style.overflow = 'unset';
        }
      };
    }
  }, [isVisible, onCloseAction]);

  if (typeof window === 'undefined') return null;

  const getPortalContainer = () => {
    const mobileContainer = document.getElementById('mobile-container');
    return mobileContainer || document.body;
  };

  const handleBackgroundClick = (e: React.MouseEvent) => {
    if (!preventBackgroundClose && e.target === e.currentTarget) {
      onCloseAction();
    }
  };

  const getAnimationProps = () => {
    if (disableAnimation) {
      return {
        initial: false,
        animate: {},
        exit: {},
        // ✅ 빌드 에러 방지를 위해 as const 추가
        transition: { duration: 0 } as const,
      };
    }

    switch (variant) {
      case 'fullscreen':
        return {
          initial: { y: '100%' },
          animate: { y: 0 },
          exit: { y: '100%' },
          // ✅ 빌드 에러 방지를 위해 as const 추가
          transition: {
            type: 'tween',
            duration: 0.3,
            ease: 'easeOut',
          } as const,
        };
      case 'slideLeft':
        return {
          initial: { x: '-100%' },
          animate: { x: 0 },
          exit: { x: '-100%' },
          // ✅ 빌드 에러 방지를 위해 as const 추가
          transition: {
            type: 'tween',
            duration: 0.3,
            ease: [0.25, 0.1, 0.25, 1],
          } as const,
        };
      case 'center':
      default:
        return {
          initial: { opacity: 0, scale: 0.95 },
          animate: { opacity: 1, scale: 1 },
          exit: { opacity: 0, scale: 0.95 },
          // ✅ 빌드 에러 방지를 위해 as const 추가
          transition: { duration: 0.2 } as const,
        };
    }
  };

  const getBackgroundAnimationProps = () => {
    if (disableAnimation) {
      return {
        initial: false,
        animate: {},
        exit: {},
      };
    }
    return {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 },
    };
  };

  return createPortal(
    <AnimatePresence mode="wait">
      {isVisible && (
        <div className={modalVariants({ variant })}>
          {variant === 'center' && (
            <motion.div
              {...getBackgroundAnimationProps()}
              className="absolute inset-0"
              style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
              onClick={handleBackgroundClick}
            />
          )}

          {variant === 'slideLeft' && (
            <motion.div
              {...getBackgroundAnimationProps()}
              className="absolute inset-0 bg-black/20"
              onClick={handleBackgroundClick}
            />
          )}

          <motion.div
            {...getAnimationProps()}
            className={contentVariants({ variant, size })}
          >
            {(title || showCloseButton) && (
              <div className={headerVariants({ variant })}>
                {(variant === 'fullscreen' || variant === 'slideLeft') &&
                  showCloseButton && (
                    <button
                      onClick={onCloseAction}
                      className="absolute left-4 rounded-full hover:bg-neutral-100 transition-colors"
                      aria-label="모달 닫기"
                    >
                      <Icon.arrowRight
                        className="rotate-180 text-neutral-1100"
                        size={24}
                      />
                    </button>
                  )}

                {title && <Text variant="s1">{title}</Text>}

                {variant === 'center' && showCloseButton && (
                  <button
                    onClick={onCloseAction}
                    className="p-1 rounded-full hover:bg-neutral-100 transition-colors"
                    aria-label="모달 닫기"
                  >
                    <Icon.close />
                  </button>
                )}
              </div>
            )}

            <div className="flex-1 overflow-y-auto">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    getPortalContainer()
  );
}
