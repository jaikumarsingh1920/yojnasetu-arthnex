import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { profileApi } from '../api/profileApi';
import { BeneficiaryProfileInput, CitizenProfileResponse, MissingFieldDetail } from '../types';
import { Alert } from '../components/Alert';
import {
  User,
  ShieldCheck,
  Sparkles,
  Save,
  CheckCircle2,
  AlertTriangle,
  Info,
  ArrowRight,
  Briefcase,
  GraduationCap,
  Building,
  Coins,
  MapPin,
  Lock,
  RefreshCw,
  Sliders,
  Award,
  ChevronRight,
  Check
} from 'lucide-react';

const INDIAN_STATES = [
  'ALL_INDIA',
  'ANDHRA_PRADESH',
  'ARUNACHAL_PRADESH',
  'ASSAM',
  'BIHAR',
  'CHHATTISGARH',
  'DELHI',
  'GOA',
  'GUJARAT',
  'HARYANA',
  'HIMACHAL_PRADESH',
  'JAMMU_AND_KASHMIR',
  'JHARKHAND',
  'KARNATAKA',
  'KERALA',
  'LADAKH',
  'MADHYA_PRADESH',
  'MAHARASHTRA',
  'MANIPUR',
  'MEGHALAYA',
  'MIZORAM',
  'NAGALAND',
  'ODISHA',
  'PUNJAB',
  'RAJASTHAN',
  'SIKKIM',
  'TAMIL_NADU',
  'TELANGANA',
  'TRIPURA',
  'UTTAR_PRADESH',
  'UTTARAKHAND',
  'WEST_BENGAL',
];

const SECTORS = [
  { value: 'MSME', label: 'Micro, Small & Medium Enterprise (MSME)' },
  { value: 'AGRICULTURE', label: 'Agriculture, Dairy & Allied Activities' },
  { value: 'HANDICRAFTS', label: 'Handicrafts, Handloom & Artisan Trades' },
  { value: 'TEXTILES', label: 'Textiles, Garments & Tailoring' },
  { value: 'SERVICES', label: 'Service Sector (Transport, Repair, Salons, etc.)' },
  { value: 'TRADING', label: 'Retail & Wholesale Trading' },
  { value: 'FOOD_PROCESSING', label: 'Food Processing & Agribusiness' },
  { value: 'SANITATION', label: 'Sanitation & Waste Management' },
  { value: 'GREEN_ENERGY', label: 'Solar & Renewable Green Energy' },
  { value: 'HEALTHCARE', label: 'Healthcare & Wellness' },
  { value: 'EDUCATION', label: 'Education & Skill Development' },
];

