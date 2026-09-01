import { apiClient, API_BASE_URL } from './client';
import {
  NaturalLanguageExtractRequest,
  NaturalLanguageExtractResponse,
  ClarificationRequest,
  ClarificationResponse,
  AIExplainableRecommendationRequest,
  AIExplainableRecommendationResponse,
  AIChatRequest,
  AIChatResponse,
} from '../types';

export const aiApi = {
  extractProfile: async (user_text: string): Promise<NaturalLanguageExtractResponse> => {
    const res = await apiClient.post<NaturalLanguageExtractResponse>('/ai/profile/extract', { user_text });
    return res.data;
  },

  getClarifications: async (req: ClarificationRequest): Promise<ClarificationResponse> => {
    const res = await apiClient.post<ClarificationResponse>('/ai/profile/clarify', req);
    return res.data;
  },

  getAIRecommendations: async (req: AIExplainableRecommendationRequest): Promise<AIExplainableRecommendationResponse> => {
    const res = await apiClient.post<AIExplainableRecommendationResponse>('/ai/recommend', req);
    return res.data;
  },

  chatWithAI: async (req: AIChatRequest): Promise<AIChatResponse> => {
    const res = await apiClient.post<AIChatResponse>('/ai/chat', req);
    return res.data;
  },

  askAboutScheme: async (schemeId: string, req: AIChatRequest): Promise<AIChatResponse> => {
    const res = await apiClient.post<AIChatResponse>(`/ai/schemes/${schemeId}/ask`, req);
    return res.data;
  },

  streamChatWithAI: async (
    req: AIChatRequest,
    onChunk: (chunk: string) => void,
    onError: (err: any) => void
  ): Promise<void> => {
    try {
      const streamUrl = API_BASE_URL.endsWith('/') 
        ? `${API_BASE_URL}ai/chat/stream` 
        : `${API_BASE_URL}/ai/chat/stream`;
      const response = await fetch(streamUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(req),
      });

      if (!response.body) {
        throw new Error('ReadableStream not supported');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const textChunk = decoder.decode(value);
        const lines = textChunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.replace('data: ', '').trim();
            if (jsonStr === '[DONE]') break;
            try {
              const parsed = JSON.parse(jsonStr);
              if (parsed.chunk) onChunk(parsed.chunk);
            } catch (e) {
              // Ignore partial JSON chunks
            }
          }
        }
      }
    } catch (err) {
      onError(err);
    }
  },
};
