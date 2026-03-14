import { db } from '@/lib/server/db';
import { chatSessions, chatMessages } from '@schema';
import { desc, eq, and, or, ilike, sql, max } from 'drizzle-orm';
import { logger } from '@/lib/utils/logger';
import type { ChatSession, ChatMessage } from '@/lib/server/models';

export interface ChatHistoryItem {
  id: string;
  title: string;
  lastMessage: string; // 계산된 필드
  createdAt: Date;
  updatedAt: Date;
}

/**
 * JOIN 방식 - 전체 텍스트 검색 (제목 + 모든 메시지 내용)
 */
export async function searchChatHistoryFullText(
  userId: string,
  options: {
    query: string;
    limit: number;
    offset: number;
  }
): Promise<ChatHistoryItem[]> {
  const { query, limit, offset } = options;
  const log = logger.child({
    module: 'chat-history',
    function: 'searchChatHistoryFullText',
    userId: userId.slice(0, 8) + '...',
  });

  try {
    log.info('전체 텍스트 검색 시작 (JOIN 방식)', { query, limit, offset });

    // 마지막 메시지 시간 서브쿼리
    const lastMessageTimeSubquery = db
      .select({
        sessionId: chatMessages.sessionId,
        maxCreatedAt: max(chatMessages.createdAt).as('maxCreatedAt'),
      })
      .from(chatMessages)
      .groupBy(chatMessages.sessionId)
      .as('lastMessageTime');

    // 검색 조건에 맞는 세션 찾기
    const result = await db
      .select({
        id: chatSessions.id,
        title: chatSessions.title,
        createdAt: chatSessions.createdAt,
        updatedAt: chatSessions.updatedAt,
        lastMessage: sql<string | null>`${chatMessages.content}`.as(
          'lastMessage'
        ),
      })
      .from(chatSessions)
      .leftJoin(
        lastMessageTimeSubquery,
        eq(chatSessions.id, lastMessageTimeSubquery.sessionId)
      )
      .leftJoin(
        chatMessages,
        and(
          eq(chatMessages.sessionId, chatSessions.id),
          eq(chatMessages.createdAt, lastMessageTimeSubquery.maxCreatedAt)
        )
      )
      .where(
        and(
          eq(chatSessions.userId, userId),
          or(
            // 제목에서 검색
            ilike(chatSessions.title, `%${query}%`),
            // 해당 세션의 모든 메시지에서 검색
            sql`EXISTS (
              SELECT 1 FROM chat_messages cm
              WHERE cm.session_id = ${chatSessions.id}
              AND cm.content ILIKE ${'%' + query + '%'}
            )`
          )
        )
      )
      .orderBy(desc(chatSessions.updatedAt))
      .limit(limit)
      .offset(offset);

    log.info('전체 텍스트 검색 완료', { resultCount: result.length });

    return result.map((session): ChatHistoryItem => {
      const hasValidMessage =
        session.lastMessage !== null &&
        session.lastMessage !== undefined &&
        typeof session.lastMessage === 'string' &&
        session.lastMessage.trim().length > 0;

      return {
        id: session.id,
        title: session.title || '제목 없음',
        lastMessage: hasValidMessage
          ? session.lastMessage!
          : '메시지가 없습니다',
        createdAt: session.createdAt,
        updatedAt: session.updatedAt,
      };
    });
  } catch (error) {
    log.error('전체 텍스트 채팅 히스토리 검색 실패', error);
    throw new Error('채팅 히스토리 검색에 실패했습니다.');
  }
}

/**
 * JOIN 방식 - 검색어를 포함한 채팅 히스토리 조회
 */
