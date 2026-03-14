import { dirname } from 'path';
import { fileURLToPath } from 'url';
import { FlatCompat } from '@eslint/eslintrc';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  {
    rules: {
      // 사용하지 않는 변수 규칙 완화
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_', // _로 시작하는 매개변수 무시
          varsIgnorePattern: '^_', // _로 시작하는 변수 무시
          caughtErrorsIgnorePattern: '^_', // _로 시작하는 catch 에러 무시
          ignoreRestSiblings: true, // rest siblings 무시
        },
      ],
      // React 컴포넌트의 사용하지 않는 props 허용
      'react/jsx-uses-vars': 'error',
      'react/jsx-uses-react': 'error',
    },
  },
];

export default eslintConfig;
