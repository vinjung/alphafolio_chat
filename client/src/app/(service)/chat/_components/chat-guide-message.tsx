'use client';
import { Button } from '@/components/shared/button';
import { Text } from '@/components/shared/text';

export type GuideMessageType =
  | 'limit-reached' // 한도 완전 소진
  | 'limit-warning' // 1회 남음 경고
  | 'request-failed' // 요청 실패 (재시도)
  | 'stream-interrupted'; // 스트리밍 중단 (재개)

interface GuideMessageConfig {
  content: string;
  extra?: string;
  contentColor: string;
  extraColor?: string;
  actionButton?: {
    text: string;
    variant: 'gradient';
    className?: string;
  };
}

interface ChatGuideMessageProps {
  type: GuideMessageType;
  onRetry?: () => void;
  onNavigateToStocks?: () => void;
  className?: string;
  customMessage?: string; // 동적 에러 메시지 지원
  guideMessageConfig?: {
    type: GuideMessageType;
    props: {
      onRetry?: () => void;
      onNavigateToStocks?: () => void;
    };
    customMessage?: string;
  };
}

const MESSAGE_CONFIGS: Record<GuideMessageType, GuideMessageConfig> = {
  'limit-reached': {
    content:
      '⚠ 오늘의 떡상 기회를 모두 사용 완료하였습니다. \n 내일 자정(00:00)에 사용 가능합니다.',
    contentColor: 'text-red-900',
    actionButton: {
      text: '떡상 종목 보러 가기',
      variant: 'gradient',
    },
  },
  'limit-warning': {
    content: '🔥 오늘의 마지막 떡상 기회! 가장 중요한 질문을 해보세요.',
    contentColor: 'text-red-900',
  },
  'request-failed': {
    content:
      '인터넷이 잠깐 삐졌나 봐요💔 \n 연결 확인하고 다시 와주세요. \n\n 계속 안 되면 잠깐 쉬었다가 다시 접속해 주세요!',
    // extra:
    //   '연결 확인하고 다시 와주세요. 계속 안 되면 잠깐 쉬었다가 다시 접속해 주세요!',
    contentColor: 'text-neutral-1100',
    actionButton: {
      text: '다시 시도하기',
      variant: 'gradient',
    },
  },
  'stream-interrupted': {
    content: '잠깐 멍~ 때렸어요 🫠 \n 자꾸 이러면 아래 이메일로 찔러주세요! \n',
    extra: 'cleverage426@gmail.com',
    contentColor: 'text-neutral-1100',
    extraColor: 'text-blue-900',
    actionButton: {
      text: '응답 다시 생성하기',
      variant: 'gradient',
      className: 'bg-blue-500 hover:bg-blue-600 text-white',
    },
  },
};

export function ChatGuideMessage({
  type,
  onRetry,
  onNavigateToStocks,
  className = '',
  customMessage,
  guideMessageConfig,
}: ChatGuideMessageProps) {
  const config = MESSAGE_CONFIGS[type];

  // 가이드 메시지 설정에서 customMessage 추출
  const configCustomMessage = guideMessageConfig?.customMessage;

  // 동적 메시지 우선순위: 가이드 설정 > 개별 prop > 기본 메시지
  const displayMessage = configCustomMessage || customMessage || config.content;

  const handleActionClick = () => {
    if (type === 'limit-reached' && onNavigateToStocks) {
      onNavigateToStocks();
    } else if (onRetry) {
      onRetry();
    }
  };

  return (
    <div className={`px-4 py-3 ${className}`}>
      <div
        className={`flex flex-col items-start gap-3 p-4 rounded-lg border bg-red-50 border-red-900`}
      >
        {/* 텍스트 영역 */}
        <div className="flex-1">
          <Text
            variant="b1"
            className={`whitespace-pre-line ${config.contentColor}`}
          >
            {displayMessage}
          </Text>

          {config.extra && (
            <Text
              variant="b1"
              className={`whitespace-pre-line mt-4 ${config.extraColor}`}
            >
              {config.extra}
            </Text>
          )}
        </div>
        {/* 액션 버튼 */}
        {config.actionButton && (
          <Button
            onClick={handleActionClick}
            className={`w-full max-h-12 text-s1 ${config.actionButton.className}`}
            variant={config.actionButton.variant}
          >
            {config.actionButton.text}
          </Button>
        )}
      </div>
    </div>
  );
}
