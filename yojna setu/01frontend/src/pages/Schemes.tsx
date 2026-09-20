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
  BookOpen,
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

  // Save scroll position for POP restoration on unmount/navigation
  useEffect(() => {
    return () => {
      const currentScroll = window.scrollY;
      if (currentScroll > 0) {
        window.history.replaceState(
          { ...window.history.state, yojnasetu_schemes_scroll: currentScroll },
          ''
        );
      }
    };
  }, []);

  // Restore scroll position on POP navigation after scheme cards are loaded
  useEffect(() => {
    if (!isLoading && schemes.length > 0) {
      const savedScroll = window.history.state?.yojnasetu_schemes_scroll;
      if (savedScroll != null && savedScroll > 0) {
        const timer = setTimeout(() => {
          window.scrollTo({ top: savedScroll, behavior: 'instant' });
        }, 50);
        return () => clearTimeout(timer);
      }
    }
  }, [isLoading, schemes.length]);

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
        <div className="bg-[#4A2525] rounded-2xl p-4 sm:p-5 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-warm-md border border-[#3B2522]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#FFF4EC]/15 border border-[#FFD0CA]/30 flex items-center justify-center shrink-0">
              <Sparkles className="w-5 h-5 text-[#F7AE56]" />
            </div>
            <div>
              <h2 className="text-sm font-bold tracking-tight text-[#FFFBF0]">
                {t('schemes.findForMyProfile', 'Find Schemes Matching Your Profile')}
              </h2>
              <p className="text-xs text-[#FFFBF0]/80">
                {t('schemes.findForMyProfileDesc', 'Instantly check rule-based eligibility for all schemes matching your citizen profile.')}
              </p>
            </div>
          </div>
          <Link
            to="/recommendations"
            className="whitespace-nowrap px-4 py-2 bg-[#EA717B] hover:bg-[#D65D67] text-white text-xs font-bold rounded-xl shadow-warm-xs transition shrink-0"
          >
            {t('nav.recommendations', 'Smart Matching')} →
          </Link>
        </div>
      )}
      {/* Main Header & Global Search Bar */}
      <div className="bg-white p-4 sm:p-6 lg:p-8 rounded-3xl border border-[#E8D8D2] shadow-warm-sm space-y-5 sm:space-y-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="bg-[#FFF4EC] text-[#4A2525] border border-[#E8D8D2] text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                {t('schemes.gazetteRepositoryBadge', 'GAZETTE VERIFIED REPOSITORY')}
              </span>
              <span className="text-xs text-[#765E59] font-semibold">
                {total > 0 ? total : (filterOptions?.total_schemes || 880)} {t('schemes.authoritativeCount', 'Schemes Indexed')}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-[#3B2522] tracking-tight flex items-center gap-2.5">
              <BookOpen className="w-7 h-7 text-[#EA717B] shrink-0" />
              {t('schemes.title', 'Explore Government Schemes')}
            </h1>
            <p className="text-xs sm:text-sm text-[#765E59] mt-1 max-w-2xl leading-relaxed">
              {t('schemes.subtitle', 'Search and filter central and state welfare, credit, and grant schemes.')}
            </p>
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            {/* Mobile Filter Drawer Button (< lg) */}
            <button
              type="button"
              onClick={() => setIsMobileFilterOpen(true)}
              className="lg:hidden flex-1 sm:flex-initial flex items-center justify-center gap-2 bg-[#FFF4EC] hover:bg-[#FFD0CA] text-[#4A2525] font-bold text-xs px-4 py-2.5 rounded-xl border border-[#E8D8D2] transition shadow-warm-xs min-h-[44px]"
            >
              <SlidersHorizontal className="w-4 h-4 text-[#EA717B] shrink-0" />
              <span>{t('schemes.filterTitle', 'Filters')}</span>
              {activeFiltersCount > 0 && (
                <span className="bg-[#EA717B] text-white text-[10px] font-extrabold w-5 h-5 rounded-full flex items-center justify-center shrink-0">
                  {activeFiltersCount}
                </span>
              )}
            </button>

            {activeFiltersCount > 0 && (
              <button
                type="button"
                onClick={handleClearAll}
                className="text-xs text-[#EA717B] hover:text-[#D65D67] font-bold flex items-center justify-center gap-1 bg-[#FFF4EC] hover:bg-[#FFD0CA]/40 px-3 py-2.5 rounded-xl border border-[#E8D8D2] transition min-h-[44px] shrink-0"
              >
                <X className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{t('schemes.resetAllFilters', 'Reset All')}</span>
              </button>
            )}
          </div>
        </div>

        {/* Global Multi-Field Search Input */}
        <form onSubmit={handleSearchSubmit} className="relative">
          <div className="relative flex items-center">
            <Search className="w-4 h-4 sm:w-5 sm:h-5 text-[#765E59] absolute left-3.5 sm:left-4 pointer-events-none" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder={t('schemes.searchPlaceholder', 'Search by scheme name, keyword, or benefits...')}
              className="w-full pl-10 sm:pl-12 pr-24 sm:pr-28 py-2.5 sm:py-3.5 rounded-2xl border border-[#E8D8D2] text-xs sm:text-sm focus:ring-2 focus:ring-[#EA717B] focus:border-[#EA717B] outline-none font-medium transition shadow-warm-xs bg-[#FFFBF0] text-[#3B2522] placeholder:text-[#765E59]"
            />
            {searchInput && (
              <button
                type="button"
                onClick={() => {
                  setSearchInput('');
                  updateFilterParams({ search: '', page: 1 });
                }}
                className="absolute right-18 sm:right-20 text-[#765E59] hover:text-[#3B2522] p-1"
                aria-label="Clear Search Input"
              >
                <X className="w-4 h-4" />
              </button>
            )}
            <button
              type="submit"
              className="absolute right-1.5 sm:right-2 bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold px-3.5 sm:px-5 py-1.5 sm:py-2 rounded-xl text-xs shadow-warm-xs transition min-h-[36px] flex items-center justify-center cursor-pointer"
            >
              {t('home.searchButton') || 'Search'}
            </button>
          </div>
        </form>

        {/* Quick Availability Filter Tabs (Matches Panel 2 Reference Mockup) */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-1 no-scrollbar text-xs font-bold">
          {[
            { id: 'ALL', label: 'All Schemes', count: filterOptions?.availability_counts?.['ALL'] ?? (total || undefined), params: { financial_type: null, application_route: null } },
            { id: 'PARTNERS', label: 'With Financial Partners', count: filterOptions?.availability_counts?.['PARTNERS'], params: { loan_available: 'true' } },
            { id: 'VERIFIED', label: 'Verified Info', count: filterOptions?.availability_counts?.['VERIFIED'], params: { route: 'OFFICIAL_PORTAL' } },
            { id: 'LIMITED', label: 'Limited Info', count: filterOptions?.availability_counts?.['LIMITED'], params: { route: 'ASSISTED' } },
            { id: 'DIRECT', label: 'Direct Departmental', count: filterOptions?.availability_counts?.['DIRECT'], params: { application_route: 'OFFICIAL_PORTAL' } },
          ].map((tab) => {
            const isSelected =
              tab.id === 'ALL'
                ? !urlFinancialType && !urlLoanAvailable
                : tab.id === 'PARTNERS'
                ? urlLoanAvailable === 'true'
                : false;

            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => {
                  if (tab.id === 'ALL') {
                    updateFilterParams({ financial_type: null, loan_available: null, application_route: null, page: 1 });
                  } else if (tab.id === 'PARTNERS') {
                    updateFilterParams({ loan_available: 'true', page: 1 });
                  } else if (tab.id === 'DIRECT') {
                    updateFilterParams({ application_route: 'OFFICIAL_PORTAL', page: 1 });
                  } else {
                    updateFilterParams(tab.params as any);
                  }
                }}
                className={`px-3.5 py-1.5 rounded-full whitespace-nowrap transition-all duration-150 flex items-center gap-1.5 shrink-0 cursor-pointer ${
                  isSelected
                    ? 'bg-[#EA717B] text-white shadow-warm-xs'
                    : 'bg-[#FFF4EC] hover:bg-[#FFD0CA]/60 text-[#4A2525] border border-[#E8D8D2]'
                }`}
              >
                <span>{tab.label}</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-extrabold ${isSelected ? 'bg-white/20 text-white' : 'bg-white text-[#765E59]'}`}>
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Active Filter Chips & Sorting Control Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-2 border-t border-[#E8D8D2]/60 text-xs">
          {/* Active Filter Chips */}
          <div className="flex flex-wrap items-center gap-1.5 flex-1">
            <span className="text-[#765E59] font-medium mr-1">
              {t('schemes.resultsCount', { shown: schemes.length, total })}
            </span>

            {urlSearch && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#FFF4EC] text-[#4A2525] border border-[#FFD0CA] font-semibold">
                Search: "{urlSearch}"
                <button
                  type="button"
                  onClick={() => updateFilterParams({ search: '' })}
                  className="hover:text-[#EA717B]"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {urlMinistry && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#FFF4EC] text-[#4A2525] border border-[#E8D8D2] font-semibold">
                Ministry: {urlMinistry}
                <button
                  type="button"
                  onClick={() => updateFilterParams({ ministry: '' })}
                  className="hover:text-[#EA717B]"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {urlSector && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#FFF4EC] text-[#4A2525] border border-[#E8D8D2] font-semibold">
                Sector: {urlSector}
                <button
                  type="button"
                  onClick={() => updateFilterParams({ sector: '' })}
                  className="hover:text-[#EA717B]"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {urlFinancialType && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#FFF4EC] text-[#4A2525] border border-[#F7AE56]/40 font-semibold">
                Type: {urlFinancialType.replace(/_/g, ' ')}
                <button
                  type="button"
                  onClick={() => updateFilterParams({ financial_type: '' })}
                  className="hover:text-[#EA717B]"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}

            {urlBeneficiary && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#FFF4EC] text-[#4A2525] border border-[#FFD0CA] font-semibold">
                Target: {urlBeneficiary}
                <button
                  type="button"
                  onClick={() => updateFilterParams({ beneficiary_category: '' })}
                  className="hover:text-[#EA717B]"
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
            <ArrowUpDown className="w-3.5 h-3.5 text-[#765E59]" />
            <span className="font-bold text-[#3B2522]">{t('schemes.sortBy')}:</span>
            <select
              value={`${urlSortBy}_${urlSortOrder}`}
              onChange={(e) => {
                const [sortField, sortDir] = e.target.value.split('_');
                updateFilterParams({ sort_by: sortField, sort_order: sortDir, page: 1 });
              }}
              className="px-3 py-1.5 rounded-xl border border-[#E8D8D2] text-xs focus:ring-2 focus:ring-[#EA717B] outline-none bg-white font-semibold text-[#3B2522]"
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

      {/* Main Content: Left Filter Sidebar + Right Schemes Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Filter Sidebar (Matches Reference Mockup Panel 2) */}
        <div className="hidden lg:block lg:col-span-3 bg-white p-5 rounded-2xl border border-[#E8D8D2] shadow-warm-xs space-y-5 sticky top-24">
          <div className="flex items-center justify-between pb-3 border-b border-[#E8D8D2]/60">
            <h3 className="text-sm font-bold text-[#3B2522] flex items-center gap-1.5">
              <Filter className="w-4 h-4 text-[#EA717B]" />
              <span>{t('common.filters', 'Filters')}</span>
            </h3>
            {activeFiltersCount > 0 && (
              <button
                type="button"
                onClick={handleClearAll}
                className="text-xs text-[#EA717B] hover:text-[#D65D67] font-bold cursor-pointer"
              >
                {t('schemes.clearAll', 'Clear All')}
              </button>
            )}
          </div>

          {/* Ministry list */}
          <div className="space-y-2">
            <span className="text-[11px] font-extrabold uppercase text-[#765E59] tracking-wider block">
              {t('schemes.ministry', 'Ministry')}
            </span>
            <div className="space-y-1 max-h-56 overflow-y-auto pr-1">
              <button
                type="button"
                onClick={() => updateFilterParams({ ministry: null, page: 1 })}
                className={`w-full text-left text-xs py-1.5 px-2 rounded-lg transition flex items-center justify-between cursor-pointer ${
                  !urlMinistry ? 'bg-[#FFF4EC] text-[#EA717B] font-bold border-l-2 border-[#EA717B]' : 'text-[#765E59] hover:bg-[#FFF4EC]/60'
                }`}
              >
                <span>{t('common.allMinistries', 'All Ministries')}</span>
                <span className="text-[10px] text-[#765E59] font-normal">({total || 859})</span>
              </button>
              {filterOptions?.ministries.slice(0, 10).map((m) => (
                <button
                  key={m.value}
                  type="button"
                  onClick={() => updateFilterParams({ ministry: m.value, page: 1 })}
                  className={`w-full text-left text-xs py-1.5 px-2 rounded-lg transition flex items-center justify-between truncate cursor-pointer ${
                    urlMinistry === m.value ? 'bg-[#FFF4EC] text-[#EA717B] font-bold border-l-2 border-[#EA717B]' : 'text-[#765E59] hover:bg-[#FFF4EC]/60'
                  }`}
                >
                  <span className="truncate pr-2">{m.label}</span>
                  <span className="text-[10px] text-[#765E59] font-normal shrink-0">({m.count})</span>
                </button>
              ))}
            </div>
          </div>

          {/* Beneficiary Type */}
          <div className="space-y-2 pt-3 border-t border-[#E8D8D2]/60">
            <span className="text-[11px] font-extrabold uppercase text-[#765E59] tracking-wider block">
              {t('schemes.beneficiaryType', 'Beneficiary Type')}
            </span>
            <div className="space-y-1 max-h-56 overflow-y-auto pr-1">
              <button
                type="button"
                onClick={() => updateFilterParams({ beneficiary_category: null, page: 1 })}
                className={`w-full text-left text-xs py-1.5 px-2 rounded-lg transition flex items-center justify-between cursor-pointer ${
                  !urlBeneficiary ? 'bg-[#FFF4EC] text-[#EA717B] font-bold border-l-2 border-[#EA717B]' : 'text-[#765E59] hover:bg-[#FFF4EC]/60'
                }`}
              >
                <span>{t('common.allBeneficiaries', 'All Beneficiaries')}</span>
              </button>
              {filterOptions?.beneficiary_categories.map((b) => (
                <button
                  key={b.value}
                  type="button"
                  onClick={() => updateFilterParams({ beneficiary_category: b.value, page: 1 })}
                  className={`w-full text-left text-xs py-1.5 px-2 rounded-lg transition flex items-center justify-between truncate cursor-pointer ${
                    urlBeneficiary === b.value ? 'bg-[#FFF4EC] text-[#EA717B] font-bold border-l-2 border-[#EA717B]' : 'text-[#765E59] hover:bg-[#FFF4EC]/60'
                  }`}
                >
                  <span className="truncate pr-2">{b.label}</span>
                  <span className="text-[10px] text-[#765E59] font-normal shrink-0">({b.count})</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Schemes Area */}
        <div className="lg:col-span-9 space-y-6">
          {/* Schemes Grid */}
          {isLoading ? (
            <div className="py-20 text-center bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs">
              <div className="w-10 h-10 border-4 border-[#EA717B] border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-xs text-[#765E59] mt-3 font-medium">{t('errors.loading') || "Loading schemes..."}</p>
            </div>
          ) : schemes.length === 0 ? (
            /* Rich No-Result Experience with Recovery CTAs */
            <div className="py-16 text-center bg-white rounded-3xl border border-[#E8D8D2] p-8 max-w-2xl mx-auto shadow-warm-sm space-y-6">
              <div className="w-16 h-16 bg-[#FFF4EC] text-[#765E59] rounded-full flex items-center justify-center mx-auto border border-[#FFD0CA]">
                <Search className="w-8 h-8" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-extrabold text-[#3B2522]">
                  {t('schemes.noSchemesTitle')}
                </h3>
                <p className="text-xs sm:text-sm text-[#765E59] leading-relaxed max-w-md mx-auto">
                  {t('schemes.noSchemesDesc')}
                </p>
              </div>

              {/* Popular Search Suggestions */}
              <div className="space-y-2 pt-2">
                <p className="text-xs font-bold text-[#3B2522] uppercase tracking-wider">
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
                      className="px-3 py-1 bg-[#FFF4EC] hover:bg-[#FFD0CA] text-[#4A2525] text-xs font-semibold rounded-full border border-[#E8D8D2] transition cursor-pointer"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>

              {/* Action Recovery Buttons */}
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4 border-t border-[#E8D8D2]/60">
                <button
                  type="button"
                  onClick={handleClearAll}
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 bg-[#EA717B] hover:bg-[#D65D67] text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow-warm-xs transition cursor-pointer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  {t('schemes.clearFilters')}
                </button>
                <Link
                  to="/recommendations"
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 bg-[#4A2525] hover:bg-[#3B2522] text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow-warm-xs transition"
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#F7AE56]" />
                  {t('schemes.findForMyProfile')}
                </Link>
              </div>
            </div>
          ) : (
            <div className="space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {schemes.map((scheme) => (
                  <SchemeCard key={scheme.scheme_id} scheme={scheme} />
                ))}
              </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="bg-white p-4 rounded-2xl border border-[#E8D8D2] shadow-warm-xs flex flex-col sm:flex-row items-center justify-between gap-4">
              <span className="text-xs text-[#765E59] font-medium">
                {t('schemes.pageCount', { page, totalPages, total })}
              </span>

              <div className="flex items-center justify-between sm:justify-center gap-2 w-full sm:w-auto">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => handlePageChange(page - 1)}
                  className="px-3 sm:px-3.5 py-2 rounded-xl border border-[#E8D8D2] text-xs font-bold text-[#765E59] hover:bg-[#FFF4EC] disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1 min-h-[44px] cursor-pointer"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>{t('common.prev', 'Previous')}</span>
                </button>

                {/* Mobile Compact Page Indicator (< sm) */}
                <span className="sm:hidden text-xs font-extrabold text-[#3B2522] px-2 whitespace-nowrap">
                  {page} / {totalPages}
                </span>

                {/* Desktop Numeric Page Buttons (>= sm) */}
                <div className="hidden sm:flex items-center gap-1">
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
                        className={`min-w-[38px] min-h-[38px] sm:w-8 sm:h-8 rounded-xl text-xs font-bold transition flex items-center justify-center cursor-pointer ${
                          page === pageNum
                            ? 'bg-[#EA717B] text-white shadow-warm-xs'
                            : 'text-[#765E59] hover:bg-[#FFF4EC]'
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
                  className="px-3 sm:px-3.5 py-2 rounded-xl border border-[#E8D8D2] text-xs font-bold text-[#765E59] hover:bg-[#FFF4EC] disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1 min-h-[44px] cursor-pointer"
                >
                  <span>{t('common.next', 'Next')}</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
            </div>
          )}
        </div>
      </div>

      {/* Mobile / Tablet Filter Drawer Modal */}
      {isMobileFilterOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-[#4A2525]/60 backdrop-blur-xs transition-opacity"
            onClick={() => setIsMobileFilterOpen(false)}
          />

          {/* Slide-out Panel */}
          <div className="relative ml-auto w-full max-w-xs sm:max-w-sm bg-[#FFFBF0] h-full shadow-warm-xl p-6 overflow-y-auto flex flex-col justify-between space-y-6 z-10 border-l border-[#E8D8D2]">
            <div className="space-y-5">
              <div className="flex items-center justify-between pb-4 border-b border-[#E8D8D2]">
                <div className="flex items-center gap-2">
                  <SlidersHorizontal className="w-5 h-5 text-[#EA717B]" />
                  <h3 className="font-extrabold text-[#3B2522] text-base">
                    {t('schemes.filterBy')}
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => setIsMobileFilterOpen(false)}
                  className="text-[#765E59] hover:text-[#3B2522] p-1 cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Mobile Ministries */}
              <div>
                <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1.5">
                  {t('schemes.filterMinistry')}
                </label>
                <select
                  value={urlMinistry}
                  onChange={(e) => updateFilterParams({ ministry: e.target.value, page: 1 })}
                  className="w-full px-3 py-2.5 rounded-xl border border-[#E8D8D2] text-xs focus:ring-2 focus:ring-[#EA717B] outline-none bg-white font-medium text-[#3B2522]"
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
                <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1.5">
                  {t('schemes.filterSector')}
                </label>
                <select
                  value={urlSector}
                  onChange={(e) => updateFilterParams({ sector: e.target.value, page: 1 })}
                  className="w-full px-3 py-2.5 rounded-xl border border-[#E8D8D2] text-xs focus:ring-2 focus:ring-[#EA717B] outline-none bg-white font-medium text-[#3B2522]"
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
                <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1.5">
                  {t('schemes.filterFinancial')}
                </label>
                <select
                  value={urlFinancialType}
                  onChange={(e) => updateFilterParams({ financial_type: e.target.value, page: 1 })}
                  className="w-full px-3 py-2.5 rounded-xl border border-[#E8D8D2] text-xs focus:ring-2 focus:ring-[#EA717B] outline-none bg-white font-medium text-[#3B2522]"
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
                <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1.5">
                  {t('schemes.filterBeneficiary')}
                </label>
                <select
                  value={urlBeneficiary}
                  onChange={(e) => updateFilterParams({ beneficiary_category: e.target.value, page: 1 })}
                  className="w-full px-3 py-2.5 rounded-xl border border-[#E8D8D2] text-xs focus:ring-2 focus:ring-[#EA717B] outline-none bg-white font-medium text-[#3B2522]"
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
                <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1.5">
                  {t('schemes.filterRoute')}
                </label>
                <select
                  value={urlRoute}
                  onChange={(e) => updateFilterParams({ application_route: e.target.value, page: 1 })}
                  className="w-full px-3 py-2.5 rounded-xl border border-[#E8D8D2] text-xs focus:ring-2 focus:ring-[#EA717B] outline-none bg-white font-medium text-[#3B2522]"
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
            <div className="space-y-2 pt-4 border-t border-[#E8D8D2]">
              <button
                type="button"
                onClick={() => setIsMobileFilterOpen(false)}
                className="w-full py-3 bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold rounded-xl text-xs shadow-warm-xs transition cursor-pointer"
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
                  className="w-full py-2.5 bg-[#FFF4EC] hover:bg-[#FFD0CA] text-[#4A2525] font-bold rounded-xl text-xs transition cursor-pointer border border-[#E8D8D2]"
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