export async function searchChatHistory(
  userId: string,
  options: {
    query: string;
    limit: number;
    offset: number;
  }
): Promise<ChatHistoryItem[]> {
  const { query, limit, offset } = options;
  const log = logger.child({
    module: 'chat-history',
    function: 'searchChatHistory',
    userId: userId.slice(0, 8) + '...',
  });

  try {
    log.info('채팅 히스토리 검색 시작 (JOIN 방식)', { query, limit, offset });

    // 마지막 메시지 시간 서브쿼리
    const lastMessageTimeSubquery = db
      .select({
        sessionId: chatMessages.sessionId,
        maxCreatedAt: max(chatMessages.createdAt).as('maxCreatedAt'),
      })
      .from(chatMessages)
      .groupBy(chatMessages.sessionId)
      .as('lastMessageTime');

    const result = await db
      .select({
        id: chatSessions.id,
        title: chatSessions.title,
        createdAt: chatSessions.createdAt,
        updatedAt: chatSessions.updatedAt,
        lastMessage: sql<string | null>`${chatMessages.content}`.as(
          'lastMessage'
        ),
      })
      .from(chatSessions)
      .leftJoin(
        lastMessageTimeSubquery,
        eq(chatSessions.id, lastMessageTimeSubquery.sessionId)
      )
      .leftJoin(
        chatMessages,
        and(
          eq(chatMessages.sessionId, chatSessions.id),
          eq(chatMessages.createdAt, lastMessageTimeSubquery.maxCreatedAt)
        )
      )
      .where(
        and(
          eq(chatSessions.userId, userId),
          or(
            // 제목에서 검색 (대소문자 구분 없음)
            ilike(chatSessions.title, `%${query}%`),
            // 해당 세션의 메시지에서 검색
            sql`EXISTS (
              SELECT 1 FROM chat_messages cm
              WHERE cm.session_id = ${chatSessions.id}
              AND cm.content ILIKE ${'%' + query + '%'}
            )`
          )
        )
      )
      .orderBy(desc(chatSessions.updatedAt))
      .limit(limit)
      .offset(offset);

    log.info('채팅 히스토리 검색 완료', { resultCount: result.length });

    return result.map((session): ChatHistoryItem => {
      const hasValidMessage =
        session.lastMessage !== null &&
        session.lastMessage !== undefined &&
        typeof session.lastMessage === 'string' &&
        session.lastMessage.trim().length > 0;

      return {
        id: session.id,
        title: session.title || '제목 없음',
        lastMessage: hasValidMessage
          ? session.lastMessage!
          : '메시지가 없습니다',
        createdAt: session.createdAt,
        updatedAt: session.updatedAt,
      };
    });
  } catch (error) {
    log.error('채팅 히스토리 검색 실패', error);
    throw new Error('채팅 히스토리 검색에 실패했습니다.');
  }
}

/**
 * 검색 결과 통계 조회
 */
export async function getSearchStats(
  userId: string,
  query: string
): Promise<{
  totalResults: number;
  searchQuery: string;
}> {
  const log = logger.child({
    module: 'chat-history',
    function: 'getSearchStats',
    userId: userId.slice(0, 8) + '...',
  });

  try {
    log.debug('검색 통계 조회 시작', { query });

    const [countResult] = await db
      .select({
        count: sql<number>`count(*)`.as('count'),
      })
      .from(chatSessions)
      .where(
        and(
          eq(chatSessions.userId, userId),
          or(
            ilike(chatSessions.title, `%${query}%`),
            sql`EXISTS (
              SELECT 1 FROM chat_messages cm
              WHERE cm.session_id = ${chatSessions.id}
              AND cm.content ILIKE ${'%' + query + '%'}
            )`
          )
        )
      );

    const totalResults = countResult?.count || 0;
    log.debug('검색 통계 조회 완료', { totalResults });

    return {
      totalResults,
      searchQuery: query,
    };
  } catch (error) {
    log.error('검색 통계 조회 실패', error);
    return {
      totalResults: 0,
      searchQuery: query,
    };
  }
}

/**
 * 특정 채팅 세션의 모든 메시지 조회
 * @param sessionId - 채팅 세션 ID
 * @param userId - 사용자 ID (권한 확인용)
 * @returns 메시지 목록
 */
