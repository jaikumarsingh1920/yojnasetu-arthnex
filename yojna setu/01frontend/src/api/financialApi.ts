import { apiClient } from './client';
import { FinancialCalculationResult } from '../types';

export interface FinancialCalculateRequest {
  scheme_id: string;
  project_cost?: number | null;
  requested_loan_amount?: number | null;
  repayment_period_months?: number | null;
  repayment_frequency?: string | null;
}

export const financialApi = {
  calculate: async (payload: FinancialCalculateRequest): Promise<FinancialCalculationResult> => {
    const response = await apiClient.post<FinancialCalculationResult>('/calculator/calculate', payload);
    return response.data;
  },
};
