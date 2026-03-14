/**
 * 채팅 히스토리용 날짜 포맷팅 유틸리티
 */

// 시간 단위 타입 정의
export type TimeUnit =
  | 'second'
  | 'minute'
  | 'hour'
  | 'day'
  | 'week'
  | 'month'
  | 'year';

// 상대적 시간 결과 타입
export interface RelativeTimeResult {
  text: string; // "1분 전", "어제" 등
  unit: TimeUnit; // 계산된 시간 단위
  value: number; // 실제 숫자 값
  isToday: boolean; // 오늘인지 여부
  isYesterday: boolean; // 어제인지 여부
}

// 그룹핑용 날짜 섹션 타입
export type DateSection =
  | 'today'
  | 'yesterday'
  | 'thisWeek'
  | 'lastWeek'
  | 'thisMonth'
  | 'older';

/**
 * 날짜를 상대적 시간으로 포맷팅
 */
export function formatRelativeTime(
  date: Date | string | number
): RelativeTimeResult {
  const now = new Date();
  const targetDate = new Date(date);

  // 유효성 검사
  if (isNaN(targetDate.getTime())) {
    return {
      text: '알 수 없음',
      unit: 'day',
      value: 0,
      isToday: false,
      isYesterday: false,
    };
  }

  const diffMs = now.getTime() - targetDate.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  const diffWeeks = Math.floor(diffDays / 7);
  const diffMonths = Math.floor(diffDays / 30);
  const diffYears = Math.floor(diffDays / 365);

  // 날짜 비교용
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const targetDay = new Date(
    targetDate.getFullYear(),
    targetDate.getMonth(),
    targetDate.getDate()
  );

  const isToday = targetDay.getTime() === today.getTime();
  const isYesterday = targetDay.getTime() === yesterday.getTime();

  // 미래 날짜 처리
  if (diffMs < 0) {
    return {
      text: '미래',
      unit: 'day',
      value: 0,
      isToday: false,
      isYesterday: false,
    };
  }

  // 오늘인 경우 - 시간 단위로 표시
  if (isToday) {
    if (diffSeconds < 60) {
      return {
        text: diffSeconds <= 5 ? '방금 전' : `${diffSeconds}초 전`,
        unit: 'second',
        value: diffSeconds,
        isToday: true,
        isYesterday: false,
      };
    }

    if (diffMinutes < 60) {
      return {
        text: `${diffMinutes}분 전`,
        unit: 'minute',
        value: diffMinutes,
        isToday: true,
        isYesterday: false,
      };
    }

    return {
      text: `${diffHours}시간 전`,
      unit: 'hour',
      value: diffHours,
      isToday: true,
      isYesterday: false,
    };
  }

  // 어제인 경우
  if (isYesterday) {
    return {
      text: '어제',
      unit: 'day',
      value: 1,
      isToday: false,
      isYesterday: true,
    };
  }

  // 1주일 이내
  if (diffDays < 7) {
    return {
      text: `${diffDays}일 전`,
      unit: 'day',
      value: diffDays,
      isToday: false,
      isYesterday: false,
    };
  }

  // 1개월 이내 (주 단위)
  if (diffDays < 30) {
    return {
      text: `${diffWeeks}주 전`,
      unit: 'week',
      value: diffWeeks,
      isToday: false,
      isYesterday: false,
    };
  }

  // 1년 이내 (월 단위)
  if (diffDays < 365) {
    return {
      text: `${diffMonths}개월 전`,
      unit: 'month',
      value: diffMonths,
      isToday: false,
      isYesterday: false,
    };
  }

  // 1년 이상
  return {
    text: `${diffYears}년 전`,
    unit: 'year',
    value: diffYears,
    isToday: false,
    isYesterday: false,
  };
}

/**
 * 날짜를 섹션별로 그룹핑하기 위한 섹션 결정
 */
export function getDateSection(date: Date | string | number): DateSection {
  const result = formatRelativeTime(date);

  if (result.isToday) return 'today';
  if (result.isYesterday) return 'yesterday';

  if (result.unit === 'day' && result.value <= 7) return 'thisWeek';
  if (result.unit === 'week' && result.value <= 4) return 'lastWeek';
  if (result.unit === 'month' && result.value <= 12) return 'thisMonth';

  return 'older';
}

/**
 * 섹션 이름을 한국어로 변환
 */
export function getSectionLabel(section: DateSection): string {
  const labels: Record<DateSection, string> = {
    today: '오늘',
    yesterday: '어제',
    thisWeek: '이번 주',
    lastWeek: '지난 주',
    thisMonth: '이번 달',
    older: '이전',
  };

  return labels[section];
}

/**
 * 채팅 히스토리 아이템용 인터페이스
 */
export interface ChatHistoryItem {
  id: string;
  title: string;
  lastMessage: string;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * 채팅 히스토리를 날짜별로 그룹핑
 */
export function groupChatHistoryByDate(items: ChatHistoryItem[]) {
  const groups: Record<DateSection, ChatHistoryItem[]> = {
    today: [],
    yesterday: [],
    thisWeek: [],
    lastWeek: [],
    thisMonth: [],
    older: [],
  };

  // 최신순으로 정렬 후 그룹핑
  const sortedItems = [...items].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  );

  sortedItems.forEach((item) => {
    const section = getDateSection(item.updatedAt);
    groups[section].push(item);
  });

  // 빈 그룹 제거하고 순서대로 반환
  const result: Array<{
    section: DateSection;
    label: string;
    items: ChatHistoryItem[];
  }> = [];

  (
    [
      'today',
      'yesterday',
      'thisWeek',
      'lastWeek',
      'thisMonth',
      'older',
    ] as DateSection[]
  ).forEach((section) => {
    if (groups[section].length > 0) {
      result.push({
        section,
        label: getSectionLabel(section),
        items: groups[section],
      });
    }
  });

  return result;
}

/**
 * 간단한 날짜 포맷팅 (채팅 메시지 타임스탬프용)
 */
export function formatMessageTime(date: Date | string | number): string {
  const targetDate = new Date(date);

  if (isNaN(targetDate.getTime())) {
    return '';
  }

  const hours = targetDate.getHours();
  const minutes = targetDate.getMinutes();
  const period = hours >= 12 ? '오후' : '오전';
  const displayHours = hours % 12 || 12;

  return `${period} ${displayHours}:${minutes.toString().padStart(2, '0')}`;
}
