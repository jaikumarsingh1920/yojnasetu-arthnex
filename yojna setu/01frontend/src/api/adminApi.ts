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
  total_ministries: number;
  total_changelogs: number;
  system_health: SystemHealthResponse;
}

export interface SchemeAuditItem {
  scheme_id: string;
  scheme_name: string;
  ministry: string;
  sector: string;
  state_coverage: string;
  verification_status: string;
  scheme_status: string;
  scheme_type?: string;
  loan_available?: string;
  rule_count: number;
  document_count: number;
  completeness_score: number;
  known_fields_count: number;
  unknown_fields_count: number;
  conditional_fields_count: number;
  last_verified_date: string;
  official_source_url?: string;
  has_official_source?: boolean;
  official_portal?: string;
  updated_at?: string;
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
  official_source_url?: string;
  official_portal?: string;
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
  action?: string;
  field?: string;
  old_value?: string;
  new_value?: string;
  reason?: string;
  admin_identifier?: string;
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

export interface SchemeCreateInput {
  scheme_id: string;
  scheme_name: string;
  ministry: string;
  scheme_type?: string;
  source_organization?: string;
  implementing_agency?: string;
  purpose?: string;
  short_description?: string;
  detailed_description?: string;
  target_beneficiary?: string;
  applicant_types?: string;
  marginalized_group?: string;
  target_groups?: string;
  social_category?: string;
  gender_condition?: string;
  state_restriction?: string;
  state_coverage?: string;
  sector?: string;
  activity_type?: string;
  business_stage?: string;
  support_type?: string;
  benefit_description?: string;
  loan_available: string;
  minimum_loan_amount?: number;
  maximum_loan_amount?: number;
  interest_rate_min?: number;
  interest_rate_max?: number;
  interest_rate_type?: string;
  repayment_period_min_months?: number;
  repayment_period_max_months?: number;
  subsidy_available?: string;
  subsidy_percentage?: number;
  subsidy_details?: string;
  grant_available?: string;
  grant_amount?: number;
  application_mode?: string;
  application_url?: string;
  official_portal?: string;
  official_source_url: string;
  source_title?: string;
  source_document?: string;
  verification_status?: string;
  last_verified_date?: string;
  required_documents?: string;
  scheme_status?: string;
  reason?: string;
}

export type SchemeUpdateInput = Partial<Omit<SchemeCreateInput, 'scheme_id'>> & {
  change_reason?: string;
};

export interface SchemeStatusUpdateInput {
  status: 'ACTIVE' | 'INACTIVE';
  reason?: string;
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
    status?: string;
    scheme_type?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedSchemeAuditResponse> => {
    const res = await apiClient.get<PaginatedSchemeAuditResponse>('/admin/schemes', { params });
    return res.data;
  },

  createScheme: async (data: SchemeCreateInput): Promise<SchemeAuditDetailResponse> => {
    const res = await apiClient.post<SchemeAuditDetailResponse>('/admin/schemes', data);
    return res.data;
  },

  updateScheme: async (schemeId: string, data: SchemeUpdateInput): Promise<SchemeAuditDetailResponse> => {
    const res = await apiClient.put<SchemeAuditDetailResponse>(`/admin/schemes/${schemeId}`, data);
    return res.data;
  },

  updateSchemeStatus: async (
    schemeId: string,
    status: 'ACTIVE' | 'INACTIVE',
    reason?: string
  ): Promise<{ scheme_id: string; scheme_status: string; message: string }> => {
    const res = await apiClient.patch<{ scheme_id: string; scheme_status: string; message: string }>(
      `/admin/schemes/${schemeId}/status`,
      { status, reason }
    );
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
