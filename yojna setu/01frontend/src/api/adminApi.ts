import { apiClient } from './client';

export interface SystemHealthComponent {
  name: string;
  status: string;
  message?: string;
  details?: Record<string, any>;
}

export interface SystemHealthResponse {
  overall_status: string;
  timestamp: string;
  components: SystemHealthComponent[];
}

export interface AdminDashboardSummaryResponse {
  total_schemes: number;
  verified_schemes: number;
  total_rules: number;
  total_documents: number;
  avg_parameter_completeness: number;
  applications_total: number;
  applications_by_status: Record<string, number>;
  pending_document_verifications: number;
  unread_notifications: number;
  system_health: SystemHealthResponse;
}

export interface SchemeAuditItem {
  scheme_id: string;
  scheme_name: string;
  ministry: string;
  sector: string;
  state_coverage: string;
  verification_status: string;
  rule_count: number;
  document_count: number;
  completeness_score: number;
  known_fields_count: number;
  unknown_fields_count: number;
  conditional_fields_count: number;
  last_verified_date: string;
}

export interface PaginatedSchemeAuditResponse {
  items: SchemeAuditItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  avg_completeness: number;
}

export interface SchemeAuditDetailResponse {
  scheme_id: string;
  scheme_name: string;
  ministry: string;
  sector: string;
  state_coverage: string;
  verification_status: string;
  purpose?: string;
  target_groups?: string;
  completeness_score: number;
  known_fields: Record<string, any>;
  unknown_fields: string[];
  conditional_fields: string[];
  not_applicable_fields: string[];
  rules: Array<{
    rule_id: string;
    field: string;
    operator: string;
    value: string;
    value_type: string;
    rule_type: string;
    priority: string;
    condition_group: string;
    error_message?: string;
  }>;
  documents: Array<{
    document_id: string;
    document_name: string;
    requirement_type: string;
    applicant_type?: string;
    source_document?: string;
    active: boolean;
  }>;
  changelogs: Array<{
    id: number;
    field?: string;
    old_value?: string;
    new_value?: string;
    reason?: string;
    created_at: string;
  }>;
  data_quality_warnings: string[];
}

export interface RuleAuditItem {
  rule_id: string;
  scheme_id: string;
  scheme_name: string;
  field: string;
  operator: string;
  value: string;
  value_type: string;
  rule_type: string;
  priority: string;
  condition_group: string;
  error_message?: string;
}

export interface PaginatedRuleAuditResponse {
  items: RuleAuditItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DocumentAuditItem {
  document_id: string;
  scheme_id: string;
  scheme_name: string;
  document_name: string;
  requirement_type: string;
  applicant_type?: string;
  source_document?: string;
  active: boolean;
  verification_status: string;
}

export interface PaginatedDocumentAuditResponse {
  items: DocumentAuditItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ChangelogItem {
  id: number;
  scheme_id: string;
  scheme_name: string;
  field?: string;
  old_value?: string;
  new_value?: string;
  reason?: string;
  source_document?: string;
  verification_status?: string;
  created_at: string;
}

export interface PaginatedChangelogResponse {
  items: ChangelogItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export const adminApi = {
  getDashboardSummary: async (): Promise<AdminDashboardSummaryResponse> => {
    const res = await apiClient.get<AdminDashboardSummaryResponse>('/admin/dashboard');
    return res.data;
  },

  getSchemeAuditList: async (params?: {
    search?: string;
    ministry?: string;
    sector?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedSchemeAuditResponse> => {
    const res = await apiClient.get<PaginatedSchemeAuditResponse>('/admin/schemes', { params });
    return res.data;
  },

  getSchemeAuditDetail: async (schemeId: string): Promise<SchemeAuditDetailResponse> => {
    const res = await apiClient.get<SchemeAuditDetailResponse>(`/admin/schemes/${schemeId}`);
    return res.data;
  },

  getRuleAuditList: async (params?: {
    scheme_id?: string;
    rule_type?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedRuleAuditResponse> => {
    const res = await apiClient.get<PaginatedRuleAuditResponse>('/admin/rules', { params });
    return res.data;
  },

  getDocumentAuditList: async (params?: {
    scheme_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedDocumentAuditResponse> => {
    const res = await apiClient.get<PaginatedDocumentAuditResponse>('/admin/documents', { params });
    return res.data;
  },

  getChangelog: async (params?: {
    scheme_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedChangelogResponse> => {
    const res = await apiClient.get<PaginatedChangelogResponse>('/admin/changelog', { params });
    return res.data;
  },

  getSystemHealth: async (): Promise<SystemHealthResponse> => {
    const res = await apiClient.get<SystemHealthResponse>('/admin/system-health');
    return res.data;
  },
};
