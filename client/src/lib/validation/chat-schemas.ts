import { z } from 'zod';
import { uuidSchema, titleSchema } from './common-schemas';

// ===== 채팅 메시지 관련 스키마 =====

/**
 * 채팅 메시지 내용 검증
 * 1-10,000자 범위, XSS 방지를 위한 기본 검증
 */
export const messageContentSchema = z
  .string()
  .trim()
  .min(1, '메시지가 비어있습니다.')
  .max(10000, '메시지는 10,000자를 초과할 수 없습니다.')
  .refine(
    (content) => !content.includes('<script'),
    'XSS 공격이 감지되었습니다.'
  )
  .refine(
    (content) => !content.includes('javascript:'),
    '허용되지 않는 스크립트가 포함되어 있습니다.'
  );

/**
 * 모델 설정 검증
 * FastAPI로 전달할 modelConfig 객체
 */
export const modelConfigSchema = z.object({
  // ✅ 채팅 서비스 타입 추가 (핵심 수정사항)
  chat_service_type: z.enum(['ALPHA_AI']).optional(),

  // LLM 제공업체 (선택사항)
  provider: z.enum(['openai', 'anthropic', 'google', 'perplexity']).optional(),

  // 모델명 (선택사항)
  model: z
    .string()
    .min(1, '모델명이 비어있습니다.')
    .max(100, '모델명이 너무 깁니다.')
    .optional(),

  // 온도 설정 (0.0-2.0)
  temperature: z
    .number()
    .min(0.0, '온도는 0.0 이상이어야 합니다.')
    .max(2.0, '온도는 2.0 이하여야 합니다.')
    .optional(),

  // 최대 토큰 수
  maxTokens: z
    .number()
    .int('정수여야 합니다.')
    .min(1, '최소 1개 토큰이 필요합니다.')
    .max(8000, '최대 8000 토큰까지 가능합니다.')
    .optional(),

  // 스트리밍 여부
  stream: z.boolean().optional().default(true),
});

/**
 * 채팅 스트림 요청 검증
 * POST /api/chat/stream 요청 body
 */
export const chatStreamRequestSchema = z.object({
  message: messageContentSchema,
  modelConfig: modelConfigSchema.optional().default({}),
});

/**
 * 채팅 세션 생성 요청 검증
 */
export const createChatSessionSchema = z.object({
  title: titleSchema.optional(),
  initialMessage: messageContentSchema.optional(),
});

/**
 * 채팅 세션 수정 요청 검증
 */
export const updateChatSessionSchema = z.object({
  sessionId: uuidSchema,
  title: titleSchema,
});

/**
 * 채팅 세션 삭제 요청 검증
 */
export const deleteChatSessionSchema = z.object({
  sessionId: uuidSchema,
});

/**
 * 채팅 히스토리 조회 쿼리 파라미터 검증
 */
export const chatHistoryQuerySchema = z.object({
  limit: z
    .string()
    .transform((val) => parseInt(val, 10))
    .pipe(z.number().int().min(1).max(100))
    .optional()
    .default('50'),
  offset: z
    .string()
    .transform((val) => parseInt(val, 10))
    .pipe(z.number().int().min(0))
    .optional()
    .default('0'),
  includeStats: z
    .string()
    .transform((val) => val === 'true')
    .pipe(z.boolean())
    .optional()
    .default('false'),
});

// ===== 타입 추출 =====
export type MessageContent = z.infer<typeof messageContentSchema>;
export type ModelConfig = z.infer<typeof modelConfigSchema>;
export type ChatStreamRequest = z.infer<typeof chatStreamRequestSchema>;
export type CreateChatSession = z.infer<typeof createChatSessionSchema>;
export type UpdateChatSession = z.infer<typeof updateChatSessionSchema>;
export type DeleteChatSession = z.infer<typeof deleteChatSessionSchema>;
export type ChatHistoryQuery = z.infer<typeof chatHistoryQuerySchema>;
