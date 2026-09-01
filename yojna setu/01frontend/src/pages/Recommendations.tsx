import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { profileApi } from '../api/profileApi';
import { recommendationApi } from '../api/recommendationApi';
import { aiApi } from '../api/aiApi';
import {
  BeneficiaryProfileInput,
  CitizenProfileResponse,
  MissingFieldDetail,
  RecommendationResponse,
  RecommendationItem,
  AIExplainableRecommendationResponse,
  NaturalLanguageExtractResponse,
} from '../types';
import { Alert } from '../components/Alert';
import { OfficialPortalModal } from '../components/OfficialPortalModal';
import { SaveSchemeButton } from '../components/SaveSchemeButton';
import { CompareButton } from '../components/CompareButton';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Award,
  Send,
  PenTool,
  Check,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  FileText,
  MapPin,
  HelpCircle,
  Calculator as CalcIcon,
  Sparkles,
  Info,
  User,
  Sliders,
  RefreshCw,
  ArrowRight
} from 'lucide-react';

type InputMode = 'PROFILE' | 'TYPE' | 'FORM';
type TabFilter = 'ELIGIBLE' | 'INSUFFICIENT' | 'INELIGIBLE' | 'ALL';

export const Recommendations: React.FC = () => {
  const { t } = useTranslation();
  const { user, isAuthenticated } = useAuth();

  // Canonical Citizen Profile State
  const [canonicalProfile, setCanonicalProfile] = useState<BeneficiaryProfileInput | null>(null);
  const [profileCompletion, setProfileCompletion] = useState<number>(0);
  const [missingProfileFields, setMissingProfileFields] = useState<MissingFieldDetail[]>([]);

  // Mode Selection State
  const [inputMode, setInputMode] = useState<InputMode>('PROFILE');

  // Text Input State
  const [userText, setUserText] = useState(
    'I am a 28 year old woman from Uttar Pradesh. I belong to SC category. My annual income is around 1.8 lakh. I want to start a small tailoring business with a project cost of 1 lakh.'
  );

  // Quick Form State
  const [formAge, setFormAge] = useState<number>(28);
  const [formGender, setFormGender] = useState<string>('FEMALE');
  const [formState, setFormState] = useState<string>('UTTAR_PRADESH');
  const [formSocialCategory, setFormSocialCategory] = useState<string>('SC');
  const [formIncomeSlab, setFormIncomeSlab] = useState<number>(180000);
  const [formNeed, setFormNeed] = useState<string>('START_BUSINESS');
  const [formBusinessStage, setFormBusinessStage] = useState<string>('NEW');
  const [formProjectCostSlab, setFormProjectCostSlab] = useState<number>(100000);
  const [formLoanRequired, setFormLoanRequired] = useState<boolean>(true);

  // Recommendation Results State
  const [topK] = useState(10);
  const [activeTab, setActiveTab] = useState<TabFilter>('ELIGIBLE');
  const [aiResult, setAiResult] = useState<AIExplainableRecommendationResponse | null>(null);
  const [standardResult, setStandardResult] = useState<RecommendationResponse | null>(null);
  const [extractionResult, setExtractionResult] = useState<NaturalLanguageExtractResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Modal State for Official Portal Redirection
  const [selectedSchemeForModal, setSelectedSchemeForModal] = useState<{ name: string; url?: string | null } | null>(null);

  // Track expanded transparency details per scheme
  const [expandedDetails, setExpandedDetails] = useState<Record<string, boolean>>({});

  // On mount, auto-load canonical citizen profile and trigger recommendation evaluation
  useEffect(() => {
    loadAndEvaluateProfile();
  }, [isAuthenticated]);

  const loadAndEvaluateProfile = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      let activeProf: BeneficiaryProfileInput | null = null;

      if (isAuthenticated) {
        const pRes = await profileApi.getProfile();
        setCanonicalProfile(pRes.profile);
        setProfileCompletion(pRes.completion_percentage);
        setMissingProfileFields(pRes.missing_fields);
        activeProf = pRes.profile;
      } else {
        const cached = localStorage.getItem('yojnasetu_citizen_profile');
        if (cached) {
          try {
            const parsed = JSON.parse(cached);
            setCanonicalProfile(parsed);
            activeProf = parsed;
          } catch (e) {
            console.warn('Failed parsing cached profile', e);
          }
        }
      }

      if (activeProf && (activeProf.age || activeProf.annual_income || activeProf.social_category)) {
        // Populate quick form state
        if (activeProf.age) setFormAge(activeProf.age);
        if (activeProf.gender) setFormGender(activeProf.gender);
        if (activeProf.state) setFormState(activeProf.state);
        if (activeProf.social_category) setFormSocialCategory(activeProf.social_category);
        if (activeProf.annual_income) setFormIncomeSlab(activeProf.annual_income);
        if (activeProf.project_cost) setFormProjectCostSlab(activeProf.project_cost);

        // Auto evaluate smart matching
        const res = await recommendationApi.getRecommendations(activeProf, topK);
        setStandardResult(res);
      }
    } catch (err: any) {
      console.warn('Auto evaluation error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetToStoredProfile = () => {
    if (!canonicalProfile) return;
    if (canonicalProfile.age) setFormAge(canonicalProfile.age);
    if (canonicalProfile.gender) setFormGender(canonicalProfile.gender);
    if (canonicalProfile.state) setFormState(canonicalProfile.state);
    if (canonicalProfile.social_category) setFormSocialCategory(canonicalProfile.social_category);
    if (canonicalProfile.annual_income) setFormIncomeSlab(canonicalProfile.annual_income);
    if (canonicalProfile.project_cost) setFormProjectCostSlab(canonicalProfile.project_cost);
    setSaveSuccessMsg(t('recommendations.resetSuccess', 'Form reset to your saved citizen profile values.'));
    setTimeout(() => setSaveSuccessMsg(null), 4000);
  };

  const handleSaveFormToProfile = async () => {
    setIsSavingProfile(true);
    setSaveSuccessMsg(null);
    setErrorMsg(null);
    try {
      const formProfile = buildProfileFromForm();
      if (isAuthenticated) {
        const res = await profileApi.updateProfile(formProfile);
        setCanonicalProfile(res.profile);
        setProfileCompletion(res.completion_percentage);
        setMissingProfileFields(res.missing_fields);
      } else {
        localStorage.setItem('yojnasetu_citizen_profile', JSON.stringify(formProfile));
        setCanonicalProfile(formProfile);
      }
      setSaveSuccessMsg(t('recommendations.profileUpdatedSuccess', 'Your Citizen Profile has been updated with these parameters!'));
      setTimeout(() => setSaveSuccessMsg(null), 5000);
    } catch (err: any) {
      setErrorMsg(t('recommendations.saveProfileError', 'Failed to update profile: ') + (err.response?.data?.detail || err.message));
    } finally {
      setIsSavingProfile(false);
    }
  };

  const toggleDetails = (schemeId: string) => {
    setExpandedDetails(prev => ({ ...prev, [schemeId]: !prev[schemeId] }));
  };

  const buildProfileFromForm = (): BeneficiaryProfileInput => {
    let sector = 'MICRO_FINANCE';
    let activity = 'SMALL_MICRO_BUSINESS';

    if (formNeed === 'START_BUSINESS') {
      sector = 'MICRO_FINANCE';
      activity = 'SMALL_MICRO_BUSINESS';
    } else if (formNeed === 'EXPAND_BUSINESS') {
      sector = 'MICRO_FINANCE';
      activity = 'BUSINESS_EXPANSION';
    } else if (formNeed === 'EDUCATION') {
      sector = 'EDUCATION';
      activity = 'HIGHER_EDUCATION';
    } else if (formNeed === 'SKILL_TRAINING') {
      sector = 'SKILL_DEVELOPMENT';
      activity = 'VOCATIONAL_TRAINING';
    } else if (formNeed === 'AGRICULTURE') {
      sector = 'AGRICULTURE';
      activity = 'FARMING_ALLIED';
    } else if (formNeed === 'HOUSING') {
      sector = 'HOUSING';
      activity = 'HOME_RENOVATION';
    }

    return {
      age: formAge,
      gender: formGender,
      state: formState,
      social_category: formSocialCategory === 'NOT_SPECIFIED' ? 'GENERAL' : formSocialCategory,
      is_sc: formSocialCategory === 'SC',
      annual_income: formIncomeSlab,
      sector: sector,
      activity_type: activity,
      business_stage: formBusinessStage,
      is_new_unit: formBusinessStage === 'NEW' || formBusinessStage === 'CONCEPT',
      project_cost: formProjectCostSlab,
      requested_loan_amount: formLoanRequired ? Math.round(formProjectCostSlab * 0.9) : 0,
      applicant_type: 'INDIVIDUAL',
    };
  };

  const handleFindSchemes = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);
    setAiResult(null);
    setStandardResult(null);

    try {
      if (inputMode === 'PROFILE' && canonicalProfile) {
        const res = await recommendationApi.getRecommendations(canonicalProfile, topK);
        setStandardResult(res);
      } else if (inputMode === 'FORM') {
        const formProfile = buildProfileFromForm();
        const res = await recommendationApi.getRecommendations(formProfile, topK);
        setStandardResult(res);
      } else {
        const ext = await aiApi.extractProfile(userText);
        setExtractionResult(ext);

        const formProfile = ext.extracted_profile;
        const res = await recommendationApi.getRecommendations(formProfile, topK);
        setStandardResult(res);

        const aiRes = await aiApi.getAIRecommendations({
          user_text: userText,
          profile: ext.extracted_profile,
          top_k: topK,
        });
        setAiResult(aiRes);
      }
    } catch (err: any) {
      setErrorMsg(t('recommendations.evalError', 'Could not find recommendations: ') + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const openPortalModal = (schemeName: string, officialUrl?: string | null) => {
    setSelectedSchemeForModal({ name: schemeName, url: officialUrl });
  };

  const getMatchLabel = (score: number) => {
    if (score >= 85) return t('recommendations.strongFit', 'Strong Fit');
    if (score >= 70) return t('recommendations.goodFit', 'Good Fit');
    if (score >= 50) return t('recommendations.moderateFit', 'Moderate Fit');
    return t('recommendations.basicFit', 'Basic Fit');
  };

  // Compile active list of items based on selected tab
  const getDisplayedItems = (): { items: RecommendationItem[]; emptyMessage: string } => {
    if (!standardResult) return { items: [], emptyMessage: t('recommendations.noEvalYet', 'No schemes evaluated yet.') };

    const eligible = standardResult.recommendations || [];
    const insufficient = standardResult.insufficient_info_schemes || [];
    const ineligible = standardResult.ineligible_schemes || [];

    if (activeTab === 'ELIGIBLE') {
      return {
        items: eligible,
        emptyMessage: t('recommendations.noEligible', 'No schemes passed all mandatory eligibility criteria for the provided profile.')
      };
    } else if (activeTab === 'INSUFFICIENT') {
      return {
        items: insufficient,
        emptyMessage: t('recommendations.noInsufficient', 'No schemes are pending missing profile information.')
      };
    } else if (activeTab === 'INELIGIBLE') {
      return {
        items: ineligible,
        emptyMessage: t('recommendations.noIneligible', 'No schemes were excluded by hard eligibility gates.')
      };
    } else {
      return {
        items: [...eligible, ...insufficient, ...ineligible],
        emptyMessage: t('recommendations.noSchemesFound', 'No evaluated schemes found.')
      };
    }
  };

  const { items: displayedItems, emptyMessage } = getDisplayedItems();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* ── Page Header ── */}
      <div className="bg-gradient-to-r from-gov-navy via-gov-blue to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-xl border-b-4 border-gov-saffron relative overflow-hidden flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 bg-gov-saffron/20 border border-gov-saffron/40 text-gov-saffron px-3.5 py-1 rounded-full text-xs font-bold tracking-wide">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            {t('recommendations.badge', 'Deterministic Smart Matching Engine')}
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
            {t('recommendations.title', 'Smart Scheme Matching & Explainable Eligibility')}
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            {t(
              'recommendations.desc',
              'Evaluates all 90 verified government schemes against your authoritative citizen profile. Displays exact, factual reasons for Why You Qualify, More Info Needed, or Why Disqualified.'
            )}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
          <Link
            to="/profile"
            className="inline-flex items-center justify-center gap-2 bg-white/10 hover:bg-white/20 text-white font-bold text-xs px-5 py-3 rounded-xl border border-white/20 transition"
          >
            <User className="w-4 h-4 text-amber-300" />
            {t('recommendations.editProfileBtn', 'View / Edit Profile')}
          </Link>
        </div>
      </div>

      {errorMsg && <Alert type="error">{errorMsg}</Alert>}
      {saveSuccessMsg && <Alert type="success">{saveSuccessMsg}</Alert>}

      {/* ── Missing Profile Fields Guidance Banner (Requirement 7) ── */}
      {missingProfileFields.length > 0 && (
        <div className="bg-amber-50 border border-amber-300 rounded-2xl p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-amber-950">
                {t('recommendations.incompleteBannerTitle', 'Complete your profile to get more accurate scheme recommendations.')}
              </h3>
              <p className="text-xs text-amber-800 mt-0.5">
                {t('recommendations.incompleteBannerSub', 'The following parameters are currently missing from your Citizen Profile:')}
              </p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {missingProfileFields.map((mf) => (
                  <span
                    key={mf.field}
                    className="inline-flex items-center text-[11px] font-bold bg-white text-amber-900 border border-amber-300 px-2.5 py-0.5 rounded-md"
                  >
                    • {mf.label}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <Link
            to="/profile"
            className="shrink-0 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow transition flex items-center gap-1.5"
          >
            <User className="w-4 h-4" />
            {t('recommendations.completeProfileBtn', 'Complete Profile →')}
          </Link>
        </div>
      )}

      {/* ── Active Profile Synchronized Bar ── */}
      {canonicalProfile && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-700 flex items-center justify-center font-bold">
              <User className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-900">
                  {t('recommendations.activeProfileTitle', 'Prefilled from your Citizen Profile')}:
                </span>
                <span className="text-[11px] font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-300">
                  {profileCompletion}% {t('recommendations.profileComplete', 'Complete')}
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-0.5">
                {[
                  canonicalProfile.gender || 'Any Gender',
                  canonicalProfile.age ? `Age ${canonicalProfile.age}` : null,
                  canonicalProfile.social_category ? `Category ${canonicalProfile.social_category}` : null,
                  canonicalProfile.annual_income ? `Income ₹${canonicalProfile.annual_income.toLocaleString('en-IN')}` : null,
                  canonicalProfile.state ? canonicalProfile.state.replace(/_/g, ' ') : null,
                  canonicalProfile.sector ? `Sector ${canonicalProfile.sector}` : null,
                ].filter(Boolean).join(' • ')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleFindSchemes()}
              disabled={isLoading}
              className="bg-gov-saffron hover:bg-orange-600 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow transition flex items-center gap-1.5 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              {t('recommendations.recalcBtn', 'Recalculate Smart Match')}
            </button>
            <Link
              to="/profile"
              className="text-xs font-bold text-gov-blue hover:underline px-2 py-1"
            >
              {t('recommendations.updateProfileLink', 'Update Profile →')}
            </Link>
          </div>
        </div>
      )}

      {/* ── 3-Way Input Choice Tab ── */}
      <div className="space-y-4">
        <h2 className="text-sm font-extrabold text-slate-900">
          {t('recommendations.chooseInputMethod', 'Evaluation Mode / Profile Input Source')}
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <button
            type="button"
            onClick={() => setInputMode('PROFILE')}
            className={`p-4 rounded-2xl border text-left transition flex flex-col justify-between space-y-2 ${
              inputMode === 'PROFILE'
                ? 'bg-sky-50 border-gov-blue ring-2 ring-gov-blue shadow-md'
                : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded-lg bg-sky-100 text-sky-800 flex items-center justify-center font-bold">
                <User className="w-4 h-4" />
              </div>
              {inputMode === 'PROFILE' && <Check className="w-4 h-4 text-gov-blue font-extrabold" />}
            </div>
            <div>
              <h3 className="font-extrabold text-slate-900 text-xs">{t('recommendations.modeProfile', '👤 Saved Citizen Profile')}</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">{t('recommendations.modeProfileDesc', 'Uses your authoritative saved profile parameters.')}</p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => setInputMode('TYPE')}
            className={`p-4 rounded-2xl border text-left transition flex flex-col justify-between space-y-2 ${
              inputMode === 'TYPE'
                ? 'bg-purple-50 border-purple-600 ring-2 ring-purple-500 shadow-md'
                : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded-lg bg-purple-100 text-purple-800 flex items-center justify-center font-bold">
                <PenTool className="w-4 h-4" />
              </div>
              {inputMode === 'TYPE' && <Check className="w-4 h-4 text-purple-600 font-extrabold" />}
            </div>
            <div>
              <h3 className="font-extrabold text-slate-900 text-xs">{t('recommendations.modeNatural', '✍️ Natural Language / Voice')}</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">{t('recommendations.modeNaturalDesc', 'Describe your situation in everyday sentences or Hindi.')}</p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => setInputMode('FORM')}
            className={`p-4 rounded-2xl border text-left transition flex flex-col justify-between space-y-2 ${
              inputMode === 'FORM'
                ? 'bg-emerald-50 border-emerald-600 ring-2 ring-emerald-500 shadow-md'
                : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
                <CheckCircle2 className="w-4 h-4" />
              </div>
              {inputMode === 'FORM' && <Check className="w-4 h-4 text-emerald-600 font-extrabold" />}
            </div>
            <div>
              <h3 className="font-extrabold text-slate-900 text-xs">{t('recommendations.modeQuickForm', '📋 Quick Override Form')}</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">{t('recommendations.modeQuickFormDesc', 'Temporarily simulate another age, category, or loan amount.')}</p>
            </div>
          </button>
        </div>
      </div>

      {/* INPUT INTERFACE 1: TEXT INPUT */}
      {inputMode === 'TYPE' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-md p-6 sm:p-8 space-y-6">
          <form onSubmit={handleFindSchemes} className="space-y-4">
            <label className="block font-extrabold text-slate-900 text-xs uppercase tracking-wider">
              {t('recommendations.describeLabel', 'Describe your background and project requirements:')}
            </label>
            <textarea
              value={userText}
              onChange={(e) => setUserText(e.target.value)}
              rows={4}
              placeholder={t('recommendations.typePlaceholder', 'e.g. I am a 28 year old woman from Uttar Pradesh belonging to SC category. My annual family income is ₹1.8 lakh. I want to start a small tailoring unit with a project cost of ₹1 lakh...')}
              className="w-full rounded-xl border-slate-300 shadow-sm focus:border-gov-blue focus:ring-gov-blue text-xs p-4 border outline-none leading-relaxed"
            />

            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>{t('recommendations.noStorageGuarantee', 'Natural language is parsed on-the-fly and never retained.')}</span>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="bg-gov-blue hover:bg-sky-900 text-white font-bold py-2.5 px-6 rounded-xl text-xs shadow transition flex items-center gap-2 disabled:opacity-50"
              >
                {isLoading ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Send className="w-4 h-4" /> {t('recommendations.evaluateBtn', 'Evaluate Eligibility & Rank')}
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* INPUT INTERFACE 2: QUICK FORM */}
      {inputMode === 'FORM' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-md p-6 sm:p-8 space-y-6">
          {/* Temporary Simulation Indicator & Profile Sync Options */}
          <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-sky-900">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-sky-600 shrink-0" />
              <span>
                {t('recommendations.simulatingNotice', 'Temporary simulation: Modifying these fields evaluates schemes without overwriting your saved profile.')}
              </span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={handleResetToStoredProfile}
                className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 font-bold transition flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3 text-slate-500" />
                {t('recommendations.resetToStored', 'Reset to Stored')}
              </button>
              <button
                type="button"
                onClick={handleSaveFormToProfile}
                disabled={isSavingProfile}
                className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-bold transition flex items-center gap-1 disabled:opacity-50 shadow-xs"
              >
                {isSavingProfile ? (
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <User className="w-3 h-3 text-sky-300" />
                )}
                {t('recommendations.updateMyProfileBtn', 'Update My Profile')}
              </button>
            </div>
          </div>

          <form onSubmit={handleFindSchemes} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 text-xs">
            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">{t('profile.age', 'Applicant Age')}</label>
              <input
                type="number"
                min={14}
                max={120}
                value={formAge}
                onChange={(e) => setFormAge(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-gov-blue outline-none font-medium"
                required
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">{t('profile.gender', 'Gender')}</label>
              <select
                value={formGender}
                onChange={(e) => setFormGender(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-gov-blue outline-none font-medium bg-white"
              >
                <option value="FEMALE">{t('gender.female', 'Female')}</option>
                <option value="MALE">{t('gender.male', 'Male')}</option>
                <option value="TRANSGENDER">{t('gender.transgender', 'Transgender')}</option>
                <option value="OTHER">{t('gender.other', 'Other')}</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">{t('profile.state', 'State')}</label>
              <select
                value={formState}
                onChange={(e) => setFormState(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-gov-blue outline-none font-medium bg-white"
              >
                <option value="ALL_INDIA">{t('states.allIndia', 'All India / Central Scheme')}</option>
                <option value="UTTAR_PRADESH">Uttar Pradesh</option>
                <option value="MAHARASHTRA">Maharashtra</option>
                <option value="BIHAR">Bihar</option>
                <option value="WEST_BENGAL">West Bengal</option>
                <option value="MADHYA_PRADESH">Madhya Pradesh</option>
                <option value="TAMIL_NADU">Tamil Nadu</option>
                <option value="RAJASTHAN">Rajasthan</option>
                <option value="KARNATAKA">Karnataka</option>
                <option value="GUJARAT">Gujarat</option>
                <option value="DELHI">Delhi</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">{t('profile.socialCategory', 'Social Category')}</label>
              <select
                value={formSocialCategory}
                onChange={(e) => setFormSocialCategory(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-gov-blue outline-none font-medium bg-white"
              >
                <option value="SC">{t('category.sc', 'Scheduled Caste (SC - NSFDC Concessional Loans)')}</option>
                <option value="OBC">{t('category.obc', 'Other Backward Class (OBC - NBCFDC Loans)')}</option>
                <option value="ST">{t('category.st', 'Scheduled Tribe (ST - NSTFDC Concessional Loans)')}</option>
                <option value="MINORITY">{t('category.minority', 'Notified Minority Community (NMDFC Schemes)')}</option>
                <option value="GENERAL">{t('category.general', 'General / Unreserved')}</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">{t('profile.annualIncome', 'Annual Family Income (₹)')}</label>
              <select
                value={formIncomeSlab}
                onChange={(e) => setFormIncomeSlab(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-gov-blue outline-none font-medium bg-white"
              >
                <option value={90000}>Below ₹1 Lakh (₹90,000)</option>
                <option value={180000}>₹1 Lakh – ₹2 Lakh (₹1,80,000)</option>
                <option value={300000}>₹2 Lakh – ₹3 Lakh (₹3,00,000)</option>
                <option value={500000}>₹3 Lakh – ₹5 Lakh (₹5,00,000)</option>
                <option value={1000000}>Above ₹5 Lakh (₹10,00,000)</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">{t('profile.projectCost', 'Project Cost')}</label>
              <select
                value={formProjectCostSlab}
                onChange={(e) => setFormProjectCostSlab(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-gov-blue outline-none font-medium bg-white"
              >
                <option value={50000}>Up to ₹50,000</option>
                <option value={100000}>₹1,00,000 (Micro Loan)</option>
                <option value={500000}>₹5,00,000 (Term Loan / Vikas)</option>
                <option value={1500000}>₹15,00,000 (Major Unit)</option>
                <option value={5000000}>Above ₹50,00,000</option>
              </select>
            </div>

            <div className="sm:col-span-2 lg:col-span-3 pt-2">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3.5 px-6 rounded-xl text-xs shadow-lg transition flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isLoading ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Send className="w-4 h-4" /> {t('recommendations.evaluateBtn', 'Evaluate Scheme Eligibility & Rank')}
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* RESULTS LIST SECTION */}
      {standardResult && (
        <div className="space-y-6 pt-4">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
            <div>
              <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
                <Award className="w-6 h-6 text-gov-saffron" />
                {t('recommendations.resultsTitle', 'Deterministic Scheme Eligibility & Rankings')}
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {t('recommendations.evalCount', { count: standardResult.evaluated_scheme_count, defaultValue: `Evaluated ${standardResult.evaluated_scheme_count} official schemes against your profile rules.` })}
              </p>
            </div>

            {/* Scheme Evaluation Summary Counters */}
            <div className="flex items-center gap-2 text-xs font-bold">
              <span className="bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-xl border border-emerald-200 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                {standardResult.eligible_scheme_count} {t('recommendations.tabEligible', 'Eligible')}
              </span>
              <span className="bg-amber-50 text-amber-700 px-3 py-1.5 rounded-xl border border-amber-200 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                {standardResult.insufficient_info_scheme_count} {t('recommendations.tabInfoNeeded', 'Info Needed')}
              </span>
              <span className="bg-rose-50 text-rose-700 px-3 py-1.5 rounded-xl border border-rose-200 flex items-center gap-1.5">
                <XCircle className="w-3.5 h-3.5 text-rose-600" />
                {standardResult.excluded_scheme_count} {t('recommendations.tabExcluded', 'Excluded')}
              </span>
            </div>
          </div>

          {/* Status Tabs Filter */}
          <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
            <button
              onClick={() => setActiveTab('ELIGIBLE')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                activeTab === 'ELIGIBLE'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              {t('recommendations.filterWhyQualify', 'Why You Qualify')} ({standardResult.eligible_scheme_count})
            </button>

            <button
              onClick={() => setActiveTab('INSUFFICIENT')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                activeTab === 'INSUFFICIENT'
                  ? 'bg-amber-600 text-white shadow-sm'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              {t('recommendations.filterMoreInfo', 'More Info Required')} ({standardResult.insufficient_info_scheme_count})
            </button>

            <button
              onClick={() => setActiveTab('INELIGIBLE')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                activeTab === 'INELIGIBLE'
                  ? 'bg-rose-600 text-white shadow-sm'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
              }`}
            >
              <XCircle className="w-3.5 h-3.5" />
              {t('recommendations.filterWhyNotQualify', "Why You Don't Qualify")} ({standardResult.excluded_scheme_count})
            </button>

            <button
              onClick={() => setActiveTab('ALL')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                activeTab === 'ALL'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              {t('recommendations.filterAll', 'All Evaluated')} ({standardResult.evaluated_scheme_count})
            </button>
          </div>

          {/* Recommendation / Evaluation Cards */}
          {displayedItems.length === 0 ? (
            <div className="bg-slate-50 border border-dashed border-slate-300 rounded-2xl p-8 text-center text-slate-600 text-sm">
              <Info className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              {emptyMessage}
            </div>
          ) : (
            <div className="space-y-6">
              {displayedItems.map((rec: RecommendationItem, idx: number) => {
                const matchPct = Math.round(rec.score || 50);
                const matchLabel = getMatchLabel(matchPct);
                const isExpanded = !!expandedDetails[rec.scheme_id];
                const officialUrl = rec.application_url || rec.official_portal || rec.official_source_url;

                const isEligible = rec.eligibility_status === 'ELIGIBLE';
                const isInsufficient = rec.eligibility_status === 'INSUFFICIENT_INFORMATION';
                const isIneligible = rec.eligibility_status === 'INELIGIBLE';

                // Pre-fill amount for calculator
                const requestedAmount = canonicalProfile?.requested_loan_amount || canonicalProfile?.project_cost || formProjectCostSlab || '';

                return (
                  <div
                    key={rec.scheme_id || idx}
                    className={`bg-white rounded-2xl border shadow-sm p-6 hover:shadow-md transition space-y-4 ${
                      isEligible
                        ? 'border-emerald-200 ring-1 ring-emerald-100'
                        : isInsufficient
                        ? 'border-amber-200 ring-1 ring-amber-100'
                        : 'border-slate-200 opacity-90'
                    }`}
                  >
                    {/* Header: Rank, Scheme Name, Status Badge, Score */}
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div className="flex items-start gap-3.5">
                        <div
                          className={`w-10 h-10 rounded-xl font-extrabold text-base flex items-center justify-center shrink-0 shadow ${
                            isEligible
                              ? 'bg-emerald-600 text-white'
                              : isInsufficient
                              ? 'bg-amber-500 text-white'
                              : 'bg-slate-400 text-white'
                          }`}
                        >
                          #{rec.rank || idx + 1}
                        </div>
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="text-lg font-bold text-slate-900 hover:text-gov-blue transition">
                              <Link to={`/schemes/${rec.scheme_id}?amount=${requestedAmount}`}>{rec.scheme_name}</Link>
                            </h3>
                            <span className="text-[11px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                              {rec.scheme_id}
                            </span>
                            {rec.is_direct_portal_scheme && (
                              <span className="text-[10px] font-bold bg-sky-100 text-sky-800 px-2 py-0.5 rounded-full">
                                Direct Govt Portal Scheme
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-2 mt-1.5">
                            {isEligible && (
                              <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 flex items-center gap-1 border border-emerald-300">
                                <CheckCircle2 className="w-3.5 h-3.5" /> ✓ Eligible
                              </span>
                            )}
                            {isInsufficient && (
                              <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-amber-100 text-amber-800 flex items-center gap-1 border border-amber-300">
                                <AlertTriangle className="w-3.5 h-3.5" /> ⚠ More information required
                              </span>
                            )}
                            {isIneligible && (
                              <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-rose-100 text-rose-800 flex items-center gap-1 border border-rose-300">
                                <XCircle className="w-3.5 h-3.5" /> ✕ Not eligible
                              </span>
                            )}
                            {rec.ministry && (
                              <span className="text-[11px] text-slate-500 hidden sm:inline">
                                • {rec.ministry}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Soft Fit Score Box */}
                      <div className="text-right bg-slate-50 px-4 py-2 rounded-xl border border-slate-200">
                        <div className="text-xl font-extrabold text-gov-navy">
                          {matchPct}% Fit
                        </div>
                        <span className="text-[11px] text-slate-600 font-bold">{matchLabel}</span>
                      </div>
                    </div>

                    {/* SECTION 1: WHY YOU QUALIFY (For Eligible Schemes) */}
                    {isEligible && (
                      <div className="bg-emerald-50/70 rounded-xl p-4 border border-emerald-200 text-xs leading-relaxed space-y-2 text-slate-800">
                        <div className="font-extrabold text-emerald-950 flex items-center gap-1.5 text-sm">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" /> {t('recommendations.whyQualifyTitle', 'Why you qualify')}
                        </div>
                        <ul className="space-y-1.5 pl-1">
                          {(rec.matched_rules && rec.matched_rules.length > 0
                            ? rec.matched_rules
                            : rec.eligibility_reasons
                          ).map((reason: string, rIdx: number) => (
                            <li key={rIdx} className="flex items-start gap-2">
                              <span className="text-emerald-700 font-bold shrink-0">✓</span>
                              <span className="text-slate-800">{reason}</span>
                            </li>
                          ))}
                          {rec.recommendation_reasons?.map((reason: string, rIdx: number) => (
                            <li key={`rec-${rIdx}`} className="flex items-start gap-2">
                              <span className="text-emerald-700 font-bold shrink-0">✓</span>
                              <span className="text-slate-800 font-medium">{reason}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* SECTION 2: WHY YOU DON'T QUALIFY (For Ineligible Schemes) */}
                    {isIneligible && (
                      <div className="bg-rose-50/80 rounded-xl p-4 border border-rose-200 text-xs leading-relaxed space-y-2 text-slate-800">
                        <div className="font-extrabold text-rose-950 flex items-center gap-1.5 text-sm">
                          <XCircle className="w-4 h-4 text-rose-600" /> {t('recommendations.whyNotQualifyTitle', "Why you don't qualify")}
                        </div>
                        <ul className="space-y-1.5 pl-1">
                          {(rec.failed_rules && rec.failed_rules.length > 0
                            ? rec.failed_rules
                            : rec.eligibility_reasons
                          ).map((reason: string, rIdx: number) => (
                            <li key={rIdx} className="flex items-start gap-2">
                              <span className="text-rose-700 font-bold shrink-0">✕</span>
                              <span className="text-slate-800 font-medium">{reason}</span>
                            </li>
                          ))}
                        </ul>
                        <div className="pt-2 border-t border-rose-200/80 text-[11px] text-rose-800 flex items-center gap-1">
                          <Info className="w-3.5 h-3.5 text-rose-600" />
                          <span>{t('recommendations.deterministicNote', 'Evaluated deterministically from official scheme eligibility rules.')}</span>
                        </div>
                      </div>
                    )}

                    {/* SECTION 3: MISSING INFORMATION (For Incomplete Schemes) */}
                    {isInsufficient && (
                      <div className="bg-amber-50/80 rounded-xl p-4 border border-amber-200 text-xs leading-relaxed space-y-3 text-slate-800">
                        <div className="flex items-center justify-between">
                          <div className="font-extrabold text-amber-950 flex items-center gap-1.5 text-sm">
                            <AlertTriangle className="w-4 h-4 text-amber-600" /> {t('recommendations.missingInfoTitle', 'Missing Information Required')}
                          </div>
                          <Link
                            to="/profile"
                            className="bg-amber-600 hover:bg-amber-700 text-white font-bold text-[11px] px-3 py-1.5 rounded-lg shadow-xs transition flex items-center gap-1"
                          >
                            <User className="w-3.5 h-3.5" /> {t('recommendations.completeProfileBtn', 'Complete Profile →')}
                          </Link>
                        </div>
                        <p className="text-slate-700 text-xs">
                          {t('recommendations.missingInfoDesc', 'The following required eligibility attributes were not provided on your profile:')}
                        </p>
                        <ul className="space-y-1.5 pl-1">
                          {(rec.missing_information && rec.missing_information.length > 0
                            ? rec.missing_information
                            : ["Additional demographic or financial parameters required."]
                          ).map((msg: string, rIdx: number) => (
                            <li key={rIdx} className="flex items-start gap-2">
                              <span className="text-amber-700 font-bold shrink-0">⚠</span>
                              <span className="text-slate-800">{msg}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Expandable Transparency / Scoring Audit Section */}
                    <div>
                      <button
                        onClick={() => toggleDetails(rec.scheme_id)}
                        className="text-xs font-bold text-slate-600 hover:text-slate-900 flex items-center gap-1 focus:outline-none"
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        {isExpanded ? t('recommendations.hideBreakdown', 'Hide Matching Breakdown') : t('recommendations.viewBreakdown', 'View Matching Factor Breakdown')}
                      </button>

                      {isExpanded && rec.score_breakdown && (
                        <div className="mt-3 p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-3">
                          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                            <span className="font-extrabold text-slate-900">Deterministic Scoring Dimensions (Sum = 100)</span>
                            <span className="font-mono text-slate-600">Total Score: {rec.score.toFixed(1)} / 100</span>
                          </div>

                          <div className="space-y-2">
                            {rec.score_breakdown.map((b, bIdx) => (
                              <div key={bIdx} className="flex items-start justify-between gap-3 text-slate-700">
                                <div className="space-y-0.5">
                                  <div className="flex items-center gap-1.5">
                                    {b.result === 'MATCH' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />}
                                    {b.result === 'PARTIAL_MATCH' && <CheckCircle2 className="w-3.5 h-3.5 text-amber-500 shrink-0" />}
                                    {b.result === 'NO_MATCH' && <XCircle className="w-3.5 h-3.5 text-rose-500 shrink-0" />}
                                    {b.result === 'NOT_EVALUATED' && <HelpCircle className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
                                    <span className="font-bold capitalize">{b.dimension.replace(/_/g, ' ')}</span>
                                  </div>
                                  <p className="text-[11px] text-slate-500 pl-5">{b.reason}</p>
                                </div>
                                <div className="text-right shrink-0 font-mono text-[11px]">
                                  <span className="font-bold text-slate-900">+{b.score.toFixed(1)}</span>
                                  <span className="text-slate-400"> / {b.max_weight.toFixed(1)}</span>
                                </div>
                              </div>
                            ))}
                          </div>

                          {rec.source_document && (
                            <div className="pt-2 border-t border-slate-200 text-[11px] text-slate-500 flex items-center gap-1">
                              <FileText className="w-3.5 h-3.5 text-slate-400" />
                              <span>Official Source: {rec.source_document}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Advisory notice */}
                    <div className="bg-slate-100/90 rounded-xl p-3 text-[11px] text-slate-600 border border-slate-200 flex items-start gap-2">
                      <Info className="w-3.5 h-3.5 text-sky-600 shrink-0 mt-0.5" />
                      <span>{t('howToApply.disclaimer', 'Eligibility guidance only. Final eligibility and approval are determined by the concerned government authority.')}</span>
                    </div>

                    {/* Action Buttons & Navigation Continuity */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100">
                      <div className="flex flex-wrap items-center gap-2 text-xs font-bold">
                        <SaveSchemeButton schemeId={rec.scheme_id} size="sm" />
                        <CompareButton schemeId={rec.scheme_id} variant="compact" />
                        <Link
                          to={`/schemes/${rec.scheme_id}?amount=${requestedAmount}`}
                          className="bg-slate-100 hover:bg-slate-200 text-slate-800 px-3 py-2 rounded-xl transition flex items-center gap-1"
                        >
                          <FileText className="w-3.5 h-3.5 text-sky-700" /> {t('recommendations.viewScheme', 'View Scheme Details')}
                        </Link>

                        {/* Scheme-Aware Financial CTA: Calculate EMI ONLY if Loan/Credit Scheme */}
                        {rec.is_credit_scheme !== false && (rec.max_loan_amount || rec.interest_rate !== undefined) ? (
                          <Link
                            to={`/schemes/${rec.scheme_id}?amount=${requestedAmount}#calculator`}
                            className="bg-emerald-50 hover:bg-emerald-100 text-emerald-800 px-3 py-2 rounded-xl transition flex items-center gap-1 border border-emerald-300 shadow-xs"
                          >
                            <CalcIcon className="w-3.5 h-3.5 text-emerald-600" /> {t('recommendations.calculateEmi', 'Calculate EMI')}
                          </Link>
                        ) : (
                          <span className="bg-slate-100 text-slate-600 px-3 py-2 rounded-xl text-xs font-medium border border-slate-200">
                            {rec.financial_category === 'GRANT_SUBSIDY' ? 'Capital Subsidy / Grant' : rec.financial_category === 'SCHOLARSHIP' ? 'Scholarship Assistance' : rec.financial_category === 'TRAINING_SKILL' ? 'Skill Training / Kit' : rec.financial_category === 'DIRECT_BENEFIT' ? 'Direct Benefit / DBT' : 'Welfare Guidance'}
                          </span>
                        )}

                        {isEligible && (
                          <Link
                            to={`/channel-partners?scheme_id=${rec.scheme_id}&state=${canonicalProfile?.state || ''}`}
                            className="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 px-3 py-2 rounded-xl transition flex items-center gap-1 border border-indigo-200 shadow-xs"
                          >
                            <MapPin className="w-3.5 h-3.5 text-indigo-600" /> {t('howToApply.ctaPartner', 'Find Authorized Channel Partners')}
                          </Link>
                        )}
                      </div>

                      {officialUrl && (
                        <button
                          onClick={() => openPortalModal(rec.scheme_name, officialUrl)}
                          className="bg-gov-saffron hover:bg-orange-600 text-white font-bold text-xs px-4 py-2 rounded-xl shadow transition flex items-center gap-1.5"
                        >
                          {t('howToApply.ctaPortal', 'Apply on Official Portal')} <ExternalLink className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* External Portal Safety Dialog */}
      <OfficialPortalModal
        isOpen={!!selectedSchemeForModal}
        onClose={() => setSelectedSchemeForModal(null)}
        schemeName={selectedSchemeForModal?.name || ''}
        officialUrl={selectedSchemeForModal?.url || ''}
      />
    </div>
  );
};
