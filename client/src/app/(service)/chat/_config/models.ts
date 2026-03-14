export interface AIModel {
  id: string;
  name: string;
  description: string;
  welcomeMessage: {
    title: string;
    content: string;
  };
  apiConfig: {
    chat_service_type: 'ALPHA_AI';
    provider: 'anthropic' | 'openai' | 'google' | 'perplexity';
    model: string;
  };
}

// API 설정 타입 별도 정의 (재사용을 위해)
export interface ModelApiConfig {
  chat_service_type: 'ALPHA_AI';
  provider: 'anthropic' | 'openai' | 'google' | 'perplexity';
  model: string;
}

// AI 모델 기본 정보 (API 매핑 포함)
const BASE_MODELS = [
  {
    id: 'stock-ai',
    name: '주식 AI',
    description: '데이터 기반 쉽고 똑똑한 투자 분석',
    apiConfig: {
      chat_service_type: 'ALPHA_AI' as const,
      provider: 'anthropic' as const,
      model: 'claude-sonnet-4-6',
    },
  },
] as const;

// 개인화된 웰컴 메시지 생성 (웰컴 화면용)
export function createPersonalizedModels(nickname: string): AIModel[] {
  return [
    {
      ...BASE_MODELS[0],
      welcomeMessage: {
        title: `**안녕하세요 ${nickname}님👋🏻** \n \n **주식 궁금한 거, 뭐든지 편하게 물어보셔요!**`,
        content: `떡상에서 제공하는 답변은 참고용이며, 투자는 개인의 판단하에 결정하시기 바랍니다. \n
        \n 🏷️ 이렇게 질문해 볼 수 있어요
        \n 1. 안전하게 투자하고 싶어요. 리스크가 적은 우량주 추천해주세요
        \n 2. 애플 주식 어떻게 생각해?
        \n 3. 분산투자가 뭐든지 쉽게 설명해 주세요`,
      },
    },
  ];
}