export async function getChatMessages(
  sessionId: string,
  userId: string
): Promise<ChatMessage[]> {
  const log = logger.child({
    module: 'chat-history',
    function: 'getChatMessages',
    sessionId: sessionId.slice(0, 8) + '...',
    userId: userId.slice(0, 8) + '...',
  });

  try {
    log.info('채팅 메시지 조회 시작');

    // 세션 소유권 확인
    const session = await db
      .select({ id: chatSessions.id })
      .from(chatSessions)
      .where(
        and(eq(chatSessions.id, sessionId), eq(chatSessions.userId, userId))
      )
      .limit(1);

    if (session.length === 0) {
      log.warn('세션 접근 권한 없음 또는 세션 없음');
      throw new Error('채팅 세션을 찾을 수 없거나 접근 권한이 없습니다.');
    }

    // 메시지 조회 (시간순 정렬)
    const messages = await db
      .select()
      .from(chatMessages)
      .where(eq(chatMessages.sessionId, sessionId))
      .orderBy(chatMessages.createdAt);

    log.info('채팅 메시지 조회 완료', { messageCount: messages.length });

    return messages;
  } catch (error) {
    log.error('채팅 메시지 조회 실패', error);
    throw error;
  }
}

/**
 * 채팅 세션에 새 메시지 추가
 * @param sessionId - 채팅 세션 ID
 * @param role - 메시지 역할 ('user' | 'assistant')
 * @param content - 메시지 내용
 * @param userId - 사용자 ID (권한 확인용)
 * @returns 생성된 메시지 정보
 */
export async function addChatMessage(
  sessionId: string,
  role: 'user' | 'assistant',
  content: string,
  userId: string
): Promise<ChatMessage> {
  const log = logger.child({
    module: 'chat-history',
    function: 'addChatMessage',
    sessionId: sessionId.slice(0, 8) + '...',
    userId: userId.slice(0, 8) + '...',
  });

  try {
    log.info('메시지 추가 시작', {
      role,
      contentLength: content.length,
      contentPreview: content.slice(0, 50) + (content.length > 50 ? '...' : ''),
    });

    // 세션 소유권 확인
    const session = await db
      .select({ id: chatSessions.id })
      .from(chatSessions)
      .where(
        and(eq(chatSessions.id, sessionId), eq(chatSessions.userId, userId))
      )
      .limit(1);

    if (session.length === 0) {
      log.warn('메시지 추가 권한 없음 또는 세션 없음');
      throw new Error('채팅 세션을 찾을 수 없거나 접근 권한이 없습니다.');
    }

    // 메시지 추가 (트리거가 자동으로 세션 업데이트)
    const [newMessage] = await db
      .insert(chatMessages)
      .values({
        sessionId,
        role,
        content,
        createdAt: new Date(),
      })
      .returning();

    if (!newMessage) {
      log.error('메시지 추가 실패 - returning 결과 없음');
      throw new Error('메시지 추가에 실패했습니다.');
    }

    log.info('메시지 추가 완료', { messageId: newMessage.id });

    return newMessage;
  } catch (error) {
    log.error('메시지 추가 실패', error);
    throw error;
  }
}

/**
 * 채팅 세션 제목 업데이트
 * @param sessionId - 채팅 세션 ID
 * @param title - 새 제목
 * @param userId - 사용자 ID (권한 확인용)
 */
export async function updateChatSessionTitle(
  sessionId: string,
  title: string,
  userId: string
): Promise<void> {
  const log = logger.child({
    module: 'chat-history',
    function: 'updateChatSessionTitle',
    sessionId: sessionId.slice(0, 8) + '...',
    userId: userId.slice(0, 8) + '...',
  });

  try {
    log.info('채팅 세션 제목 업데이트 시작', { title });

    // returning()을 사용해서 업데이트된 행 확인
    const result = await db
      .update(chatSessions)
      .set({
        title: title.slice(0, 200),
        updatedAt: new Date(),
      })
      .where(
        and(eq(chatSessions.id, sessionId), eq(chatSessions.userId, userId))
      )
      .returning({ id: chatSessions.id });

    // 업데이트된 행이 없으면 권한 없음 또는 세션 없음
    if (result.length === 0) {
      log.warn('제목 업데이트 권한 없음 또는 세션 없음');
      throw new Error('채팅 세션을 찾을 수 없거나 접근 권한이 없습니다.');
    }

    log.info('채팅 세션 제목 업데이트 완료');
  } catch (error) {
    log.error('채팅 세션 제목 업데이트 실패', error);
    throw error;
  }
}

/**
 * 채팅 세션 삭제
 * @param sessionId - 채팅 세션 ID
 * @param userId - 사용자 ID (권한 확인용)
 */
