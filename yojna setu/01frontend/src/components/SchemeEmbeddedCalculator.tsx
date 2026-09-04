import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Scheme } from '../types';
import { formatCurrency, formatPercent } from '../utils/formatters';
import {
  Calculator as CalcIcon,
  ShieldCheck,
  Percent,
  Calendar,
  IndianRupee,
  PieChart,
  ChevronDown,
  ChevronUp,
  Award,
  Sparkles,
  Info,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

interface SchemeEmbeddedCalculatorProps {
  scheme: Scheme;
  initialLoanAmount?: number | null;
}

export const SchemeEmbeddedCalculator: React.FC<SchemeEmbeddedCalculatorProps> = ({ scheme, initialLoanAmount }) => {
  const { t } = useTranslation();

  const isCredit = scheme.is_credit_scheme !== false && (
    Boolean(scheme.max_loan_amount) ||
    scheme.interest_rate !== undefined ||
    scheme.interest_rate_max !== undefined ||
    scheme.loan_available === 'YES'
  );

  const hasFixedLoan = scheme.max_loan_amount !== undefined && scheme.max_loan_amount !== null && Number(scheme.max_loan_amount) > 0;
  const officialMaxLoan = hasFixedLoan ? Number(scheme.max_loan_amount) : 1000000;
  const officialMinLoan = scheme.min_loan_amount ? Number(scheme.min_loan_amount) : 10000;

  const hasFixedRate = (scheme.interest_rate !== undefined && scheme.interest_rate !== null) ||
                       (scheme.interest_rate_max !== undefined && scheme.interest_rate_max !== null);
  const officialRate = hasFixedRate
    ? (scheme.interest_rate !== undefined && scheme.interest_rate !== null ? Number(scheme.interest_rate) : Number(scheme.interest_rate_max))
    : null;

  const hasFixedTenure = Boolean(scheme.repayment_period_months || scheme.repayment_period_max_months);
  const officialTenureMonths = hasFixedTenure
    ? Number(scheme.repayment_period_months || scheme.repayment_period_max_months)
    : 36;

  // Local interactive slider state
  const [loanAmount, setLoanAmount] = useState<number>(() => {
    if (initialLoanAmount && initialLoanAmount > 0) {
      return Math.min(initialLoanAmount, officialMaxLoan);
    }
    if (officialMaxLoan >= 100000) return Math.min(200000, officialMaxLoan);
    return officialMaxLoan;
  });
  const [annualInterestRate, setAnnualInterestRate] = useState<number>(officialRate ?? 8.5);
  const [tenureMonths, setTenureMonths] = useState<number>(officialTenureMonths);
  const [showAmortization, setShowAmortization] = useState<boolean>(false);
  const [scheduleMode, setScheduleMode] = useState<'MONTHLY' | 'YEARLY'>('YEARLY');

  // Mathematical reducing-balance EMI calculation
  const calculation = useMemo(() => {
    const P = Math.max(0, loanAmount);
    const R = Math.max(0, annualInterestRate);
    const N = Math.max(1, tenureMonths);

    let emi = 0;
    let totalInterest = 0;
    const schedule: Array<{
      month: number;
      opening: number;
      installment: number;
      principal: number;
      interest: number;
      closing: number;
    }> = [];

    if (R === 0) {
      // 0% Interest Welfare Loan
      emi = Math.round((P / N) * 100) / 100;
      let balance = P;
      for (let m = 1; m <= N; m++) {
        const principalComp = m === N ? balance : Math.min(balance, emi);
        const closing = Math.max(0, Math.round((balance - principalComp) * 100) / 100);
        schedule.push({
          month: m,
          opening: Math.round(balance * 100) / 100,
          installment: Math.round(principalComp * 100) / 100,
          principal: Math.round(principalComp * 100) / 100,
          interest: 0,
          closing,
        });
        balance = closing;
      }
    } else {
      // Standard Reducing Balance: EMI = P * r * (1+r)^N / ((1+r)^N - 1)
      const r = R / (12 * 100);
      const onePlusR_N = Math.pow(1 + r, N);
      emi = Math.round((P * r * onePlusR_N / (onePlusR_N - 1)) * 100) / 100;

      let balance = P;
      for (let m = 1; m <= N; m++) {
        const opening = balance;
        const interest = Math.round(opening * r * 100) / 100;
        let principalComp = 0;
        let installment = emi;

        if (m === N) {
          principalComp = opening;
          installment = Math.round((principalComp + interest) * 100) / 100;
          balance = 0;
        } else {
          principalComp = Math.round((emi - interest) * 100) / 100;
          installment = emi;
          balance = Math.max(0, Math.round((opening - principalComp) * 100) / 100);
        }

        totalInterest += interest;
        schedule.push({
          month: m,
          opening,
          installment,
          principal: principalComp,
          interest,
          closing: balance,
        });
      }
      totalInterest = Math.round(totalInterest * 100) / 100;
    }

    const totalRepayment = Math.round((P + totalInterest) * 100) / 100;
    const principalPct = totalRepayment > 0 ? Math.round((P / totalRepayment) * 100) : 100;
    const interestPct = totalRepayment > 0 ? Math.round((totalInterest / totalRepayment) * 100) : 0;

    // Aggregate Yearly Schedule
    const yearlySchedule: Array<{
      year: number;
      opening: number;
      principal: number;
      interest: number;
      total: number;
      closing: number;
    }> = [];

    let currentYear = 1;
    let yrPrincipal = 0;
    let yrInterest = 0;
    let yrOpening = P;

    schedule.forEach((entry, idx) => {
      yrPrincipal += entry.principal;
      yrInterest += entry.interest;

      if ((idx + 1) % 12 === 0 || idx === schedule.length - 1) {
        yearlySchedule.push({
          year: currentYear,
          opening: yrOpening,
          principal: Math.round(yrPrincipal * 100) / 100,
          interest: Math.round(yrInterest * 100) / 100,
          total: Math.round((yrPrincipal + yrInterest) * 100) / 100,
          closing: entry.closing,
        });
        currentYear += 1;
        yrPrincipal = 0;
        yrInterest = 0;
        yrOpening = entry.closing;
      }
    });

    return {
      emi,
      totalInterest,
      totalRepayment,
      principalPct,
      interestPct,
      schedule,
      yearlySchedule,
    };
  }, [loanAmount, annualInterestRate, tenureMonths]);

  // Non-credit scheme rendering (Grants, Subsidies, Training, Scholarships, Direct Benefit)
  if (!isCredit) {
    const categoryName = (scheme.financial_category || 'GRANT_SUBSIDY').replace(/_/g, ' ');
    return (
      <div id="financial-terms" className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-purple-100 text-purple-800 text-[10px] font-extrabold px-2.5 py-0.5 rounded uppercase tracking-wider">
                {categoryName}
              </span>
              <span className="text-slate-400 text-xs">• {t('calculator.nonCreditBadge', 'No Loan Required')}</span>
            </div>
            <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 mt-1 flex items-center gap-2">
              <Award className="w-5 h-5 text-purple-600" /> {t('calculator.nonCreditTitle', 'Grant / Direct Welfare Benefit Scheme')}
            </h2>
          </div>
        </div>

        {/* Advisory Notice Banner */}
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl text-xs text-amber-950 flex items-start gap-3">
          <Info className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-bold">{t('calculator.nonCreditNoticeDesc', 'Loan / EMI calculation is not applicable for this scheme.')}</p>
            <p className="text-amber-900 leading-relaxed">
              {t('calculator.nonCreditSubtitle', 'This scheme provides direct financial grants, subsidies, or skill toolkits without repayable loan terms.')}
            </p>
          </div>
        </div>

        {/* Structured Financial Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
            <span className="text-slate-500 text-[10px] uppercase font-bold">{t('calculator.assistanceType', 'Assistance Type')}</span>
            <p className="font-extrabold text-slate-900 text-sm">
              {scheme.financial_category === 'GRANT_SUBSIDY'
                ? 'Capital Subsidy / Grant'
                : scheme.financial_category === 'SCHOLARSHIP'
                ? 'Education Scholarship Grant'
                : scheme.financial_category === 'TRAINING_SKILL'
                ? 'Free Training & Toolkits'
                : scheme.financial_category === 'DIRECT_BENEFIT'
                ? 'Direct Cash Transfer (DBT)'
                : scheme.financial_category === 'GUARANTEE_CREDIT_SUPPORT'
                ? 'Credit Guarantee Cover'
                : 'Welfare Assistance'}
            </p>
            <span className="text-slate-500 text-[11px] block">{t('calculator.nonRepayableAssistance', 'Non-repayable assistance')}</span>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
            <span className="text-slate-500 text-[10px] uppercase font-bold">{t('calculator.assistanceQuantum', 'Assistance Quantum')}</span>
            <p className="font-extrabold text-emerald-700 text-sm">
              {scheme.subsidy_percentage
                ? `${scheme.subsidy_percentage}% of Project Cost`
                : scheme.grant_amount
                ? formatCurrency(scheme.grant_amount)
                : scheme.benefit_description || 'As per scheme guidelines'}
            </p>
            <span className="text-slate-500 text-[11px] block">{t('calculator.officialTermsPreloaded', 'Official Terms Pre-Loaded')}</span>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
            <span className="text-slate-500 text-[10px] uppercase font-bold">{t('calculator.repaymentObligation', 'Repayment Obligation')}</span>
            <p className="font-extrabold text-slate-600 text-sm">
              {t('common.notApplicable', 'Not applicable')}
            </p>
            <span className="text-slate-500 text-[11px] block">{t('calculator.zeroRepayment', 'Zero repayment obligation')}</span>
          </div>
        </div>

        {/* Factual Assistance Summary */}
        {scheme.financial_assistance_summary && (
          <div className="bg-sky-50 border border-sky-100 p-4 rounded-xl text-xs text-sky-900 flex items-start gap-2.5">
            <Sparkles className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block mb-0.5">{t('calculator.officialAssistanceSummary', 'Official Assistance Summary:')}</span>
              <p className="text-sky-800 leading-relaxed">{scheme.financial_assistance_summary}</p>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Credit / Loan Scheme Interactive Calculator
  return (
    <div id="calculator" className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="bg-emerald-100 text-emerald-800 text-[10px] font-extrabold px-2.5 py-0.5 rounded uppercase tracking-wider">
              {t('calculator.loanAndCreditCalc', 'LOAN & CREDIT CALCULATOR')}
            </span>
            <span className="text-slate-400 text-xs">• {t('calculator.schemeAware', 'Scheme-Aware')}</span>
          </div>
          <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 mt-1 flex items-center gap-2">
            <CalcIcon className="w-5 h-5 text-emerald-600" /> {t('calculator.calcEmiAndRepayment', 'Calculate EMI & Loan Repayment')}
          </h2>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>{t('calculator.officialTermsPreloaded', 'Official Terms Pre-Loaded')}</span>
        </div>
      </div>

      {/* Official Guidelines Disclosure Notices */}
      {!hasFixedRate && (
        <div className="bg-sky-50 border border-sky-200 p-3.5 rounded-xl text-xs text-sky-900 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">{t('calculator.rateDisclosure', 'Interest Rate Disclosure')}:</span>
            <span className="ml-1 text-sky-800">
              {t('calculator.rateDisclosureDesc', 'Interest rate: As determined by the financing institution / not specified in available official scheme guidelines. Use the slider below to simulate benchmark interest rates.')}
            </span>
          </div>
        </div>
      )}

      {/* Calculator Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Sliders & Controls */}
        <div className="lg:col-span-7 space-y-6">
          {/* Principal / Loan Amount */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                {t('calculator.loanAmountPrincipal', 'Loan Amount (Principal)')}
              </label>
              <span className="text-sm font-extrabold text-gov-navy font-mono bg-sky-50 px-2.5 py-0.5 rounded-lg border border-sky-100">
                {formatCurrency(loanAmount)}
              </span>
            </div>

            <input
              type="range"
              min={officialMinLoan}
              max={officialMaxLoan}
              step={Math.max(1000, Math.round(officialMaxLoan / 100))}
              value={loanAmount}
              onChange={(e) => setLoanAmount(Number(e.target.value))}
              className="w-full accent-emerald-600 cursor-pointer h-2 bg-slate-200 rounded-lg"
            />

            <div className="flex flex-wrap justify-between items-center text-[10px] text-slate-400 font-medium gap-1">
              <span>{t('compare.min', 'Min')}: {scheme.min_loan_amount ? formatCurrency(officialMinLoan) : t('calculator.asPerBank', 'As per bank')}</span>
              <span className="text-right truncate max-w-[200px]">
                {hasFixedLoan ? t('calculator.maxLimit', 'Max Limit: {{amount}}', { amount: formatCurrency(officialMaxLoan) }) : t('calculator.asPerBank', 'As per bank appraisal')}
              </span>
            </div>

            {/* Quick Presets */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {[50000, 100000, 200000, 500000, officialMaxLoan]
                .filter((v, idx, arr) => v <= officialMaxLoan && arr.indexOf(v) === idx)
                .map((val) => (
                  <button
                    key={val}
                    type="button"
                    onClick={() => setLoanAmount(val)}
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-lg border transition ${
                      loanAmount === val
                        ? 'bg-emerald-600 text-white border-emerald-600'
                        : 'bg-slate-50 text-slate-700 hover:bg-slate-100 border-slate-200'
                    }`}
                  >
                    {formatCurrency(val)}
                  </button>
                ))}
            </div>
          </div>

          {/* Interest Rate */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                {hasFixedRate ? t('calculator.annualInterestRate', 'Annual Interest Rate (% p.a.)') : t('calculator.simulateRate', 'Simulate Interest Rate (% p.a.)')}
              </label>
              <span className="text-sm font-extrabold text-amber-700 font-mono bg-amber-50 px-2.5 py-0.5 rounded-lg border border-amber-100">
                {annualInterestRate === 0 ? t('calculator.interestFree', '0% (Interest-Free)') : `${annualInterestRate}% p.a.`}
              </span>
            </div>

            <input
              type="range"
              min="0"
              max="18"
              step="0.25"
              value={annualInterestRate}
              onChange={(e) => setAnnualInterestRate(Number(e.target.value))}
              className="w-full accent-amber-600 cursor-pointer h-2 bg-slate-200 rounded-lg"
            />

            <div className="flex flex-wrap justify-between items-center text-[10px] text-slate-400 font-medium gap-1">
              <span>{t('calculator.interestFree', '0% (Interest-Free)')}</span>
              <span className="text-center truncate max-w-[180px]">
                {hasFixedRate
                  ? t('calculator.officialSchemeRate', 'Official: {{rate}}% p.a.', { rate: officialRate })
                  : t('calculator.asDeterminedLender', 'As determined by institution')}
              </span>
              <span>18%</span>
            </div>
          </div>

          {/* Repayment Tenure */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                {hasFixedTenure ? t('calculator.loanTenure', 'Repayment Tenure') : t('calculator.simulateTenure', 'Simulate Repayment Tenure')}
              </label>
              <span className="text-sm font-extrabold text-slate-800 font-mono bg-slate-100 px-2.5 py-0.5 rounded-lg border border-slate-200">
                {tenureMonths} {t('calculator.months', 'Months')} ({(tenureMonths / 12).toFixed(1)} {t('calculator.years', 'Yrs')})
              </span>
            </div>

            <input
              type="range"
              min="6"
              max={Math.max(officialTenureMonths, 120)}
              step="6"
              value={tenureMonths}
              onChange={(e) => setTenureMonths(Number(e.target.value))}
              className="w-full accent-indigo-600 cursor-pointer h-2 bg-slate-200 rounded-lg"
            />

            <div className="flex flex-wrap justify-between items-center text-[10px] text-slate-400 font-medium gap-1">
              <span>6 {t('calculator.months', 'Mo.')}</span>
              <span className="text-center truncate max-w-[180px]">
                {hasFixedTenure
                  ? `Official: ${officialTenureMonths} Mo.`
                  : t('calculator.asDeterminedLender', 'As per guidelines')}
              </span>
              <span>{Math.max(officialTenureMonths, 120)} {t('calculator.months', 'Mo.')}</span>
            </div>
          </div>
        </div>

        {/* Right Column: Calculation Result Card */}
        <div className="lg:col-span-5 bg-gradient-to-br from-slate-900 via-gov-navy to-slate-900 text-white rounded-2xl p-4 sm:p-6 shadow-xl space-y-5 sm:space-y-6 flex flex-col justify-between">
          <div className="space-y-4">
            <span className="text-[10px] font-extrabold text-gov-saffron uppercase tracking-widest bg-slate-800 px-2.5 py-1 rounded">
              {t('calculator.monthlyEmi', 'ESTIMATED MONTHLY INSTALLMENT')}
            </span>

            <div>
              <div className="text-3xl sm:text-4xl font-extrabold font-mono text-emerald-400">
                ₹{calculation.emi.toLocaleString('en-IN')}
              </div>
              <span className="text-slate-400 text-xs font-medium">
                {t('calculator.payableMonthly', 'Payable monthly for {{count}} installments', { count: tenureMonths })}
              </span>
            </div>

            <div className="border-t border-slate-800 pt-4 space-y-2.5 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">{t('calculator.principalAmount', 'Principal Loan Amount')}</span>
                <span className="font-mono font-bold">{formatCurrency(loanAmount)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">{t('calculator.totalInterestPayable', 'Total Interest Payable')}</span>
                <span className="font-mono font-bold text-amber-400">+{formatCurrency(calculation.totalInterest)}</span>
              </div>
              {scheme.subsidy_percentage && (
                <div className="flex justify-between items-center text-emerald-400 font-bold">
                  <span>{t('calculator.estimatedGovtSubsidy', 'Estimated Govt Subsidy')} ({scheme.subsidy_percentage}%)</span>
                  <span className="font-mono">-{formatCurrency((loanAmount * scheme.subsidy_percentage) / 100)}</span>
                </div>
              )}
              <div className="flex justify-between items-center border-t border-slate-800 pt-2 text-sm font-bold text-white">
                <span>{t('calculator.totalRepayment', 'Total Amount Payable')}</span>
                <span className="font-mono text-emerald-400">{formatCurrency(calculation.totalRepayment)}</span>
              </div>
            </div>

            {/* Split Bar */}
            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between text-[10px] text-slate-400 font-bold">
                <span>{t('calculator.principalAmount', 'Principal')} ({calculation.principalPct}%)</span>
                <span>{t('calculator.totalInterest', 'Interest')} ({calculation.interestPct}%)</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden flex">
                <div style={{ width: `${calculation.principalPct}%` }} className="bg-emerald-500 h-full" />
                <div style={{ width: `${calculation.interestPct}%` }} className="bg-amber-500 h-full" />
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setShowAmortization(!showAmortization)}
            className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold py-2.5 rounded-xl border border-slate-700 transition flex items-center justify-center gap-1.5"
          >
            {showAmortization ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            {showAmortization ? t('calculator.hideAmortization', 'Hide Amortization Schedule') : t('calculator.viewAmortization', 'View Full Amortization Schedule')}
          </button>
        </div>
      </div>

      {/* Expandable Amortization Schedule */}
      {showAmortization && (
        <div className="mt-6 border-t border-slate-200 pt-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-sky-600" /> {t('calculator.amortizationSchedule', 'Complete Repayment Schedule')}
            </h3>
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
              <button
                type="button"
                onClick={() => setScheduleMode('YEARLY')}
                className={`px-3 py-1 rounded-lg font-bold transition ${
                  scheduleMode === 'YEARLY' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {t('calculator.yearlySummary', 'Yearly Summary')}
              </button>
              <button
                type="button"
                onClick={() => setScheduleMode('MONTHLY')}
                className={`px-3 py-1 rounded-lg font-bold transition ${
                  scheduleMode === 'MONTHLY' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {t('calculator.monthlyView', 'Monthly Breakdown')}
              </button>
            </div>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-200 max-h-72 overflow-y-auto">
            <table className="w-full text-left text-xs min-w-[520px]">
              <thead className="bg-slate-50 text-slate-600 font-bold uppercase text-[10px] sticky top-0 border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">{scheduleMode === 'YEARLY' ? t('calculator.year', 'Period') : t('calculator.month', 'Period')}</th>
                  <th className="py-2.5 px-3">{t('calculator.openingBalance', 'Opening Principal')}</th>
                  <th className="py-2.5 px-3">{t('calculator.principalPaid', 'Principal Component')}</th>
                  <th className="py-2.5 px-3">{t('calculator.interestPaid', 'Interest Component')}</th>
                  <th className="py-2.5 px-3">{t('calculator.emiInstallment', 'Installment Paid')}</th>
                  <th className="py-2.5 px-3">{t('calculator.closingBalance', 'Closing Balance')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                {scheduleMode === 'YEARLY'
                  ? calculation.yearlySchedule.map((row) => (
                      <tr key={row.year} className="hover:bg-slate-50">
                        <td className="py-2 px-3 font-sans font-bold text-slate-900">{t('calculator.year', 'Year')} {row.year}</td>
                        <td className="py-2 px-3">{formatCurrency(row.opening)}</td>
                        <td className="py-2 px-3 text-emerald-700 font-bold">{formatCurrency(row.principal)}</td>
                        <td className="py-2 px-3 text-amber-700 font-bold">{formatCurrency(row.interest)}</td>
                        <td className="py-2 px-3 font-bold text-slate-900">{formatCurrency(row.total)}</td>
                        <td className="py-2 px-3 font-bold">{formatCurrency(row.closing)}</td>
                      </tr>
                    ))
                  : calculation.schedule.map((row) => (
                      <tr key={row.month} className="hover:bg-slate-50">
                        <td className="py-1.5 px-3 font-sans font-medium text-slate-700">{t('calculator.month', 'Month')} {row.month}</td>
                        <td className="py-1.5 px-3">{formatCurrency(row.opening)}</td>
                        <td className="py-1.5 px-3 text-emerald-700">{formatCurrency(row.principal)}</td>
                        <td className="py-1.5 px-3 text-amber-700">{formatCurrency(row.interest)}</td>
                        <td className="py-1.5 px-3 font-bold text-slate-900">{formatCurrency(row.installment)}</td>
                        <td className="py-1.5 px-3">{formatCurrency(row.closing)}</td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
