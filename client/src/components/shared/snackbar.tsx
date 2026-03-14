'use client';

import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { createRoot, Root } from 'react-dom/client';
import { motion, AnimatePresence } from 'motion/react';
import { cva } from '@/lib/utils/cva.config';
import { Icon } from '../icons';

const snackbarVariants = cva({
  base: [
    'max-w-[352px] mx-auto', // 최대 너비 + 자동 중앙 정렬
    'p-2.5 rounded-xl shadow-[0_4px_12px_0_rgba(0,0,0,0.1)]',
    'flex items-center gap-2 transition-all duration-300',
    'pointer-events-auto',
  ],
  variants: {
    variant: {
      success: ['bg-black text-white'],
      error: ['bg-red-500 text-white'],
      info: ['bg-blue-500 text-white'],
    },
    position: {
      top: [],
      bottom: [],
    },
  },
  defaultVariants: {
    variant: 'success',
    position: 'bottom',
  },
});

interface SnackbarProps {
  message: string;
  variant?: 'success' | 'error' | 'info';
  position?: 'top' | 'bottom';
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// 스낵바 컴포넌트
function SnackbarComponent({
  message,
  variant = 'success',
  position = 'bottom',
  duration = 3000,
  action,
  onClose,
}: SnackbarProps & { onClose: () => void }) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(onClose, 300);
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(onClose, 300);
  };

  // 위치에 따른 애니메이션 설정
  const getAnimationProps = () => {
    return position === 'top'
      ? {
          initial: { y: -200, opacity: 0 },
          animate: { y: 0, opacity: 1 },
          exit: { y: -100, opacity: 0 },
        }
      : {
          initial: { y: 100, opacity: 0 },
          animate: { y: 0, opacity: 1 },
          exit: { y: 100, opacity: 0 },
        };
  };

  const showCloseButton = duration === 0 || duration > 5000 || action;

  // 모바일 컨테이너 기준 컨테이너 찾기
  const getContainer = () => {
    if (typeof window === 'undefined') return null;

    // 모바일 컨테이너를 우선으로 찾기
    const mobileContainer = document.getElementById('mobile-container');
    return mobileContainer || document.body;
  };

  const container = getContainer();
  if (!container) return null;

  return createPortal(
    <AnimatePresence>
      {isVisible && (
        <motion.div
          {...getAnimationProps()}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className={snackbarVariants({ variant, position })}
          style={
            position === 'top'
              ? {
                  position: 'absolute',
                  top: '56px',
                  left: '16px',
                  right: '16px',
                  zIndex: 9999,
                }
              : {
                  position: 'absolute',
                  bottom: '100px',
                  left: '16px',
                  right: '16px',
                  zIndex: 9999,
                }
          }
        >
          <Icon.check size={26} />
          <span className="text-sm flex-1">{message}</span>

          {action && (
            <button
              onClick={action.onClick}
              className="ml-2 text-sm font-medium underline hover:no-underline transition-all"
            >
              {action.label}
            </button>
          )}

          {showCloseButton && (
            <Icon.close
              size={24}
              onClick={handleClose}
              aria-label="닫기"
              className="ml-2 text-neutral-0 cursor-pointer hover:opacity-70 transition-opacity"
            />
          )}
        </motion.div>
      )}
    </AnimatePresence>,
    container
  );
}

// 글로벌 스낵바 표시 함수
let currentRoot: Root | null = null;

export function showGlobalSnackbar(
  message: string,
  options: Partial<SnackbarProps> = {}
): void {
  if (typeof window === 'undefined') return;

  // 기존 스낵바 제거
  if (currentRoot) {
    currentRoot.unmount();
    currentRoot = null;
  }

  // 모바일 컨테이너에서 임시 컨테이너 생성
  const mobileContainer = document.getElementById('mobile-container');
  const container = document.createElement('div');

  if (mobileContainer) {
    mobileContainer.appendChild(container);
  } else {
    // 폴백: body에 추가
    document.body.appendChild(container);
  }

  currentRoot = createRoot(container);

  currentRoot.render(
    <SnackbarComponent
      message={message}
      variant={options.variant || 'success'}
      position={options.position || 'bottom'}
      duration={options.duration || 3000}
      action={options.action}
      onClose={() => {
        if (currentRoot) {
          currentRoot.unmount();
          currentRoot = null;
        }
        if (container.parentNode) {
          container.parentNode.removeChild(container);
        }
      }}
    />
  );
}
