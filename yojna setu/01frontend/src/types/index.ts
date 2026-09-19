// ─────────────────────────────────────────────────────────────
// User & Auth Types
// ─────────────────────────────────────────────────────────────

export type UserRole = "BENEFICIARY" | "PARTNER_USER" | "PARTNER_ADMIN" | "SYSTEM_ADMIN";

export interface User {
  user_id: string;
  email?: string | null;
  phone?: string | null;
  full_name?: string | null;
  avatar_url?: string | null;
  auth_provider?: string | null;
  role: UserRole;
  is_active: boolean;
  preferred_language?: string;
  partner_id?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
  user: User;
}

export interface LoginRequest {
  username?: string;
  identifier?: string;
  password: string;
}

export interface GoogleLoginRequest {
  id_token: string;
  preferred_language?: string;
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
  description?: string | null;
  source_document?: string | null;
  source_section?: string | null;
}

export interface SchemeDocument {
  document_id: string;
  scheme_id: string;
  document_name: string;
  requirement_type: string; // REQUIRED, OPTIONAL, CONDITIONAL, MANDATORY
  condition?: string | null;
  applicant_type?: string | null;
  source_document?: string | null;
  source_page?: string | null;
  source_section?: string | null;
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
  loan_available?: string | null;
  min_loan_amount?: number | null;
  max_loan_amount?: number | null;
  max_project_cost?: number | null;
  max_subsidy_amount?: number | null;
  subsidy_percentage?: number | null;
  financing_percentage?: number | null;
  beneficiary_contribution_percentage?: number | null;
  interest_rate?: number | null;
  interest_rate_min?: number | null;
  interest_rate_max?: number | null;
  interest_rate_type?: string | null;
  interest_subsidy?: number | null;
  benefit_description?: string | null;
  repayment_period_months?: number | null;
  repayment_period_min_months?: number | null;
  repayment_period_max_months?: number | null;
  repayment_frequency?: string | null;
  moratorium_period_months?: number | null;
  moratorium_min_months?: number | null;
  moratorium_max_months?: number | null;
  moratorium_interest_mode?: string | null;
  collateral_required?: string | null;
  security_required?: string | null;
  guarantee_requirement?: string | null;
  processing_fee?: string | null;
  min_project_cost?: number | null;
  application_mode?: string | null;
  application_route?: string | null;
  partner_count?: number | null;
  application_steps?: string | null;
  required_documents?: string | null;
  application_url?: string | null;
  official_portal?: string | null;
  official_source_url?: string | null;
  source_title?: string | null;
  source_document?: string | null;
  source_page?: string | null;
  source_section?: string | null;
  source_published_date?: string | null;
  last_verified_date?: string | null;
  scheme_version?: string | null;
  short_description?: string | null;
  purpose?: string | null;
  target_beneficiary?: string | null;
  max_loan_amount_raw?: string | null;
  financial_category?: string | null;
  is_credit_scheme?: boolean;
  calculator_applicable?: boolean;
  financial_assistance_summary?: string | null;
  grant_amount?: number | null;
  subsidy_amount?: number | null;
  subsidy_details?: string | null;
  district_restriction?: string | null;
  district_coverage?: string | null;
  business_types?: string | null;
  new_unit_required?: string | null;
  existing_unit_allowed?: string | null;
  business_registration_required?: string | null;
  education_applicable?: string | null;
  enterprise_size_requirement?: string | null;
  social_category?: string | null;
  gender_condition?: string | null;
  gender_requirement?: string | null;
  income_limit?: number | null;
  income_operator?: string | null;
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

export interface FilterOptionItem {
  label: string;
  value: string;
  count: number;
}

export interface FilterOptionsResponse {
  ministries: FilterOptionItem[];
  sectors: FilterOptionItem[];
  financial_types: FilterOptionItem[];
  beneficiary_categories: FilterOptionItem[];
  states: FilterOptionItem[];
  application_routes: FilterOptionItem[];
  total_schemes: number;
  availability_counts?: Record<string, number>;
}

export interface SchemePersonalizedEligibility {
  status: 'ELIGIBLE' | 'INSUFFICIENT_INFORMATION' | 'INELIGIBLE';
  reasons: string[];
  missing_fields: string[];
}

export interface SchemeComparisonItem {
  scheme: Scheme;
  personalized_eligibility?: SchemePersonalizedEligibility | null;
}

export interface SchemeComparisonResponse {
  compared_schemes: SchemeComparisonItem[];
  invalid_ids: string[];
}


// ─────────────────────────────────────────────────────────────
// Beneficiary Profile Input & Completion Types
// ─────────────────────────────────────────────────────────────

export interface BeneficiaryProfileInput {
  age?: number | null;
  annual_income?: number | null;
  monthly_income?: number | null;
  monthly_expenses?: number | null;
  monthly_obligations?: number | null;
  social_category?: string | null;
  is_sc?: boolean | null;
  is_pwd?: boolean | null;
  disability_status?: string | null;
  is_minority?: boolean | null;
  gender?: string | null;
  marital_status?: string | null;
  state?: string | null;
  district?: string | null;
  employment_status?: string | null;
  occupation?: string | null;
  education_level?: string | null;
  applicant_type?: string | null;
  entrepreneur_type?: string | null;
  is_artisan?: boolean | null;
  is_farmer?: boolean | null;
  is_street_vendor?: boolean | null;
  is_safai_karamchari?: boolean | null;
  business_stage?: string | null;
  is_new_unit?: boolean | null;
  sector?: string | null;
  activity_type?: string | null;
  project_cost?: number | null;
  requested_loan_amount?: number | null;
  collateral_available?: boolean | null;
  application_route?: string | null;
}

export interface MissingFieldDetail {
  field: string;
  label: string;
  impact_reason: string;
  category: string;
}

export interface CitizenProfileResponse {
  profile: BeneficiaryProfileInput;
  completion_percentage: number;
  completed_fields_count: number;
  total_fields_count: number;
  missing_fields: MissingFieldDetail[];
  is_eligible_for_smart_matching: boolean;
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
  eligibility_status: "ELIGIBLE" | "INELIGIBLE" | "INSUFFICIENT_INFORMATION" | "CONDITIONAL" | "NOT_APPLICABLE";
  score: number;
  eligible?: boolean;
  matched_rules?: string[];
  failed_rules?: string[];
  missing_information?: string[];
  matched_factors: string[];
  unmatched_factors: string[];
  not_evaluated_factors: string[];
  eligibility_reasons: string[];
  recommendation_reasons: string[];
  score_breakdown: ScoreDimensionBreakdown[];
  financial_category?: string | null;
  is_credit_scheme?: boolean;
  calculator_applicable?: boolean;
  financial_assistance_summary?: string | null;
  max_loan_amount?: number | null;
  interest_rate?: number | null;
  repayment_period_max_months?: number | null;
  subsidy_percentage?: number | null;
  grant_amount?: number | null;
  financial_suitability?: string | null;
  financial_suitability_reason?: string | null;
  estimated_monthly_installment?: number | null;
  available_subsidy_amount?: number | null;
  required_own_contribution?: number | null;
  ministry?: string | null;
  source_organization?: string | null;
  official_portal?: string | null;
  application_url?: string | null;
  official_source_url?: string | null;
  source_document?: string | null;
  is_direct_portal_scheme?: boolean;
  short_description?: string | null;
  purpose?: string | null;
  key_conditions?: string[];
  conditional_rules?: string[];
}

export interface RecommendationResponse {
  profile_summary: Record<string, any>;
  evaluated_scheme_count: number;
  eligible_scheme_count: number;
  excluded_scheme_count: number;
  insufficient_info_scheme_count: number;
  conditional_scheme_count?: number;
  not_applicable_scheme_count?: number;
  recommendations: RecommendationItem[];
  conditional_schemes?: RecommendationItem[];
  ineligible_schemes?: RecommendationItem[];
  insufficient_info_schemes?: RecommendationItem[];
  not_applicable_schemes?: RecommendationItem[];
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
  | "REJECTED"
  | "WITHDRAWN"
  | "COMPLETED";


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

// ─────────────────────────────────────────────────────────────
// Financial Health Types
// ─────────────────────────────────────────────────────────────

export interface FinancialHealthInput {
  annual_income?: number | null;
  monthly_income?: number | null;
  monthly_expenses?: number | null;
  requested_loan_amount?: number | null;
  project_cost?: number | null;
  existing_liabilities?: number | null;
  monthly_obligations?: number | null;
  liquid_savings?: number | null;
  profile?: BeneficiaryProfileInput | null;
}

export interface FinancialIndicatorResult {
  indicator_name: string;
  label: string;
  value?: number | null;
  formatted_value: string;
  benchmark: string;
  status: 'HEALTHY' | 'MODERATE' | 'STRESSED' | 'HIGH_RISK' | 'NOT_EVALUATED';
  score?: number | null;
  weight: number;
  explanation: string;
}

export interface MissingFinancialField {
  field: string;
  label: string;
  impact_reason: string;
}

export interface FinancialHealthResponse {
  status: 'HEALTHY' | 'MODERATE' | 'STRESSED' | 'HIGH_RISK' | 'INSUFFICIENT_INFORMATION';
  score?: number | null;
  summary_headline: string;
  summary_detail?: string;
  indicators: FinancialIndicatorResult[];
  risk_flags: string[];
  positive_factors: string[];
  recommendations: string[];
  missing_fields: MissingFinancialField[];
  monthly_income?: number | null;
  monthly_expenses?: number | null;
  existing_monthly_obligations?: number | null;
  proposed_monthly_emi?: number | null;
  total_monthly_obligations?: number | null;
  estimated_disposable_income?: number | null;
  debt_to_income_ratio?: number | null;
  required_margin_money?: number | null;
  margin_money_gap?: number | null;
  calculation_version: string;
  evaluated_at: string;
  overall_status?: 'HEALTHY' | 'MODERATE' | 'STRESSED' | 'HIGH_RISK' | 'INSUFFICIENT_INFORMATION';
  health_score?: number;
}

// ─────────────────────────────────────────────────────────────
// Ingestion & Candidate Governance Types
// ─────────────────────────────────────────────────────────────

export interface CandidateScheme {
  candidate_id: string;
  run_id?: string | null;
  discovered_name: string;
  scheme_name?: string;
  normalized_name?: string | null;
  scheme_code?: string | null;
  discovery_source?: string | null;
  discovery_url?: string | null;
  source_url?: string | null;
  official_source_url?: string | null;
  source_document?: string | null;
  source_type?: string | null;
  target_source?: string | null;
  ministry?: string | null;
  implementing_agency?: string | null;
  level?: string | null;
  state?: string | null;
  state_coverage?: string | null;
  district_coverage?: string | null;
  category?: string | null;
  sector?: string | null;
  scheme_category?: string | null;
  target_beneficiaries?: string | null;
  stated_benefits?: string | null;
  relevance_status: 'HIGH_PRIORITY' | 'RELEVANT' | 'LOW_PRIORITY' | 'IRRELEVANT' | string;
  relevance_reason?: string | null;
  extraction_status?: string | null;
  verification_status?: string | null;
  duplicate_status?: 'UNIQUE' | 'DUPLICATE_CANDIDATE' | 'MERGED' | string;
  duplicate_of_scheme_id?: string | null;
  data_confidence?: number | null;
  confidence_score?: number | null;
  extracted_data?: Record<string, any>;
  raw_parameters?: Record<string, any>;
  missing_fields?: string[];
  evidence?: Record<string, any>;
  validation_status?: string | null;
  validation_errors?: any[];
  candidate_status: 'DISCOVERED' | 'STAGED' | 'APPROVED' | 'REJECTED' | 'NEEDS_REVIEW' | 'ARCHIVED';
  admin_notes?: string | null;
  rejection_reason?: string | null;
  created_at: string;
  updated_at?: string | null;
  reviewed_at?: string | null;
  reviewed_by?: string | null;
}

export interface CandidateReviewInput {
  action: 'APPROVE' | 'REJECT' | 'NEEDS_REVIEW';
  notes?: string;
  rejection_reason?: string;
}

export interface CandidateReviewResponse {
  candidate_id: string;
  candidate_status: string;
  canonical_scheme_id?: string | null;
  message: string;
}

export interface DetectedFieldChange {
  field: string;
  old_value?: any;
  new_value?: any;
}

export interface FieldDiff {
  field: string;
  old_value?: any;
  new_value?: any;
  diff_category?: 'CRITICAL' | 'NON_CRITICAL' | string;
  diff_summary?: string;
}

export interface PendingSchemeUpdate {
  update_id: string;
  scheme_id: string;
  source_id?: string | null;
  snapshot_id?: string | null;
  proposal_type?: 'MODIFICATION' | 'NEW_SCHEME' | 'DEACTIVATION' | string;
  change_classification?: 'MODIFIED' | 'NEW_SCHEME' | 'POSSIBLY_WITHDRAWN' | string;
  old_version?: string;
  extracted_data?: Record<string, any>;
  detected_changes?: DetectedFieldChange[];
  validation_status?: 'VALID' | 'NEEDS_REVIEW' | 'INVALID' | string;
  validation_errors?: string[];
  governance_classification?: 'AUTO_SAFE' | 'NEEDS_REVIEW' | 'REJECTED' | string;
  governance_category?: string;
  status: 'PENDING' | 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | string;
  created_at?: string;
  detected_at?: string;
  reviewed_at?: string | null;
  reviewed_by?: string | null;
  review_notes?: string | null;
  rejection_reason?: string | null;
  // Legacy / convenience fields
  change_type?: string;
  old_value?: any;
  new_value?: any;
  proposed_data?: Record<string, any>;
  field_diffs?: FieldDiff[];
}

export interface PendingUpdateReviewInput {
  action: 'APPROVE' | 'REJECT';
  reason?: string;
  notes?: string;
}

export interface IngestionRun {
  run_id: string;
  started_at: string;
  completed_at?: string | null;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED' | 'PAUSED';
  records_seen: number;
  records_changed: number;
  records_unchanged: number;
  records_failed: number;
  records_staged: number;
  records_promoted: number;
  records_needing_review: number;
  checkpoint_data?: string | null;
  error_summary?: string | null;
}

export interface DiscoveryBatchRunResponse {
  discovered: number;
  staged_for_review: number;
  duplicates_filtered: number;
  message?: string;
}

export interface SourceResponse {
  source_id: string;
  scheme_id?: string | null;
  source_name: string;
  source_url: string;
  base_url?: string | null;
  authority?: string | null;
  authority_type?: string | null;
  source_type: string;
  fetch_frequency?: string | null;
  fetch_frequency_hours: number;
  is_active: boolean;
  last_fetched_at?: string | null;
  last_status: string;
  last_http_code?: number | null;
  consecutive_failures?: number;
  health_status?: 'HEALTHY' | 'DEGRADED' | 'FAILED' | string;
  created_at: string;
}

export interface IngestionQualityMetricsResponse {
  total_canonical_schemes: number;
  total_candidates_discovered: number;
  candidates_staged_for_review: number;
  candidates_approved: number;
  candidates_rejected: number;
  candidates_officially_verified: number;
  candidates_duplicate_flagged: number;
  canonical_schemes_with_rules: number;
  canonical_schemes_with_documents: number;
  canonical_schemes_with_official_evidence: number;
  coverage_by_level: Record<string, number>;
  top_ministries: Record<string, number>;
  top_categories: Record<string, number>;
  state_coverage_count: number;
}

export interface SchedulerLastRunMetrics {
  run_id?: string;
  started_at?: string | null;
  completed_at?: string | null;
  status?: string;
  records_seen: number;
  records_changed: number;
  records_unchanged: number;
  records_failed: number;
  records_staged: number;
  records_needing_review: number;
  sources_checked: number;
  sources_succeeded: number;
  sources_failed: number;
  unchanged_sources: number;
  changed_sources: number;
  new_schemes_detected: number;
  modified_schemes_detected: number;
  deactivation_candidates: number;
  validation_failures: number;
  pending_admin_reviews: number;
}

export interface SchedulerStatusResponse {
  scheduler_enabled: boolean;
  is_running: boolean;
  is_executing_cycle: boolean;
  cadence: string;
  interval_hours: number;
  interval_days: number;
  interval_minutes: number;
  last_run_id?: string | null;
  last_run_status: string;
  last_run_time?: string | null;
  next_scheduled_run?: string | null;
  last_successful_run_at?: string | null;
  last_run?: SchedulerLastRunMetrics | null;
  pending_updates_count: number;
  sources_summary: {
    total_sources: number;
    active_sources: number;
    healthy_sources: number;
    degraded_sources: number;
    failed_sources: number;
  };
  last_cycle_metrics?: Record<string, any>;
}

