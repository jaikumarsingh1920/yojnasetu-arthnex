import { apiClient } from './client';
import { Scheme, PaginatedSchemeListResponse, FilterOptionsResponse, SchemeComparisonResponse } from '../types';

export interface SchemeQueryParams {
  search?: string;
  verification_status?: string;
  scheme_type?: string;
  financial_type?: string;
  ministry?: string;
  sector?: string;
  beneficiary_category?: string;
  marginalized_group?: string;
  business_stage?: string;
  state_restriction?: string;
  loan_available?: string;
  subsidy_available?: string;
  grant_available?: string;
  application_route?: string;
  scheme_status?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
}

export const schemeApi = {
  getSchemes: async (params?: SchemeQueryParams): Promise<PaginatedSchemeListResponse> => {
    const response = await apiClient.get<PaginatedSchemeListResponse>('/schemes', { params });
    return response.data;
  },

  getFilterOptions: async (): Promise<FilterOptionsResponse> => {
    const response = await apiClient.get<FilterOptionsResponse>('/schemes/filter-options');
    return response.data;
  },

  getSchemeById: async (schemeId: string): Promise<Scheme> => {
    const response = await apiClient.get<Scheme>(`/schemes/${schemeId}`);
    return response.data;
  },

  getComparison: async (schemeIds: string[]): Promise<SchemeComparisonResponse> => {
    const idsParam = schemeIds.join(',');
    const response = await apiClient.get<SchemeComparisonResponse>('/schemes/compare', {
      params: { ids: idsParam },
    });
    return response.data;
  },
};
