import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Building2, IndianRupee, ShieldCheck, Tag, ArrowRight, Sparkles, CheckCircle2 } from 'lucide-react';
import { Scheme } from '../types';
import { VerificationBadge } from './Badge';

import { CompareButton } from './CompareButton';

interface SchemeCardProps {
  scheme: Scheme;
}

export const SchemeCard: React.FC<SchemeCardProps> = ({ scheme }) => {
  const { t } = useTranslation();

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition flex flex-col justify-between overflow-hidden group">
      <div className="p-5">
        {/* Header Badges */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <VerificationBadge status={scheme.verification_status} />
          {(() => {
            const rawType = scheme.scheme_type || scheme.support_type;
            if (!rawType || rawType === 'UNKNOWN') return null;
            const cleanType = rawType.replace(/_/g, ' ').replace(/;/g, ' •');
            return (
              <span className="text-[11px] bg-slate-100 text-slate-700 font-semibold px-2.5 py-0.5 rounded border border-slate-300 uppercase">
                {cleanType}
              </span>
            );
          })()}
        </div>

        {/* Scheme Title */}
        <h3 className="text-base font-extrabold text-slate-900 group-hover:text-sky-700 transition line-clamp-2 mb-2">
          {scheme.scheme_name}
        </h3>

        {/* Ministry & Agency */}
        <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-4">
          <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span className="truncate">{scheme.ministry || scheme.implementing_agency || "Government of India"}</span>
        </div>

        {/* Objective */}
        <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed mb-4">
          {scheme.short_description || scheme.objective || scheme.purpose || "Verified government welfare and enterprise support scheme."}
        </p>

        {/* Key Financial Features Pill Grid */}
        <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-3 rounded-lg border border-slate-100 mb-4">
          {scheme.is_credit_scheme !== false && (scheme.max_loan_amount || scheme.interest_rate_max !== undefined) ? (
            <>
              <div>
                <span className="text-[10px] text-slate-400 font-medium block uppercase">{t('schemeCard.maxSupport')}</span>
                <span className="font-bold text-slate-800 flex items-center">
                  {scheme.max_loan_amount
                    ? scheme.max_loan_amount >= 10000000
                      ? `₹${(scheme.max_loan_amount / 10000000).toFixed(1)} Cr`
                      : scheme.max_loan_amount >= 100000
                      ? `₹${(scheme.max_loan_amount / 100000).toFixed(1)} Lakh`
                      : `₹${Number(scheme.max_loan_amount).toLocaleString('en-IN')}`
                    : scheme.max_loan_amount_raw && scheme.max_loan_amount_raw !== 'UNKNOWN'
                    ? scheme.max_loan_amount_raw
                    : 'As per appraisal'}
                </span>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 font-medium block uppercase">{t('schemeCard.interestRate')}</span>
                <span className="font-bold text-slate-800">
                  {scheme.interest_rate !== null && scheme.interest_rate !== undefined
                    ? scheme.interest_rate === 0
                      ? '0% (Interest-Free)'
                      : `${scheme.interest_rate}% p.a.`
                    : scheme.interest_rate_max !== null && scheme.interest_rate_max !== undefined
                    ? scheme.interest_rate_max === 0
                      ? '0% (Interest-Free)'
                      : `${scheme.interest_rate_max}% p.a.`
                    : t('calculator.asPerBank', 'As per bank')}
                </span>
              </div>
            </>
          ) : (
            <>
              <div>
                <span className="text-[10px] text-slate-400 font-medium block uppercase">{t('schemeCard.assistanceType', 'Assistance Type')}</span>
                <span className="font-bold text-slate-800 truncate block">
                  {scheme.financial_category === 'GRANT_SUBSIDY'
                    ? scheme.subsidy_percentage
                      ? `Subsidy (${scheme.subsidy_percentage}%)`
                      : scheme.grant_amount
                      ? `Grant (₹${(scheme.grant_amount / 100000).toFixed(1)}L)`
                      : 'Capital Subsidy'
                    : scheme.financial_category === 'SCHOLARSHIP'
                    ? 'Scholarship Grant'
                    : scheme.financial_category === 'TRAINING_SKILL'
                    ? 'Free Training / Kit'
                    : scheme.financial_category === 'DIRECT_BENEFIT'
                    ? 'Direct Benefit / DBT'
                    : scheme.financial_category === 'GUARANTEE_CREDIT_SUPPORT'
                    ? 'Credit Guarantee'
                    : 'Welfare Support'}
                </span>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 font-medium block uppercase">{t('schemeCard.loanFacility', 'Loan Facility')}</span>
                <span className="font-bold text-slate-500">
                  {t('common.notApplicable', 'Not applicable')}
                </span>
              </div>
            </>
          )}
        </div>

        {/* Target Group Tags */}
        <div className="flex flex-wrap gap-1.5">
          {(() => {
            const rawTarget = scheme.target_groups || scheme.marginalized_group || scheme.target_beneficiary;
            if (!rawTarget || rawTarget === 'UNKNOWN') {
              return (
                <span className="text-[10px] bg-slate-100 text-slate-700 font-medium px-2 py-0.5 rounded border border-slate-200 truncate max-w-[200px]">
                  {t('schemeCard.target')} {t('schemeCard.allCitizens')}
                </span>
              );
            }
            return (
              <span className="text-[10px] bg-amber-50 text-amber-800 font-medium px-2 py-0.5 rounded border border-amber-200 truncate max-w-[200px]">
                {t('schemeCard.target')} {rawTarget.replace(/_/g, ' ')}
              </span>
            );
          })()}
          {scheme.sector && scheme.sector !== 'UNKNOWN' && (
            <span className="text-[10px] bg-sky-50 text-sky-800 font-medium px-2 py-0.5 rounded border border-sky-200">
              {t('schemeCard.sector')} {scheme.sector.replace(/_/g, ' ')}
            </span>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="bg-slate-50 px-5 py-3 border-t border-slate-100 flex items-center justify-between gap-2">
        <Link
          to={`/schemes/${scheme.scheme_id}`}
          className="text-xs font-bold text-sky-700 hover:text-sky-900 flex items-center gap-1 group-hover:translate-x-0.5 transition"
        >
          {t('schemeCard.viewDetails')}
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>

        <div className="flex items-center gap-2">
          <CompareButton schemeId={scheme.scheme_id} variant="compact" />
          {scheme.is_credit_scheme !== false && (scheme.max_loan_amount || scheme.interest_rate_max !== undefined) ? (
            <Link
              to={`/calculator?scheme=${scheme.scheme_id}`}
              className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 bg-emerald-50 px-2.5 py-1.5 rounded-lg border border-emerald-200 transition"
            >
              {t('schemeCard.calcEMI')}
            </Link>
          ) : (
            <Link
              to={`/schemes/${scheme.scheme_id}`}
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 px-2.5 py-1.5 rounded-lg border border-slate-200 transition"
            >
              {t('schemeCard.guidelines', 'Guidelines')}
            </Link>
          )}
        </div>
      </div>
    </div>
  );
};
