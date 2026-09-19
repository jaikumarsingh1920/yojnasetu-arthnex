import React from 'react';
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
  Building2,
  Clock
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
  const cards: GlanceCardItem[] = [];

  // 1. Maximum Loan / Assistance / Project Cost
  const maxLoan = scheme.max_loan_amount;
  const maxProject = scheme.max_project_cost;
  const grantAmount = scheme.grant_amount;

  if (maxLoan && Number(maxLoan) > 0) {
    cards.push({
      id: 'max-loan',
      label: 'Maximum Loan Amount',
      value: formatCurrency(Number(maxLoan)),
      subtext: scheme.min_loan_amount ? `Min: ${formatCurrency(Number(scheme.min_loan_amount))}` : 'As per official scheme limit',
      icon: Coins,
      iconBg: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
    });
  } else if (maxProject && Number(maxProject) > 0) {
    cards.push({
      id: 'max-project',
      label: 'Maximum Project Cost',
      value: formatCurrency(Number(maxProject)),
      subtext: scheme.min_project_cost ? `Min: ${formatCurrency(Number(scheme.min_project_cost))}` : 'Project appraisal limit',
      icon: Coins,
      iconBg: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
    });
  } else if (grantAmount && Number(grantAmount) > 0) {
    cards.push({
      id: 'grant-amount',
      label: 'Financial Grant',
      value: formatCurrency(Number(grantAmount)),
      subtext: 'Direct non-repayable assistance',
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
      label: 'Subsidy / Margin Money',
      value: `${subsidyPercent}% of Project Cost`,
      subtext: maxSubsidy ? `Up to ${formatCurrency(Number(maxSubsidy))}` : 'Government capital subsidy',
      icon: Sparkles,
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-600',
    });
  } else if (maxSubsidy && Number(maxSubsidy) > 0) {
    cards.push({
      id: 'max-subsidy',
      label: 'Maximum Subsidy Support',
      value: formatCurrency(Number(maxSubsidy)),
      subtext: 'Direct government capital subsidy',
      icon: Sparkles,
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-600',
    });
  } else if (benefitDesc && benefitDesc.trim().length > 3 && !benefitDesc.includes('RULE-')) {
    cards.push({
      id: 'benefit-desc',
      label: 'Financial Assistance',
      value: benefitDesc.length > 45 ? `${benefitDesc.slice(0, 45)}...` : benefitDesc,
      subtext: 'Documented welfare assistance',
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
      label: 'Concessional Interest Rate',
      value: Number(rate) === 0 ? '0% (Interest-Free)' : `${rate}% per annum`,
      subtext: scheme.interest_rate_type || 'Annual reducing balance rate',
      icon: Percent,
      iconBg: 'bg-sky-50',
      iconColor: 'text-sky-600',
    });
  } else if (maxRate !== undefined && maxRate !== null && Number(maxRate) > 0) {
    const rateText = minRate ? `${minRate}% – ${maxRate}% p.a.` : `Up to ${maxRate}% p.a.`;
    cards.push({
      id: 'interest-rate-range',
      label: 'Interest Rate Range',
      value: rateText,
      subtext: 'Concessional scheme rate',
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
      label: 'Repayment Period',
      value: `Up to ${tenureMonths} Months (${years} Years)`,
      subtext: moratorium ? `+ ${moratorium} months moratorium` : 'Structured repayment tenure',
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
      label: 'Target Beneficiaries',
      value: cleanTarget.length > 40 ? `${cleanTarget.slice(0, 40)}...` : cleanTarget,
      subtext: scheme.sector ? `Sector: ${scheme.sector}` : 'Documented focus group',
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

  let routeLabel = 'Departmental Route';
  let routeSubtext = 'District welfare office / offline window';
  if (route === 'DIRECT_PORTAL') {
    routeLabel = 'Direct Govt Portal';
    routeSubtext = 'Online direct portal application';
  } else if (isPartnerRouted) {
    routeLabel = 'Authorized Channel Partner';
    routeSubtext = scheme.partner_count ? `${scheme.partner_count} mapped partner institutions` : 'State Channelizing Agencies & Banks';
  }

  cards.push({
    id: 'application-route',
    label: 'Application Route',
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
            Scheme at a Glance
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Key program parameters verified from official gazette documentation.
          </p>
        </div>
        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200 self-start sm:self-auto">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          Verified Gazette Parameters
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
