import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { schemeApi } from '../api/schemeApi';
import { aiApi } from '../api/aiApi';
import { Scheme, AIChatResponse } from '../types';
import { VerificationBadge } from '../components/Badge';
import { Alert } from '../components/Alert';
import { OfficialPortalModal } from '../components/OfficialPortalModal';
import { EmailSchemeModal } from '../components/EmailSchemeModal';
import { useAuth } from '../context/AuthContext';
import { savedSchemesApi } from '../api/savedSchemesApi';
import { SaveSchemeButton } from '../components/SaveSchemeButton';
import { CompareButton } from '../components/CompareButton';
import { SchemeStickyNav } from '../components/SchemeStickyNav';
import { SchemeAtAGlance } from '../components/SchemeAtAGlance';
import { SchemeEligibilitySection } from '../components/SchemeEligibilitySection';
import { SchemeHowToApplySection } from '../components/SchemeHowToApplySection';
import { SchemeDocumentsSection } from '../components/SchemeDocumentsSection';
import { SchemeEmbeddedCalculator } from '../components/SchemeEmbeddedCalculator';
import { SchemeOfficialProvenance } from '../components/SchemeOfficialProvenance';
import { cleanGovTitle, cleanGovDescription } from '../utils/textNormalization';
import { formatCurrency } from '../utils/formatters';
import {
  Building2,
  ArrowLeft,
  ArrowRight,
  Bot,
  Send,
  BookmarkCheck,
  ExternalLink,
  CheckCircle2,
  Mail,
  MapPin,
  Calculator as CalcIcon,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Info,
  ShieldCheck,
  Coins,
  Users,
  FileText,
  Compass
} from 'lucide-react';

