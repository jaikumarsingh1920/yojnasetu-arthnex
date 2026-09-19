import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Building2, ArrowRight, Calculator, MapPin, FileText, Banknote, Users } from 'lucide-react';
import { Scheme } from '../types';
import { VerificationBadge } from './Badge';
import { CompareButton } from './CompareButton';

interface SchemeCardProps {
  scheme: Scheme;
}

export const SchemeCard: React.FC<SchemeCardProps> = ({ scheme }) => {
  const { t } = useTranslation();

  return (
    <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-sm hover:shadow-warm-md hover:border-[#D9C4BC] transition-all duration-200 flex flex-col justify-between overflow-hidden group">
      <div className="p-5 sm:p-6 space-y-3.5">
        {/* Top Badges: Ministry & Category */}
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-semibold text-[#765E59] truncate max-w-[220px]">
            {scheme.ministry || scheme.implementing_agency || 'Government of India'}
          </span>
          {(() => {
            const rawType = scheme.scheme_type || scheme.support_type || scheme.financial_category;
            if (!rawType || rawType === 'UNKNOWN') return null;
            const cleanType = rawType.replace(/_/g, ' ').replace(/;/g, ' •');
            return (
              <span className="text-[10px] bg-[#EAF4EE] text-[#1B5E20] border border-[#A5D6A7]/60 font-bold px-2 py-0.5 rounded-lg uppercase tracking-wider shrink-0">
                {cleanType}
              </span>
            );
          })()}
        </div>

        {/* Scheme Title */}
        <Link to={`/schemes/${scheme.scheme_id}`} className="block">
          <h3 className="text-base font-extrabold text-[#3B2522] group-hover:text-[#EA717B] transition line-clamp-2 leading-snug">
            {scheme.scheme_name}
          </h3>
        </Link>

        {/* Objective / Purpose */}
        <p className="text-xs text-[#765E59] line-clamp-2 leading-relaxed">
          {scheme.short_description ||
            scheme.objective ||
            scheme.purpose ||
            'Verified government welfare and enterprise support scheme.'}
        </p>

        {/* 3 Visual Feature Blocks with Peach Gelato / Warm Icon Tiles */}
        <div className="space-y-2.5 pt-1">
          {/* 1. Financial Support */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#FFD0CA]/60 text-[#EA717B] border border-[#EA717B]/20 flex items-center justify-center shrink-0">
              <Banknote className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <span className="text-[11px] text-[#9B817A] block font-medium">Financial Support:</span>
              <span className="text-xs font-bold text-[#3B2522] truncate block">
                {scheme.max_loan_amount
                  ? scheme.max_loan_amount >= 10000000
                    ? `Up to ₹${(scheme.max_loan_amount / 10000000).toFixed(1)} Cr`
                    : scheme.max_loan_amount >= 100000
                    ? `Up to ₹${(scheme.max_loan_amount / 100000).toFixed(1)} Lakh`
                    : `Up to ₹${Number(scheme.max_loan_amount).toLocaleString('en-IN')}`
                  : scheme.subsidy_percentage
                  ? `${scheme.subsidy_percentage}% Capital Subsidy`
                  : scheme.financial_category === 'GRANT_SUBSIDY'
                  ? 'Capital Subsidy / Grant'
                  : 'Official Financial Assistance'}
              </span>
            </div>
          </div>

          {/* 2. Eligible Beneficiary */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#FFF4EC] text-[#F7AE56] border border-[#F7AE56]/30 flex items-center justify-center shrink-0">
              <Users className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <span className="text-[11px] text-[#9B817A] block font-medium">Eligible:</span>
              <span className="text-xs font-bold text-[#3B2522] truncate block">
                {(() => {
                  const target = scheme.target_groups || scheme.marginalized_group || scheme.target_beneficiary;
                  if (target && target !== 'UNKNOWN') return target.replace(/_/g, ' ');
                  if (scheme.min_age || scheme.max_age) {
                    return `${scheme.min_age || 18}+ years`;
                  }
                  return 'Citizens meeting scheme criteria';
                })()}
              </span>
            </div>
          </div>

          {/* 3. Channel Partner Delivery */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#FFF0EE] text-[#EA717B] border border-[#FFD0CA] flex items-center justify-center shrink-0">
              <Building2 className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <span className="text-[11px] text-[#9B817A] block font-medium">Partners:</span>
              <span className="text-xs font-bold text-[#3B2522] truncate block">
                {scheme.application_route === 'OFFICIAL_PORTAL'
                  ? 'Official Ministry Portal'
                  : 'Authorized Banks & Facilitation Centers'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div className="bg-[#FFF4EC]/70 px-5 py-3.5 border-t border-[#E8D8D2] flex items-center justify-between gap-3">
        <Link
          to={`/schemes/${scheme.scheme_id}`}
          className="flex-1 inline-flex items-center justify-center gap-1.5 bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold text-xs py-2 px-3.5 rounded-xl transition duration-200 shadow-warm-sm group-hover:shadow-warm-md"
        >
          <span>{t('schemeCard.viewDetails', 'View Details')}</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </Link>

        <div className="flex items-center gap-1 shrink-0">
          <CompareButton schemeId={scheme.scheme_id} schemeName={scheme.scheme_name} variant="compact" />
          <Link
            to={`/channel-partners?scheme_id=${scheme.scheme_id}`}
            className="p-2 rounded-xl text-[#765E59] hover:text-[#3B2522] hover:bg-white border border-transparent hover:border-[#E8D8D2] transition"
            title="Locate Authorized Channel Partners"
          >
            <MapPin className="w-3.5 h-3.5" />
          </Link>
          {scheme.is_credit_scheme !== false &&
            (scheme.max_loan_amount || scheme.interest_rate_max !== undefined) && (
              <Link
                to={`/calculator?scheme=${scheme.scheme_id}`}
                className="p-2 rounded-xl text-[#765E59] hover:text-[#3B2522] hover:bg-white border border-transparent hover:border-[#E8D8D2] transition"
                title="Calculate EMI & Subsidy"
              >
                <Calculator className="w-3.5 h-3.5" />
              </Link>
            )}
        </div>
      </div>
    </div>
  );
};
