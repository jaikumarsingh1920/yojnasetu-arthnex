import React, { useState, useMemo } from 'react';
import { useParams, Link, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { partnerApi, SchemeFinancialDetail } from '../api/partnerApi';
import { FinancialStatusBadge } from '../components/FinancialStatusBadge';
import {
  cleanGovTitle,
  cleanGovDescription,
  normalizeGovText,
  splitOverviewAndDetails,
} from '../utils/textNormalization';
import {
  localizeGovMinistry,
  localizeGovSchemeTitle,
} from '../utils/civicLocalization';
import {
  Building2,
  ShieldCheck,
  Search,
  Filter,
  ArrowLeft,
  ChevronRight,
  ExternalLink,
  Info,
  Layers,
  Calendar,
  AlertCircle,
  MapPin,
  CheckCircle2,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Globe
} from 'lucide-react';

export const SchemeFinancialHealth: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { schemeId } = useParams<{ schemeId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();

  // Expandable description toggle state
  const [isFullDetailsOpen, setIsFullDetailsOpen] = useState<boolean>(false);

  // Filter state stored in URL query parameters so navigation / browser back preserves state
  const searchQuery = searchParams.get('q') || '';
  const selectedState = searchParams.get('state') || 'ALL';
  const selectedPartnerType = searchParams.get('type') || 'ALL';
  const selectedStatus = searchParams.get('status') || 'ALL';

  // TanStack Query caching (5 min fresh, instant restore on Back navigation with ZERO loading flash)
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<SchemeFinancialDetail>({
    queryKey: ['scheme-financial-health', schemeId],
    queryFn: () => partnerApi.getSchemeFinancialHealth(schemeId!),
    enabled: !!schemeId,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });

  const updateFilter = (key: string, value: string) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (!value || value === 'ALL') {
        next.delete(key);
      } else {
        next.set(key, value);
      }
      return next;
    }, { replace: true });
  };

  const clearAllFilters = () => {
    setSearchParams({}, { replace: true });
  };

  // Split scheme description into concise overview and full progressive details
  const { overviewText, fullDetailsText, hasExpandableDetails } = useMemo(() => {
    if (!data) return { overviewText: '', fullDetailsText: '', hasExpandableDetails: false };

    // Prefer backend pre-split if available, else use frontend utility
    if (data.overview && data.full_details && data.full_details !== data.overview) {
      return {
        overviewText: cleanGovDescription(data.overview),
        fullDetailsText: cleanGovDescription(data.full_details),
        hasExpandableDetails: true,
      };
    }

    const descToProcess = data.short_description || data.description || '';
    const { overview, fullDetails, hasMore } = splitOverviewAndDetails(descToProcess, 35);
    return {
      overviewText: overview,
      fullDetailsText: fullDetails,
      hasExpandableDetails: hasMore,
    };
  }, [data]);

  // Compute unique states and partner types from data
  const states = useMemo(() => {
    if (!data?.partners) return [];
    return Array.from(
      new Set(data.partners.map((p) => p.state).filter(Boolean) as string[])
    ).sort();
  }, [data?.partners]);

  const partnerTypes = useMemo(() => {
    if (!data?.partners) return [];
    return Array.from(
      new Set(
        data.partners
          .map((p) => p.institution_type || p.partner_type)
          .filter(Boolean) as string[]
      )
    ).sort();
  }, [data?.partners]);

  // Neutral Filter Evaluation (strictly preserving official / alphabetical order)
  const filteredPartners = useMemo(() => {
    if (!data?.partners) return [];
    const q = searchQuery.toLowerCase().trim();

    return data.partners.filter((p) => {
      const partnerName = cleanGovTitle(p.partner_name).toLowerCase();
      const instName = cleanGovTitle(p.institution_name || '').toLowerCase();
      const pCode = (p.partner_code || '').toLowerCase();

      const matchesSearch =
        !q ||
        partnerName.includes(q) ||
        instName.includes(q) ||
        pCode.includes(q);

      const matchesState =
        selectedState === 'ALL' || p.state === selectedState;

      const matchesType =
        selectedPartnerType === 'ALL' ||
        p.institution_type === selectedPartnerType ||
        p.partner_type === selectedPartnerType;

      const matchesStatus =
        selectedStatus === 'ALL' || p.financial_status?.code === selectedStatus;

      return matchesSearch && matchesState && matchesType && matchesStatus;
    });
  }, [data?.partners, searchQuery, selectedState, selectedPartnerType, selectedStatus]);

  if (isLoading && !data) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center space-y-4">
        <div className="w-12 h-12 border-4 border-gov-blue border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm font-bold text-slate-600">
          Loading scheme channel partners and financial indicators...
        </p>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-8 text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-rose-600 mx-auto" />
          <h2 className="text-lg font-black text-rose-900">{t('schemeFinancial.notFound', 'Scheme Financial Details Not Found')}</h2>
          <p className="text-xs text-rose-700 max-w-md mx-auto">
            {(error as any)?.message || 'The requested scheme could not be found.'}
          </p>
          <button
            onClick={() => navigate('/financial-health')}
            className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-4 py-2 rounded-xl transition cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Financial Health Hub
          </button>
        </div>
      </div>
    );
  }

  const cleanSchemeName = localizeGovSchemeTitle(cleanGovTitle(data.scheme_name), i18n.language);
  const cleanMinistry = localizeGovMinistry(cleanGovTitle(data.ministry), i18n.language);
  const hasPartners = data.total_channel_partners > 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-[#765E59] font-medium">
        <Link to="/" className="hover:text-[#EA717B] transition">{t('nav.home', 'Home')}</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to="/financial-health" className="hover:text-[#EA717B] transition">{t('nav.financialHealth', 'Financial Health')}</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-[#3B2522] font-bold truncate max-w-sm">{cleanSchemeName}</span>
      </nav>

      {/* Scheme Header Banner */}
      <div className="bg-gradient-to-br from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white rounded-3xl p-6 sm:p-8 shadow-warm-md border border-[#E8D8D2]/20 space-y-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="space-y-2.5 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="bg-white/10 text-[#F7AE56] border border-white/20 px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wider">
                {data.scheme_id}
              </span>
              {cleanMinistry && (
                <span className="bg-white/10 text-[#FFFBF0]/90 border border-white/20 px-2.5 py-1 rounded-full text-[10px] font-semibold">
                  {cleanMinistry}
                </span>
              )}
            </div>

            {/* Clean Scheme Title */}
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight leading-snug">
              {cleanSchemeName}
            </h1>

            {/* Concise Overview & Progressive Disclosure */}
            {overviewText && (
              <div className="space-y-2 pt-1">
                <p className="text-xs sm:text-sm text-[#FFFBF0]/85 leading-relaxed font-normal">
                  {overviewText}
                </p>

                {hasExpandableDetails && (
                  <div>
                    {isFullDetailsOpen && (
                      <div className="mt-3 p-4 bg-white/10 rounded-2xl border border-white/15 text-xs text-[#FFFBF0]/90 space-y-2 leading-relaxed whitespace-pre-line animate-fadeIn">
                        <span className="text-[11px] font-bold text-[#F7AE56] uppercase tracking-wider block">
                          {t('schemeDetail.fullSchemeInformation', 'Full Scheme Information')}
                        </span>
                        {fullDetailsText}
                      </div>
                    )}
                    <button
                      onClick={() => setIsFullDetailsOpen(!isFullDetailsOpen)}
                      className="inline-flex items-center gap-1.5 text-xs font-bold text-[#F7AE56] hover:text-white transition mt-1 cursor-pointer"
                    >
                      <span>{isFullDetailsOpen ? t('schemeDetail.showLess', 'Show less') : t('schemeDetail.readFullDetails', 'Read full scheme details')}</span>
                      {isFullDetailsOpen ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          <button
            onClick={() => navigate('/financial-health')}
            className="shrink-0 bg-white/10 hover:bg-white/20 text-[#FFFBF0] text-xs font-bold px-4 py-2.5 rounded-xl border border-white/20 transition flex items-center gap-2 cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" /> {t('financialHealth.tabAll', 'All Schemes')}
          </button>
        </div>

        {/* Aggregate Stat Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-white/15">
          <div className="bg-white/10 rounded-2xl p-3.5 border border-white/10 space-y-0.5">
            <span className="text-[11px] text-[#FFFBF0]/70 font-semibold block">{t('financialHealth.channelPartnersCount', 'Channel Partners')}</span>
            <span className="text-xl font-black text-white font-mono">{data.total_channel_partners}</span>
          </div>

          <div className="bg-white/10 rounded-2xl p-3.5 border border-white/10 space-y-0.5">
            <span className="text-[11px] text-emerald-300 font-semibold block">{t('financialHealth.tabVerified', 'Verified Info Available')}</span>
            <span className="text-xl font-black text-emerald-300 font-mono">{data.partners_with_verified_financial_info}</span>
          </div>

          <div className="bg-white/10 rounded-2xl p-3.5 border border-white/10 space-y-0.5">
            <span className="text-[11px] text-[#FFD0CA] font-semibold block">{t('financialHealth.limitedInfo', 'Limited Information')}</span>
            <span className="text-xl font-black text-[#FFD0CA] font-mono">{data.partners_with_limited_information}</span>
          </div>

          <div className="bg-white/10 rounded-2xl p-3.5 border border-white/10 space-y-0.5">
            <span className="text-[11px] text-[#F7AE56] font-semibold block">{t('schemeFinancial.latestReportingPeriod', 'Latest Reporting Period')}</span>
            <span className="text-sm font-bold text-white block truncate">{data.latest_reporting_period || '31 March 2024'}</span>
          </div>
        </div>
      </div>

      {/* Citizen Guidance Notice */}
      <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-2xl p-4 text-xs text-[#4A2525] flex items-start gap-3">
        <Info className="w-4 h-4 text-[#EA717B] shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-bold text-[#3B2522]">{t('financialHealth.statutoryNotice', 'Neutral Information Directory')}</p>
          <p className="text-[#765E59] leading-relaxed font-medium">
            Partners are displayed in neutral alphabetical order without ranking or preferential scoring. Financial figures describe the parent institution as a whole and do not guarantee loan approval or determine scheme eligibility.
          </p>
        </div>
      </div>

      {/* Channel Partner Search & Filtering (when partners exist) */}
      {hasPartners ? (
        <div className="space-y-6">
          <div className="bg-white border border-[#E8D8D2] rounded-2xl p-4 shadow-warm-xs space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Search Partner Name */}
              <div className="relative">
                <Search className="w-4 h-4 text-[#765E59] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => updateFilter('q', e.target.value)}
                  placeholder={t('financialHealth.searchPlaceholder', 'Search partner name or code...')}
                  aria-label="Search partner name"
                  className="w-full bg-[#FFFBF0] border border-[#E8D8D2] rounded-xl pl-9 pr-3 py-2 text-xs text-[#3B2522] placeholder:text-[#765E59]/60 outline-none focus:border-[#EA717B] focus:bg-white transition"
                />
              </div>

              {/* Filter State */}
              <div>
                <select
                  value={selectedState}
                  onChange={(e) => updateFilter('state', e.target.value)}
                  aria-label="Filter by State"
                  className="w-full bg-[#FFFBF0] border border-[#E8D8D2] text-[#3B2522] text-xs font-semibold rounded-xl px-3 py-2 outline-none focus:border-[#EA717B] transition cursor-pointer"
                >
                  <option value="ALL">{t('financialHealth.allStates', 'All States')} ({states.length})</option>
                  {states.map((st) => (
                    <option key={st} value={st}>
                      {st}
                    </option>
                  ))}
                </select>
              </div>

              {/* Filter Partner Type */}
              <div>
                <select
                  value={selectedPartnerType}
                  onChange={(e) => updateFilter('type', e.target.value)}
                  aria-label="Filter by Partner Type"
                  className="w-full bg-[#FFFBF0] border border-[#E8D8D2] text-[#3B2522] text-xs font-semibold rounded-xl px-3 py-2 outline-none focus:border-[#EA717B] transition cursor-pointer"
                >
                  <option value="ALL">{t('financialHealth.allPartnerTypes', 'All Partner Types')}</option>
                  {partnerTypes.map((pt) => (
                    <option key={pt} value={pt}>
                      {pt.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>

              {/* Filter Status */}
              <div>
                <select
                  value={selectedStatus}
                  onChange={(e) => updateFilter('status', e.target.value)}
                  aria-label="Filter by Financial Status"
                  className="w-full bg-[#FFFBF0] border border-[#E8D8D2] text-[#3B2522] text-xs font-semibold rounded-xl px-3 py-2 outline-none focus:border-[#EA717B] transition cursor-pointer"
                >
                  <option value="ALL">{t('financialHealth.allStatuses', 'All Financial Statuses')}</option>
                  <option value="STRONGER">{t('financialHealth.statusStronger', 'Financial position looks stronger')}</option>
                  <option value="MIXED">{t('financialHealth.statusMixed', 'Financial position is mixed')}</option>
                  <option value="HIGHER_STRESS">{t('financialHealth.statusAttention', 'Financial position needs attention')}</option>
                  <option value="LIMITED_DATA">{t('financialHealth.statusNotEnoughInfo', 'Not enough information')}</option>
                </select>
              </div>
            </div>

            {/* Results Counter */}
            <div className="flex items-center justify-between text-xs text-[#765E59] pt-2 border-t border-[#E8D8D2]">
              <span>
                {t('schemeFinancial.showingPartners', { count: filteredPartners.length, total: data.partners.length, defaultValue: `Showing ${filteredPartners.length} of ${data.partners.length} channel partners` })}
              </span>
              {(searchQuery || selectedState !== 'ALL' || selectedPartnerType !== 'ALL' || selectedStatus !== 'ALL') && (
                <button
                  onClick={clearAllFilters}
                  className="text-[#EA717B] hover:underline font-semibold cursor-pointer"
                >
                  {t('common.clearFilters', 'Clear filters')}
                </button>
              )}
            </div>
          </div>

          {/* Channel Partners List */}
          {filteredPartners.length === 0 ? (
            <div className="bg-white border border-[#E8D8D2] rounded-3xl p-12 text-center space-y-2 shadow-warm-xs">
              <Building2 className="w-10 h-10 text-[#765E59] mx-auto" />
              <h3 className="text-sm font-bold text-[#3B2522]">{t('schemeFinancial.noPartnersMatch', 'No channel partners match the selected filters')}</h3>
              <p className="text-xs text-[#765E59]">{t('schemeFinancial.adjustSearchPrompt', 'Try adjusting your search criteria or resetting filters.')}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredPartners.map((partner) => {
                const isNsfdcAuth = partner.nsfdc_authorized === 'AUTHORIZED';
                const evidenceCount = partner.financial_status?.evidence_count ?? 0;
                const evidenceText =
                  evidenceCount === 3
                    ? t('financialPartner.threeIndicators', 'Based on 3 verified financial indicators')
                    : evidenceCount === 2
                    ? t('financialPartner.twoIndicators', 'Based on 2 verified financial indicators')
                    : evidenceCount === 1
                    ? t('financialPartner.oneIndicator', 'Only limited verified financial information is available')
                    : t('financialPartner.noDataDesc', 'Not enough verified financial information is available');

                const locText =
                  partner.branch_location ||
                  (partner.city && partner.state
                    ? `${partner.city}, ${partner.state}`
                    : partner.state || 'Location not specified');

                const cleanInstName = cleanGovTitle(partner.institution_name || partner.partner_name);
                const cleanPartName = cleanGovTitle(partner.partner_name);

                return (
                  <div
                    key={partner.partner_id}
                    className="bg-white border border-[#E8D8D2] hover:border-[#FFD0CA] rounded-3xl p-5 shadow-warm-xs hover:shadow-warm-md transition-all flex flex-col justify-between space-y-4"
                  >
                    <div className="space-y-3">
                      {/* Badges */}
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider border ${
                            isNsfdcAuth
                              ? 'bg-[#2D6A4F]/10 text-[#2D6A4F] border-[#2D6A4F]/30'
                              : 'bg-[#F7AE56]/20 text-[#4A2525] border-[#F7AE56]/40'
                          }`}
                        >
                          <ShieldCheck className="w-3 h-3 text-[#2D6A4F]" />
                          {isNsfdcAuth ? 'NSFDC Channel Partner' : 'Channel Partner'}
                        </span>

                        <span className="bg-[#FFF4EC] text-[#4A2525] border border-[#FFD0CA] px-2 py-0.5 rounded-full text-[10px] font-bold">
                          Financial info: Institution-level
                        </span>
                      </div>

                      {/* Partner Name & Institution Details */}
                      <div>
                        <h3 className="text-base font-black text-[#3B2522] leading-snug">
                          {cleanInstName}
                        </h3>
                        {cleanInstName !== cleanPartName && (
                          <p className="text-xs text-[#765E59] font-medium">
                            Operating Center: {cleanPartName}
                          </p>
                        )}
                        <p className="text-xs text-[#765E59] flex items-center gap-1 mt-1">
                          <MapPin className="w-3.5 h-3.5 text-[#765E59]/70 shrink-0" />
                          <span>{locText}</span>
                        </p>
                      </div>

                      {/* Citizen Financial Position Badge */}
                      <div className="pt-2">
                        <FinancialStatusBadge status={partner.financial_status} size="sm" />
                        <p className="text-[11px] text-[#765E59] mt-1 font-medium">
                          {evidenceText}
                        </p>
                      </div>
                    </div>

                    {/* Card Action - Passes current search params so Back navigation preserves state */}
                    <div className="pt-3 border-t border-[#E8D8D2] flex items-center justify-between">
                      <span className="text-[10px] font-mono text-[#765E59]">
                        {partner.partner_code}
                      </span>
                      <Link
                        to={`/financial-health/partner/${partner.partner_id}?schemeId=${encodeURIComponent(
                          data.scheme_id
                        )}&schemeName=${encodeURIComponent(cleanSchemeName)}&returnSearch=${encodeURIComponent(
                          location.search
                        )}`}
                        className="inline-flex items-center gap-1.5 text-xs font-bold text-[#EA717B] hover:text-[#d65f69] hover:underline cursor-pointer"
                      >
                        <span>{t('common.viewDetails', 'View details')}</span>
                        <ChevronRight className="w-4 h-4" />
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        /* Direct Delivery Scheme Display (0 channel partners) */
        <div className="bg-white border border-[#E8D8D2] rounded-3xl p-8 text-center space-y-4 shadow-warm-xs">
          <div className="w-14 h-14 bg-[#FFF4EC] text-[#EA717B] border border-[#FFD0CA] rounded-full flex items-center justify-center mx-auto">
            <Globe className="w-7 h-7" />
          </div>
          <div className="space-y-2 max-w-lg mx-auto">
            <h2 className="text-lg font-black text-[#3B2522]">{t('schemeFinancial.directDelivery', 'Direct Departmental Delivery Scheme')}</h2>
            <p className="text-xs sm:text-sm text-[#765E59] leading-relaxed font-medium">
              {t('schemeFinancial.directDeliveryDesc', 'This scheme is administered directly by the government department or nodal authority through official digital application portals, without intermediary commercial channel partners.')}
            </p>
            <p className="text-xs text-[#765E59]/80 leading-relaxed">
              Because benefits are disbursed directly without external lending intermediaries, institutional partner financial balance sheets are not applicable for this scheme.
            </p>
          </div>
          <div className="pt-2">
            <Link
              to={`/schemes/${data.scheme_id}`}
              className="inline-flex items-center gap-2 bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold px-5 py-2.5 rounded-xl transition shadow-warm-xs"
            >
              <span>{t('schemeFinancial.viewCompleteGuidelines', 'View complete scheme guidelines & eligibility')}</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
