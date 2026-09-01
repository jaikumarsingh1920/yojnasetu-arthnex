import React, { useState, useEffect } from 'react';
import {
  X,
  Save,
  AlertCircle,
  CheckCircle2,
  Building2,
  Users,
  Coins,
  ShieldCheck,
  FileText,
  ExternalLink,
  Info
} from 'lucide-react';
import { adminApi, SchemeCreateInput, SchemeUpdateInput, SchemeAuditItem } from '../../api/adminApi';

interface SchemeFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  schemeToEdit?: SchemeAuditItem | null;
}

export const SchemeFormModal: React.FC<SchemeFormModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  schemeToEdit,
}) => {
  const isEditing = Boolean(schemeToEdit);
  const [activeTab, setActiveTab] = useState<'IDENTITY' | 'ELIGIBILITY' | 'FINANCIAL' | 'ROUTING'>('IDENTITY');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form State
  const [formData, setFormData] = useState<SchemeCreateInput>({
    scheme_id: '',
    scheme_name: '',
    ministry: '',
    scheme_type: '',
    implementing_agency: '',
    purpose: '',
    target_beneficiary: '',
    marginalized_group: '',
    social_category: 'ALL',
    gender_condition: 'ALL',
    state_coverage: 'All India',
    state_restriction: 'ALL_INDIA',
    loan_available: 'NO',
    minimum_loan_amount: undefined,
    maximum_loan_amount: undefined,
    interest_rate_min: undefined,
    interest_rate_max: undefined,
    interest_rate_type: 'Fixed',
    repayment_period_min_months: undefined,
    repayment_period_max_months: undefined,
    subsidy_available: 'NO',
    subsidy_percentage: undefined,
    subsidy_details: '',
    grant_available: 'NO',
    grant_amount: undefined,
    application_mode: 'ONLINE',
    official_portal: '',
    official_source_url: '',
    required_documents: 'Aadhaar Card; Business PAN; Bank Statement',
    verification_status: 'VERIFIED',
    scheme_status: 'ACTIVE',
    reason: '',
  });

  useEffect(() => {
    if (schemeToEdit) {
      // Fetch detailed data for accurate editing
      adminApi.getSchemeAuditDetail(schemeToEdit.scheme_id).then((detail) => {
        const known = detail.known_fields || {};
        setFormData({
          scheme_id: detail.scheme_id,
          scheme_name: detail.scheme_name,
          ministry: detail.ministry,
          scheme_type: detail.sector || '',
          implementing_agency: detail.ministry || '',
          purpose: detail.purpose || '',
          target_beneficiary: detail.target_groups || '',
          marginalized_group: known.marginalized_group || '',
          social_category: known.social_category || 'ALL',
          gender_condition: known.gender_condition || 'ALL',
          state_coverage: detail.state_coverage || 'All India',
          state_restriction: known.state_restriction || 'ALL_INDIA',
          loan_available: (schemeToEdit.loan_available === 'YES' || schemeToEdit.loan_available === 'TRUE') ? 'YES' : 'NO',
          minimum_loan_amount: known.min_loan_amount || known.minimum_loan_amount || undefined,
          maximum_loan_amount: known.max_loan_amount || known.maximum_loan_amount || undefined,
          interest_rate_min: known.interest_rate_min || undefined,
          interest_rate_max: known.interest_rate_max || undefined,
          interest_rate_type: known.interest_rate_type || 'Fixed',
          repayment_period_min_months: known.repayment_period_min_months || undefined,
          repayment_period_max_months: known.repayment_period_max_months || undefined,
          subsidy_available: known.subsidy_available === 'YES' ? 'YES' : 'NO',
          subsidy_percentage: known.subsidy_percentage || undefined,
          subsidy_details: known.subsidy_details || '',
          grant_available: known.grant_available === 'YES' ? 'YES' : 'NO',
          grant_amount: known.grant_amount || undefined,
          application_mode: known.application_mode || 'ONLINE',
          official_portal: detail.official_portal || '',
          official_source_url: detail.official_source_url || '',
          required_documents: (detail.documents || []).map((d: any) => d.document_name).join('; ') || '',
          verification_status: detail.verification_status || 'VERIFIED',
          scheme_status: schemeToEdit.scheme_status || 'ACTIVE',
          reason: 'Administrative parameter update',
        });
      }).catch((err) => {
        console.error('Failed to load scheme detail for editing:', err);
      });
    } else {
      // Reset to fresh form
      setFormData({
        scheme_id: '',
        scheme_name: '',
        ministry: '',
        scheme_type: 'General Enterprise',
        implementing_agency: '',
        purpose: '',
        target_beneficiary: 'Eligible Citizens & Entrepreneurs',
        marginalized_group: '',
        social_category: 'ALL',
        gender_condition: 'ALL',
        state_coverage: 'All India',
        state_restriction: 'ALL_INDIA',
        loan_available: 'NO',
        minimum_loan_amount: undefined,
        maximum_loan_amount: undefined,
        interest_rate_min: undefined,
        interest_rate_max: undefined,
        interest_rate_type: 'Fixed',
        repayment_period_min_months: undefined,
        repayment_period_max_months: undefined,
        subsidy_available: 'NO',
        subsidy_percentage: undefined,
        subsidy_details: '',
        grant_available: 'NO',
        grant_amount: undefined,
        application_mode: 'ONLINE',
        official_portal: '',
        official_source_url: '',
        required_documents: 'Aadhaar Card; Business Registration; Bank Account Details',
        verification_status: 'VERIFIED',
        scheme_status: 'ACTIVE',
        reason: 'Initial scheme addition to catalog',
      });
    }
    setErrorMsg(null);
    setSuccessMsg(null);
    setActiveTab('IDENTITY');
  }, [schemeToEdit, isOpen]);

  if (!isOpen) return null;

  const handleChange = (field: keyof SchemeCreateInput, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    // Client-side Validation
    if (!formData.scheme_name.trim()) {
      setErrorMsg('Scheme Name is required.');
      setActiveTab('IDENTITY');
      return;
    }
    if (!formData.ministry.trim()) {
      setErrorMsg('Ministry / Department is required.');
      setActiveTab('IDENTITY');
      return;
    }
    if (!isEditing && !formData.scheme_id.trim()) {
      setErrorMsg('Scheme ID is required.');
      setActiveTab('IDENTITY');
      return;
    }
    if (!formData.official_source_url.trim().startsWith('http://') && !formData.official_source_url.trim().startsWith('https://')) {
      setErrorMsg('Official Source URL must be a valid link starting with http:// or https://');
      setActiveTab('ROUTING');
      return;
    }
    if (formData.official_portal && !formData.official_portal.trim().startsWith('http://') && !formData.official_portal.trim().startsWith('https://')) {
      setErrorMsg('Official Portal URL must begin with http:// or https://');
      setActiveTab('ROUTING');
      return;
    }

    if (formData.loan_available === 'YES') {
      if (formData.minimum_loan_amount && formData.maximum_loan_amount && Number(formData.minimum_loan_amount) > Number(formData.maximum_loan_amount)) {
        setErrorMsg('Minimum loan amount cannot exceed maximum loan amount.');
        setActiveTab('FINANCIAL');
        return;
      }
      if (formData.interest_rate_min && formData.interest_rate_max && Number(formData.interest_rate_min) > Number(formData.interest_rate_max)) {
        setErrorMsg('Minimum interest rate cannot exceed maximum interest rate.');
        setActiveTab('FINANCIAL');
        return;
      }
    }

    setIsSubmitting(true);

    try {
      if (isEditing && schemeToEdit) {
        const updatePayload: SchemeUpdateInput = {
          scheme_name: formData.scheme_name,
          ministry: formData.ministry,
          scheme_type: formData.scheme_type,
          implementing_agency: formData.implementing_agency,
          purpose: formData.purpose,
          target_beneficiary: formData.target_beneficiary,
          marginalized_group: formData.marginalized_group,
          social_category: formData.social_category,
          gender_condition: formData.gender_condition,
          state_coverage: formData.state_coverage,
          state_restriction: formData.state_restriction,
          loan_available: formData.loan_available,
          minimum_loan_amount: formData.loan_available === 'YES' ? formData.minimum_loan_amount : undefined,
          maximum_loan_amount: formData.loan_available === 'YES' ? formData.maximum_loan_amount : undefined,
          interest_rate_min: formData.loan_available === 'YES' ? formData.interest_rate_min : undefined,
          interest_rate_max: formData.loan_available === 'YES' ? formData.interest_rate_max : undefined,
          interest_rate_type: formData.interest_rate_type,
          repayment_period_min_months: formData.loan_available === 'YES' ? formData.repayment_period_min_months : undefined,
          repayment_period_max_months: formData.loan_available === 'YES' ? formData.repayment_period_max_months : undefined,
          subsidy_available: formData.subsidy_available,
          subsidy_percentage: formData.subsidy_percentage,
          subsidy_details: formData.subsidy_details,
          grant_available: formData.grant_available,
          grant_amount: formData.grant_amount,
          application_mode: formData.application_mode,
          official_portal: formData.official_portal,
          official_source_url: formData.official_source_url,
          required_documents: formData.required_documents,
          verification_status: formData.verification_status,
          scheme_status: formData.scheme_status,
          change_reason: formData.reason || 'Administrative update to scheme parameters',
        };
        await adminApi.updateScheme(schemeToEdit.scheme_id, updatePayload);
        setSuccessMsg(`Scheme '${formData.scheme_name}' successfully updated in canonical database.`);
      } else {
        await adminApi.createScheme(formData);
        setSuccessMsg(`Scheme '${formData.scheme_name}' successfully registered with ID ${formData.scheme_id}.`);
      }

      setTimeout(() => {
        onSuccess();
        onClose();
      }, 900);
    } catch (err: any) {
      console.error('Failed to save scheme:', err);
      const detail = err.response?.data?.detail;
      const message = Array.isArray(detail) ? detail.map((d: any) => d.msg || d.message).join(', ') : detail || 'Failed to save scheme. Please verify all inputs.';
      setErrorMsg(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 sm:p-6 border-b border-slate-200 bg-slate-900 text-white">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-rose-600/30 border border-rose-500/50 rounded-xl text-rose-400">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold">
                {isEditing ? `Edit Scheme: ${formData.scheme_id}` : 'Add New Government Scheme'}
              </h2>
              <p className="text-xs text-slate-300">
                {isEditing ? 'Update canonical parameters, financial terms, and statutory details.' : 'Register a new scheme into the verified single source of truth.'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Section Navigation Tabs */}
        <div className="flex border-b border-slate-200 bg-slate-50 px-6 py-2 overflow-x-auto gap-2 text-xs font-bold">
          {[
            { id: 'IDENTITY', label: '1. Identity & Classification', icon: Building2 },
            { id: 'ELIGIBILITY', label: '2. Beneficiary & Scope', icon: Users },
            { id: 'FINANCIAL', label: '3. Financial Facility', icon: Coins },
            { id: 'ROUTING', label: '4. Routing & Verification', icon: ShieldCheck },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg transition whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'text-slate-600 hover:bg-slate-200/60'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Alerts */}
        {errorMsg && (
          <div className="mx-6 mt-4 p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-3 text-rose-800 text-xs">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div className="font-medium">{errorMsg}</div>
          </div>
        )}
        {successMsg && (
          <div className="mx-6 mt-4 p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start gap-3 text-emerald-800 text-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div className="font-medium">{successMsg}</div>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* TAB 1: IDENTITY & CLASSIFICATION */}
          {activeTab === 'IDENTITY' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Scheme ID <span className="text-rose-600">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    disabled={isEditing}
                    placeholder="e.g. SIH26092-091"
                    value={formData.scheme_id}
                    onChange={(e) => handleChange('scheme_id', e.target.value.toUpperCase())}
                    className={`w-full px-3.5 py-2.5 text-xs rounded-xl border ${
                      isEditing ? 'bg-slate-100 text-slate-500 border-slate-200' : 'border-slate-300 focus:ring-2 focus:ring-slate-900'
                    }`}
                  />
                  <span className="text-[10px] text-slate-400 mt-1 block">Canonical permanent primary key.</span>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Scheme Status <span className="text-rose-600">*</span>
                  </label>
                  <select
                    value={formData.scheme_status}
                    onChange={(e) => handleChange('scheme_status', e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-2 focus:ring-slate-900 bg-white"
                  >
                    <option value="ACTIVE">ACTIVE (Visible in catalog, calculator, RAG)</option>
                    <option value="INACTIVE">INACTIVE (Hidden from public; preserved in admin)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Scheme Official Name <span className="text-rose-600">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Pradhan Mantri Formalisation of Micro food processing Enterprises (PMFME)"
                  value={formData.scheme_name}
                  onChange={(e) => handleChange('scheme_name', e.target.value)}
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Governing Ministry / Department <span className="text-rose-600">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Ministry of Micro, Small & Medium Enterprises"
                    value={formData.ministry}
                    onChange={(e) => handleChange('ministry', e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-2 focus:ring-slate-900"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Scheme Classification / Sector
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Credit & Financial Inclusion, Agriculture, Skill Training"
                    value={formData.scheme_type || ''}
                    onChange={(e) => handleChange('scheme_type', e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-2 focus:ring-slate-900"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Scheme Purpose / Statutory Objective
                </label>
                <textarea
                  rows={3}
                  placeholder="Describe the formal objective and scope of financial or advisory support..."
                  value={formData.purpose || ''}
                  onChange={(e) => handleChange('purpose', e.target.value)}
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-2 focus:ring-slate-900"
                />
              </div>
            </div>
          )}

          {/* TAB 2: BENEFICIARY & SCOPE */}
          {activeTab === 'ELIGIBILITY' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Target Beneficiaries
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Street vendors, Artisans, SC/ST entrepreneurs, Small farmers"
                    value={formData.target_beneficiary || ''}
                    onChange={(e) => handleChange('target_beneficiary', e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-2 focus:ring-slate-900"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Marginalized Group Focus
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. WOMEN, SC, ST, OBC, PWD, MINORITY, ALL"
                    value={formData.marginalized_group || ''}
                    onChange={(e) => handleChange('marginalized_group', e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-2 focus:ring-slate-900"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Social Category
                  </label>
                  <select
                    value={formData.social_category || 'ALL'}
                    onChange={(e) => handleChange('social_category', e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 bg-white"
                  >
                    <option value="ALL">All Categories</option>
                    <option value="SC">Scheduled Caste (SC)</option>
                    <option value="ST">Scheduled Tribe (ST)</option>
                    <option value="OBC">Other Backward Class (OBC)</option>
                    <option value="GENERAL">General</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Gender Condition
                  </label>
                  <select
                    value={formData.gender_condition || 'ALL'}
                    onChange={(e) => handleChange('gender_condition', e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 bg-white"
                  >
                    <option value="ALL">Any / All Genders</option>
                    <option value="FEMALE">Female Only</option>
                    <option value="MALE">Male Only</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    State Applicability
                  </label>
                  <input
                    type="text"
                    placeholder="All India or Specific State"
                    value={formData.state_coverage || 'All India'}
                    onChange={(e) => handleChange('state_coverage', e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300"
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: FINANCIAL FACILITY */}
          {activeTab === 'FINANCIAL' && (
            <div className="space-y-5">
              {/* Credit Facility Switch */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-slate-800 block">Credit / Loan Facility Available?</span>
                  <span className="text-[11px] text-slate-500 block">
                    Choose YES if this scheme provides bank-disbursed term loans or working capital loans.
                  </span>
                </div>
                <div className="flex items-center gap-2 bg-white p-1 rounded-xl border border-slate-200">
                  <button
                    type="button"
                    onClick={() => handleChange('loan_available', 'YES')}
                    className={`px-3 py-1 text-xs font-bold rounded-lg transition ${
                      formData.loan_available === 'YES' ? 'bg-emerald-600 text-white shadow' : 'text-slate-600'
                    }`}
                  >
                    YES
                  </button>
                  <button
                    type="button"
                    onClick={() => handleChange('loan_available', 'NO')}
                    className={`px-3 py-1 text-xs font-bold rounded-lg transition ${
                      formData.loan_available === 'NO' ? 'bg-rose-600 text-white shadow' : 'text-slate-600'
                    }`}
                  >
                    NO
                  </button>
                </div>
              </div>

              {formData.loan_available === 'YES' ? (
                <div className="space-y-4 p-4 bg-emerald-50/50 border border-emerald-200 rounded-xl">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">
                        Minimum Loan Amount (₹)
                      </label>
                      <input
                        type="number"
                        min={0}
                        placeholder="e.g. 10000"
                        value={formData.minimum_loan_amount ?? ''}
                        onChange={(e) => handleChange('minimum_loan_amount', e.target.value ? Number(e.target.value) : undefined)}
                        className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 bg-white"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">
                        Maximum Loan Amount (₹)
                      </label>
                      <input
                        type="number"
                        min={0}
                        placeholder="e.g. 1000000"
                        value={formData.maximum_loan_amount ?? ''}
                        onChange={(e) => handleChange('maximum_loan_amount', e.target.value ? Number(e.target.value) : undefined)}
                        className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 bg-white"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">
                        Interest Rate Min (%)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min={0}
                        max={100}
                        placeholder="e.g. 7.0"
                        value={formData.interest_rate_min ?? ''}
                        onChange={(e) => handleChange('interest_rate_min', e.target.value ? Number(e.target.value) : undefined)}
                        className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 bg-white"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">
                        Interest Rate Max (%)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min={0}
                        max={100}
                        placeholder="e.g. 11.5"
                        value={formData.interest_rate_max ?? ''}
                        onChange={(e) => handleChange('interest_rate_max', e.target.value ? Number(e.target.value) : undefined)}
                        className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 bg-white"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">
                        Max Tenure (Months)
                      </label>
                      <input
                        type="number"
                        min={1}
                        placeholder="e.g. 60"
                        value={formData.repayment_period_max_months ?? ''}
                        onChange={(e) => handleChange('repayment_period_max_months', e.target.value ? Number(e.target.value) : undefined)}
                        className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 bg-white"
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl flex items-center gap-2 text-slate-600 text-xs">
                  <Info className="w-4 h-4 text-slate-500 shrink-0" />
                  <span>Non-credit scheme. Loan amount, interest, and tenure parameters will be preserved as "Not Applicable".</span>
                </div>
              )}

              {/* Capital Subsidy Section */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-100">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Subsidy Available?
                  </label>
                  <select
                    value={formData.subsidy_available}
                    onChange={(e) => handleChange('subsidy_available', e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 bg-white"
                  >
                    <option value="NO">NO</option>
                    <option value="YES">YES (Capital Subsidy Provided)</option>
                  </select>
                </div>

                {formData.subsidy_available === 'YES' && (
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Subsidy Percentage (%)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min={0}
                      max={100}
                      placeholder="e.g. 25 or 35"
                      value={formData.subsidy_percentage ?? ''}
                      onChange={(e) => handleChange('subsidy_percentage', e.target.value ? Number(e.target.value) : undefined)}
                      className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 bg-white"
                    />
                  </div>
                )}
              </div>

              {/* Direct Benefit / Grant Section */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-100">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Direct Grant / Scholarship Available?
                  </label>
                  <select
                    value={formData.grant_available}
                    onChange={(e) => handleChange('grant_available', e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 bg-white"
                  >
                    <option value="NO">NO</option>
                    <option value="YES">YES (Grant / Direct Support)</option>
                  </select>
                </div>

                {formData.grant_available === 'YES' && (
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Grant / Benefit Amount (₹)
                    </label>
                    <input
                      type="number"
                      min={0}
                      placeholder="e.g. 50000"
                      value={formData.grant_amount ?? ''}
                      onChange={(e) => handleChange('grant_amount', e.target.value ? Number(e.target.value) : undefined)}
                      className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 bg-white"
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: ROUTING & VERIFICATION */}
          {activeTab === 'ROUTING' && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Official Source / Gazette URL <span className="text-rose-600">*</span>
                </label>
                <input
                  type="url"
                  required
                  placeholder="https://msme.gov.in/schemes/..."
                  value={formData.official_source_url}
                  onChange={(e) => handleChange('official_source_url', e.target.value)}
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-2 focus:ring-slate-900"
                />
                <span className="text-[10px] text-slate-400 mt-1 block">Must start with http:// or https://</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Official Citizen Application Portal Link
                </label>
                <input
                  type="url"
                  placeholder="https://pmsvanidhi.mohua.gov.in/"
                  value={formData.official_portal || ''}
                  onChange={(e) => handleChange('official_portal', e.target.value)}
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Application Mode
                  </label>
                  <select
                    value={formData.application_mode}
                    onChange={(e) => handleChange('application_mode', e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 bg-white"
                  >
                    <option value="ONLINE">ONLINE (Direct National Portal)</option>
                    <option value="PARTNER_ASSISTED">PARTNER_ASSISTED (Authorized Channel Partner / Bank)</option>
                    <option value="OFFLINE">OFFLINE (District Department Office)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Verification Status
                  </label>
                  <select
                    value={formData.verification_status}
                    onChange={(e) => handleChange('verification_status', e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 bg-white"
                  >
                    <option value="VERIFIED">VERIFIED (Statutory Gazette Confirmed)</option>
                    <option value="UNDER_REVIEW">UNDER_REVIEW</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Required Preparation Documents (Semicolon separated)
                </label>
                <input
                  type="text"
                  placeholder="Aadhaar Card; Business Registration Certificate; Bank Passbook"
                  value={formData.required_documents || ''}
                  onChange={(e) => handleChange('required_documents', e.target.value)}
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Changelog Audit Reason <span className="text-slate-400 font-normal">(Recorded in Scheme Changelog)</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. Budget 2026 guidelines adjustment or revised official portal link"
                  value={formData.reason || ''}
                  onChange={(e) => handleChange('reason', e.target.value)}
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300"
                />
              </div>
            </div>
          )}

          {/* Footer Controls */}
          <div className="pt-4 border-t border-slate-200 flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition"
            >
              Cancel
            </button>
            <div className="flex items-center gap-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center gap-1.5 px-5 py-2.5 text-xs font-extrabold text-white bg-slate-900 hover:bg-slate-800 disabled:opacity-50 rounded-xl shadow-md transition"
              >
                <Save className="w-4 h-4" />
                {isSubmitting ? 'Saving to Database...' : isEditing ? 'Save Changes' : 'Register Scheme'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
