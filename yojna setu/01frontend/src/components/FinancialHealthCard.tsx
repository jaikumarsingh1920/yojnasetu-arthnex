import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { financialApi } from '../api/financialApi';
import {
  FinancialHealthResponse,
  FinancialIndicatorResult,
  BeneficiaryProfileInput
} from '../types';
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RefreshCw,
  TrendingUp,
  Coins,
  Wallet,
  Scale,
  Info,
  Lock,
  ArrowRight
} from 'lucide-react';

interface FinancialHealthCardProps {
  profileData?: BeneficiaryProfileInput;
  isAuthenticated?: boolean;
  className?: string;
}

export const FinancialHealthCard: React.FC<FinancialHealthCardProps> = ({
  profileData,
  isAuthenticated = false,
  className = '',
}) => {
  const { t } = useTranslation();
  const [data, setData] = useState<FinancialHealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAssessment = async () => {
    setIsLoading(true);
    setError(null);
    try {
      if (isAuthenticated && !profileData) {
        const res = await financialApi.getFinancialHealth();
        setData(res);
      } else {
        const res = await financialApi.assessFinancialHealth({
          annual_income: profileData?.annual_income ?? undefined,
          requested_loan_amount: profileData?.requested_loan_amount ?? undefined,
          project_cost: profileData?.project_cost ?? undefined,
          profile: profileData,
        });
        setData(res);
      }
    } catch (err: any) {
      console.warn('Financial health evaluation error:', err);
      setError(
        err?.response?.data?.detail ||
        'Could not evaluate financial suitability at this time.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAssessment();
  }, [isAuthenticated, profileData?.annual_income, profileData?.requested_loan_amount, profileData?.project_cost]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return {
          label: 'Healthy Borrowing Capacity',
          bg: 'bg-emerald-100 text-emerald-800 border-emerald-300',
          icon: CheckCircle2,
          iconColor: 'text-emerald-600',
        };
      case 'MODERATE':
        return {
          label: 'Moderate Financial Suitability',
          bg: 'bg-sky-100 text-sky-800 border-sky-300',
          icon: ShieldCheck,
          iconColor: 'text-sky-600',
        };
      case 'STRESSED':
        return {
          label: 'Stressed / Tight Margin',
          bg: 'bg-amber-100 text-amber-800 border-amber-300',
          icon: AlertTriangle,
          iconColor: 'text-amber-600',
        };
      case 'HIGH_RISK':
        return {
          label: 'High Debt Burden / Overleveraged',
          bg: 'bg-rose-100 text-rose-800 border-rose-300',
          icon: XCircle,
          iconColor: 'text-rose-600',
        };
      default:
        return {
          label: 'Insufficient Information',
          bg: 'bg-slate-100 text-slate-700 border-slate-300',
          icon: HelpCircle,
          iconColor: 'text-slate-500',
        };
    }
  };

  const statusInfo = getStatusBadge(data?.status || 'INSUFFICIENT_INFORMATION');
  const StatusIcon = statusInfo.icon;

  return (
    <div className={`bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs overflow-hidden ${className}`}>
      {/* Card Header */}
      <div className="bg-gradient-to-r from-[#4A2525] via-[#3B2522] to-[#4A2525] p-6 text-white space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex items-center gap-2 bg-[#FFF4EC]/15 border border-[#FFD0CA]/25 text-[#FFD0CA] px-3 py-1 rounded-full text-xs font-bold">
            <Scale className="w-3.5 h-3.5 text-[#F7AE56]" />
            <span>{t('calculator.engineTitle', 'Deterministic Debt Service & Suitability Engine')}</span>
          </div>

          <button
            type="button"
            onClick={fetchAssessment}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded-xl text-xs font-semibold transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{t('calculator.reAssess', 'Re-assess')}</span>
          </button>
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-1">
          <div>
            <h3 className="text-xl font-extrabold tracking-tight">
              Citizen Financial Health & Borrowing Suitability
            </h3>
            <p className="text-xs text-[#FFD0CA] mt-1 max-w-2xl">
              Factual, transparent debt service evaluation to help you understand your sustainable loan capacity before applying.
            </p>
          </div>

          {data && data.score !== null && data.score !== undefined && (
            <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl px-5 py-3 text-center shrink-0">
              <span className="text-[10px] uppercase font-bold text-[#FFD0CA] block tracking-wider">
                Suitability Score
              </span>
              <span className="text-3xl font-black text-white font-mono">
                {Number(data.score).toFixed(0)}
                <span className="text-sm font-normal text-[#FFD0CA]"> / 100</span>
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Authoritative Disclaimer Banner (Principle 17 & SIH Compliance) */}
      <div className="bg-[#FFF4EC] border-b border-[#FFD0CA] px-6 py-3 flex items-start gap-3 text-[#4A2525] text-xs">
        <Info className="w-4 h-4 text-[#EA717B] shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-bold">{t('calculator.selfDeclaredAdvisory', 'Self-Declared Advisory Only:')} </span>
          <span>
            This assessment is calculated deterministically from your self-declared income, project cost, and loan requirements.
            YojnaSetu does not access, verify, or store bank account records or credit bureau reports. Official lending decisions rest solely with the channel bank or government authority.
          </span>
        </div>
      </div>

      {/* Main Body */}
      <div className="p-6 space-y-6">
        {error && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {isLoading && !data && (
          <div className="py-12 text-center text-[#765E59] text-xs flex flex-col items-center gap-2">
            <RefreshCw className="w-6 h-6 animate-spin text-[#EA717B]" />
            <span>{t('calculator.evaluatingParams', 'Evaluating deterministic financial parameters...')}</span>
          </div>
        )}

        {data && (
          <>
            {/* Status & Headline Banner */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-2xl border border-[#E8D8D2] bg-[#FFFBF0]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white border border-[#E8D8D2] shadow-warm-xs flex items-center justify-center shrink-0">
                  <StatusIcon className={`w-6 h-6 ${statusInfo.iconColor}`} />
                </div>
                <div>
                  <span className={`inline-block text-[11px] font-extrabold px-2.5 py-0.5 rounded-full border mb-1 ${statusInfo.bg}`}>
                    {statusInfo.label}
                  </span>
                  <h4 className="text-sm font-bold text-[#3B2522]">
                    {data.summary_headline}
                  </h4>
                </div>
              </div>

              <div className="text-[11px] text-[#765E59]/70 font-mono shrink-0">
                Algorithm: {data.calculation_version}
              </div>
            </div>

            {/* Core Monthly Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
              <div className="bg-white p-3 rounded-xl border border-[#E8D8D2] shadow-warm-xs">
                <span className="text-[10px] font-bold uppercase text-[#765E59] block tracking-wider">
                  {t('calculator.monthlyIncome', 'Monthly Income')}
                </span>
                <span className="text-sm sm:text-base font-extrabold text-[#3B2522] font-mono block mt-0.5">
                  {data.monthly_income ? `₹${Number(data.monthly_income).toLocaleString('en-IN')}` : 'Not Specified'}
                </span>
                <span className="text-[9px] text-[#765E59]">{t('calculator.totalFamilyEarnings', 'Total family earnings')}</span>
              </div>

              <div className="bg-white p-3 rounded-xl border border-[#E8D8D2] shadow-warm-xs">
                <span className="text-[10px] font-bold uppercase text-[#765E59] block tracking-wider">
                  {t('calculator.monthlyExpenses', 'Monthly Expenses')}
                </span>
                <span className="text-sm sm:text-base font-extrabold text-[#765E59] font-mono block mt-0.5">
                  {data.monthly_expenses !== undefined && data.monthly_expenses !== null
                    ? `₹${Number(data.monthly_expenses).toLocaleString('en-IN')}`
                    : 'Not Specified'}
                </span>
                <span className="text-[9px] text-[#765E59]">{t('calculator.livingBusinessCosts', 'Living / business costs')}</span>
              </div>

              <div className="bg-white p-3 rounded-xl border border-[#E8D8D2] shadow-warm-xs">
                <span className="text-[10px] font-bold uppercase text-[#765E59] block tracking-wider">
                  {t('calculator.existingEmis', 'Existing EMIs')}
                </span>
                <span className="text-sm sm:text-base font-extrabold text-[#765E59] font-mono block mt-0.5">
                  {data.existing_monthly_obligations !== undefined && data.existing_monthly_obligations !== null
                    ? `₹${Number(data.existing_monthly_obligations).toLocaleString('en-IN')}`
                    : '₹0'}
                </span>
                <span className="text-[9px] text-[#765E59]">{t('calculator.currentLoanObligations', 'Current loan obligations')}</span>
              </div>

              <div className="bg-white p-3 rounded-xl border border-[#E8D8D2] shadow-warm-xs">
                <span className="text-[10px] font-bold uppercase text-[#765E59] block tracking-wider">
                  {t('calculator.standardEmi', 'Proposed EMI')}
                </span>
                <span className="text-sm sm:text-base font-extrabold text-[#EA717B] font-mono block mt-0.5">
                  {data.proposed_monthly_emi !== undefined && data.proposed_monthly_emi !== null
                    ? `₹${Number(data.proposed_monthly_emi).toLocaleString('en-IN')}`
                    : 'N/A'}
                </span>
                <span className="text-[9px] text-[#765E59]">{t('calculator.estimatedNewEmi', 'Estimated new loan EMI')}</span>
              </div>

              <div className="bg-white p-3 rounded-xl border border-[#E8D8D2] shadow-warm-xs">
                <span className="text-[10px] font-bold uppercase text-[#765E59] block tracking-wider">
                  {t('calculator.repaymentObligation', 'Repayment Burden')}
                </span>
                <span className={`text-sm sm:text-base font-extrabold font-mono block mt-0.5 ${
                  data.debt_to_income_ratio && Number(data.debt_to_income_ratio) > 50 ? 'text-rose-600' : 'text-[#3B2522]'
                }`}>
                  {data.debt_to_income_ratio !== undefined && data.debt_to_income_ratio !== null
                    ? `${Number(data.debt_to_income_ratio).toFixed(1)}%`
                    : 'N/A'}
                </span>
                <span className="text-[9px] text-[#765E59]">{t('calculator.debtToIncomeRatio', 'Debt to income ratio')}</span>
              </div>

              <div className="bg-white p-3 rounded-xl border border-[#E8D8D2] shadow-warm-xs">
                <span className="text-[10px] font-bold uppercase text-[#765E59] block tracking-wider">
                  {t('calculator.disposableCushion', 'Disposable Cushion')}
                </span>
                <span className={`text-sm sm:text-base font-extrabold font-mono block mt-0.5 ${
                  Number(data.estimated_disposable_income || 0) > 0 ? 'text-emerald-700' : 'text-rose-600'
                }`}>
                  {data.estimated_disposable_income !== null && data.estimated_disposable_income !== undefined
                    ? `₹${Number(data.estimated_disposable_income).toLocaleString('en-IN')}`
                    : 'Not Specified'}
                </span>
                <span className="text-[9px] text-[#765E59]">{t('calculator.remainingPostEmi', 'Remaining post-EMI / month')}</span>
              </div>
            </div>

            {/* Evaluated Indicators List */}
            {data.indicators && data.indicators.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-xs font-extrabold text-[#3B2522] uppercase tracking-wider">
                  Evaluated Financial Indicators
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {data.indicators.map((ind: FinancialIndicatorResult, i: number) => {
                    const isHealthy = ind.status === 'HEALTHY';
                    const isMod = ind.status === 'MODERATE';
                    const isStressed = ind.status === 'STRESSED' || ind.status === 'HIGH_RISK';

                    return (
                      <div
                        key={i}
                        className={`p-4 rounded-2xl border space-y-2 transition ${
                          isHealthy
                            ? 'bg-emerald-50/50 border-emerald-200'
                            : isMod
                            ? 'bg-[#FFF4EC] border-[#FFD0CA]'
                            : isStressed
                            ? 'bg-amber-50/50 border-amber-200'
                            : 'bg-[#FFFBF0] border-[#E8D8D2]'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="text-xs font-bold text-[#3B2522] block">
                              {ind.label}
                            </span>
                            <span className="text-[10px] text-[#765E59] font-medium">
                              Benchmark: {ind.benchmark}
                            </span>
                          </div>
                          <span
                            className={`text-xs font-mono font-black px-2 py-0.5 rounded-lg border ${
                              isHealthy
                                ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                                : isMod
                                ? 'bg-[#FFD0CA] text-[#4A2525] border-[#EA717B]/30'
                                : 'bg-amber-100 text-amber-800 border-amber-300'
                            }`}
                          >
                            {ind.formatted_value}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#765E59] leading-relaxed">
                          {ind.explanation}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Positive Factors & Risk Flags */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {data.positive_factors && data.positive_factors.length > 0 && (
                <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200 space-y-2">
                  <span className="text-xs font-extrabold text-emerald-900 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Borrowing Strengths
                  </span>
                  <ul className="space-y-1">
                    {data.positive_factors.map((factor: string, i: number) => (
                      <li key={i} className="text-[11px] text-[#765E59] flex items-start gap-1.5">
                        <span className="text-emerald-600 font-bold">•</span>
                        <span>{factor}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {data.risk_flags && data.risk_flags.length > 0 && (
                <div className="p-4 rounded-2xl bg-rose-50/60 border border-rose-200 space-y-2">
                  <span className="text-xs font-extrabold text-rose-900 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    Cautionary Stress Signals
                  </span>
                  <ul className="space-y-1">
                    {data.risk_flags.map((flag: string, i: number) => (
                      <li key={i} className="text-[11px] text-[#765E59] flex items-start gap-1.5">
                        <span className="text-rose-600 font-bold">•</span>
                        <span>{flag}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Actionable Recommendations */}
            {data.recommendations && data.recommendations.length > 0 && (
              <div className="p-4 rounded-2xl bg-[#FFF4EC] border border-[#FFD0CA] space-y-2">
                <span className="text-xs font-extrabold text-[#4A2525] flex items-center gap-1.5">
                  <TrendingUp className="w-4 h-4 text-[#EA717B]" />
                  Prudent Financial Next Steps
                </span>
                <ul className="space-y-1.5">
                  {data.recommendations.map((rec: string, i: number) => (
                    <li key={i} className="text-[11px] text-[#3B2522] flex items-start gap-2 leading-relaxed">
                      <ArrowRight className="w-3.5 h-3.5 text-[#EA717B] shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Missing Fields Notice */}
            {data.missing_fields && data.missing_fields.length > 0 && (
              <div className="p-4 rounded-2xl bg-[#FFFBF0] border border-[#E8D8D2] text-xs space-y-1.5">
                <div className="font-bold text-[#4A2525] flex items-center gap-1.5">
                  <HelpCircle className="w-4 h-4 text-[#F7AE56]" />
                  <span>{t('calculator.additionalParamsPrecision', 'Additional Parameters To Improve Assessment Precision:')}</span>
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                  {data.missing_fields.map((mf, idx) => (
                    <span
                      key={idx}
                      className="bg-white border border-[#E8D8D2] text-[#4A2525] text-[11px] font-semibold px-2.5 py-0.5 rounded-lg shadow-warm-xs"
                      title={mf.impact_reason}
                    >
                      • {mf.label}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
