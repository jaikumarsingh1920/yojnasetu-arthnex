import { apiClient } from './client';
import { Scheme } from '../types';

export interface SavedSchemeItem {
  id: string;
  user_id: string;
  scheme_id: string;
  created_at: string;
  scheme: Scheme;
}

export interface SavedSchemeListResponse {
  items: SavedSchemeItem[];
  total: number;
}

export interface SavedSchemeStatusResponse {
  scheme_id: string;
  is_saved: boolean;
}

export interface EmailSchemeResponse {
  sent: boolean;
  message: string;
  recipient_email?: string;
}

export const savedSchemesApi = {
  saveScheme: async (schemeId: string): Promise<SavedSchemeItem> => {
    const response = await apiClient.post<SavedSchemeItem>(`/saved-schemes/${schemeId}`);
    return response.data;
  },

  removeSavedScheme: async (schemeId: string): Promise<{ message: string; scheme_id: string }> => {
    const response = await apiClient.delete<{ message: string; scheme_id: string }>(`/saved-schemes/${schemeId}`);
    return response.data;
  },

  listSavedSchemes: async (): Promise<SavedSchemeListResponse> => {
    const response = await apiClient.get<SavedSchemeListResponse>('/saved-schemes');
    return response.data;
  },

  checkSavedStatus: async (schemeId: string): Promise<SavedSchemeStatusResponse> => {
    const response = await apiClient.get<SavedSchemeStatusResponse>(`/saved-schemes/${schemeId}`);
    return response.data;
  },

  emailScheme: async (schemeId: string): Promise<EmailSchemeResponse> => {
    const response = await apiClient.post<EmailSchemeResponse>(`/saved-schemes/${schemeId}/email`);
    return response.data;
  },
};
