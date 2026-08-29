// ─────────────────────────────────────────────────────────────
// User & Auth Types
// ─────────────────────────────────────────────────────────────

export type UserRole = "BENEFICIARY" | "PARTNER_USER" | "PARTNER_ADMIN" | "SYSTEM_ADMIN";

export interface User {
  user_id: string;
  email?: string | null;
  phone?: string | null;
  role: UserRole;
  is_active: boolean;
  partner_id?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  username?: string;
  identifier?: string;
  password: string;
}

export interface RegisterRequest {
  email?: string;
  phone?: string;
  password: string;
  role?: UserRole;
}

// ─────────────────────────────────────────────────────────────
// Scheme Types
// ─────────────────────────────────────────────────────────────

export interface SchemeRule {
  rule_id: string;
  scheme_id: string;
  field: string;
  operator: string;
  value: string;
  value_type: string;
  rule_type: string;
  priority: number;
  condition_group?: string | null;
  error_message?: string | null;
}

export interface SchemeDocument {
  document_id: string;
  scheme_id: string;
  document_name: string;
  requirement_type: string; // REQUIRED, OPTIONAL, CONDITIONAL
  condition?: string | null;
  active: boolean;
}

export interface SchemeVerification {
  verification_id: string;
  scheme_id: string;
  source_name: string;
  source_url?: string | null;
  verified_by?: string | null;
  status: string;
}

export interface Scheme {
  scheme_id: string;
  scheme_name: string;
  scheme_code?: string | null;
  ministry?: string | null;
  implementing_agency?: string | null;
  scheme_type?: string | null;
  sector?: string | null;
  objective?: string | null;
  target_groups?: string | null;
  applicant_types?: string | null;
  marginalized_group?: string | null;
  sc_required?: string | null;
  business_stage?: string | null;
  activity_type?: string | null;
  support_type?: string | null;
  new_business_allowed?: string | null;
  existing_business_allowed?: string | null;
  state_restriction?: string | null;
  state_coverage?: string | null;
  min_age?: number | null;
  max_age?: number | null;
  income_limit?: number | null;
  max_loan_amount?: number | null;
  max_project_cost?: number | null;
  max_subsidy_amount?: number | null;
  subsidy_percentage?: number | null;
  financing_percentage?: number | null;
  interest_rate?: number | null;
  repayment_period_months?: number | null;
  moratorium_period_months?: number | null;
  collateral_required?: string | null;
  application_route?: string | null;
  application_url?: string | null;
  official_portal?: string | null;
  official_source_url?: string | null;
  short_description?: string | null;
  purpose?: string | null;
  target_beneficiary?: string | null;
  max_loan_amount_raw?: string | null;
  interest_rate_type?: string | null;
  interest_rate_min_raw?: string | null;
  verification_status: string;
  rules?: SchemeRule[];
  documents?: SchemeDocument[];
  verifications?: SchemeVerification[];
}

