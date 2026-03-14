'use client';

import React, { useEffect, useState, useRef } from 'react';
import { Icon } from '@/components/icons';
import { completeOnboardingAction } from '@/app/(service)/(home)/_actions/onboarding';
import { useRouter } from 'next/navigation';

export interface Hole {
  shape: 'circle' | 'rect';
  left?: number | string;
  right?: number | string;
  top?: number | string;
  bottom?: number | string;
  w: number | string;
  h: number | string;
  rx?: number;
  ry?: number;
}

interface OverlayImage {
  src: string;
  left?: number | string;
  right?: number | string;
  top?: number | string;
  bottom?: number | string;
  w: number;
  h: number;
  style?: React.CSSProperties;
}

interface MaskOverlayProps {
  holes: Hole[];
  images?: OverlayImage[];
  dimmColor?: string;
  isGuest?: boolean;
}

const MaskOverlay: React.FC<MaskOverlayProps> = ({
  holes,
  images,
  dimmColor = 'rgba(0,0,0,0.8)',
  isGuest = false,
}) => {
  const [size, setSize] = useState({ width: 428, height: 844 });
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setSize({
          width: Math.min(rect.width, 428),
          height: rect.height,
        });
      } else {
        const isMobile = window.innerWidth <= 428;
        setSize({
          width: isMobile ? window.innerWidth : 428,
          height: window.innerHeight,
        });
      }
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  const handleClose = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    e.preventDefault();
    if (isGuest) {
      const expires = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
      const isLocalhostOrHttp =
        window.location.hostname === 'localhost' ||
        window.location.protocol === 'http:';
      const secureAttribute = isLocalhostOrHttp ? '' : '; Secure';

      document.cookie = `hasSeenGuestOnboarding=true; Path=/; SameSite=Lax; Expires=${expires.toUTCString()}${secureAttribute}`;
      router.refresh();
    } else {
      const result = await completeOnboardingAction();
      if (result.success) {
        router.refresh();
      } else {
        console.error('온보딩 완료 상태 DB 업데이트 실패:', result.message);
      }
    }
  };

  // 🎯 WebP 고해상도 srcSet 생성 함수
  const generateSrcSet = (baseSrc: string): string => {
    const baseNameWithoutExt = baseSrc.replace(/\.webp$/, '');

    // 1x, 2x, 3x WebP 이미지 srcSet 생성
    const srcSet = [
      `${baseSrc} 1x`,
      `${baseNameWithoutExt}@2x.webp 2x`,
      `${baseNameWithoutExt}@3x.webp 3x`,
    ].join(', ');

    return srcSet;
  };

  // 헬퍼 함수: 숫자 또는 % 문자열을 실제 픽셀 값으로 변환
  const parseSizeValue = (value: number | string, baseSize: number): number => {
    if (typeof value === 'string' && value.endsWith('%')) {
      const percentage = parseFloat(value) / 100;
      return baseSize * percentage;
    }
    return value as number;
  };

  const getHoleProps = (hole: Hole) => {
    const actualWidth = parseSizeValue(hole.w, size.width);
    const actualHeight = parseSizeValue(hole.h, size.height);

    let x_coord: number;
    let y_coord: number;

    // 수평(X) 좌표 계산
    if (hole.left != null) {
      x_coord = parseSizeValue(hole.left, size.width);
    } else if (hole.right != null) {
      const rightValue = parseSizeValue(hole.right, size.width);
      x_coord = size.width - rightValue - actualWidth;
    } else {
      x_coord = (size.width - actualWidth) / 2;
    }

    // 수직(Y) 좌표 계산
    if (hole.top != null) {
      y_coord = parseSizeValue(hole.top, size.height);
    } else if (hole.bottom != null) {
      const bottomValue = parseSizeValue(hole.bottom, size.height);
      y_coord = size.height - bottomValue - actualHeight;
    } else {
      y_coord = (size.height - actualHeight) / 2;
    }

    if (hole.shape === 'circle') {
      const r = Math.min(actualWidth, actualHeight) / 2;
      const cx = x_coord + r;
      const cy = y_coord + r;
      return (
        <circle
          key={`${hole.shape}-${cx}-${cy}`}
          cx={cx}
          cy={cy}
          r={r}
          fill="black"
        />
      );
    } else if (hole.shape === 'rect') {
      return (
        <rect
          key={`${hole.shape}-${x_coord}-${y_coord}`}
          x={x_coord}
          y={y_coord}
          width={actualWidth}
          height={actualHeight}
          rx={hole.rx || 0}
          ry={hole.ry || 0}
          fill="black"
        />
      );
    }
    return null;
  };

  const getImgStyle = (img: OverlayImage): React.CSSProperties => {
    const style: React.CSSProperties = {
      position: 'absolute',
      width: img.w,
      height: img.h,
      // 🎯 픽셀 정렬 개선을 위한 CSS 추가
      imageRendering: 'crisp-edges',
      transform: 'translateZ(0)', // GPU 가속으로 렌더링 품질 개선
      ...img.style,
    };

    // 🎯 좌표를 정수값으로 반올림하여 픽셀 정렬 개선
    if (img.left !== undefined) {
      style.left =
        typeof img.left === 'string' ? img.left : Math.round(img.left);
    }
    if (img.right !== undefined) {
      style.right =
        typeof img.right === 'string' ? img.right : Math.round(img.right);
    }
    if (img.top !== undefined) {
      style.top = typeof img.top === 'string' ? img.top : Math.round(img.top);
    }
    if (img.bottom !== undefined) {
      style.bottom =
        typeof img.bottom === 'string' ? img.bottom : Math.round(img.bottom);
    }

    return style;
  };

  // ✅ 마스크 오버레이 영역 터치 시 이벤트 전파 차단
  const handleMaskInteraction = (e: React.MouseEvent | React.TouchEvent) => {
    e.stopPropagation();
    e.preventDefault();
  };

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 z-[100] pointer-events-auto"
      onMouseDown={handleMaskInteraction}
      onTouchStart={handleMaskInteraction}
    >
      <div className="absolute top-0 left-0 p-4 pointer-events-auto z-[101]">
        <button onClick={handleClose} aria-label="가이드 닫기">
          <Icon.close size={24} className="text-neutral-0" />
        </button>
      </div>

      <svg
        width={size.width}
        height={size.height}
        viewBox={`0 0 ${size.width} ${size.height}`}
        className="absolute inset-0 w-full h-full pointer-events-none z-[100]"
        style={{ display: 'block' }}
      >
        <defs>
          <mask id="mask">
            <rect
              x="0"
              y="0"
              width={size.width}
              height={size.height}
              fill="white"
            />
            {holes.map((h) => getHoleProps(h))}
          </mask>
        </defs>
        <rect
          x="0"
          y="0"
          width={size.width}
          height={size.height}
          fill={dimmColor}
          mask="url(#mask)"
        />
      </svg>

      {images?.map((img, idx) => (
        <picture
          key={idx}
          style={getImgStyle(img)}
          className="pointer-events-none select-none z-[200]"
        >
          {/* 🎯 WebP 고해상도 버전만 사용 */}
          <source srcSet={generateSrcSet(img.src)} type="image/webp" />

          {/* 🎯 기본 img 태그 */}
          <img
            src={img.src}
            width={img.w}
            height={img.h}
            alt=""
            draggable={false}
            className="pointer-events-none select-none"
            style={{
              width: img.w,
              height: img.h,
              // 🎯 이미지 렌더링 품질 개선
              imageRendering: 'crisp-edges',
            }}
          />
        </picture>
      ))}
    </div>
  );
};

export default MaskOverlay;
