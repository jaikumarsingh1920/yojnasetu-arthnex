import React, { useState, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { partnerApi, SchemeFinancialSummary } from '../api/partnerApi';
import {
  cleanGovTitle,
  cleanGovDescription,
  normalizeGovText,
} from '../utils/textNormalization';
import {
  ShieldCheck,
  Search,
  Building2,
  CheckCircle2,
  HelpCircle,
  ArrowRight,
  Filter,
  Info,
  Layers,
  Calendar,
  AlertCircle,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Globe
} from 'lucide-react';

type AvailabilityTab = 'ALL' | 'WITH_PARTNERS' | 'VERIFIED' | 'LIMITED' | 'DIRECT';

export const FinancialHealthHub: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();

  // Filters from URL or default state
  const searchQuery = searchParams.get('q') || '';
  const selectedMinistry = searchParams.get('ministry') || 'ALL';
  const selectedTab = (searchParams.get('tab') as AvailabilityTab) || 'ALL';
  const currentPage = parseInt(searchParams.get('page') || '1', 10);

  // TanStack Query caching (prevents re-fetching on back navigation, 5 min fresh)
  const {
    data: schemes = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<SchemeFinancialSummary[]>({
    queryKey: ['financial-health-schemes'],
    queryFn: () => partnerApi.getFinancialHealthSchemes({ limit: 1000 }),
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });

  const updateParam = (updates: Record<string, string | null>) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      Object.entries(updates).forEach(([key, val]) => {
        if (!val || val === 'ALL' || (key === 'page' && val === '1')) {
          next.delete(key);
        } else {
          next.set(key, val);
        }
      });
      return next;
    }, { replace: true });
  };

  const handleSearchChange = (val: string) => {
    updateParam({ q: val || null, page: '1' });
  };

  const handleMinistryChange = (val: string) => {
    updateParam({ ministry: val, page: '1' });
  };

  const handleTabChange = (tab: AvailabilityTab) => {
    updateParam({ tab: tab === 'ALL' ? null : tab, page: '1' });
  };

  const handlePageChange = (page: number) => {
    updateParam({ page: page.toString() });
    window.scrollTo({ top: 400, behavior: 'smooth' });
  };

  // Unique ministries
  const ministries = useMemo(() => {
    return Array.from(
      new Set(schemes.map((s) => cleanGovTitle(s.ministry)).filter(Boolean))
    ).sort();
  }, [schemes]);

  // Aggregate stats dynamically computed from DB data
  const totalSchemesCount = schemes.length;
  const totalWithPartnersCount = useMemo(
    () => schemes.filter((s) => s.channel_partners_count > 0).length,
    [schemes]
  );
  const totalVerifiedSchemesCount = useMemo(
    () => schemes.filter((s) => (s.with_verified_financial_info_count || 0) > 0).length,
    [schemes]
  );
  const totalLimitedOnlySchemesCount = useMemo(
    () => schemes.filter((s) => s.channel_partners_count > 0 && (s.with_verified_financial_info_count || 0) === 0).length,
    [schemes]
  );
  const totalDirectDeliveryCount = useMemo(
    () => schemes.filter((s) => s.channel_partners_count === 0).length,
    [schemes]
  );

  const totalVerifiedPartners = useMemo(
    () => schemes.reduce((acc, s) => acc + (s.with_verified_financial_info_count || 0), 0),
    [schemes]
  );
  const totalLimitedPartners = useMemo(
    () => schemes.reduce((acc, s) => acc + (s.limited_information_count || 0), 0),
    [schemes]
  );

  // Filter evaluation with normalized text matching
  const filteredSchemes = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();

    return schemes.filter((s) => {
      const normTitle = cleanGovTitle(s.scheme_name).toLowerCase();
      const normDesc = cleanGovDescription(s.short_description || '').toLowerCase();
      const normMinistry = cleanGovTitle(s.ministry || '').toLowerCase();

      const matchesSearch =
        !q ||
        normTitle.includes(q) ||
        s.scheme_id.toLowerCase().includes(q) ||
        normDesc.includes(q) ||
        normMinistry.includes(q);

      const matchesMinistry =
        selectedMinistry === 'ALL' || cleanGovTitle(s.ministry) === selectedMinistry;

      let matchesTab = true;
      if (selectedTab === 'WITH_PARTNERS') {
        matchesTab = s.channel_partners_count > 0;
      } else if (selectedTab === 'VERIFIED') {
        matchesTab = (s.with_verified_financial_info_count || 0) > 0;
      } else if (selectedTab === 'LIMITED') {
        matchesTab = s.channel_partners_count > 0 && (s.with_verified_financial_info_count || 0) === 0;
      } else if (selectedTab === 'DIRECT') {
        matchesTab = s.channel_partners_count === 0;
      }

      return matchesSearch && matchesMinistry && matchesTab;
    });
  }, [schemes, searchQuery, selectedMinistry, selectedTab]);

  // Client-side pagination for optimal DOM performance
  const pageSize = 24;
  const totalPages = Math.max(1, Math.ceil(filteredSchemes.length / pageSize));
  const validCurrentPage = Math.min(Math.max(1, currentPage), totalPages);
  const paginatedSchemes = useMemo(() => {
    const start = (validCurrentPage - 1) * pageSize;
    return filteredSchemes.slice(start, start + pageSize);
  }, [filteredSchemes, validCurrentPage, pageSize]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-[#765E59] font-medium">
        <Link to="/" className="hover:text-[#EA717B] transition">Home</Link>
        <span>/</span>
        <span className="text-[#3B2522] font-bold">Financial Health</span>
      </nav>

      {/* Hero / Introduction Header */}
      <div className="bg-gradient-to-br from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white rounded-3xl p-6 sm:p-10 shadow-warm-md border border-[#E8D8D2]/20 space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-[#FFFBF0] text-xs font-bold border border-white/20">
          <ShieldCheck className="w-4 h-4 text-[#F7AE56]" />
          <span>Statutory Channel Partner Transparency</span>
        </div>

        <div className="space-y-2.5 max-w-3xl">
          <h1 className="text-2xl sm:text-4xl font-black text-white tracking-tight">
            Financial Health
          </h1>
          <p className="text-sm sm:text-base text-[#FFFBF0]/90 font-medium leading-relaxed">
            Understand publicly reported financial information about scheme channel partners.
          </p>
          <p className="text-xs sm:text-sm text-[#FFFBF0]/80 leading-relaxed font-normal">
            YojnaSetu shows verified statutory financial information where it is publicly available. You can explore this information scheme by scheme and partner by partner across all canonical government schemes.
          </p>
          <p className="text-xs sm:text-sm text-[#F7AE56] font-semibold pt-1">
            Select a scheme to see what verified financial information is available for its channel partners.
          </p>
        </div>

        {/* Scope and Disclaimer Notice */}
        <div className="p-3.5 bg-white/10 rounded-2xl border border-white/15 text-xs text-[#FFFBF0]/90 flex items-start gap-2.5 max-w-2xl">
          <Info className="w-4 h-4 text-[#F7AE56] shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong>Important notice:</strong> This information does not guarantee loan approval, faster processing, or financial safety. Scheme eligibility and loan approval are decided separately under scheme rules and the channel partner&apos;s process.
          </p>
        </div>

        {/* Dynamic Data Summary Across YojnaSetu */}
        {!isLoading && !isError && schemes.length > 0 && (
          <div className="pt-4 border-t border-white/15 space-y-3">
            <span className="text-[11px] uppercase tracking-wider text-[#F7AE56] font-extrabold block">
              Financial Information Coverage Across YojnaSetu
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-white/10 rounded-2xl p-3.5 border border-white/10 space-y-0.5">
                <span className="text-[11px] text-[#FFFBF0]/70 block font-medium">Canonical Schemes</span>
                <span className="text-xl font-black text-white font-mono">{totalSchemesCount} schemes</span>
              </div>
              <div className="bg-white/10 rounded-2xl p-3.5 border border-white/10 space-y-0.5">
                <span className="text-[11px] text-[#F7AE56] block font-medium">With Financial Partners</span>
                <span className="text-xl font-black text-[#F7AE56] font-mono">{totalWithPartnersCount} schemes</span>
              </div>
              <div className="bg-white/10 rounded-2xl p-3.5 border border-white/10 space-y-0.5">
                <span className="text-[11px] text-[#2D6A4F] block font-medium">Verified Partner Info</span>
                <span className="text-xl font-black text-[#2D6A4F] font-mono">{totalVerifiedPartners} records</span>
              </div>
              <div className="bg-white/10 rounded-2xl p-3.5 border border-white/10 space-y-0.5">
                <span className="text-[11px] text-[#FFD0CA] block font-medium">Direct Delivery</span>
                <span className="text-xl font-black text-[#FFD0CA] font-mono">{totalDirectDeliveryCount} schemes</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Explanation Banner */}
      <div className="bg-white border border-[#E8D8D2] rounded-3xl p-6 shadow-warm-xs space-y-3">
        <div className="flex items-center gap-2 text-[#3B2522]">
          <HelpCircle className="w-5 h-5 text-[#EA717B] shrink-0" />
          <h2 className="text-base font-black">What will I find here?</h2>
        </div>
        <p className="text-xs sm:text-sm text-[#3B2522] leading-relaxed font-medium">
          You can see the financial information publicly available for institutions that work as channel partners for government schemes.
        </p>
        <p className="text-xs sm:text-sm text-[#765E59] leading-relaxed">
          Where enough verified information is available, YojnaSetu provides a clear, citizen-friendly summary alongside the actual numbers and statutory regulatory sources. Direct delivery schemes without intermediary financial partners are also catalogued truthfully.
        </p>
      </div>

      {/* Explore by Scheme Controls */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-xl font-black text-[#3B2522] tracking-tight">
              Explore by scheme
            </h2>
            <p className="text-xs text-[#765E59] font-medium">
              Select a scheme to view all associated channel partners and their verified financial indicators.
            </p>
          </div>
        </div>

        {/* Availability Filter Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          <button
            onClick={() => handleTabChange('ALL')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
              selectedTab === 'ALL'
                ? 'bg-[#EA717B] text-white shadow-warm-xs'
                : 'bg-white text-[#765E59] hover:bg-[#FFF4EC] border border-[#E8D8D2]'
            }`}
          >
            All Schemes ({totalSchemesCount})
          </button>
          <button
            onClick={() => handleTabChange('WITH_PARTNERS')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
              selectedTab === 'WITH_PARTNERS'
                ? 'bg-[#EA717B] text-white shadow-warm-xs'
                : 'bg-white text-[#765E59] hover:bg-[#FFF4EC] border border-[#E8D8D2]'
            }`}
          >
            With Financial Partners ({totalWithPartnersCount})
          </button>
          <button
            onClick={() => handleTabChange('VERIFIED')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
              selectedTab === 'VERIFIED'
                ? 'bg-[#EA717B] text-white shadow-warm-xs'
                : 'bg-white text-[#765E59] hover:bg-[#FFF4EC] border border-[#E8D8D2]'
            }`}
          >
            Verified Information Available ({totalVerifiedSchemesCount})
          </button>
          <button
            onClick={() => handleTabChange('LIMITED')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
              selectedTab === 'LIMITED'
                ? 'bg-[#EA717B] text-white shadow-warm-xs'
                : 'bg-white text-[#765E59] hover:bg-[#FFF4EC] border border-[#E8D8D2]'
            }`}
          >
            Limited Information ({totalLimitedOnlySchemesCount})
          </button>
          <button
            onClick={() => handleTabChange('DIRECT')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
              selectedTab === 'DIRECT'
                ? 'bg-[#EA717B] text-white shadow-warm-xs'
                : 'bg-white text-[#765E59] hover:bg-[#FFF4EC] border border-[#E8D8D2]'
            }`}
          >
            Direct Departmental ({totalDirectDeliveryCount})
          </button>
        </div>

        {/* Filter and Search Bar */}
        <div className="bg-white border border-[#E8D8D2] rounded-2xl p-4 shadow-warm-xs flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-96">
            <Search className="w-4 h-4 text-[#765E59] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Search schemes by title, keyword, or code..."
              aria-label="Search schemes"
              className="w-full bg-[#FFFBF0] border border-[#E8D8D2] rounded-xl pl-10 pr-4 py-2 text-xs text-[#3B2522] placeholder:text-[#765E59]/60 outline-none focus:border-[#EA717B] focus:bg-white transition"
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
            <Filter className="w-4 h-4 text-[#765E59] shrink-0" />
            <span className="text-xs font-bold text-[#765E59] shrink-0">Ministry:</span>
            <select
              value={selectedMinistry}
              onChange={(e) => handleMinistryChange(e.target.value)}
              aria-label="Filter by Ministry"
              className="bg-[#FFFBF0] border border-[#E8D8D2] text-[#3B2522] text-xs font-semibold rounded-xl px-3 py-2 outline-none focus:border-[#EA717B] transition cursor-pointer max-w-xs truncate"
            >
              <option value="ALL">All Ministries ({ministries.length})</option>
              {ministries.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Active Filter Summary Counter */}
        <div className="flex items-center justify-between text-xs text-[#765E59] px-1">
          <span>
            Showing <strong className="text-[#3B2522] font-mono">{filteredSchemes.length}</strong> of{' '}
            <strong className="text-[#3B2522] font-mono">{totalSchemesCount}</strong> canonical schemes
          </span>
          {(searchQuery || selectedMinistry !== 'ALL' || selectedTab !== 'ALL') && (
            <button
              onClick={() => {
                setSearchParams({});
              }}
              className="text-[#EA717B] hover:underline font-semibold cursor-pointer"
            >
              Reset all filters
            </button>
          )}
        </div>
      </div>

      {/* Content Area */}
      {isLoading ? (
        <div className="py-20 text-center space-y-4">
          <div className="w-12 h-12 border-4 border-gov-blue border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-bold text-slate-600">
            Loading scheme channel partner financial indicators...
          </p>
        </div>
      ) : isError ? (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-8 text-center space-y-3">
          <AlertCircle className="w-10 h-10 text-rose-600 mx-auto" />
          <h2 className="text-base font-black text-rose-900">Failed to Load Financial Health Hub</h2>
          <p className="text-xs text-rose-700 max-w-md mx-auto">
            {(error as any)?.message || 'Failed to load scheme financial health coverage data.'}
          </p>
          <button
            onClick={() => refetch()}
            className="bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold px-4 py-2 rounded-xl transition cursor-pointer shadow-warm-xs"
          >
            Retry
          </button>
        </div>
      ) : filteredSchemes.length === 0 ? (
        <div className="bg-white border border-[#E8D8D2] rounded-3xl p-12 text-center space-y-2 shadow-warm-xs">
          <Building2 className="w-10 h-10 text-[#765E59] mx-auto" />
          <h3 className="text-sm font-bold text-[#3B2522]">No matching schemes found</h3>
          <p className="text-xs text-[#765E59]">Try adjusting your search query, tab, or ministry filter.</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {paginatedSchemes.map((scheme) => {
              const cleanTitle = cleanGovTitle(scheme.scheme_name);
              const cleanDesc = cleanGovDescription(scheme.short_description || scheme.overview, 30);
              const cleanMinistry = cleanGovTitle(scheme.ministry);
              const hasPartners = scheme.channel_partners_count > 0;

              return (
                <div
                  key={scheme.scheme_id}
                  className="bg-white border border-[#E8D8D2] hover:border-[#FFD0CA] rounded-3xl p-6 shadow-warm-xs hover:shadow-warm-md transition-all h-full flex flex-col justify-between space-y-4 group"
                >
                  <div className="space-y-3">
                    {/* Compact Ministry Header Badge */}
                    <div className="flex items-center justify-between gap-2">
                      <span className="bg-[#FFF4EC] text-[#4A2525] border border-[#FFD0CA] text-[11px] font-bold px-2.5 py-0.5 rounded-full truncate max-w-[210px]">
                        {cleanMinistry || 'Government Scheme'}
                      </span>
                      <span className="font-mono text-[10px] text-[#765E59] shrink-0">
                        {scheme.scheme_id}
                      </span>
                    </div>

                    {/* Scheme Name - Strong Hierarchy */}
                    <h3 className="text-base font-black text-[#3B2522] group-hover:text-[#EA717B] transition leading-snug line-clamp-2 min-h-[3rem]">
                      {cleanTitle}
                    </h3>

                    {/* Short Clean Description */}
                    <p className="text-xs text-[#765E59] line-clamp-2 leading-relaxed font-normal min-h-[2.5rem]">
                      {cleanDesc || 'Official central government scheme providing targeted assistance to eligible citizens.'}
                    </p>
                  </div>

                  {/* Partner Information Summary */}
                  <div className="space-y-3 pt-3 border-t border-[#E8D8D2]">
                    {hasPartners ? (
                      <div className="bg-[#FFFBF0] rounded-2xl p-3.5 space-y-2 text-xs border border-[#E8D8D2]">
                        <div className="flex items-center justify-between font-bold text-[#3B2522]">
                          <span className="flex items-center gap-1.5">
                            <Building2 className="w-3.5 h-3.5 text-[#765E59]" />
                            Channel partners
                          </span>
                          <span className="font-mono text-[#3B2522] font-extrabold text-sm">
                            {scheme.channel_partners_count} total
                          </span>
                        </div>

                        <div className="flex items-center justify-between text-[#765E59] text-[11px]">
                          <span className="flex items-center gap-1 text-[#2D6A4F] font-semibold">
                            <CheckCircle2 className="w-3.5 h-3.5 text-[#2D6A4F] shrink-0" />
                            Financial information available
                          </span>
                          <span className="font-mono font-bold text-[#2D6A4F]">
                            {scheme.with_verified_financial_info_count}
                          </span>
                        </div>

                        <div className="flex items-center justify-between text-[#765E59] text-[11px]">
                          <span className="flex items-center gap-1 text-[#765E59] font-medium">
                            <HelpCircle className="w-3.5 h-3.5 text-[#765E59] shrink-0" />
                            Limited information
                          </span>
                          <span className="font-mono font-bold text-[#765E59]">
                            {scheme.limited_information_count}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-2xl p-3.5 space-y-1.5 text-xs text-[#4A2525]">
                        <div className="flex items-center justify-between font-bold">
                          <span className="flex items-center gap-1.5 text-[#3B2522]">
                            <Globe className="w-3.5 h-3.5 text-[#EA717B]" />
                            Direct Delivery Scheme
                          </span>
                          <span className="font-mono text-[11px] font-bold text-[#4A2525] bg-[#FFD0CA] px-2 py-0.5 rounded-full">
                            Direct Agency
                          </span>
                        </div>
                        <p className="text-[11px] text-[#765E59] leading-relaxed">
                          Administered directly through departmental portals without intermediary banking partners.
                        </p>
                      </div>
                    )}

                    {/* Primary CTA */}
                    <Link
                      to={`/financial-health/scheme/${scheme.scheme_id}`}
                      className="w-full inline-flex items-center justify-center gap-2 bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold py-2.5 px-4 rounded-xl transition shadow-warm-xs group/btn"
                    >
                      <span>{hasPartners ? 'View financial information' : 'View scheme information'}</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 transition-transform" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="bg-white border border-[#E8D8D2] rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs shadow-warm-xs">
              <span className="text-[#765E59] font-medium">
                Showing page <strong className="text-[#3B2522] font-mono">{validCurrentPage}</strong> of{' '}
                <strong className="text-[#3B2522] font-mono">{totalPages}</strong> ({filteredSchemes.length} schemes)
              </span>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handlePageChange(validCurrentPage - 1)}
                  disabled={validCurrentPage === 1}
                  className="px-3 py-1.5 rounded-xl border border-[#E8D8D2] text-[#765E59] font-bold hover:bg-[#FFF4EC] disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1 cursor-pointer"
                >
                  <ChevronLeft className="w-4 h-4" /> Previous
                </button>

                <div className="hidden sm:flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum = i + 1;
                    if (totalPages > 5 && validCurrentPage > 3) {
                      pageNum = Math.min(validCurrentPage - 3 + i + 1, totalPages);
                    }
                    return (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={`w-8 h-8 rounded-xl font-mono text-xs font-bold transition cursor-pointer ${
                          validCurrentPage === pageNum
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
                  onClick={() => handlePageChange(validCurrentPage + 1)}
                  disabled={validCurrentPage === totalPages}
                  className="px-3 py-1.5 rounded-xl border border-[#E8D8D2] text-[#765E59] font-bold hover:bg-[#FFF4EC] disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1 cursor-pointer"
                >
                  Next <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SECTION: How this information works */}
      <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-3xl p-6 sm:p-8 space-y-4">
        <div className="flex items-center gap-2 text-[#3B2522]">
          <Info className="w-5 h-5 text-[#EA717B] shrink-0" />
          <h2 className="text-base font-black">How this information works</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs text-[#765E59]">
          <div className="bg-white p-4 rounded-2xl border border-[#E8D8D2] space-y-1.5 shadow-warm-xs">
            <span className="font-extrabold text-[#3B2522] block">1. Verified Statutory Data</span>
            <p className="text-[#765E59] leading-relaxed font-medium">
              Information is derived from verified public disclosures (such as RBI DBIE) and official annual regulatory returns.
            </p>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-[#E8D8D2] space-y-1.5 shadow-warm-xs">
            <span className="font-extrabold text-[#3B2522] block">2. Neutral Information Only</span>
            <p className="text-[#765E59] leading-relaxed font-medium">
              YojnaSetu does not rank, score, or recommend financial partners. All channel partners are shown in neutral alphabetical order.
            </p>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-[#E8D8D2] space-y-1.5 shadow-warm-xs">
            <span className="font-extrabold text-[#3B2522] block">3. Institution-Level Scope</span>
            <p className="text-[#765E59] leading-relaxed font-medium">
              Statutory balance sheet figures describe the banking institution as a corporate whole, not any individual local branch.
            </p>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-[#E8D8D2] space-y-1.5 shadow-warm-xs">
            <span className="font-extrabold text-[#3B2522] block">4. Separate Scheme Rules</span>
            <p className="text-[#765E59] leading-relaxed font-medium">
              Financial information does not determine scheme eligibility or loan approvals. Those are processed independently under scheme rules.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