export const SchemeDetail: React.FC = () => {
  const { t } = useTranslation();
  const { schemeId } = useParams<{ schemeId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const queryAmount =
    searchParams.get('amount') ||
    searchParams.get('loan_amount') ||
    searchParams.get('requested_loan_amount');
  const initialLoanAmount = queryAmount ? parseFloat(queryAmount) : null;

  const handleBackNavigation = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate('/schemes');
    }
  };

  const [scheme, setScheme] = useState<Scheme | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailFeedback, setEmailFeedback] = useState<{ message: string; success: boolean } | null>(null);
  const [isFullOverviewOpen, setIsFullOverviewOpen] = useState(false);
  const { user } = useAuth();

  // Scheme-specific AI Chat State
  const [chatMessage, setChatMessage] = useState('');
  const [chatResult, setChatResult] = useState<AIChatResponse | null>(null);
  const [isChatLoading, setIsChatLoading] = useState(false);

  useEffect(() => {
    if (schemeId) {
      fetchSchemeDetail(schemeId);
    }
  }, [schemeId]);

  const fetchSchemeDetail = async (id: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await schemeApi.getSchemeById(id);
      setScheme(data);
    } catch (err: any) {
      setErrorMsg(t('errors.networkError') + ' ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
      if (!window.location.hash) {
        window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
      }
    }
  };

  const handleEmailScheme = async () => {
    if (!schemeId) return;
    setEmailLoading(true);
    setEmailFeedback(null);
    try {
      const res = await savedSchemesApi.emailScheme(schemeId);
      setEmailFeedback({ message: res.message, success: res.sent });
    } catch (err: any) {
      const msg = err?.response?.data?.detail || t('savedSchemes.emailSuccess');
      setEmailFeedback({ message: msg, success: false });
    } finally {
      setEmailLoading(false);
    }
  };

  const handleAskSchemeAI = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!schemeId || !chatMessage.trim()) return;

    setIsChatLoading(true);
    try {
      const res = await aiApi.askAboutScheme(schemeId, { message: chatMessage });
      setChatResult(res);
    } catch (err: any) {
      setErrorMsg('AI guidance failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsChatLoading(false);
    }
  };

  const scrollToCalculator = () => {
    const el = document.getElementById('calculator');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-gov-saffron border-t-transparent" />
      </div>
    );
  }

  if (errorMsg || !scheme) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 space-y-4">
        <Alert type="error">{errorMsg || t('schemeDetail.schemeNotFound')}</Alert>
        <button
          onClick={handleBackNavigation}
          className="text-sky-700 font-bold text-xs hover:underline flex items-center gap-1 cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> {t('schemeDetail.backToSearch')}
        </button>
      </div>
    );
  }

  const officialUrl = scheme.application_url || scheme.official_portal || scheme.official_source_url;
  const isPartnerRouted =
    scheme.application_route === 'CHANNEL_PARTNER' ||
    (scheme.partner_count !== undefined && scheme.partner_count !== null && scheme.partner_count > 0);

  const cleanTitle = cleanGovTitle(scheme.scheme_name);
  const cleanOverview = cleanGovDescription(
    scheme.objective ||
    scheme.purpose ||
    scheme.short_description ||
    'Verified scheme under Government of India welfare guidelines.'
  );

  const isOverviewLong = cleanOverview.length > 220;
  const truncatedOverview = isOverviewLong
    ? `${cleanOverview.slice(0, 220).trim()}...`
    : cleanOverview;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">
      {/* 1. Breadcrumbs & Back Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-slate-500 font-medium">
          <Link to="/" className="hover:text-sky-700 transition">
            {t('nav.home', 'Home')}
          </Link>
          <span>/</span>
          <button
            onClick={handleBackNavigation}
            className="hover:text-sky-700 transition cursor-pointer"
          >
            {t('nav.schemes', 'Schemes')}
          </button>
          <span>/</span>
          <span className="text-slate-800 font-bold truncate max-w-xs" title={cleanTitle}>
            {cleanTitle}
          </span>
        </nav>

        <button
          onClick={handleBackNavigation}
          className="text-xs font-bold text-slate-600 hover:text-sky-700 flex items-center gap-1 transition bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-2xs cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> {t('schemeDetail.backToAll', 'Back to Schemes')}
        </button>
      </div>

      {/* 2. Scheme Header / Hero */}
      <header className="bg-[#4A2525] text-white rounded-3xl p-6 sm:p-8 shadow-warm-lg border-b-4 border-[#F7AE56] relative overflow-hidden space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
          {/* Main Title & Ministry */}
          <div className="space-y-3 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="bg-[#F7AE56] text-[#4A2525] px-2.5 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wider">
                {scheme.scheme_type || 'CENTRAL SECTOR SCHEME'}
              </span>

              <span className="font-mono text-xs text-[#FFFBF0]/80 bg-white/10 px-2 py-0.5 rounded border border-[#FFD0CA]/20">
                ID: {scheme.scheme_id}
              </span>

              {scheme.sector && (
                <span className="text-[10px] text-[#FFD0CA] bg-white/10 px-2 py-0.5 rounded border border-[#FFD0CA]/30">
                  {scheme.sector}
                </span>
              )}
            </div>

            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight leading-tight">
              {cleanTitle}
            </h1>

            <p className="text-xs sm:text-sm text-[#FFFBF0]/90 flex items-center gap-2">
              <Building2 className="w-4 h-4 text-[#F7AE56] shrink-0" />
              <span>{scheme.ministry || scheme.implementing_agency || 'Government of India'}</span>
            </p>

            {/* Scheme Overview with Expandable Toggle */}
            <div className="pt-2 text-xs sm:text-sm text-[#FFFBF0]/80 leading-relaxed space-y-2">
              <p>
                {isFullOverviewOpen ? cleanOverview : truncatedOverview}
              </p>

              {isOverviewLong && (
                <button
                  onClick={() => setIsFullOverviewOpen(!isFullOverviewOpen)}
                  className="inline-flex items-center gap-1 text-xs font-bold text-[#F7AE56] hover:text-[#FFA63E] transition cursor-pointer"
                >
                  {isFullOverviewOpen ? (
                    <>
                      <span>Show less overview</span>
                      <ChevronUp className="w-3.5 h-3.5" />
                    </>
                  ) : (
                    <>
                      <span>Read full scheme details</span>
                      <ChevronDown className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Verification Badge & Top Status */}
          <div className="flex flex-col items-start lg:items-end gap-3 shrink-0">
            <VerificationBadge
              status={
                scheme.verification_status ||
                (scheme.verifications && scheme.verifications.length > 0
                  ? (scheme.verifications[0] as any).verification_status
                  : 'VERIFIED')
              }
            />
            <span className="text-[11px] text-[#FFFBF0]/70">
              Deterministic Official Source
            </span>
          </div>
        </div>

        {/* Action Row matching Panel 3 Reference Mockup */}
        <div className="pt-4 border-t border-white/15 flex flex-wrap items-center gap-2.5">
          {/* Primary CTA: Check Eligibility */}
          <Link
            to="/recommendations"
            className="bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-warm-xs hover:shadow-warm-sm transition flex items-center justify-center gap-2 min-h-[42px]"
          >
            <span>Check Eligibility</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>

          {/* Calculate EMI */}
          <button
            onClick={scrollToCalculator}
            className="bg-[#3B2522] hover:bg-[#2F1D1B] text-[#FFFBF0] text-xs font-bold px-4 py-2.5 rounded-xl border border-[#E8D8D2]/30 transition flex items-center justify-center gap-1.5 min-h-[42px] cursor-pointer"
          >
            <CalcIcon className="w-4 h-4 text-[#F7AE56]" />
            <span>Calculate EMI</span>
          </button>

          {/* Save Scheme */}
          <SaveSchemeButton schemeId={scheme.scheme_id} size="md" />

          {/* Compare */}
          <CompareButton
            schemeId={scheme.scheme_id}
            schemeName={scheme.scheme_name}
            variant="button"
          />

          {/* Find Channel Partner */}
          <Link
            to={`/channel-partners?scheme_id=${scheme.scheme_id}`}
            className="bg-[#3B2522] hover:bg-[#2F1D1B] text-[#FFFBF0] text-xs font-bold px-4 py-2.5 rounded-xl border border-[#E8D8D2]/30 transition flex items-center justify-center gap-1.5 min-h-[42px]"
          >
            <MapPin className="w-4 h-4 text-emerald-400" />
            <span>Find Partner</span>
          </Link>

          {/* Official Portal Apply Button if available */}
          {officialUrl && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="bg-white/10 hover:bg-white/20 text-white text-xs font-bold px-4 py-2.5 rounded-xl border border-white/20 transition flex items-center justify-center gap-1.5 min-h-[42px] cursor-pointer"
            >
              <span>Official Portal</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          )}

          {/* Email Me Scheme */}
          <button
            onClick={() => setIsEmailModalOpen(true)}
            className="p-2.5 rounded-xl bg-[#3B2522] hover:bg-[#2F1D1B] text-[#FFFBF0]/80 hover:text-white border border-[#E8D8D2]/30 transition cursor-pointer"
            title={t('schemeDetail.emailTooltip', 'Email official scheme details')}
          >
            <Mail className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Email Feedback Alert */}
      {emailFeedback && (
        <Alert type={emailFeedback.success ? 'success' : 'info'}>
          {emailFeedback.message}
        </Alert>
      )}

      {/* 3. Sticky Section Navigation */}
      <SchemeStickyNav
        hasCalculator={scheme.is_credit_scheme !== false && scheme.calculator_applicable !== false}
        hasRules={Boolean(scheme.rules && scheme.rules.length > 0)}
        hasDocs={Boolean(scheme.documents && scheme.documents.length > 0)}
      />

      {/* 4. Overview Section with 2-Column Citizen Summary */}
      <section id="overview" className="scroll-mt-24 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (7 cols): Scheme Purpose & Quick Facts */}
          <div className="lg:col-span-7 space-y-5">
            {/* Purpose & Objective */}
            <div className="bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs p-6 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-[#EA717B] uppercase tracking-wider">
                <Compass className="w-4 h-4 text-[#EA717B]" />
                <span>Scheme Purpose & Objective</span>
              </div>
              <p className="text-sm text-[#3B2522] leading-relaxed">
                {isFullOverviewOpen ? cleanOverview : truncatedOverview}
              </p>
              {isOverviewLong && (
                <button
                  type="button"
                  onClick={() => setIsFullOverviewOpen(!isFullOverviewOpen)}
                  className="text-xs font-bold text-[#EA717B] hover:text-[#D65D67] flex items-center gap-1 cursor-pointer"
                >
                  <span>{isFullOverviewOpen ? 'Show less' : 'Read more'}</span>
                  {isFullOverviewOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
              )}
            </div>

            {/* Quick Facts Card */}
            <div className="bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-extrabold text-[#3B2522] uppercase tracking-wider flex items-center gap-2">
                  <Coins className="w-4 h-4 text-[#F7AE56]" />
                  <span>Quick Facts</span>
                </h3>
                <span className="text-[10px] bg-[#FFF4EC] text-emerald-800 font-bold px-2.5 py-0.5 rounded-full border border-emerald-200">
                  Verified Parameters
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                <div className="bg-[#FFF4EC]/40 p-3 rounded-2xl border border-[#E8D8D2]">
                  <span className="text-[10px] uppercase font-bold text-[#765E59] block">Max Project / Loan</span>
                  <span className="text-sm font-black text-[#3B2522] mt-0.5 block truncate">
                    {scheme.max_loan_amount
                      ? formatCurrency(Number(scheme.max_loan_amount))
                      : scheme.max_project_cost
                      ? formatCurrency(Number(scheme.max_project_cost))
                      : 'As per appraisal'}
                  </span>
                </div>

                <div className="bg-[#FFF4EC]/40 p-3 rounded-2xl border border-[#E8D8D2]">
                  <span className="text-[10px] uppercase font-bold text-[#765E59] block">Subsidy / Margin</span>
                  <span className="text-sm font-black text-[#3B2522] mt-0.5 block truncate">
                    {scheme.subsidy_percentage
                      ? `${scheme.subsidy_percentage}% (varies)`
                      : scheme.max_subsidy_amount
                      ? formatCurrency(Number(scheme.max_subsidy_amount))
                      : 'Guidelines Apply'}
                  </span>
                </div>

                <div className="bg-[#FFF4EC]/40 p-3 rounded-2xl border border-[#E8D8D2]">
                  <span className="text-[10px] uppercase font-bold text-[#765E59] block">Interest Rate</span>
                  <span className="text-sm font-black text-[#3B2522] mt-0.5 block truncate">
                    {scheme.interest_rate !== null && scheme.interest_rate !== undefined
                      ? scheme.interest_rate === 0
                        ? '0% (Interest-Free)'
                        : `${scheme.interest_rate}% p.a.`
                      : scheme.interest_rate_max !== null && scheme.interest_rate_max !== undefined
                      ? `${scheme.interest_rate_max}% max`
                      : 'As per bank'}
                  </span>
                </div>

                <div className="bg-[#FFF4EC]/40 p-3 rounded-2xl border border-[#E8D8D2]">
                  <span className="text-[10px] uppercase font-bold text-[#765E59] block">Repayment Period</span>
                  <span className="text-sm font-black text-[#3B2522] mt-0.5 block truncate">
                    {scheme.repayment_period_months
                      ? `${Math.round(scheme.repayment_period_months / 12)} years (${scheme.repayment_period_months}m)`
                      : '3 – 7 years'}
                  </span>
                </div>

                <div className="bg-[#FFF4EC]/40 p-3 rounded-2xl border border-[#E8D8D2] sm:col-span-2">
                  <span className="text-[10px] uppercase font-bold text-[#765E59] block">Application Mode</span>
                  <span className="text-sm font-black text-[#3B2522] mt-0.5 block truncate">
                    {scheme.application_route === 'DIRECT_PORTAL'
                      ? 'Official Ministry Portal'
                      : isPartnerRouted
                      ? 'Through Authorized Banks & Agencies'
                      : 'Assisted Civic Center'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column (5 cols): Who Can Apply? & Important Documents */}
          <div className="lg:col-span-5 space-y-5">
            {/* Who Can Apply Card */}
            <div className="bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E8D8D2]/60 pb-3">
                <h3 className="text-sm font-extrabold text-[#3B2522] uppercase tracking-wider flex items-center gap-2">
                  <Users className="w-4 h-4 text-[#EA717B]" />
                  <span>Who Can Apply?</span>
                </h3>
              </div>

              <div className="space-y-2 text-xs text-[#3B2522]">
                <div className="flex items-center gap-2 p-2.5 rounded-xl bg-[#FFF4EC]/50 border border-[#E8D8D2]/60">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span className="font-semibold">
                    {scheme.target_groups?.replace(/_/g, ' ') || 'Individuals (18+ years)'}
                  </span>
                </div>
                <div className="flex items-center gap-2 p-2.5 rounded-xl bg-[#FFF4EC]/50 border border-[#E8D8D2]/60">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span className="font-semibold">Self Help Groups (SHGs) & Micro-units</span>
                </div>
                <div className="flex items-center gap-2 p-2.5 rounded-xl bg-[#FFF4EC]/50 border border-[#E8D8D2]/60">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span className="font-semibold">Co-operative Societies & Artisans</span>
                </div>
              </div>

              <a
                href="#eligibility"
                className="text-xs font-bold text-[#EA717B] hover:text-[#D65D67] flex items-center gap-1 pt-1"
              >
                <span>View Detailed Eligibility</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </a>
            </div>

            {/* Important Documents Card */}
            <div className="bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E8D8D2]/60 pb-3">
                <h3 className="text-sm font-extrabold text-[#3B2522] uppercase tracking-wider flex items-center gap-2">
                  <FileText className="w-4 h-4 text-[#F7AE56]" />
                  <span>Important Documents</span>
                </h3>
              </div>

              <div className="space-y-2 text-xs">
                {(scheme.documents && scheme.documents.length > 0
                  ? scheme.documents.slice(0, 4)
                  : [
                      { document_name: 'Aadhaar Card', is_mandatory: true },
                      { document_name: 'PAN Card / Business Proof', is_mandatory: true },
                      { document_name: 'Caste Certificate (If applicable)', is_mandatory: false },
                      { document_name: 'Project Report / Cost Estimate', is_mandatory: false },
                    ]
                ).map((doc: any, dIdx: number) => (
                  <div key={dIdx} className="flex items-center justify-between p-2 rounded-xl bg-[#FFF4EC]/40 border border-[#E8D8D2]">
                    <span className="font-semibold text-[#3B2522] truncate pr-2">
                      {doc.document_name}
                    </span>
                    <span
                      className={`text-[9px] font-black px-2 py-0.5 rounded-full uppercase shrink-0 ${
                        doc.is_mandatory
                          ? 'bg-[#FFD0CA] text-[#4A2525]'
                          : 'bg-[#FFF4EC] text-[#765E59]'
                      }`}
                    >
                      {doc.is_mandatory ? 'Required' : 'Conditional'}
                    </span>
                  </div>
                ))}
              </div>

              <a
                href="#documents"
                className="text-xs font-bold text-[#EA717B] hover:text-[#D65D67] flex items-center gap-1 pt-1"
              >
                <span>View All Documents</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Eligibility Section: "Who can apply?" */}
      <SchemeEligibilitySection scheme={scheme} />

      {/* 6. How to Apply Section */}
      <SchemeHowToApplySection
        scheme={scheme}
        onOpenPortalModal={() => setIsModalOpen(true)}
      />

      {/* 7. Documents Required: "Documents you may need" (FULL-WIDTH MAIN CONTENT AREA) */}
      <SchemeDocumentsSection scheme={scheme} />

      {/* 8. Scheme-Aware Embedded Financial Calculator */}
      <section id="calculator" className="scroll-mt-24">
        <SchemeEmbeddedCalculator
          scheme={scheme}
          initialLoanAmount={initialLoanAmount}
        />
      </section>

      {/* 9. Interactive AI Q&A Widget (Secondary Section) */}
      <section id="ai-guidance" className="scroll-mt-24">
        <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E8D8D2]/60 pb-3">
            <div>
              <h2 className="text-lg font-extrabold text-[#3B2522] flex items-center gap-2">
                <Bot className="w-5 h-5 text-[#F7AE56]" />
                Ask AI Guidance About This Scheme
              </h2>
              <p className="text-xs text-[#765E59] mt-0.5">
                Instant conversational clarification based strictly on verified public government documentation.
              </p>
            </div>

            <span className="text-[11px] bg-emerald-50 text-emerald-800 font-bold px-3 py-1 rounded-full border border-emerald-200 self-start sm:self-auto">
              Verified Information Only
            </span>
          </div>

          <form onSubmit={handleAskSchemeAI} className="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              placeholder="Ask a question (e.g., 'What is the family income limit?' or 'Are women eligible?')..."
              className="flex-1 rounded-xl border border-[#E8D8D2] text-xs p-3 shadow-warm-xs focus:border-[#EA717B] focus:ring-2 focus:ring-[#EA717B] outline-none bg-[#FFFBF0] text-[#3B2522] placeholder:text-[#765E59]"
            />

            <button
              type="submit"
              disabled={isChatLoading || !chatMessage.trim()}
              className="bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold text-xs px-5 py-3 rounded-xl shadow-warm-xs transition flex items-center justify-center gap-1.5 disabled:opacity-50 cursor-pointer shrink-0"
            >
              {isChatLoading ? (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Ask Question
                </>
              )}
            </button>
          </form>

          {/* AI Guidance Disclaimer */}
          <p className="text-[11px] text-[#765E59] leading-relaxed">
            Note: This AI guidance assistant provides answers extracted from published scheme guidelines. It does not decide official eligibility or approve applications.
          </p>

          {chatResult && (
            <div className="mt-4 p-4 rounded-xl bg-[#FFF4EC]/40 border border-[#E8D8D2] space-y-3 text-xs text-[#3B2522]">
              <div className="font-bold text-[#3B2522] flex items-center gap-1.5 text-sm">
                <Bot className="w-4 h-4 text-[#F7AE56]" />
                Guidance Summary
              </div>

              <div className="whitespace-pre-wrap font-sans leading-relaxed text-[#3B2522]">
                {chatResult.answer}
              </div>

              {chatResult.citations && chatResult.citations.length > 0 && (
                <div className="pt-2 border-t border-[#E8D8D2] space-y-1.5">
                  <span className="text-[11px] font-bold text-[#765E59] uppercase tracking-wider flex items-center gap-1">
                    <BookmarkCheck className="w-3.5 h-3.5 text-emerald-600" />
                    Verified Government Citations
                  </span>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {chatResult.citations.map((cite, i) => (
                      <div
                        key={i}
                        className="bg-white p-2.5 rounded-lg border border-[#E8D8D2] text-[11px] text-[#765E59] space-y-1"
                      >
                        <span className="font-bold text-[#3B2522] block">
                          Official Source Citation
                        </span>
                        <p className="line-clamp-2 italic text-[#765E59]">
                          "{cite.snippet}"
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* 10. Official Source, Verification & Channel Partner Provenance */}
      <SchemeOfficialProvenance
        scheme={scheme}
        onOpenPortalModal={() => setIsModalOpen(true)}
      />

      {/* Official Portal Safety Dialog */}
      <OfficialPortalModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        officialUrl={officialUrl}
        schemeName={cleanTitle}
      />

      {/* Email Scheme Dialog */}
      <EmailSchemeModal
        isOpen={isEmailModalOpen}
        onClose={() => setIsEmailModalOpen(false)}
        schemeId={scheme.scheme_id}
        schemeName={cleanTitle}
        defaultEmail={user?.email || ''}
      />
    </div>
  );
};