import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { schemeApi } from '../api/schemeApi';
import { financialApi } from '../api/financialApi';
import {
  Scheme,
  FinancialCalculationResult,
  AmortizationEntry,
  FinancialHealthResponse,
  FinancialIndicatorResult,
} from '../types';
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
  Award,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  RefreshCw,
  Wallet,
  Scale,
  TrendingUp,
  Coins,
} from 'lucide-react';

export const CalculatorPage: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const defaultSchemeParam = searchParams.get('scheme') || '';

  // Tab State: 'EMI' (Mathematical Amortization) vs 'HEALTH' (Affordability & Debt Service)
  const tabParam = searchParams.get('tab');
  // Read restored history state if available (from Back/Forward navigation)
  const historyState = (typeof window !== 'undefined' && window.history.state?.yojnasetu_calc_state) || null;

  const [activeTab, setActiveTab] = useState<'EMI' | 'HEALTH'>(
    historyState?.activeTab || (tabParam === 'health' ? 'HEALTH' : 'EMI')
  );

  useEffect(() => {
    if (tabParam === 'health') {
      setActiveTab('HEALTH');
    } else if (tabParam === 'emi') {
      setActiveTab('EMI');
    }
  }, [tabParam]);

  const persistCalculatorState = (overrides?: Record<string, any>) => {
    if (typeof window === 'undefined') return;
    const currentSaved = window.history.state?.yojnasetu_calc_state || {};
    const updated = {
      ...currentSaved,
      activeTab,
      selectedSchemeId,
      loanAmount,
      annualInterestRate,
      tenureValue,
      tenureUnit,
      projectCost,
      monthlyIncome,
      monthlyExpenses,
      monthlyObligations,
      healthResult,
      ...overrides,
    };
    window.history.replaceState({ ...window.history.state, yojnasetu_calc_state: updated }, '');
  };

  const handleTabSwitch = (newTab: 'EMI' | 'HEALTH') => {
    setActiveTab(newTab);
    persistCalculatorState({ activeTab: newTab });
    const p = new URLSearchParams(searchParams);
    p.set('tab', newTab === 'HEALTH' ? 'health' : 'emi');
    setSearchParams(p, { replace: true });
  };

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [selectedSchemeId, setSelectedSchemeId] = useState<string>(
    historyState?.selectedSchemeId ?? defaultSchemeParam
  );

  // Core Financial Inputs
  const [loanAmount, setLoanAmount] = useState<number>(() => {
    if (historyState?.loanAmount !== undefined) return historyState.loanAmount;
    const p = searchParams.get('loan');
    return p ? Number(p) : 100000;
  });
  const [annualInterestRate, setAnnualInterestRate] = useState<number>(() => {
    if (historyState?.annualInterestRate !== undefined) return historyState.annualInterestRate;
    const p = searchParams.get('rate');
    return p ? Number(p) : 7.0;
  });
  const [tenureValue, setTenureValue] = useState<number>(() => {
    if (historyState?.tenureValue !== undefined) return historyState.tenureValue;
    const p = searchParams.get('tenure');
    return p ? Number(p) : 3;
  });
  const [tenureUnit, setTenureUnit] = useState<'YEARS' | 'MONTHS'>(() => {
    if (historyState?.tenureUnit !== undefined) return historyState.tenureUnit;
    const p = searchParams.get('unit');
    return p === 'MONTHS' ? 'MONTHS' : 'YEARS';
  });
  const [projectCost, setProjectCost] = useState<number>(() => {
    if (historyState?.projectCost !== undefined) return historyState.projectCost;
    const p = searchParams.get('cost');
    return p ? Number(p) : 120000;
  });

  // Financial Health / Affordability Context Inputs
  const [monthlyIncome, setMonthlyIncome] = useState<number>(() => {
    if (historyState?.monthlyIncome !== undefined) return historyState.monthlyIncome;
    const p = searchParams.get('income');
    return p ? Number(p) : 30000;
  });
  const [monthlyExpenses, setMonthlyExpenses] = useState<number>(() => {
    if (historyState?.monthlyExpenses !== undefined) return historyState.monthlyExpenses;
    const p = searchParams.get('expenses');
    return p ? Number(p) : 18000;
  });
  const [monthlyObligations, setMonthlyObligations] = useState<number>(() => {
    if (historyState?.monthlyObligations !== undefined) return historyState.monthlyObligations;
    const p = searchParams.get('obligations');
    return p ? Number(p) : 3000;
  });

  const [healthResult, setHealthResult] = useState<FinancialHealthResponse | null>(
    historyState?.healthResult ?? null
  );
  const [isHealthLoading, setIsHealthLoading] = useState<boolean>(false);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [healthValidationWarning, setHealthValidationWarning] = useState<string | null>(null);

  // UI state for EMI schedule
  const [showFullSchedule, setShowFullSchedule] = useState<boolean>(false);
  const [scheduleViewMode, setScheduleViewMode] = useState<'MONTHLY' | 'YEARLY'>('MONTHLY');
  const [backendResult, setBackendResult] = useState<FinancialCalculationResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const loanInputRef = useRef<HTMLInputElement>(null);
  const healthLoanInputRef = useRef<HTMLInputElement>(null);

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
          principalComp = balance;
          installmentAmount = Math.round((balance + interest) * 100) / 100;
          balance = 0;
        } else {
          principalComp = Math.round((emi - interest) * 100) / 100;
          balance = Math.max(0, Math.round((balance - principalComp) * 100) / 100);
          installmentAmount = emi;
        }

        totalInterest += interest;
        schedule.push({
          installment_number: m,
          period_label: `Month ${m}`,
          opening_principal: Math.round(opening * 100) / 100,
          installment_amount: installmentAmount,
          principal_component: principalComp,
          interest_component: interest,
          closing_principal: balance,
        });
      }
    }

    const totalRepayment = Math.round((P + totalInterest) * 100) / 100;
    const principalPercent = totalRepayment > 0 ? Math.round((P / totalRepayment) * 100) : 100;
    const interestPercent = totalRepayment > 0 ? Math.round((totalInterest / totalRepayment) * 100) : 0;

    // Aggregate Yearly Schedule for Summary View
    const yearlySchedule: any[] = [];
    let currentYear = 1;
    let yearOpening = P;
    let yearPrincipal = 0;
    let yearInterest = 0;
    let yearTotal = 0;

    schedule.forEach((entry, idx) => {
      yearPrincipal += entry.principal_component || 0;
      yearInterest += entry.interest_component || 0;
      yearTotal += entry.installment_amount || 0;

      if ((idx + 1) % 12 === 0 || idx === schedule.length - 1) {
        yearlySchedule.push({
          year: currentYear,
          opening_principal: Math.round(yearOpening * 100) / 100,
          total_installment: Math.round(yearTotal * 100) / 100,
          principal_paid: Math.round(yearPrincipal * 100) / 100,
          interest_paid: Math.round(yearInterest * 100) / 100,
          closing_principal: entry.closing_principal ?? 0,
        });
        currentYear++;
        yearOpening = entry.closing_principal ?? 0;
        yearPrincipal = 0;
        yearInterest = 0;
        yearTotal = 0;
      }
    });

    return {
      emi,
      totalInterest: Math.round(totalInterest * 100) / 100,
      totalRepayment,
      principalPercent,
      interestPercent,
      schedule,
      yearlySchedule,
      isValid: true,
    };
  }, [loanAmount, annualInterestRate, totalMonths]);

  // Debounced backend scheme calculation (subsidy, margin, etc.)
  useEffect(() => {
    if (!selectedSchemeId) {
      setBackendResult(null);
      return;
    }

    const timer = setTimeout(() => {
      if (loanAmount > 0 && totalMonths > 0) {
        setIsLoading(true);
        financialApi
          .calculate({
            scheme_id: selectedSchemeId,
            requested_loan_amount: loanAmount,
            project_cost: projectCost,
            repayment_period_months: totalMonths,
            interest_rate: annualInterestRate,
          })
          .then((res) => {
            setBackendResult(res);
          })
          .catch((err) => {
            console.warn('Backend scheme subsidy calculation error:', err);
          })
          .finally(() => {
            setIsLoading(false);
          });
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [selectedSchemeId, loanAmount, projectCost, totalMonths, annualInterestRate]);

  // Handle Input Changes with Safety Guards
  const handleLoanChange = (val: number) => {
    const clean = isNaN(val) ? 0 : Math.max(0, val);
    setLoanAmount(clean);
    persistCalculatorState({ loanAmount: clean });
    if (projectCost < clean) {
      const newCost = Math.round(clean * 1.15);
      setProjectCost(newCost);
      persistCalculatorState({ loanAmount: clean, projectCost: newCost });
    }
    if (clean <= 0) {
      setValidationError(t('calculator.positiveLoanWarning', 'Please enter a positive loan amount.'));
    } else {
      setValidationError(null);
    }
  };

  const handleRateChange = (val: number) => {
    const clean = isNaN(val) ? 0 : Math.max(0, Math.min(val, 50));
    setAnnualInterestRate(clean);
    persistCalculatorState({ annualInterestRate: clean });
  };

  const handleTenureChange = (val: number) => {
    const clean = isNaN(val) ? 1 : Math.max(1, val);
    setTenureValue(clean);
    persistCalculatorState({ tenureValue: clean });
  };

  const handleIncomeChange = (val: number) => {
    const clean = isNaN(val) ? 0 : Math.max(0, val);
    setMonthlyIncome(clean);
    persistCalculatorState({ monthlyIncome: clean });
  };

  const handleExpensesChange = (val: number) => {
    const clean = isNaN(val) ? 0 : Math.max(0, val);
    setMonthlyExpenses(clean);
    persistCalculatorState({ monthlyExpenses: clean });
  };

  const handleObligationsChange = (val: number) => {
    const clean = isNaN(val) ? 0 : Math.max(0, val);
    setMonthlyObligations(clean);
    persistCalculatorState({ monthlyObligations: clean });
  };

  const handleReset = () => {
    setSelectedSchemeId(defaultSchemeParam || '');
    setLoanAmount(100000);
    setAnnualInterestRate(7.0);
    setTenureValue(3);
    setTenureUnit('YEARS');
    setProjectCost(120000);
    setHealthResult(null);
    setValidationError(null);
    persistCalculatorState({
      selectedSchemeId: defaultSchemeParam || '',
      loanAmount: 100000,
      annualInterestRate: 7.0,
      tenureValue: 3,
      tenureUnit: 'YEARS',
      projectCost: 120000,
      healthResult: null,
    });
  };

  const selectedScheme = schemes.find((s) => s.scheme_id === selectedSchemeId);

  // Scheme Interest & Tenure Verification Status
  const isSelectedSchemeNonCredit = selectedScheme && selectedScheme.is_credit_scheme === false;
  const isSelectedSchemeRateUnspecified = selectedScheme && selectedScheme.is_credit_scheme !== false && (
    (selectedScheme.interest_rate === null || selectedScheme.interest_rate === undefined) &&
    (selectedScheme.interest_rate_max === null || selectedScheme.interest_rate_max === undefined)
  );

  // Perform Deterministic Financial Health Evaluation
  const handleAssessHealth = async () => {
    setHealthValidationWarning(null);
    setHealthError(null);

    if (isSelectedSchemeNonCredit) {
      setHealthValidationWarning("Loan Affordability is NOT APPLICABLE for this non-credit scheme. Assistance is provided as a direct subsidy or grant with no loan repayment obligations.");
      return;
    }

    if (!monthlyIncome || monthlyIncome <= 0) {
      setHealthValidationWarning("To assess whether this loan fits your finances, please provide your approximate monthly family income.");
      return;
    }

    if (!monthlyExpenses || monthlyExpenses <= 0) {
      setHealthValidationWarning("To assess whether this loan fits your finances, please enter your approximate monthly living and business expenses.");
      return;
    }

    if (!loanAmount || loanAmount <= 0) {
      setHealthValidationWarning("Please enter a valid requested loan amount.");
      return;
    }

    setIsHealthLoading(true);
    try {
      const res = await financialApi.assessFinancialHealth({
        monthly_income: monthlyIncome,
        annual_income: monthlyIncome * 12,
        monthly_expenses: monthlyExpenses,
        monthly_obligations: monthlyObligations || 0,
        requested_loan_amount: loanAmount,
        project_cost: projectCost || Math.round(loanAmount * 1.15),
        profile: {
          monthly_income: monthlyIncome,
          annual_income: monthlyIncome * 12,
          monthly_expenses: monthlyExpenses,
          monthly_obligations: monthlyObligations || 0,
          requested_loan_amount: loanAmount,
          project_cost: projectCost || Math.round(loanAmount * 1.15),
        },
      });
      setHealthResult(res);
      persistCalculatorState({ healthResult: res });
    } catch (err: any) {
      console.warn("Financial health evaluation failed:", err);
      setHealthError(err?.response?.data?.detail || "Could not evaluate financial suitability at this time.");
    } finally {
      setIsHealthLoading(false);
    }
  };

  // Status Badge Helper for Financial Health Card
  const getHealthStatusBadge = (status?: string) => {
    switch (status) {
      case 'HEALTHY':
        return {
          label: '🟢 Comfortable / Healthy',
          headline: 'COMFORTABLE',
          bg: 'bg-emerald-50 text-emerald-800 border-emerald-200',
          indicatorBg: 'bg-emerald-600 text-white',
          icon: CheckCircle2,
          colorText: 'text-emerald-700',
          desc: 'This financing comfortably fits within your cashflow cushion without creating repayment stress.',
        };
      case 'MODERATE':
        return {
          label: '🟡 Manageable / Moderate',
          headline: 'MANAGEABLE',
          bg: 'bg-[#F7AE56]/20 text-[#3B2522] border-[#F7AE56]/40',
          indicatorBg: 'bg-[#F7AE56] text-white',
          icon: ShieldCheck,
          colorText: 'text-[#3B2522]',
          desc: 'This financing is manageable with disciplined budgeting, though disposable cushion is tighter.',
        };
      case 'STRESSED':
      case 'HIGH_RISK':
        return {
          label: '🔴 High Repayment Burden',
          headline: 'HIGH REPAYMENT BURDEN',
          bg: 'bg-[#EA717B]/15 text-[#4A2525] border-[#EA717B]/30',
          indicatorBg: 'bg-[#EA717B] text-white',
          icon: AlertTriangle,
          colorText: 'text-[#4A2525]',
          desc: 'High repayment burden detected. Existing obligations plus this EMI leave insufficient disposable cushion.',
        };
      default:
        return {
          label: '⚪ Insufficient Information',
          headline: 'INCOMPLETE DATA',
          bg: 'bg-[#FFF4EC] text-[#765E59] border-[#E8D8D2]',
          indicatorBg: 'bg-[#765E59] text-white',
          icon: HelpCircle,
          colorText: 'text-[#765E59]',
          desc: 'Please provide monthly income and expenses to evaluate financial affordability.',
        };
    }
  };

  const currentBadge = getHealthStatusBadge(healthResult?.status);
  const StatusBadgeIcon = currentBadge.icon;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white p-6 sm:p-8 rounded-3xl shadow-warm-lg border border-[#E8D8D2]/20 relative overflow-hidden">
        <div className="relative z-10 max-w-3xl space-y-2">
          <div className="inline-flex items-center gap-2 bg-[#FFD0CA]/20 text-[#FFD0CA] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border border-[#FFD0CA]/30">
            <CalcIcon className="w-3.5 h-3.5" />
            <span>{t('calculator.officialGovTools', 'Official Government Financing Tools')}</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-white">
            {activeTab === 'EMI' ? t('calculator.pageTitle', 'Loan EMI, Interest & Subsidy Calculator') : t('calculator.tabAffordability', 'Assess Loan Affordability (Financial Health)')}
          </h1>
          <p className="text-[#FFFBF0]/80 text-xs sm:text-sm leading-relaxed">
            {activeTab === 'EMI'
              ? t('calculator.subtitle', 'Calculate exact loan EMIs, interest rates, and government subsidy estimates using scheme rules.')
              : t('calculator.householdContextDesc', 'Self-declared parameters for deterministic affordability evaluation.')}
          </p>
        </div>
      </div>

      {/* Dual Mode Switcher Tabs */}
      <div className="bg-white p-2 rounded-2xl border border-[#E8D8D2] shadow-warm-xs flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            type="button"
            id="tab-emi-calculator"
            onClick={() => handleTabSwitch('EMI')}
            className={`flex-1 sm:flex-initial px-5 py-3 rounded-xl text-xs font-black flex items-center justify-center gap-2 transition cursor-pointer ${
              activeTab === 'EMI'
                ? 'bg-[#EA717B] text-white shadow-warm-xs'
                : 'text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFF4EC]'
            }`}
          >
            <CalcIcon className="w-4 h-4" />
            <span>{t('calculator.tabEmi', 'EMI Repayment Calculator')}</span>
          </button>

          <button
            type="button"
            id="tab-financial-health"
            onClick={() => handleTabSwitch('HEALTH')}
            className={`flex-1 sm:flex-initial px-5 py-3 rounded-xl text-xs font-black flex items-center justify-center gap-2 transition cursor-pointer ${
              activeTab === 'HEALTH'
                ? 'bg-[#4A2525] text-white shadow-warm-xs'
                : 'text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFF4EC]'
            }`}
          >
            <ShieldCheck className="w-4 h-4 text-[#F7AE56]" />
            <span>{t('calculator.tabAffordability', 'Assess Loan Affordability (Financial Health)')}</span>
          </button>
        </div>

        <div className="text-[11px] text-[#765E59] font-medium px-3 hidden lg:block">
          {activeTab === 'EMI' ? (
            <span className="text-[#EA717B] font-bold">{t('calculator.tabEmi', 'Mathematical Repayment Mode')}</span>
          ) : (
            <span className="text-[#F7AE56] font-bold">{t('calculator.tabAffordability', 'Citizen Affordability Engine Active')}</span>
          )}
        </div>
      </div>

      {validationError && <Alert type="warning">{validationError}</Alert>}
      {healthValidationWarning && <Alert type="warning">{healthValidationWarning}</Alert>}
      {healthError && <Alert type="error">{healthError}</Alert>}

      {/* ─────────────────────────────────────────────────────────────
          VIEW 1: EMI REPAYMENT CALCULATOR
          ───────────────────────────────────────────────────────────── */}
      {activeTab === 'EMI' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* LEFT COLUMN: Input Form Controls (5 cols) */}
          <div className="lg:col-span-5 bg-white p-4 sm:p-6 lg:p-7 rounded-3xl border border-[#E8D8D2] shadow-warm-xs space-y-5 sm:space-y-6">
            <div className="flex items-center justify-between border-b border-[#E8D8D2]/60 pb-3">
              <h2 className="text-sm font-extrabold text-[#3B2522] uppercase tracking-wider flex items-center gap-2">
                <IndianRupee className="w-4 h-4 text-[#EA717B]" />
                {t('calculator.financingParameters', 'Financing Parameters')}
              </h2>
              <button
                onClick={handleReset}
                className="text-xs text-[#765E59] hover:text-[#3B2522] font-semibold flex items-center gap-1 transition cursor-pointer"
                title={t('calculator.resetTitle', 'Reset to default parameters')}
              >
                <RotateCcw className="w-3.5 h-3.5" /> {t('calculator.reset', 'Reset')}
              </button>
            </div>

            <div className="space-y-5">
              {/* Scheme Selector */}
              <div>
                <label htmlFor="scheme-select" className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1.5">
                  {t('calculator.targetScheme', 'Target Government Scheme (Optional)')}
                </label>
                <select
                  id="scheme-select"
                  value={selectedSchemeId}
                  onChange={(e) => {
                    setSelectedSchemeId(e.target.value);
                    const p = new URLSearchParams(searchParams);
                    if (e.target.value) {
                      p.set('scheme', e.target.value);
                    } else {
                      p.delete('scheme');
                    }
                    setSearchParams(p);
                  }}
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-[#E8D8D2] focus:ring-1 focus:ring-[#EA717B] focus:border-[#EA717B] outline-none bg-[#FFFBF0] font-semibold text-[#3B2522]"
                >
                  <option value="">{t('calculator.standardGeneralLoan', 'Standard General Loan (Custom Parameters)')}</option>
                  {schemes.map((s) => (
                    <option key={s.scheme_id} value={s.scheme_id}>
                      {s.scheme_name}
                    </option>
                  ))}
                </select>

                {selectedScheme && (
                  <div
                    className={`mt-2 rounded-xl p-3 border text-xs flex items-start gap-2.5 ${
                      selectedScheme.is_credit_scheme === false
                        ? 'bg-[#FFF4EC] border-[#F7AE56]/40 text-[#3B2522]'
                        : 'bg-[#FFF4EC] border-[#FFD0CA] text-[#3B2522]'
                    }`}
                  >
                    {selectedScheme.is_credit_scheme === false ? (
                      <Info className="w-4 h-4 text-[#F7AE56] shrink-0 mt-0.5" />
                    ) : (
                      <Award className="w-4 h-4 text-[#EA717B] shrink-0 mt-0.5" />
                    )}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold">{selectedScheme.scheme_name}</span>
                        <span
                          className={`text-[9px] font-extrabold px-2 py-0.5 rounded uppercase ${
                            selectedScheme.is_credit_scheme === false
                              ? 'bg-[#FFD0CA]/60 text-[#4A2525]'
                              : 'bg-[#FFD0CA]/60 text-[#4A2525]'
                          }`}
                        >
                          {(selectedScheme.financial_category || (selectedScheme.is_credit_scheme ? 'LOAN_CREDIT' : 'GRANT_SUBSIDY')).replace(/_/g, ' ')}
                        </span>
                      </div>
                      {selectedScheme.is_credit_scheme === false ? (
                        <p className="text-[#765E59] text-[11px] leading-relaxed">
                          Notice: Loan / EMI calculation is not applicable for this scheme. Assistance is provided as a subsidy, grant, or direct welfare benefit.{' '}
                          <Link to={`/schemes/${selectedScheme.scheme_id}`} className="underline font-bold hover:text-[#3B2522]">
                            View scheme details
                          </Link>.
                        </p>
                      ) : (
                        <div className="text-[#765E59] text-[10px] space-y-0.5">
                          <p>
                            {selectedScheme.ministry || 'Government of India'} • {selectedScheme.max_loan_amount ? `Max Limit: ${formatCurrency(selectedScheme.max_loan_amount)}` : 'Maximum amount: As per appraisal'}
                          </p>
                          {isSelectedSchemeRateUnspecified && (
                            <p className="text-[#F7AE56] font-semibold">
                              Note: Applicable interest rate depends on the financing bank and is not fixed by scheme rules.
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Loan Amount Input */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label htmlFor="loan-amount-input" className="text-xs font-bold text-[#3B2522] uppercase tracking-wider">
                    {t('calculator.loanAmount', 'Loan Amount Required (₹)')}
                  </label>
                  <span className="text-sm font-extrabold text-[#4A2525] font-mono bg-[#FFF4EC] px-2.5 py-0.5 rounded-lg border border-[#E8D8D2]">
                    {formatCurrency(loanAmount)}
                  </span>
                </div>
                <div className="relative">
                  <input
                    id="loan-amount-input"
                    ref={loanInputRef}
                    type="number"
                    min="1000"
                    max="100000000"
                    step="5000"
                    value={loanAmount}
                    onChange={(e) => handleLoanChange(Number(e.target.value))}
                    className="w-full px-3.5 py-2.5 text-xs font-bold rounded-xl border border-[#E8D8D2] bg-[#FFFBF0] text-[#3B2522] focus:bg-white focus:ring-1 focus:ring-[#EA717B] focus:border-[#EA717B] outline-none"
                    placeholder="e.g. 200000"
                  />
                  <span className="absolute right-3.5 top-2.5 text-[#765E59] font-bold text-xs">₹</span>
                </div>

                <input
                  type="range"
                  min="10000"
                  max="5000000"
                  step="10000"
                  value={loanAmount}
                  onChange={(e) => handleLoanChange(Number(e.target.value))}
                  className="w-full accent-[#EA717B] cursor-pointer h-1.5 bg-[#FFF4EC] border border-[#E8D8D2] rounded-lg"
                />

                {/* Quick Presets */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {[50000, 100000, 200000, 500000, 1000000].map((amt) => (
                    <button
                      key={amt}
                      type="button"
                      onClick={() => handleLoanChange(amt)}
                      className={`text-[10px] font-bold px-2 py-1 rounded-lg border transition cursor-pointer ${
                        loanAmount === amt
                          ? 'bg-[#EA717B] text-white border-[#EA717B]'
                          : 'bg-[#FFFBF0] text-[#765E59] hover:bg-[#FFF4EC] border-[#E8D8D2]'
                      }`}
                    >
                      ₹{(amt / 100000).toFixed(amt < 100000 ? 1 : 0)}L
                    </button>
                  ))}
                </div>
              </div>

              {/* Interest Rate Input */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label htmlFor="interest-rate-input" className="text-xs font-bold text-[#3B2522] uppercase tracking-wider">
                    {t('calculator.annualInterestRate', 'Annual Interest Rate (% p.a.)')}
                  </label>
                  <span className="text-sm font-extrabold text-[#3B2522] font-mono bg-[#F7AE56]/20 px-2.5 py-0.5 rounded-lg border border-[#F7AE56]/40">
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
                    className="w-full px-3.5 py-2.5 text-xs font-bold rounded-xl border border-[#E8D8D2] bg-[#FFFBF0] text-[#3B2522] focus:bg-white focus:ring-1 focus:ring-[#EA717B] focus:border-[#EA717B] outline-none"
                    placeholder="e.g. 7.0"
                  />
                  <span className="absolute right-3.5 top-2.5 text-[#765E59] font-bold text-xs">%</span>
                </div>

                <input
                  type="range"
                  min="0"
                  max="24"
                  step="0.25"
                  value={annualInterestRate}
                  onChange={(e) => handleRateChange(Number(e.target.value))}
                  className="w-full accent-[#F7AE56] cursor-pointer h-1.5 bg-[#FFF4EC] border border-[#E8D8D2] rounded-lg"
                />

                <div className="flex flex-wrap gap-1.5 pt-1">
                  {[
                    { label: '0% Interest-Free', rate: 0 },
                    { label: '4% Concessional', rate: 4 },
                    { label: '7% Benchmark', rate: 7 },
                    { label: '9.5% Bank Base', rate: 9.5 },
                    { label: '12% Commercial', rate: 12 },
                  ].map((item) => (
                    <button
                      key={item.rate}
                      type="button"
                      onClick={() => handleRateChange(item.rate)}
                      className={`text-[10px] font-bold px-2 py-1 rounded-lg border transition cursor-pointer ${
                        annualInterestRate === item.rate
                          ? 'bg-[#EA717B] text-white border-[#EA717B]'
                          : 'bg-[#FFFBF0] text-[#765E59] hover:bg-[#FFF4EC] border-[#E8D8D2]'
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Loan Tenure Input */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label htmlFor="tenure-input" className="text-xs font-bold text-[#3B2522] uppercase tracking-wider">
                    {t('calculator.loanTenure', 'Loan Tenure')}
                  </label>
                  <div className="flex items-center gap-1 bg-[#FFF4EC] p-0.5 rounded-lg border border-[#E8D8D2] text-[10px] font-bold">
                    <button
                      type="button"
                      onClick={() => {
                        if (tenureUnit === 'MONTHS') {
                          setTenureValue(Math.max(1, Math.round(tenureValue / 12)));
                          setTenureUnit('YEARS');
                        }
                      }}
                      className={`px-2 py-1 rounded-md transition cursor-pointer ${
                        tenureUnit === 'YEARS' ? 'bg-white text-[#3B2522] shadow-warm-xs' : 'text-[#765E59] hover:text-[#3B2522]'
                      }`}
                    >
                      Years
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        if (tenureUnit === 'YEARS') {
                          setTenureValue(tenureValue * 12);
                          setTenureUnit('MONTHS');
                        }
                      }}
                      className={`px-2 py-1 rounded-md transition cursor-pointer ${
                        tenureUnit === 'MONTHS' ? 'bg-white text-[#3B2522] shadow-warm-xs' : 'text-[#765E59] hover:text-[#3B2522]'
                      }`}
                    >
                      Months
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
                    className="w-full min-w-0 flex-1 px-3.5 py-2.5 text-xs font-bold rounded-xl border border-[#E8D8D2] bg-[#FFFBF0] text-[#3B2522] focus:bg-white focus:ring-1 focus:ring-[#EA717B] focus:border-[#EA717B] outline-none"
                  />
                  <span className="text-xs font-bold text-[#3B2522] whitespace-nowrap bg-[#FFF4EC] px-3 py-2.5 rounded-xl border border-[#E8D8D2] shrink-0 font-mono">
                    {tenureUnit === 'YEARS' ? `${tenureValue * 12} Months` : `${(tenureValue / 12).toFixed(1)} Years`}
                  </span>
                </div>

                <input
                  type="range"
                  min="1"
                  max={tenureUnit === 'YEARS' ? 30 : 360}
                  step="1"
                  value={tenureValue}
                  onChange={(e) => handleTenureChange(Number(e.target.value))}
                  className="w-full accent-[#EA717B] cursor-pointer h-1.5 bg-[#FFF4EC] border border-[#E8D8D2] rounded-lg"
                />

                <div className="flex flex-wrap gap-1.5 pt-1">
                  {[1, 3, 5, 7, 10].map((yr) => {
                    const val = tenureUnit === 'YEARS' ? yr : yr * 12;
                    return (
                      <button
                        key={yr}
                        type="button"
                        onClick={() => handleTenureChange(val)}
                        className={`text-[10px] font-bold px-2.5 py-1 rounded-lg border transition cursor-pointer ${
                          tenureValue === val
                            ? 'bg-[#EA717B] text-white border-[#EA717B]'
                            : 'bg-[#FFFBF0] text-[#765E59] hover:bg-[#FFF4EC] border-[#E8D8D2]'
                        }`}
                      >
                        {yr} {yr === 1 ? 'Year' : 'Years'}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Formula Integrity Badge */}
            <div className="bg-[#FFF4EC] p-4 rounded-2xl border border-[#E8D8D2] text-xs text-[#765E59] space-y-1.5">
              <div className="flex items-center gap-1.5 font-bold text-[#3B2522] text-xs">
                <ShieldCheck className="w-4 h-4 text-[#EA717B]" />
                <span>{t('calculator.emiFormulaTitle', 'Standard Reducing Balance EMI Formula')}</span>
              </div>
              <p className="text-[11px] text-[#765E59] font-mono">
                EMI = P × r × (1+r)ⁿ / ((1+r)ⁿ - 1)
              </p>
            </div>
          </div>

          {/* RIGHT COLUMN: Results Dashboard & Amortization (7 cols) */}
          {/* RIGHT COLUMN: Results Dashboard & Amortization (7 cols) */}
          <div id="calculator-results" className="lg:col-span-7 space-y-6 scroll-mt-24">
            {/* Main Output KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Monthly EMI */}
              <div className="bg-white p-5 rounded-3xl border border-[#E8D8D2] shadow-warm-xs relative overflow-hidden space-y-2 group hover:shadow-warm-md transition">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-2xl bg-[#FFD0CA]/50 text-[#EA717B] flex items-center justify-center">
                    <IndianRupee className="w-5 h-5" />
                  </div>
                  <span className="w-2.5 h-2.5 rounded-full bg-[#EA717B] animate-pulse" />
                </div>
                <div>
                  <span className="text-[11px] font-bold text-[#765E59] uppercase tracking-wider block">
                    {t('calculator.monthlyInstallment', 'Monthly EMI')}
                  </span>
                  <div className="text-2xl sm:text-3xl font-black text-[#3B2522] tracking-tight font-mono mt-0.5">
                    {formatCurrency(calculatedData.emi)}
                  </div>
                </div>
                <p className="text-[11px] text-[#765E59] font-medium">
                  {totalMonths} monthly installments
                </p>
              </div>

              {/* Total Interest Payable */}
              <div className="bg-white p-5 rounded-3xl border border-[#E8D8D2] shadow-warm-xs space-y-2 group hover:shadow-warm-md transition">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-2xl bg-[#F7AE56]/20 text-[#3B2522] flex items-center justify-center">
                    <Percent className="w-5 h-5 text-[#F7AE56]" />
                  </div>
                </div>
                <div>
                  <span className="text-[11px] font-bold text-[#765E59] uppercase tracking-wider block">
                    {t('calculator.totalInterestPayable', 'Total Interest')}
                  </span>
                  <div className="text-2xl sm:text-3xl font-black text-[#F7AE56] tracking-tight font-mono mt-0.5">
                    {formatCurrency(calculatedData.totalInterest)}
                  </div>
                </div>
                <p className="text-[11px] text-[#765E59] font-medium">
                  {calculatedData.interestPercent}% of total repayment
                </p>
              </div>

              {/* Total Repayment */}
              <div className="bg-white p-5 rounded-3xl border border-[#E8D8D2] shadow-warm-xs space-y-2 group hover:shadow-warm-md transition">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-2xl bg-[#FFD0CA]/40 text-[#4A2525] flex items-center justify-center">
                    <Wallet className="w-5 h-5 text-[#4A2525]" />
                  </div>
                </div>
                <div>
                  <span className="text-[11px] font-bold text-[#765E59] uppercase tracking-wider block">
                    Total Repayment
                  </span>
                  <div className="text-2xl sm:text-3xl font-black text-[#4A2525] tracking-tight font-mono mt-0.5">
                    {formatCurrency(calculatedData.totalRepayment)}
                  </div>
                </div>
                <p className="text-[11px] text-[#765E59] font-medium">
                  Principal + Total Interest
                </p>
              </div>
            </div>

            {/* Bridge to Financial Health */}
            <div className="bg-[#FFF4EC] p-5 rounded-3xl border border-[#FFD0CA] shadow-warm-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <div className="w-12 h-12 rounded-2xl bg-white border border-[#E8D8D2] text-emerald-600 flex items-center justify-center shrink-0 mt-0.5">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <div className="text-sm font-black text-[#3B2522]">
                    Can you afford this EMI?
                  </div>
                  <p className="text-xs text-[#765E59] leading-relaxed max-w-lg">
                    Based on standard guidelines, assess your actual household budget, income, and debt-to-income cushion before borrowing.
                  </p>
                </div>
              </div>
              <button
                type="button"
                id="btn-assess-affordability-bridge"
                onClick={() => handleTabSwitch('HEALTH')}
                className="px-5 py-2.5 bg-[#EA717B] hover:bg-[#d95d67] text-white text-xs font-bold rounded-xl shadow-warm-xs transition flex items-center gap-1.5 shrink-0 cursor-pointer"
              >
                <span>Check Financial Health →</span>
              </button>
            </div>

            {/* Breakdown Segmented Bar */}
            <div className="bg-white p-4 sm:p-6 rounded-3xl border border-[#E8D8D2] shadow-warm-xs space-y-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-1 sm:gap-4">
                <h3 className="text-xs font-extrabold text-[#3B2522] uppercase tracking-wider flex items-center gap-2">
                  <PieChart className="w-4 h-4 text-[#EA717B] shrink-0" />
                  <span>{t('calculator.principalVsInterest', 'Principal vs Interest Breakdown')}</span>
                </h3>
                <span className="text-xs font-bold text-[#3B2522] font-mono">
                  {t('calculator.total', 'Total')}: {formatCurrency(calculatedData.totalRepayment)}
                </span>
              </div>

              <div className="w-full h-4 bg-[#FFF4EC] rounded-full overflow-hidden flex border border-[#E8D8D2]">
                <div
                  style={{ width: `${calculatedData.principalPercent}%` }}
                  className="bg-[#EA717B] h-full transition-all duration-300"
                  title={`Principal: ${calculatedData.principalPercent}%`}
                />
                <div
                  style={{ width: `${calculatedData.interestPercent}%` }}
                  className="bg-[#F7AE56] h-full transition-all duration-300"
                  title={`Interest: ${calculatedData.interestPercent}%`}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
                <div className="flex items-center gap-2 bg-[#FFFBF0] p-3 rounded-2xl border border-[#E8D8D2]">
                  <div className="w-3.5 h-3.5 bg-[#EA717B] rounded-md shrink-0" />
                  <div>
                    <span className="text-[10px] font-bold text-[#765E59] uppercase block">{t('calculator.principalAmount', 'Principal Amount')}</span>
                    <span className="font-extrabold text-[#3B2522] font-mono text-sm">
                      {formatCurrency(loanAmount)} ({calculatedData.principalPercent}%)
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 bg-[#FFFBF0] p-3 rounded-2xl border border-[#E8D8D2]">
                  <div className="w-3.5 h-3.5 bg-[#F7AE56] rounded-md shrink-0" />
                  <div>
                    <span className="text-[10px] font-bold text-[#765E59] uppercase block">{t('calculator.totalInterest', 'Total Interest')}</span>
                    <span className="font-extrabold text-[#F7AE56] font-mono text-sm">
                      {formatCurrency(calculatedData.totalInterest)} ({calculatedData.interestPercent}%)
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Government Subsidy (if Scheme Selected) */}
            {backendResult && (backendResult.subsidy_amount || backendResult.beneficiary_contribution_amount) && (
              <div className="bg-[#4A2525] text-white p-6 rounded-3xl border border-[#E8D8D2]/20 shadow-warm-md space-y-3">
                <div className="flex items-center justify-between">
                  <div className="inline-flex items-center gap-2 bg-white/15 text-[#F7AE56] text-xs font-bold px-3 py-1 rounded-full border border-white/20">
                    <Sparkles className="w-3.5 h-3.5 text-[#F7AE56]" />
                    <span>Official Scheme Subsidy & Benefit Details</span>
                  </div>
                  {selectedScheme && (
                    <Link
                      to={`/schemes/${selectedScheme.scheme_id}`}
                      className="text-xs text-[#FFD0CA] hover:text-white font-bold flex items-center gap-1 transition"
                    >
                      <span>{t('calculator.viewSchemeRules', 'View Scheme Rules')}</span> <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs pt-1">
                  {backendResult.subsidy_amount !== undefined && backendResult.subsidy_amount !== null && (
                    <div className="bg-black/20 p-3 rounded-xl border border-white/10">
                      <span className="text-[#FFD0CA]/80 text-[10px] uppercase font-bold block">{t('calculator.estimatedGovtSubsidy', 'Estimated Govt Subsidy')}</span>
                      <span className="text-lg font-black text-[#F7AE56] font-mono mt-0.5 block">
                        {formatCurrency(backendResult.subsidy_amount)}
                      </span>
                    </div>
                  )}
                  {backendResult.beneficiary_contribution_amount !== undefined && backendResult.beneficiary_contribution_amount !== null && (
                    <div className="bg-black/20 p-3 rounded-xl border border-white/10">
                      <span className="text-[#FFD0CA]/80 text-[10px] uppercase font-bold block">{t('calculator.applicantContribution', 'Applicant Contribution')}</span>
                      <span className="text-lg font-black text-white font-mono mt-0.5 block">
                        {formatCurrency(backendResult.beneficiary_contribution_amount)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Amortization Schedule Table */}
            <div className="bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs overflow-hidden space-y-4">
              <div className="p-6 pb-0 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                <div>
                  <h3 className="text-base font-extrabold text-[#3B2522] flex items-center gap-2">
                    <Table className="w-4 h-4 text-[#EA717B]" />
                    <span>{t('calculator.loanAmortizationSchedule', 'Loan Amortization Schedule')}</span>
                  </h3>
                  <p className="text-xs text-[#765E59] mt-0.5">
                    Complete breakdown of principal reduction and interest deduction over tenure.
                  </p>
                </div>

                <div className="flex items-center gap-1 bg-[#FFF4EC] p-1 rounded-xl border border-[#E8D8D2] text-xs font-bold">
                  <button
                    type="button"
                    onClick={() => setScheduleViewMode('MONTHLY')}
                    className={`px-3 py-1 rounded-lg transition cursor-pointer ${
                      scheduleViewMode === 'MONTHLY' ? 'bg-white text-[#3B2522] shadow-warm-xs' : 'text-[#765E59] hover:text-[#3B2522]'
                    }`}
                  >
                    Monthly View
                  </button>
                  <button
                    type="button"
                    onClick={() => setScheduleViewMode('YEARLY')}
                    className={`px-3 py-1 rounded-lg transition cursor-pointer ${
                      scheduleViewMode === 'YEARLY' ? 'bg-white text-[#3B2522] shadow-warm-xs' : 'text-[#765E59] hover:text-[#3B2522]'
                    }`}
                  >
                    Yearly Summary
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-medium">
                  <thead className="bg-[#FFF4EC] text-[#3B2522] font-bold border-y border-[#E8D8D2] uppercase text-[10px] tracking-wider">
                    <tr>
                      <th className="py-3 px-4">{scheduleViewMode === 'MONTHLY' ? t('calculator.month', 'Month') : t('calculator.year', 'Year')}</th>
                      <th className="py-3 px-4">{t('calculator.openingBalance', 'Opening Balance')}</th>
                      <th className="py-3 px-4">{t('calculator.monthlyInstallment', 'EMI Installment')}</th>
                      <th className="py-3 px-4 text-emerald-700">{t('calculator.principalPaid', 'Principal Paid')}</th>
                      <th className="py-3 px-4 text-[#EA717B]">{t('calculator.interestPaid', 'Interest Paid')}</th>
                      <th className="py-3 px-4 text-right">{t('calculator.closingBalance', 'Closing Balance')}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E8D8D2]/50 text-[#765E59] font-mono bg-white">
                    {scheduleViewMode === 'MONTHLY' ? (
                      (showFullSchedule ? calculatedData.schedule : calculatedData.schedule.slice(0, 12)).map((row) => (
                        <tr key={row.installment_number} className="hover:bg-[#FFF4EC]/50 transition">
                          <td className="py-2.5 px-4 font-bold text-[#3B2522] font-sans">{t('calculator.month', 'Month')} {row.installment_number}</td>
                          <td className="py-2.5 px-4">{formatCurrency(row.opening_principal)}</td>
                          <td className="py-2.5 px-4 font-bold text-[#3B2522]">{formatCurrency(row.installment_amount)}</td>
                          <td className="py-2.5 px-4 text-emerald-700 font-bold">{formatCurrency(row.principal_component)}</td>
                          <td className="py-2.5 px-4 text-[#EA717B] font-bold">{formatCurrency(row.interest_component)}</td>
                          <td className="py-2.5 px-4 text-right font-bold text-[#3B2522]">{formatCurrency(row.closing_principal)}</td>
                        </tr>
                      ))
                    ) : (
                      calculatedData.yearlySchedule.map((yr) => (
                        <tr key={yr.year} className="hover:bg-[#FFF4EC]/50 transition">
                          <td className="py-2.5 px-4 font-bold text-[#3B2522] font-sans">Year {yr.year}</td>
                          <td className="py-2.5 px-4">{formatCurrency(yr.opening_principal)}</td>
                          <td className="py-2.5 px-4 font-bold text-[#3B2522]">{formatCurrency(yr.total_installment)}</td>
                          <td className="py-2.5 px-4 text-emerald-700 font-bold">{formatCurrency(yr.principal_paid)}</td>
                          <td className="py-2.5 px-4 text-[#EA717B] font-bold">{formatCurrency(yr.interest_paid)}</td>
                          <td className="py-2.5 px-4 text-right font-bold text-[#3B2522]">{formatCurrency(yr.closing_principal)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {scheduleViewMode === 'MONTHLY' && calculatedData.schedule.length > 12 && (
                <div className="p-4 bg-[#FFFBF0] border-t border-[#E8D8D2] text-center">
                  <button
                    type="button"
                    onClick={() => setShowFullSchedule(!showFullSchedule)}
                    className="text-xs font-bold text-[#EA717B] hover:text-[#d95d67] inline-flex items-center gap-1.5 transition cursor-pointer"
                  >
                    {showFullSchedule ? (
                      <>{t('calculator.showFirst12Months', 'Show First 12 Months Only')} <ChevronUp className="w-4 h-4" /></>
                    ) : (
                      <>{t('calculator.showAllTenureMonths', 'Show Full {{months}}-Month Amortization Schedule', { months: totalMonths })} <ChevronDown className="w-4 h-4" /></>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          VIEW 2: FINANCIAL HEALTH & LOAN AFFORDABILITY ASSESSMENT
          ───────────────────────────────────────────────────────────── */}
      {activeTab === 'HEALTH' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* LEFT COLUMN: Citizen Financial Inputs Form (5 cols) */}
          <div className="lg:col-span-5 bg-white p-5 sm:p-7 rounded-3xl border border-[#E8D8D2] shadow-warm-xs space-y-6">
            <div className="border-b border-[#E8D8D2]/60 pb-3 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-extrabold text-[#3B2522] uppercase tracking-wider flex items-center gap-2">
                  <Scale className="w-4 h-4 text-[#EA717B]" />
                  <span>{t('calculator.householdContext')}</span>
                </h2>
                <p className="text-[11px] text-[#765E59] mt-0.5">
                  {t('calculator.householdContextDesc')}
                </p>
              </div>

              <button
                type="button"
                onClick={() => {
                  setMonthlyIncome(30000);
                  setMonthlyExpenses(18000);
                  setMonthlyObligations(3000);
                  setHealthResult(null);
                  setHealthValidationWarning(null);
                }}
                className="text-xs text-[#765E59] hover:text-[#3B2522] flex items-center gap-1 font-semibold cursor-pointer"
                title={t('calculator.resetTitle')}
              >
                <RotateCcw className="w-3.5 h-3.5" /> {t('calculator.reset')}
              </button>
            </div>

            <div className="space-y-4">
              {/* Target Scheme Selector */}
              <div>
                <label htmlFor="health-scheme-select" className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1.5">
                  {t('calculator.targetScheme')}
                </label>
                <select
                  id="health-scheme-select"
                  value={selectedSchemeId}
                  onChange={(e) => {
                    setSelectedSchemeId(e.target.value);
                    const p = new URLSearchParams(searchParams);
                    if (e.target.value) {
                      p.set('scheme', e.target.value);
                    } else {
                      p.delete('scheme');
                    }
                    setSearchParams(p);
                  }}
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-[#E8D8D2] focus:ring-1 focus:ring-[#EA717B] focus:border-[#EA717B] outline-none bg-[#FFFBF0] font-semibold text-[#3B2522]"
                >
                  <option value="">{t('calculator.standardGeneralLoan')}</option>
                  {schemes.map((s) => (
                    <option key={s.scheme_id} value={s.scheme_id}>
                      {s.scheme_name}
                    </option>
                  ))}
                </select>

                {selectedScheme && isSelectedSchemeNonCredit && (
                  <div className="mt-2 p-3 bg-[#FFF4EC] border border-[#F7AE56]/40 rounded-xl text-[#3B2522] text-xs flex items-start gap-2">
                    <Info className="w-4 h-4 text-[#F7AE56] shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold block text-[#3B2522]">{t('calculator.nonCreditNoticeTitle')}</span>
                      <span className="text-[#765E59]">
                        {t('calculator.nonCreditNoticeDesc')}
                      </span>
                    </div>
                  </div>
                )}

                {selectedScheme && isSelectedSchemeRateUnspecified && (
                  <div className="mt-2 p-3 bg-[#FFF4EC] border border-[#FFD0CA] rounded-xl text-[#3B2522] text-xs flex items-start gap-2">
                    <Info className="w-4 h-4 text-[#EA717B] shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold block text-[#3B2522]">{t('calculator.unspecifiedNoticeTitle')}</span>
                      <span className="text-[#765E59]">
                        {t('calculator.unspecifiedNoticeDesc')}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Monthly Income (Required) */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label htmlFor="health-monthly-income" className="text-xs font-bold text-[#3B2522] uppercase tracking-wider flex items-center gap-1.5">
                    <Wallet className="w-3.5 h-3.5 text-[#EA717B]" />
                    <span>{t('calculator.monthlyFamilyIncome')} <span className="text-[#EA717B]">*</span></span>
                  </label>
                  <span className="text-xs font-black text-[#3B2522] font-mono bg-[#FFF4EC] px-2 py-0.5 rounded border border-[#E8D8D2]">
                    {formatCurrency(monthlyIncome)}
                  </span>
                </div>
                <input
                  id="health-monthly-income"
                  type="number"
                  min="0"
                  step="1000"
                  value={monthlyIncome}
                  onChange={(e) => handleIncomeChange(Math.max(0, Number(e.target.value)))}
                  className="w-full px-3.5 py-2.5 text-xs font-bold rounded-xl border border-[#E8D8D2] bg-[#FFFBF0] text-[#3B2522] focus:bg-white focus:ring-1 focus:ring-[#EA717B] focus:border-[#EA717B] outline-none"
                  placeholder="e.g. 30000"
                  required
                />
                <p className="text-[10px] text-[#765E59]">{t('calculator.monthlyFamilyIncomeDesc')}</p>
              </div>

              {/* Monthly Expenses (Required) */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label htmlFor="health-monthly-expenses" className="text-xs font-bold text-[#3B2522] uppercase tracking-wider flex items-center gap-1.5">
                    <Coins className="w-3.5 h-3.5 text-[#F7AE56]" />
                    <span>{t('calculator.monthlyExpenses')} <span className="text-[#EA717B]">*</span></span>
                  </label>
                  <span className="text-xs font-black text-[#3B2522] font-mono bg-[#FFF4EC] px-2 py-0.5 rounded border border-[#E8D8D2]">
                    {formatCurrency(monthlyExpenses)}
                  </span>
                </div>
                <input
                  id="health-monthly-expenses"
                  type="number"
                  min="0"
                  step="1000"
                  value={monthlyExpenses}
                  onChange={(e) => handleExpensesChange(Math.max(0, Number(e.target.value)))}
                  className="w-full px-3.5 py-2.5 text-xs font-bold rounded-xl border border-[#E8D8D2] bg-[#FFFBF0] text-[#3B2522] focus:bg-white focus:ring-1 focus:ring-[#EA717B] focus:border-[#EA717B] outline-none"
                  placeholder="e.g. 18000"
                  required
                />
                <p className="text-[10px] text-[#765E59]">{t('calculator.monthlyExpensesDesc')}</p>
              </div>

              {/* Existing Monthly Debt Obligations / EMIs (Optional) */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label htmlFor="health-monthly-obligations" className="text-xs font-bold text-[#3B2522] uppercase tracking-wider flex items-center gap-1.5">
                    <IndianRupee className="w-3.5 h-3.5 text-[#765E59]" />
                    <span>{t('calculator.existingEmis')} <span className="text-[#765E59] text-[10px] font-normal">{t('calculator.optional')}</span></span>
                  </label>
                  <span className="text-xs font-black text-[#765E59] font-mono bg-[#FFF4EC] px-2 py-0.5 rounded border border-[#E8D8D2]">
                    {formatCurrency(monthlyObligations)}
                  </span>
                </div>
                <input
                  id="health-monthly-obligations"
                  type="number"
                  min="0"
                  step="500"
                  value={monthlyObligations}
                  onChange={(e) => handleObligationsChange(Math.max(0, Number(e.target.value)))}
                  className="w-full px-3.5 py-2.5 text-xs font-bold rounded-xl border border-[#E8D8D2] bg-[#FFFBF0] text-[#3B2522] focus:bg-white focus:ring-1 focus:ring-[#EA717B] focus:border-[#EA717B] outline-none"
                  placeholder="e.g. 3000"
                />
                <p className="text-[10px] text-[#765E59]">{t('calculator.existingEmisDesc')}</p>
              </div>

              {/* Requested Loan Amount (Required) */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label htmlFor="health-loan-amount" className="text-xs font-bold text-[#3B2522] uppercase tracking-wider flex items-center gap-1.5">
                    <CalcIcon className="w-3.5 h-3.5 text-[#EA717B]" />
                    <span>{t('calculator.requestedLoan')} <span className="text-[#EA717B]">*</span></span>
                  </label>
                  <span className="text-xs font-black text-[#4A2525] font-mono bg-[#FFF4EC] px-2 py-0.5 rounded border border-[#E8D8D2]">
                    {formatCurrency(loanAmount)}
                  </span>
                </div>
                <input
                  id="health-loan-amount"
                  ref={healthLoanInputRef}
                  type="number"
                  min="5000"
                  step="10000"
                  value={loanAmount}
                  onChange={(e) => handleLoanChange(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 text-xs font-bold rounded-xl border border-[#E8D8D2] bg-[#FFFBF0] text-[#3B2522] focus:bg-white focus:ring-1 focus:ring-[#EA717B] focus:border-[#EA717B] outline-none"
                  placeholder="e.g. 200000"
                  required
                />
              </div>

              {/* Rate & Tenure Parameters (Read-only or Adjustable) */}
              <div className="grid grid-cols-2 gap-3 pt-1">
                <div>
                  <label htmlFor="health-interest-rate" className="block text-[10px] font-bold text-[#765E59] uppercase mb-1">
                    {t('calculator.interestRatePerAnnum')}
                  </label>
                  <input
                    id="health-interest-rate"
                    type="number"
                    min="0"
                    max="40"
                    step="0.25"
                    value={annualInterestRate}
                    onChange={(e) => handleRateChange(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs font-bold rounded-lg border border-[#E8D8D2] bg-[#FFFBF0] text-[#3B2522] focus:bg-white focus:ring-1 focus:ring-[#EA717B] focus:border-[#EA717B] outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="health-tenure" className="block text-[10px] font-bold text-[#765E59] uppercase mb-1">
                    {tenureUnit === 'YEARS' ? t('calculator.tenureYears') : t('calculator.tenureMonths')}
                  </label>
                  <input
                    id="health-tenure"
                    type="number"
                    min="1"
                    max={tenureUnit === 'YEARS' ? 30 : 360}
                    value={tenureValue}
                    onChange={(e) => handleTenureChange(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs font-bold rounded-lg border border-[#E8D8D2] bg-[#FFFBF0] text-[#3B2522] focus:bg-white focus:ring-1 focus:ring-[#EA717B] focus:border-[#EA717B] outline-none"
                  />
                </div>
              </div>

              {/* Assess Action Button */}
              <div className="pt-2">
                <button
                  type="button"
                  id="btn-assess-financial-health"
                  onClick={handleAssessHealth}
                  disabled={isHealthLoading}
                  className="w-full py-3.5 px-4 bg-[#EA717B] hover:bg-[#d95d67] text-white font-black rounded-xl text-xs shadow-warm-xs transition flex items-center justify-center gap-2 disabled:opacity-60 cursor-pointer"
                >
                  <ShieldCheck className="w-4 h-4 text-white" />
                  <span>{isHealthLoading ? t('calculator.evaluatingParams') : t('calculator.tabAffordability')}</span>
                </button>
              </div>
            </div>

            {/* Authoritative Disclaimer */}
            <div className="bg-[#FFF4EC] p-3.5 rounded-2xl border border-[#E8D8D2] text-[#765E59] text-[11px] leading-relaxed flex items-start gap-2">
              <Info className="w-4 h-4 text-[#EA717B] shrink-0 mt-0.5" />
              <span>
                <strong className="text-[#3B2522]">{t('calculator.zeroBureauTitle')}</strong> {t('calculator.zeroBureauDesc')}
              </span>
            </div>
          </div>

          {/* RIGHT COLUMN: Citizen-Friendly Financial Health Result Card (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {!healthResult && !isHealthLoading && (
              <div className="bg-white p-8 rounded-3xl border border-[#E8D8D2] shadow-warm-xs text-center space-y-4">
                <div className="w-16 h-16 rounded-full bg-[#FFF4EC] border border-[#E8D8D2] flex items-center justify-center mx-auto text-[#EA717B]">
                  <Scale className="w-8 h-8" />
                </div>
                <div className="max-w-md mx-auto space-y-1.5">
                  <h3 className="text-lg font-black text-[#3B2522]">
                    Ready to Evaluate Your Loan Affordability
                  </h3>
                  <p className="text-xs text-[#765E59] leading-relaxed">
                    Enter your approximate monthly income and living/business expenses on the left to see if this financing comfortably fits your financial situation.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleAssessHealth}
                  className="px-6 py-2.5 bg-[#EA717B] hover:bg-[#d95d67] text-white font-bold text-xs rounded-xl shadow-warm-xs transition inline-flex items-center gap-2 cursor-pointer"
                >
                  <ShieldCheck className="w-4 h-4 text-white" />
                  <span>{t('calculator.assessWithCurrent')}</span>
                </button>
              </div>
            )}

            {isHealthLoading && (
              <div className="bg-white p-12 rounded-3xl border border-[#E8D8D2] shadow-warm-xs text-center space-y-3">
                <RefreshCw className="w-8 h-8 animate-spin text-[#EA717B] mx-auto" />
                <p className="text-xs font-bold text-[#3B2522]">{t('calculator.evaluatingRatios')}</p>
                <p className="text-[11px] text-[#765E59]">{t('calculator.evaluatingCushion')}</p>
              </div>
            )}

            {healthResult && !isHealthLoading && (
              <div className="bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs overflow-hidden space-y-6 p-6 sm:p-8">
                {/* 🌟 1. FINANCIAL HEALTH HEADER & STATUS BADGE 🌟 */}
                <div className="border-b border-[#E8D8D2]/60 pb-5 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className="text-xs font-black uppercase tracking-wider text-[#765E59]">
                      FINANCIAL HEALTH ASSESSMENT
                    </span>
                    <span className="text-[11px] font-mono font-semibold text-[#765E59]">
                      Deterministic Engine v{healthResult.calculation_version || '2.1.0'}
                    </span>
                  </div>

                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div>
                      <h3 className="text-xl sm:text-2xl font-black text-[#3B2522] tracking-tight">
                        Can this loan fit your finances?
                      </h3>
                      <p className="text-xs text-[#765E59] mt-1">
                        {currentBadge.desc}
                      </p>
                    </div>

                    {/* Prominent Status Pill */}
                    <div className={`px-4 py-2 rounded-2xl border font-black text-sm sm:text-base flex items-center gap-2 shadow-warm-xs shrink-0 ${currentBadge.bg}`}>
                      <StatusBadgeIcon className="w-5 h-5" />
                      <span>{currentBadge.headline}</span>
                    </div>
                  </div>
                </div>

                {/* 🌟 2. THE UNDERLYING NUMBERS (TRANSPARENT BREAKDOWN) 🌟 */}
                <div className="space-y-3">
                  <h4 className="text-xs font-black uppercase tracking-wider text-[#3B2522] flex items-center gap-1.5">
                    <Wallet className="w-3.5 h-3.5 text-[#EA717B]" />
                    <span>{t('calculator.cashflowSummaryTitle')}</span>
                  </h4>

                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="bg-[#FFFBF0] p-3.5 rounded-2xl border border-[#E8D8D2]">
                      <span className="text-[10px] uppercase font-bold text-[#765E59] block tracking-wider">
                        {t('calculator.monthlyIncome', 'Monthly Income')}
                      </span>
                      <span className="text-base sm:text-lg font-black text-[#3B2522] font-mono block mt-0.5">
                        {healthResult.monthly_income ? formatCurrency(healthResult.monthly_income) : formatCurrency(monthlyIncome)}
                      </span>
                      <span className="text-[9px] text-[#765E59]">{t('calculator.selfDeclaredEarnings')}</span>
                    </div>

                    <div className="bg-[#FFFBF0] p-3.5 rounded-2xl border border-[#E8D8D2]">
                      <span className="text-[10px] uppercase font-bold text-[#765E59] block tracking-wider">
                        {t('calculator.monthlyExpenses')}
                      </span>
                      <span className="text-base sm:text-lg font-black text-[#3B2522] font-mono block mt-0.5">
                        {healthResult.monthly_expenses ? formatCurrency(healthResult.monthly_expenses) : formatCurrency(monthlyExpenses)}
                      </span>
                      <span className="text-[9px] text-[#765E59]">{t('calculator.livingCosts')}</span>
                    </div>

                    <div className="bg-[#FFFBF0] p-3.5 rounded-2xl border border-[#E8D8D2]">
                      <span className="text-[10px] uppercase font-bold text-[#765E59] block tracking-wider">
                        {t('calculator.existingEmis')}
                      </span>
                      <span className="text-base sm:text-lg font-black text-[#3B2522] font-mono block mt-0.5">
                        {healthResult.existing_monthly_obligations !== undefined && healthResult.existing_monthly_obligations !== null
                          ? formatCurrency(healthResult.existing_monthly_obligations)
                          : formatCurrency(monthlyObligations)}
                      </span>
                      <span className="text-[9px] text-[#765E59]">{t('calculator.currentDebtObligations')}</span>
                    </div>

                    <div className="bg-[#FFFBF0] p-3.5 rounded-2xl border border-[#E8D8D2]">
                      <span className="text-[10px] uppercase font-bold text-[#765E59] block tracking-wider">
                        {t('calculator.standardEmi')}
                      </span>
                      <span className="text-base sm:text-lg font-black text-[#4A2525] font-mono block mt-0.5">
                        {healthResult.proposed_monthly_emi !== undefined && healthResult.proposed_monthly_emi !== null
                          ? formatCurrency(healthResult.proposed_monthly_emi)
                          : formatCurrency(calculatedData.emi)}
                      </span>
                      <span className="text-[9px] text-[#765E59]">{t('calculator.newLoanEmi')}</span>
                    </div>

                    <div className="bg-[#FFFBF0] p-3.5 rounded-2xl border border-[#E8D8D2]">
                      <span className="text-[10px] uppercase font-bold text-[#765E59] block tracking-wider">
                        {t('calculator.repaymentObligation')}
                      </span>
                      <span className={`text-base sm:text-lg font-black font-mono block mt-0.5 ${
                        healthResult.debt_to_income_ratio && Number(healthResult.debt_to_income_ratio) > 50
                          ? 'text-[#EA717B]'
                          : 'text-[#3B2522]'
                      }`}>
                        {healthResult.debt_to_income_ratio !== undefined && healthResult.debt_to_income_ratio !== null
                          ? `${Number(healthResult.debt_to_income_ratio).toFixed(1)}%`
                          : `${((((healthResult.existing_monthly_obligations || monthlyObligations) + (healthResult.proposed_monthly_emi || calculatedData.emi)) / (monthlyIncome || 1)) * 100).toFixed(1)}%`}
                      </span>
                      <span className="text-[9px] text-[#765E59]">{t('calculator.dtiRatio')}</span>
                    </div>

                    <div className="bg-[#FFF4EC] p-3.5 rounded-2xl border border-[#FFD0CA]">
                      <span className="text-[10px] uppercase font-bold text-emerald-800 block tracking-wider">
                        {t('calculator.disposableCushion')}
                      </span>
                      <span className={`text-base sm:text-lg font-black font-mono block mt-0.5 ${
                        Number(healthResult.estimated_disposable_income || 0) > 0 ? 'text-emerald-700' : 'text-[#EA717B]'
                      }`}>
                        {healthResult.estimated_disposable_income !== null && healthResult.estimated_disposable_income !== undefined
                          ? `${formatCurrency(healthResult.estimated_disposable_income)} / ${t('calculator.month')}`
                          : `${formatCurrency(Math.max(0, monthlyIncome - monthlyExpenses - (monthlyObligations + calculatedData.emi)))} / ${t('calculator.month')}`}
                      </span>
                      <span className="text-[9px] text-emerald-700 font-medium">{t('calculator.disposableCushion')}</span>
                    </div>
                  </div>
                </div>

                {/* 🌟 3. HEADLINE & CITIZEN GUIDANCE 🌟 */}
                <div className="bg-[#FFF4EC] p-4 rounded-2xl border border-[#E8D8D2] space-y-1">
                  <h5 className="text-xs font-black text-[#3B2522]">
                    {healthResult.summary_headline}
                  </h5>
                  {healthResult.summary_detail && (
                    <p className="text-xs text-[#765E59] leading-relaxed">
                      {healthResult.summary_detail}
                    </p>
                  )}
                </div>

                {/* 🌟 4. CITIZEN ACTIONS: Adjust Loan / View Breakdown 🌟 */}
                <div className="flex flex-wrap items-center gap-3 pt-1">
                  <button
                    type="button"
                    onClick={() => {
                      if (healthLoanInputRef.current) {
                        healthLoanInputRef.current.focus();
                        healthLoanInputRef.current.select();
                      }
                    }}
                    className="px-4 py-2 bg-[#FFFBF0] hover:bg-[#FFF4EC] text-[#3B2522] font-bold text-xs rounded-xl border border-[#E8D8D2] transition cursor-pointer"
                  >
                    {t('calculator.editParameters')}
                  </button>

                  <button
                    type="button"
                    onClick={() => handleTabSwitch('EMI')}
                    className="px-4 py-2 bg-[#EA717B] hover:bg-[#d95d67] text-white font-bold text-xs rounded-xl shadow-warm-xs transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <Table className="w-3.5 h-3.5" />
                    <span>{t('calculator.viewFullBreakdown')}</span>
                  </button>
                </div>

                {/* 🌟 5. EVALUATED INDICATOR BENCHMARKS 🌟 */}
                {healthResult.indicators && healthResult.indicators.length > 0 && (
                  <div className="space-y-3 pt-2">
                    <h4 className="text-xs font-black uppercase tracking-wider text-[#3B2522]">
                      Standard Prudent Lending Benchmarks
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {healthResult.indicators.map((ind: FinancialIndicatorResult, i: number) => {
                        const isOk = ind.status === 'HEALTHY';
                        const isMod = ind.status === 'MODERATE';
                        return (
                          <div
                            key={i}
                            className={`p-3.5 rounded-xl border text-xs space-y-1.5 ${
                              isOk ? 'bg-emerald-50/50 border-emerald-200' : isMod ? 'bg-[#F7AE56]/15 border-[#F7AE56]/30' : 'bg-[#EA717B]/10 border-[#EA717B]/20'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-[#3B2522]">{ind.label}</span>
                              <span className="font-mono font-black text-xs px-2 py-0.5 rounded bg-white border border-[#E8D8D2] text-[#3B2522]">
                                {ind.formatted_value}
                              </span>
                            </div>
                            <p className="text-[11px] text-[#765E59] leading-relaxed">
                              {ind.explanation}
                            </p>
                            <div className="text-[10px] text-[#765E59] font-medium">
                              Benchmark standard: {ind.benchmark}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* 🌟 6. STRENGTHS & CAUTIONARY FACTORS 🌟 */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                  {healthResult.positive_factors && healthResult.positive_factors.length > 0 && (
                    <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200 space-y-2">
                      <span className="text-xs font-black text-emerald-950 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <span>{t('calculator.strengthsTitle')}</span>
                      </span>
                      <ul className="space-y-1 text-[11px] text-[#765E59]">
                        {healthResult.positive_factors.map((f, idx) => (
                          <li key={idx} className="flex items-start gap-1.5">
                            <span className="text-emerald-600 font-bold">•</span>
                            <span>{f}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {healthResult.risk_flags && healthResult.risk_flags.length > 0 && (
                    <div className="p-4 rounded-2xl bg-[#EA717B]/10 border border-[#EA717B]/20 space-y-2">
                      <span className="text-xs font-black text-[#4A2525] flex items-center gap-1.5">
                        <AlertTriangle className="w-4 h-4 text-[#EA717B]" />
                        <span>{t('calculator.stressSignalsTitle')}</span>
                      </span>
                      <ul className="space-y-1 text-[11px] text-[#765E59]">
                        {healthResult.risk_flags.map((rf, idx) => (
                          <li key={idx} className="flex items-start gap-1.5">
                            <span className="text-[#EA717B] font-bold">•</span>
                            <span>{rf}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