export const Profile: React.FC = () => {
  const { t } = useTranslation();
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [profileData, setProfileData] = useState<BeneficiaryProfileInput>({
    age: 28,
    gender: 'FEMALE',
    state: 'MAHARASHTRA',
    district: '',
    social_category: 'SC',
    is_sc: true,
    is_pwd: false,
    is_minority: false,
    annual_income: 180000,
    employment_status: 'SELF_EMPLOYED',
    education_level: '10TH_PASS',
    applicant_type: 'INDIVIDUAL',
    entrepreneur_type: 'MICRO',
    is_artisan: false,
    is_farmer: false,
    is_street_vendor: false,
    is_safai_karamchari: false,
    business_stage: 'NEW_BUSINESS',
    is_new_unit: true,
    sector: 'MSME',
    activity_type: 'TRADITIONAL_TRADE_18',
    project_cost: 100000,
    requested_loan_amount: 90000,
    collateral_available: false,
    application_route: 'PARTNER_ASSISTED',
  });

  const [completionScore, setCompletionScore] = useState<number>(0);
  const [missingFields, setMissingFields] = useState<MissingFieldDetail[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setIsLoading(true);
    try {
      if (isAuthenticated) {
        const res = await profileApi.getProfile();
        setProfileData(res.profile);
        setCompletionScore(res.completion_percentage);
        setMissingFields(res.missing_fields);
      } else {
        // Load guest profile from localStorage if exists
        const cached = localStorage.getItem('yojnasetu_citizen_profile');
        if (cached) {
          const parsed = JSON.parse(cached);
          setProfileData(parsed);
        }
        calculateGuestScore(profileData);
      }
    } catch (err: any) {
      console.warn('Profile fetch error, using local fallback:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const calculateGuestScore = (prof: BeneficiaryProfileInput) => {
    let count = 0;
    const coreKeys = ['age', 'gender', 'state', 'social_category', 'annual_income', 'applicant_type', 'education_level', 'sector', 'business_stage', 'project_cost'];
    coreKeys.forEach(k => {
      if ((prof as any)[k] !== undefined && (prof as any)[k] !== null && (prof as any)[k] !== '') {
        count++;
      }
    });
    setCompletionScore(Math.round((count / coreKeys.length) * 100));
  };

  const handleChange = (field: keyof BeneficiaryProfileInput, value: any) => {
    setProfileData(prev => {
      const updated = { ...prev, [field]: value };
      if (field === 'social_category') {
        if (value === 'SC') updated.is_sc = true;
        else if (['ST', 'OBC', 'GENERAL', 'MINORITY'].includes(value)) updated.is_sc = false;
      }
      return updated;
    });
  };

  const handleSave = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsSaving(true);
    setFeedback(null);

    try {
      // Validate bounds
      if (profileData.age && (profileData.age < 14 || profileData.age > 120)) {
        throw new Error(t('profile.invalidAge', 'Age must be between 14 and 120 years.'));
      }
      if (profileData.annual_income && profileData.annual_income < 0) {
        throw new Error(t('profile.invalidIncome', 'Annual income cannot be negative.'));
      }
      if (profileData.project_cost && profileData.project_cost < 0) {
        throw new Error(t('profile.invalidCost', 'Project cost cannot be negative.'));
      }

      if (isAuthenticated) {
        const res = await profileApi.updateProfile(profileData);
        setProfileData(res.profile);
        setCompletionScore(res.completion_percentage);
        setMissingFields(res.missing_fields);
      } else {
        localStorage.setItem('yojnasetu_citizen_profile', JSON.stringify(profileData));
        calculateGuestScore(profileData);
      }

      setFeedback({
        type: 'success',
        message: t('profile.saveSuccess', 'Citizen profile updated and verified successfully! Smart matching is ready.'),
      });
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || err.message || t('profile.saveError', 'Failed to save profile. Please check inputs.'),
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveAndMatch = async () => {
    await handleSave();
    navigate('/recommendations');
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* ── Top Header Banner ── */}
      <div className="bg-gradient-to-r from-gov-navy via-gov-blue to-slate-900 text-white p-6 sm:p-8 rounded-3xl shadow-xl border-b-4 border-gov-saffron flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 bg-sky-900/60 text-sky-300 text-xs font-bold px-3 py-1 rounded-full border border-sky-700">
            <ShieldCheck className="w-4 h-4 text-sky-400" />
            {t('profile.canonicalBadge', 'Authoritative Citizen Profile')}
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            {t('profile.title', 'Citizen Profile & Eligibility Parameters')}
          </h1>
          <p className="text-slate-300 text-sm max-w-2xl leading-relaxed">
            {t(
              'profile.subtitle',
              'Your structured profile acts as the single source of truth for deterministic eligibility evaluation across all 90 government schemes. Zero document uploads required.'
            )}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
          <button
            type="button"
            onClick={handleSaveAndMatch}
            disabled={isSaving}
            className="inline-flex items-center justify-center gap-2 bg-gov-saffron hover:bg-orange-600 text-white font-bold text-sm px-6 py-3 rounded-xl shadow-lg shadow-orange-950/20 transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-amber-200" />
            {t('profile.smartMatchCTA', 'Find Matching Schemes →')}
          </button>
        </div>
      </div>

      {feedback && (
        <Alert type={feedback.type}>
          <div className="flex items-center justify-between">
            <span>{feedback.message}</span>
            {feedback.type === 'success' && (
              <Link to="/recommendations" className="text-xs font-bold underline ml-4 hover:opacity-80">
                {t('profile.viewRecommendations', 'View Smart Recommendations →')}
              </Link>
            )}
          </div>
        </Alert>
      )}

      {/* ── Completion & Missing Fields Banner ── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col md:flex-row items-center gap-6 justify-between">
        <div className="flex items-center gap-4">
          <div className="relative w-16 h-16 flex items-center justify-center">
            <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-slate-100"
                strokeWidth="3.5"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className={completionScore >= 80 ? 'text-emerald-500' : completionScore >= 50 ? 'text-amber-500' : 'text-gov-blue'}
                strokeDasharray={`${completionScore}, 100`}
                strokeWidth="3.5"
                strokeLinecap="round"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <span className="absolute text-sm font-black text-slate-900">{completionScore}%</span>
          </div>

          <div>
            <h3 className="text-base font-bold text-slate-900">
              {t('profile.completionTitle', 'Profile Readiness Score')}
            </h3>
            <p className="text-xs text-slate-500">
              {completionScore >= 80
                ? t('profile.completeReady', 'Comprehensive profile — all 90 schemes can be evaluated accurately.')
                : t('profile.completePending', 'Complete missing details below to unlock more accurate scheme matches.')}
            </p>
          </div>
        </div>

        {missingFields.length > 0 && (
          <div className="flex flex-wrap gap-2 items-center justify-end">
            <span className="text-xs font-semibold text-slate-500">{t('profile.missingFields', 'Missing Information')}:</span>
            {missingFields.slice(0, 4).map((mf) => (
              <span
                key={mf.field}
                className="inline-flex items-center gap-1 text-[11px] font-bold bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-1 rounded-full"
                title={mf.impact_reason}
              >
                <AlertTriangle className="w-3 h-3 text-amber-600" />
                {mf.label}
              </span>
            ))}
            {missingFields.length > 4 && (
              <span className="text-[11px] font-medium text-slate-500">+{missingFields.length - 4} more</span>
            )}
          </div>
        )}
      </div>

      {/* ── Main Profile Form ── */}
      <form onSubmit={handleSave} className="space-y-8">
        {/* ── Section 1: Personal & Social Background ── */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
            <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-700 flex items-center justify-center">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                {t('profile.sectionPersonal', '1. Personal & Social Identity')}
              </h2>
              <p className="text-xs text-slate-500">
                {t('profile.sectionPersonalDesc', 'Demographic parameters used for age criteria and affirmative social credit schemes.')}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Age */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.age', 'Applicant Age (Years)')} *
              </label>
              <input
                type="number"
                min={14}
                max={120}
                value={profileData.age ?? ''}
                onChange={(e) => handleChange('age', e.target.value ? parseInt(e.target.value) : null)}
                placeholder="e.g. 28"
                className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl px-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
                required
              />
            </div>

            {/* Gender */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.gender', 'Gender')} *
              </label>
              <select
                value={profileData.gender || ''}
                onChange={(e) => handleChange('gender', e.target.value || null)}
                className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl px-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
                required
              >
                <option value="FEMALE">{t('gender.female', 'Female (Unlocks Women Schemes & Subsidies)')}</option>
                <option value="MALE">{t('gender.male', 'Male')}</option>
                <option value="TRANSGENDER">{t('gender.transgender', 'Transgender')}</option>
                <option value="OTHER">{t('gender.other', 'Other')}</option>
              </select>
            </div>

            {/* Social Category */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.socialCategory', 'Social Category (Caste / Community)')} *
              </label>
              <select
                value={profileData.social_category || 'GENERAL'}
                onChange={(e) => handleChange('social_category', e.target.value || null)}
                className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl px-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
                required
              >
                <option value="SC">{t('category.sc', 'Scheduled Caste (SC - NSFDC Concessional Loans)')}</option>
                <option value="ST">{t('category.st', 'Scheduled Tribe (ST - NSTFDC Concessional Loans)')}</option>
                <option value="OBC">{t('category.obc', 'Other Backward Class (OBC - NBCFDC Loans)')}</option>
                <option value="MINORITY">{t('category.minority', 'Notified Minority Community (NMDFC Schemes)')}</option>
                <option value="GENERAL">{t('category.general', 'General / Unreserved')}</option>
              </select>
            </div>

            {/* State */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.state', 'State of Residence / Enterprise')} *
              </label>
              <select
                value={profileData.state || 'ALL_INDIA'}
                onChange={(e) => handleChange('state', e.target.value || null)}
                className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl px-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
                required
              >
                {INDIAN_STATES.map((st) => (
                  <option key={st} value={st}>
                    {st.replace(/_/g, ' ')}
                  </option>
                ))}
              </select>
            </div>

            {/* District */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.district', 'District (Optional)')}
              </label>
              <input
                type="text"
                value={profileData.district || ''}
                onChange={(e) => handleChange('district', e.target.value || null)}
                placeholder={t('profile.districtPlaceholder', 'e.g. Pune, Lucknow, Patna')}
                className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl px-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
              />
            </div>

            {/* Special Identity Checkboxes */}
            <div className="sm:col-span-2 lg:col-span-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
              <span className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
                {t('profile.specialAffirmations', 'Special Beneficiary Affirmations')}
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                <label className="flex items-center gap-2.5 cursor-pointer text-xs font-semibold text-slate-800">
                  <input
                    type="checkbox"
                    checked={!!profileData.is_pwd}
                    onChange={(e) => handleChange('is_pwd', e.target.checked)}
                    className="w-4 h-4 text-gov-blue rounded border-slate-300 focus:ring-gov-blue"
                  />
                  <span>{t('profile.isPwd', 'Person with Disability (Divyangjan)')}</span>
                </label>

                <label className="flex items-center gap-2.5 cursor-pointer text-xs font-semibold text-slate-800">
                  <input
                    type="checkbox"
                    checked={!!profileData.is_minority}
                    onChange={(e) => handleChange('is_minority', e.target.checked)}
                    className="w-4 h-4 text-gov-blue rounded border-slate-300 focus:ring-gov-blue"
                  />
                  <span>{t('profile.isMinority', 'Minority Community')}</span>
                </label>

                <label className="flex items-center gap-2.5 cursor-pointer text-xs font-semibold text-slate-800">
                  <input
                    type="checkbox"
                    checked={!!profileData.is_artisan}
                    onChange={(e) => handleChange('is_artisan', e.target.checked)}
                    className="w-4 h-4 text-gov-blue rounded border-slate-300 focus:ring-gov-blue"
                  />
                  <span>{t('profile.isArtisan', 'Traditional Artisan / Craftsman')}</span>
                </label>

                <label className="flex items-center gap-2.5 cursor-pointer text-xs font-semibold text-slate-800">
                  <input
                    type="checkbox"
                    checked={!!profileData.is_safai_karamchari}
                    onChange={(e) => handleChange('is_safai_karamchari', e.target.checked)}
                    className="w-4 h-4 text-gov-blue rounded border-slate-300 focus:ring-gov-blue"
                  />
                  <span>{t('profile.isSafai', 'Sanitation Worker / Safai Karamchari')}</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* ── Section 2: Economic & Income ── */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <Coins className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                {t('profile.sectionEconomic', '2. Economic Status & Family Income')}
              </h2>
              <p className="text-xs text-slate-500">
                {t('profile.sectionEconomicDesc', 'Required for income ceiling checks on means-tested welfare and interest subvention schemes.')}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Annual Income */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.annualIncome', 'Annual Family Income (INR ₹)')} *
              </label>
              <div className="relative">
                <span className="absolute left-4 top-2.5 text-slate-400 font-bold text-sm">₹</span>
                <input
                  type="number"
                  min={0}
                  step={1000}
                  value={profileData.annual_income ?? ''}
                  onChange={(e) => handleChange('annual_income', e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="e.g. 180000"
                  className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl pl-8 pr-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
                  required
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                {profileData.annual_income && profileData.annual_income <= 300000
                  ? '✓ Eligible for BPL / Concessional Social Welfare Schemes (Under ₹3.0 Lakh ceiling).'
                  : 'Above ₹3.0 Lakh limit for concessional welfare; eligible for MSME credit schemes.'}
              </p>
            </div>

            {/* Employment Status */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.employmentStatus', 'Current Employment Status')} *
              </label>
              <select
                value={profileData.employment_status || 'SELF_EMPLOYED'}
                onChange={(e) => handleChange('employment_status', e.target.value || null)}
                className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl px-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
                required
              >
                <option value="SELF_EMPLOYED">{t('emp.selfEmployed', 'Self Employed / Small Enterprise')}</option>
                <option value="UNEMPLOYED">{t('emp.unemployed', 'Unemployed (Seeking livelihood scheme)')}</option>
                <option value="SALARIED">{t('emp.salaried', 'Salaried Worker')}</option>
                <option value="STUDENT">{t('emp.student', 'Student / Trainee')}</option>
                <option value="DAILY_WAGE">{t('emp.dailyWage', 'Daily Wage Earner / Informal Worker')}</option>
              </select>
            </div>
          </div>
        </div>

        {/* ── Section 3: Education & Vocation ── */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
              <GraduationCap className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                {t('profile.sectionEducation', '3. Education & Vocation Category')}
              </h2>
              <p className="text-xs text-slate-500">
                {t('profile.sectionEducationDesc', 'Helps match schemes requiring 8th pass (e.g. PMEGP) or specialized artisan credit.')}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Education Level */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.educationLevel', 'Highest Education Completed')} *
              </label>
              <select
                value={profileData.education_level || '10TH_PASS'}
                onChange={(e) => handleChange('education_level', e.target.value || null)}
                className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl px-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
                required
              >
                <option value="ILLITERATE">{t('edu.illiterate', 'No Formal Education')}</option>
                <option value="BELOW_8TH">{t('edu.below8th', 'Below 8th Standard')}</option>
                <option value="8TH_PASS">{t('edu.8thPass', '8th Pass (Meets PMEGP base requirement)')}</option>
                <option value="10TH_PASS">{t('edu.10thPass', '10th Pass (Matriculation)')}</option>
                <option value="12TH_PASS">{t('edu.12thPass', '12th Pass (Higher Secondary)')}</option>
                <option value="DIPLOMA">{t('edu.diploma', 'Technical Diploma / ITI')}</option>
                <option value="GRADUATE">{t('edu.graduate', 'Graduate (Bachelor Degree)')}</option>
                <option value="POST_GRADUATE">{t('edu.postGraduate', 'Post Graduate / Masters')}</option>
              </select>
            </div>

            {/* Applicant Classification */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.applicantType', 'Applicant Vocation Classification')} *
              </label>
              <select
                value={profileData.applicant_type || 'INDIVIDUAL'}
                onChange={(e) => handleChange('applicant_type', e.target.value || null)}
                className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl px-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
                required
              >
                <option value="INDIVIDUAL">{t('appType.individual', 'Individual Citizen / Beneficiary')}</option>
                <option value="ARTISAN">{t('appType.artisan', 'Traditional Artisan / Craftsman (PM Vishwakarma)')}</option>
                <option value="FARMER">{t('appType.farmer', 'Farmer / Agricultural Producer')}</option>
                <option value="STREET_VENDOR">{t('appType.vendor', 'Street Vendor (PM SVANidhi)')}</option>
                <option value="WOMEN_ENTREPRENEUR">{t('appType.women', 'Women Entrepreneur (Stand-Up India / TREAD)')}</option>
                <option value="SHG">{t('appType.shg', 'Self Help Group (SHG / NRLM)')}</option>
                <option value="MICRO_ENTERPRISE">{t('appType.micro', 'Micro Enterprise Owner (PMEGP / MUDRA)')}</option>
                <option value="STUDENT">{t('appType.student', 'Student / Scholarship Seeker')}</option>
              </select>
            </div>
          </div>
        </div>

        {/* ── Section 4: Enterprise, Project & Loan Parameters ── */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
              <Briefcase className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                {t('profile.sectionEnterprise', '4. Business, Project & Credit Parameters')}
              </h2>
              <p className="text-xs text-slate-500">
                {t('profile.sectionEnterpriseDesc', 'Pre-fills the Scheme-Aware Financial Calculator and matches loan limit ceilings.')}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Sector */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.sector', 'Economic Sector')} *
              </label>
              <select
                value={profileData.sector || 'MSME'}
                onChange={(e) => handleChange('sector', e.target.value || null)}
                className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl px-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
                required
              >
                {SECTORS.map((sec) => (
                  <option key={sec.value} value={sec.value}>
                    {sec.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Business Stage */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.businessStage', 'Business Stage')} *
              </label>
              <select
                value={profileData.business_stage || 'NEW_BUSINESS'}
                onChange={(e) => handleChange('business_stage', e.target.value || null)}
                className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl px-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
                required
              >
                <option value="NEW_BUSINESS">{t('stage.new', 'New Unit / Greenfield Startup')}</option>
                <option value="EXISTING_BUSINESS">{t('stage.existing', 'Existing Business Expansion')}</option>
              </select>
            </div>

            {/* Project Cost */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.projectCost', 'Estimated Project Cost (INR ₹)')}
              </label>
              <div className="relative">
                <span className="absolute left-4 top-2.5 text-slate-400 font-bold text-sm">₹</span>
                <input
                  type="number"
                  min={0}
                  step={5000}
                  value={profileData.project_cost ?? ''}
                  onChange={(e) => {
                    const cost = e.target.value ? parseFloat(e.target.value) : null;
                    setProfileData(prev => ({
                      ...prev,
                      project_cost: cost,
                      requested_loan_amount: cost ? Math.round(cost * 0.9) : prev.requested_loan_amount
                    }));
                  }}
                  placeholder="e.g. 100000"
                  className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl pl-8 pr-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
                />
              </div>
            </div>

            {/* Requested Loan Amount */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.loanAmount', 'Requested Loan Amount (INR ₹)')}
              </label>
              <div className="relative">
                <span className="absolute left-4 top-2.5 text-slate-400 font-bold text-sm">₹</span>
                <input
                  type="number"
                  min={0}
                  step={5000}
                  value={profileData.requested_loan_amount ?? ''}
                  onChange={(e) => handleChange('requested_loan_amount', e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="e.g. 90000"
                  className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl pl-8 pr-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                {t('profile.calcSyncNote', 'Pre-fills the Financial Calculator across all matched loan schemes.')}
              </p>
            </div>

            {/* Collateral Available */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.collateral', 'Collateral Security Available?')}
              </label>
              <select
                value={profileData.collateral_available ? 'YES' : 'NO'}
                onChange={(e) => handleChange('collateral_available', e.target.value === 'YES')}
                className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl px-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
              >
                <option value="NO">{t('profile.noCollateral', 'No (Prefer CGTMSE / Collateral-Free Loans)')}</option>
                <option value="YES">{t('profile.hasCollateral', 'Yes (Collateral Security Available)')}</option>
              </select>
            </div>

            {/* Application Route */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                {t('profile.applicationRoute', 'Preferred Application Route')}
              </label>
              <select
                value={profileData.application_route || 'PARTNER_ASSISTED'}
                onChange={(e) => handleChange('application_route', e.target.value || null)}
                className="w-full bg-slate-50 border border-slate-300 focus:border-gov-blue focus:bg-white rounded-xl px-4 py-2.5 text-sm text-slate-900 font-medium outline-none transition"
              >
                <option value="PARTNER_ASSISTED">{t('route.partner', 'Authorized Channel Partner Assistance (Bank/SCA)')}</option>
                <option value="DIRECT_PORTAL">{t('route.portal', 'Direct Online Government Portal')}</option>
              </select>
            </div>
          </div>
        </div>

        {/* ── Privacy & Zero-Document Guarantee Box ── */}
        <div className="bg-sky-50 border border-sky-200 rounded-2xl p-5 flex items-start gap-4 text-sky-900">
          <Lock className="w-5 h-5 text-sky-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <h4 className="font-bold text-sky-950">
              {t('profile.privacyGuaranteeTitle', 'Privacy & Zero-Document Upload Policy')}
            </h4>
            <p className="text-sky-800 leading-relaxed">
              {t(
                'profile.privacyGuaranteeDesc',
                'YojnaSetu strictly stores only structured eligibility attributes. No personal identification documents, aadhaar scans, or certificates are ever uploaded or stored. Recommendations are calculated deterministically on the server.'
              )}
            </p>
          </div>
        </div>

        {/* ── Save and Action Buttons ── */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-200">
          <button
            type="button"
            onClick={() => loadProfile()}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 font-bold text-sm transition"
          >
            <RefreshCw className="w-4 h-4 text-slate-500" />
            {t('profile.resetBtn', 'Reset to Stored Values')}
          </button>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              type="submit"
              disabled={isSaving}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm transition shadow"
            >
              <Save className="w-4 h-4 text-slate-300" />
              {isSaving ? t('profile.saving', 'Saving...') : t('profile.saveBtn', 'Save Profile')}
            </button>

            <button
              type="button"
              onClick={handleSaveAndMatch}
              disabled={isSaving}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gov-saffron hover:bg-orange-600 text-white font-bold text-sm shadow-md transition"
            >
              <Sparkles className="w-4 h-4 text-amber-200" />
              {t('profile.saveAndSmartMatch', 'Save & Find Schemes →')}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
