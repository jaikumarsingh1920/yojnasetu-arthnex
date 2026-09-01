import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { schemeApi } from '../api/schemeApi';
import { SchemeComparisonResponse, SchemeComparisonItem, Scheme } from '../types';
import { useComparison } from '../context/ComparisonContext';
import { useAuth } from '../context/AuthContext';
import { SaveSchemeButton } from '../components/SaveSchemeButton';
import {
  Scale,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Calculator,
  ExternalLink,
  MapPin,
  FileText,
  Building2,
  ShieldCheck,
  Plus,
  X,
  Sparkles,
  Info,
  Layers,
  Banknote,
  SendHorizontal,
  Bookmark,
} from 'lucide-react';

interface ComparisonFeatureRowProps {
  label: string;
  icon?: React.ReactNode;
  hint?: string;
  items: SchemeComparisonItem[];
  renderValue: (item: SchemeComparisonItem, index: number) => React.ReactNode;
  isLast?: boolean;
}

const ComparisonFeatureRow: React.FC<ComparisonFeatureRowProps> = ({
  label,
  icon,
  hint,
  items,
  renderValue,
  isLast = false,
}) => {
  const colCount = items.length;

  // Grid column class mapping for tablet/desktop
  const getGridColsClass = () => {
    switch (colCount) {
      case 2:
        return 'md:grid-cols-2';
      case 3:
        return 'md:grid-cols-3';
      case 4:
        return 'md:grid-cols-4';
      default:
        return 'md:grid-cols-2';
    }
  };

  return (
    <div
      className={`py-4 ${
        !isLast ? 'border-b border-slate-100' : ''
      } flex flex-col md:flex-row md:items-start transition-colors hover:bg-slate-50/50 -mx-4 sm:-mx-6 px-4 sm:px-6`}
    >
      {/* Parameter Label (Left on desktop/tablet, Top on mobile) */}
      <div className="w-full md:w-56 shrink-0 md:pr-6 mb-2 md:mb-0">
        <div className="flex items-center gap-1.5">
          {icon && <span className="text-slate-400 shrink-0">{icon}</span>}
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">{label}</span>
        </div>
        {hint && <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">{hint}</p>}
      </div>

      {/* Scheme Values (Right on desktop/tablet, stacked / mini-grid on mobile) */}
      <div className={`w-full flex-1 grid grid-cols-1 ${colCount === 2 ? 'sm:grid-cols-2' : ''} ${getGridColsClass()} gap-3 sm:gap-4`}>
        {items.map((item, index) => (
          <div
            key={item.scheme.scheme_id}
            className="bg-slate-50/70 sm:bg-transparent p-2.5 sm:p-0 rounded-xl sm:rounded-none border border-slate-200/60 sm:border-0"
          >
            {/* Scheme identification badge on mobile if > 2 schemes or small screens */}
            <div className="flex items-center justify-between gap-1 mb-1 sm:hidden">
              <span className="text-[10px] font-mono font-bold text-gov-blue bg-gov-blue/10 px-1.5 py-0.5 rounded">
                {item.scheme.scheme_code || item.scheme.scheme_id}
              </span>
              <span className="text-[10px] text-slate-500 font-medium truncate max-w-[150px]">
                {item.scheme.scheme_name}
              </span>
            </div>

            {/* Rendered Value */}
            <div className="text-xs text-slate-800 leading-relaxed font-normal">
              {renderValue(item, index)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

interface ComparisonSectionCardProps {
  title: string;
  icon: React.ReactNode;
  subtitle?: string;
  badge?: string;
  children: React.ReactNode;
}

const ComparisonSectionCard: React.FC<ComparisonSectionCardProps> = ({
  title,
  icon,
  subtitle,
  badge,
  children,
}) => {
  return (
    <section className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden mb-6 last:mb-0">
      {/* Card Header */}
      <div className="px-5 sm:px-6 py-4 bg-slate-50/90 border-b border-slate-200/80 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white rounded-xl border border-slate-200/80 shadow-xs text-gov-blue">
            {icon}
          </div>
          <div>
            <h2 className="text-sm sm:text-base font-bold text-slate-900">{title}</h2>
            {subtitle && <p className="text-[11px] text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
        </div>

        {badge && (
          <span className="text-[10px] font-bold text-gov-blue bg-gov-blue/10 px-2.5 py-1 rounded-full border border-gov-blue/20">
            {badge}
          </span>
        )}
      </div>

      {/* Card Content Rows */}
      <div className="px-5 sm:px-6 py-2">{children}</div>
    </section>
  );
};

export const Compare: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  const { selectedSchemeIds, removeSchemeFromCompare, clearComparison } = useComparison();

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [comparisonData, setComparisonData] = useState<SchemeComparisonResponse | null>(null);

  // Extract scheme IDs from URL params e.g. ?schemes=SIH26092-001,SIH26092-053
  const urlSchemesParam = searchParams.get('schemes') || '';
  const schemeIdsFromUrl = urlSchemesParam
    ? urlSchemesParam.split(',').map((s) => s.trim()).filter(Boolean)
    : [];

  useEffect(() => {
    // If URL has scheme IDs, load comparison data
    if (schemeIdsFromUrl.length > 0) {
      fetchComparison(schemeIdsFromUrl);
    } else if (selectedSchemeIds.length > 0) {
      // Sync URL with context selected ids if no url params present
      setSearchParams({ schemes: selectedSchemeIds.join(',') }, { replace: true });
    } else {
      setLoading(false);
      setComparisonData(null);
    }
  }, [urlSchemesParam]);

  const fetchComparison = async (ids: string[]) => {
    setLoading(true);
    setError(null);
    try {
      const data = await schemeApi.getComparison(ids);
      setComparisonData(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load scheme comparison data.');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveScheme = (schemeId: string) => {
    removeSchemeFromCompare(schemeId);
    const updated = schemeIdsFromUrl.filter((id) => id !== schemeId);
    if (updated.length > 0) {
      setSearchParams({ schemes: updated.join(',') });
    } else {
      setSearchParams({});
    }
  };

  const handleClearAll = () => {
    clearComparison();
    setSearchParams({});
  };

  const items: SchemeComparisonItem[] = comparisonData?.compared_schemes || [];

  // Helper functions for neutral comparison highlights
  const getMaxLoan = (item: SchemeComparisonItem): number => {
    return item.scheme.max_loan_amount || 0;
  };

  const getMinInterest = (item: SchemeComparisonItem): number => {
    return item.scheme.interest_rate_min || item.scheme.interest_rate || 999;
  };

  const maxLoanValue = Math.max(...items.map(getMaxLoan));
  const minInterestValue = Math.min(...items.map(getMinInterest));

  // Helper to format loan amounts
  const formatLoanAmount = (scheme: Scheme) => {
    if (scheme.is_credit_scheme === false || scheme.loan_available === 'NO') {
      return (
        <span className="text-slate-500 italic">
          {t('compare.notApplicable', 'Not applicable')} ({t('compare.noCreditWelfare', 'Grant / Subsidy Scheme')})
        </span>
      );
    }
    if (scheme.max_loan_amount && scheme.max_loan_amount > 0) {
      const isHighest = scheme.max_loan_amount === maxLoanValue && items.length > 1;
      return (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="font-bold text-slate-900 text-sm">
            ₹{scheme.max_loan_amount.toLocaleString('en-IN')}
          </span>
          {isHighest && (
            <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded border border-emerald-300">
              {t('compare.highestStated', 'Highest stated')}
            </span>
          )}
        </div>
      );
    }
    if (scheme.max_loan_amount_raw) {
      return <span className="font-bold text-slate-900">{scheme.max_loan_amount_raw}</span>;
    }
    return (
      <span className="text-slate-400 italic">
        {t('common.notSpecifiedInOfficialData', 'Not specified in available official data')}
      </span>
    );
  };

  // Helper to format interest rate
  const formatInterestRate = (scheme: Scheme) => {
    if (scheme.is_credit_scheme === false || scheme.loan_available === 'NO') {
      return <span className="text-slate-500 italic">{t('compare.notApplicable', 'Not applicable')}</span>;
    }
    const minRate = scheme.interest_rate_min || scheme.interest_rate;
    const maxRate = scheme.interest_rate_max;
    if (minRate) {
      const isLowest = minRate < 999 && minRate === minInterestValue && items.length > 1;
      return (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="font-bold text-slate-900 text-sm">
            {minRate}%{maxRate ? ` – ${maxRate}%` : ''} p.a.
          </span>
          {isLowest && (
            <span className="text-[10px] bg-blue-100 text-blue-800 font-bold px-2 py-0.5 rounded border border-blue-300">
              {t('compare.lowestStated', 'Lowest stated')}
            </span>
          )}
        </div>
      );
    }
    return (
      <span className="text-slate-400 italic">
        {t('common.notSpecifiedInOfficialData', 'Not specified in available official data')}
      </span>
    );
  };

  // Helper to format repayment tenure
  const formatTenure = (scheme: Scheme) => {
    if (scheme.is_credit_scheme === false || scheme.loan_available === 'NO') {
      return <span className="text-slate-500 italic">{t('compare.notApplicable', 'Not applicable')}</span>;
    }
    const months = scheme.repayment_period_months || scheme.repayment_period_max_months;
    if (months && months > 0) {
      const years = (months / 12).toFixed(1).replace('.0', '');
      return (
        <span className="font-semibold text-slate-900">
          {months} {t('compare.months', 'months')} ({years} {t('compare.years', 'years')})
        </span>
      );
    }
    return (
      <span className="text-slate-400 italic">
        {t('common.notSpecifiedInOfficialData', 'Not specified in available official data')}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 py-6 sm:py-8 px-4 sm:px-6 lg:px-8 pb-24">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header Breadcrumb & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 sm:p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div>
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-gov-blue mb-2 transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>{t('compare.back', 'Back')}</span>
            </button>
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-gov-blue/10 rounded-xl text-gov-blue">
                <Scale className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">
                  {t('compare.compareSchemes', 'Compare Schemes')}
                </h1>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  {t('compare.selectUpTo4', 'Compare 2 to 4 schemes side-by-side in clear vertical sections.')}
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5 self-end sm:self-center">
            {items.length > 0 && (
              <button
                type="button"
                onClick={handleClearAll}
                className="text-xs font-semibold text-slate-500 hover:text-red-600 px-3 py-2 rounded-xl border border-slate-200 hover:border-red-200 bg-slate-50 hover:bg-red-50 transition"
              >
                {t('compare.clearComparison', 'Clear All')}
              </button>
            )}
            <Link
              to="/schemes"
              className="inline-flex items-center gap-1.5 text-xs font-bold text-white bg-gov-blue hover:bg-gov-blue-dark px-4 py-2.5 rounded-xl shadow-xs transition"
            >
              <Plus className="w-4 h-4" />
              <span>{t('compare.addMore', 'Add Scheme')}</span>
            </Link>
          </div>
        </div>

        {/* Invalid Scheme IDs Notice */}
        {comparisonData?.invalid_ids && comparisonData.invalid_ids.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-3 text-amber-800 text-xs font-medium">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
            <span>
              {t('compare.invalidIdsNotice', 'Note: Some requested scheme IDs could not be found or are inactive:')}{' '}
              <strong className="font-mono">{comparisonData.invalid_ids.join(', ')}</strong>
            </span>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4 shadow-sm">
            <div className="w-8 h-8 border-4 border-gov-blue border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm font-semibold text-slate-600">
              {t('compare.loading', 'Fetching official scheme comparison data...')}
            </p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center space-y-3">
            <AlertTriangle className="w-8 h-8 text-red-500 mx-auto" />
            <h3 className="text-base font-bold text-red-900">{t('compare.errorTitle', 'Unable to Compare Schemes')}</h3>
            <p className="text-xs text-red-700">{error}</p>
            <button
              type="button"
              onClick={() => fetchComparison(schemeIdsFromUrl)}
              className="text-xs font-bold text-white bg-red-600 hover:bg-red-700 px-4 py-2 rounded-xl"
            >
              {t('compare.retry', 'Try Again')}
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && items.length === 0 && (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4 shadow-sm">
            <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto text-slate-400">
              <Scale className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">{t('compare.emptyTitle', 'No Schemes Selected for Comparison')}</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              {t('compare.emptyDesc', 'Select 2 to 4 schemes from Scheme Discovery or Recommendations to view a side-by-side comparison.')}
            </p>
            <Link
              to="/schemes"
              className="inline-block bg-gov-blue text-white font-bold text-xs px-6 py-3 rounded-xl shadow hover:bg-gov-blue-dark transition"
            >
              {t('compare.browseSchemes', 'Browse Schemes')}
            </Link>
          </div>
        )}

        {/* COMPARISON CONTENT */}
        {!loading && !error && items.length > 0 && (
          <div className="space-y-6">
            {/* SCHEMES HEADER CARDS */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  {t('compare.comparing', 'Comparing')} ({items.length} {t('compare.compareSchemes', 'Schemes')})
                </span>
                <span className="text-xs text-slate-400 font-medium hidden sm:inline">
                  {items.map((i) => i.scheme.scheme_code || i.scheme.scheme_id).join(' vs ')}
                </span>
              </div>

              <div
                className={`grid grid-cols-1 sm:grid-cols-2 ${
                  items.length === 3 ? 'lg:grid-cols-3' : items.length >= 4 ? 'lg:grid-cols-4' : 'lg:grid-cols-2'
                } gap-4`}
              >
                {items.map(({ scheme }) => (
                  <div
                    key={scheme.scheme_id}
                    className="relative bg-slate-50/80 p-4 rounded-xl border border-slate-200/80 flex flex-col justify-between hover:border-slate-300 transition"
                  >
                    {/* Remove button */}
                    <button
                      type="button"
                      onClick={() => handleRemoveScheme(scheme.scheme_id)}
                      className="absolute top-3 right-3 text-slate-400 hover:text-red-500 p-1 rounded-md hover:bg-white transition"
                      title={t('compare.removeScheme', 'Remove')}
                    >
                      <X className="w-4 h-4" />
                    </button>

                    <div>
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-[10px] font-mono font-bold text-gov-blue bg-gov-blue/10 px-2 py-0.5 rounded">
                          {scheme.scheme_code || scheme.scheme_id}
                        </span>
                        {scheme.is_credit_scheme ? (
                          <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">
                            {t('compare.loanAvailable', 'Credit')}
                          </span>
                        ) : (
                          <span className="text-[10px] font-bold text-slate-600 bg-slate-200 px-1.5 py-0.5 rounded">
                            {t('compare.noCreditWelfare', 'Welfare')}
                          </span>
                        )}
                      </div>

                      <h3 className="text-xs sm:text-sm font-bold text-slate-900 line-clamp-2 pr-6">
                        {scheme.scheme_name}
                      </h3>

                      <p className="text-[11px] text-slate-500 mt-1 line-clamp-1">
                        {scheme.ministry || 'Government of India'}
                      </p>
                    </div>

                    {/* Quick Scheme Actions */}
                    <div className="mt-3 pt-3 border-t border-slate-200/70 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <SaveSchemeButton schemeId={scheme.scheme_id} size="sm" />
                        <Link
                          to={`/schemes/${scheme.scheme_id}`}
                          className="text-[11px] font-bold text-gov-blue hover:underline flex items-center gap-1"
                        >
                          <span>{t('compare.details', 'Details')}</span>
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      </div>

                      {scheme.calculator_applicable !== false && scheme.is_credit_scheme !== false && (
                        <Link
                          to={`/calculator?scheme_id=${scheme.scheme_id}`}
                          className="text-[10px] font-bold text-emerald-700 hover:text-emerald-800 bg-emerald-50 hover:bg-emerald-100 px-2 py-1 rounded-md border border-emerald-200 flex items-center gap-1 transition"
                        >
                          <Calculator className="w-3 h-3" />
                          <span>{t('compare.openCalculator', 'EMI')}</span>
                        </Link>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* CARD 0: PERSONALIZED ELIGIBILITY (IF ASSESSED OR USER LOGGED IN) */}
            <ComparisonSectionCard
              title={t('compare.secPersonalized', 'Your Eligibility Fit')}
              icon={<Sparkles className="w-5 h-5 text-emerald-500" />}
              subtitle={
                user
                  ? t('compare.profileAssessmentSubtitle', 'Automated assessment based on your registered citizen profile')
                  : t('compare.loginNotice', 'Sign in to automatically evaluate your eligibility against each scheme')
              }
              badge={user ? t('common.personalized', 'Personalized') : undefined}
            >
              <ComparisonFeatureRow
                label={t('compare.eligibilityStatus', 'Eligibility Status')}
                items={items}
                isLast={true}
                renderValue={({ scheme, personalized_eligibility }) => {
                  if (!personalized_eligibility) {
                    return (
                      <div className="text-[11px] text-slate-500 italic bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                        {user
                          ? t('compare.profileIncompleteNotice', 'Complete your profile to view eligibility status.')
                          : t('compare.loginRequired', 'Log in to evaluate personalized eligibility.')}
                      </div>
                    );
                  }

                  return (
                    <div className="space-y-2">
                      {personalized_eligibility.status === 'ELIGIBLE' && (
                        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 font-bold border border-emerald-300">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          <span>{t('compare.eligible', '✓ Eligible')}</span>
                        </div>
                      )}
                      {personalized_eligibility.status === 'INSUFFICIENT_INFORMATION' && (
                        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-100 text-amber-800 font-bold border border-amber-300">
                          <AlertTriangle className="w-4 h-4 text-amber-600" />
                          <span>{t('compare.moreInfoRequired', '⚠ More Info Required')}</span>
                        </div>
                      )}
                      {personalized_eligibility.status === 'INELIGIBLE' && (
                        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-100 text-red-800 font-bold border border-red-300">
                          <XCircle className="w-4 h-4 text-red-600" />
                          <span>{t('compare.ineligible', '✕ Not Eligible')}</span>
                        </div>
                      )}

                      {personalized_eligibility.reasons && personalized_eligibility.reasons.length > 0 && (
                        <ul className="text-[11px] text-slate-600 space-y-1 mt-2 list-disc list-inside">
                          {personalized_eligibility.reasons.slice(0, 3).map((r, i) => (
                            <li key={i}>{r}</li>
                          ))}
                        </ul>
                      )}

                      {personalized_eligibility.missing_fields && personalized_eligibility.missing_fields.length > 0 && (
                        <div className="mt-2 text-[11px] text-amber-800 bg-amber-50 p-2 rounded-lg border border-amber-200">
                          <strong>{t('compare.missingAttrs', 'Missing attributes:')}</strong>
                          <div className="capitalize">{personalized_eligibility.missing_fields.join(', ')}</div>
                        </div>
                      )}
                    </div>
                  );
                }}
              />
            </ComparisonSectionCard>

            {/* CARD 1: SCHEME OVERVIEW */}
            <ComparisonSectionCard
              title={t('compare.secOverview', 'Scheme Overview')}
              icon={<Building2 className="w-5 h-5 text-gov-blue" />}
              subtitle={t('compare.secOverviewSubtitle', 'Core mandate, ministry sponsoring body, and geographical scope')}
            >
              <ComparisonFeatureRow
                label={t('compare.schemeType', 'Scheme Type')}
                items={items}
                renderValue={({ scheme }) => (
                  <span className="inline-block px-2.5 py-1 rounded-md bg-slate-100 text-slate-800 border border-slate-200 text-[11px] font-bold">
                    {scheme.financial_category ? scheme.financial_category.replace(/_/g, ' ') : scheme.scheme_type || 'CREDIT / LOAN'}
                  </span>
                )}
              />

              <ComparisonFeatureRow
                label={t('compare.ministry', 'Ministry / Department')}
                items={items}
                renderValue={({ scheme }) => (
                  <div>
                    <div className="font-semibold text-slate-900">{scheme.ministry || 'Government of India'}</div>
                    {scheme.implementing_agency && (
                      <div className="text-[11px] text-slate-500 mt-0.5 font-medium">{scheme.implementing_agency}</div>
                    )}
                  </div>
                )}
              />

              <ComparisonFeatureRow
                label={t('compare.targetBeneficiary', 'Target Beneficiary')}
                items={items}
                renderValue={({ scheme }) => (
                  <span className="font-medium text-slate-800">
                    {scheme.target_beneficiary || scheme.target_groups || t('compare.generalCitizens', 'General Citizens')}
                  </span>
                )}
              />

              <ComparisonFeatureRow
                label={t('compare.schemePurpose', 'Scheme Purpose & Benefits')}
                items={items}
                renderValue={({ scheme }) => (
                  <p className="text-[11px] text-slate-600 line-clamp-3">
                    {scheme.financial_assistance_summary || scheme.benefit_description || scheme.short_description || scheme.purpose || t('compare.noneSpecified', 'Refer to official scheme guidelines')}
                  </p>
                )}
              />

              <ComparisonFeatureRow
                label={t('compare.geographicCoverage', 'Geographic Coverage')}
                items={items}
                isLast={true}
                renderValue={({ scheme }) => (
                  <div className="flex items-center gap-1.5 font-medium text-slate-800">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>
                      {scheme.state_restriction && scheme.state_restriction !== 'ALL_INDIA'
                        ? scheme.state_restriction.replace(/_/g, ' ')
                        : t('compare.allIndia', 'All India / Central Scheme')}
                    </span>
                  </div>
                )}
              />
            </ComparisonSectionCard>

            {/* CARD 2: ELIGIBILITY CRITERIA */}
            <ComparisonSectionCard
              title={t('compare.secEligibility', 'Eligibility Criteria')}
              icon={<ShieldCheck className="w-5 h-5 text-gov-blue" />}
              subtitle={t('compare.secEligibilitySubtitle', 'Age, income, social category, and vocational qualification')}
            >
              <ComparisonFeatureRow
                label={t('compare.ageCriteria', 'Age Criteria')}
                items={items}
                renderValue={({ scheme }) => {
                  if (scheme.min_age || scheme.max_age) {
                    return (
                      <span className="font-semibold text-slate-900">
                        {scheme.min_age ? `Min ${scheme.min_age} yrs` : ''}
                        {scheme.min_age && scheme.max_age ? ' – ' : ''}
                        {scheme.max_age ? `Max ${scheme.max_age} yrs` : ''}
                      </span>
                    );
                  }
                  return (
                    <span className="text-slate-400 italic">
                      {t('common.notSpecifiedInOfficialData', 'Not specified in available official data')}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.incomeLimit', 'Income Limit / Ceiling')}
                items={items}
                renderValue={({ scheme }) => {
                  const incomeRule = scheme.rules?.find((r) => r.field.includes('income'));
                  if (incomeRule) {
                    return (
                      <span className="font-semibold text-slate-900">
                        {incomeRule.description || `${incomeRule.operator} ₹${incomeRule.value}/year`}
                      </span>
                    );
                  }
                  return (
                    <span className="text-slate-500 font-medium">
                      {t('compare.noIncomeLimit', 'No mandatory income ceiling specified')}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.socialCategory', 'Social Category & Gender')}
                items={items}
                renderValue={({ scheme }) => {
                  const genderRule = scheme.rules?.find((r) => r.field === 'gender');
                  return (
                    <div>
                      <span className="font-semibold text-slate-900">
                        {scheme.marginalized_group || scheme.target_groups || t('compare.allCategories', 'All Categories')}
                      </span>
                      {genderRule && (
                        <div className="text-[11px] text-slate-500 font-medium mt-0.5">
                          Gender: {genderRule.value}
                        </div>
                      )}
                    </div>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.occupation', 'Sector / Vocation')}
                items={items}
                renderValue={({ scheme }) => (
                  <span className="font-semibold text-slate-900">
                    {scheme.sector ? scheme.sector.replace(/_/g, ' ') : t('compare.allSectors', 'All Sectors')}
                  </span>
                )}
              />

              <ComparisonFeatureRow
                label={t('compare.otherConditions', 'Key Conditions')}
                items={items}
                isLast={true}
                renderValue={({ scheme }) => {
                  const rules = scheme.rules || [];
                  if (rules.length > 0) {
                    return (
                      <ul className="text-[11px] text-slate-600 space-y-1 list-disc list-inside">
                        {rules.slice(0, 2).map((r, i) => (
                          <li key={i}>{r.description || `${r.field.replace(/_/g, ' ')}: ${r.value}`}</li>
                        ))}
                      </ul>
                    );
                  }
                  return (
                    <span className="text-slate-500 text-[11px]">
                      {t('compare.standardOfficialNorms', 'Standard KYC and official ministry guidelines apply')}
                    </span>
                  );
                }}
              />
            </ComparisonSectionCard>

            {/* CARD 3: FINANCIAL ASSISTANCE & CREDIT TERMS */}
            <ComparisonSectionCard
              title={t('compare.secFinancial', 'Financial Assistance & Credit Terms')}
              icon={<Banknote className="w-5 h-5 text-gov-blue" />}
              subtitle={t('compare.secFinancialSubtitle', 'Credit ceiling, interest rates, tenure, subsidy, and collateral')}
            >
              <ComparisonFeatureRow
                label={t('compare.loanAvailable', 'Loan Facility Available')}
                items={items}
                renderValue={({ scheme }) => {
                  if (scheme.is_credit_scheme !== false && scheme.loan_available !== 'NO') {
                    return (
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded border border-emerald-300">
                        ✓ {t('compare.yes', 'Yes')} ({t('compare.creditFacility', 'Credit Facility')})
                      </span>
                    );
                  }
                  return (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-slate-700 bg-slate-100 px-2.5 py-0.5 rounded border border-slate-300">
                      ✕ {t('compare.noCreditWelfare', 'No — Grant / Subsidy / Welfare')}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.maxLoan', 'Maximum Stated Loan')}
                items={items}
                renderValue={({ scheme }) => formatLoanAmount(scheme)}
              />

              <ComparisonFeatureRow
                label={t('compare.interestRate', 'Interest Rate')}
                items={items}
                renderValue={({ scheme }) => formatInterestRate(scheme)}
              />

              <ComparisonFeatureRow
                label={t('compare.tenure', 'Repayment Tenure')}
                items={items}
                renderValue={({ scheme }) => formatTenure(scheme)}
              />

              <ComparisonFeatureRow
                label={t('compare.moratorium', 'Moratorium Period')}
                items={items}
                renderValue={({ scheme }) => {
                  if (scheme.is_credit_scheme === false || scheme.loan_available === 'NO') {
                    return <span className="text-slate-500 italic">{t('compare.notApplicable', 'Not applicable')}</span>;
                  }
                  if (scheme.moratorium_period_months && scheme.moratorium_period_months > 0) {
                    return (
                      <span className="font-semibold text-slate-900">
                        {scheme.moratorium_period_months} {t('compare.months', 'months')}
                      </span>
                    );
                  }
                  return (
                    <span className="text-slate-400 italic">
                      {t('common.notSpecifiedInOfficialData', 'Not specified in available official data')}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.subsidy', 'Subsidy / Grant Assistance')}
                items={items}
                renderValue={({ scheme }) => {
                  if (scheme.subsidy_percentage && scheme.subsidy_percentage > 0) {
                    return (
                      <span className="font-bold text-emerald-800">
                        Up to {scheme.subsidy_percentage}%{' '}
                        {scheme.max_subsidy_amount ? `(Max ₹${scheme.max_subsidy_amount.toLocaleString('en-IN')})` : ''}
                      </span>
                    );
                  }
                  if (scheme.max_subsidy_amount && scheme.max_subsidy_amount > 0) {
                    return (
                      <span className="font-bold text-emerald-800">
                        Up to ₹{scheme.max_subsidy_amount.toLocaleString('en-IN')}
                      </span>
                    );
                  }
                  if (scheme.grant_amount && scheme.grant_amount > 0) {
                    return (
                      <span className="font-bold text-emerald-800">
                        Grant: ₹{scheme.grant_amount.toLocaleString('en-IN')}
                      </span>
                    );
                  }
                  return (
                    <span className="text-slate-500 font-medium">
                      {scheme.is_credit_scheme ? t('compare.interestSubvention', 'Direct interest subvention / credit guarantee') : t('compare.grantAssistance', 'Direct benefit transfer / non-loan subsidy')}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.marginMoney', 'Beneficiary Contribution')}
                items={items}
                renderValue={({ scheme }) => {
                  if (scheme.financing_percentage && scheme.financing_percentage > 0 && scheme.financing_percentage < 100) {
                    return (
                      <span className="font-semibold text-slate-900">
                        {100 - scheme.financing_percentage}% of project cost
                      </span>
                    );
                  }
                  return (
                    <span className="text-slate-500 font-medium">
                      {t('compare.standardMarginMoney', 'Standard 5% - 10% or as per lending institution')}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.collateral', 'Collateral Requirement')}
                items={items}
                renderValue={({ scheme }) => {
                  if (scheme.collateral_required === 'NO' || scheme.collateral_required === 'NONE') {
                    return (
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        {t('compare.noCollateral', 'No collateral required (Credit Guarantee covered)')}
                      </span>
                    );
                  }
                  if (scheme.collateral_required) {
                    return <span className="font-medium text-slate-800">{scheme.collateral_required}</span>;
                  }
                  return (
                    <span className="text-slate-500 font-medium">
                      {t('compare.collateralNorms', 'No collateral for loans up to statutory limits (RBI guidelines)')}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.calculatorAction', 'Calculator')}
                items={items}
                isLast={true}
                renderValue={({ scheme }) => {
                  if (scheme.calculator_applicable !== false && scheme.is_credit_scheme !== false) {
                    return (
                      <Link
                        to={`/calculator?scheme_id=${scheme.scheme_id}`}
                        className="inline-flex items-center gap-1.5 text-emerald-700 bg-emerald-50 hover:bg-emerald-100 font-bold px-3 py-1.5 rounded-lg border border-emerald-200 text-xs transition"
                      >
                        <Calculator className="w-3.5 h-3.5" />
                        <span>{t('compare.openCalculator', 'Calculate EMI')}</span>
                      </Link>
                    );
                  }
                  return (
                    <span className="text-slate-400 text-xs italic">
                      {t('compare.notApplicable', 'Not applicable')}
                    </span>
                  );
                }}
              />
            </ComparisonSectionCard>

            {/* CARD 4: DOCUMENTS */}
            <ComparisonSectionCard
              title={t('compare.secDocuments', 'Documents & Proofs')}
              icon={<FileText className="w-5 h-5 text-gov-blue" />}
              subtitle={t('compare.secDocumentsSubtitle', 'Mandatory identity, residence, business, and conditional proofs')}
            >
              <ComparisonFeatureRow
                label={t('compare.requiredDocs', 'Mandatory Documents')}
                items={items}
                renderValue={({ scheme }) => {
                  const docs = scheme.documents || [];
                  const reqDocs = docs.filter(
                    (d) => d.requirement_type === 'MANDATORY' || d.requirement_type === 'REQUIRED'
                  );

                  if (reqDocs.length > 0) {
                    return (
                      <ul className="space-y-1">
                        {reqDocs.map((d, i) => (
                          <li key={i} className="flex items-start gap-1.5 text-slate-700 text-[11px]">
                            <FileText className="w-3.5 h-3.5 text-gov-blue shrink-0 mt-0.5" />
                            <span>{d.document_name}</span>
                          </li>
                        ))}
                      </ul>
                    );
                  }

                  return (
                    <span className="text-slate-600 font-medium text-[11px]">
                      {scheme.required_documents || t('compare.noDocsRequired', 'Standard KYC & ID Proof only')}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.optionalDocs', 'Optional / Conditional Proofs')}
                items={items}
                isLast={true}
                renderValue={({ scheme }) => {
                  const docs = scheme.documents || [];
                  const optDocs = docs.filter(
                    (d) => d.requirement_type === 'OPTIONAL' || d.requirement_type === 'CONDITIONAL'
                  );

                  if (optDocs.length > 0) {
                    return (
                      <ul className="space-y-1">
                        {optDocs.map((d, i) => (
                          <li key={i} className="flex items-start gap-1.5 text-slate-600 text-[11px]">
                            <span className="text-slate-400">•</span>
                            <span>{d.document_name}</span>
                          </li>
                        ))}
                      </ul>
                    );
                  }

                  return (
                    <span className="text-slate-400 italic text-[11px]">
                      {t('compare.noOptionalDocs', 'No conditional documents specified')}
                    </span>
                  );
                }}
              />
            </ComparisonSectionCard>

            {/* CARD 5: APPLICATION & ACCESS */}
            <ComparisonSectionCard
              title={t('compare.secApplication', 'Application & Access Route')}
              icon={<SendHorizontal className="w-5 h-5 text-gov-blue" />}
              subtitle={t('compare.secApplicationSubtitle', 'Submission channels, authorized portal links, and channel partners')}
            >
              <ComparisonFeatureRow
                label={t('compare.applicationMode', 'Application Mode')}
                items={items}
                renderValue={({ scheme }) => (
                  <span className="font-semibold text-slate-900">
                    {scheme.application_mode || 'Online / Institutional'}
                  </span>
                )}
              />

              <ComparisonFeatureRow
                label={t('compare.applicationRoute', 'Application Route')}
                items={items}
                renderValue={({ scheme }) => {
                  if (scheme.application_route === 'DIRECT_PORTAL') {
                    return (
                      <span className="inline-flex items-center gap-1 font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200 text-[11px]">
                        <ExternalLink className="w-3.5 h-3.5" /> {t('compare.directOnlinePortal', 'Direct Online Portal')}
                      </span>
                    );
                  }
                  if (scheme.application_route === 'CHANNEL_PARTNER') {
                    return (
                      <span className="inline-flex items-center gap-1 font-bold text-indigo-800 bg-indigo-50 px-2.5 py-1 rounded-md border border-indigo-200 text-[11px]">
                        <Building2 className="w-3.5 h-3.5" /> {t('compare.channelPartner', 'Channel Partner / Agency')}
                      </span>
                    );
                  }
                  if (scheme.application_route === 'PARTNER_ASSISTED') {
                    return (
                      <span className="inline-flex items-center gap-1 font-bold text-blue-800 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200 text-[11px]">
                        <Building2 className="w-3.5 h-3.5" /> {t('compare.bankAssisted', 'Channel Partner / Bank Assisted')}
                      </span>
                    );
                  }
                  return (
                    <span className="text-slate-600 font-medium text-[11px]">
                      {t('compare.officialGovRoute', 'Official Government Route')}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.officialPortal', 'Official Portal')}
                items={items}
                renderValue={({ scheme }) => {
                  const portalUrl = scheme.official_portal || scheme.application_url;
                  if (portalUrl) {
                    return (
                      <a
                        href={portalUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 font-bold text-gov-blue hover:text-gov-blue-dark hover:underline text-xs"
                      >
                        <span className="truncate max-w-[180px] sm:max-w-[220px]">{portalUrl}</span>
                        <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                      </a>
                    );
                  }
                  return (
                    <span className="text-slate-400 italic">
                      {t('common.notSpecified', 'Not specified')}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.channelAgency', 'Implementing Agency')}
                items={items}
                renderValue={({ scheme }) => (
                  <span className="font-medium text-slate-800">
                    {scheme.implementing_agency || scheme.ministry || 'Government of India'}
                  </span>
                )}
              />

              <ComparisonFeatureRow
                label={t('compare.actionButton', 'Application CTA')}
                items={items}
                isLast={true}
                renderValue={({ scheme }) => {
                  const portalUrl = scheme.official_portal || scheme.application_url;
                  return (
                    <div className="flex flex-wrap items-center gap-2">
                      {portalUrl && (
                        <a
                          href={portalUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 font-bold text-white bg-gov-blue hover:bg-gov-blue-dark px-3.5 py-1.5 rounded-xl text-xs shadow-xs transition"
                        >
                          <span>{t('compare.applyOfficial', 'Official Portal')}</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                      <Link
                        to={`/channel-partners?scheme_id=${scheme.scheme_id}`}
                        className="inline-flex items-center gap-1.5 font-bold text-emerald-700 hover:text-emerald-800 bg-emerald-50 hover:bg-emerald-100 px-3 py-1.5 rounded-xl border border-emerald-200 text-xs transition"
                      >
                        <Building2 className="w-3.5 h-3.5" />
                        <span>{t('compare.locatePartners', 'Find Partners')}</span>
                      </Link>
                    </div>
                  );
                }}
              />
            </ComparisonSectionCard>

            {/* CARD 6: VERIFICATION & PROVENANCE */}
            <ComparisonSectionCard
              title={t('compare.secVerification', 'Verification & Official Coverage')}
              icon={<CheckCircle2 className="w-5 h-5 text-emerald-600" />}
              subtitle={t('compare.secVerificationSubtitle', 'Official gazette audit, statutory source validation, and update recency')}
            >
              <ComparisonFeatureRow
                label={t('compare.govVerification', 'Government Verification')}
                items={items}
                renderValue={({ scheme }) => (
                  <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded border border-emerald-300">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    <span>{scheme.verification_status || 'VERIFIED_OFFICIAL'}</span>
                  </span>
                )}
              />

              <ComparisonFeatureRow
                label={t('compare.officialSource', 'Official Source')}
                items={items}
                renderValue={({ scheme }) => {
                  if (scheme.official_source_url) {
                    return (
                      <a
                        href={scheme.official_source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gov-blue font-semibold hover:underline flex items-center gap-1 truncate max-w-[220px]"
                      >
                        <span className="truncate">{scheme.official_source_url}</span>
                        <ExternalLink className="w-3 h-3 shrink-0" />
                      </a>
                    );
                  }
                  return (
                    <span className="text-slate-400 italic">{t('common.notSpecified', 'Not specified')}</span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.lastVerified', 'Last Verified Date')}
                items={items}
                renderValue={() => (
                  <span className="font-mono text-slate-700 text-xs">
                    2026-09-01
                  </span>
                )}
              />

              <ComparisonFeatureRow
                label={t('compare.geographicCoverage', 'States/UTs')}
                items={items}
                isLast={true}
                renderValue={({ scheme }) => (
                  <span className="font-medium text-slate-800">
                    {scheme.state_restriction && scheme.state_restriction !== 'ALL_INDIA'
                      ? scheme.state_restriction.replace(/_/g, ' ')
                      : t('compare.allIndia', 'All India / Central Scheme')}
                  </span>
                )}
              />
            </ComparisonSectionCard>
          </div>
        )}
      </div>
    </div>
  );
};
