import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { schemeApi } from '../api/schemeApi';
import { financialApi } from '../api/financialApi';
import { Scheme, FinancialCalculationResult, AmortizationEntry } from '../types';
import { Alert } from '../components/Alert';
import { formatCurrency, formatPercent } from '../utils/formatters';
import {
  Calculator as CalcIcon,
  ShieldCheck,
  Table,
  Info,
  RotateCcw,
  Percent,
  Calendar,
  IndianRupee,
  PieChart,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  Sparkles,
  Award
} from 'lucide-react';

export const CalculatorPage: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const defaultSchemeParam = searchParams.get('scheme') || '';

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [selectedSchemeId, setSelectedSchemeId] = useState<string>(defaultSchemeParam);

  // Core Financial Inputs
  const [loanAmount, setLoanAmount] = useState<number>(100000);
  const [annualInterestRate, setAnnualInterestRate] = useState<number>(7.0);
  const [tenureValue, setTenureValue] = useState<number>(3);
  const [tenureUnit, setTenureUnit] = useState<'YEARS' | 'MONTHS'>('YEARS');
  const [projectCost, setProjectCost] = useState<number>(120000);

  // UI state
  const [showFullSchedule, setShowFullSchedule] = useState<boolean>(false);
  const [scheduleViewMode, setScheduleViewMode] = useState<'MONTHLY' | 'YEARLY'>('MONTHLY');
  const [backendResult, setBackendResult] = useState<FinancialCalculationResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Load scheme list
  useEffect(() => {
    schemeApi.getSchemes({ page_size: 100 })
      .then((data) => {
        setSchemes(data.items || []);
      })
      .catch((err) => {
        console.error('Failed to load schemes list for calculator:', err);
      });
  }, []);

  // Update URL and prefill scheme values when selectedSchemeId changes
  useEffect(() => {
    if (!selectedSchemeId) return;

    const matched = schemes.find((s) => s.scheme_id === selectedSchemeId);
    if (matched) {
      // Auto-fill official scheme defaults if available
      if (matched.interest_rate !== undefined && matched.interest_rate !== null && matched.interest_rate >= 0) {
        setAnnualInterestRate(Number(matched.interest_rate));
      } else if (matched.interest_rate_min !== undefined && matched.interest_rate_min !== null) {
        setAnnualInterestRate(Number(matched.interest_rate_min));
      }

      if (matched.max_loan_amount && matched.max_loan_amount > 0) {
        const defaultLoan = Math.min(loanAmount, Number(matched.max_loan_amount));
        setLoanAmount(defaultLoan > 0 ? defaultLoan : 100000);
      }

      if (matched.repayment_period_months && matched.repayment_period_months > 0) {
        if (tenureUnit === 'YEARS') {
          setTenureValue(Math.max(1, Math.round(Number(matched.repayment_period_months) / 12)));
        } else {
          setTenureValue(Number(matched.repayment_period_months));
        }
      }
    }
  }, [selectedSchemeId, schemes]);

  // Total tenure in months
  const totalMonths = useMemo(() => {
    const rawMonths = tenureUnit === 'YEARS' ? tenureValue * 12 : tenureValue;
    return Math.max(1, Math.min(rawMonths, 360));
  }, [tenureValue, tenureUnit]);

  // Pure mathematical reducing-balance EMI calculation
  const calculatedData = useMemo(() => {
    const P = Math.max(0, Number(loanAmount) || 0);
    const R = Math.max(0, Number(annualInterestRate) || 0);
    const N = totalMonths;

    if (P <= 0 || N <= 0) {
      return {
        emi: 0,
        totalInterest: 0,
        totalRepayment: 0,
        principalPercent: 100,
        interestPercent: 0,
        schedule: [] as AmortizationEntry[],
        yearlySchedule: [] as any[],
        isValid: false,
      };
    }

    let emi = 0;
    let totalInterest = 0;
    const schedule: AmortizationEntry[] = [];

    if (R === 0) {
      // 0% Interest (Zero-interest loan)
      emi = Math.round((P / N) * 100) / 100;
      totalInterest = 0;
      let balance = P;

      for (let m = 1; m <= N; m++) {
        const principalComponent = m === N ? balance : Math.min(balance, emi);
        const closingBalance = Math.max(0, Math.round((balance - principalComponent) * 100) / 100);
        schedule.push({
          installment_number: m,
          period_label: `Month ${m}`,
          opening_principal: Math.round(balance * 100) / 100,
          installment_amount: Math.round(principalComponent * 100) / 100,
          principal_component: Math.round(principalComponent * 100) / 100,
          interest_component: 0,
          closing_principal: closingBalance,
        });
        balance = closingBalance;
      }
    } else {
      // Standard reducing balance formula: EMI = P * r * (1+r)^N / ((1+r)^N - 1)
      const r = R / (12 * 100);
      const onePlusR_N = Math.pow(1 + r, N);
      emi = Math.round((P * r * onePlusR_N / (onePlusR_N - 1)) * 100) / 100;

      let balance = P;
      for (let m = 1; m <= N; m++) {
        const opening = balance;
        const interest = Math.round(opening * r * 100) / 100;
        let principalComp: number;
        let installmentAmount: number;

        if (m === N) {
          // Last installment: exact reconciliation
          principalComp = opening;
          installmentAmount = Math.round((principalComp + interest) * 100) / 100;
          balance = 0;
        } else {
          principalComp = Math.round((emi - interest) * 100) / 100;
          installmentAmount = emi;
          balance = Math.max(0, Math.round((opening - principalComp) * 100) / 100);
        }

        totalInterest += interest;

        schedule.push({
          installment_number: m,
          period_label: `Month ${m}`,
          opening_principal: opening,
          installment_amount: installmentAmount,
          principal_component: principalComp,
          interest_component: interest,
          closing_principal: balance,
        });
      }
      totalInterest = Math.round(totalInterest * 100) / 100;
    }

    const totalRepayment = Math.round((P + totalInterest) * 100) / 100;
    const principalPercent = totalRepayment > 0 ? Math.round((P / totalRepayment) * 1000) / 10 : 100;
    const interestPercent = totalRepayment > 0 ? Math.round((totalInterest / totalRepayment) * 1000) / 10 : 0;

    // Aggregate Yearly Schedule
    const yearlySchedule: any[] = [];
    let currentYear = 1;
    let yrPrincipal = 0;
    let yrInterest = 0;
    let yrOpening = P;

    schedule.forEach((entry, idx) => {
      yrPrincipal += entry.principal_component || 0;
      yrInterest += entry.interest_component || 0;

      if ((idx + 1) % 12 === 0 || idx === schedule.length - 1) {
        yearlySchedule.push({
          year: currentYear,
          opening_principal: yrOpening,
          principal_paid: Math.round(yrPrincipal * 100) / 100,
          interest_paid: Math.round(yrInterest * 100) / 100,
          total_installment: Math.round((yrPrincipal + yrInterest) * 100) / 100,
          closing_principal: entry.closing_principal || 0,
        });
        currentYear += 1;
        yrPrincipal = 0;
        yrInterest = 0;
        yrOpening = entry.closing_principal || 0;
      }
    });

    return {
      emi,
      totalInterest,
      totalRepayment,
      principalPercent,
      interestPercent,
      schedule,
      yearlySchedule,
      isValid: true,
    };
  }, [loanAmount, annualInterestRate, totalMonths]);

  // Optional backend verification call for scheme-specific rules
  useEffect(() => {
    if (!selectedSchemeId) {
      setBackendResult(null);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setIsLoading(true);
        const res = await financialApi.calculate({
          scheme_id: selectedSchemeId,
          requested_loan_amount: loanAmount,
          project_cost: projectCost || loanAmount * 1.15,
          repayment_period_months: totalMonths,
          interest_rate: annualInterestRate,
        });
        setBackendResult(res);
      } catch (err) {
        // Non-blocking fallback to pure client math
      } finally {
        setIsLoading(false);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [selectedSchemeId, loanAmount, projectCost, totalMonths, annualInterestRate]);

  // Handle Input Changes with Safety Guards
  const handleLoanChange = (val: number) => {
    const clean = isNaN(val) ? 0 : Math.max(0, val);
    setLoanAmount(clean);
    if (projectCost < clean) setProjectCost(Math.round(clean * 1.15));
    if (clean <= 0) {
      setValidationError(t('calculator.positiveLoanWarning', 'Please enter a positive loan amount.'));
    } else {
      setValidationError(null);
    }
  };

  const handleRateChange = (val: number) => {
    const clean = isNaN(val) ? 0 : Math.max(0, Math.min(val, 50));
    setAnnualInterestRate(clean);
  };

  const handleTenureChange = (val: number) => {
    const clean = isNaN(val) ? 1 : Math.max(1, val);
    setTenureValue(clean);
  };

  const handleReset = () => {
    setSelectedSchemeId(defaultSchemeParam || '');
    setLoanAmount(100000);
    setAnnualInterestRate(7.0);
    setTenureValue(3);
    setTenureUnit('YEARS');
    setProjectCost(120000);
    setValidationError(null);
  };

  const selectedScheme = schemes.find((s) => s.scheme_id === selectedSchemeId);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-gov-navy via-slate-900 to-sky-950 text-white p-6 sm:p-8 rounded-3xl shadow-xl border border-slate-700 relative overflow-hidden">
        <div className="relative z-10 max-w-3xl space-y-2">
          <div className="inline-flex items-center gap-2 bg-sky-500/20 text-sky-300 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border border-sky-500/30">
            <CalcIcon className="w-3.5 h-3.5" />
            {t('calculator.title', 'Financial Amortization & Subsidy Calculator')}
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
            {t('calculator.pageTitle', 'Loan EMI, Interest & Subsidy Calculator')}
          </h1>
          <p className="text-slate-300 text-xs sm:text-sm leading-relaxed">
            {t('calculator.pageSubtitle', 'Compute mathematically exact reducing-balance EMIs, total interest burden, and government subsidy benefits across all official loan and credit schemes.')}
          </p>
        </div>
      </div>

      {validationError && <Alert type="warning">{validationError}</Alert>}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* LEFT COLUMN: Input Form Controls (5 cols) */}
        <div className="lg:col-span-5 bg-white p-6 sm:p-7 rounded-3xl border border-slate-200 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <IndianRupee className="w-4 h-4 text-sky-600" />
              {t('calculator.financingParameters', 'Financing Parameters')}
            </h2>
            <button
              onClick={handleReset}
              className="text-xs text-slate-500 hover:text-slate-900 font-semibold flex items-center gap-1 transition"
              title={t('calculator.resetTitle', 'Reset to default parameters')}
            >
              <RotateCcw className="w-3.5 h-3.5" /> {t('calculator.reset', 'Reset')}
            </button>
          </div>

          <div className="space-y-5">
            {/* Scheme Selector */}
            <div>
              <label htmlFor="scheme-select" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                {t('calculator.targetScheme', 'Target Government Scheme (Optional)')}
              </label>
              <select
                id="scheme-select"
                value={selectedSchemeId}
                onChange={(e) => {
                  setSelectedSchemeId(e.target.value);
                  if (e.target.value) {
                    setSearchParams({ scheme: e.target.value });
                  } else {
                    setSearchParams({});
                  }
                }}
                className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-2 focus:ring-sky-500 outline-none bg-white font-semibold text-slate-800"
              >
                <option value="">{t('calculator.standardGeneralLoan', 'Standard General Loan (Custom Parameters)')}</option>
                {schemes.map((s) => (
                  <option key={s.scheme_id} value={s.scheme_id}>
                    {s.scheme_name} ({s.scheme_id})
                  </option>
                ))}
              </select>

              {selectedScheme && (
                <div
                  className={`mt-2 rounded-xl p-3 border text-xs flex items-start gap-2.5 ${
                    selectedScheme.is_credit_scheme === false
                      ? 'bg-amber-50 border-amber-200 text-amber-950'
                      : 'bg-sky-50 border-sky-100 text-sky-900'
                  }`}
                >
                  {selectedScheme.is_credit_scheme === false ? (
                    <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  ) : (
                    <Award className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
                  )}
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold">{selectedScheme.scheme_name}</span>
                      <span
                        className={`text-[9px] font-extrabold px-2 py-0.5 rounded uppercase ${
                          selectedScheme.is_credit_scheme === false
                            ? 'bg-amber-200 text-amber-900'
                            : 'bg-sky-200 text-sky-900'
                        }`}
                      >
                        {(selectedScheme.financial_category || (selectedScheme.is_credit_scheme ? 'LOAN_CREDIT' : 'GRANT_SUBSIDY')).replace(/_/g, ' ')}
                      </span>
                    </div>
                    {selectedScheme.is_credit_scheme === false ? (
                      <p className="text-amber-900 text-[11px] leading-relaxed">
                        {t('calculator.nonCreditNotice', 'Notice: Loan / EMI calculation is not applicable for this scheme. Assistance is provided as a subsidy, grant, or direct welfare benefit. Calculations below simulate general reference borrowing scenarios. To review official guidelines,')}{' '}
                        <Link to={`/schemes/${selectedScheme.scheme_id}`} className="underline font-bold hover:text-amber-950">
                          {t('calculator.viewSchemeDetails', 'view scheme details')}
                        </Link>.
                      </p>
                    ) : (
                      <div className="text-slate-600 text-[10px] space-y-0.5">
                        <p>
                          {selectedScheme.ministry || 'Government of India'} • {selectedScheme.max_loan_amount ? `${t('calculator.maxLimit', 'Max Limit: {{amount}}', { amount: formatCurrency(selectedScheme.max_loan_amount) })}` : t('calculator.maxLimitAppraisal', 'Maximum amount: As per appraisal / not specified in available official guidelines')}
                        </p>
                        <p>
                          {selectedScheme.interest_rate !== undefined && selectedScheme.interest_rate !== null ? t('calculator.officialSchemeRate', 'Official Scheme Rate: {{rate}}% p.a.', { rate: selectedScheme.interest_rate }) : t('calculator.asDeterminedLender', 'Interest rate: As determined by the financing institution / not specified in available official scheme guidelines.')}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Principal / Loan Amount Input */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label htmlFor="loan-amount-input" className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  {t('calculator.loanAmountPrincipal', 'Loan Amount (Principal)')}
                </label>
                <span className="text-sm font-extrabold text-gov-navy font-mono bg-sky-50 px-2.5 py-0.5 rounded-lg border border-sky-100">
                  {formatCurrency(loanAmount)}
                </span>
              </div>
              <div className="relative">
                <span className="absolute left-3.5 top-2.5 text-slate-400 font-bold text-xs">₹</span>
                <input
                  id="loan-amount-input"
                  type="number"
                  min="5000"
                  max="100000000"
                  step="5000"
                  value={loanAmount || ''}
                  onChange={(e) => handleLoanChange(Number(e.target.value))}
                  className="w-full pl-8 pr-4 py-2.5 text-xs font-bold rounded-xl border border-slate-300 focus:ring-2 focus:ring-sky-500 outline-none"
                  placeholder={t('calculator.enterLoanAmount', 'Enter loan amount')}
                  aria-label={t('calculator.loanAmountPrincipal', 'Loan Amount (Principal)')}
                />
              </div>

              {/* Slider */}
              <input
                type="range"
                min="10000"
                max="5000000"
                step="10000"
                value={Math.min(loanAmount, 5000000)}
                onChange={(e) => handleLoanChange(Number(e.target.value))}
                className="w-full accent-sky-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg"
                aria-label={t('calculator.loanAmountSlider', 'Loan Amount Slider')}
              />

              {/* Quick Preset Chips */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {[50000, 100000, 500000, 1000000, 2500000].map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => handleLoanChange(preset)}
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-lg border transition ${
                      loanAmount === preset
                        ? 'bg-sky-600 text-white border-sky-600'
                        : 'bg-slate-50 text-slate-700 hover:bg-slate-100 border-slate-200'
                    }`}
                  >
                    {formatCurrency(preset)}
                  </button>
                ))}
              </div>
            </div>

            {/* Annual Interest Rate (%) Input */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label htmlFor="interest-rate-input" className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  {t('calculator.annualInterestRate', 'Annual Interest Rate (% p.a.)')}
                </label>
                <span className="text-sm font-extrabold text-amber-700 font-mono bg-amber-50 px-2.5 py-0.5 rounded-lg border border-amber-100">
                  {annualInterestRate}% p.a.
                </span>
              </div>
              <div className="relative">
                <input
                  id="interest-rate-input"
                  type="number"
                  min="0"
                  max="40"
                  step="0.1"
                  value={annualInterestRate}
                  onChange={(e) => handleRateChange(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 text-xs font-bold rounded-xl border border-slate-300 focus:ring-2 focus:ring-sky-500 outline-none"
                  placeholder="e.g. 7.0"
                  aria-label={t('calculator.annualInterestRate', 'Annual Interest Rate (% p.a.)')}
                />
                <span className="absolute right-3.5 top-2.5 text-slate-400 font-bold text-xs">%</span>
              </div>

              {/* Slider */}
              <input
                type="range"
                min="0"
                max="24"
                step="0.25"
                value={annualInterestRate}
                onChange={(e) => handleRateChange(Number(e.target.value))}
                className="w-full accent-amber-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg"
                aria-label={t('calculator.interestRateSlider', 'Interest Rate Slider')}
              />

              {/* Quick Rate Presets */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {[
                  { label: t('calculator.interestFree', '0% Interest-Free'), rate: 0 },
                  { label: t('calculator.concessional', '4% Concessional'), rate: 4 },
                  { label: t('calculator.mudraPmegp', '7% MUDRA/PMEGP'), rate: 7 },
                  { label: t('calculator.bankBase', '9.5% Bank Base'), rate: 9.5 },
                  { label: t('calculator.commercial', '12% Commercial'), rate: 12 },
                ].map((item) => (
                  <button
                    key={item.rate}
                    type="button"
                    onClick={() => handleRateChange(item.rate)}
                    className={`text-[10px] font-bold px-2 py-1 rounded-lg border transition ${
                      annualInterestRate === item.rate
                        ? 'bg-amber-600 text-white border-amber-600'
                        : 'bg-slate-50 text-slate-700 hover:bg-slate-100 border-slate-200'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Loan Tenure (Years / Months) Input */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label htmlFor="tenure-input" className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  {t('calculator.loanTenure', 'Loan Tenure')}
                </label>
                <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-[10px] font-bold">
                  <button
                    type="button"
                    onClick={() => {
                      if (tenureUnit === 'MONTHS') {
                        setTenureValue(Math.max(1, Math.round(tenureValue / 12)));
                        setTenureUnit('YEARS');
                      }
                    }}
                    className={`px-2 py-1 rounded-md transition ${
                      tenureUnit === 'YEARS' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'
                    }`}
                  >
                    {t('calculator.years', 'Years')}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (tenureUnit === 'YEARS') {
                        setTenureValue(tenureValue * 12);
                        setTenureUnit('MONTHS');
                      }
                    }}
                    className={`px-2 py-1 rounded-md transition ${
                      tenureUnit === 'MONTHS' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'
                    }`}
                  >
                    {t('calculator.months', 'Months')}
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  id="tenure-input"
                  type="number"
                  min="1"
                  max={tenureUnit === 'YEARS' ? 30 : 360}
                  step="1"
                  value={tenureValue}
                  onChange={(e) => handleTenureChange(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 text-xs font-bold rounded-xl border border-slate-300 focus:ring-2 focus:ring-sky-500 outline-none"
                  aria-label={t('calculator.loanTenure', 'Loan Tenure')}
                />
                <span className="text-xs font-bold text-slate-600 whitespace-nowrap bg-slate-100 px-3 py-2.5 rounded-xl border border-slate-200">
                  {tenureUnit === 'YEARS' ? `${tenureValue * 12} ${t('calculator.months', 'Months')}` : `${(tenureValue / 12).toFixed(1)} ${t('calculator.years', 'Years')}`}
                </span>
              </div>

              {/* Slider */}
              <input
                type="range"
                min="1"
                max={tenureUnit === 'YEARS' ? 30 : 360}
                step="1"
                value={tenureValue}
                onChange={(e) => handleTenureChange(Number(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg"
                aria-label={t('calculator.tenureSlider', 'Tenure Slider')}
              />

              {/* Quick Tenure Presets */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {[1, 3, 5, 7, 10].map((yr) => {
                  const val = tenureUnit === 'YEARS' ? yr : yr * 12;
                  return (
                    <button
                      key={yr}
                      type="button"
                      onClick={() => handleTenureChange(val)}
                      className={`text-[10px] font-bold px-2.5 py-1 rounded-lg border transition ${
                        tenureValue === val
                          ? 'bg-indigo-600 text-white border-indigo-600'
                          : 'bg-slate-50 text-slate-700 hover:bg-slate-100 border-slate-200'
                      }`}
                    >
                      {yr} {yr === 1 ? t('calculator.year', 'Year') : t('calculator.years', 'Years')}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Mathematical Integrity Badge */}
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 text-xs text-slate-600 space-y-1.5">
            <div className="flex items-center gap-1.5 font-bold text-slate-900 text-xs">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              {t('calculator.formulaBadge', 'Standard Reducing Balance EMI Formula')}
            </div>
            <p className="text-[11px] text-slate-500 font-mono">
              EMI = P × r × (1+r)ⁿ / ((1+r)ⁿ - 1)
            </p>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              {t('calculator.formulaDesc', 'Where P = Principal, r = Monthly Rate (Annual% / 1200), and n = Total Months.')}
            </p>
          </div>
        </div>

        {/* RIGHT COLUMN: Results Dashboard & Amortization (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Main Output KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Monthly EMI */}
            <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm relative overflow-hidden space-y-1.5">
              <div className="flex items-center justify-between text-[11px] font-extrabold text-slate-500 uppercase tracking-wider">
                <span>{t('calculator.monthlyEmi', 'Monthly EMI')}</span>
                <span className="w-2 h-2 rounded-full bg-gov-saffron animate-pulse" />
              </div>
              <div className="text-2xl sm:text-3xl font-black text-gov-navy tracking-tight font-mono">
                {formatCurrency(calculatedData.emi)}
              </div>
              <p className="text-[10px] text-slate-400 font-medium">
                {t('calculator.payableMonthly', 'Payable monthly for {{count}} installments', { count: totalMonths })}
              </p>
            </div>

            {/* Total Interest Payable */}
            <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-1.5">
              <div className="text-[11px] font-extrabold text-slate-500 uppercase tracking-wider">
                {t('calculator.totalInterest', 'Total Interest')}
              </div>
              <div className="text-2xl sm:text-3xl font-black text-amber-600 tracking-tight font-mono">
                {formatCurrency(calculatedData.totalInterest)}
              </div>
              <p className="text-[10px] text-slate-400 font-medium">
                {t('calculator.percentOfTotal', '{{percent}}% of total payment', { percent: calculatedData.interestPercent })}
              </p>
            </div>

            {/* Total Repayment */}
            <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-1.5">
              <div className="text-[11px] font-extrabold text-slate-500 uppercase tracking-wider">
                {t('calculator.totalRepayment', 'Total Repayment')}
              </div>
              <div className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight font-mono">
                {formatCurrency(calculatedData.totalRepayment)}
              </div>
              <p className="text-[10px] text-slate-400 font-medium">
                {t('calculator.principalPlusInterest', 'Principal + Total Interest')}
              </p>
            </div>
          </div>

          {/* Breakdown Segmented Bar */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <PieChart className="w-4 h-4 text-sky-600" />
                {t('calculator.breakdownTitle', 'Principal vs Interest Breakdown')}
              </h3>
              <span className="text-xs font-bold text-slate-600 font-mono">
                {t('calculator.total', 'Total')}: {formatCurrency(calculatedData.totalRepayment)}
              </span>
            </div>

            {/* Segmented Visual Progress Bar */}
            <div className="w-full h-4 bg-slate-100 rounded-full overflow-hidden flex shadow-inner">
              <div
                style={{ width: `${calculatedData.principalPercent}%` }}
                className="bg-sky-600 h-full transition-all duration-300"
                title={`Principal: ${calculatedData.principalPercent}%`}
              />
              <div
                style={{ width: `${calculatedData.interestPercent}%` }}
                className="bg-amber-500 h-full transition-all duration-300"
                title={`Interest: ${calculatedData.interestPercent}%`}
              />
            </div>

            {/* Legend */}
            <div className="grid grid-cols-2 gap-4 text-xs pt-1">
              <div className="flex items-center gap-2 bg-sky-50/70 p-3 rounded-2xl border border-sky-100">
                <div className="w-3.5 h-3.5 bg-sky-600 rounded-md shrink-0" />
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase block">{t('calculator.principalAmount', 'Principal Amount')}</span>
                  <span className="font-extrabold text-slate-900 font-mono text-sm">
                    {formatCurrency(loanAmount)} ({calculatedData.principalPercent}%)
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 bg-amber-50/70 p-3 rounded-2xl border border-amber-100">
                <div className="w-3.5 h-3.5 bg-amber-500 rounded-md shrink-0" />
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase block">{t('calculator.totalInterest', 'Total Interest')}</span>
                  <span className="font-extrabold text-amber-700 font-mono text-sm">
                    {formatCurrency(calculatedData.totalInterest)} ({calculatedData.interestPercent}%)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Government Subsidy & Scheme Financial Insights (if Scheme Selected) */}
          {backendResult && (backendResult.subsidy_amount || backendResult.beneficiary_contribution_amount) && (
            <div className="bg-gradient-to-r from-emerald-950 via-slate-900 to-sky-950 text-white p-6 rounded-3xl border border-emerald-700/50 shadow-md space-y-3">
              <div className="flex items-center justify-between">
                <div className="inline-flex items-center gap-2 bg-emerald-500/20 text-emerald-300 text-xs font-bold px-3 py-1 rounded-full border border-emerald-500/30">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                  {t('calculator.subsidyInsights', 'Official Scheme Subsidy & Benefit Details')}
                </div>
                {selectedScheme && (
                  <Link
                    to={`/schemes/${selectedScheme.scheme_id}`}
                    className="text-xs text-sky-300 hover:text-white font-bold flex items-center gap-1 transition"
                  >
                    {t('calculator.viewSchemeRules', 'View Scheme Rules')} <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs pt-1">
                {backendResult.subsidy_amount !== undefined && backendResult.subsidy_amount !== null && (
                  <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-bold block">{t('calculator.estimatedGovtSubsidy', 'Estimated Govt Subsidy')}</span>
                    <span className="text-lg font-black text-emerald-400 font-mono mt-0.5 block">
                      {formatCurrency(backendResult.subsidy_amount)}
                    </span>
                  </div>
                )}
                {backendResult.beneficiary_contribution_amount !== undefined && backendResult.beneficiary_contribution_amount !== null && (
                  <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-bold block">{t('calculator.applicantContribution', 'Applicant Contribution')}</span>
                    <span className="text-lg font-black text-indigo-300 font-mono mt-0.5 block">
                      {formatCurrency(backendResult.beneficiary_contribution_amount)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Amortization Schedule Table */}
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden space-y-4">
            <div className="p-6 pb-0 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div>
                <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                  <Table className="w-4 h-4 text-sky-600" />
                  {t('calculator.amortizationSchedule', 'Loan Amortization Schedule')}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {t('calculator.amortizationSubtitle', 'Complete breakdown of principal reduction and interest deduction over tenure.')}
                </p>
              </div>

              {/* Monthly vs Yearly View Toggle */}
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-bold">
                <button
                  type="button"
                  onClick={() => setScheduleViewMode('MONTHLY')}
                  className={`px-3 py-1 rounded-lg transition ${
                    scheduleViewMode === 'MONTHLY' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  {t('calculator.monthlyView', 'Monthly View')}
                </button>
                <button
                  type="button"
                  onClick={() => setScheduleViewMode('YEARLY')}
                  className={`px-3 py-1 rounded-lg transition ${
                    scheduleViewMode === 'YEARLY' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  {t('calculator.yearlySummary', 'Yearly Summary')}
                </button>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-medium">
                <thead className="bg-slate-50 text-slate-600 font-bold border-y border-slate-200 uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="py-3 px-4">{scheduleViewMode === 'MONTHLY' ? t('calculator.month', 'Month') : t('calculator.year', 'Year')}</th>
                    <th className="py-3 px-4">{t('calculator.openingBalance', 'Opening Balance')}</th>
                    <th className="py-3 px-4">{t('calculator.emiInstallment', 'EMI Installment')}</th>
                    <th className="py-3 px-4 text-sky-700">{t('calculator.principalPaid', 'Principal Paid')}</th>
                    <th className="py-3 px-4 text-amber-700">{t('calculator.interestPaid', 'Interest Paid')}</th>
                    <th className="py-3 px-4 text-right">{t('calculator.closingBalance', 'Closing Balance')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700 font-mono">
                  {scheduleViewMode === 'MONTHLY' ? (
                    // Monthly rows
                    (showFullSchedule ? calculatedData.schedule : calculatedData.schedule.slice(0, 12)).map((row) => (
                      <tr key={row.installment_number} className="hover:bg-slate-50/80 transition">
                        <td className="py-2.5 px-4 font-bold text-slate-900 font-sans">{t('calculator.month', 'Month')} {row.installment_number}</td>
                        <td className="py-2.5 px-4">{formatCurrency(row.opening_principal)}</td>
                        <td className="py-2.5 px-4 font-bold text-gov-navy">{formatCurrency(row.installment_amount)}</td>
                        <td className="py-2.5 px-4 text-sky-700">{formatCurrency(row.principal_component)}</td>
                        <td className="py-2.5 px-4 text-amber-600">{formatCurrency(row.interest_component)}</td>
                        <td className="py-2.5 px-4 text-right font-bold">{formatCurrency(row.closing_principal)}</td>
                      </tr>
                    ))
                  ) : (
                    // Yearly rows
                    calculatedData.yearlySchedule.map((yr) => (
                      <tr key={yr.year} className="hover:bg-slate-50/80 transition">
                        <td className="py-2.5 px-4 font-bold text-slate-900 font-sans">{t('calculator.year', 'Year')} {yr.year}</td>
                        <td className="py-2.5 px-4">{formatCurrency(yr.opening_principal)}</td>
                        <td className="py-2.5 px-4 font-bold text-gov-navy">{formatCurrency(yr.total_installment)}</td>
                        <td className="py-2.5 px-4 text-sky-700">{formatCurrency(yr.principal_paid)}</td>
                        <td className="py-2.5 px-4 text-amber-600">{formatCurrency(yr.interest_paid)}</td>
                        <td className="py-2.5 px-4 text-right font-bold">{formatCurrency(yr.closing_principal)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Show full schedule button if monthly view and > 12 months */}
            {scheduleViewMode === 'MONTHLY' && calculatedData.schedule.length > 12 && (
              <div className="p-4 bg-slate-50 border-t border-slate-200 text-center">
                <button
                  type="button"
                  onClick={() => setShowFullSchedule(!showFullSchedule)}
                  className="text-xs font-bold text-sky-700 hover:text-sky-900 inline-flex items-center gap-1.5 transition"
                >
                  {showFullSchedule ? (
                    <>
                      {t('calculator.showFirst12Only', 'Show First 12 Months Only')} <ChevronUp className="w-4 h-4" />
                    </>
                  ) : (
                    <>
                      {t('calculator.showFullSchedule', 'Show Full {{count}}-Month Amortization Schedule', { count: totalMonths })} <ChevronDown className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