export async function deleteChatSession(
  sessionId: string,
  userId: string
): Promise<void> {
  const log = logger.child({
    module: 'chat-history',
    function: 'deleteChatSession',
    sessionId: sessionId.slice(0, 8) + '...',
    userId: userId.slice(0, 8) + '...',
  });

  try {
    log.info('채팅 세션 삭제 시작');

    // returning()을 사용해서 삭제된 행 확인
    const result = await db
      .delete(chatSessions)
      .where(
        and(eq(chatSessions.id, sessionId), eq(chatSessions.userId, userId))
      )
      .returning({ id: chatSessions.id });

    if (result.length === 0) {
      log.warn('세션 삭제 권한 없음 또는 세션 없음');
      throw new Error('채팅 세션을 찾을 수 없거나 접근 권한이 없습니다.');
    }

    log.info('채팅 세션 삭제 완료');
  } catch (error) {
    log.error('채팅 세션 삭제 실패', error);
    throw error;
  }
}

/**
 * 사용자의 채팅 통계 조회
 * @param userId - 사용자 ID
 * @returns 통계 정보
 */
export async function getChatStats(userId: string) {
  const log = logger.child({
    module: 'chat-history',
    function: 'getChatStats',
    userId: userId.slice(0, 8) + '...',
  });

  try {
    log.debug('채팅 통계 조회 시작');

    const [stats] = await db
      .select({
        totalSessions: sql<number>`COUNT(*)`,
        totalMessages: sql<number>`SUM(${chatSessions.messageCount})`,
        latestSessionDate: sql<Date>`MAX(${chatSessions.updatedAt})`,
      })
      .from(chatSessions)
      .where(eq(chatSessions.userId, userId));

    const result = {
      totalSessions: Number(stats?.totalSessions || 0),
      totalMessages: Number(stats?.totalMessages || 0),
      latestSessionDate: stats?.latestSessionDate || null,
    };

    log.debug('채팅 통계 조회 완료', result);

    return result;
  } catch (error) {
    log.error('채팅 통계 조회 실패', error);
    return {
      totalSessions: 0,
      totalMessages: 0,
      latestSessionDate: null,
    };
  }
}
// ✅ 수정된 함수들만 추가/변경
// 기존 타입 정의들은 그대로 유지...

/**
 * ✅ 새 함수: 특정 모델의 최근 채팅 세션 조회
 * @param userId - 사용자 ID
 * @param modelId - 모델 ID (예: 'stock-ai', 'brain-ai')
 * @returns 해당 모델의 최근 세션 정보 (없으면 null)
 */
export async function getLatestSessionByModel(
  userId: string,
  modelId: string
): Promise<ChatSession | null> {
  const log = logger.child({
    module: 'chat-history',
    function: 'getLatestSessionByModel',
    userId: userId.slice(0, 8) + '...',
    modelId,
  });

  try {
    log.info('모델별 최근 세션 조회 시작');

    const sessions = await db
      .select()
      .from(chatSessions)
      .where(
        and(eq(chatSessions.userId, userId), eq(chatSessions.modelId, modelId))
      )
      .orderBy(desc(chatSessions.updatedAt))
      .limit(1);

    const latestSession = sessions[0] || null;
    log.info('모델별 최근 세션 조회 완료', {
      found: !!latestSession,
      sessionId: latestSession?.id?.slice(0, 8) + '...' || 'none',
    });

    return latestSession;
  } catch (error) {
    log.error('모델별 최근 세션 조회 실패', error);
    return null;
  }
}

/**
 * ✅ 수정된 함수: 새 채팅 세션 생성 (modelId 추가)
 * @param userId - 사용자 ID
 * @param title - 채팅 제목
 * @param modelId - 모델 ID (기본값: 'stock-ai')
 * @returns 생성된 세션 정보
 */
