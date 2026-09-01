import { apiClient } from './client';
import {
  BeneficiaryProfileInput,
  CitizenProfileResponse,
  RecommendationResponse,
} from '../types';

export const profileApi = {
  /**
   * Retrieves the authenticated citizen's canonical profile, completion score, and missing fields.
   */
  async getProfile(): Promise<CitizenProfileResponse> {
    const response = await apiClient.get<CitizenProfileResponse>('/profile');
    return response.data;
  },

  /**
   * Updates citizen profile attributes with backend validation and persistence.
   */
  async updateProfile(profile: BeneficiaryProfileInput): Promise<CitizenProfileResponse> {
    const response = await apiClient.put<CitizenProfileResponse>('/profile', profile);
    return response.data;
  },

  /**
   * Executes deterministic smart matching across all 90 verified schemes.
   */
  async smartMatch(profileOverride?: BeneficiaryProfileInput, topK: number = 10): Promise<RecommendationResponse> {
    const response = await apiClient.post<RecommendationResponse>('/profile/match', profileOverride || null, {
      params: { top_k: topK },
    });
    return response.data;
  },
};
