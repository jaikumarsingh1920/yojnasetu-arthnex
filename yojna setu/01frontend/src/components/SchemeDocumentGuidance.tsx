import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Scheme, SchemeDocument } from '../types';
import {
  FileText,
  ShieldCheck,
  AlertCircle,
  ExternalLink,
  MapPin,
  Building2,
  CheckCircle2,
  Globe,
  HelpCircle,
  ArrowRight,
  Info,
  Layers,
  FileCheck
} from 'lucide-react';

interface SchemeDocumentGuidanceProps {
  scheme: Scheme;
  onOpenPortalModal?: () => void;
}

export const SchemeDocumentGuidance: React.FC<SchemeDocumentGuidanceProps> = ({
  scheme,
  onOpenPortalModal
}) => {
  const { t } = useTranslation();

  // Determine authoritative route
  const isPartnerRouted =
    scheme.application_route === 'CHANNEL_PARTNER' ||
    (scheme.partner_count !== undefined && scheme.partner_count !== null && scheme.partner_count > 0) ||
    ['SIH26092-053', 'SIH26092-054', 'SIH26092-055', 'SIH26092-056', 'SIH26092-057', 'SIH26092-058', 'SIH26092-059', 'SIH26092-060', 'SIH26092-061', 'SIH26092-062', 'SIH26092-063', 'SIH26092-068', 'SIH26092-069', 'SIH26092-070', 'SIH26092-074', 'SIH26092-031', 'SIH26092-032', 'SIH26092-033'].includes(scheme.scheme_id);

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

  const isUnverifiedRoute = !isPartnerRouted && !isDirectPortal;

  const docs: SchemeDocument[] = (scheme.documents || []).filter(d => d.active !== false);

  // Parse application steps if string exists in database
  const parseRawSteps = (rawSteps?: string | null): string[] => {
    if (!rawSteps || rawSteps.trim() === '') return [];
    // Split by semicolons, newlines, or numbered points (e.g., "1.", "Step 1:")
    const lines = rawSteps.split(/(?:\r?\n|;|\d+\.\s+)/).map(s => s.trim()).filter(s => s.length > 5);
    return lines;
  };

  const customSteps = parseRawSteps(scheme.application_steps);

  return (
    <div className="space-y-6">
      {/* 1. HOW TO APPLY SECTION */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 pb-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-gov-blue" />
              {t('howToApply.title', 'How to Apply')}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {t('howToApply.subtitle', 'Official step-by-step application guidance based on verified government directives.')}
            </p>
          </div>
          <span
            className={`text-[10px] font-extrabold px-2.5 py-1 rounded-full border uppercase shrink-0 ${
              isDirectPortal
                ? 'bg-sky-50 text-sky-700 border-sky-200'
                : isPartnerRouted
                ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                : 'bg-amber-50 text-amber-700 border-amber-200'
            }`}
          >
            {isDirectPortal
              ? t('howToApply.routePortalBadge', 'Direct Govt Portal')
              : isPartnerRouted
              ? t('howToApply.routePartnerBadge', 'Channel Partner Route')
              : t('howToApply.routeUnverifiedBadge', 'Departmental Route')}
          </span>
        </div>

        {/* Route Details Card */}
        {isDirectPortal && (
          <div className="space-y-4">
            <div className="bg-sky-50 border border-sky-200 p-4 rounded-xl space-y-2 text-xs text-sky-900">
              <div className="flex items-center gap-2 font-bold text-sky-950 text-sm">
                <Globe className="w-4 h-4 text-sky-700" />
                {t('howToApply.directPortalTitle', 'Apply through Official Government Portal')}
              </div>
              <p className="text-sky-800 leading-relaxed text-xs">
                {t('howToApply.directPortalDesc', 'Applications for this scheme are handled directly on the verified official government portal. You do not need to visit middle-men or unverified agencies.')}
              </p>
            </div>

            {/* Step-by-Step Procedure */}
            <div className="space-y-3">
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-slate-400" />
                {t('howToApply.stepsHeading', 'Application Steps')}
              </h4>

              {customSteps.length > 0 ? (
                <div className="space-y-2">
                  {customSteps.map((step, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                      <span className="w-5 h-5 rounded-full bg-gov-blue text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
                        {idx + 1}
                      </span>
                      <p className="text-slate-800 font-medium leading-relaxed">{step}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-2 text-xs text-slate-700">
                  <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="w-5 h-5 rounded-full bg-gov-blue text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
                      1
                    </span>
                    <div>
                      <p className="font-bold text-slate-900">{t('howToApply.step1PortalTitle', 'Prepare Required Documents')}</p>
                      <p className="text-slate-600 text-[11px] mt-0.5">
                        {t('howToApply.step1PortalDesc', 'Keep digital copies of your Aadhaar, bank passbook, and proof of category/income ready.')}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="w-5 h-5 rounded-full bg-gov-blue text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
                      2
                    </span>
                    <div>
                      <p className="font-bold text-slate-900">{t('howToApply.step2PortalTitle', 'Visit the Official Government Portal')}</p>
                      <p className="text-slate-600 text-[11px] mt-0.5">
                        {t('howToApply.step2PortalDesc', 'Click the button below to safely open the official government portal in a secure window.')}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="w-5 h-5 rounded-full bg-gov-blue text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
                      3
                    </span>
                    <div>
                      <p className="font-bold text-slate-900">{t('howToApply.step3PortalTitle', 'Submit Online Application')}</p>
                      <p className="text-slate-600 text-[11px] mt-0.5">
                        {t('howToApply.step3PortalDesc', 'Authenticate via Aadhaar OTP, complete the scheme form, and save your Application Reference Number.')}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* CTA Button */}
            {onOpenPortalModal ? (
              <button
                onClick={onOpenPortalModal}
                className="w-full bg-gov-saffron hover:bg-orange-600 text-white font-bold text-xs py-3 px-4 rounded-xl shadow transition flex items-center justify-center gap-2"
              >
                {t('howToApply.ctaPortal', 'Apply on Official Portal')}
                <ExternalLink className="w-4 h-4" />
              </button>
            ) : officialUrl ? (
              <a
                href={officialUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full bg-gov-saffron hover:bg-orange-600 text-white font-bold text-xs py-3 px-4 rounded-xl shadow transition flex items-center justify-center gap-2"
              >
                {t('howToApply.ctaPortal', 'Apply on Official Portal')}
                <ExternalLink className="w-4 h-4" />
              </a>
            ) : null}
          </div>
        )}

        {isPartnerRouted && (
          <div className="space-y-4">
            <div className="bg-indigo-50 border border-indigo-200 p-4 rounded-xl space-y-2 text-xs text-indigo-900">
              <div className="flex items-center gap-2 font-bold text-indigo-950 text-sm">
                <Building2 className="w-4 h-4 text-indigo-700" />
                {t('howToApply.partnerTitle', 'Apply through an Authorized Channel Partner')}
              </div>
              <p className="text-indigo-800 leading-relaxed text-xs">
                {t('howToApply.partnerDesc', 'This scheme is disbursed through authorized State Channelizing Agencies (SCAs), Public Sector Banks (PSBs), and Regional Rural Banks (RRBs).')}
              </p>
            </div>

            {/* Step-by-Step Procedure */}
            <div className="space-y-3">
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-slate-400" />
                {t('howToApply.stepsHeading', 'Application Steps')}
              </h4>

              {customSteps.length > 0 ? (
                <div className="space-y-2">
                  {customSteps.map((step, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                      <span className="w-5 h-5 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
                        {idx + 1}
                      </span>
                      <p className="text-slate-800 font-medium leading-relaxed">{step}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-2 text-xs text-slate-700">
                  <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="w-5 h-5 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
                      1
                    </span>
                    <div>
                      <p className="font-bold text-slate-900">{t('howToApply.step1PartnerTitle', 'Check Required Documents Checklist')}</p>
                      <p className="text-slate-600 text-[11px] mt-0.5">
                        {t('howToApply.step1PartnerDesc', 'Ensure you have physical originals and copies of all documents listed below.')}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="w-5 h-5 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
                      2
                    </span>
                    <div>
                      <p className="font-bold text-slate-900">{t('howToApply.step2PartnerTitle', 'Locate Nearest Authorized Partner')}</p>
                      <p className="text-slate-600 text-[11px] mt-0.5">
                        {t('howToApply.step2PartnerDesc', 'Use our verified GPS locator to find the closest State Channelizing Agency or bank branch.')}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="w-5 h-5 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
                      3
                    </span>
                    <div>
                      <p className="font-bold text-slate-900">{t('howToApply.step3PartnerTitle', 'Submit Application to Partner Office')}</p>
                      <p className="text-slate-600 text-[11px] mt-0.5">
                        {t('howToApply.step3PartnerDesc', 'Submit your application form and project proposal directly at the partner counter.')}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* CTA Button to Partner Locator with Scheme ID filter */}
            <Link
              to={`/channel-partners?scheme_id=${scheme.scheme_id}`}
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs py-3 px-4 rounded-xl shadow transition flex items-center justify-center gap-2"
            >
              <MapPin className="w-4 h-4 text-sky-200" />
              {t('howToApply.ctaPartner', 'Find Authorized Channel Partners')}
            </Link>

            {officialUrl && (
              <button
                onClick={onOpenPortalModal}
                className="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs py-2 px-4 rounded-xl transition flex items-center justify-center gap-1.5"
              >
                {t('howToApply.ctaOfficialGuidelines', 'View Official Guidelines')}
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}

        {isUnverifiedRoute && (
          <div className="space-y-4">
            <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl space-y-2 text-xs text-amber-900">
              <div className="flex items-center gap-2 font-bold text-amber-950 text-sm">
                <AlertCircle className="w-4 h-4 text-amber-700" />
                {t('howToApply.unverifiedTitle', 'Departmental Application Route')}
              </div>
              <p className="text-amber-800 leading-relaxed text-xs">
                {t('howToApply.unverifiedDesc', 'Application route could not be verified from an open online portal or channel partner registry. Applications are accepted directly through concerned District Departments or institutional windows.')}
              </p>
            </div>

            <div className="space-y-2 text-xs text-slate-700">
              <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
                <span className="w-5 h-5 rounded-full bg-amber-600 text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
                  1
                </span>
                <div>
                  <p className="font-bold text-slate-900">{t('howToApply.step1UnverifiedTitle', 'Review Official Scheme Gazette')}</p>
                  <p className="text-slate-600 text-[11px] mt-0.5">
                    {t('howToApply.step1UnverifiedDesc', 'Check the authoritative ministry notification link below for eligibility criteria.')}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200">
                <span className="w-5 h-5 rounded-full bg-amber-600 text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
                  2
                </span>
                <div>
                  <p className="font-bold text-slate-900">{t('howToApply.step2UnverifiedTitle', 'Contact Local District Office')}</p>
                  <p className="text-slate-600 text-[11px] mt-0.5">
                    {t('howToApply.step2UnverifiedDesc', 'Visit your local District Welfare Officer, DIC, or Lead Bank District Manager.')}
                  </p>
                </div>
              </div>
            </div>

            {officialUrl ? (
              <button
                onClick={onOpenPortalModal}
                className="w-full bg-gov-blue hover:bg-gov-navy text-white font-bold text-xs py-3 px-4 rounded-xl shadow transition flex items-center justify-center gap-2"
              >
                {t('howToApply.ctaSource', 'View Official Source Guidelines')}
                <ExternalLink className="w-4 h-4" />
              </button>
            ) : (
              <div className="text-center p-2 text-xs text-slate-500 italic">
                {t('howToApply.noSourceLink', 'Official online application route is currently not verified.')}
              </div>
            )}
          </div>
        )}

        {/* Mandatory Transparency Disclaimer */}
        <div className="bg-slate-100/90 rounded-xl p-3.5 space-y-1 text-[11px] text-slate-600 border border-slate-200">
          <p className="font-semibold text-slate-800 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-sky-600" />
            {t('howToApply.disclaimerTitle', 'Official Notice')}
          </p>
          <p className="text-[10px] text-slate-500 leading-tight">
            {t('howToApply.disclaimer', 'Eligibility guidance only. Final eligibility and approval are determined by the concerned government authority.')}
          </p>
        </div>
      </div>

      {/* 2. DOCUMENTS YOU MAY NEED */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 pb-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-600" /> {t('documents.title', 'Required Documents Checklist')}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {t('documents.subtitle', 'Official documents required before application submission.')}
            </p>
          </div>
          {docs.length > 0 && (
            <span className="text-[11px] font-bold bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-full border border-indigo-200 shrink-0">
              {docs.length} {docs.length === 1 ? t('documents.officialRequirement', 'Requirement') : t('documents.officialRequirements', 'Requirements')}
            </span>
          )}
        </div>

        {/* Document Items List OR Uncertainty Notice */}
        {docs.length === 0 ? (
          <div className="bg-amber-50/80 border border-amber-200 p-4 rounded-xl flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-xs font-bold text-amber-900">{t('documents.uncertaintyTitle', 'Document List Under Review')}</p>
              <p className="text-xs text-amber-800 leading-relaxed">
                {t('documents.uncertaintyDesc', 'Specific document guidelines are being verified from authoritative ministry gazettes. Please carry standard KYC documents (Aadhaar, Bank Passbook, Proof of Residence).')}
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {docs.map((doc) => (
              <div
                key={doc.document_id}
                className="bg-slate-50 hover:bg-slate-100/80 transition p-4 rounded-xl border border-slate-200 text-xs space-y-2"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-slate-900 text-sm block">
                        {doc.document_name}
                      </span>
                      {doc.condition && (
                        <p className="text-[11px] text-slate-600 mt-0.5">
                          {doc.condition}
                        </p>
                      )}
                    </div>
                  </div>
                  <span
                    className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border uppercase shrink-0 ${
                      doc.requirement_type === 'REQUIRED' || doc.requirement_type === 'MANDATORY'
                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                        : doc.requirement_type === 'CONDITIONAL'
                        ? 'bg-amber-50 text-amber-700 border-amber-200'
                        : 'bg-slate-100 text-slate-700 border-slate-200'
                    }`}
                  >
                    {doc.requirement_type === 'REQUIRED' || doc.requirement_type === 'MANDATORY'
                      ? t('documents.mandatory', 'Mandatory')
                      : doc.requirement_type === 'CONDITIONAL'
                      ? t('documents.conditional', 'Conditional')
                      : t('documents.optional', 'Optional')}
                  </span>
                </div>

                {/* Source Provenance */}
                <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-[10px] text-slate-400">
                  <span className="flex items-center gap-1 font-mono">
                    <ShieldCheck className="w-3 h-3 text-emerald-600" />
                    {doc.document_id}
                  </span>
                  {doc.source_section && (
                    <span className="text-slate-500 truncate max-w-[200px]" title={doc.source_section}>
                      {t('documents.sourceLabel', 'Source:')} {doc.source_section}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Advisory / Safe Storage Callout */}
        <div className="bg-slate-100/90 rounded-xl p-3.5 space-y-1 text-[11px] text-slate-600 border border-slate-200">
          <p className="font-semibold text-slate-800 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-sky-600" />
            {t('documents.carryOriginals', 'Carry Original Verification Documents')}
          </p>
          <p className="text-[10px] text-slate-500 leading-tight">
            {t('documents.zeroStorage', 'Zero Document Storage: YojnaSetu never uploads, stores, or requests sensitive documents. Present physical or DigiLocker documents only to authorized centers.')}
          </p>
        </div>
      </div>
    </div>
  );
};
