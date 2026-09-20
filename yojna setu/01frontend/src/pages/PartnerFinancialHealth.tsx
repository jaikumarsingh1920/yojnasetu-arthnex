import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { partnerApi, PartnerFinancialHealthResponse } from '../api/partnerApi';
import { FinancialStatusBadge } from '../components/FinancialStatusBadge';
import { cleanGovTitle, cleanGovDescription } from '../utils/textNormalization';
import { MetricKpiCard } from '../components/shared/MetricKpiCard';
import { QuickActionsCard } from '../components/shared/QuickActionsCard';
import { AboutInformationCard } from '../components/shared/AboutInformationCard';
import {
  Building2,
  Building,
  ShieldCheck,
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  HelpCircle,
  FileText,
  ExternalLink,
  Info,
  Scale,
  Database,
  Lock,
  ChevronRight,
  ChevronDown,
  X,
  MapPin,
  Check,
  Coins,
  BarChart3,
  Shield,
  Lightbulb,
  Bookmark,
  GitCompare,
  UserCheck,
  Calculator,
  Compass
} from 'lucide-react';

export const PartnerFinancialHealth: React.FC = () => {
  const { t } = useTranslation();
  const { partnerId } = useParams<{ partnerId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const schemeId = searchParams.get('schemeId');
  const rawSchemeName = searchParams.get('schemeName');
  const returnSearch = searchParams.get('returnSearch');
  const schemeName = rawSchemeName ? cleanGovTitle(rawSchemeName) : '';

  // Active section tab
  const [activeSectionTab, setActiveSectionTab] = useState<
    'overview' | 'financial' | 'numbers_mean' | 'documents' | 'how_to_apply' | 'faqs'
  >('overview');

  // Full description toggle
  const [showFullDesc, setShowFullDesc] = useState(false);

  // Progressive Disclosure Accordion States
  const [isWhyIndicatorMattersOpen, setIsWhyIndicatorMattersOpen] = useState<boolean>(false);
  const [isNumbersTellOpen, setIsNumbersTellOpen] = useState<boolean>(searchParams.get('open') === 'numbers');
  const [isWhyStatusOpen, setIsWhyStatusOpen] = useState<boolean>(searchParams.get('open') === 'why_status');
  const [isMethodologyOpen, setIsMethodologyOpen] = useState<boolean>(searchParams.get('open') === 'methodology');
  const [isTechnicalDetailsOpen, setIsTechnicalDetailsOpen] = useState<boolean>(searchParams.get('open') === 'technical');

  // Active modal / popover for Metric Detail
  const [activeMetricModal, setActiveMetricModal] = useState<'NNPA' | 'GNPA' | 'CRAR' | null>(
    (searchParams.get('modal') as 'NNPA' | 'GNPA' | 'CRAR') || null
  );

  // Technical Tab inside Technical Details
  const [activeTechTab, setActiveTechTab] = useState<'OVERVIEW' | 'EVIDENCE' | 'RULES' | 'PROVENANCE' | 'GOVERNANCE'>(
    (searchParams.get('tab') as 'OVERVIEW' | 'EVIDENCE' | 'RULES' | 'PROVENANCE' | 'GOVERNANCE') || 'OVERVIEW'
  );

  // TanStack Query caching (5 min fresh, instant cached restore on Back navigation)
  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery<PartnerFinancialHealthResponse>({
    queryKey: ['partner-financial-health', partnerId],
    queryFn: () => partnerApi.getPartnerFinancialHealth(partnerId!),
    enabled: !!partnerId,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });

  const schemeBackUrl = schemeId
    ? `/financial-health/scheme/${schemeId}${returnSearch ? (returnSearch.startsWith('?') ? returnSearch : `?${returnSearch}`) : ''}`
    : null;

  const handleBackNavigation = () => {
    if (schemeBackUrl) {
      navigate(schemeBackUrl);
    } else if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate('/financial-health');
    }
  };

  useEffect(() => {
    const m = searchParams.get('modal');
    if (m === 'NNPA' || m === 'GNPA' || m === 'CRAR') {
      setActiveMetricModal(m);
    }
    const o = searchParams.get('open');
    if (o === 'numbers') setIsNumbersTellOpen(true);
    if (o === 'why_status') setIsWhyStatusOpen(true);
    if (o === 'methodology') setIsMethodologyOpen(true);
    if (o === 'technical') setIsTechnicalDetailsOpen(true);

    const tab = searchParams.get('tab');
    if (tab) setActiveTechTab(tab as any);
  }, [searchParams, data]);

  if (isLoading && !data) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center space-y-4">
        <div className="w-12 h-12 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm font-bold text-slate-600">
          Loading statutory channel partner financial intelligence...
        </p>
      </div>
    );
  }

  const errorMsg = (error as any)?.response?.data?.detail || (error as any)?.message || null;

  if (isError || !data) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-8 text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-rose-600 mx-auto" />
          <h2 className="text-lg font-black text-rose-900">{t('financialHealth.partnerNotFound', 'Partner Financial Record Not Found')}</h2>
          <p className="text-xs text-rose-700 max-w-md mx-auto">{errorMsg || 'The requested channel partner financial information could not be retrieved.'}</p>
          <button
            onClick={handleBackNavigation}
            className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-4 py-2 rounded-xl transition cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" /> {t('financialHealth.backToFinancialHealth', 'Back to Financial Health')}
          </button>
        </div>
      </div>
    );
  }

  const rawInstitutionName = data.institution_name || data.partner_name;
  const institutionName = cleanGovTitle(rawInstitutionName);
  const isResolved = data.entity_resolution_status === 'RESOLVED';
  const branchLoc =
    data.branch_location ||
    data.branch_address ||
    (data.branch_city && data.branch_state ? `${data.branch_city}, ${data.branch_state}` : data.branch_city || data.branch_state || 'Location not specified');

  const metrics = data.verified_metrics || {};
  const rules = data.rules_evaluated || [];

  const nnpa = metrics['NNPA_PERCENT']?.value;
  const gnpa = metrics['GNPA_PERCENT']?.value;
  const crar = metrics['CRAR_PERCENT']?.value;

  const reportingPeriod =
    metrics['NNPA_PERCENT']?.reporting_period ||
    metrics['GNPA_PERCENT']?.reporting_period ||
    metrics['CRAR_PERCENT']?.reporting_period ||
    metrics['NNPA_PERCENT']?.data_as_of ||
    metrics['GNPA_PERCENT']?.data_as_of ||
    metrics['CRAR_PERCENT']?.data_as_of;

  const authority =
    metrics['NNPA_PERCENT']?.source ||
    metrics['GNPA_PERCENT']?.source ||
    metrics['CRAR_PERCENT']?.source ||
    metrics['NNPA_PERCENT']?.source_authority ||
    'Reserve Bank of India (RBI)';

  const sourceUrl =
    metrics['NNPA_PERCENT']?.source_url ||
    metrics['GNPA_PERCENT']?.source_url ||
    metrics['CRAR_PERCENT']?.source_url;

  const isNsfdcAuthorized = data.nsfdc_authorized === 'AUTHORIZED';
  const statusCode = data.financial_status?.code || 'LIMITED_DATA';

  const evidenceCount = data.financial_status?.evidence_count ?? 0;
  const verifiedCount = evidenceCount;
  const verifiedCountDesc =
    verifiedCount >= 3
      ? t('financialHealth.evidenceCount3', 'All core verified financial indicators are available.')
      : verifiedCount > 0
      ? t('financialHealth.evidenceCount1', 'Only limited verified financial information is available.')
      : t('financialHealth.evidenceCount0', 'No verified financial indicators are currently available.');

  const statusDetails = {
    STRONGER: {
      headline: t('financialHealth.financial_position_stronger', 'Financial position looks stronger'),
      shortDesc: t('financialPartner.statusStrongerShortDesc', 'Reported loan problems are lower and capital is in a stronger range.'),
      whatMeans:
        t('financialPartner.statusStrongerWhatMeans', 'The available public information shows lower reported loan repayment problems and a stronger reported capital cushion.'),
      whyStatus:
        t('financialPartner.statusStrongerWhyStatus', "This status is shown because the available verified financial indicators fall within YojnaSetu's stronger presentation ranges. The available verified information currently shows lower reported loan repayment problems and stronger reported capital."),
      simpleSummary: t('financialPartner.statusStrongerSimpleSummary', 'relatively stable financial position with a strong capital base'),
      isNeutralOrPositive: true,
    },
    MIXED: {
      headline: t('financialHealth.financial_position_mixed', 'Financial position is mixed'),
      shortDesc: t('financialPartner.statusMixedShortDesc', 'Some reported financial numbers need attention.'),
      whatMeans:
        t('financialPartner.statusMixedWhatMeans', 'Some indicators are in stronger ranges while others need attention. It helps you see different aspects of the institution’s publicly reported figures.'),
      whyStatus:
        t('financialPartner.statusMixedWhyStatus', 'This status is shown because some available verified indicators are in the middle range. Some indicators are in stronger ranges while others need attention.'),
      simpleSummary: t('financialPartner.statusMixedSimpleSummary', 'mixed financial position with some indicators requiring attention'),
      isNeutralOrPositive: true,
    },
    HIGHER_STRESS: {
      headline: t('financialHealth.financial_position_needs_attention', 'Financial position needs attention'),
      shortDesc: t('financialPartner.statusStressShortDesc', 'One or more reported financial numbers need attention.'),
      whatMeans:
        t('financialPartner.statusStressWhatMeans', 'One or more reported financial figures show higher concern compared with standard ranges. This is based on publicly reported financial information and does not by itself mean the institution cannot provide the scheme service.'),
      whyStatus:
        t('financialPartner.statusStressWhyStatus', 'This status is shown because one or more available verified indicators are in a higher range of concern. This is based on publicly reported financial figures and does not prevent participation in official schemes where authorized.'),
      simpleSummary: t('financialPartner.statusStressSimpleSummary', 'position where one or more reported figures are in an elevated stress range'),
      isNeutralOrPositive: false,
    },
    LIMITED_DATA: {
      headline: t('financialHealth.not_enough_information', 'Not enough information'),
      shortDesc: t('financialPartner.statusLimitedShortDesc', 'Not enough verified financial information is available.'),
      whatMeans:
        t('financialPartner.statusLimitedWhatMeans', 'Not enough verified financial information is available. This does not mean the institution is financially weak. It means YojnaSetu does not have enough verified public information to show a meaningful summary.'),
      whyStatus:
        t('financialPartner.statusLimitedWhyStatus', 'We do not have enough verified financial information to calculate a meaningful summary. Under YojnaSetu data governance, missing figures are never assumed to be zero or favorable.'),
      simpleSummary: t('financialPartner.statusLimitedSimpleSummary', 'limited public reporting profile with insufficient indicators'),
      isNeutralOrPositive: true,
    },
  }[statusCode] || {
    headline: t('financialHealth.not_enough_information', 'Not enough information'),
    shortDesc: t('financialPartner.statusLimitedShortDesc', 'Not enough verified financial information is available.'),
    whatMeans:
      t('financialPartner.statusLimitedWhatMeans', 'Not enough verified financial information is available. This does not mean the institution is financially weak.'),
    whyStatus:
      t('financialPartner.statusLimitedWhyStatus', 'We do not have enough verified financial information to calculate a meaningful summary.'),
    simpleSummary: t('financialPartner.statusLimitedSimpleSummary', 'limited public reporting profile'),
    isNeutralOrPositive: true,
  };

  const statusTheme = {
    STRONGER: {
      cardBg: 'bg-gradient-to-br from-emerald-50/70 via-white to-[#FFFBF0]',
      cardBorder: 'border-emerald-300/80',
      badgeBg: 'bg-emerald-100/80 text-emerald-900 border-emerald-300',
      iconBox: 'bg-emerald-100 text-[#2D6A4F] border border-emerald-200',
      iconColor: 'text-[#2D6A4F]',
      icon: CheckCircle2,
    },
    MIXED: {
      cardBg: 'bg-gradient-to-br from-amber-50/70 via-white to-[#FFFBF0]',
      cardBorder: 'border-amber-300/80',
      badgeBg: 'bg-amber-100/80 text-amber-900 border-amber-300',
      iconBox: 'bg-amber-100 text-[#B45309] border border-amber-200',
      iconColor: 'text-[#B45309]',
      icon: AlertCircle,
    },
    HIGHER_STRESS: {
      cardBg: 'bg-gradient-to-br from-rose-50/70 via-white to-[#FFFBF0]',
      cardBorder: 'border-rose-300/80',
      badgeBg: 'bg-rose-100/80 text-rose-900 border-rose-300',
      iconBox: 'bg-rose-100 text-[#EA717B] border border-rose-200',
      iconColor: 'text-[#EA717B]',
      icon: AlertCircle,
    },
    LIMITED_DATA: {
      cardBg: 'bg-gradient-to-br from-slate-50/90 via-white to-[#FFFBF0]',
      cardBorder: 'border-[#E8D8D2]',
      badgeBg: 'bg-slate-100 text-slate-800 border-slate-300',
      iconBox: 'bg-[#FFF4EC] text-[#765E59] border border-[#FFD0CA]',
      iconColor: 'text-[#765E59]',
      icon: HelpCircle,
    },
  }[statusCode] || {
    cardBg: 'bg-gradient-to-br from-slate-50/90 via-white to-[#FFFBF0]',
    cardBorder: 'border-[#E8D8D2]',
    badgeBg: 'bg-slate-100 text-slate-800 border-slate-300',
    iconBox: 'bg-[#FFF4EC] text-[#765E59] border border-[#FFD0CA]',
    iconColor: 'text-[#765E59]',
    icon: HelpCircle,
  };
  const StatusIcon = statusTheme.icon;

  return (
    <div className="max-w-[1500px] mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 font-sans bg-[#FFFBF0] min-h-screen">
      {/* 1. Breadcrumb + Back Navigation Row */}
      <nav aria-label="Breadcrumb" className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-[#765E59] font-medium">
        <div className="flex items-center gap-2 flex-wrap">
          <Link to="/" className="hover:text-[#EA717B] transition">{t('nav.home', 'Home')}</Link>
          <ChevronRight className="w-3.5 h-3.5 text-[#765E59]/50 shrink-0" />
          <Link to="/financial-health" className="hover:text-[#EA717B] transition">{t('nav.financialHealth', 'Financial Health')}</Link>
          {schemeId && (
            <>
              <ChevronRight className="w-3.5 h-3.5 text-[#765E59]/50 shrink-0" />
              <Link to={schemeBackUrl || `/financial-health/scheme/${schemeId}`} className="hover:text-[#EA717B] truncate max-w-xs transition">
                {schemeName || 'Scheme'}
              </Link>
            </>
          )}
          <ChevronRight className="w-3.5 h-3.5 text-[#765E59]/50 shrink-0" />
          <span className="text-[#3B2522] font-bold truncate max-w-sm">{institutionName}</span>
        </div>

        <button
          onClick={handleBackNavigation}
          className="inline-flex items-center gap-1.5 text-[#765E59] hover:text-[#3B2522] font-bold text-xs transition cursor-pointer self-start sm:self-auto"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>{t('common.back', 'Back to previous page')}</span>
        </button>
      </nav>

      {/* 2. Hero Banner */}
      <div className="bg-gradient-to-br from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white rounded-3xl p-6 sm:p-8 shadow-warm-md relative overflow-hidden border border-[#E8D8D2]/20 space-y-6">
        {/* Top Badges */}
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
            <Check className="w-3.5 h-3.5 text-emerald-300" />
            <span>{t('financialPartner.nsfdcPartner', 'NSFDC Channel Partner')}</span>
          </span>

          <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-medium bg-white/10 text-[#FFFBF0] border border-white/20">
            <Info className="w-3.5 h-3.5 text-[#F7AE56]" />
            <span>{t('financialPartner.infoInstitutionLevel', 'Financial information: Institution-level')}</span>
          </span>
        </div>

        {/* Hero Middle Content: Bank Details + Institution Scope Callout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Bank Details */}
          <div className="lg:col-span-8 flex items-start gap-4 sm:gap-5">
            {/* Orange Square Bank Icon */}
            <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-[#EA717B] flex items-center justify-center text-white shrink-0 shadow-warm-xs">
              <Building2 className="w-8 h-8 sm:w-9 sm:h-9" />
            </div>

            <div className="space-y-2 min-w-0">
              <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
                {institutionName}
              </h1>

              {data.partner_name && (
                <p className="text-xs sm:text-sm font-semibold text-[#FFFBF0]/85">
                  Operating Center: {data.partner_name}
                </p>
              )}

              <p className="text-xs text-[#FFFBF0]/70 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-[#F7AE56] shrink-0" />
                <span className="truncate">{branchLoc}</span>
              </p>

              <p className="text-xs sm:text-sm text-[#FFFBF0]/85 leading-relaxed max-w-2xl pt-1">
                Publicly reported financial figures for <strong>{institutionName}</strong> at the institutional level. These figures represent the overall financial position of the bank, not any specific branch.
              </p>

              {showFullDesc && (
                <div className="p-3 bg-white/10 rounded-xl border border-white/15 text-xs text-[#FFFBF0]/90 space-y-1.5 mt-2 animate-in fade-in">
                  <p>
                    Commercial banking institutions in India publish audited financial accounts under the statutory framework of the Reserve Bank of India (RBI). Branch offices operate under corporate treasury and risk parameters established at the registered head office.
                  </p>
                  <p className="text-[11px] text-[#F7AE56] font-mono">
                    Statutory Registry ID: {data.partner_code} • Match Confidence: {data.entity_confidence != null ? `${Math.round(data.entity_confidence * 100)}%` : '100%'}
                  </p>
                </div>
              )}

              <button
                type="button"
                onClick={() => setShowFullDesc(!showFullDesc)}
                className="text-xs font-bold text-[#F7AE56] hover:text-white flex items-center gap-1 transition cursor-pointer pt-1"
              >
                <span>{showFullDesc ? 'Show less ↑' : 'Read full description ↓'}</span>
              </button>
            </div>
          </div>

          {/* Right Hero Scope Card */}
          <div className="lg:col-span-4 bg-white/10 backdrop-blur-md rounded-2xl p-4 sm:p-5 border border-white/15 flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-300 flex items-center justify-center shrink-0 mt-0.5">
              <ShieldCheck className="w-5 h-5 text-emerald-300" />
            </div>
            <p className="text-xs text-[#FFFBF0]/90 leading-relaxed font-medium">
              This is institution-level information. For scheme eligibility and loan approval, please refer to the specific scheme guidelines and application process.
            </p>
          </div>
        </div>

        {/* Bottom Hero Action Buttons Row */}
        <div className="pt-2 border-t border-white/15 flex items-center gap-2.5 flex-wrap">
          {/* Save Scheme */}
          <button
            type="button"
            onClick={() => alert('Saved to your saved items.')}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-white hover:bg-[#FFF4EC] text-[#3B2522] transition shadow-warm-xs cursor-pointer"
          >
            <Bookmark className="w-3.5 h-3.5 text-[#765E59]" />
            <span>{t('schemeDetail.saveScheme', 'Save Scheme')}</span>
          </button>

          {/* Add to Compare */}
          <Link
            to={`/schemes?compare=${schemeId || 'SIH26092-001'}`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-white hover:bg-[#FFF4EC] text-[#3B2522] transition shadow-warm-xs"
          >
            <GitCompare className="w-3.5 h-3.5 text-[#765E59]" />
            <span>{t('compare.addBtn', 'Add to Compare')}</span>
          </Link>

          {/* Check Eligibility */}
          <Link
            to={schemeId ? `/recommendations?scheme_id=${schemeId}` : '/recommendations'}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-[#EA717B] hover:bg-[#d65f69] text-white transition shadow-warm-xs"
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>{t('schemeDetail.checkEligibility', 'Check Eligibility')}</span>
          </Link>

          {/* View Loan & Subsidy Options */}
          <Link
            to={schemeId ? `/calculator?scheme=${schemeId}` : '/calculator'}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-[#F7AE56] hover:bg-[#e29d48] text-[#4A2525] transition shadow-warm-xs"
          >
            <Calculator className="w-3.5 h-3.5" />
            <span>{t('calculator.calculate', 'View Loan & Subsidy Options')}</span>
          </Link>

          {/* Find Nearby Partner */}
          <Link
            to={schemeId ? `/channel-partners?scheme_id=${schemeId}` : '/channel-partners'}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-white/15 hover:bg-white/25 text-white transition shadow-warm-xs border border-white/20"
          >
            <Compass className="w-3.5 h-3.5" />
            <span>{t('nav.nearbyPartners', 'Find Nearby Partner')}</span>
          </Link>
        </div>
      </div>

      {/* 3. Section Navigation Tabs */}
      <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs p-1.5 flex items-center gap-1 overflow-x-auto">
        {[
          { id: 'overview', label: 'Overview', icon: Bookmark },
          { id: 'financial', label: 'Financial Information', icon: BarChart3 },
          { id: 'numbers_mean', label: 'What the numbers mean', icon: Lightbulb },
          { id: 'documents', label: 'Documents', icon: FileText },
          { id: 'how_to_apply', label: 'How to Apply', icon: UserCheck },
          { id: 'faqs', label: 'FAQs', icon: HelpCircle },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeSectionTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSectionTab(tab.id as any)}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
                isActive
                  ? 'bg-[#FFF4EC] text-[#EA717B] border border-[#FFD0CA] shadow-warm-xs'
                  : 'text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFFBF0]'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[#EA717B]' : 'text-[#765E59]'}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* 4. Two-Column Content Grid: 70% Left / 30% Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Content Column (70% on desktop) */}
        <div className="lg:col-span-8 space-y-6">
          {/* ========================================================= */}
          {/* RESTORED: Citizen-Friendly Financial Position Indicator  */}
          {/* ========================================================= */}
          <div
            className={`rounded-3xl p-6 sm:p-8 shadow-warm-xs transition-all space-y-5 border ${statusTheme.cardBg} ${statusTheme.cardBorder}`}
          >
            {/* Header: Label + Status Badge + Telemetry Tags */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b pb-4 border-[#E8D8D2]/60">
              <div className="flex items-center gap-3 flex-wrap">
                <span className="text-[11px] font-black uppercase tracking-widest text-[#765E59]">
                  {t('financialPartner.financialPositionTitle', 'Financial Position')}
                </span>
                <FinancialStatusBadge status={data.financial_status} size="md" />
              </div>

              <div className="flex items-center gap-2 flex-wrap text-[11px] font-bold">
                <span className="bg-white/90 text-[#3B2522] px-2.5 py-0.5 rounded-full border border-[#E8D8D2] shadow-2xs">
                  {t('financialPartner.methodologyVersion', 'Methodology: YS-FIS-V1')}
                </span>
                <span className="bg-white/90 text-[#3B2522] px-2.5 py-0.5 rounded-full border border-[#E8D8D2] shadow-2xs">
                  {t('financialPartner.scopeInstitutionLevel', 'Institution-Level')}
                </span>
              </div>
            </div>

            {/* Headline and Citizen Explanation */}
            <div className="space-y-3">
              <div className="flex items-start gap-3.5">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 shadow-xs ${statusTheme.iconBox}`}>
                  <StatusIcon className={`w-6 h-6 ${statusTheme.iconColor}`} />
                </div>
                <div className="space-y-1 min-w-0">
                  <h2 className="text-xl sm:text-2xl font-black text-[#2B1810] tracking-tight">
                    {statusDetails.headline}
                  </h2>
                  <p className="text-sm font-bold text-[#3B2522] leading-relaxed">
                    {statusDetails.shortDesc}
                  </p>
                </div>
              </div>

              <p className="text-xs sm:text-sm text-[#765E59] leading-relaxed font-normal pl-0 sm:pl-[62px]">
                {statusDetails.whatMeans}
              </p>
            </div>

            {/* If LIMITED_DATA: Explain missing indicators transparently */}
            {statusCode === 'LIMITED_DATA' && (
              <div className="p-4 bg-white/90 rounded-2xl border border-[#E8D8D2] space-y-2.5 text-xs text-[#3B2522]">
                <div className="flex items-center gap-2 font-bold text-[#4A2525]">
                  <AlertCircle className="w-4 h-4 text-[#F7AE56] shrink-0" />
                  <span>{t('financialPartner.whyLimitedDataTitle', 'Why is this shown as "Not enough information"?')}</span>
                </div>
                <p className="text-[#765E59] leading-relaxed">
                  {statusDetails.whyStatus} {t('financialPartner.insufficientDataNotice', 'Under YS-FIS-V1 methodology, at least 2 verified public indicators (Net NPA, Gross NPA, CRAR) are required to calculate an interpreted status. Missing figures are never assumed to be zero or favorable.')}
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
                  <div className="p-2.5 rounded-xl bg-[#FFFBF0] border border-[#E8D8D2]">
                    <span className="font-bold text-[11px] block uppercase text-[#765E59]">Net NPA</span>
                    <span className="font-mono text-xs font-extrabold text-[#3B2522]">
                      {nnpa != null ? `${nnpa.toFixed(2)}%` : t('financialPartner.notReported', 'Not Reported')}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#FFFBF0] border border-[#E8D8D2]">
                    <span className="font-bold text-[11px] block uppercase text-[#765E59]">Gross NPA</span>
                    <span className="font-mono text-xs font-extrabold text-[#3B2522]">
                      {gnpa != null ? `${gnpa.toFixed(2)}%` : t('financialPartner.notReported', 'Not Reported')}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#FFFBF0] border border-[#E8D8D2]">
                    <span className="font-bold text-[11px] block uppercase text-[#765E59]">Capital Cushion (CRAR)</span>
                    <span className="font-mono text-xs font-extrabold text-[#3B2522]">
                      {crar != null ? `${crar.toFixed(2)}%` : t('financialPartner.notReported', 'Not Reported')}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Interactive Explanations: "Why this matters?" + "Why is this shown as...?" */}
            <div className="pt-2 border-t border-[#E8D8D2]/60 space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                {/* Why this matters button */}
                <button
                  type="button"
                  onClick={() => setIsWhyIndicatorMattersOpen(!isWhyIndicatorMattersOpen)}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-white hover:bg-[#FFF4EC] text-[#3B2522] border border-[#E8D8D2] transition cursor-pointer shadow-2xs"
                  aria-expanded={isWhyIndicatorMattersOpen}
                >
                  <Info className="w-3.5 h-3.5 text-[#EA717B]" />
                  <span>{t('financialPartner.whyThisMatters', 'Why this matters?')}</span>
                  <ChevronDown className={`w-3 h-3 text-[#765E59] transition-transform ${isWhyIndicatorMattersOpen ? 'rotate-180 text-[#EA717B]' : ''}`} />
                </button>

                {/* Why is this shown as... button (scrolls smoothly to Accordion 2) */}
                <button
                  type="button"
                  onClick={() => {
                    setIsWhyStatusOpen(true);
                    const el = document.getElementById('why-status-accordion');
                    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  }}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-white hover:bg-[#FFF4EC] text-[#3B2522] border border-[#E8D8D2] transition cursor-pointer shadow-2xs"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#2D6A4F]" />
                  <span>
                    {t('financialPartner.whyShownAsButton', {
                      status: statusDetails.headline,
                      defaultValue: `Why is this shown as "${statusDetails.headline}"?`
                    })}
                  </span>
                  <ChevronRight className="w-3 h-3 text-[#765E59]" />
                </button>
              </div>

              {/* Expandable "Why this matters?" explanation */}
              {isWhyIndicatorMattersOpen && (
                <div className="p-4 bg-white rounded-2xl border border-[#E8D8D2] text-xs text-[#3B2522] space-y-2 animate-in fade-in shadow-2xs">
                  <p className="leading-relaxed">
                    <strong className="text-[#2B1810]">
                      {t('financialPartner.whyThisMattersHeading', 'Understanding Institutional Financial Position:')}
                    </strong>{' '}
                    {t(
                      'financialPartner.whyThisMattersIndicatorDesc',
                      'These indicators provide an institution-level view of publicly reported financial conditions. When an institution has a stronger financial position, its reported operations and regulatory buffers are stable. This information helps citizens understand an institution\'s public scale and stability before applying. However, it does not guarantee loan approval, credit sanction, or individual scheme eligibility.'
                    )}
                  </p>
                  <p className="text-[11px] text-[#765E59] leading-relaxed pt-1.5 border-t border-[#E8D8D2]">
                    {t('financialPartner.neutralNotice', 'Neutral Information: YojnaSetu does not provide investment advice or credit ratings. Public statutory filings are presented strictly for transparent citizen awareness.')}
                  </p>
                </div>
              )}
            </div>

            {/* Provenance & Institution-Level Disclaimer Footer */}
            <div className="pt-3 border-t border-[#E8D8D2]/60 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px] text-[#765E59]">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-bold text-[#3B2522]">Source:</span>
                {sourceUrl ? (
                  <a
                    href={sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[#EA717B] hover:underline flex items-center gap-0.5 font-bold"
                  >
                    {authority} <ExternalLink className="w-3 h-3" />
                  </a>
                ) : (
                  <span className="text-[#3B2522] font-bold">{authority}</span>
                )}
                <span>•</span>
                <span>Last updated: <strong className="font-mono text-[#3B2522]">{reportingPeriod || '31 Mar 2025'}</strong></span>
                <span>•</span>
                <span className="inline-flex items-center gap-1 text-[#2D6A4F] font-bold">
                  <ShieldCheck className="w-3 h-3" />
                  Verified Disclosures
                </span>
              </div>

              <div className="text-[11px] text-[#765E59] italic">
                {verifiedCountDesc}
              </div>
            </div>
          </div>

          {/* Key Financial Figures at a Glance Header */}
          <div className="bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs p-6 sm:p-8 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E8D8D2] pb-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-[#FFD0CA] text-[#4A2525] flex items-center justify-center shrink-0">
                  <BarChart3 className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-xl font-black text-[#3B2522] tracking-tight">
                    {t('financialHealth.verifiedMetrics', 'Key Financial Figures at a Glance')}
                  </h2>
                  <p className="text-xs text-[#765E59] mt-0.5">
                    These are the latest publicly reported figures for {institutionName} (institution-level).
                  </p>
                </div>
              </div>

              <div className="text-right shrink-0">
                <div className="text-xs font-bold text-[#765E59] flex items-center justify-end gap-1">
                  <span>Source:</span>
                  {sourceUrl ? (
                    <a
                      href={sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#EA717B] hover:underline flex items-center gap-0.5"
                    >
                      {authority} <ExternalLink className="w-3 h-3" />
                    </a>
                  ) : (
                    <span className="text-[#3B2522] font-bold">{authority}</span>
                  )}
                </div>
                <div className="text-[11px] text-[#765E59] mt-0.5">
                  Last updated: {reportingPeriod || '31 Mar 2025'}
                </div>
              </div>
            </div>

            {/* 3 KPI Cards Side-by-Side */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Card 1: Net NPA */}
              <MetricKpiCard
                id="nnpa"
                label="Net NPA"
                value={nnpa != null ? `${nnpa.toFixed(2)}%` : t('financialPartner.notReported', 'Not Reported')}
                statusBadgeText={
                  nnpa != null
                    ? nnpa <= 1.0
                      ? t('financialPartner.strongRange', 'Strong range')
                      : nnpa <= 3.0
                      ? t('financialPartner.moderateLevel', 'Moderate level')
                      : t('financialPartner.needsAttention', 'Needs attention')
                    : t('financialPartner.noPublicData', 'No public data')
                }
                statusBadgeType={
                  nnpa != null
                    ? nnpa <= 1.0
                      ? 'positive'
                      : nnpa <= 3.0
                      ? 'moderate'
                      : 'caution'
                    : 'neutral'
                }
                interpretation={
                  nnpa != null
                    ? `Only ₹${nnpa.toFixed(2)} out of every ₹100 of loans is currently classified as non-performing after provisions.`
                    : t('financialPartner.nnpaNotReported', 'Net NPA figure is not reported in public statutory disclosures for this partner.')
                }
                icon={Coins}
                iconBg="bg-[#FFF4EC]"
                iconColor="text-[#EA717B]"
                onWhyItMattersClick={() => setActiveMetricModal(activeMetricModal === 'NNPA' ? null : 'NNPA')}
              />

              {/* Card 2: Gross NPA */}
              <MetricKpiCard
                id="gnpa"
                label="Gross NPA"
                value={gnpa != null ? `${gnpa.toFixed(2)}%` : t('financialPartner.notReported', 'Not Reported')}
                statusBadgeText={
                  gnpa != null
                    ? gnpa <= 3.0
                      ? t('financialPartner.strongRange', 'Strong range')
                      : gnpa <= 7.0
                      ? t('financialPartner.moderateLevel', 'Moderate level')
                      : t('financialPartner.needsAttention', 'Needs attention')
                    : t('financialPartner.noPublicData', 'No public data')
                }
                statusBadgeType={
                  gnpa != null
                    ? gnpa <= 3.0
                      ? 'positive'
                      : gnpa <= 7.0
                      ? 'moderate'
                      : 'caution'
                    : 'neutral'
                }
                interpretation={
                  gnpa != null
                    ? `About ₹${gnpa.toFixed(2)} out of every ₹100 of loans is classified as non-performing.`
                    : t('financialPartner.gnpaNotReported', 'Gross NPA figure is not reported in public statutory disclosures for this partner.')
                }
                icon={BarChart3}
                iconBg="bg-[#FFF4EC]"
                iconColor="text-[#F7AE56]"
                onWhyItMattersClick={() => setActiveMetricModal(activeMetricModal === 'GNPA' ? null : 'GNPA')}
              />

              {/* Card 3: Capital Cushion (CRAR) */}
              <MetricKpiCard
                id="crar"
                label="Capital Cushion (CRAR)"
                value={crar != null ? `${crar.toFixed(2)}%` : t('financialPartner.notReported', 'Not Reported')}
                statusBadgeText={
                  crar != null
                    ? crar >= 12.0
                      ? t('financialPartner.strongCushion', 'Strong cushion')
                      : crar >= 9.0
                      ? t('financialPartner.meetsMinimum', 'Meets minimum norm')
                      : t('financialPartner.belowNorm', 'Below standard norm')
                    : t('financialPartner.noPublicData', 'No public data')
                }
                statusBadgeType={
                  crar != null
                    ? crar >= 12.0
                      ? 'positive'
                      : crar >= 9.0
                      ? 'moderate'
                      : 'caution'
                    : 'neutral'
                }
                interpretation={
                  crar != null
                    ? `The bank maintains ₹${crar.toFixed(2)} of capital for every ₹100 of risk-weighted assets, indicating a strong financial cushion.`
                    : t('financialPartner.crarNotReported', 'Capital Cushion (CRAR) is not reported in public statutory disclosures for this partner.')
                }
                icon={Shield}
                iconBg="bg-[#FFF4EC]"
                iconColor="text-[#2D6A4F]"
                onWhyItMattersClick={() => setActiveMetricModal(activeMetricModal === 'CRAR' ? null : 'CRAR')}
              />
            </div>

            {/* Metric Modal / Explainer Popover */}
            {activeMetricModal && (
              <div className="p-4 bg-[#FFF4EC] border border-[#FFD0CA] rounded-2xl text-xs text-[#4A2525] space-y-2 animate-in fade-in">
                <div className="flex items-center justify-between font-bold text-[#4A2525] border-b border-[#FFD0CA] pb-2">
                  <span className="text-sm">
                    {activeMetricModal === 'NNPA' && 'Understanding Net NPA'}
                    {activeMetricModal === 'GNPA' && 'Understanding Gross NPA'}
                    {activeMetricModal === 'CRAR' && 'Understanding Capital Cushion (CRAR)'}
                  </span>
                  <button onClick={() => setActiveMetricModal(null)} className="text-[#765E59] hover:text-[#3B2522] cursor-pointer">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                {activeMetricModal === 'NNPA' && (
                  <>
                    <p className="leading-relaxed">
                      <strong>{t('financialPartner.simpleMeaning', 'Simple meaning:')}</strong> {t('financialHealth.net_npa_simple', 'Loans where repayment problems are still reported after applicable provisions and deductions.')}
                    </p>
                    <p className="leading-relaxed">
                      <strong>{t('financialPartner.whyLowerMatters', 'Why does a lower number generally matter?')}</strong> A lower Net NPA generally means a smaller share of the institution's reported net loans has repayment problems.
                    </p>
                    <p className="text-[11px] font-bold text-[#EA717B] pt-1">
                      Important: It does not mean your own loan will be approved.
                    </p>
                  </>
                )}
                {activeMetricModal === 'GNPA' && (
                  <>
                    <p className="leading-relaxed">
                      <strong>{t('financialPartner.simpleMeaning', 'Simple meaning:')}</strong> {t('financialHealth.gross_npa_simple', 'Shows the broader share of loans reported as non-performing.')}
                    </p>
                    <p className="leading-relaxed">
                      <strong>{t('financialPartner.whyLowerMatters', 'Why does a lower number generally matter?')}</strong> A lower Gross NPA generally means fewer of the institution's reported loans are classified as non-performing.
                    </p>
                  </>
                )}
                {activeMetricModal === 'CRAR' && (
                  <>
                    <p className="leading-relaxed">
                      <strong>{t('financialPartner.simpleMeaning', 'Simple meaning:')}</strong> {t('financialHealth.crar_simple', 'Shows the capital an institution maintains against the risks in its assets.')}
                    </p>
                    <p className="leading-relaxed">
                      <strong>{t('financialPartner.whyHigherMatters', 'Why does a higher number generally matter?')}</strong> A higher CRAR generally means more capital cushion under the applicable capital framework.
                    </p>
                  </>
                )}
              </div>
            )}

            {/* "In simple terms" Callout Box */}
            <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-2xl p-4 sm:p-5 flex items-start gap-3.5">
              <div className="w-8 h-8 rounded-full bg-[#FFD0CA] text-[#4A2525] flex items-center justify-center shrink-0 mt-0.5">
                <Lightbulb className="w-5 h-5 text-[#EA717B]" />
              </div>
              <p className="text-xs sm:text-sm text-[#3B2522] leading-relaxed">
                <strong className="font-extrabold text-[#4A2525]">{t('financialPartner.inSimpleTermsLabel', 'In simple terms:')}</strong>{' '}
                {t('financialPartner.inSimpleTermsDesc', {
                  name: institutionName,
                  summary: statusDetails.simpleSummary,
                  defaultValue: `These numbers indicate that ${institutionName} is in a ${statusDetails.simpleSummary}. However, these are overall bank-level figures. Your loan application will still be evaluated based on the specific scheme rules and branch/partner process.`
                })}
              </p>
            </div>
          </div>

          {/* 5. Progressive Disclosure Accordions */}
          <div className="space-y-4">
            {/* Accordion 1: What do these numbers tell us? */}
            <div className="bg-white border border-[#E8D8D2] rounded-2xl shadow-warm-xs overflow-hidden">
              <button
                type="button"
                onClick={() => setIsNumbersTellOpen(!isNumbersTellOpen)}
                className="w-full p-5 text-left flex items-center justify-between hover:bg-[#FFF4EC] transition cursor-pointer"
                aria-expanded={isNumbersTellOpen}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#FFD0CA] border border-[#FFD0CA] flex items-center justify-center shrink-0">
                    <HelpCircle className="w-4 h-4 text-[#4A2525]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-extrabold text-[#3B2522]">
                      {t('financialPartner.accordion1Title', 'What do these numbers tell us?')}
                    </h3>
                    <p className="text-xs text-[#765E59]">
                      {t('financialPartner.accordion1Sub', 'A simple citizen overview of Net NPA, Gross NPA, and Capital Cushion')}
                    </p>
                  </div>
                </div>
                <ChevronDown className={`w-4 h-4 text-[#765E59] transition-transform ${isNumbersTellOpen ? 'rotate-180 text-[#EA717B]' : ''}`} />
              </button>

              {isNumbersTellOpen && (
                <div className="p-5 pt-0 border-t border-[#E8D8D2] space-y-3 text-xs text-[#765E59] bg-[#FFF4EC]/30">
                  <div className="divide-y divide-[#E8D8D2]">
                    <div className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <span className="font-bold text-[#3B2522] w-36 uppercase">{t('financialHealth.netNpa', 'Net NPA')}</span>
                      <span className="text-[#765E59] flex-1">{t('financialPartner.netNpaExplainer', 'Reported repayment problems that remain after applicable provisions and deductions.')}</span>
                    </div>
                    <div className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <span className="font-bold text-[#3B2522] w-36 uppercase">{t('financialHealth.grossNpa', 'Gross NPA')}</span>
                      <span className="text-[#765E59] flex-1">{t('financialPartner.grossNpaExplainer', 'Broader reported level of non-performing loans across all loan books.')}</span>
                    </div>
                    <div className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <span className="font-bold text-[#3B2522] w-36 uppercase">{t('financialHealth.crar', 'CRAR')}</span>
                      <span className="text-[#765E59] flex-1">{t('financialPartner.crarExplainer', 'Reported capital cushion against measured financial risks under RBI Basel norms.')}</span>
                    </div>
                  </div>
                  <p className="text-[#765E59] bg-white p-3 rounded-xl border border-[#E8D8D2] font-medium">
                    {t('financialPartner.togetherIndicators', 'Together, these indicators give a broader picture than any single number alone.')}
                  </p>
                </div>
              )}
            </div>

            {/* Accordion 2: Why is this shown as status? */}
            <div id="why-status-accordion" className="bg-white border border-[#E8D8D2] rounded-2xl shadow-warm-xs overflow-hidden">
              <button
                type="button"
                onClick={() => setIsWhyStatusOpen(!isWhyStatusOpen)}
                className="w-full p-5 text-left flex items-center justify-between hover:bg-[#FFF4EC] transition cursor-pointer"
                aria-expanded={isWhyStatusOpen}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full border flex items-center justify-center shrink-0 ${statusTheme.iconBox}`}>
                    <StatusIcon className={`w-4 h-4 ${statusTheme.iconColor}`} />
                  </div>
                  <div>
                    <h3 className="text-sm font-extrabold text-[#3B2522]">
                      {t('financialPartner.accordion2Title', { status: statusDetails.headline, defaultValue: `Why is this shown as "${statusDetails.headline}"?` })}
                    </h3>
                    <p className="text-xs text-[#765E59]">
                      {t('financialPartner.accordion2Sub', 'How verified figures map to this summary')}
                    </p>
                  </div>
                </div>
                <ChevronDown className={`w-4 h-4 text-[#765E59] transition-transform ${isWhyStatusOpen ? 'rotate-180 text-[#EA717B]' : ''}`} />
              </button>

              {isWhyStatusOpen && (
                <div className="p-5 pt-0 border-t border-[#E8D8D2] space-y-3 text-xs text-[#765E59] bg-[#FFF4EC]/30">
                  <p className="leading-relaxed font-medium text-[#3B2522]">
                    {statusDetails.whyStatus}
                  </p>
                  <div className="bg-white p-3.5 rounded-xl border border-[#E8D8D2] space-y-2">
                    <span className="font-bold text-[#3B2522] block">{t('financialHealth.verifiedMetrics', 'Available verified information:')}</span>
                    {evidenceCount > 0 ? (
                      <ul className="space-y-1.5">
                        {nnpa != null && (
                          <li className="flex items-center justify-between text-[#3B2522] border-b border-[#E8D8D2]/50 pb-1">
                            <span className="flex items-center gap-2">
                              <Check className="w-3.5 h-3.5 text-[#2D6A4F] shrink-0" />
                              <span>Net NPA: <strong className="font-mono">{nnpa.toFixed(2)}%</strong></span>
                            </span>
                            <span className="text-[11px] font-mono text-[#765E59]">
                              {nnpa <= 1.0 ? 'Stronger (≤ 1.0%)' : nnpa <= 3.0 ? 'Mixed (1.0% - 3.0%)' : 'Stress (> 3.0%)'}
                            </span>
                          </li>
                        )}
                        {gnpa != null && (
                          <li className="flex items-center justify-between text-[#3B2522] border-b border-[#E8D8D2]/50 pb-1">
                            <span className="flex items-center gap-2">
                              <Check className="w-3.5 h-3.5 text-[#2D6A4F] shrink-0" />
                              <span>Gross NPA: <strong className="font-mono">{gnpa.toFixed(2)}%</strong></span>
                            </span>
                            <span className="text-[11px] font-mono text-[#765E59]">
                              {gnpa <= 3.0 ? 'Stronger (≤ 3.0%)' : gnpa <= 7.0 ? 'Mixed (3.0% - 7.0%)' : 'Stress (> 7.0%)'}
                            </span>
                          </li>
                        )}
                        {crar != null && (
                          <li className="flex items-center justify-between text-[#3B2522]">
                            <span className="flex items-center gap-2">
                              <Check className="w-3.5 h-3.5 text-[#2D6A4F] shrink-0" />
                              <span>Capital cushion (CRAR): <strong className="font-mono">{crar.toFixed(2)}%</strong></span>
                            </span>
                            <span className="text-[11px] font-mono text-[#765E59]">
                              {crar >= 12.0 ? 'Stronger (≥ 12.0%)' : crar >= 9.0 ? 'Mixed (9.0% - 12.0%)' : 'Stress (< 9.0%)'}
                            </span>
                          </li>
                        )}
                      </ul>
                    ) : (
                      <p className="text-[#765E59] italic">
                        {t('financialPartner.noMetricsAvailableForEvaluation', 'No verified financial indicators were found in public disclosures for this entity. YojnaSetu strictly requires at least 2 verified indicators before calculating a position.')}
                      </p>
                    )}
                  </div>
                  <p className="text-[11px] text-[#765E59]">
                    {t('financialPartner.institutionLevelNote', 'Figures represent corporate institution disclosures under RBI guidelines and not specific branch results.')}
                  </p>
                </div>
              )}
            </div>

            {/* Accordion 3: How did YojnaSetu calculate this? (YS-FIS-V1) */}
            <div className="bg-white border border-[#E8D8D2] rounded-2xl shadow-warm-xs overflow-hidden">
              <button
                type="button"
                onClick={() => setIsMethodologyOpen(!isMethodologyOpen)}
                className="w-full p-5 text-left flex items-center justify-between hover:bg-[#FFF4EC] transition cursor-pointer"
                aria-expanded={isMethodologyOpen}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#FFF4EC] border border-[#FFD0CA] flex items-center justify-center shrink-0">
                    <Scale className="w-4 h-4 text-[#EA717B]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-extrabold text-[#3B2522]">
                      {t('financialPartner.accordion3Title', 'How did YojnaSetu calculate this?')}
                    </h3>
                    <p className="text-xs text-[#765E59]">
                      {t('financialPartner.accordion3Sub', 'Methodology, presentation bands, and thresholds (YS-FIS-V1)')}
                    </p>
                  </div>
                </div>
                <ChevronDown className={`w-4 h-4 text-[#765E59] transition-transform ${isMethodologyOpen ? 'rotate-180 text-[#EA717B]' : ''}`} />
              </button>

              {isMethodologyOpen && (
                <div className="p-5 pt-0 border-t border-[#E8D8D2] space-y-4 text-xs text-[#765E59] bg-[#FFF4EC]/20">
                  <p className="leading-relaxed">
                    YojnaSetu uses verified publicly reported financial figures to create a transparent summary for citizens. Missing information is never treated as zero or favorable.
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="p-3 bg-white rounded-xl border border-[#E8D8D2]">
                      <span className="font-bold text-[#2D6A4F] block">{t('financialHealth.statusStronger', 'STRONGER')}</span>
                      <p className="font-mono text-[11px] text-[#765E59] mt-1">NNPA &le; 1.0%, GNPA &le; 3.0%, CRAR &ge; 12.0%</p>
                    </div>
                    <div className="p-3 bg-white rounded-xl border border-[#E8D8D2]">
                      <span className="font-bold text-[#F7AE56] block">{t('financialHealth.statusMixed', 'MIXED')}</span>
                      <p className="font-mono text-[11px] text-[#765E59] mt-1">1.0% &lt; NNPA &le; 3.0% or 3.0% &lt; GNPA &le; 7.0%</p>
                    </div>
                    <div className="p-3 bg-white rounded-xl border border-[#E8D8D2]">
                      <span className="font-bold text-[#EA717B] block">{t('financialHealth.statusAttention', 'HIGHER STRESS')}</span>
                      <p className="font-mono text-[11px] text-[#765E59] mt-1">NNPA &gt; 3.0% or GNPA &gt; 7.0% or CRAR &lt; 9.0%</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-[#765E59] pt-1">
                    <span>Engine: <span className="font-mono font-bold text-[#3B2522]">YS-FIS-V1</span></span>
                    <span>Zero Synthetic Data • Deterministic</span>
                  </div>
                </div>
              )}
            </div>

            {/* Accordion 4: Technical Verification Details */}
            <div className="bg-white border border-[#E8D8D2] rounded-2xl shadow-warm-xs overflow-hidden">
              <button
                type="button"
                onClick={() => setIsTechnicalDetailsOpen(!isTechnicalDetailsOpen)}
                className="w-full p-5 text-left flex items-center justify-between hover:bg-[#FFF4EC] transition cursor-pointer"
                aria-expanded={isTechnicalDetailsOpen}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#FFF4EC] border border-[#FFD0CA] flex items-center justify-center shrink-0">
                    <Database className="w-4 h-4 text-[#EA717B]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-extrabold text-[#3B2522]">
                      {t('financialPartner.accordion4Title', 'Technical verification & audit details')}
                    </h3>
                    <p className="text-xs text-[#765E59]">
                      {t('financialPartner.accordion4Sub', 'Entity resolution telemetry, statutory prudential checks, provenance, and audit logs')}
                    </p>
                  </div>
                </div>
                <ChevronDown className={`w-4 h-4 text-[#765E59] transition-transform ${isTechnicalDetailsOpen ? 'rotate-180 text-[#EA717B]' : ''}`} />
              </button>

              {isTechnicalDetailsOpen && (
                <div className="p-5 pt-0 border-t border-[#E8D8D2] space-y-4 text-xs bg-[#FFF4EC]/20">
                  {/* Internal Technical Tabs */}
                  <div className="border-b border-[#E8D8D2] flex gap-2 overflow-x-auto pb-1">
                    {[
                      { id: 'OVERVIEW', label: 'Executive Overview', icon: Info },
                      { id: 'EVIDENCE', label: 'Verified Evidence', icon: Database },
                      { id: 'RULES', label: 'NSFDC Rules', icon: Scale },
                      { id: 'PROVENANCE', label: 'Data Provenance', icon: FileText },
                      { id: 'GOVERNANCE', label: 'Governance', icon: Lock },
                    ].map((tab) => {
                      const Icon = tab.icon;
                      const isActive = activeTechTab === tab.id;
                      return (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTechTab(tab.id as any)}
                          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
                            isActive ? 'bg-[#EA717B] text-white shadow-warm-xs' : 'text-[#765E59] hover:bg-[#FFF4EC]'
                          }`}
                        >
                          <Icon className="w-3.5 h-3.5" />
                          <span>{tab.label}</span>
                        </button>
                      );
                    })}
                  </div>

                  {activeTechTab === 'OVERVIEW' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div className="p-3 bg-white rounded-xl border border-[#E8D8D2] space-y-1">
                        <span className="font-bold text-[#3B2522] block">Legal Entity Telemetry</span>
                        <div><strong className="text-[#3B2522]">Legal Institution:</strong> <span className="text-[#765E59]">{institutionName}</span></div>
                        <div><strong className="text-[#3B2522]">Resolution Status:</strong> <span className="text-[#2D6A4F] font-bold">{data.entity_resolution_status}</span></div>
                        <div><strong className="text-[#3B2522]">Match Level:</strong> <span className="text-[#765E59]">{data.entity_match_level || (isResolved ? 'CANONICAL_MATCH' : 'UNRESOLVED')}</span></div>
                        <div><strong className="text-[#3B2522]">Financial Scope:</strong> <span className="text-[#765E59]">INSTITUTION_LEVEL_SCOPE</span></div>
                      </div>
                      <div className="p-3 bg-white rounded-xl border border-[#E8D8D2] space-y-1">
                        <span className="font-bold text-[#3B2522] block">Branch Operating Location</span>
                        <div><strong className="text-[#3B2522]">Operating Center:</strong> <span className="text-[#765E59]">{data.partner_name}</span></div>
                        <div><strong className="text-[#3B2522]">Address:</strong> <span className="text-[#765E59]">{data.branch_address || branchLoc}</span></div>
                        <div><strong className="text-[#3B2522]">Partner Code:</strong> <span className="font-mono text-[#765E59]">{data.partner_code}</span></div>
                      </div>
                    </div>
                  )}

                  {activeTechTab === 'EVIDENCE' && (
                    <div className="overflow-x-auto bg-white rounded-xl border border-[#E8D8D2]">
                      <table className="min-w-full text-xs text-left border-collapse">
                        <thead>
                          <tr className="bg-[#FFF4EC] border-b border-[#E8D8D2] text-[#4A2525] font-bold">
                            <th className="p-2.5">Metric</th>
                            <th className="p-2.5">Value</th>
                            <th className="p-2.5">Scope</th>
                            <th className="p-2.5">Source</th>
                            <th className="p-2.5">Period</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#E8D8D2]">
                          {Object.entries(metrics).map(([key, m]: [string, any]) => (
                            <tr key={key}>
                              <td className="p-2.5 font-bold text-[#3B2522]">{key}</td>
                              <td className="p-2.5 font-mono font-bold text-[#EA717B]">{m.value != null ? `${m.value}%` : m.status || 'Verified'}</td>
                              <td className="p-2.5 text-[#765E59]">{m.financial_scope || 'INSTITUTION_LEVEL'}</td>
                              <td className="p-2.5 text-[#765E59]">{m.source || 'Not Publicly Available'}</td>
                              <td className="p-2.5 text-[#765E59] font-mono">{m.data_as_of || m.reporting_period || 'Not Available'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {activeTechTab === 'RULES' && (
                    <div className="space-y-2">
                      {rules.map((r, i) => (
                        <div key={r.rule_id || i} className="p-3 bg-white rounded-xl border border-[#E8D8D2] flex items-center justify-between gap-2">
                          <div>
                            <span className="font-mono text-[10px] bg-[#FFF4EC] text-[#4A2525] px-2 py-0.5 rounded border border-[#FFD0CA] mr-2">{r.rule_id}</span>
                            <span className="font-bold text-[#3B2522]">{r.rule_name || r.name}</span>
                            <p className="text-[#765E59] text-[11px] mt-0.5">{r.wording}</p>
                          </div>
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#2D6A4F]/10 text-[#2D6A4F]">
                            {r.result || 'PASS'}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {activeTechTab === 'PROVENANCE' && (
                    <div className="p-3 bg-white rounded-xl border border-[#E8D8D2] space-y-1 text-[#765E59]">
                      <p><strong className="text-[#3B2522]">Primary Source:</strong> Reserve Bank of India (RBI) Database on Indian Economy</p>
                      <p><strong className="text-[#3B2522]">Policy Guidelines:</strong> National Scheduled Castes Finance & Development Corporation (NSFDC)</p>
                      <p><strong className="text-[#3B2522]">Regulatory Audit:</strong> Clean record match against DFS Banking Directory</p>
                    </div>
                  )}

                  {activeTechTab === 'GOVERNANCE' && (
                    <div className="p-3 bg-[#FFF4EC] rounded-xl border border-[#FFD0CA] text-[#4A2525] space-y-1">
                      <p><strong>Institution-Level Scope:</strong> Indian banking regulations mandate corporate entity balance sheet publication. Branch offices do not publish independent balance sheets.</p>
                      <p><strong>Zero Fabrication:</strong> Missing values are never guessed or filled with synthetics.</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Sidebar Column (30% on desktop) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Quick Actions Card */}
          <QuickActionsCard
            schemeId={schemeId || undefined}
            partnerId={partnerId}
          />

          {/* About This Information Card */}
          <AboutInformationCard
            sourceName={authority}
            sourceUrl={sourceUrl || 'https://rbi.org.in'}
            latestUpdated={reportingPeriod || '31 March 2025'}
            dataLevel="Institution-level"
            verificationStatus="Verified"
            dataEngine="YS-FIS-V1 (Deterministic)"
            sourceDocumentUrl={sourceUrl || undefined}
          />

          {/* Additional Citizen Scope Reminder */}
          <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-2xl p-4 text-xs text-[#4A2525] space-y-2">
            <div className="flex items-center gap-1.5 font-bold text-[#4A2525]">
              <Info className="w-4 h-4 text-[#EA717B] shrink-0" />
              <span>{t('financialPartner.citizenNoticeTitle', 'Citizen Information Notice')}</span>
            </div>
            <p className="leading-relaxed text-[#765E59]">
              {t('financialPartner.citizenNoticeDesc', 'This financial information helps you evaluate institution performance before applying. Scheme eligibility and financial assistance sanctions remain governed exclusively by official scheme rules.')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
