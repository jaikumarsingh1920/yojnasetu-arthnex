import React from 'react';
import { useTranslation } from 'react-i18next';
import { Scheme } from '../types';
import { formatCurrency } from '../utils/formatters';
import {
  Coins,
  Percent,
  Calendar,
  Users,
  Route,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';

interface SchemeAtAGlanceProps {
  scheme: Scheme;
}

interface GlanceCardItem {
  id: string;
  label: string;
  value: string;
  subtext?: string;
  icon: React.FC<{ className?: string }>;
  iconBg: string;
  iconColor: string;
}

export const SchemeAtAGlance: React.FC<SchemeAtAGlanceProps> = ({ scheme }) => {
  const { t } = useTranslation();
  const cards: GlanceCardItem[] = [];

  // 1. Maximum Loan / Assistance / Project Cost
  const maxLoan = scheme.max_loan_amount;
  const maxProject = scheme.max_project_cost;
  const grantAmount = scheme.grant_amount;

  if (maxLoan && Number(maxLoan) > 0) {
    cards.push({
      id: 'max-loan',
      label: t('shared.maxLoanAmount'),
      value: formatCurrency(Number(maxLoan)),
      subtext: scheme.min_loan_amount ? `${t('shared.min', 'Min')}: ${formatCurrency(Number(scheme.min_loan_amount))}` : t('schemeDetail.glance.asPerSchemeLimit', 'As per official scheme limit'),
      icon: Coins,
      iconBg: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
    });
  } else if (maxProject && Number(maxProject) > 0) {
    cards.push({
      id: 'max-project',
      label: t('shared.maxProjectCost'),
      value: formatCurrency(Number(maxProject)),
      subtext: scheme.min_project_cost ? `${t('shared.min', 'Min')}: ${formatCurrency(Number(scheme.min_project_cost))}` : t('schemeDetail.glance.projectAppraisalLimit', 'Project appraisal limit'),
      icon: Coins,
      iconBg: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
    });
  } else if (grantAmount && Number(grantAmount) > 0) {
    cards.push({
      id: 'grant-amount',
      label: t('shared.financialGrant'),
      value: formatCurrency(Number(grantAmount)),
      subtext: t('schemeDetail.glance.directNonRepayable', 'Direct non-repayable assistance'),
      icon: Coins,
      iconBg: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
    });
  }

  // 2. Subsidy / Financial Benefit
  const subsidyPercent = scheme.subsidy_percentage;
  const maxSubsidy = scheme.max_subsidy_amount;
  const benefitDesc = scheme.benefit_description;

  if (subsidyPercent && Number(subsidyPercent) > 0) {
    cards.push({
      id: 'subsidy',
      label: t('shared.subsidyMarginMoney'),
      value: `${subsidyPercent}%`,
      subtext: maxSubsidy ? `${t('shared.upTo', 'Up to')} ${formatCurrency(Number(maxSubsidy))}` : t('schemeDetail.glance.govtCapitalSubsidy', 'Government capital subsidy'),
      icon: Sparkles,
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-600',
    });
  } else if (maxSubsidy && Number(maxSubsidy) > 0) {
    cards.push({
      id: 'max-subsidy',
      label: t('shared.maximumSubsidySupport'),
      value: formatCurrency(Number(maxSubsidy)),
      subtext: t('schemeDetail.glance.govtCapitalSubsidy', 'Direct government capital subsidy'),
      icon: Sparkles,
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-600',
    });
  } else if (benefitDesc && benefitDesc.trim().length > 3 && !benefitDesc.includes('RULE-')) {
    cards.push({
      id: 'benefit-desc',
      label: t('shared.financialGrant'),
      value: benefitDesc.length > 45 ? `${benefitDesc.slice(0, 45)}...` : benefitDesc,
      subtext: t('shared.documentedFocusGroup', 'Documented welfare assistance'),
      icon: Sparkles,
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-600',
    });
  }

  // 3. Interest Rate
  const rate = scheme.interest_rate;
  const minRate = scheme.interest_rate_min;
  const maxRate = scheme.interest_rate_max;

  if (rate !== undefined && rate !== null && Number(rate) >= 0) {
    cards.push({
      id: 'interest-rate',
      label: t('shared.concessionalInterestRate'),
      value: Number(rate) === 0 ? t('shared.interestFree', '0% (Interest-Free)') : `${rate}% ${t('shared.perAnnum', 'per annum')}`,
      subtext: scheme.interest_rate_type || t('shared.annualReducingBalance', 'Annual reducing balance rate'),
      icon: Percent,
      iconBg: 'bg-sky-50',
      iconColor: 'text-sky-600',
    });
  } else if (maxRate !== undefined && maxRate !== null && Number(maxRate) > 0) {
    const rateText = minRate ? `${minRate}% – ${maxRate}% ${t('shared.pA', 'p.a.')}` : `${t('shared.upTo', 'Up to')} ${maxRate}% ${t('shared.pA', 'p.a.')}`;
    cards.push({
      id: 'interest-rate-range',
      label: t('shared.interestRateRange'),
      value: rateText,
      subtext: t('shared.concessionalSchemeRate', 'Concessional scheme rate'),
      icon: Percent,
      iconBg: 'bg-sky-50',
      iconColor: 'text-sky-600',
    });
  }

  // 4. Repayment Period & Moratorium
  const tenureMonths = scheme.repayment_period_months || scheme.repayment_period_max_months;
  const moratorium = scheme.moratorium_period_months || scheme.moratorium_min_months;

  if (tenureMonths && Number(tenureMonths) > 0) {
    const years = (Number(tenureMonths) / 12).toFixed(Number(tenureMonths) % 12 === 0 ? 0 : 1);
    cards.push({
      id: 'repayment-tenure',
      label: t('shared.repaymentTenure'),
      value: `${t('shared.upTo', 'Up to')} ${tenureMonths} ${t('schemeDetail.repaymentPeriod', 'Months')} (${years} ${t('schemeDetail.years', 'Years')})`,
      subtext: moratorium ? `+ ${moratorium} ${t('shared.moratoriumSubtext', 'months moratorium')}` : t('shared.structuredRepaymentTenure', 'Structured repayment tenure'),
      icon: Calendar,
      iconBg: 'bg-indigo-50',
      iconColor: 'text-indigo-600',
    });
  }

  // 5. Target Beneficiaries
  const targetBeneficiary =
    scheme.target_groups ||
    scheme.marginalized_group ||
    scheme.target_beneficiary ||
    scheme.applicant_types;

  if (targetBeneficiary && targetBeneficiary.trim().length > 0) {
    const cleanTarget = targetBeneficiary.replace(/_/g, ' ');
    cards.push({
      id: 'target-beneficiaries',
      label: t('shared.targetBeneficiaries'),
      value: cleanTarget.length > 40 ? `${cleanTarget.slice(0, 40)}...` : cleanTarget,
      subtext: scheme.sector ? `${t('shared.sector', 'Sector')}: ${scheme.sector}` : t('shared.documentedFocusGroup', 'Documented focus group'),
      icon: Users,
      iconBg: 'bg-violet-50',
      iconColor: 'text-violet-600',
    });
  }

  // 6. Application Route
  const route = scheme.application_route;
  const isPartnerRouted =
    route === 'CHANNEL_PARTNER' ||
    (scheme.partner_count !== undefined && scheme.partner_count !== null && scheme.partner_count > 0);

  let routeLabel = t('shared.departmentalRoute', 'Departmental Route');
  let routeSubtext = t('shared.districtWelfareOffice', 'District welfare office / offline window');
  if (route === 'DIRECT_PORTAL') {
    routeLabel = t('shared.directGovtPortal', 'Direct Govt Portal');
    routeSubtext = t('shared.onlineDirectPortalApp', 'Online direct portal application');
  } else if (isPartnerRouted) {
    routeLabel = t('shared.authorizedChannelPartner', 'Authorized Channel Partner');
    routeSubtext = scheme.partner_count ? `${scheme.partner_count} ${t('shared.mappedPartnerInstitutions', 'mapped partner institutions')}` : t('shared.stateChannelizingAgencies', 'State Channelizing Agencies & Banks');
  }

  cards.push({
    id: 'application-route',
    label: t('shared.processingRoute'),
    value: routeLabel,
    subtext: routeSubtext,
    icon: Route,
    iconBg: 'bg-rose-50',
    iconColor: 'text-rose-600',
  });

  // If no cards were generated (extremely rare fallback), return null
  if (cards.length === 0) return null;

  return (
    <section id="glance" className="scroll-mt-24 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-gov-saffron" />
            {t('shared.schemeAtAGlance')}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {t('shared.glanceSubtitle')}
          </p>
        </div>
        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200 self-start sm:self-auto">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          {t('shared.verifiedGazetteParams')}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.id}
              className="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200/90 shadow-xs hover:shadow-md hover:border-slate-300 transition-all duration-150 flex items-start gap-3.5 group"
            >
              <div className={`w-11 h-11 rounded-xl ${card.iconBg} ${card.iconColor} flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform`}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="min-w-0 flex-1 space-y-1">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block truncate">
                  {card.label}
                </span>
                <p className="text-base sm:text-lg font-extrabold text-slate-900 leading-tight truncate" title={card.value}>
                  {card.value}
                </p>
                {card.subtext && (
                  <p className="text-[11px] text-slate-500 truncate" title={card.subtext}>
                    {card.subtext}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
