import { apiClient } from './client';
import {
  ApplicationResponse,
  PaginatedApplicationListResponse,
  BeneficiaryProfileInput,
  SubmissionValidationResponse,
} from '../types';

export interface ApplicationCreatePayload {
  scheme_id: string;
  profile: BeneficiaryProfileInput;
}

export interface ApplicationUpdatePayload {
  profile: BeneficiaryProfileInput;
}

export const applicationApi = {
  createApplication: async (payload: ApplicationCreatePayload): Promise<ApplicationResponse> => {
    const response = await apiClient.post<ApplicationResponse>('/applications', payload);
    return response.data;
  },

  getMyApplications: async (status?: string, page: number = 1, pageSize: number = 20): Promise<PaginatedApplicationListResponse> => {
    const response = await apiClient.get<PaginatedApplicationListResponse>('/applications', {
      params: { status, page, page_size: pageSize }
    });
    return response.data;
  },

  getApplicationById: async (applicationId: string): Promise<ApplicationResponse> => {
    const response = await apiClient.get<ApplicationResponse>(`/applications/${applicationId}`);
    return response.data;
  },

  updateDraftApplication: async (applicationId: string, payload: ApplicationUpdatePayload): Promise<ApplicationResponse> => {
    const response = await apiClient.put<ApplicationResponse>(`/applications/${applicationId}`, payload);
    return response.data;
  },

  uploadDocument: async (applicationId: string, appDocumentId: string, file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post(`/applications/${applicationId}/documents/${appDocumentId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  validateSubmission: async (applicationId: string): Promise<SubmissionValidationResponse> => {
    const response = await apiClient.get<SubmissionValidationResponse>(`/applications/${applicationId}/validate`);
    return response.data;
  },

  submitApplication: async (applicationId: string): Promise<ApplicationResponse> => {
    const response = await apiClient.post<ApplicationResponse>(`/applications/${applicationId}/submit`);
    return response.data;
  },
};