export async function createChatSession(
  userId: string,
  title: string,
  modelId: string = 'stock-ai'
): Promise<ChatSession> {
  const log = logger.child({
    module: 'chat-history',
    function: 'createChatSession',
    userId: userId.slice(0, 8) + '...',
    modelId,
  });

  try {
    log.info('채팅 세션 생성 시작', { title, modelId });

    const [newSession] = await db
      .insert(chatSessions)
      .values({
        userId,
        title: title.slice(0, 200), // 제목 길이 제한
        modelId, // ✅ 모델 ID 추가
        createdAt: new Date(),
        updatedAt: new Date(),
        messageCount: 0,
      })
      .returning();

    if (!newSession) {
      log.error('채팅 세션 생성 실패 - returning 결과 없음');
      throw new Error('채팅 세션 생성에 실패했습니다.');
    }

    log.info('채팅 세션 생성 완료', {
      sessionId: newSession.id,
      modelId: newSession.modelId,
    });

    return newSession;
  } catch (error) {
    log.error('채팅 세션 생성 실패', error);
    throw new Error('채팅 세션 생성에 실패했습니다.');
  }
}

/**
 * ✅ 수정된 함수: 사용자의 채팅 히스토리 목록 조회 (모델별 필터링 추가)
 * @param userId - 사용자 ID
 * @param limit - 조회할 개수 (기본값: 50)
 * @param offset - 건너뛸 개수 (기본값: 0)
 * @param modelId - 모델별 필터링 (선택사항)
 * @returns 채팅 히스토리 목록
 */
export async function getChatHistory(
  userId: string,
  limit: number = 50,
  offset: number = 0,
  modelId?: string // ✅ 모델별 필터링 옵션 추가
): Promise<ChatHistoryItem[]> {
  const log = logger.child({
    module: 'chat-history',
    function: 'getChatHistory',
    userId: userId.slice(0, 8) + '...',
    modelId: modelId || 'all',
  });

  log.info('채팅 히스토리 조회 시작', { limit, offset, modelId });

  try {
    // 1단계: 각 세션의 마지막 메시지 시간 찾기 (서브쿼리)
    const lastMessageTimeSubquery = db
      .select({
        sessionId: chatMessages.sessionId,
        maxCreatedAt: max(chatMessages.createdAt).as('maxCreatedAt'),
      })
      .from(chatMessages)
      .groupBy(chatMessages.sessionId)
      .as('lastMessageTime');

    // ✅ 2단계: WHERE 조건 구성 (모델별 필터링 포함)
    const whereConditions = modelId
      ? and(eq(chatSessions.userId, userId), eq(chatSessions.modelId, modelId))
      : eq(chatSessions.userId, userId);

    // 3단계: 메인 쿼리 - 세션과 마지막 메시지 JOIN
    const result = await db
      .select({
        id: chatSessions.id,
        title: chatSessions.title,
        createdAt: chatSessions.createdAt,
        updatedAt: chatSessions.updatedAt,
        modelId: chatSessions.modelId, // ✅ 모델 ID도 포함
        lastMessage: sql<string | null>`${chatMessages.content}`.as(
          'lastMessage'
        ),
      })
      .from(chatSessions)
      .leftJoin(
        lastMessageTimeSubquery,
        eq(chatSessions.id, lastMessageTimeSubquery.sessionId)
      )
      .leftJoin(
        chatMessages,
        and(
          eq(chatMessages.sessionId, chatSessions.id),
          eq(chatMessages.createdAt, lastMessageTimeSubquery.maxCreatedAt)
        )
      )
      .where(whereConditions) // ✅ 모델별 필터링 적용
      .orderBy(desc(chatSessions.updatedAt))
      .limit(Math.min(limit, 100))
      .offset(Math.max(offset, 0));

    log.info('채팅 히스토리 JOIN 쿼리 완료', {
      resultCount: result.length,
      modelFilter: modelId || 'none',
    });

    // 결과 매핑
    return result.map((session) => {
      return {
        id: session.id,
        title: session.title,
        lastMessage: session.lastMessage
          ? session.lastMessage.slice(0, 100) +
            (session.lastMessage.length > 100 ? '...' : '')
          : '메시지가 없습니다',
        createdAt: session.createdAt,
        updatedAt: session.updatedAt,
      };
    });
  } catch (error) {
    log.error('채팅 히스토리 검색 실패', error);
    throw new Error('채팅 히스토리 검색에 실패했습니다.');
  }
}

