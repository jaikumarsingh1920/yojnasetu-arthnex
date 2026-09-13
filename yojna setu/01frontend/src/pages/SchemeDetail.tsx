import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
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
import { SchemeDocumentGuidance } from '../components/SchemeDocumentGuidance';
import { SchemeEmbeddedCalculator } from '../components/SchemeEmbeddedCalculator';
import { formatCurrency, formatPercent } from '../utils/formatters';
import {
  Building2,
  FileText,
  ShieldCheck,
  ArrowLeft,
  Info,
  Bot,
  Send,
  BookmarkCheck,
  ExternalLink,
  CheckCircle2,
  Mail,
  MapPin,
  Calculator as CalcIcon,
} from 'lucide-react';

export const SchemeDetail: React.FC = () => {
  const { t } = useTranslation();
  const { schemeId } = useParams<{ schemeId: string }>();
  const [searchParams] = useSearchParams();
  const queryAmount = searchParams.get('amount') || searchParams.get('loan_amount') || searchParams.get('requested_loan_amount');
  const initialLoanAmount = queryAmount ? parseFloat(queryAmount) : null;

  const [scheme, setScheme] = useState<Scheme | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailFeedback, setEmailFeedback] = useState<{ message: string; success: boolean } | null>(null);
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
        <Link to="/schemes" className="text-sky-700 font-bold text-xs hover:underline flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> {t('schemeDetail.backToSearch')}
        </Link>
      </div>
    );
  }

  const officialUrl = scheme.application_url || scheme.official_portal || scheme.official_source_url;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Breadcrumbs & Back Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <nav className="flex items-center gap-2 text-xs text-slate-500 font-medium">
          <Link to="/" className="hover:text-sky-700 transition">
            {t('nav.home', 'Home')}
          </Link>
          <span>/</span>
          <Link to="/schemes" className="hover:text-sky-700 transition">
            {t('nav.schemes')}
          </Link>
          <span>/</span>
          <span className="text-slate-800 font-bold truncate max-w-xs">
            {scheme.scheme_name}
          </span>
        </nav>

        <Link
          to="/schemes"
          className="text-xs font-bold text-slate-600 hover:text-sky-700 flex items-center gap-1 transition bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" /> {t('schemeDetail.backToAll')}
        </Link>
      </div>

      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-gov-blue via-gov-navy to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-xl border-b-4 border-gov-saffron relative overflow-hidden space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="bg-gov-saffron text-white px-2.5 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wider">
                {scheme.scheme_type || "CENTRAL SCHEME"}
              </span>

              <span className="font-mono text-xs text-slate-300 bg-slate-800 px-2 py-0.5 rounded">
                ID: {scheme.scheme_id}
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {scheme.scheme_name}
            </h1>

            <p className="text-xs text-slate-300 flex items-center gap-2">
              <Building2 className="w-4 h-4 text-gov-saffron" />
              {scheme.ministry || scheme.implementing_agency || "Government of India"}
            </p>
          </div>

          <div className="flex flex-col items-start sm:items-end gap-3 w-full sm:w-auto">
            <VerificationBadge
              status={
                scheme.verification_status ||
                (scheme.verifications && scheme.verifications.length > 0
                  ? (scheme.verifications[0] as any).verification_status
                  : 'VERIFIED')
              }
            />

            <div className="flex flex-wrap items-center gap-2 sm:gap-3 w-full sm:w-auto">
              
              {/* Existing Save Button */}
              <SaveSchemeButton schemeId={scheme.scheme_id} size="md" />

              {/* Existing Compare Button */}
              <CompareButton schemeId={scheme.scheme_id} variant="button" />

              {/* MOVED: Calculate EMI & Subsidy */}
              <Link
                to={`/calculator?scheme=${scheme.scheme_id}`}
                className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow transition flex items-center justify-center gap-1.5 w-full sm:w-auto text-center min-h-[44px]"
              >
                <CalcIcon className="w-4 h-4" />
                Calculate EMI & Subsidy
              </Link>

              {/* MOVED: Find Nearest Center */}
              <Link
                to={`/channel-partners?scheme_id=${scheme.scheme_id}`}
                className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow transition flex items-center justify-center gap-1.5 w-full sm:w-auto text-center min-h-[44px]"
              >
                <MapPin className="w-4 h-4" />
                Find Nearest Center
              </Link>

              {/* MOVED: Check My Eligibility */}
              <Link
                to="/recommendations"
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold px-4 py-2.5 rounded-xl border border-slate-700 transition flex items-center justify-center gap-1.5 w-full sm:w-auto text-center min-h-[44px]"
              >
                Check My Eligibility
              </Link>

              {/* Existing Email Button */}
              <button
                onClick={() => setIsEmailModalOpen(true)}
                className="bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs px-3.5 sm:px-4 py-2.5 rounded-xl border border-slate-700 transition flex items-center justify-center gap-1.5 shadow-sm min-h-[44px] cursor-pointer"
                title={t('schemeDetail.emailTooltip', 'Email official scheme details')}
              >
                <Mail className="w-4 h-4 text-sky-400" />
                {t('schemeDetail.emailMe', 'Email Me This Scheme')}
              </button>

              {scheme.application_route === 'CHANNEL_PARTNER' ||
              (scheme.partner_count && scheme.partner_count > 0) ? (
                <Link
                  to={`/channel-partners?scheme_id=${scheme.scheme_id}`}
                  className="w-full sm:w-auto bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-lg transition flex items-center justify-center gap-2 min-h-[44px]"
                >
                  <MapPin className="w-4 h-4 text-sky-300" />
                  {t(
                    'howToApply.ctaPartner',
                    'Find Authorized Channel Partners'
                  )}
                </Link>
              ) : officialUrl ? (
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="w-full sm:w-auto bg-gov-saffron hover:bg-orange-600 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-lg transition flex items-center justify-center gap-2 min-h-[44px]"
                >
                  {scheme.application_route === 'DIRECT_PORTAL'
                    ? t('howToApply.ctaPortal', 'Apply on Official Portal')
                    : t(
                        'howToApply.ctaOfficialGuidelines',
                        'View Official Guidelines'
                      )}
                  <ExternalLink className="w-4 h-4" />
                </button>
              ) : null}
            </div>
          </div>
        </div>
      </div>

      {emailFeedback && (
        <Alert type={emailFeedback.success ? 'success' : 'info'}>
          {emailFeedback.message}
        </Alert>
      )}

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left 2 Columns: Scheme Details */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Overview */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-slate-900 border-b border-slate-200 pb-3 flex items-center gap-2">
              <Info className="w-5 h-5 text-sky-600" />
              {t('schemeDetail.purposeTitle')}
            </h2>

            <p className="text-xs text-slate-600 leading-relaxed">
              {scheme.objective ||
                "Verified scheme under Government of India welfare guidelines."}
            </p>
          </div>

          {/* Official Provenance & Verification Card */}
          <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-200 pb-2.5 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              {t(
                'schemeDetail.provenanceTitle',
                'Official Provenance & Verification Metadata'
              )}
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="space-y-1">
                <span className="font-semibold text-slate-500 block">
                  {t(
                    'schemeDetail.officialSourceMinistry',
                    'Official Source / Ministry'
                  )}
                </span>

                <span className="font-bold text-slate-800">
                  {scheme.ministry ||
                    scheme.implementing_agency ||
                    (scheme as any).source_organization ||
                    t(
                      'schemeDetail.notSpecifiedOfficial',
                      'Not specified in available official data'
                    )}
                </span>
              </div>

              <div className="space-y-1">
                <span className="font-semibold text-slate-500 block">
                  {t('schemeDetail.officialSourceUrl', 'Official Source URL')}
                </span>

                {officialUrl ? (
                  <a
                    href={officialUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sky-700 font-bold hover:underline flex items-center gap-1 truncate max-w-full break-all"
                  >
                    <span className="truncate">{officialUrl}</span>
                    <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                  </a>
                ) : (
                  <span className="italic text-slate-400">
                    {t(
                      'schemeDetail.notSpecifiedOfficial',
                      'Not specified in available official data'
                    )}
                  </span>
                )}
              </div>

              <div className="space-y-1">
                <span className="font-semibold text-slate-500 block">
                  {t(
                    'schemeDetail.verificationStatus',
                    'Verification Status'
                  )}
                </span>

                <span className="inline-flex items-center gap-1 font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full text-[11px]">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  {scheme.verification_status ||
                    (scheme.verifications?.[0] as any)
                      ?.verification_status ||
                    t('schemeDetail.verifiedBadge', 'VERIFIED')}
                </span>
              </div>

              <div className="space-y-1">
                <span className="font-semibold text-slate-500 block">
                  {t(
                    'schemeDetail.lastVerifiedDate',
                    'Last Verified Date'
                  )}
                </span>

                <span className="font-mono text-slate-700">
                  {(scheme as any).last_verified_date ||
                  (scheme as any).source_date ||
                  (scheme as any).updated_at
                    ? new Date(
                        (scheme as any).updated_at || Date.now()
                      ).toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })
                    : t(
                        'schemeDetail.notSpecifiedOfficial',
                        'Not specified in available official data'
                      )}
                </span>
              </div>
            </div>
          </div>

          {/* Scheme-Aware Embedded Financial Calculator & Assistance Section */}
          <div id="calculator" className="scroll-mt-24">
            <SchemeEmbeddedCalculator
              scheme={scheme}
              initialLoanAmount={initialLoanAmount}
            />
          </div>

          {/* Rules List */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex justify-between items-center border-b border-slate-200 pb-3">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                {t('schemeDetail.eligibilityTitle')} (
                {scheme.rules?.length || 0})
              </h2>
            </div>

            <div className="bg-sky-50 border border-sky-200 p-3.5 rounded-xl text-xs text-sky-900 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-sky-700 shrink-0 mt-0.5" />

              <div>
                <p className="font-bold">
                  {t('schemeDetail.guidanceNoteTitle')}
                </p>

                <p className="text-[11px] text-sky-800 mt-0.5">
                  {t('schemeDetail.guidanceNoteDesc')}
                </p>
              </div>
            </div>

            {!scheme.rules || scheme.rules.length === 0 ? (
              <p className="text-xs text-slate-500 italic">
                {t('schemeDetail.standardConditions')}
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {scheme.rules.map((rule) => {
                  const f = (rule.field || '').toLowerCase();
                  const val = String(rule.value || '').trim();
                  let displayCriterion = `${rule.field.replace(
                    /_/g,
                    ' '
                  )}: ${val}`;

                  if (f === 'age_min')
                    displayCriterion = `Minimum Age: ${val} years`;
                  else if (f === 'age_max')
                    displayCriterion = `Maximum Age: ${val} years`;
                  else if (
                    f === 'annual_income_max' ||
                    f === 'income_limit'
                  ) {
                    const num = Number(val);

                    displayCriterion =
                      !isNaN(num) && num > 0
                        ? `Annual Family Income Limit: ₹${num.toLocaleString(
                            'en-IN'
                          )}`
                        : `Annual Income Limit: ${val}`;
                  } else if (
                    f === 'gender_condition' ||
                    f === 'gender'
                  ) {
                    displayCriterion = `Eligible Gender: ${
                      val === 'F' || val === 'FEMALE'
                        ? 'Female Beneficiaries'
                        : val
                    }`;
                  } else if (
                    f === 'social_category' ||
                    f === 'caste'
                  ) {
                    displayCriterion = `Target Social Category: ${val}`;
                  } else if (
                    f === 'activity_type' ||
                    f === 'trade'
                  ) {
                    if (val === 'TRADITIONAL_TRADE_18')
                      displayCriterion =
                        'Covered Trades: 18 traditional artisan and craft trades';
                    else
                      displayCriterion = `Eligible Activities: ${val.replace(
                        /_/g,
                        ' '
                      )}`;
                  } else if (
                    f === 'state_coverage' ||
                    f === 'state'
                  ) {
                    displayCriterion = `Geographic Coverage: ${val}`;
                  } else if (f === 'project_cost_max') {
                    const num = Number(val);

                    displayCriterion =
                      !isNaN(num) && num > 0
                        ? `Maximum Project Cost: ₹${num.toLocaleString(
                            'en-IN'
                          )}`
                        : `Project Cost Limit: ${val}`;
                  } else if (
                    rule.description &&
                    !rule.description.includes('RULE-')
                  ) {
                    displayCriterion = rule.description;
                  }

                  return (
                    <div
                      key={rule.rule_id}
                      className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between font-bold text-slate-800">
                        <span className="font-semibold text-slate-700 capitalize text-xs">
                          {rule.field.replace(/_/g, ' ')}
                        </span>

                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                            rule.rule_type === 'ELIGIBILITY'
                              ? 'bg-sky-100 text-sky-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {rule.rule_type}
                        </span>
                      </div>

                      <p className="text-slate-900 font-bold">
                        {displayCriterion}
                      </p>

                      {rule.error_message &&
                        !rule.error_message.includes('RULE-') && (
                          <p className="text-[11px] text-slate-500">
                            {rule.error_message}
                          </p>
                        )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Interactive AI Q&A Widget */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-md p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Bot className="w-5 h-5 text-sky-600" />
                {t('schemeDetail.askAiTitle')}
              </h2>

              <span className="text-[11px] bg-emerald-50 text-emerald-800 font-bold px-2.5 py-0.5 rounded-full border border-emerald-200">
                {t('schemeDetail.verifiedInfoBadge')}
              </span>
            </div>

            <form onSubmit={handleAskSchemeAI} className="flex gap-2">
              <input
                type="text"
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder={t('schemeDetail.askAiPlaceholder')}
                className="flex-1 rounded-xl border-slate-300 text-xs p-3 shadow-sm focus:border-sky-500 focus:ring-sky-500 border outline-none"
              />

              <button
                type="submit"
                disabled={isChatLoading || !chatMessage.trim()}
                className="bg-gov-blue hover:bg-gov-navy text-white font-bold text-xs px-5 py-3 rounded-xl shadow transition flex items-center gap-1.5 disabled:opacity-50"
              >
                {isChatLoading ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    {t('schemeDetail.askBtn')}
                  </>
                )}
              </button>
            </form>

            {chatResult && (
              <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 text-xs text-slate-700">
                <div className="font-bold text-slate-900 flex items-center gap-1.5">
                  <Bot className="w-4 h-4 text-sky-600" />
                  {t('schemeDetail.answerLabel')}
                </div>

                <div className="whitespace-pre-wrap font-sans leading-relaxed text-slate-800">
                  {chatResult.answer}
                </div>

                {chatResult.citations &&
                  chatResult.citations.length > 0 && (
                    <div className="pt-2 border-t border-slate-200 space-y-1.5">
                      <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                        <BookmarkCheck className="w-3.5 h-3.5 text-emerald-600" />
                        {t('schemeDetail.sourcesLabel')}
                      </span>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {chatResult.citations.map((cite, i) => (
                          <div
                            key={i}
                            className="bg-white p-2.5 rounded-lg border border-slate-200 text-[11px] text-slate-600 space-y-1"
                          >
                            <span className="font-bold text-slate-800 block">
                              {t('schemeDetail.verifiedInfo')}
                            </span>

                            <p className="line-clamp-2 italic text-slate-500">
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
        </div>

        {/* Right Column: Scheme-Specific Document Guidance & How to Apply */}
        <div className="space-y-8">
          <SchemeDocumentGuidance
            scheme={scheme}
            onOpenPortalModal={() => setIsModalOpen(true)}
          />
        </div>
      </div>

      {/* 
        Next Actions Continuity Banner REMOVED
        The three actions have been moved to the Hero Banner above.
      */}

      {/* Official Portal Safety Dialog */}
      <OfficialPortalModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        officialUrl={officialUrl}
        schemeName={scheme.scheme_name}
      />

      {/* Email Scheme Dialog */}
      <EmailSchemeModal
        isOpen={isEmailModalOpen}
        onClose={() => setIsEmailModalOpen(false)}
        schemeId={scheme.scheme_id}
        schemeName={scheme.scheme_name}
        defaultEmail={user?.email || ''}
      />
    </div>
  );
};