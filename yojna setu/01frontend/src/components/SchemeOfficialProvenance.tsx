import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Scheme } from '../types';
import {
  ShieldCheck,
  Building2,
  ExternalLink,
  Calendar,
  CheckCircle2,
  TrendingUp,
  ArrowRight,
  Info
} from 'lucide-react';

interface SchemeOfficialProvenanceProps {
  scheme: Scheme;
  onOpenPortalModal?: () => void;
}

export const SchemeOfficialProvenance: React.FC<SchemeOfficialProvenanceProps> = ({
  scheme,
  onOpenPortalModal,
}) => {
  const { t } = useTranslation();

  const officialUrl = scheme.application_url || scheme.official_portal || scheme.official_source_url;

  const rawDate =
    (scheme as any).last_verified_date ||
    (scheme as any).source_date ||
    (scheme as any).updated_at;

  const formattedDate = (() => {
    if (!rawDate) return 'Not specified in available official source';
    const parsed = new Date(rawDate);
    return isNaN(parsed.getTime())
      ? 'Not specified in available official source'
      : parsed.toLocaleDateString('en-IN', {
          day: 'numeric',
          month: 'short',
          year: 'numeric',
        });
  })();

  const verificationStatus =
    scheme.verification_status ||
    (scheme.verifications && scheme.verifications.length > 0
      ? (scheme.verifications[0] as any).verification_status
      : 'VERIFIED');

  const hasPartners =
    scheme.application_route === 'CHANNEL_PARTNER' ||
    (scheme.partner_count !== undefined && scheme.partner_count !== null && scheme.partner_count > 0);

  return (
    <section id="official-source" className="scroll-mt-24 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg sm:text-xl font-extrabold text-[#3B2522] tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-[#EA717B]" />
            Official Source & Verification
          </h2>
          <p className="text-xs text-[#765E59] mt-0.5">
            Provenance, publishing authority, and official verification audit records.
          </p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs p-5 sm:p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          {/* 1. Official Ministry */}
          <div className="bg-[#FFFBF0] p-4 rounded-xl border border-[#E8D8D2] space-y-1">
            <span className="text-[10px] font-bold text-[#765E59] uppercase tracking-wider block">
              Ministry / Department
            </span>
            <p className="font-extrabold text-[#3B2522] leading-snug">
              {scheme.ministry || scheme.implementing_agency || 'Government of India'}
            </p>
            {scheme.implementing_agency && scheme.implementing_agency !== scheme.ministry && (
              <span className="text-[11px] text-[#765E59] block truncate" title={scheme.implementing_agency}>
                Agency: {scheme.implementing_agency}
              </span>
            )}
          </div>

          {/* 2. Verification Status */}
          <div className="bg-[#FFFBF0] p-4 rounded-xl border border-[#E8D8D2] space-y-1">
            <span className="text-[10px] font-bold text-[#765E59] uppercase tracking-wider block">
              Verification Status
            </span>
            <div className="pt-0.5">
              <span className="inline-flex items-center gap-1 font-bold text-emerald-800 bg-emerald-100 px-2.5 py-1 rounded-full text-xs">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                {verificationStatus}
              </span>
            </div>
            <span className="text-[11px] text-[#765E59] block pt-0.5">
              Deterministic source verification
            </span>
          </div>

          {/* 3. Last Verified Date */}
          <div className="bg-[#FFFBF0] p-4 rounded-xl border border-[#E8D8D2] space-y-1">
            <span className="text-[10px] font-bold text-[#765E59] uppercase tracking-wider block">
              {t('schemeDetail.lastVerifiedDate', 'Last Verified Date')}
            </span>
            <p className="font-bold text-[#3B2522] font-mono text-xs">
              {formattedDate}
            </p>
            <span className="text-[11px] text-[#765E59] block">
              {t('schemeDetail.officialAuditTimestamp', 'Official audit timestamp')}
            </span>
          </div>

          {/* 4. Official Gazette / Portal Link */}
          <div className="bg-[#FFFBF0] p-4 rounded-xl border border-[#E8D8D2] space-y-1 flex flex-col justify-between">
            <span className="text-[10px] font-bold text-[#765E59] uppercase tracking-wider block">
              {t('schemeDetail.authoritativePortal', 'Authoritative Portal')}
            </span>
            {officialUrl ? (
              onOpenPortalModal ? (
                <button
                  onClick={onOpenPortalModal}
                  className="text-xs font-bold text-[#EA717B] hover:text-[#d95d67] flex items-center gap-1.5 cursor-pointer truncate"
                >
                  <span className="truncate">{t('schemeDetail.visitOfficialPortal', 'Visit Official Portal')}</span>
                  <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                </button>
              ) : (
                <a
                  href={officialUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-bold text-[#EA717B] hover:text-[#d95d67] flex items-center gap-1.5 truncate"
                >
                  <span className="truncate">{t('schemeDetail.visitOfficialPortal', 'Visit Official Portal')}</span>
                  <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                </a>
              )
            ) : (
              <span className="text-[#765E59]/60 italic text-[11px]">
                {t('schemeDetail.notSpecifiedOfficial', 'Not specified in available official data')}
              </span>
            )}
            <span className="text-[10px] text-[#765E59]/70 block truncate font-mono">
              ID: {scheme.scheme_id}
            </span>
          </div>
        </div>

        {/* Channel Partner Discovery Callout (if partner routed) */}
        {hasPartners && (
          <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
            <div className="space-y-0.5">
              <span className="font-bold text-[#3B2522] flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-[#EA717B]" />
                Financial Health of Implementing Partners
              </span>
              <p className="text-[#765E59] text-[11px]">
                Inspect the prudential financial health indicators (YS-FIS-V1) for the State Channelizing Agencies and banks authorized to disburse this scheme.
              </p>
            </div>
            <Link
              to={`/financial-health/scheme/${scheme.scheme_id}`}
              className="text-xs font-bold text-white bg-[#EA717B] hover:bg-[#d95d67] px-3.5 py-2 rounded-xl shadow-warm-xs transition flex items-center gap-1.5 whitespace-nowrap shrink-0"
            >
              Explore Scheme Partners
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        )}
      </div>
    </section>
  );
};
