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
  Banknote,
  SendHorizontal,
  SlidersHorizontal,
  ChevronRight,
  Clock,
  HelpCircle,
} from 'lucide-react';

interface ComparisonFeatureRowProps {
  label: string;
  icon?: React.ReactNode;
  hint?: string;
  items: SchemeComparisonItem[];
  renderValue: (item: SchemeComparisonItem, index: number) => React.ReactNode;
  isLast?: boolean;
  isDifferent?: boolean;
  highlightDifferences?: boolean;
}

const ComparisonFeatureRow: React.FC<ComparisonFeatureRowProps> = ({
  label,
  icon,
  hint,
  items,
  renderValue,
  isLast = false,
  isDifferent = false,
  highlightDifferences = true,
}) => {
  const colCount = items.length;

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

  const showDiffBadge = highlightDifferences && isDifferent && items.length >= 2;

  return (
    <div
      className={`py-4 ${
        !isLast ? 'border-b border-[#E8D8D2]/60' : ''
      } flex flex-col md:flex-row md:items-start transition-colors ${
        showDiffBadge
          ? 'bg-[#FFF4EC]/80 border-l-2 border-l-[#F7AE56] pl-3 md:pl-4'
          : 'hover:bg-[#FFFBF0]/60'
      } -mx-4 sm:-mx-6 px-4 sm:px-6`}
    >
      {/* Parameter Label (Left on desktop/tablet, Top on mobile) */}
      <div className="w-full md:w-60 shrink-0 md:pr-6 mb-2 md:mb-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          {icon && <span className="text-[#765E59] shrink-0">{icon}</span>}
          <span className="text-xs font-bold text-[#3B2522] uppercase tracking-wider">{label}</span>
          {showDiffBadge && (
            <span className="text-[10px] font-semibold text-[#4A2525] bg-[#FFD0CA] border border-[#EA717B]/30 px-1.5 py-0.2 rounded-full tracking-wide">
              Differs
            </span>
          )}
        </div>
        {hint && <p className="text-[11px] text-[#765E59] mt-0.5 leading-snug">{hint}</p>}
      </div>

      {/* Scheme Values (Right on desktop/tablet, stacked / mini-grid on mobile) */}
      <div
        className={`w-full flex-1 grid grid-cols-1 ${
          colCount === 2 ? 'sm:grid-cols-2' : ''
        } ${getGridColsClass()} gap-3 sm:gap-4`}
      >
        {items.map((item, index) => (
          <div
            key={item.scheme.scheme_id}
            className="bg-[#FFFBF0] sm:bg-transparent p-2.5 sm:p-0 rounded-xl sm:rounded-none border border-[#E8D8D2] sm:border-0"
          >
            {/* Scheme identification badge on mobile */}
            <div className="flex items-center justify-between gap-1 mb-1 sm:hidden">
              <span className="text-[10px] font-mono font-bold text-[#4A2525] bg-[#FFD0CA] px-1.5 py-0.5 rounded">
                {item.scheme.scheme_code || item.scheme.scheme_id}
              </span>
              <span className="text-[10px] text-[#765E59] font-medium truncate max-w-[150px]">
                {item.scheme.scheme_name}
              </span>
            </div>

            {/* Rendered Value */}
            <div className="text-xs text-[#3B2522] leading-relaxed font-normal">
              {renderValue(item, index)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

interface ComparisonSectionCardProps {
  id?: string;
  title: string;
  icon: React.ReactNode;
  subtitle?: string;
  badge?: string;
  children: React.ReactNode;
}

const ComparisonSectionCard: React.FC<ComparisonSectionCardProps> = ({
  id,
  title,
  icon,
  subtitle,
  badge,
  children,
}) => {
  return (
    <section
      id={id}
      className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs overflow-hidden mb-6 last:mb-0 scroll-mt-20"
    >
      {/* Card Header */}
      <div className="px-5 sm:px-6 py-4 bg-[#FFF4EC] border-b border-[#E8D8D2] flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white rounded-xl border border-[#E8D8D2] shadow-warm-xs text-[#EA717B]">
            {icon}
          </div>
          <div>
            <h2 className="text-sm sm:text-base font-bold text-[#3B2522]">{title}</h2>
            {subtitle && <p className="text-[11px] text-[#765E59] mt-0.5">{subtitle}</p>}
          </div>
        </div>

        {badge && (
          <span className="text-[10px] font-bold text-[#4A2525] bg-[#FFD0CA] px-2.5 py-1 rounded-full border border-[#EA717B]/20">
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
  const [highlightDifferences, setHighlightDifferences] = useState<boolean>(true);
  const [isScrolled, setIsScrolled] = useState<boolean>(false);

  // Extract scheme IDs from URL params: supports 'schemes', 'ids', 'scheme_ids', or 's1'/'s2'
  const schemesParam =
    searchParams.get('schemes') ||
    searchParams.get('ids') ||
    searchParams.get('scheme_ids') ||
    '';

  let schemeIdsFromUrl: string[] = [];
  if (schemesParam) {
    schemeIdsFromUrl = schemesParam
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
  } else {
    const s1 = searchParams.get('s1');
    const s2 = searchParams.get('s2');
    const s3 = searchParams.get('s3');
    const s4 = searchParams.get('s4');
    const list = [s1, s2, s3, s4].filter((s): s is string => Boolean(s && s.trim()));
    if (list.length > 0) {
      schemeIdsFromUrl = list;
    }
  }

  // Deduplicate requested IDs preserving order and capped at 4
  const effectiveSchemeIds = Array.from(new Set(schemeIdsFromUrl)).slice(0, 4);

  useEffect(() => {
    if (effectiveSchemeIds.length > 0) {
      fetchComparison(effectiveSchemeIds);
    } else if (selectedSchemeIds.length > 0) {
      setSearchParams({ schemes: selectedSchemeIds.join(',') }, { replace: true });
    } else {
      setLoading(false);
      setComparisonData(null);
    }
  }, [schemesParam, searchParams.get('s1'), searchParams.get('s2')]);

  // Track scroll position for sticky header
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 320);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

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
    const updated = effectiveSchemeIds.filter((id) => id !== schemeId);
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

  // Helper to detect if values differ across schemes
  const checkDifference = (getter: (s: Scheme) => any): boolean => {
    if (items.length < 2) return false;
    const first = getter(items[0].scheme);
    for (let i = 1; i < items.length; i++) {
      const current = getter(items[i].scheme);
      if (first !== current) return true;
    }
    return false;
  };

  // Helper to format loan amounts factually
  const formatLoanAmount = (scheme: Scheme) => {
    if (scheme.is_credit_scheme === false || scheme.loan_available === 'NO') {
      return (
        <span className="text-slate-500 italic">
          {t('compare.notApplicable', 'Not applicable')} (Grant / Welfare Scheme)
        </span>
      );
    }
    if (scheme.max_loan_amount && scheme.max_loan_amount > 0) {
      const minText =
        scheme.min_loan_amount && scheme.min_loan_amount > 0
          ? `₹${scheme.min_loan_amount.toLocaleString('en-IN')} – `
          : '';
      return (
        <div>
          <span className="font-bold text-slate-900 text-sm">
            {minText}₹{scheme.max_loan_amount.toLocaleString('en-IN')}
          </span>
          {scheme.max_loan_amount_raw && (
            <div className="text-[11px] text-slate-500 mt-0.5">{scheme.max_loan_amount_raw}</div>
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

  // Helper to format interest rate factually
  const formatInterestRate = (scheme: Scheme) => {
    if (scheme.is_credit_scheme === false || scheme.loan_available === 'NO') {
      return <span className="text-slate-500 italic">{t('compare.notApplicable', 'Not applicable')}</span>;
    }
    const minRate = scheme.interest_rate_min || scheme.interest_rate;
    const maxRate = scheme.interest_rate_max;
    const subsidy = scheme.interest_subsidy;

    if (minRate !== undefined && minRate !== null) {
      return (
        <div>
          <span className="font-bold text-slate-900 text-sm">
            {minRate}%{maxRate && maxRate !== minRate ? ` – ${maxRate}%` : ''} p.a.
          </span>
          {subsidy && subsidy > 0 && (
            <div className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded mt-1 border border-emerald-200 inline-block">
              +{subsidy}% Interest Subvention
            </div>
          )}
          {scheme.interest_rate_type && (
            <div className="text-[11px] text-slate-500 mt-0.5 capitalize">{scheme.interest_rate_type}</div>
          )}
        </div>
      );
    }

    if (subsidy && subsidy > 0) {
      return (
        <div>
          <span className="text-slate-600 font-medium">{t('compare.bankBaseRate', 'Bank Base Rate')}</span>
          <div className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded mt-1 border border-emerald-200 inline-block">
            +{subsidy}% Interest Subvention
          </div>
        </div>
      );
    }

    return (
      <span className="text-slate-500 font-medium text-[11px]">
        Lender-determined (Subject to bank appraisal & RBI guidelines)
      </span>
    );
  };

  // Helper to format repayment tenure factually
  const formatTenure = (scheme: Scheme) => {
    if (scheme.is_credit_scheme === false || scheme.loan_available === 'NO') {
      return <span className="text-slate-500 italic">{t('compare.notApplicable', 'Not applicable')}</span>;
    }
    const minMonths = scheme.repayment_period_min_months;
    const maxMonths = scheme.repayment_period_max_months || scheme.repayment_period_months;

    if (maxMonths && maxMonths > 0) {
      const minYears = minMonths ? (minMonths / 12).toFixed(1).replace('.0', '') : null;
      const maxYears = (maxMonths / 12).toFixed(1).replace('.0', '');
      return (
        <div>
          <span className="font-semibold text-slate-900">
            {minMonths ? `${minMonths} – ` : ''}
            {maxMonths} months ({minYears ? `${minYears} – ` : ''}
            {maxYears} years)
          </span>
          {scheme.repayment_frequency && (
            <div className="text-[11px] text-slate-500 mt-0.5 capitalize">
              Frequency: {scheme.repayment_frequency}
            </div>
          )}
        </div>
      );
    }
    return (
      <span className="text-slate-500 font-medium text-[11px]">
        Lender-determined as per project cashflow
      </span>
    );
  };

  // Helper to format moratorium factually
  const formatMoratorium = (scheme: Scheme) => {
    if (scheme.is_credit_scheme === false || scheme.loan_available === 'NO') {
      return <span className="text-slate-500 italic">{t('compare.notApplicable', 'Not applicable')}</span>;
    }
    const minM = scheme.moratorium_min_months;
    const maxM = scheme.moratorium_max_months || scheme.moratorium_period_months;

    if (maxM && maxM > 0) {
      return (
        <div>
          <span className="font-semibold text-slate-900">
            {minM ? `${minM} – ` : ''}
            {maxM} months
          </span>
          {scheme.moratorium_interest_mode && (
            <div className="text-[11px] text-slate-500 mt-0.5">
              Mode: {scheme.moratorium_interest_mode}
            </div>
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

  return (
    <div className="min-h-screen bg-[#FFFBF0] py-6 sm:py-8 px-4 sm:px-6 lg:px-8 pb-28">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Top Header Card */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 sm:p-6 rounded-2xl border border-[#E8D8D2] shadow-warm-xs">
          <div>
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#765E59] hover:text-[#EA717B] mb-2 transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>{t('compare.back', 'Back')}</span>
            </button>
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-[#FFF4EC] rounded-xl text-[#EA717B] border border-[#FFD0CA]">
                <Scale className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-extrabold text-[#3B2522]">
                  {t('compare.compareSchemes', 'Compare Schemes')}
                </h1>
                <p className="text-xs sm:text-sm text-[#765E59] mt-0.5">
                  Factual side-by-side verification of government financial assistance, eligibility, and loan terms.
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 self-start sm:self-center">
            {items.length >= 2 && (
              <button
                type="button"
                onClick={() => setHighlightDifferences((prev) => !prev)}
                className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl border transition ${
                  highlightDifferences
                    ? 'bg-[#FFD0CA] text-[#4A2525] border-[#EA717B]/30 shadow-warm-xs'
                    : 'bg-white text-[#765E59] border-[#E8D8D2] hover:bg-[#FFFBF0]'
                }`}
                title="Highlight parameters that differ between the compared schemes"
              >
                <SlidersHorizontal className="w-3.5 h-3.5" />
                <span>
                  {highlightDifferences ? 'Highlighting Differences' : 'Highlight Differences'}
                </span>
              </button>
            )}

            {items.length > 0 && (
              <button
                type="button"
                onClick={handleClearAll}
                className="text-xs font-semibold text-[#765E59] hover:text-red-600 px-3 py-2 rounded-xl border border-[#E8D8D2] hover:border-red-200 bg-[#FFF4EC] hover:bg-red-50 transition"
              >
                {t('compare.clearComparison', 'Clear All')}
              </button>
            )}

            {items.length < 4 && (
              <Link
                to="/schemes"
                className="inline-flex items-center gap-1.5 text-xs font-bold text-white bg-[#EA717B] hover:bg-[#d65f69] px-4 py-2.5 rounded-xl shadow-warm-xs transition"
              >
                <Plus className="w-4 h-4" />
                <span>{t('compare.addMore', 'Add Scheme')}</span>
              </Link>
            )}
          </div>
        </div>

        {/* Invalid Scheme IDs Notice */}
        {comparisonData?.invalid_ids && comparisonData.invalid_ids.length > 0 && (
          <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-xl p-4 flex items-center gap-3 text-[#4A2525] text-xs font-medium">
            <AlertTriangle className="w-5 h-5 text-[#EA717B] shrink-0" />
            <span>
              {t('compare.invalidIdsNotice', 'Note: Some requested scheme IDs could not be found or are inactive:')}{' '}
              <strong className="font-mono">{comparisonData.invalid_ids.join(', ')}</strong>
            </span>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-2xl border border-[#E8D8D2] p-12 text-center space-y-4 shadow-warm-xs">
            <div className="w-8 h-8 border-4 border-[#EA717B] border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm font-semibold text-[#765E59]">
              {t('compare.loading', 'Fetching official scheme comparison data...')}
            </p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center space-y-3">
            <AlertTriangle className="w-8 h-8 text-red-500 mx-auto" />
            <h3 className="text-base font-bold text-red-900">
              {t('compare.errorTitle', 'Unable to Compare Schemes')}
            </h3>
            <p className="text-xs text-red-700">{error}</p>
            <button
              type="button"
              onClick={() => fetchComparison(effectiveSchemeIds)}
              className="text-xs font-bold text-white bg-[#EA717B] hover:bg-[#d65f69] px-4 py-2 rounded-xl shadow-warm-xs"
            >
              {t('compare.retry', 'Try Again')}
            </button>
          </div>
        )}

        {/* Empty State: 0 Schemes */}
        {!loading && !error && items.length === 0 && (
          <div className="bg-white rounded-2xl border border-[#E8D8D2] p-12 text-center space-y-4 shadow-warm-xs">
            <div className="w-16 h-16 bg-[#FFF4EC] rounded-2xl flex items-center justify-center mx-auto text-[#EA717B]">
              <Scale className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-[#3B2522]">
              {t('compare.emptyTitle', 'No Schemes Selected for Comparison')}
            </h3>
            <p className="text-xs text-[#765E59] max-w-md mx-auto leading-relaxed">
              Select 2 to 4 schemes from Scheme Discovery or Recommendations to view a side-by-side comparison of loan limits, interest rates, eligibility criteria, and channel partners.
            </p>
            <div className="flex items-center justify-center gap-3 pt-2">
              <Link
                to="/schemes"
                className="bg-[#EA717B] text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-warm-xs hover:bg-[#d65f69] transition"
              >
                {t('compare.browseSchemes', 'Browse Schemes')}
              </Link>
              <Link
                to="/recommendations"
                className="bg-[#FFF4EC] text-[#4A2525] font-bold text-xs px-5 py-2.5 rounded-xl border border-[#FFD0CA] hover:bg-[#FFD0CA]/40 transition"
              >
                View Recommendations
              </Link>
            </div>
          </div>
        )}

        {/* 1 Scheme Selected Warning Card */}
        {!loading && !error && items.length === 1 && (
          <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-2xl p-5 sm:p-6 shadow-warm-xs flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-[#FFD0CA] rounded-xl text-[#4A2525] shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#3B2522]">
                  Select at least one more scheme to compare side-by-side
                </h4>
                <p className="text-xs text-[#765E59] mt-0.5">
                  You have selected <strong>{items[0].scheme.scheme_name}</strong>. Add another scheme from the directory or recommendations to compare facts side-by-side.
                </p>
              </div>
            </div>
            <Link
              to="/schemes"
              className="inline-flex items-center gap-1.5 text-xs font-bold text-white bg-[#EA717B] hover:bg-[#d65f69] px-4 py-2.5 rounded-xl shadow-warm-xs shrink-0 transition"
            >
              <Plus className="w-4 h-4" />
              <span>{t('compare.addSchemeToCompare', 'Add Another Scheme')}</span>
            </Link>
          </div>
        )}

        {/* Sticky Header on Deep Scroll */}
        {isScrolled && items.length >= 2 && (
          <div className="fixed top-16 left-0 right-0 z-40 bg-[#FFFBF0]/95 backdrop-blur-md border-b border-[#E8D8D2] shadow-warm-md py-2.5 px-4 sm:px-8 transition-all animate-in slide-in-from-top duration-200">
            <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
              <div className="text-xs font-bold text-[#765E59] uppercase tracking-wider hidden lg:block shrink-0">
                Comparing Schemes:
              </div>
              <div
                className={`grid grid-cols-1 sm:grid-cols-2 ${
                  items.length === 3 ? 'lg:grid-cols-3' : items.length >= 4 ? 'lg:grid-cols-4' : 'lg:grid-cols-2'
                } gap-2 sm:gap-3 flex-1`}
              >
                {items.map(({ scheme }) => (
                  <div
                    key={scheme.scheme_id}
                    className="flex items-center justify-between gap-2 bg-white border border-[#E8D8D2] px-3 py-1.5 rounded-xl shadow-warm-xs"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="text-[10px] font-mono font-bold text-[#4A2525] truncate">
                        {scheme.scheme_code || scheme.scheme_id}
                      </div>
                      <div className="text-xs font-bold text-[#3B2522] truncate">
                        {scheme.scheme_name}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {scheme.calculator_applicable !== false && scheme.is_credit_scheme !== false && (
                        <Link
                          to={`/calculator?scheme=${scheme.scheme_id}`}
                          className="p-1 text-[#EA717B] hover:bg-[#FFF4EC] rounded-lg"
                          title="Calculate EMI"
                        >
                          <Calculator className="w-3.5 h-3.5" />
                        </Link>
                      )}
                      <Link
                        to={`/channel-partners?scheme_id=${scheme.scheme_id}`}
                        className="p-1 text-[#F7AE56] hover:bg-[#FFF4EC] rounded-lg"
                        title="Locate Channel Partners"
                      >
                        <Building2 className="w-3.5 h-3.5" />
                      </Link>
                      <button
                        type="button"
                        onClick={() => handleRemoveScheme(scheme.scheme_id)}
                        className="p-1 text-[#765E59] hover:text-red-500 rounded-lg"
                        title="Remove scheme"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* MAIN COMPARISON CONTENT */}
        {!loading && !error && items.length > 0 && (
          <div className="space-y-6">
            {/* TOP SCHEMES HEADER CARDS */}
            <div className="bg-white border border-[#E8D8D2] rounded-2xl p-5 sm:p-6 shadow-warm-xs">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-[#765E59] uppercase tracking-wider">
                  {t('compare.comparing', 'Comparing')} ({items.length}/4 {t('compare.compareSchemes', 'Schemes')})
                </span>
                <span className="text-xs text-[#765E59] font-medium hidden sm:inline">
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
                    className="relative bg-[#FFFBF0] p-4 sm:p-5 rounded-2xl border border-[#E8D8D2] flex flex-col justify-between hover:border-[#EA717B]/40 transition shadow-warm-xs"
                  >
                    {/* Remove button */}
                    <button
                      type="button"
                      onClick={() => handleRemoveScheme(scheme.scheme_id)}
                      className="absolute top-3 right-3 text-[#765E59] hover:text-red-500 p-1 rounded-md hover:bg-white transition"
                      title={t('compare.removeScheme', 'Remove from comparison')}
                      aria-label={`Remove ${scheme.scheme_name}`}
                    >
                      <X className="w-4 h-4" />
                    </button>

                    <div>
                      <div className="flex items-center gap-2 mb-2 flex-wrap pr-6">
                        <span className="text-[10px] font-mono font-bold text-[#4A2525] bg-[#FFD0CA] px-2 py-0.5 rounded-lg border border-[#EA717B]/20">
                          {scheme.scheme_code || scheme.scheme_id}
                        </span>
                        {scheme.is_credit_scheme !== false ? (
                          <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-lg border border-emerald-200">
                            {t('compare.loanAvailable', 'Credit / Loan')}
                          </span>
                        ) : (
                          <span className="text-[10px] font-bold text-[#4A2525] bg-[#FFF4EC] px-2 py-0.5 rounded-lg border border-[#FFD0CA]">
                            {t('compare.noCreditWelfare', 'Grant / Subsidy / Welfare')}
                          </span>
                        )}
                      </div>

                      <h3 className="text-sm sm:text-base font-extrabold text-[#3B2522] line-clamp-2 leading-snug">
                        {scheme.scheme_name}
                      </h3>

                      <p className="text-xs text-[#765E59] mt-1 line-clamp-1 font-medium">
                        {scheme.ministry || 'Government of India'}
                      </p>
                    </div>

                    {/* Primary Action Buttons */}
                    <div className="mt-4 pt-3.5 border-t border-[#E8D8D2] space-y-2">
                      {/* Secondary Link Strip: Save & Full Details */}
                      <div className="flex items-center justify-between gap-2">
                        <SaveSchemeButton schemeId={scheme.scheme_id} size="sm" />
                        <Link
                          to={`/schemes/${scheme.scheme_id}`}
                          className="text-xs font-bold text-[#EA717B] hover:underline flex items-center gap-1"
                        >
                          <span>{t('compare.details', 'Full Details')}</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>

                      {/* Three Prominent CTAs: Check Eligibility, Calculate, Find Partner */}
                      <div className="grid grid-cols-1 gap-1.5 pt-1">
                        <Link
                          to={`/recommendations?scheme=${scheme.scheme_id}`}
                          className="text-xs font-bold text-[#3B2522] hover:text-[#EA717B] bg-white hover:bg-[#FFF4EC] px-3 py-2 rounded-xl border border-[#E8D8D2] flex items-center justify-center gap-1.5 transition shadow-warm-xs text-center"
                          title="Evaluate citizen profile eligibility against this scheme"
                        >
                          <ShieldCheck className="w-3.5 h-3.5 text-[#EA717B] shrink-0" />
                          <span>Check Eligibility</span>
                        </Link>

                        <div className="grid grid-cols-2 gap-1.5">
                          {scheme.calculator_applicable !== false && scheme.is_credit_scheme !== false ? (
                            <Link
                              to={`/calculator?scheme=${scheme.scheme_id}`}
                              className="text-xs font-bold text-emerald-800 hover:text-emerald-900 bg-emerald-50 hover:bg-emerald-100 px-2.5 py-2 rounded-xl border border-emerald-200 flex items-center justify-center gap-1.5 transition text-center"
                              title="Calculate monthly EMI and interest schedule"
                            >
                              <Calculator className="w-3.5 h-3.5 shrink-0" />
                              <span>{t('compare.openCalculator', 'Calculate')}</span>
                            </Link>
                          ) : (
                            <span className="text-[11px] font-semibold text-[#765E59] bg-[#FFF4EC] px-2 py-2 rounded-xl border border-[#E8D8D2] text-center flex items-center justify-center">
                              Non-Credit
                            </span>
                          )}

                          <Link
                            to={`/channel-partners?scheme_id=${scheme.scheme_id}`}
                            className="text-xs font-bold text-[#4A2525] hover:text-[#3B2522] bg-[#FFF4EC] hover:bg-[#FFD0CA]/50 px-2.5 py-2 rounded-xl border border-[#FFD0CA] flex items-center justify-center gap-1.5 transition text-center"
                            title="Locate authorized channel partner branches and banks"
                          >
                            <Building2 className="w-3.5 h-3.5 text-[#F7AE56] shrink-0" />
                            <span>{t('compare.locatePartners', 'Find Partner')}</span>
                          </Link>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {/* Add Scheme Slot Card if items < 4 */}
                {items.length < 4 && (
                  <div className="border-2 border-dashed border-[#E8D8D2] hover:border-[#EA717B]/50 rounded-2xl p-5 flex flex-col items-center justify-center text-center space-y-2.5 bg-[#FFFBF0] hover:bg-[#FFF4EC]/50 transition group min-h-[220px]">
                    <div className="p-3 bg-white group-hover:bg-[#EA717B] group-hover:text-white text-[#765E59] rounded-full border border-[#E8D8D2] transition shadow-warm-xs">
                      <Plus className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-[#3B2522]">{t('compare.addSchemeToCompare', 'Add Another Scheme')}</h4>
                      <p className="text-[11px] text-[#765E59] mt-0.5">
                        Compare up to 4 schemes side-by-side
                      </p>
                    </div>
                    <Link
                      to="/schemes"
                      className="text-xs font-bold text-[#EA717B] bg-white hover:bg-[#FFF4EC] px-3.5 py-1.5 rounded-xl border border-[#E8D8D2] shadow-warm-xs transition"
                    >
                      Browse Schemes
                    </Link>
                  </div>
                )}
              </div>
            </div>

            {/* SECTION 1: PERSONALIZED CITIZEN FIT (IF EVALUATED OR LOGGED IN) */}
            <ComparisonSectionCard
              id="section-eligibility-fit"
              title={t('compare.secPersonalized', 'Personalized Eligibility Fit')}
              icon={<Sparkles className="w-5 h-5 text-emerald-600" />}
              subtitle={
                user
                  ? t('compare.profileAssessmentSubtitle', 'Automated statutory assessment evaluated against your registered profile')
                  : t('compare.loginNotice', 'Sign in or complete profile to evaluate personalized statutory eligibility')
              }
              badge={user ? t('common.personalized', 'Personalized') : undefined}
            >
              <ComparisonFeatureRow
                label={t('compare.eligibilityStatus', 'Eligibility Status')}
                items={items}
                isLast={true}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => items.find((i) => i.scheme.scheme_id === s.scheme_id)?.personalized_eligibility?.status)}
                renderValue={({ scheme, personalized_eligibility }) => {
                  if (!personalized_eligibility) {
                    return (
                      <div className="text-[11px] text-slate-500 italic bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                        {user ? (
                          <span>{t('compare.profileIncompleteNotice', 'Complete your profile to view eligibility status.')}</span>
                        ) : (
                          <div className="space-y-1.5">
                            <span>{t('compare.loginRequired', 'Log in to evaluate personalized eligibility.')}</span>
                            <div className="pt-1">
                              <Link
                                to="/login"
                                className="inline-block text-[11px] font-bold text-[#EA717B] hover:underline"
                              >
                                Sign in →
                              </Link>
                            </div>
                          </div>
                        )}
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
                        <ul className="text-[11px] text-slate-600 space-y-1 mt-2 list-disc list-inside bg-slate-50/60 p-2 rounded-lg border border-slate-200/60">
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

            {/* SECTION 2: SCHEME PURPOSE & MANDATE */}
            <ComparisonSectionCard
              title={t('compare.secOverview', 'Scheme Purpose & Mandate')}
              icon={<Building2 className="w-5 h-5 text-[#EA717B]" />}
              subtitle="Core purpose, nodal ministry, target beneficiary groups, and applicant entity types"
            >
              <ComparisonFeatureRow
                label={t('compare.schemeType', 'Financial Category')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.financial_category || s.scheme_type)}
                renderValue={({ scheme }) => (
                  <span className="inline-block px-2.5 py-1 rounded-md bg-slate-100 text-slate-800 border border-slate-200 text-[11px] font-bold">
                    {scheme.financial_category ? scheme.financial_category.replace(/_/g, ' ') : scheme.scheme_type || 'CREDIT / LOAN'}
                  </span>
                )}
              />

              <ComparisonFeatureRow
                label={t('compare.ministry', 'Ministry / Department')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.ministry)}
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
                label={t('compare.schemePurpose', 'Scheme Purpose & Benefits')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.financial_assistance_summary || s.purpose || s.objective)}
                renderValue={({ scheme }) => (
                  <p className="text-xs text-slate-700 leading-relaxed">
                    {scheme.financial_assistance_summary ||
                      scheme.benefit_description ||
                      scheme.short_description ||
                      scheme.purpose ||
                      scheme.objective ||
                      t('compare.noneSpecified', 'Refer to official scheme guidelines')}
                  </p>
                )}
              />

              <ComparisonFeatureRow
                label={t('compare.targetBeneficiary', 'Target Group')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.target_beneficiary || s.target_groups)}
                renderValue={({ scheme }) => (
                  <span className="font-semibold text-slate-800">
                    {scheme.target_beneficiary || scheme.target_groups || t('compare.generalCitizens', 'General Citizens & Micro-Entrepreneurs')}
                  </span>
                )}
              />

              <ComparisonFeatureRow
                label="Eligible Applicant Types"
                hint="Entity types eligible to apply"
                items={items}
                isLast={true}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.applicant_types)}
                renderValue={({ scheme }) => (
                  <span className="text-xs text-slate-700 font-medium">
                    {scheme.applicant_types || 'Individuals, Self-Help Groups (SHGs), MSMEs, Proprietorships'}
                  </span>
                )}
              />
            </ComparisonSectionCard>

            {/* SECTION 3: FINANCIAL ASSISTANCE & CREDIT TERMS */}
            <ComparisonSectionCard
              title={t('compare.secFinancial', 'Financial Assistance & Credit Terms')}
              icon={<Banknote className="w-5 h-5 text-emerald-600" />}
              subtitle="Project limits, loan ceilings, interest rates, tenure, moratorium, and subsidies"
            >
              <ComparisonFeatureRow
                label={t('compare.loanAvailable', 'Credit Facility')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.is_credit_scheme)}
                renderValue={({ scheme }) => {
                  if (scheme.is_credit_scheme !== false && scheme.loan_available !== 'NO') {
                    return (
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded border border-emerald-300">
                        ✓ {t('compare.yes', 'Yes')} (Credit Facility)
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
                label="Project Cost Ceiling"
                hint="Allowable total project outlay"
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.max_project_cost)}
                renderValue={({ scheme }) => {
                  if (scheme.max_project_cost && scheme.max_project_cost > 0) {
                    const minText = scheme.min_project_cost ? `₹${scheme.min_project_cost.toLocaleString('en-IN')} – ` : '';
                    return (
                      <span className="font-bold text-slate-900 text-sm">
                        {minText}₹{scheme.max_project_cost.toLocaleString('en-IN')}
                      </span>
                    );
                  }
                  return (
                    <span className="text-slate-500 font-medium text-[11px]">
                      No statutory project ceiling specified
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.maxLoan', 'Stated Loan Amount')}
                hint="Minimum & Maximum credit limits"
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.max_loan_amount)}
                renderValue={({ scheme }) => formatLoanAmount(scheme)}
              />

              <ComparisonFeatureRow
                label={t('compare.marginMoney', 'Beneficiary Contribution')}
                hint="Required borrower equity / margin money"
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.beneficiary_contribution_percentage || s.financing_percentage)}
                renderValue={({ scheme }) => {
                  if (scheme.beneficiary_contribution_percentage && scheme.beneficiary_contribution_percentage > 0) {
                    return (
                      <span className="font-semibold text-slate-900">
                        {scheme.beneficiary_contribution_percentage}% of project cost
                      </span>
                    );
                  }
                  if (scheme.financing_percentage && scheme.financing_percentage > 0 && scheme.financing_percentage < 100) {
                    return (
                      <span className="font-semibold text-slate-900">
                        {100 - scheme.financing_percentage}% of project cost
                      </span>
                    );
                  }
                  return (
                    <span className="text-slate-500 font-medium text-[11px]">
                      Standard 5% – 10% (or as per lending bank appraisal)
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.interestRate', 'Interest Rate')}
                hint="Annual rate / subvention"
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.interest_rate_min || s.interest_rate)}
                renderValue={({ scheme }) => formatInterestRate(scheme)}
              />

              <ComparisonFeatureRow
                label={t('compare.subsidy', 'Subsidy / Capital Grant')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.subsidy_percentage || s.max_subsidy_amount || s.grant_amount)}
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
                  if (scheme.subsidy_details) {
                    return <span className="text-xs text-emerald-800 font-medium">{scheme.subsidy_details}</span>;
                  }
                  return (
                    <span className="text-slate-500 font-medium text-[11px]">
                      {scheme.is_credit_scheme !== false
                        ? 'No capital subsidy stated (Credit facility only)'
                        : 'Direct benefit transfer / non-loan assistance'}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.tenure', 'Repayment Tenure')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.repayment_period_max_months || s.repayment_period_months)}
                renderValue={({ scheme }) => formatTenure(scheme)}
              />

              <ComparisonFeatureRow
                label={t('compare.moratorium', 'Moratorium Period')}
                hint="Initial repayment holiday"
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.moratorium_period_months || s.moratorium_max_months)}
                renderValue={({ scheme }) => formatMoratorium(scheme)}
              />

              <ComparisonFeatureRow
                label={t('compare.collateral', 'Collateral & Guarantee')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.collateral_required || s.guarantee_requirement)}
                renderValue={({ scheme }) => {
                  if (scheme.collateral_required === 'NO' || scheme.collateral_required === 'NONE') {
                    return (
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        No collateral required (Covered under Credit Guarantee)
                      </span>
                    );
                  }
                  if (scheme.guarantee_requirement) {
                    return <span className="font-medium text-slate-800">{scheme.guarantee_requirement}</span>;
                  }
                  if (scheme.collateral_required) {
                    return <span className="font-medium text-slate-800">{scheme.collateral_required}</span>;
                  }
                  return (
                    <span className="text-slate-500 font-medium text-[11px]">
                      No collateral for loans up to statutory limits (RBI norms)
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.calculatorAction', 'Financial Calculator')}
                items={items}
                isLast={true}
                renderValue={({ scheme }) => {
                  if (scheme.calculator_applicable !== false && scheme.is_credit_scheme !== false) {
                    return (
                      <Link
                        to={`/calculator?scheme=${scheme.scheme_id}`}
                        className="inline-flex items-center gap-1.5 text-emerald-700 hover:text-emerald-800 bg-emerald-50 hover:bg-emerald-100 font-bold px-3 py-1.5 rounded-lg border border-emerald-200 text-xs transition"
                      >
                        <Calculator className="w-3.5 h-3.5" />
                        <span>{t('compare.openCalculator', 'Calculate EMI')}</span>
                      </Link>
                    );
                  }
                  return (
                    <span className="text-slate-400 text-xs italic">
                      {t('compare.notApplicable', 'Not applicable (Non-Credit)')}
                    </span>
                  );
                }}
              />
            </ComparisonSectionCard>

            {/* SECTION 4: MAJOR ELIGIBILITY CONDITIONS */}
            <ComparisonSectionCard
              title={t('compare.secEligibility', 'Major Eligibility Conditions')}
              icon={<ShieldCheck className="w-5 h-5 text-[#EA717B]" />}
              subtitle="Age limits, income ceilings, category conditions, enterprise stage, and statutory rules"
            >
              <ComparisonFeatureRow
                label={t('compare.ageCriteria', 'Age Limits')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => `${s.min_age}-${s.max_age}`)}
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
                      {t('common.notSpecifiedInOfficialData', 'No age limits specified in official guidelines')}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.incomeLimit', 'Income Ceiling')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.income_limit || s.rules?.find((r) => r.field.includes('income'))?.value)}
                renderValue={({ scheme }) => {
                  const incomeRule = scheme.rules?.find((r) => r.field.includes('income'));
                  if (scheme.income_limit && scheme.income_limit > 0) {
                    return (
                      <span className="font-semibold text-slate-900">
                        {scheme.income_operator || 'Up to'} ₹{scheme.income_limit.toLocaleString('en-IN')}/year
                      </span>
                    );
                  }
                  if (incomeRule) {
                    return (
                      <span className="font-semibold text-slate-900">
                        {incomeRule.description || `${incomeRule.operator} ₹${incomeRule.value}/year`}
                      </span>
                    );
                  }
                  return (
                    <span className="text-slate-500 font-medium text-[11px]">
                      {t('compare.noIncomeLimit', 'No mandatory household income ceiling specified')}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.socialCategory', 'Social Category & Focus')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.marginalized_group || s.social_category || s.sc_required)}
                renderValue={({ scheme }) => (
                  <div>
                    <span className="font-semibold text-slate-900">
                      {scheme.marginalized_group || scheme.social_category || scheme.target_groups || t('compare.allCategories', 'All Social Categories')}
                    </span>
                    {scheme.sc_required && scheme.sc_required !== 'NO' && (
                      <div className="text-[11px] text-amber-800 bg-amber-50 px-1.5 py-0.5 rounded mt-1 border border-amber-200 inline-block font-semibold">
                        Priority: SC/ST Beneficiaries
                      </div>
                    )}
                  </div>
                )}
              />

              <ComparisonFeatureRow
                label="Gender Conditions"
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.gender_condition || s.gender_requirement || s.rules?.find((r) => r.field === 'gender')?.value)}
                renderValue={({ scheme }) => {
                  const genderRule = scheme.rules?.find((r) => r.field === 'gender');
                  const cond = scheme.gender_condition || scheme.gender_requirement || (genderRule ? genderRule.value : null);
                  if (cond && cond !== 'ALL' && cond !== 'ANY') {
                    return (
                      <span className="font-semibold text-indigo-900 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200 text-xs">
                        {cond}
                      </span>
                    );
                  }
                  return <span className="text-slate-700 font-medium">{t('compare.allGenders', 'All Genders (Men, Women, Transgender)')}</span>;
                }}
              />

              <ComparisonFeatureRow
                label="Permitted Business Stage"
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => `${s.new_business_allowed}-${s.existing_business_allowed}-${s.business_stage}`)}
                renderValue={({ scheme }) => {
                  if (scheme.business_stage) {
                    return <span className="font-semibold text-slate-900">{scheme.business_stage.replace(/_/g, ' ')}</span>;
                  }
                  if (scheme.new_business_allowed === 'YES' && scheme.existing_business_allowed === 'YES') {
                    return <span className="font-semibold text-slate-900">{t('compare.bothNewExisting', 'Both New & Existing Businesses Allowed')}</span>;
                  }
                  if (scheme.new_business_allowed === 'YES') {
                    return <span className="font-semibold text-slate-900">{t('compare.newOnly', 'New Business Units Only')}</span>;
                  }
                  if (scheme.existing_business_allowed === 'YES') {
                    return <span className="font-semibold text-slate-900">{t('compare.existingOnly', 'Existing Units (Modernization / Expansion)')}</span>;
                  }
                  return <span className="text-slate-600 font-medium">{t('compare.newOrExisting', 'New or Existing Units as per guidelines')}</span>;
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.occupation', 'Permitted Sector & Activity')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => `${s.sector}-${s.activity_type}`)}
                renderValue={({ scheme }) => (
                  <div>
                    <span className="font-semibold text-slate-900">
                      {scheme.sector ? scheme.sector.replace(/_/g, ' ') : t('compare.allSectors', 'All Economic Sectors')}
                    </span>
                    {scheme.activity_type && (
                      <div className="text-[11px] text-slate-500 mt-0.5 font-medium">
                        Activities: {scheme.activity_type}
                      </div>
                    )}
                  </div>
                )}
              />

              <ComparisonFeatureRow
                label="Education & Training"
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.education_applicable || s.rules?.find((r) => r.field.includes('education'))?.value)}
                renderValue={({ scheme }) => {
                  const eduRule = scheme.rules?.find((r) => r.field.includes('education') || r.field.includes('qualification'));
                  if (scheme.education_applicable) {
                    return <span className="font-semibold text-slate-900">{scheme.education_applicable}</span>;
                  }
                  if (eduRule) {
                    return <span className="font-semibold text-slate-900">{eduRule.description || eduRule.value}</span>;
                  }
                  return (
                    <span className="text-slate-500 font-medium text-[11px]">
                      No mandatory minimum educational qualification stated
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.otherConditions', 'Key Statutory Rules')}
                hint="Specific verified rule conditions"
                items={items}
                isLast={true}
                renderValue={({ scheme }) => {
                  const rules = scheme.rules || [];
                  if (rules.length > 0) {
                    return (
                      <ul className="text-[11px] text-slate-600 space-y-1.5 list-disc list-inside">
                        {rules.slice(0, 3).map((r, i) => (
                          <li key={i}>
                            <span className="font-semibold text-slate-800">{r.field.replace(/_/g, ' ')}:</span>{' '}
                            {r.description || `${r.operator} ${r.value}`}
                          </li>
                        ))}
                      </ul>
                    );
                  }
                  return (
                    <span className="text-slate-500 text-[11px]">
                      {t('compare.standardOfficialNorms', 'Standard statutory norms and ministry circulars apply')}
                    </span>
                  );
                }}
              />
            </ComparisonSectionCard>

            {/* SECTION 5: GEOGRAPHICAL SCOPE & COVERAGE */}
            <ComparisonSectionCard
              title="Geographical Scope & Coverage"
              icon={<MapPin className="w-5 h-5 text-indigo-600" />}
              subtitle="All-India central implementation vs specific state or district coverage"
            >
              <ComparisonFeatureRow
                label={t('compare.geographicCoverage', 'State / UT Coverage')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.state_restriction || s.state_coverage)}
                renderValue={({ scheme }) => (
                  <div className="flex items-center gap-1.5 font-semibold text-slate-900">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>
                      {scheme.state_restriction && scheme.state_restriction !== 'ALL_INDIA'
                        ? scheme.state_restriction.replace(/_/g, ' ')
                        : t('compare.allIndia', 'All India / Central Scheme')}
                    </span>
                  </div>
                )}
              />

              <ComparisonFeatureRow
                label="District Scope"
                items={items}
                isLast={true}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.district_restriction || s.district_coverage)}
                renderValue={({ scheme }) => (
                  <span className="text-xs text-slate-700 font-medium">
                    {scheme.district_restriction && scheme.district_restriction !== 'ALL_DISTRICTS'
                      ? scheme.district_restriction.replace(/_/g, ' ')
                      : 'All Districts nationwide'}
                  </span>
                )}
              />
            </ComparisonSectionCard>

            {/* SECTION 6: REQUIRED DOCUMENTS & PROOFS */}
            <ComparisonSectionCard
              title={t('compare.secDocuments', 'Documents & Verification Proofs')}
              icon={<FileText className="w-5 h-5 text-[#EA717B]" />}
              subtitle="Mandatory identity, residence, business, and conditional documents"
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
                            <FileText className="w-3.5 h-3.5 text-[#EA717B] shrink-0 mt-0.5" />
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
                label={t('compare.optionalDocs', 'Conditional / Optional Proofs')}
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

            {/* SECTION 7: APPLICATION ROUTE & PARTNER ROUTING */}
            <ComparisonSectionCard
              title={t('compare.secApplication', 'Application Route & Channel Partner Routing')}
              icon={<SendHorizontal className="w-5 h-5 text-indigo-600" />}
              subtitle="Application channels, authorized portals, and channel partner branch network"
            >
              <ComparisonFeatureRow
                label={t('compare.applicationMode', 'Application Mode')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.application_mode)}
                renderValue={({ scheme }) => (
                  <span className="font-semibold text-slate-900">
                    {scheme.application_mode || 'Online / Institutional'}
                  </span>
                )}
              />

              <ComparisonFeatureRow
                label={t('compare.applicationRoute', 'Application Route')}
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.application_route)}
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
                label="Partner Network"
                hint="Authorized lending partners in database"
                items={items}
                highlightDifferences={highlightDifferences}
                isDifferent={checkDifference((s) => s.partner_count)}
                renderValue={({ scheme }) => (
                  <div>
                    <span className="font-bold text-slate-900 text-sm">
                      {scheme.partner_count !== undefined && scheme.partner_count !== null
                        ? `${scheme.partner_count} Partners`
                        : 'Multiple Nationalized Banks'}
                    </span>
                    <div className="pt-1">
                      <Link
                        to={`/channel-partners?scheme_id=${scheme.scheme_id}`}
                        className="text-[11px] font-bold text-indigo-700 hover:underline inline-flex items-center gap-1"
                      >
                        <Building2 className="w-3 h-3" />
                        <span>{t('compare.locatePartners', 'Locate Partners Near You')} →</span>
                      </Link>
                    </div>
                  </div>
                )}
              />

              <ComparisonFeatureRow
                label={t('compare.officialPortal', 'Official Portal Link')}
                items={items}
                renderValue={({ scheme }) => {
                  const portalUrl = scheme.official_portal || scheme.application_url;
                  if (portalUrl) {
                    return (
                      <a
                        href={portalUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 font-bold text-[#EA717B] hover:text-[#d65f69] hover:underline text-xs truncate max-w-[220px]"
                      >
                        <span className="truncate">{portalUrl}</span>
                        <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                      </a>
                    );
                  }
                  return (
                    <span className="text-slate-400 italic">
                      {t('common.notSpecified', 'Not specified in available data')}
                    </span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label="Routing Actions"
                items={items}
                isLast={true}
                renderValue={({ scheme }) => {
                  const portalUrl = scheme.official_portal || scheme.application_url;
                  return (
                    <div className="flex flex-wrap items-center gap-2">
                      <Link
                        to={`/channel-partners?scheme_id=${scheme.scheme_id}`}
                        className="inline-flex items-center gap-1.5 font-bold text-[#4A2525] hover:text-[#3B2522] bg-[#FFF4EC] hover:bg-[#FFD0CA]/40 px-3 py-1.5 rounded-xl border border-[#FFD0CA] text-xs transition"
                      >
                        <Building2 className="w-3.5 h-3.5 text-[#F7AE56]" />
                        <span>{t('compare.locatePartners', 'Find Partner')}</span>
                      </Link>

                      {portalUrl && (
                        <a
                          href={portalUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 font-bold text-white bg-[#EA717B] hover:bg-[#d65f69] px-3 py-1.5 rounded-xl text-xs shadow-warm-xs transition"
                        >
                          <span>{t('compare.applyOfficial', 'Official Portal')}</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  );
                }}
              />
            </ComparisonSectionCard>

            {/* SECTION 8: OFFICIAL VERIFICATION & PROVENANCE */}
            <ComparisonSectionCard
              title={t('compare.secVerification', 'Official Verification & Provenance')}
              icon={<ShieldCheck className="w-5 h-5 text-emerald-600" />}
              subtitle="Statutory verification status, official source document, gazette references, and version recency"
            >
              <ComparisonFeatureRow
                label={t('compare.govVerification', 'Verification Status')}
                items={items}
                renderValue={({ scheme }) => (
                  <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded border border-emerald-300">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    <span>{scheme.verification_status || 'VERIFIED'}</span>
                  </span>
                )}
              />

              <ComparisonFeatureRow
                label="Source Document"
                items={items}
                renderValue={({ scheme }) => {
                  if (scheme.source_document || scheme.source_title) {
                    return (
                      <div>
                        <div className="font-semibold text-slate-900 text-xs">
                          {scheme.source_document || scheme.source_title}
                        </div>
                        {scheme.source_page && (
                          <div className="text-[11px] text-slate-500 mt-0.5 font-mono">
                            Page: {scheme.source_page}
                            {scheme.source_section ? ` | Section: ${scheme.source_section}` : ''}
                          </div>
                        )}
                      </div>
                    );
                  }
                  return (
                    <span className="text-slate-500 text-xs">Official Ministry Guidelines</span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.officialSource', 'Official Gazette Link')}
                items={items}
                renderValue={({ scheme }) => {
                  if (scheme.official_source_url) {
                    return (
                      <a
                        href={scheme.official_source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#EA717B] font-semibold hover:underline flex items-center gap-1 truncate max-w-[220px] text-xs"
                      >
                        <span className="truncate">{scheme.official_source_url}</span>
                        <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                      </a>
                    );
                  }
                  return (
                    <span className="text-slate-400 italic text-xs">{t('common.notSpecified', 'Not specified')}</span>
                  );
                }}
              />

              <ComparisonFeatureRow
                label={t('compare.lastVerified', 'Last Verified Date')}
                items={items}
                isLast={true}
                renderValue={({ scheme }) => (
                  <span className="font-mono text-slate-700 text-xs">
                    {scheme.last_verified_date || scheme.source_published_date || 'Current Statutory Version'}
                  </span>
                )}
              />
            </ComparisonSectionCard>

            {/* BOTTOM SUMMARY ACTION FOOTER */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Summary Actions
                </span>
                <span className="text-xs text-slate-400">
                  Ready to proceed with your chosen scheme?
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
                    className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2"
                  >
                    <div className="text-xs font-bold text-slate-900 truncate">
                      {scheme.scheme_name}
                    </div>

                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      <Link
                        to={`/recommendations?scheme=${scheme.scheme_id}`}
                        className="text-xs font-bold text-[#EA717B] bg-white hover:bg-[#FFF4EC] px-2.5 py-1.5 rounded-lg border border-[#E8D8D2] shadow-warm-xs flex items-center gap-1"
                      >
                        <ShieldCheck className="w-3 h-3" />
                        <span>{t('compare.checkEligibility', 'Check Eligibility')}</span>
                      </Link>

                      {scheme.calculator_applicable !== false && scheme.is_credit_scheme !== false ? (
                        <Link
                          to={`/calculator?scheme=${scheme.scheme_id}`}
                          className="text-xs font-bold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 px-2.5 py-1.5 rounded-lg border border-emerald-200 flex items-center gap-1"
                        >
                          <Calculator className="w-3 h-3" />
                          <span>{t('compare.calculate', 'Calculate')}</span>
                        </Link>
                      ) : (
                        <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2 py-1.5 rounded-lg border border-slate-200">
                          {t('calculator.nonCreditBadge', 'Non-Credit')}
                        </span>
                      )}

                      <Link
                        to={`/channel-partners?scheme_id=${scheme.scheme_id}`}
                        className="text-xs font-bold text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1.5 rounded-lg border border-indigo-200 flex items-center gap-1"
                      >
                        <Building2 className="w-3 h-3" />
                        <span>{t('compare.findPartner', 'Find Partner')}</span>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
