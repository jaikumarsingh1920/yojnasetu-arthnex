import { apiClient } from './client';
import {
  PaginatedPartnerApplicationListResponse,
  ApplicationResponse,
  ApprovalReadinessResponse,
} from '../types';

export interface DocumentReviewPayload {
  verification_status: 'VERIFIED' | 'REJECTED';
  reason?: string;
}

export interface ReviewDecisionPayload {
  decision: 'APPROVED' | 'REJECTED';
  reason?: string;
}

export interface AssignmentPayload {
  partner_id?: string;
  reviewer_id?: string;
}

export const partnerApi = {
  getPartnerApplications: async (status?: string, partnerId?: string, page: number = 1, pageSize: number = 20): Promise<PaginatedPartnerApplicationListResponse> => {
    const response = await apiClient.get<PaginatedPartnerApplicationListResponse>('/partner/applications', {
      params: { status, partner_id: partnerId, page, page_size: pageSize }
    });
    return response.data;
  },

  getPartnerApplicationDetail: async (applicationId: string): Promise<ApplicationResponse> => {
    const response = await apiClient.get<ApplicationResponse>(`/partner/applications/${applicationId}`);
    return response.data;
  },

  assignApplication: async (applicationId: string, payload: AssignmentPayload): Promise<ApplicationResponse> => {
    const response = await apiClient.post<ApplicationResponse>(`/partner/applications/${applicationId}/assign`, payload);
    return response.data;
  },

  startReview: async (applicationId: string): Promise<ApplicationResponse> => {
    const response = await apiClient.post<ApplicationResponse>(`/partner/applications/${applicationId}/start-review`);
    return response.data;
  },

  reviewDocument: async (applicationId: string, appDocumentId: string, payload: DocumentReviewPayload): Promise<any> => {
    const response = await apiClient.post(`/partner/applications/${applicationId}/documents/${appDocumentId}/review`, payload);
    return response.data;
  },

  verifyDocument: async (applicationId: string, appDocumentId: string, payload: { verification_status: 'VERIFIED' | 'REJECTED' | 'NEEDS_CORRECTION'; reason?: string }): Promise<any> => {
    const response = await apiClient.post(`/partner/applications/${applicationId}/documents/${appDocumentId}/verify`, payload);
    return response.data;
  },

  requestCorrection: async (applicationId: string, payload: { reason: string; correction_fields?: string[] }): Promise<ApplicationResponse> => {
    const response = await apiClient.post<ApplicationResponse>(`/partner/applications/${applicationId}/request-correction`, payload);
    return response.data;
  },

  approveApplication: async (applicationId: string): Promise<ApplicationResponse> => {
    const response = await apiClient.post<ApplicationResponse>(`/partner/applications/${applicationId}/approve`);
    return response.data;
  },

  rejectApplication: async (applicationId: string, reason: string): Promise<ApplicationResponse> => {
    const response = await apiClient.post<ApplicationResponse>(`/partner/applications/${applicationId}/reject`, { decision: 'REJECTED', reason });
    return response.data;
  },

  addReviewNote: async (applicationId: string, content: string): Promise<any> => {
    const response = await apiClient.post(`/partner/applications/${applicationId}/notes`, { content });
    return response.data;
  },

  checkApprovalReadiness: async (applicationId: string): Promise<ApprovalReadinessResponse> => {
    const response = await apiClient.get<ApprovalReadinessResponse>(`/partner/applications/${applicationId}/approval-readiness`);
    return response.data;
  },

  processReviewDecision: async (applicationId: string, payload: ReviewDecisionPayload): Promise<ApplicationResponse> => {
    const response = await apiClient.post<ApplicationResponse>(`/partner/applications/${applicationId}/review`, payload);
    return response.data;
  },

  getAdminApplications: async (params?: { status?: string; scheme_id?: string; partner_id?: string; reviewer_id?: string; search?: string; page?: number; page_size?: number }): Promise<PaginatedPartnerApplicationListResponse> => {
    const response = await apiClient.get<PaginatedPartnerApplicationListResponse>('/admin/applications', { params });
    return response.data;
  },

  getAdminStats: async (): Promise<any> => {
    const response = await apiClient.get('/admin/applications/stats');
    return response.data;
  },
};
