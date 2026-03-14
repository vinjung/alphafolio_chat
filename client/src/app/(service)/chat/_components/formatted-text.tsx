import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Text } from '@/components/shared/text';
import { ToolCallSection } from './tool-call-section';
import type { Components } from 'react-markdown';

// 포맷된 텍스트를 렌더링하는 컴포넌트
interface FormattedTextProps {
  children: string;
  className?: string;
}

/**
 * XML 태그 블록을 감지하고 추출하는 함수 (기존 유지)
 */
function extractToolBlocks(text: string): {
  beforeContent: string;
  toolBlocks: Array<{ content: string; toolCount: number }>;
  afterContent: string;
} {
  // XML 태그가 포함된 영역을 전체적으로 찾기
  const hasToolTags = /<[^>]+>/.test(text);

  if (!hasToolTags) {
    return {
      beforeContent: text,
      toolBlocks: [],
      afterContent: '',
    };
  }

  // 첫 번째 XML 태그 위치 찾기
  const firstTagMatch = text.match(/<[^>]+>/);
  if (!firstTagMatch) {
    return {
      beforeContent: text,
      toolBlocks: [],
      afterContent: '',
    };
  }

  const firstTagIndex = text.indexOf(firstTagMatch[0]);

  // 마지막 XML 태그 위치 찾기 (닫는 태그 포함)
  const lastTagMatch = text.match(/.*(<\/[^>]+>|<[^>]*\/>)/);
  let lastTagIndex = text.length;

  if (lastTagMatch) {
    const lastMatch = lastTagMatch[1];
    lastTagIndex = text.lastIndexOf(lastMatch) + lastMatch.length;
  }

  // 전체 툴링 영역을 하나의 블록으로 처리
  const beforeContent = text.slice(0, firstTagIndex).trim();
  const toolContent = text.slice(firstTagIndex, lastTagIndex);
  const afterContent = text.slice(lastTagIndex).trim();

  // 전체 블록에서 도구 사용 횟수 계산
  const toolMatches =
    toolContent.match(/<tool_use>|<WebSearch>|<tool_name>/g) || [];
  const toolCount = Math.max(1, toolMatches.length);

  const toolBlocks = toolContent.trim()
    ? [
        {
          content: toolContent,
          toolCount,
        },
      ]
    : [];

  return {
    beforeContent,
    toolBlocks,
    afterContent,
  };
}

/**
 * 툴 블록 내용을 간단하게 표시 (기존 유지)
 */
function formatToolContent(content: string): React.ReactNode[] {
  // XML 태그를 모두 제거하고 내용만 추출
  const cleanContent = content
    .replace(/<[^>]*>/g, '') // 모든 XML 태그 제거
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0); // 빈 줄 제거

  return cleanContent.map((line, index) => (
    <li key={index} className="text-xs text-neutral-600">
      {line}
    </li>
  ));
}

/**
 * react-markdown 커스텀 컴포넌트 설정 (정확한 타입 적용)
 */
const markdownComponents: Components = {
  // 문단 스타일링
  p: ({ children }) => <div className="mb-4 last:mb-0">{children}</div>,

  // 강조 텍스트 (볼드)
  strong: ({ children }) => (
    <Text as="strong" variant="s2" className="font-bold">
      {children}
    </Text>
  ),

  // 헤딩을 강조 텍스트처럼 처리
  h1: ({ children }) => (
    <Text as="strong" variant="s2" className="font-bold">
      {children}
    </Text>
  ),
  h2: ({ children }) => (
    <Text as="strong" variant="s2" className="font-bold">
      {children}
    </Text>
  ),
  h3: ({ children }) => (
    <Text as="strong" variant="s2" className="font-bold">
      {children}
    </Text>
  ),
  h4: ({ children }) => (
    <Text as="strong" variant="s2" className="font-bold">
      {children}
    </Text>
  ),
  h5: ({ children }) => (
    <Text as="strong" variant="s2" className="font-bold">
      {children}
    </Text>
  ),
  h6: ({ children }) => (
    <Text as="strong" variant="s2" className="font-bold">
      {children}
    </Text>
  ),

  // 순서 없는 리스트 (ul)
  ul: ({ children }) => (
    <ul className="space-y-1 mb-4 ml-4" style={{ listStyleType: 'disc' }}>
      {children}
    </ul>
  ),

  // 순서 있는 리스트 (ol)
  ol: ({ children }) => (
    <ol className="space-y-1 mb-4 ml-4" style={{ listStyleType: 'decimal' }}>
      {children}
    </ol>
  ),

  // 리스트 아이템
  li: ({ children }) => <li>{children}</li>,

  // 구분선
  hr: () => <hr className="my-4 border-neutral-300" />,

  // 코드 블록 (인라인)
  code: ({ children }) => (
    <code className="bg-neutral-100 px-1 py-0.5 rounded text-sm font-mono">
      {children}
    </code>
  ),

  // 링크
  a: ({ href, children }) => (
    <a
      href={href}
      className="text-red-600 underline hover:text-red-700"
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
    </a>
  ),
};

export function FormattedText({ children, className }: FormattedTextProps) {
  // 1. 툴 블록 추출
  const { beforeContent, toolBlocks, afterContent } =
    extractToolBlocks(children);

  return (
    <Text as="div" variant="b2" className={className}>
      {/* 툴 블록 이전 내용 - ReactMarkdown으로 렌더링 */}
      {beforeContent.trim() && (
        <ReactMarkdown components={markdownComponents}>
          {beforeContent}
        </ReactMarkdown>
      )}

      {/* 툴 블록들을 ToolCallSection으로 렌더링 */}
      {toolBlocks.map((block, index) => (
        <ToolCallSection key={`tool-${index}`} toolCount={block.toolCount}>
          {formatToolContent(block.content)}
        </ToolCallSection>
      ))}

      {/* 툴 블록 이후 내용 - ReactMarkdown으로 렌더링 */}
      {afterContent.trim() && (
        <ReactMarkdown components={markdownComponents}>
          {afterContent}
        </ReactMarkdown>
      )}
    </Text>
  );
}