/**
 * ✅ 새 함수: 모델별 채팅 세션 개수 조회
 * @param userId - 사용자 ID
 * @param modelId - 모델 ID
 * @returns 해당 모델의 세션 개수
 */
export async function getSessionCountByModel(
  userId: string,
  modelId: string
): Promise<number> {
  const log = logger.child({
    module: 'chat-history',
    function: 'getSessionCountByModel',
    userId: userId.slice(0, 8) + '...',
    modelId,
  });

  try {
    log.debug('모델별 세션 개수 조회 시작');

    const [countResult] = await db
      .select({
        count: sql<number>`count(*)`.as('count'),
      })
      .from(chatSessions)
      .where(
        and(eq(chatSessions.userId, userId), eq(chatSessions.modelId, modelId))
      );

    const sessionCount = countResult?.count || 0;
    log.debug('모델별 세션 개수 조회 완료', { sessionCount });

    return sessionCount;
  } catch (error) {
    log.error('모델별 세션 개수 조회 실패', error);
    return 0;
  }
}

/**
 * ✅ 새 함수: 특정 채팅 세션 정보 조회 (권한 확인 포함)
 * @param sessionId - 채팅 세션 ID
 * @param userId - 사용자 ID (권한 확인용)
 * @returns 세션 정보 (modelId 포함)
 */
export async function getChatSession(
  sessionId: string,
  userId: string
): Promise<ChatSession | null> {
  const log = logger.child({
    module: 'chat-history',
    function: 'getChatSession',
    sessionId: sessionId.slice(0, 8) + '...',
    userId: userId.slice(0, 8) + '...',
  });

  try {
    log.info('채팅 세션 정보 조회 시작');

    // 세션 소유권 확인 및 정보 조회
    const sessions = await db
      .select({
        id: chatSessions.id,
        title: chatSessions.title,
        modelId: chatSessions.modelId, // ✅ modelId 포함
        userId: chatSessions.userId,
        createdAt: chatSessions.createdAt,
        updatedAt: chatSessions.updatedAt,
        messageCount: chatSessions.messageCount,
      })
      .from(chatSessions)
      .where(
        and(eq(chatSessions.id, sessionId), eq(chatSessions.userId, userId))
      )
      .limit(1);

    if (sessions.length === 0) {
      log.warn('세션 접근 권한 없음 또는 세션 없음');
      return null;
    }

    const session = sessions[0];
    log.info('채팅 세션 정보 조회 완료', {
      sessionId: session.id,
      modelId: session.modelId,
      title: session.title.slice(0, 30),
      messageCount: session.messageCount,
    });

    return session;
  } catch (error) {
    log.error('채팅 세션 정보 조회 실패', error);
    return null;
  }
}

/**
 * ✅ 새 함수: 메시지와 세션 정보를 함께 조회
 * @param sessionId - 채팅 세션 ID
 * @param userId - 사용자 ID (권한 확인용)
 * @returns 세션 정보 + 메시지 목록
 */
export async function getChatSessionWithMessages(
  sessionId: string,
  userId: string
): Promise<{
  session: ChatSession | null;
  messages: ChatMessage[];
}> {
  const log = logger.child({
    module: 'chat-history',
    function: 'getChatSessionWithMessages',
    sessionId: sessionId.slice(0, 8) + '...',
    userId: userId.slice(0, 8) + '...',
  });

  try {
    log.info('세션+메시지 통합 조회 시작');

    // 1. 세션 정보 조회 (권한 확인 포함)
    const session = await getChatSession(sessionId, userId);

    if (!session) {
      log.warn('세션 정보 없음 - 메시지 조회 건너뜀');
      return {
        session: null,
        messages: [],
      };
    }

    // 2. 메시지 조회 (세션이 존재하므로 권한 확인 완료)
    const messages = await db
      .select()
      .from(chatMessages)
      .where(eq(chatMessages.sessionId, sessionId))
      .orderBy(chatMessages.createdAt);

    log.info('세션+메시지 통합 조회 완료', {
      sessionId: session.id,
      modelId: session.modelId,
      messageCount: messages.length,
    });

    return {
      session,
      messages,
    };
  } catch (error) {
    log.error('세션+메시지 통합 조회 실패', error);
    return {
      session: null,
      messages: [],
    };
  }
}
