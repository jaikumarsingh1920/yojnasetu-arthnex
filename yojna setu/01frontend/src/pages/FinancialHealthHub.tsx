import React, { useState, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { partnerApi, SchemeFinancialSummary } from '../api/partnerApi';
import {
  cleanGovTitle,
  cleanGovDescription,
} from '../utils/textNormalization';
import {
  localizeGovMinistry,
  localizeGovSchemeTitle,
  localizeGovDescription,
} from '../utils/civicLocalization';
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
  ChevronDown,
  Globe,
  Landmark,
  Check,
  Coins,
  BarChart3,
  Lightbulb,
  Shield,
  FileText,
  Scale
} from 'lucide-react';

type AvailabilityTab = 'ALL' | 'WITH_PARTNERS' | 'VERIFIED' | 'LIMITED' | 'DIRECT';

export const FinancialHealthHub: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();

  // Accordion state for educational disclosure
  const [isEducationOpen, setIsEducationOpen] = useState(false);

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
    <div className="min-h-screen bg-[#FFFBF0] font-sans">
      <div className="max-w-[1500px] mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-8">
        {/* 1. Breadcrumb Navigation */}
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-[#765E59] font-medium">
          <Link to="/" className="hover:text-[#EA717B] transition">{t('nav.home', 'Home')}</Link>
          <ChevronRight className="w-3.5 h-3.5 text-[#765E59]/50 shrink-0" />
          <span className="text-[#3B2522] font-bold">{t('nav.financialHealth', 'Financial Health')}</span>
        </nav>

        {/* 2. Hero Banner matching PartnerFinancialHealth visual standard */}
        <div className="bg-gradient-to-br from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white rounded-3xl p-6 sm:p-8 lg:p-10 shadow-warm-md border border-[#E8D8D2]/20 relative overflow-hidden space-y-6">
          {/* Top Badges */}
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
              <Check className="w-3.5 h-3.5 text-emerald-300" />
              <span>{t('financialHealth.statutoryTransparencyBadge', 'Statutory Channel Partner Transparency')}</span>
            </span>

            <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-medium bg-white/10 text-[#FFFBF0] border border-white/20">
              <Info className="w-3.5 h-3.5 text-[#F7AE56]" />
              <span>{t('financialHealth.rbiDisclosuresBadge', 'RBI & Statutory Public Disclosures')}</span>
            </span>
          </div>

          {/* Hero Middle Grid: Bank/Civic Icon + Headings + Scope Box */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-8 flex items-start gap-4 sm:gap-5">
              {/* Orange Square Bank Icon */}
              <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-[#EA717B] flex items-center justify-center text-white shrink-0 shadow-warm-xs">
                <Landmark className="w-8 h-8 sm:w-9 sm:h-9" />
              </div>

              <div className="space-y-2 min-w-0">
                <h1 className="text-2xl sm:text-4xl font-black text-white tracking-tight">
                  {t('financialHealth.hubTitle', 'Financial Health & Statutory Transparency')}
                </h1>
                <p className="text-xs sm:text-sm text-[#FFFBF0]/85 leading-relaxed max-w-2xl">
                  {t('financialHealth.hubSubtitle', 'Understand publicly reported financial intelligence about government scheme channel partners. YojnaSetu presents verified statutory indicators (Net NPA, Gross NPA, CRAR) published under RBI and statutory guidelines to empower citizens before they apply.')}
                </p>
                <p className="text-xs text-[#F7AE56] font-semibold pt-1">
                  {t('financialHealth.hubHint', 'Select any welfare scheme below to inspect verified financial stability figures for its implementing banks and state corporations.')}
                </p>
              </div>
            </div>

            {/* Right Scope Card */}
            <div className="lg:col-span-4 bg-white/10 backdrop-blur-md rounded-2xl p-4 sm:p-5 border border-white/15 flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-300 flex items-center justify-center shrink-0 mt-0.5">
                <ShieldCheck className="w-5 h-5 text-emerald-300" />
              </div>
              <p className="text-xs text-[#FFFBF0]/90 leading-relaxed font-medium">
                <strong>{t('financialHealth.institutionalScopeTitle', 'Institutional Scope:')}</strong>{' '}
                {t('financialHealth.institutionalScopeDesc', 'Figures represent corporate parent institutions under RBI disclosures. Financial indicators do not guarantee loan sanction or determine individual scheme eligibility.')}
              </p>
            </div>
          </div>
        </div>

        {/* 3. 4 Interactive Summary KPI Cards */}
        {!isLoading && !isError && schemes.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
            {/* Card 1: Canonical Schemes */}
            <div className="bg-white rounded-2xl p-5 border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-1 hover:border-[#EA717B]/40 transition-all duration-200 group flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-[#FFF4EC] text-[#EA717B] border border-[#FFD0CA] flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Landmark className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-bold text-[#765E59] uppercase tracking-wider bg-[#FFFBF0] px-2.5 py-0.5 rounded-full border border-[#E8D8D2]">
                    {t('financialHealth.centralAndState', 'Central & State')}
                  </span>
                </div>
                <div>
                  <span className="text-2xl sm:text-3xl font-black text-[#2B1810] font-mono block">
                    {totalSchemesCount}
                  </span>
                  <span className="text-xs font-bold text-[#3B2522] block mt-0.5">
                    {t('financialHealth.canonicalSchemes', 'Canonical Schemes')}
                  </span>
                </div>
              </div>
              <p className="text-[11px] text-[#765E59] mt-3 pt-2.5 border-t border-[#E8D8D2]">
                {t('financialHealth.canonicalSchemesDesc', 'Gazetted welfare programs tracked across ministries')}
              </p>
            </div>

            {/* Card 2: With Financial Partners */}
            <div className="bg-white rounded-2xl p-5 border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-1 hover:border-[#F7AE56]/40 transition-all duration-200 group flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-[#FFF4EC] text-[#F7AE56] border border-[#FCD9B4] flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-bold text-[#F7AE56] uppercase tracking-wider bg-[#FFF4EC] px-2.5 py-0.5 rounded-full border border-[#FCD9B4]">
                    {t('financialHealth.partnered', 'Partnered')}
                  </span>
                </div>
                <div>
                  <span className="text-2xl sm:text-3xl font-black text-[#2B1810] font-mono block">
                    {totalWithPartnersCount}
                  </span>
                  <span className="text-xs font-bold text-[#3B2522] block mt-0.5">
                    {t('financialHealth.withFinancialPartners', 'With Financial Partners')}
                  </span>
                </div>
              </div>
              <p className="text-[11px] text-[#765E59] mt-3 pt-2.5 border-t border-[#E8D8D2]">
                {t('financialHealth.withFinancialPartnersDesc', 'Delivered via scheduled commercial banks & SCAs')}
              </p>
            </div>

            {/* Card 3: Verified Partner Info */}
            <div className="bg-white rounded-2xl p-5 border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-1 hover:border-[#2D6A4F]/40 transition-all duration-200 group flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-[#EAF4EE] text-[#2D6A4F] border border-[#2D6A4F]/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-bold text-[#2D6A4F] uppercase tracking-wider bg-[#EAF4EE] px-2.5 py-0.5 rounded-full border border-[#2D6A4F]/20">
                    {t('financialHealth.rbiVerified', 'RBI Verified')}
                  </span>
                </div>
                <div>
                  <span className="text-2xl sm:text-3xl font-black text-[#2D6A4F] font-mono block">
                    {totalVerifiedPartners}
                  </span>
                  <span className="text-xs font-bold text-[#3B2522] block mt-0.5">
                    {t('financialHealth.verifiedPartnerRecords', 'Verified Partner Records')}
                  </span>
                </div>
              </div>
              <p className="text-[11px] text-[#765E59] mt-3 pt-2.5 border-t border-[#E8D8D2]">
                {t('financialHealth.verifiedPartnerRecordsDesc', 'Public statutory indicators & balance disclosures')}
              </p>
            </div>

            {/* Card 4: Direct Delivery */}
            <div className="bg-white rounded-2xl p-5 border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-1 hover:border-[#EA717B]/40 transition-all duration-200 group flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-[#FFF4EC] text-[#4A2525] border border-[#E8D8D2] flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Globe className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-bold text-[#765E59] uppercase tracking-wider bg-[#FFFBF0] px-2.5 py-0.5 rounded-full border border-[#E8D8D2]">
                    {t('financialHealth.directDbt', 'Direct DBT')}
                  </span>
                </div>
                <div>
                  <span className="text-2xl sm:text-3xl font-black text-[#2B1810] font-mono block">
                    {totalDirectDeliveryCount}
                  </span>
                  <span className="text-xs font-bold text-[#3B2522] block mt-0.5">
                    {t('financialHealth.directDeliverySchemes', 'Direct Delivery Schemes')}
                  </span>
                </div>
              </div>
              <p className="text-[11px] text-[#765E59] mt-3 pt-2.5 border-t border-[#E8D8D2]">
                {t('financialHealth.directDeliverySchemesDesc', 'Direct government benefit transfer without banking intermediaries')}
              </p>
            </div>
          </div>
        )}

        {/* 4. 4-Pillar Information Guidance Grid */}
        <div className="bg-white border border-[#E8D8D2] rounded-3xl p-6 sm:p-8 shadow-warm-xs space-y-5">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 text-[#3B2522]">
              <div className="w-8 h-8 rounded-lg bg-[#FFF4EC] text-[#EA717B] border border-[#FFD0CA] flex items-center justify-center">
                <HelpCircle className="w-4 h-4" />
              </div>
              <h2 className="text-lg font-black tracking-tight">{t('financialHealth.understandingTitle', 'Understanding Channel Partner Information')}</h2>
            </div>
            <span className="text-[11px] font-bold text-[#765E59] bg-[#FFFBF0] px-3 py-1 rounded-full border border-[#E8D8D2] hidden sm:inline-block">
              {t('financialHealth.transparencyFramework', 'Transparency Framework')}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-[#EAF4EE] border border-[#2D6A4F]/20 space-y-2">
              <div className="flex items-center gap-2 text-[#2D6A4F] font-bold text-xs">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{t('financialHealth.whatThisMeansTitle', 'What this means')}</span>
              </div>
              <p className="text-xs text-[#3B2522] leading-relaxed">
                {t('financialHealth.whatThisMeansDesc', 'Public statutory and regulatory disclosures regarding institutional partners that implement government welfare programs.')}
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-[#FFF4EC] border border-[#F7AE56]/30 space-y-2">
              <div className="flex items-center gap-2 text-[#B45309] font-bold text-xs">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{t('financialHealth.whatItDoesNotMeanTitle', 'What it does NOT mean')}</span>
              </div>
              <p className="text-xs text-[#3B2522] leading-relaxed">
                {t('financialHealth.whatItDoesNotMeanDesc', 'Not a guarantee of loan sanction, priority approval, investment safety, or commercial credit endorsement.')}
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-[#FFF4EC] border border-[#FFD0CA] space-y-2">
              <div className="flex items-center gap-2 text-[#EA717B] font-bold text-xs">
                <Building2 className="w-4 h-4 shrink-0" />
                <span>{t('financialHealth.whereDataFromTitle', 'Where data comes from')}</span>
              </div>
              <p className="text-xs text-[#3B2522] leading-relaxed">
                {t('financialHealth.whereDataFromDesc', 'Official RBI regulatory filings, scheduled bank disclosures, state corporation audits, and gazetted portal registers.')}
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-[#FFFBF0] border border-[#E8D8D2] space-y-2">
              <div className="flex items-center gap-2 text-[#4A2525] font-bold text-xs">
                <Info className="w-4 h-4 shrink-0" />
                <span>{t('financialHealth.howToInterpretTitle', 'How to interpret')}</span>
              </div>
              <p className="text-xs text-[#3B2522] leading-relaxed">
                {t('financialHealth.howToInterpretDesc', 'Use to understand which partners operate in your area and their institutional scale before applying for schemes.')}
              </p>
            </div>
          </div>
        </div>

        {/* RESTORED: YS-FIS-V1 Citizen Financial Health Interpretation Framework Section */}
        <div className="bg-white border border-[#E8D8D2] rounded-3xl p-6 sm:p-8 shadow-warm-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E8D8D2] pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-[#FFF4EC] text-[#EA717B] border border-[#FFD0CA] flex items-center justify-center shrink-0">
                <Scale className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg sm:text-xl font-black text-[#3B2522] tracking-tight">
                  {t('financialHealth.frameworkTitle', 'Citizen Financial Health Interpretation Framework (YS-FIS-V1)')}
                </h2>
                <p className="text-xs text-[#765E59] mt-0.5">
                  {t('financialHealth.frameworkSubtitle', 'How YojnaSetu deterministically maps verified statutory indicators into citizen-friendly financial positions')}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs font-bold shrink-0">
              <span className="bg-[#FFF4EC] text-[#4A2525] px-3 py-1 rounded-full border border-[#FFD0CA]">
                Engine: YS-FIS-V1
              </span>
              <span className="bg-[#EAF4EE] text-[#2D6A4F] px-3 py-1 rounded-full border border-[#2D6A4F]/20">
                Zero Synthetic Data
              </span>
            </div>
          </div>

          {/* 4 Deterministic Presentation Bands */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Band 1: Stronger */}
            <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-50/60 to-white border border-emerald-200 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-1 text-[11px] font-black uppercase text-emerald-800 bg-emerald-100/70 px-2.5 py-0.5 rounded-full border border-emerald-300">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                  Stronger
                </span>
                <span className="text-[10px] font-mono font-bold text-emerald-700">Code: STRONGER</span>
              </div>
              <h3 className="text-sm font-extrabold text-[#2B1810]">
                {t('financialHealth.statusStrongerTitle', 'Financial position looks stronger')}
              </h3>
              <p className="text-xs text-[#765E59] leading-relaxed">
                Reported loan problems are lower and capital is in a stronger range across public filings.
              </p>
              <div className="p-2 rounded-xl bg-white/80 border border-emerald-100 text-[10px] font-mono text-emerald-900 space-y-0.5">
                <div>NNPA &le; 1.0%</div>
                <div>GNPA &le; 3.0%</div>
                <div>CRAR &ge; 12.0%</div>
              </div>
            </div>

            {/* Band 2: Mixed */}
            <div className="p-4 rounded-2xl bg-gradient-to-br from-amber-50/60 to-white border border-amber-200 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-1 text-[11px] font-black uppercase text-amber-800 bg-amber-100/70 px-2.5 py-0.5 rounded-full border border-amber-300">
                  <AlertCircle className="w-3 h-3 text-amber-600" />
                  Mixed
                </span>
                <span className="text-[10px] font-mono font-bold text-amber-700">Code: MIXED</span>
              </div>
              <h3 className="text-sm font-extrabold text-[#2B1810]">
                {t('financialHealth.statusMixedTitle', 'Financial position is mixed')}
              </h3>
              <p className="text-xs text-[#765E59] leading-relaxed">
                Some indicators are in stronger ranges while others are in the middle band requiring attention.
              </p>
              <div className="p-2 rounded-xl bg-white/80 border border-amber-100 text-[10px] font-mono text-amber-900 space-y-0.5">
                <div>1.0% &lt; NNPA &le; 3.0%</div>
                <div>3.0% &lt; GNPA &le; 7.0%</div>
                <div>9.0% &le; CRAR &lt; 12.0%</div>
              </div>
            </div>

            {/* Band 3: Needs Attention */}
            <div className="p-4 rounded-2xl bg-gradient-to-br from-rose-50/60 to-white border border-rose-200 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-1 text-[11px] font-black uppercase text-rose-800 bg-rose-100/70 px-2.5 py-0.5 rounded-full border border-rose-300">
                  <AlertCircle className="w-3 h-3 text-rose-600" />
                  Needs Attention
                </span>
                <span className="text-[10px] font-mono font-bold text-rose-700">Code: HIGHER_STRESS</span>
              </div>
              <h3 className="text-sm font-extrabold text-[#2B1810]">
                {t('financialHealth.statusStressTitle', 'Financial position needs attention')}
              </h3>
              <p className="text-xs text-[#765E59] leading-relaxed">
                One or more reported numbers fall into higher stress ranges. Does not disqualify official schemes where authorized.
              </p>
              <div className="p-2 rounded-xl bg-white/80 border border-rose-100 text-[10px] font-mono text-rose-900 space-y-0.5">
                <div>NNPA &gt; 3.0% OR</div>
                <div>GNPA &gt; 7.0% OR</div>
                <div>CRAR &lt; 9.0%</div>
              </div>
            </div>

            {/* Band 4: Limited Information */}
            <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-50/80 to-white border border-[#E8D8D2] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-1 text-[11px] font-black uppercase text-slate-800 bg-slate-100 px-2.5 py-0.5 rounded-full border border-slate-300">
                  <HelpCircle className="w-3 h-3 text-slate-600" />
                  Not Enough Info
                </span>
                <span className="text-[10px] font-mono font-bold text-slate-600">Code: LIMITED_DATA</span>
              </div>
              <h3 className="text-sm font-extrabold text-[#2B1810]">
                {t('financialHealth.statusLimitedTitle', 'Not enough information')}
              </h3>
              <p className="text-xs text-[#765E59] leading-relaxed">
                Fewer than 2 verified public indicators exist. Under data governance rules, missing values are never guessed.
              </p>
              <div className="p-2 rounded-xl bg-white/80 border border-slate-200 text-[10px] font-mono text-slate-700 space-y-0.5">
                <div>Evidence count &lt; 2</div>
                <div>Unresolved entity</div>
                <div>Zero synthetic fill</div>
              </div>
            </div>
          </div>

          {/* Governance & Disclaimer Banner */}
          <div className="p-4 bg-[#FFFBF0] rounded-2xl border border-[#E8D8D2] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-[#765E59]">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-[#EA717B] shrink-0" />
              <span>
                <strong>Important Boundary:</strong> Indicators represent institution-level statutory disclosures and do not guarantee loan sanction, individual scheme eligibility, or financial safety.
              </span>
            </div>
            <Link
              to="/resources"
              className="text-[#EA717B] hover:underline font-bold whitespace-nowrap shrink-0"
            >
              Learn more in Governance &rarr;
            </Link>
          </div>
        </div>

        {/* 5. Explore by Scheme Controls with Segmented Tabs */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-xl font-black text-[#3B2522] tracking-tight">
                {t('financialHealth.exploreByScheme', 'Explore by scheme')}
              </h2>
              <p className="text-xs text-[#765E59] font-medium">
                {t('financialHealth.exploreBySchemeSubtitle', 'Select a scheme to view all associated channel partners and their verified financial indicators.')}
              </p>
            </div>
          </div>

          {/* Segmented Tab Bar matching PartnerFinancialHealth tab style */}
          <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs p-1.5 flex items-center gap-1.5 overflow-x-auto scrollbar-none">
            {[
              { id: 'ALL' as AvailabilityTab, label: t('financialHealth.tabAll', 'All Schemes'), count: totalSchemesCount },
              { id: 'WITH_PARTNERS' as AvailabilityTab, label: t('financialHealth.tabWithPartners', 'With Financial Partners'), count: totalWithPartnersCount },
              { id: 'VERIFIED' as AvailabilityTab, label: t('financialHealth.tabVerified', 'Verified Info Available'), count: totalVerifiedSchemesCount },
              { id: 'LIMITED' as AvailabilityTab, label: t('financialHealth.tabLimited', 'Limited Information'), count: totalLimitedOnlySchemesCount },
              { id: 'DIRECT' as AvailabilityTab, label: t('financialHealth.tabDirect', 'Direct Departmental'), count: totalDirectDeliveryCount },
            ].map((tab) => {
              const isActive = selectedTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
                    isActive
                      ? 'bg-[#EA717B] text-white shadow-warm-xs'
                      : 'text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFF4EC]'
                  }`}
                >
                  <span>{tab.label}</span>
                  <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono ${isActive ? 'bg-white/20 text-white' : 'bg-[#FFF4EC] text-[#765E59]'}`}>
                    {tab.count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Filter and Search Bar */}
          <div className="bg-white border border-[#E8D8D2] rounded-2xl p-4 shadow-warm-xs flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="relative w-full md:w-96">
              <Search className="w-4 h-4 text-[#765E59] absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                placeholder={t('financialHealth.searchPlaceholder', 'Search schemes by title, keyword, or code...')}
                aria-label={t('financialHealth.searchAriaLabel', 'Search schemes')}
                className="w-full bg-[#FFFBF0] border border-[#E8D8D2] rounded-xl pl-10 pr-4 py-2 text-xs text-[#3B2522] placeholder:text-[#765E59]/60 outline-none focus:border-[#EA717B] focus:bg-white transition"
              />
            </div>

            <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
              <Filter className="w-4 h-4 text-[#765E59] shrink-0" />
              <span className="text-xs font-bold text-[#765E59] shrink-0">{t('financialHealth.ministryLabel', 'Ministry:')}</span>
              <select
                value={selectedMinistry}
                onChange={(e) => handleMinistryChange(e.target.value)}
                aria-label="Filter by Ministry"
                className="bg-[#FFFBF0] border border-[#E8D8D2] text-[#3B2522] text-xs font-semibold rounded-xl px-3 py-2 outline-none focus:border-[#EA717B] transition cursor-pointer max-w-xs truncate"
              >
                <option value="ALL">{t('financialHealth.allMinistries', 'All Ministries')} ({ministries.length})</option>
                {ministries.map((m) => (
                  <option key={m} value={m}>
                    {localizeGovMinistry(m, i18n.language)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Active Filter Summary Counter */}
          <div className="flex items-center justify-between text-xs text-[#765E59] px-1">
            <span>
              {t('financialHealth.showingSchemes', { count: filteredSchemes.length, total: totalSchemesCount })}
            </span>
            {(searchQuery || selectedMinistry !== 'ALL' || selectedTab !== 'ALL') && (
              <button
                onClick={() => {
                  setSearchParams({});
                }}
                className="text-[#EA717B] hover:underline font-semibold cursor-pointer"
              >
                {t('financialHealth.resetFilters', 'Reset all filters')}
              </button>
            )}
          </div>
        </div>

        {/* 6. Content Area */}
        {isLoading ? (
          <div className="py-20 text-center space-y-4">
            <div className="w-12 h-12 border-4 border-[#EA717B] border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm font-bold text-[#765E59]">
              {t('financialHealth.loadingHub', 'Loading scheme channel partner financial indicators...')}
            </p>
          </div>
        ) : isError ? (
          <div className="bg-rose-50 border border-rose-200 rounded-2xl p-8 text-center space-y-3">
            <AlertCircle className="w-10 h-10 text-rose-600 mx-auto" />
            <h2 className="text-base font-black text-rose-900">{t('financialHealth.failedHub', 'Failed to Load Financial Health Hub')}</h2>
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
            <h3 className="text-sm font-bold text-[#3B2522]">{t('financialHealth.noSchemesFound', 'No matching schemes found')}</h3>
            <p className="text-xs text-[#765E59]">{t('financialHealth.noSchemesFoundDesc', 'Try adjusting your search query, tab, or ministry filter.')}</p>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {paginatedSchemes.map((scheme) => {
                const cleanMinistry = localizeGovMinistry(cleanGovTitle(scheme.ministry), i18n.language);
                const cleanTitle = localizeGovSchemeTitle(cleanGovTitle(scheme.scheme_name), i18n.language);
                const cleanDesc = localizeGovDescription(
                  cleanGovDescription(scheme.short_description || scheme.overview, 30),
                  scheme.scheme_name,
                  i18n.language
                );
                const hasPartners = scheme.channel_partners_count > 0;

                return (
                  <div
                    key={scheme.scheme_id}
                    className="bg-white border border-[#E8D8D2] hover:border-[#FFD0CA] rounded-3xl p-6 shadow-warm-xs hover:shadow-warm-md hover:-translate-y-1 transition-all h-full flex flex-col justify-between space-y-4 group"
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
                        <Link to={`/financial-health/scheme/${scheme.scheme_id}`}>
                          {cleanTitle}
                        </Link>
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
                              {t('financialHealth.channelPartnersCount', 'Channel partners')}
                            </span>
                            <span className="font-mono text-[#3B2522] font-extrabold text-sm">
                              {t('financialHealth.totalCount', { count: scheme.channel_partners_count })}
                            </span>
                          </div>

                          <div className="flex items-center justify-between text-[#765E59] text-[11px]">
                            <span className="flex items-center gap-1 text-[#2D6A4F] font-semibold">
                              <CheckCircle2 className="w-3.5 h-3.5 text-[#2D6A4F] shrink-0" />
                              {t('financialHealth.infoAvailable', 'Financial information available')}
                            </span>
                            <span className="font-mono font-bold text-[#2D6A4F]">
                              {scheme.with_verified_financial_info_count}
                            </span>
                          </div>

                          <div className="flex items-center justify-between text-[#765E59] text-[11px]">
                            <span className="flex items-center gap-1 text-[#765E59] font-medium">
                              <HelpCircle className="w-3.5 h-3.5 text-[#765E59] shrink-0" />
                              {t('financialHealth.limitedInfo', 'Limited information')}
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
                              {t('financialHealth.directDeliverySchemes', 'Direct Delivery Scheme')}
                            </span>
                            <span className="font-mono text-[11px] font-bold text-[#4A2525] bg-[#FFD0CA] px-2 py-0.5 rounded-full">
                              {t('financialHealth.directAgency', 'Direct Agency')}
                            </span>
                          </div>
                          <p className="text-[11px] text-[#765E59] leading-relaxed">
                            {t('financialHealth.directAgencyDesc', 'Administered directly through departmental portals without intermediary banking partners.')}
                          </p>
                        </div>
                      )}

                      {/* Primary CTA */}
                      <Link
                        to={`/financial-health/scheme/${scheme.scheme_id}`}
                        className="w-full inline-flex items-center justify-center gap-2 bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold py-2.5 px-4 rounded-xl transition shadow-warm-xs group/btn"
                      >
                        <span>{hasPartners ? t('financialHealth.viewFinancialInfo', 'View financial information') : t('financialHealth.viewSchemeInfo', 'View scheme information')}</span>
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
                  {t('financialHealth.showingPage', { page: validCurrentPage, total: totalPages, count: filteredSchemes.length })}
                </span>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handlePageChange(validCurrentPage - 1)}
                    disabled={validCurrentPage === 1}
                    className="px-3 py-1.5 rounded-xl border border-[#E8D8D2] text-[#765E59] font-bold hover:bg-[#FFF4EC] disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1 cursor-pointer"
                  >
                    <ChevronLeft className="w-4 h-4" /> {t('common.previous', 'Previous')}
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
                    {t('common.next', 'Next')} <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 7. SECTION: How this information works */}
        <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-3xl p-6 sm:p-8 space-y-4">
          <div className="flex items-center gap-2 text-[#3B2522]">
            <Info className="w-5 h-5 text-[#EA717B] shrink-0" />
            <h2 className="text-base font-black">{t('financialHealth.howInfoWorks', 'How this information works')}</h2>
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

        {/* 8. Progressive Disclosure Accordion: What do bank numbers mean? */}
        <div className="bg-white border border-[#E8D8D2] rounded-3xl shadow-warm-xs overflow-hidden">
          <button
            type="button"
            onClick={() => setIsEducationOpen(!isEducationOpen)}
            className="w-full p-6 text-left flex items-center justify-between hover:bg-[#FFF4EC] transition cursor-pointer"
            aria-expanded={isEducationOpen}
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-[#FFF4EC] border border-[#FFD0CA] flex items-center justify-center shrink-0">
                <Lightbulb className="w-5 h-5 text-[#EA717B]" />
              </div>
              <div>
                <h3 className="text-sm sm:text-base font-extrabold text-[#3B2522]">
                  Citizen Guide: What do Bank Net NPA, Gross NPA, and CRAR mean?
                </h3>
                <p className="text-xs text-[#765E59]">
                  A simple citizen overview of the 3 statutory figures reported by scheduled commercial banks
                </p>
              </div>
            </div>
            <ChevronDown className={`w-5 h-5 text-[#765E59] transition-transform ${isEducationOpen ? 'rotate-180 text-[#EA717B]' : ''}`} />
          </button>

          {isEducationOpen && (
            <div className="p-6 pt-0 border-t border-[#E8D8D2] space-y-4 text-xs text-[#765E59] bg-[#FFF4EC]/20">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
                <div className="bg-white p-4 rounded-2xl border border-[#E8D8D2] space-y-2 shadow-warm-xs">
                  <div className="flex items-center gap-2 text-[#EA717B] font-bold text-xs">
                    <Coins className="w-4 h-4" />
                    <span>{t('financialHealth.netNpaLowerBetter', 'Net NPA (Lower is better)')}</span>
                  </div>
                  <p className="text-xs text-[#3B2522] leading-relaxed">
                    Shows loans where repayment problems remain after deducting provisions set aside by the bank. A lower Net NPA means a smaller share of loans is troubled.
                  </p>
                </div>

                <div className="bg-white p-4 rounded-2xl border border-[#E8D8D2] space-y-2 shadow-warm-xs">
                  <div className="flex items-center gap-2 text-[#F7AE56] font-bold text-xs">
                    <BarChart3 className="w-4 h-4" />
                    <span>{t('financialHealth.grossNpaBroader', 'Gross NPA (Broader picture)')}</span>
                  </div>
                  <p className="text-xs text-[#3B2522] leading-relaxed">
                    Shows the total value of loans classified as non-performing before any provisions. Gives a broad view of historical loan quality across the bank.
                  </p>
                </div>

                <div className="bg-white p-4 rounded-2xl border border-[#E8D8D2] space-y-2 shadow-warm-xs">
                  <div className="flex items-center gap-2 text-[#2D6A4F] font-bold text-xs">
                    <Shield className="w-4 h-4" />
                    <span>{t('financialHealth.crarHigherBetter', 'Capital Cushion / CRAR (Higher is better)')}</span>
                  </div>
                  <p className="text-xs text-[#3B2522] leading-relaxed">
                    Shows how much capital buffer the bank holds against risks in its assets under RBI Basel norms. RBI mandates a minimum of 9% (or 11.5% with buffers).
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
