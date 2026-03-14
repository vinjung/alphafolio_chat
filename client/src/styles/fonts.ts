import localFont from 'next/font/local';

export const pretendard = localFont({
  src: [
    { path: '../../public/fonts/PretendardVariable.woff2', style: 'normal' },
    // fallback otf/ttf 있으면 아래에
  ],
  display: 'swap',
  variable: '--font-pretendard',
});

export const recipekorea = localFont({
  src: [
    { path: '../../public/fonts/Recipekorea.woff2', style: 'normal' },
    // fallback otf/ttf 있으면 아래에
  ],
  display: 'swap',
  variable: '--font-recipekorea',
});
