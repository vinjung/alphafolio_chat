import { getCurrentSession } from '@/lib/server/session';
import { getChatHistory } from '@/lib/server/chat-history';
import { ChatInterface } from './_components/chat-interface';
import type { ChatHistoryItem } from '@/lib/server/chat-history';

export default async function ChatWelcomePage() {
  // 세션 체크 (리다이렉트 없음)
  const { user } = await getCurrentSession();

  // 로그인된 사용자만 채팅 히스토리 로드
  let chatHistory: ChatHistoryItem[] = [];
  if (user) {
    try {
      chatHistory = await getChatHistory(user.id, 30); // 최근 30개만
    } catch (error) {
      console.error('서버에서 채팅 히스토리 로드 실패:', error);
      // 실패해도 빈 배열로 계속 진행
    }
  }

  return (
    <ChatInterface
      chatId="welcome"
      isWelcomeMode={true}
      userNickname={user?.nickname || '떡상러'} // 비회원은 기본 닉네임
      preloadedChatHistory={chatHistory} // 비회원은 빈 배열
    />
  );
}
