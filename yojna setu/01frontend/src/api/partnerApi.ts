import { apiClient } from './client';
import {
  PaginatedPartnerApplicationListResponse,
  ApplicationResponse,
  ApprovalReadinessResponse,
} from '../types';

export interface PartnerData {
  partner_id: string;
  name: string;
  code: string;
  partner_type: string;
  partner_sub_type?: string | null;
  institution_type?: string | null;
  partner_category: string; // 'AUTHORIZED_SCHEME_PARTNER' | 'IMPLEMENTING_ASSISTANCE_CENTRE' | 'NEARBY_FINANCIAL_SERVICE_POINT'
  address?: string | null;
  district?: string | null;
  state?: string | null;
  pincode?: string | null;
  phone?: string | null;
  email?: string | null;
  website?: string | null;
  service_type?: string | null;
  last_verified_date?: string | null;
  scheme_authorization_level?: string | null;
  coordinates_status?: string | null;
  source_url?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  npa_percentage?: number | null;
  overdue_percentage?: number | null;
  is_accepting_applications: boolean;
  is_active: boolean;
  verification_status?: string | null;
  supported_schemes?: string[];
  created_at?: string;
}

export interface NearestPartnerResponse {
  partner: PartnerData;
  distance_km: number;
  is_scheme_matched?: boolean;
  partner_category?: string;
  supported_schemes?: string[];
  service_type?: string | null;
  authorization_level?: string | null;
  scheme_authorized_category?: string | null;
  scheme_mapping_notes?: string | null;
  suitability_reason?: string | null;
  lending_capacity_status?: string | null;
}

export interface PaginatedPartnerAuditResponse {
  items: PartnerData[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  total_active: number;
  total_inactive: number;
}

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
  getNearestPartners: async (
    latitude: number,
    longitude: number,
    radiusKm: number = 100,
    schemeId?: string,
    loanCategory?: string,
    partnerCategory?: string,
    district?: string,
    state?: string,
    serviceType?: string
  ): Promise<NearestPartnerResponse[]> => {
    const response = await apiClient.get<NearestPartnerResponse[]>('/partner/nearest', {
      params: {
        latitude,
        longitude,
        radius_km: radiusKm,
        scheme_id: schemeId,
        loan_category: loanCategory,
        partner_category: partnerCategory,
        district,
        state,
        service_type: serviceType
      }
    });
    return response.data;
  },

  browseDirectory: async (
    district?: string,
    state?: string,
    partnerCategory?: string,
    schemeId?: string
  ): Promise<NearestPartnerResponse[]> => {
    const response = await apiClient.get<NearestPartnerResponse[]>('/partner/directory', {
      params: { district, state, partner_category: partnerCategory, scheme_id: schemeId }
    });
    return response.data;
  },

  getAdminPartners: async (params: {
    search?: string;
    district?: string;
    state?: string;
    partner_category?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }): Promise<any> => {
    const response = await apiClient.get('/admin/partners', { params });
    return response.data;
  },

  createAdminPartner: async (data: any): Promise<any> => {
    const response = await apiClient.post('/admin/partners', data);
    return response.data;
  },

  updateAdminPartner: async (partnerId: string, data: any): Promise<any> => {
    const response = await apiClient.put(`/admin/partners/${partnerId}`, data);
    return response.data;
  },

  updateAdminPartnerStatus: async (partnerId: string, isActive: boolean, reason?: string): Promise<any> => {
    const response = await apiClient.patch(`/admin/partners/${partnerId}/status`, { is_active: isActive, reason });
    return response.data;
  },

  linkPartnerScheme: async (partnerId: string, data: any): Promise<any> => {
    const response = await apiClient.post(`/admin/partners/${partnerId}/schemes`, data);
    return response.data;
  },

  unlinkPartnerScheme: async (partnerId: string, schemeId: string, reason?: string): Promise<any> => {
    const response = await apiClient.delete(`/admin/partners/${partnerId}/schemes/${schemeId}`, {
      params: { reason }
    });
    return response.data;
  },
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

  completeApplication: async (applicationId: string, notes?: string): Promise<ApplicationResponse> => {
    const response = await apiClient.post<ApplicationResponse>(`/partner/applications/${applicationId}/complete`, null, {
      params: { notes }
    });
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
