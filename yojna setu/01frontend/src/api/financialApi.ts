import { apiClient } from './client';
import { FinancialCalculationResult, FinancialHealthInput, FinancialHealthResponse } from '../types';

export interface FinancialCalculateRequest {
  scheme_id: string;
  project_cost?: number | null;
  requested_loan_amount?: number | null;
  interest_rate?: number | null;
  repayment_period_months?: number | null;
  repayment_frequency?: string | null;
}

export const financialApi = {
  calculate: async (payload: FinancialCalculateRequest): Promise<FinancialCalculationResult> => {
    const response = await apiClient.post<FinancialCalculationResult>('/calculator/calculate', payload);
    return response.data;
  },

  getFinancialHealth: async (): Promise<FinancialHealthResponse> => {
    const response = await apiClient.get<FinancialHealthResponse>('/financial-health');
    return response.data;
  },

  assessFinancialHealth: async (input: FinancialHealthInput): Promise<FinancialHealthResponse> => {
    const response = await apiClient.post<FinancialHealthResponse>('/financial-health/assess', input);
    return response.data;
  },
};

