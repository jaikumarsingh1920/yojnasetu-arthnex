import { apiClient } from './client';
import { BeneficiaryProfileInput, RecommendationResponse } from '../types';

export const recommendationApi = {
  getRecommendations: async (profile: BeneficiaryProfileInput, topK: number = 5): Promise<RecommendationResponse> => {
    const response = await apiClient.post<RecommendationResponse>('/recommendations', {
      profile,
      top_k: topK
    });
    return response.data;
  },
};
