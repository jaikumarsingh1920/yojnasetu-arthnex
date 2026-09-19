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
  city?: string | null;
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

export interface FinancialMetricObservation {
  value?: number | null;
  status?: string | null;
  unit?: string | null;
  financial_scope?: string | null;
  scope_description?: string | null;
  institution_name?: string | null;
  branch_name?: string | null;
  source?: string | null;
  source_authority?: string | null;
  source_url?: string | null;
  document?: string | null;
  reporting_period?: string | null;
  data_as_of?: string | null;
  status_label?: string | null;
  rule_applicability?: string | null;
}

export interface FinancialRuleEvaluation {
  rule_id: string;
  rule_name?: string;
  name?: string;
  metric?: string;
  metric_name?: string;
  operator?: string;
  threshold?: number | string | null;
  threshold_value?: number | null;
  threshold_status?: string | null;
  unit?: string | null;
  authority?: string;
  financial_scope?: string;
  source_document?: string;
  source_url?: string;
  wording?: string;
  result?: string;
  rule_status?: string;
  actual_value?: any;
  observed_value?: any;
  observed_status?: any;
  observation_source?: string | null;
  data_as_of?: string | null;
  explanation?: string;
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
  google_maps_url?: string | null;
  coordinate_precision?: string | null;
  confidence?: string | null;
  application_channel?: string | null;
  routing_status?: string;
  institution_name?: string | null;
  branch_location?: string | null;
  entity_resolution_status?: string | null;
  entity_match_level?: string | null;
  entity_confidence?: number | null;
  entity_resolution_notes?: string | null;
  financial_scope?: string | null;
  financial_intelligence?: {
    NNPA_PERCENT?: FinancialMetricObservation;
    GNPA_PERCENT?: FinancialMetricObservation;
    CRAR_PERCENT?: FinancialMetricObservation;
    [key: string]: FinancialMetricObservation | any;
  };
  rules_evaluated?: FinancialRuleEvaluation[];
  routing_reasons?: string[];
  prudential_status?: string | null;
  prudential_summary?: string | null;
  statutory_checks?: Record<string, any> | null;
  is_restricted?: boolean;
  exclusion_reason?: string | null;
}

export interface FinancialIndicatorStatus {
  code: 'STRONGER' | 'MIXED' | 'HIGHER_STRESS' | 'LIMITED_DATA';
  label: string;
  short_description: string;
  explanation: string;
  why_this_status?: string | null;
  evidence_count: number;
  calculated_from: string[];
  methodology_version: string;
  scope_disclaimer?: string | null;
}

export interface SchemeFinancialSummary {
  scheme_id: string;
  scheme_name: string;
  short_description?: string | null;
  overview?: string | null;
  full_details?: string | null;
  description?: string | null;
  ministry?: string | null;
  sector?: string | null;
  channel_partners_count: number;
  with_verified_financial_info_count: number;
  limited_information_count: number;
  latest_reporting_period?: string | null;
  delivery_mode?: 'FINANCIAL_INTERMEDIARY' | 'DIRECT_DEPARTMENTAL_OR_ONLINE' | string;
}

export interface SchemePartnerFinancialCard {
  partner_id: string;
  partner_name: string;
  partner_code: string;
  institution_name?: string | null;
  partner_type?: string | null;
  institution_type?: string | null;
  nsfdc_authorized?: string | null;
  branch_location?: string | null;
  city?: string | null;
  district?: string | null;
  state?: string | null;
  pincode?: string | null;
  financial_status: FinancialIndicatorStatus;
  verified_metrics: Record<string, FinancialMetricObservation>;
  latest_reporting_period?: string | null;
}

export interface SchemeFinancialDetail {
  scheme_id: string;
  scheme_name: string;
  short_description?: string | null;
  description?: string | null;
  overview?: string | null;
  full_details?: string | null;
  ministry?: string | null;
  sector?: string | null;
  total_channel_partners: number;
  partners_with_verified_financial_info: number;
  partners_with_limited_information: number;
  latest_reporting_period?: string | null;
  delivery_mode?: 'FINANCIAL_INTERMEDIARY' | 'DIRECT_DEPARTMENTAL_OR_ONLINE' | string;
  partners: SchemePartnerFinancialCard[];
}

export interface PartnerFinancialHealthResponse {
  partner_id: string;
  partner_name: string;
  partner_code: string;
  institution_name?: string | null;
  entity_resolution_status?: string | null;
  entity_match_level?: string | null;
  entity_confidence?: number | null;
  entity_resolution_notes?: string | null;
  branch_location?: string | null;
  branch_address?: string | null;
  branch_city?: string | null;
  branch_state?: string | null;
  branch_pincode?: string | null;
  financial_scope?: string | null;
  institution_type?: string | null;
  routing_status: string;
  is_restricted: boolean;
  primary_reason: string;
  rules_evaluated: FinancialRuleEvaluation[];
  verified_metrics: Record<string, FinancialMetricObservation>;
  unverified_metrics: string[];
  record_status?: string | null;
  nsfdc_authorized?: string | null;
  financial_status?: FinancialIndicatorStatus | null;
}

export interface PartnerRoutingAuditResponse {
  recommended_partners: NearestPartnerResponse[];
  excluded_partners: NearestPartnerResponse[];
  total_evaluated: number;
  total_recommended: number;
  total_excluded: number;
  routing_summary: string;
  hard_restrictions_enforced: boolean;
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
    serviceType?: string,
    includeExcluded?: boolean
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
        service_type: serviceType,
        include_excluded: includeExcluded
      }
    });
    return response.data;
  },

  getRoutingAudit: async (
    latitude: number,
    longitude: number,
    radiusKm: number = 100,
    schemeId?: string,
    loanCategory?: string,
    partnerCategory?: string,
    district?: string,
    state?: string
  ): Promise<PartnerRoutingAuditResponse> => {
    const response = await apiClient.get<PartnerRoutingAuditResponse>('/partner/routing-audit', {
      params: {
        latitude,
        longitude,
        radius_km: radiusKm,
        scheme_id: schemeId,
        loan_category: loanCategory,
        partner_category: partnerCategory,
        district,
        state
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

  getCoverageReport: async (): Promise<{
    total_schemes: number;
    total_partners: number;
    total_scheme_partner_mappings: number;
    schemes_with_at_least_one_partner: number;
    coverage_percentage: number;
  }> => {
    const response = await apiClient.get('/partner/coverage-report');
    return response.data;
  },

  getPartnerFinancialHealth: async (partnerId: string): Promise<PartnerFinancialHealthResponse> => {
    const response = await apiClient.get<PartnerFinancialHealthResponse>(`/partner/${partnerId}/financial-health`);
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

  getFinancialHealthSchemes: async (params?: {
    limit?: number;
    search?: string;
    ministry?: string;
    has_partners_only?: boolean;
    availability?: string;
  }): Promise<SchemeFinancialSummary[]> => {
    const response = await apiClient.get<SchemeFinancialSummary[]>('/partners/financial-health/schemes', { params });
    return response.data;
  },

  getSchemeFinancialHealth: async (
    schemeId: string,
    params?: { search?: string; state?: string; district?: string; partner_type?: string; status?: string }
  ): Promise<SchemeFinancialDetail> => {
    const response = await apiClient.get<SchemeFinancialDetail>(`/partners/financial-health/schemes/${schemeId}`, { params });
    return response.data;
  },
};
