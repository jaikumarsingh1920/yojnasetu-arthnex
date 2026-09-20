import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Scheme } from '../types';
import {
  Building2,
  ExternalLink,
  MapPin,
  Globe,
  FileCheck,
  CheckCircle2,
  Layers,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  Info,
  TrendingUp
} from 'lucide-react';

interface SchemeHowToApplySectionProps {
  scheme: Scheme;
  onOpenPortalModal?: () => void;
}

export const SchemeHowToApplySection: React.FC<SchemeHowToApplySectionProps> = ({
  scheme,
  onOpenPortalModal,
}) => {
  const { t } = useTranslation();

  // Determine authoritative route
  const isPartnerRouted =
    scheme.application_route === 'CHANNEL_PARTNER' ||
    (scheme.partner_count !== undefined && scheme.partner_count !== null && scheme.partner_count > 0) ||
    [
      'SIH26092-053', 'SIH26092-054', 'SIH26092-055', 'SIH26092-056',
      'SIH26092-057', 'SIH26092-058', 'SIH26092-059', 'SIH26092-060',
      'SIH26092-061', 'SIH26092-062', 'SIH26092-063', 'SIH26092-068',
      'SIH26092-069', 'SIH26092-070', 'SIH26092-074', 'SIH26092-031',
      'SIH26092-032', 'SIH26092-033',
    ].includes(scheme.scheme_id);

  const officialUrl = scheme.application_url || scheme.official_portal || scheme.official_source_url;

  const isDirectPortal =
    !isPartnerRouted &&
    (scheme.application_route === 'DIRECT_PORTAL' ||
      Boolean(
        officialUrl &&
          (officialUrl.startsWith('http://') || officialUrl.startsWith('https://')) &&
          (scheme.application_mode === 'ONLINE' ||
            scheme.scheme_type === 'PORTAL_SCHEME' ||
            Boolean(scheme.official_portal))
      ));

  const isDepartmental = !isPartnerRouted && !isDirectPortal;

  // Parse custom application steps if stored in scheme record
  const parseRawSteps = (rawSteps?: string | null): string[] => {
    if (!rawSteps || rawSteps.trim() === '') return [];
    return rawSteps
      .split(/(?:\r?\n|;|\d+\.\s+)/)
      .map((s) => s.trim())
      .filter((s) => s.length > 5);
  };

  const customSteps = parseRawSteps(scheme.application_steps);

  const routeTitle = isDirectPortal
    ? t('schemeDetail.howToApply.directPortalRoute', 'Direct Official Portal Route')
    : isPartnerRouted
    ? t('schemeDetail.howToApply.channelPartnerRoute', 'Authorized Channel Partner Route')
    : t('schemeDetail.howToApply.departmentalRoute', 'District Departmental Route');

  const routeBadgeColor = isDirectPortal
    ? 'bg-sky-50 text-sky-700 border-sky-200'
    : isPartnerRouted
    ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
    : 'bg-amber-50 text-amber-700 border-amber-200';

  return (
    <section id="how-to-apply" className="scroll-mt-24 space-y-6">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg sm:text-xl font-extrabold text-[#3B2522] tracking-tight flex items-center gap-2">
            <Building2 className="w-5 h-5 text-[#EA717B]" />
            {t('schemeDetail.howToApplyTitle', 'How to Apply')}
          </h2>
          <p className="text-xs text-[#765E59] mt-0.5">
            {t('schemeDetail.howToApply.howToApplyDesc', 'Follow this verified 4-step process to submit your application through the official channel.')}
          </p>
        </div>

        <span
          className={`inline-flex items-center gap-1.5 text-[11px] font-extrabold px-3 py-1 rounded-full border uppercase tracking-wider self-start sm:self-auto bg-[#FFF4EC] text-[#EA717B] border-[#FFD0CA]`}
        >
          {isDirectPortal ? (
            <Globe className="w-3.5 h-3.5" />
          ) : isPartnerRouted ? (
            <Building2 className="w-3.5 h-3.5" />
          ) : (
            <AlertCircle className="w-3.5 h-3.5" />
          )}
          {routeTitle}
        </span>
      </div>

      {/* Main Process Container */}
      <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs p-5 sm:p-6 space-y-6">
        {/* Route Overview Banner */}
        <div
          className="p-4 rounded-xl border text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-[#FFF4EC] border-[#FFD0CA] text-[#4A2525]"
        >
          <div className="space-y-1">
            <p className="font-bold text-sm text-[#4A2525]">
              {isDirectPortal
                ? 'Apply Directly on Verified Government Portal'
                : isPartnerRouted
                ? 'Disbursed Through Authorized Channel Partners & Banks'
                : 'Processed Through District Welfare / DIC Offices'}
            </p>
            <p className="text-[11px] text-[#765E59] leading-relaxed max-w-2xl">
              {isDirectPortal
                ? 'Online application is managed directly by the ministry portal. Authentication is performed via Aadhaar OTP without unauthorized third parties.'
                : isPartnerRouted
                ? 'This scheme is routed through authorized State Channelizing Agencies (SCAs), Public Sector Banks (PSBs), and Regional Rural Banks (RRBs).'
                : 'This scheme accepts applications directly through designated District Welfare Officers, DICs, or departmental institutional counters.'}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0 w-full sm:w-auto">
            {isDirectPortal && onOpenPortalModal && (
              <button
                onClick={onOpenPortalModal}
                className="w-full sm:w-auto bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold text-xs py-2.5 px-4 rounded-xl shadow-warm-xs transition flex items-center justify-center gap-1.5 cursor-pointer"
              >
                Apply on Official Portal
                <ExternalLink className="w-4 h-4" />
              </button>
            )}

            {isPartnerRouted && (
              <Link
                to={`/channel-partners?scheme_id=${scheme.scheme_id}`}
                className="w-full sm:w-auto bg-[#4A2525] hover:bg-[#3B2522] text-white font-bold text-xs py-2.5 px-4 rounded-xl shadow-warm-xs transition flex items-center justify-center gap-1.5"
              >
                <MapPin className="w-4 h-4 text-[#F7AE56]" />
                Find Channel Partners
              </Link>
            )}

            {isDepartmental && officialUrl && (
              <button
                onClick={onOpenPortalModal}
                className="w-full sm:w-auto bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold text-xs py-2.5 px-4 rounded-xl shadow-warm-xs transition flex items-center justify-center gap-1.5 cursor-pointer"
              >
                View Official Guidelines
                <ExternalLink className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* 4-Step Process Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Step 1 */}
          <div className="bg-[#FFF4EC]/30 p-4 rounded-xl border border-[#E8D8D2] space-y-2 relative">
            <div className="flex items-center justify-between">
              <span className="w-7 h-7 rounded-full bg-[#EA717B] text-white font-extrabold text-xs flex items-center justify-center shadow-warm-xs">
                1
              </span>
              <span className="text-[10px] uppercase font-bold text-[#765E59] tracking-wider">
                Step 1
              </span>
            </div>
            <h4 className="text-xs font-bold text-[#3B2522] pt-1">
              Check Your Eligibility
            </h4>
            <p className="text-[11px] text-[#765E59] leading-relaxed">
              Review age, income limits, target social category, and trade requirements in the eligibility section above.
            </p>
          </div>

          {/* Step 2 */}
          <div className="bg-[#FFF4EC]/30 p-4 rounded-xl border border-[#E8D8D2] space-y-2 relative">
            <div className="flex items-center justify-between">
              <span className="w-7 h-7 rounded-full bg-[#EA717B] text-white font-extrabold text-xs flex items-center justify-center shadow-warm-xs">
                2
              </span>
              <span className="text-[10px] uppercase font-bold text-[#765E59] tracking-wider">
                Step 2
              </span>
            </div>
            <h4 className="text-xs font-bold text-[#3B2522] pt-1">
              Prepare Required Documents
            </h4>
            <p className="text-[11px] text-[#765E59] leading-relaxed">
              Assemble required documents such as Aadhaar, bank passbook, income certificate, and caste proof in original and digital copies.
            </p>
          </div>

          {/* Step 3 */}
          <div className="bg-[#FFF4EC]/30 p-4 rounded-xl border border-[#E8D8D2] space-y-2 relative">
            <div className="flex items-center justify-between">
              <span className="w-7 h-7 rounded-full bg-[#EA717B] text-white font-extrabold text-xs flex items-center justify-center shadow-warm-xs">
                3
              </span>
              <span className="text-[10px] uppercase font-bold text-[#765E59] tracking-wider">
                Step 3
              </span>
            </div>
            <h4 className="text-xs font-bold text-[#3B2522] pt-1">
              {isDirectPortal
                ? 'Apply on Official Portal'
                : isPartnerRouted
                ? 'Visit Channel Partner'
                : 'Submit to District Office'}
            </h4>
            <p className="text-[11px] text-[#765E59] leading-relaxed">
              {isDirectPortal
                ? 'Authenticate with Aadhaar OTP on the official portal and submit your application with reference number.'
                : isPartnerRouted
                ? 'Locate your nearest authorized State Channelizing Agency or bank branch and submit the application form.'
                : 'Visit the local District Welfare Officer, DIC, or Lead Bank Manager to tender your application.'}
            </p>
          </div>

          {/* Step 4 */}
          <div className="bg-[#FFF4EC]/30 p-4 rounded-xl border border-[#E8D8D2] space-y-2 relative">
            <div className="flex items-center justify-between">
              <span className="w-7 h-7 rounded-full bg-[#EA717B] text-white font-extrabold text-xs flex items-center justify-center shadow-warm-xs">
                4
              </span>
              <span className="text-[10px] uppercase font-bold text-[#765E59] tracking-wider">
                Step 4
              </span>
            </div>
            <h4 className="text-xs font-bold text-[#3B2522] pt-1">
              Complete Verification & Sanction
            </h4>
            <p className="text-[11px] text-[#765E59] leading-relaxed">
              Present physical documents for departmental appraisal. Upon approval, benefit or loan is disbursed via Direct Benefit Transfer.
            </p>
          </div>
        </div>

        {/* Custom Application Steps if present in database */}
        {customSteps.length > 0 && (
          <div className="space-y-3 pt-2 border-t border-[#E8D8D2]/60">
            <h4 className="text-xs font-extrabold uppercase tracking-wider text-[#765E59] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-[#EA717B]" />
              {t('schemeDetail.howToApply.documentedSteps', 'Documented Departmental Steps')}
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {customSteps.map((step, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2.5 p-3 rounded-xl bg-[#FFF4EC]/40 border border-[#E8D8D2] text-xs"
                >
                  <span className="w-5 h-5 rounded-full bg-[#EA717B] text-white font-bold flex items-center justify-center shrink-0 text-[10px]">
                    {idx + 1}
                  </span>
                  <p className="text-[#3B2522] font-medium leading-relaxed">{step}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Channel Partner Directory Callout (for partner routed schemes) */}
        {isPartnerRouted && (
          <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
            <div className="space-y-0.5">
              <span className="font-bold text-[#4A2525] flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-[#EA717B]" />
                {t('schemeDetail.howToApply.channelPartnerCallout', 'Channel Partner Financial Health Directory')}
              </span>
              <p className="text-[#765E59] text-[11px]">
                {t('schemeDetail.howToApply.channelPartnerCalloutDesc', 'Review financial health indicators and institutional stability of authorized channel partners for this scheme.')}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Link
                to={`/financial-health/scheme/${scheme.scheme_id}`}
                className="text-xs font-bold text-[#4A2525] hover:text-[#EA717B] flex items-center gap-1 bg-white px-3 py-1.5 rounded-lg border border-[#E8D8D2] shadow-warm-xs hover:bg-[#FFF4EC] transition"
              >
                {t('schemeDetail.howToApply.viewPartnerFinancialHealth', 'View Partner Financial Health')}
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        )}

        {/* Mandatory Official Disclaimer */}
        <div className="bg-[#FFF4EC]/50 rounded-xl p-3.5 text-xs text-[#765E59] border border-[#E8D8D2] flex items-start gap-2.5">
          <Info className="w-4 h-4 text-[#EA717B] shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <p className="font-bold text-[#3B2522] text-[11px]">{t('schemeDetail.howToApply.officialNotice', 'Official Notice')}</p>
            <p className="text-[11px] text-[#765E59] leading-relaxed">
              {t('schemeDetail.howToApply.officialNoticeDesc', 'Final eligibility, document verification, and approval are decided by the concerned authority. YojnaSetu provides procedural guidance based on verified government documentation.')}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
