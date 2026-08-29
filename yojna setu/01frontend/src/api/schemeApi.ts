import { apiClient } from './client';
import { Scheme, PaginatedSchemeListResponse } from '../types';

export interface SchemeQueryParams {
  search?: string;
  verification_status?: string;
  scheme_type?: string;
  ministry?: string;
  sector?: string;
  page?: number;
  page_size?: number;
}

export const schemeApi = {
  getSchemes: async (params?: SchemeQueryParams): Promise<PaginatedSchemeListResponse> => {
    const response = await apiClient.get<PaginatedSchemeListResponse>('/schemes', { params });
    return response.data;
  },

  getSchemeById: async (schemeId: string): Promise<Scheme> => {
    const response = await apiClient.get<Scheme>(`/schemes/${schemeId}`);
    return response.data;
  },
};
