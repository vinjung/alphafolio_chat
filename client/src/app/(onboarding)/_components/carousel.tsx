'use client';
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Text } from '@/components/shared/text';
import { cx } from '@/lib/utils/cva.config';
import Image from 'next/image';

const AUTO_INTERVAL = 3000;

const slides = [
  {
    image: '/images/slide-1.webp',
    fallback: '/images/slide-1.png',
    width: 300,
    height: 224,
    title: <Text variant="t1">그래서?.? 어떤걸...?</Text>,
    desc: (
      <>
        <Text variant="b1">
          &ldquo;말은 많은데 대체 뭐를 사야 내 계좌가 웃죠?&ldquo; 떡상만 믿어,
          너 혼자 투자하게 안 해 😘
        </Text>
      </>
    ),
  },
  {
    image: '/images/slide-2.webp',
    fallback: '/images/slide-2.png',
    width: 300,
    height: 224,
    title: <Text variant="t1">내게 필요한 핵심만 딱, 빠르게!</Text>,
    desc: (
      <>
        <Text variant="b1">
          떡상이 알아서 핵심만 챙겨줬잖아…
          <br /> 이건 운명이지? 🥹🫶🏻
        </Text>
      </>
    ),
  },
];

export default function OnboardingCarousel() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIndex((prev) => (prev + 1) % slides.length);
    }, AUTO_INTERVAL);
    return () => clearTimeout(timer);
  }, [index]);

  return (
    <div className="w-full max-w-sm mx-auto flex flex-col items-center justify-center">
      <div className="w-full flex items-end justify-center">
        <AnimatePresence mode="wait">
          <motion.div
            key={index}
            className="h-56 relative w-full flex justify-center"
            initial={{ x: 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -100, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Image
              src={slides[index].image}
              alt={`slide-${index + 1}`}
              fill
              className="object-contain"
              priority={index === 0}
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
              draggable={false}
            />
          </motion.div>
        </AnimatePresence>
      </div>

      {/* 인디케이터 */}
      <div className="mt-12 mb-4 flex gap-2 items-center">
        {slides.map((_, i) => (
          <motion.div
            key={i}
            animate={{
              width: i === index ? 27 : 8,
            }}
            className={cx(
              'h-2 rounded-full transition-all',
              i === index ? 'bg-red-900' : 'bg-red-80'
            )}
          />
        ))}
      </div>

      {/* 텍스트 */}
      <AnimatePresence mode="wait">
        <motion.div
          key={index}
          className="flex flex-col items-center mt-4 gap-2"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -20, opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="text-xl font-extrabold text-neutral-900 mb-2 text-center">
            {slides[index].title}
          </div>
          <div className="text-base text-neutral-500 text-center leading-snug">
            {slides[index].desc}
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
