import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { schemeApi, SchemeQueryParams } from '../api/schemeApi';
import { Scheme, FilterOptionsResponse } from '../types';
import { SchemeCard } from '../components/SchemeCard';
import { Alert } from '../components/Alert';
import { useAuth } from '../context/AuthContext';
import {
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  X,
  SlidersHorizontal,
  Sparkles,
  ArrowUpDown,
  Check,
  Building2,
  Briefcase,
  Users,
  Banknote,
  MapPin,
  Compass,
  FileCheck,
  HelpCircle,
} from 'lucide-react';

export const Schemes: React.FC = () => {
  const { t } = useTranslation();
  const { user, isAuthenticated } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  // Read URL query parameters
  const urlSearch = searchParams.get('search') || '';
  const urlMinistry = searchParams.get('ministry') || '';
  const urlSector = searchParams.get('sector') || '';
  const urlFinancialType = searchParams.get('financial_type') || '';
  const urlBeneficiary = searchParams.get('beneficiary_category') || '';
  const urlState = searchParams.get('state_restriction') || '';
  const urlRoute = searchParams.get('application_route') || '';
  const urlLoanAvailable = searchParams.get('loan_available') || '';
  const urlSubsidyAvailable = searchParams.get('subsidy_available') || '';
  const urlSortBy = searchParams.get('sort_by') || (urlSearch ? 'relevance' : 'scheme_id');
  const urlSortOrder = searchParams.get('sort_order') || 'asc';
  const urlPage = parseInt(searchParams.get('page') || '1', 10) || 1;

  // Local state
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(urlPage);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Search input state with debouncing
  const [searchInput, setSearchInput] = useState(urlSearch);

  // Dynamic filter options state from DB
  const [filterOptions, setFilterOptions] = useState<FilterOptionsResponse | null>(null);
  const [isLoadingFilters, setIsLoadingFilters] = useState(true);

  // Mobile filter drawer state
  const [isMobileFilterOpen, setIsMobileFilterOpen] = useState(false);

  // Fetch dynamic filter options from database once on mount
  useEffect(() => {
    let isMounted = true;
    const fetchOptions = async () => {
      try {
        const options = await schemeApi.getFilterOptions();
        if (isMounted) {
          setFilterOptions(options);
        }
      } catch (err) {
        console.error('Failed to load dynamic filter options:', err);
      } finally {
        if (isMounted) {
          setIsLoadingFilters(false);
        }
      }
    };
    fetchOptions();
    return () => {
      isMounted = false;
    };
  }, []);

  // Synchronize local search input when URL changes externally
  useEffect(() => {
    setSearchInput(urlSearch);
    setPage(urlPage);
  }, [urlSearch, urlPage]);

  // Debounced search trigger (350ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== urlSearch) {
        updateFilterParams({ search: searchInput, page: 1 });
      }
    }, 350);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Centralized URL param updater
  const updateFilterParams = useCallback(
    (updates: Record<string, string | number | null | undefined>) => {
      const currentParams = new URLSearchParams(searchParams);

      Object.entries(updates).forEach(([key, val]) => {
        if (val === null || val === undefined || val === '') {
          currentParams.delete(key);
        } else {
          currentParams.set(key, String(val));
        }
      });

      // Reset to page 1 if changing any search/filter other than page
      if (!('page' in updates)) {
        currentParams.delete('page');
      }

      setSearchParams(currentParams, { replace: true });
    },
    [searchParams, setSearchParams]
  );

  // Fetch schemes from backend whenever URL query parameters change
  const fetchSchemes = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const queryParams: SchemeQueryParams = {
        page: urlPage,
        page_size: 12,
        search: urlSearch.trim() || undefined,
        ministry: urlMinistry || undefined,
        sector: urlSector || undefined,
        financial_type: urlFinancialType || undefined,
        beneficiary_category: urlBeneficiary || undefined,
        state_restriction: urlState || undefined,
        application_route: urlRoute || undefined,
        loan_available: urlLoanAvailable || undefined,
        subsidy_available: urlSubsidyAvailable || undefined,
        sort_by: urlSortBy || undefined,
        sort_order: urlSortOrder || undefined,
      };

      const data = await schemeApi.getSchemes(queryParams);
      setSchemes(data.items);
      setTotal(data.total);
      setTotalPages(data.pages);
      setPage(data.page);
    } catch (err: any) {
      setErrorMsg(t('errors.networkError') + ' ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  }, [
    urlPage,
    urlSearch,
    urlMinistry,
    urlSector,
    urlFinancialType,
    urlBeneficiary,
    urlState,
    urlRoute,
    urlLoanAvailable,
    urlSubsidyAvailable,
    urlSortBy,
    urlSortOrder,
    t,
  ]);

  useEffect(() => {
    fetchSchemes();
  }, [fetchSchemes]);

  // Handlers for individual filter changes
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateFilterParams({ search: searchInput.trim(), page: 1 });
  };

  const handleClearAll = () => {
    setSearchInput('');
    setSearchParams({});
  };

  const handlePageChange = (newPage: number) => {
    updateFilterParams({ page: newPage });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Count active filters (excluding sorting and page)
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (urlSearch) count++;
    if (urlMinistry) count++;
    if (urlSector) count++;
    if (urlFinancialType) count++;
    if (urlBeneficiary) count++;
    if (urlState) count++;
    if (urlRoute) count++;
    if (urlLoanAvailable) count++;
    if (urlSubsidyAvailable) count++;
    return count;
  }, [
    urlSearch,
    urlMinistry,
    urlSector,
    urlFinancialType,
    urlBeneficiary,
    urlState,
    urlRoute,
    urlLoanAvailable,
    urlSubsidyAvailable,
  ]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Personalized Recommendation Banner if Authenticated */}
      {isAuthenticated && (
        <div className="bg-gradient-to-r from-sky-900 to-indigo-900 rounded-2xl p-4 sm:p-5 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-md border border-sky-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/20 border border-sky-400/30 flex items-center justify-center shrink-0">
              <Sparkles className="w-5 h-5 text-sky-300" />
            </div>
            <div>
              <h2 className="text-sm font-bold tracking-tight">
                {t('schemes.findForMyProfile')}
              </h2>
              <p className="text-xs text-sky-200">
                {t('schemes.findForMyProfileDesc', 'Instantly check rule-based eligibility for all 90 schemes matching your citizen profile.')}
              </p>
            </div>
          </div>
          <Link
            to="/recommendations"
            className="whitespace-nowrap px-4 py-2 bg-white hover:bg-sky-50 text-sky-900 text-xs font-extrabold rounded-xl shadow transition shrink-0"
          >
            {t('nav.recommendations')} →
          </Link>
        </div>
      )}

      {/* Main Header & Global Search Bar */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="bg-sky-100 text-sky-800 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                {t('schemes.gazetteRepositoryBadge', 'GAZETTE VERIFIED REPOSITORY')}
              </span>
              <span className="text-xs text-slate-500 font-semibold">
                {filterOptions?.total_schemes || 90} {t('schemes.authoritativeCount', 'Schemes Authoritative')}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
              <Search className="w-7 h-7 text-sky-600" />
              {t('schemes.title')}
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl">
              {t('schemes.subtitle')}
            </p>
          </div>

          {/* Quick Actions / Mobile Filter Toggle */}
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              type="button"
              onClick={() => setIsMobileFilterOpen(true)}
              className="lg:hidden flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-900 text-white rounded-xl text-xs font-bold shadow transition"
            >
              <SlidersHorizontal className="w-4 h-4" />
              {t('schemes.mobileFilterBtn')}
              {activeFiltersCount > 0 && (
                <span className="bg-sky-500 text-white text-[10px] px-1.5 py-0.2 rounded-full font-bold">
                  {activeFiltersCount}
                </span>
              )}
            </button>

            {activeFiltersCount > 0 && (
              <button
                type="button"
                onClick={handleClearAll}
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold px-3.5 py-2.5 rounded-xl transition flex items-center gap-1.5 shadow-xs"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                {t('schemes.clearAll')}
              </button>
            )}
          </div>
        </div>

        {/* Global Multi-Field Search Input */}
        <form onSubmit={handleSearchSubmit} className="relative">
          <div className="relative flex items-center">
            <Search className="w-5 h-5 text-slate-400 absolute left-4 pointer-events-none" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder={t('schemes.searchPlaceholder')}
              className="w-full pl-12 pr-28 py-3.5 rounded-2xl border border-slate-300 text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none font-medium transition shadow-xs"
            />
            {searchInput && (
              <button
                type="button"
                onClick={() => {
                  setSearchInput('');
                  updateFilterParams({ search: '', page: 1 });
                }}
                className="absolute right-20 text-slate-400 hover:text-slate-600 p-1"
                aria-label="Clear Search Input"
              >
                <X className="w-4 h-4" />
              </button>
            )}
            <button
              type="submit"
              className="absolute right-2 bg-sky-600 hover:bg-sky-700 text-white font-bold px-4 py-2 rounded-xl text-xs shadow transition"
            >
              {t('home.searchButton') || "Search"}
            </button>
          </div>
        </form>

        {/* Desktop Multi-Dropdown Filter Bar */}
        <div className="hidden lg:grid grid-cols-5 gap-3 pt-1 border-t border-slate-100">
          {/* Ministry Filter */}
          <div>
            <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
              {t('schemes.filterMinistry')}
            </label>
            <select
              value={urlMinistry}
              onChange={(e) => updateFilterParams({ ministry: e.target.value, page: 1 })}
              className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white font-medium truncate"
            >
              <option value="">{t('schemes.allMinistries')}</option>
              {filterOptions?.ministries.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label} ({m.count})
                </option>
              ))}
            </select>
          </div>

          {/* Sector Filter */}
          <div>
            <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
              {t('schemes.filterSector')}
            </label>
            <select
              value={urlSector}
              onChange={(e) => updateFilterParams({ sector: e.target.value, page: 1 })}
              className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white font-medium truncate"
            >
              <option value="">{t('schemes.allSectors')}</option>
              {filterOptions?.sectors.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label} ({s.count})
                </option>
              ))}
            </select>
          </div>

          {/* Financial Type / Category */}
          <div>
            <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
              {t('schemes.filterFinancial')}
            </label>
            <select
              value={urlFinancialType}
              onChange={(e) => updateFilterParams({ financial_type: e.target.value, page: 1 })}
              className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white font-medium truncate"
            >
              <option value="">{t('schemes.allFinancialTypes')}</option>
              {filterOptions?.financial_types.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label} ({f.count})
                </option>
              ))}
            </select>
          </div>

          {/* Beneficiary Category */}
          <div>
            <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
              {t('schemes.filterBeneficiary')}
            </label>
            <select
              value={urlBeneficiary}
              onChange={(e) => updateFilterParams({ beneficiary_category: e.target.value, page: 1 })}
              className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white font-medium truncate"
            >
              <option value="">{t('schemes.allBeneficiaries')}</option>
              {filterOptions?.beneficiary_categories.map((b) => (
                <option key={b.value} value={b.value}>
                  {b.label} ({b.count})
                </option>
              ))}
            </select>
          </div>

          {/* Application Route */}
          <div>
            <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
              {t('schemes.filterRoute')}
            </label>
            <select
              value={urlRoute}
              onChange={(e) => updateFilterParams({ application_route: e.target.value, page: 1 })}
              className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white font-medium truncate"
            >
              <option value="">{t('schemes.allRoutes')}</option>
              {filterOptions?.application_routes.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label} ({r.count})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Active Filter Chips & Sorting Control Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-2 border-t border-slate-100 text-xs">
          {/* Active Filter Chips */}
          <div className="flex flex-wrap items-center gap-1.5 flex-1">
            <span className="text-slate-500 font-medium mr-1">
              {t('schemes.resultsCount', { shown: schemes.length, total })}
            </span>

            {urlSearch && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-sky-50 text-sky-800 border border-sky-200 font-semibold">
                Search: "{urlSearch}"
                <button
                  type="button"
                  onClick={() => updateFilterParams({ search: '' })}
                  className="hover:text-sky-950"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {urlMinistry && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 text-slate-800 border border-slate-300 font-semibold">
                Ministry: {urlMinistry}
                <button
                  type="button"
                  onClick={() => updateFilterParams({ ministry: '' })}
                  className="hover:text-slate-950"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {urlSector && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 text-slate-800 border border-slate-300 font-semibold">
                Sector: {urlSector}
                <button
                  type="button"
                  onClick={() => updateFilterParams({ sector: '' })}
                  className="hover:text-slate-950"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {urlFinancialType && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-300 font-semibold">
                Type: {urlFinancialType.replace(/_/g, ' ')}
                <button
                  type="button"
                  onClick={() => updateFilterParams({ financial_type: '' })}
                  className="hover:text-amber-950"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {urlBeneficiary && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-purple-50 text-purple-800 border border-purple-300 font-semibold">
                Target: {urlBeneficiary}
                <button
                  type="button"
                  onClick={() => updateFilterParams({ beneficiary_category: '' })}
                  className="hover:text-purple-950"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {urlRoute && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-300 font-semibold">
                {t('schemes.routeLabel', 'Route')}: {urlRoute.replace(/_/g, ' ')}
                <button
                  type="button"
                  onClick={() => updateFilterParams({ application_route: '' })}
                  className="hover:text-emerald-950"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
          </div>

          {/* Sorting Dropdown */}
          <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-bold text-slate-700">{t('schemes.sortBy')}:</span>
            <select
              value={`${urlSortBy}_${urlSortOrder}`}
              onChange={(e) => {
                const [sortField, sortDir] = e.target.value.split('_');
                updateFilterParams({ sort_by: sortField, sort_order: sortDir, page: 1 });
              }}
              className="px-3 py-1.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white font-semibold"
            >
              <option value="relevance_asc">{t('schemes.sortRelevance')}</option>
              <option value="scheme_name_asc">{t('schemes.sortNameAsc')}</option>
              <option value="scheme_name_desc">{t('schemes.sortNameDesc')}</option>
              <option value="max_loan_amount_desc">{t('schemes.sortMaxLoan')}</option>
              <option value="interest_rate_min_asc">{t('schemes.sortInterestRate')}</option>
              <option value="created_at_desc">{t('schemes.sortRecent')}</option>
            </select>
          </div>
        </div>
      </div>

      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* Schemes Grid */}
      {isLoading ? (
        <div className="py-20 text-center bg-white rounded-3xl border border-slate-200">
          <div className="w-10 h-10 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs text-slate-500 mt-3 font-medium">{t('errors.loading') || "Loading schemes..."}</p>
        </div>
      ) : schemes.length === 0 ? (
        /* Rich No-Result Experience with Recovery CTAs */
        <div className="py-16 text-center bg-white rounded-3xl border border-slate-200 p-8 max-w-2xl mx-auto shadow-sm space-y-6">
          <div className="w-16 h-16 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mx-auto">
            <Search className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-extrabold text-slate-900">
              {t('schemes.noSchemesTitle')}
            </h3>
            <p className="text-xs sm:text-sm text-slate-500 leading-relaxed max-w-md mx-auto">
              {t('schemes.noSchemesDesc')}
            </p>
          </div>

          {/* Popular Search Suggestions */}
          <div className="space-y-2 pt-2">
            <p className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              {t('schemes.trySuggestions')}
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {['MUDRA', 'PMEGP', 'PM Vishwakarma', 'Kisan', 'Scholarship', 'Women'].map((term) => (
                <button
                  key={term}
                  type="button"
                  onClick={() => {
                    setSearchInput(term);
                    updateFilterParams({ search: term, page: 1 });
                  }}
                  className="px-3 py-1 bg-sky-50 hover:bg-sky-100 text-sky-800 text-xs font-semibold rounded-full border border-sky-200 transition"
                >
                  {term}
                </button>
              ))}
            </div>
          </div>

          {/* Action Recovery Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={handleClearAll}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              {t('schemes.clearFilters')}
            </button>
            <Link
              to="/recommendations"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow transition"
            >
              <Sparkles className="w-3.5 h-3.5 text-sky-400" />
              {t('schemes.findForMyProfile')}
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {schemes.map((scheme) => (
              <SchemeCard key={scheme.scheme_id} scheme={scheme} />
            ))}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
              <span className="text-xs text-slate-500 font-medium">
                {t('schemes.pageCount', { page, totalPages, total })}
              </span>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => handlePageChange(page - 1)}
                  className="px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1 min-h-[44px]"
                >
                  <ChevronLeft className="w-4 h-4" />
                  {t('common.prev', 'Previous')}
                </button>

                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(totalPages, 7) }, (_, idx) => {
                    let pageNum: number;
                    if (totalPages <= 7) {
                      pageNum = idx + 1;
                    } else if (page <= 4) {
                      pageNum = idx + 1;
                    } else if (page >= totalPages - 3) {
                      pageNum = totalPages - 6 + idx;
                    } else {
                      pageNum = page - 3 + idx;
                    }

                    return (
                      <button
                        key={pageNum}
                        type="button"
                        onClick={() => handlePageChange(pageNum)}
                        className={`min-w-[38px] min-h-[38px] sm:w-8 sm:h-8 rounded-xl text-xs font-bold transition flex items-center justify-center ${
                          page === pageNum
                            ? 'bg-sky-600 text-white shadow-xs'
                            : 'text-slate-700 hover:bg-slate-100'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => handlePageChange(page + 1)}
                  className="px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1 min-h-[44px]"
                >
                  {t('common.next', 'Next')}
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Mobile / Tablet Filter Drawer Modal */}
      {isMobileFilterOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity"
            onClick={() => setIsMobileFilterOpen(false)}
          />

          {/* Slide-out Panel */}
          <div className="relative ml-auto w-full max-w-xs sm:max-w-sm bg-white h-full shadow-2xl p-6 overflow-y-auto flex flex-col justify-between space-y-6 z-10">
            <div className="space-y-5">
              <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  <SlidersHorizontal className="w-5 h-5 text-sky-600" />
                  <h3 className="font-extrabold text-slate-900 text-base">
                    {t('schemes.filterBy')}
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => setIsMobileFilterOpen(false)}
                  className="text-slate-400 hover:text-slate-700 p-1"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Mobile Ministries */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  {t('schemes.filterMinistry')}
                </label>
                <select
                  value={urlMinistry}
                  onChange={(e) => updateFilterParams({ ministry: e.target.value, page: 1 })}
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white font-medium"
                >
                  <option value="">{t('schemes.allMinistries')}</option>
                  {filterOptions?.ministries.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label} ({m.count})
                    </option>
                  ))}
                </select>
              </div>

              {/* Mobile Sectors */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  {t('schemes.filterSector')}
                </label>
                <select
                  value={urlSector}
                  onChange={(e) => updateFilterParams({ sector: e.target.value, page: 1 })}
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white font-medium"
                >
                  <option value="">{t('schemes.allSectors')}</option>
                  {filterOptions?.sectors.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label} ({s.count})
                    </option>
                  ))}
                </select>
              </div>

              {/* Mobile Financial Type */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  {t('schemes.filterFinancial')}
                </label>
                <select
                  value={urlFinancialType}
                  onChange={(e) => updateFilterParams({ financial_type: e.target.value, page: 1 })}
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white font-medium"
                >
                  <option value="">{t('schemes.allFinancialTypes')}</option>
                  {filterOptions?.financial_types.map((f) => (
                    <option key={f.value} value={f.value}>
                      {f.label} ({f.count})
                    </option>
                  ))}
                </select>
              </div>

              {/* Mobile Beneficiary Category */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  {t('schemes.filterBeneficiary')}
                </label>
                <select
                  value={urlBeneficiary}
                  onChange={(e) => updateFilterParams({ beneficiary_category: e.target.value, page: 1 })}
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white font-medium"
                >
                  <option value="">{t('schemes.allBeneficiaries')}</option>
                  {filterOptions?.beneficiary_categories.map((b) => (
                    <option key={b.value} value={b.value}>
                      {b.label} ({b.count})
                    </option>
                  ))}
                </select>
              </div>

              {/* Mobile Application Route */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  {t('schemes.filterRoute')}
                </label>
                <select
                  value={urlRoute}
                  onChange={(e) => updateFilterParams({ application_route: e.target.value, page: 1 })}
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white font-medium"
                >
                  <option value="">{t('schemes.allRoutes')}</option>
                  {filterOptions?.application_routes.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label} ({r.count})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Mobile Actions */}
            <div className="space-y-2 pt-4 border-t border-slate-200">
              <button
                type="button"
                onClick={() => setIsMobileFilterOpen(false)}
                className="w-full py-3 bg-sky-600 hover:bg-sky-700 text-white font-bold rounded-xl text-xs shadow transition"
              >
                {t('schemes.closeFilters')} ({total} {t('schemes.title') || 'Schemes'})
              </button>
              {activeFiltersCount > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    handleClearAll();
                    setIsMobileFilterOpen(false);
                  }}
                  className="w-full py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl text-xs transition"
                >
                  {t('schemes.clearAll')}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