export interface PaginatedSchemeListResponse {
  items: Scheme[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ─────────────────────────────────────────────────────────────
// Beneficiary Profile Input Type
// ─────────────────────────────────────────────────────────────

export interface BeneficiaryProfileInput {
  age?: number | null;
  annual_income?: number | null;
  social_category?: string | null;
  is_sc?: boolean | null;
  gender?: string | null;
  state?: string | null;
  district?: string | null;
  applicant_type?: string | null;
  entrepreneur_type?: string | null;
  business_stage?: string | null;
  is_new_unit?: boolean | null;
  sector?: string | null;
  activity_type?: string | null;
  project_cost?: number | null;
  requested_loan_amount?: number | null;
  collateral_available?: boolean | null;
  application_route?: string | null;
}

// ─────────────────────────────────────────────────────────────
// Recommendation Types
// ─────────────────────────────────────────────────────────────

export interface ScoreDimensionBreakdown {
  dimension: string;
  max_weight: number;
  score: number;
  result: "MATCH" | "PARTIAL_MATCH" | "NO_MATCH" | "NOT_EVALUATED";
  reason: string;
}

export interface RecommendationItem {
  rank: number;
  scheme_id: string;
  scheme_name: string;
  eligibility_status: "ELIGIBLE" | "INELIGIBLE" | "INSUFFICIENT_INFORMATION" | "CONDITIONAL";
  score: number;
  matched_factors: string[];
  unmatched_factors: string[];
  not_evaluated_factors: string[];
  eligibility_reasons: string[];
  recommendation_reasons: string[];
  score_breakdown: ScoreDimensionBreakdown[];
}

export interface RecommendationResponse {
  profile_summary: Record<string, any>;
  evaluated_scheme_count: number;
  eligible_scheme_count: number;
  excluded_scheme_count: number;
  insufficient_info_scheme_count: number;
  recommendations: RecommendationItem[];
  missing_profile_fields: string[];
}

// ─────────────────────────────────────────────────────────────
// Financial Calculator Types
// ─────────────────────────────────────────────────────────────

export interface ResolvedFinancialParameter {
  field: string;
  value?: any;
  status: "RESOLVED" | "UNKNOWN" | "CONDITIONAL" | "NOT_APPLICABLE";
  source_rule_id?: string | null;
  reason?: string | null;
}

export interface AmortizationEntry {
  installment_number: number;
  period_label?: string;
  opening_principal?: number;
  installment_amount?: number;
  payment_amount?: number;
  principal_component?: number;
  interest_component?: number;
  closing_principal?: number;
  remaining_balance?: number;
}

export interface FinancialCalculationResult {
  scheme_id: string;
  scheme_name?: string | null;
  status: "CALCULATED" | "VALIDATION_FAILED" | "INSUFFICIENT_INFORMATION" | "SUCCESS" | "PARTIAL" | "FAILED" | "INELIGIBLE_SCENARIO";
  project_cost?: number | null;
  requested_loan_amount?: number | null;
  eligible_loan_amount?: number | null;
  approved_loan_amount?: number | null;
  beneficiary_contribution_amount?: number | null;
  beneficiary_contribution?: number | null;
  subsidy_amount?: number | null;
  grant_amount?: number | null;
  margin_percentage?: number | null;
  interest_rate?: number | null;
  interest_rate_annual?: number | null;
  repayment_period_months?: number | null;
  tenure_months?: number | null;
  moratorium_months?: number | null;
  repayment_frequency?: string | null;
  periodic_installment?: number | null;
  installment_amount?: number | null;
  total_interest?: number | null;
  total_interest_payable?: number | null;
  total_repayment?: number | null;
  total_repayment_amount?: number | null;
  amortization_schedule?: AmortizationEntry[];
  resolved_parameters?: ResolvedFinancialParameter[];
  validation_errors?: any[];
  missing_parameters?: string[];
  warnings?: string[];
  notes?: string[];
}

// ─────────────────────────────────────────────────────────────
// Application Workflow Types
// ─────────────────────────────────────────────────────────────

export type ApplicationStatus =
  | "DRAFT"
  | "DOCUMENTS_PENDING"
  | "READY_FOR_SUBMISSION"
  | "SUBMITTED"
  | "UNDER_REVIEW"
  | "CORRECTION_REQUIRED"
  | "APPROVED"
  | "REJECTED";

export interface ApplicationDocument {
  app_document_id: string;
  application_id: string;
  document_id?: string | null;
  document_name: string;
  requirement_type: string; // REQUIRED, OPTIONAL, CONDITIONAL
  condition?: string | null;
  is_uploaded: boolean;
  file_path?: string | null;
  file_name?: string | null;
  file_size_bytes?: number | null;
  mime_type?: string | null;
  verification_status: "PENDING" | "VERIFIED" | "REJECTED" | "NEEDS_CORRECTION";
  rejection_reason?: string | null;
  verified_by?: string | null;
  verified_at?: string | null;
  uploaded_at?: string | null;
  created_at: string;
}

export interface StatusHistory {
  history_id: string;
  application_id: string;
  old_status?: string | null;
  new_status: string;
  changed_by?: string | null;
  reason?: string | null;
  created_at: string;
}

export interface ApplicationReviewNote {
  note_id: string;
  application_id: string;
  author_id: string;
  author_role: string;
  content: string;
  created_at: string;
}

export interface ApplicationResponse {
  application_id: string;
  user_id: string;
  scheme_id: string;
  scheme_name?: string | null;
  status: ApplicationStatus;
  assigned_partner_id?: string | null;
  assigned_reviewer_id?: string | null;
  profile_snapshot?: Record<string, any> | null;
  eligibility_snapshot?: Record<string, any> | null;
  rejection_reason?: string | null;
  correction_reason?: string | null;
  correction_fields?: string | null;
  created_at: string;
  updated_at: string;
  submitted_at?: string | null;
  documents: ApplicationDocument[];
  status_history: StatusHistory[];
  review_notes?: ApplicationReviewNote[];
}

export interface PaginatedApplicationListResponse {
  items: ApplicationResponse[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export type PaginatedPartnerApplicationListResponse = PaginatedApplicationListResponse;

export interface SubmissionValidationResponse {
  application_id: string;
  status: string;
  can_submit: boolean;
  missing_documents: string[];
  message: string;
}

export interface ApprovalReadinessResponse {
  application_id: string;
  status: string;
  can_approve: boolean;
  blocking_documents: string[];
  message: string;
}

// AI Intelligence Layer Types
export interface ExtractedFieldConfidence {
  field: string;
  value: any;
  confidence: number;
  source_snippet?: string;
}

export interface NaturalLanguageExtractRequest {
  user_text: string;
}

export interface NaturalLanguageExtractResponse {
  user_text: string;
  extracted_profile: BeneficiaryProfileInput;
  field_confidences: ExtractedFieldConfidence[];
  missing_high_priority_fields: string[];
  fields_requiring_clarification: string[];
  is_fallback: boolean;
  provider_name: string;
}

export interface ClarificationQuestion {
  field: string;
  question: string;
  options?: string[];
  impact_reason: string;
}

export interface ClarificationRequest {
  extracted_profile: BeneficiaryProfileInput;
  missing_fields?: string[];
}

export interface ClarificationResponse {
  questions: ClarificationQuestion[];
  completion_percentage: number;
}

export interface SourceCitation {
  scheme_id: string;
  scheme_name?: string;
  source_type: string;
  source_document?: string;
  rule_id?: string;
  snippet: string;
  relevance_score: number;
}

export interface AICopilotAction {
  label: string;
  action_type: string;
  target_url: string;
  payload?: Record<string, any>;
}

export interface AIChatRequest {
  message: string;
  session_id?: string;
  scheme_id?: string;
  application_id?: string;
  page_context?: Record<string, any>;
  profile?: BeneficiaryProfileInput;
  conversation_history?: Array<{ role: string; content: string }>;
  preferred_language?: string;
}

export interface RichCard {
  card_type: string;
  title: string;
  subtitle?: string;
  data: Record<string, any>;
}

export interface AIChatResponse {
  answer: string;
  intent?: string;
  response_mode?: string;
  citations: SourceCitation[];
  actions?: AICopilotAction[];
  rich_cards?: RichCard[];
  suggested_questions?: string[];
  session_id?: string;
  deterministic_used: boolean;
  financial_calculation?: any;
  is_fallback: boolean;
  provider_name: string;
}

export interface AIExplainableRecommendationRequest {
  user_text?: string;
  profile?: BeneficiaryProfileInput;
  top_k?: number;
}

export interface AIRecommendationItem {
  rank: number;
  scheme_id: string;
  scheme_name: string;
  eligibility_status: string;
  score: number;
  ai_explanation: string;
  matched_factors: string[];
  eligibility_reasons: string[];
  financial_fit_summary: string;
  citations: SourceCitation[];
}

export interface AIExplainableRecommendationResponse {
  evaluated_scheme_count: number;
  eligible_scheme_count: number;
  recommendations: AIRecommendationItem[];
  missing_profile_fields: string[];
  clarification_questions: ClarificationQuestion[];
  is_fallback: boolean;
  provider_name: string;
}

// ─────────────────────────────────────────────────────────────
// Notification Types
// ─────────────────────────────────────────────────────────────

export interface NotificationItem {
  notification_id: string;
  recipient_user_id: string;
  application_id?: string | null;
  notification_type: string;
  title: string;
  message: string;
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT' | string;
  is_read: boolean;
  created_at: string;
  read_at?: string | null;
  metadata_json?: string | null;
  channel: string;
  delivery_status: string;
}

export interface PaginatedNotificationListResponse {
  items: NotificationItem[];
  total: number;
  page: number;
  page_size: number;
  unread_count: number;
}

export interface NotificationPreference {
  user_id: string;
  in_app_enabled: boolean;
  email_enabled: boolean;
  sms_enabled: boolean;
  whatsapp_enabled: boolean;
  push_enabled: boolean;
  updated_at: string;
}
