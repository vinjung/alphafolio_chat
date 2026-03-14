// client/src/types/chat.d.ts

import type { VisualizationData } from './chart';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: Date;
  isStreaming?: boolean;
  isError?: boolean;
  visualization?: VisualizationData;
}
