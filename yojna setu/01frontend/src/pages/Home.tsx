import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { schemeApi } from '../api/schemeApi';
import { partnerApi } from '../api/partnerApi';
import { blogApi, FinancialBlog } from '../api/blogApi';
import { HomeHero } from '../components/HomeHero';
import {
  Search,
  ShieldCheck,
  Building2,
  FileCheck2,
  ArrowRight,
  FileText,
  Coins,
  GraduationCap,
  Hammer,
  HeartHandshake,
  TrendingUp,
  MapPin,
  CheckCircle2,
  Sparkles,
  Compass,
  Cpu,
  Calculator,
  MessageSquare,
  Globe2,
  ExternalLink,
  Users,
  ChevronDown,
  ChevronUp,
  UserCheck,
  HelpCircle,
  BookOpen,
  Database,
  Languages,
} from 'lucide-react';
import { SchemeCard } from '../components/SchemeCard';
import { Scheme } from '../types';

export const Home: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [featuredSchemes, setFeaturedSchemes] = useState<Scheme[]>([]);
  const [latestBlogs, setLatestBlogs] = useState<FinancialBlog[]>([]);
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(0);
  const [stats, setStats] = useState<{
    totalSchemes: number;
    channelPartners: number;
    languages: number;
  }>({
    totalSchemes: 859,
    channelPartners: 171,
    languages: 12,
  });

  // Fetch actual live schemes & partner count from backend
  useEffect(() => {
    schemeApi
      .getSchemes({ page_size: 6 })
      .then((res) => {
        if (res.items && res.items.length > 0) {
          setFeaturedSchemes(res.items.slice(0, 3));
        }
        if (res.total && res.total > 0) {
          setStats((prev) => ({ ...prev, totalSchemes: res.total }));
        }
      })
      .catch((err) => {
        console.error('Failed to load schemes:', err);
      });

    partnerApi
      .getCoverageReport()
      .then((report) => {
        if (report && report.total_partners) {
          setStats((prev) => ({
            ...prev,
            channelPartners: report.total_partners,
            totalSchemes: report.total_schemes || prev.totalSchemes,
          }));
        }
      })
      .catch(() => {
        // Fallback to verified canonical baseline 171
      });

    blogApi
      .list()
      .then((items) => {
        if (items && items.length > 0) {
          setLatestBlogs(items.slice(0, 3));
        }
      })
      .catch(() => {});
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/schemes?search=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      navigate('/schemes');
    }
  };

  const handleTrendingClick = (tag: string) => {
    navigate(`/schemes?search=${encodeURIComponent(tag)}`);
  };

  const openAiPrompt = (promptText: string) => {
    window.dispatchEvent(
      new CustomEvent('open-yojnasetu-ai', {
        detail: { prompt: promptText },
      })
    );
  };

  return (
    <div className="space-y-12 sm:space-y-16 lg:space-y-20 pb-20 bg-[#FFFBF0] text-[#3B2522] min-h-screen">
      {/* ============================================================
          1. COMPOSED FULL-WIDTH HERO SLIDESHOW (75–85vh)
          ============================================================ */}
      <HomeHero totalSchemes={stats.totalSchemes} />

      {/* Prominent Citizen Matching CTA Strip */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 sm:mt-8 mb-6 text-center relative z-30">
        <div className="inline-flex flex-wrap items-center justify-center gap-3 bg-white/95 backdrop-blur-sm p-3 rounded-2xl border border-[#E8D8D2] shadow-warm-xs">
          <span className="text-xs font-bold text-[#765E59] px-2">
            {t('home.citizenMatching.prompt', 'Looking for personalized welfare recommendations?')}
          </span>
          <Link
            to="/recommendations"
            className="inline-flex items-center gap-2 bg-[#EA717B] hover:bg-[#D65D67] text-white text-xs sm:text-sm font-bold px-5 py-2.5 rounded-xl shadow-warm-xs transition min-h-[48px]"
          >
            <Sparkles className="w-4 h-4 text-amber-200" />
            <span>{t('home.findMatchingSchemes')}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* ============================================================
          2. QUICK TRUST STATS STRIP (LIVE DATA DRIVEN)
          4 distinct modern civic cards with semantic icon containers
          ============================================================ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-30">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {/* Stat 1: Gazette-Verified Schemes */}
          <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-1 hover:border-[#D9C4BC] transition-all duration-200 p-6 flex flex-col items-center text-center group">
            <div className="w-12 h-12 rounded-xl bg-[#FFF4EC] text-[#EA717B] border border-[#FFD0CA] flex items-center justify-center mb-3.5 group-hover:scale-110 transition-transform duration-200">
              <BookOpen className="w-6 h-6" />
            </div>
            <div className="text-3xl sm:text-4xl font-black text-[#2B1810] tracking-tight">
              {stats.totalSchemes}+
            </div>
            <div className="mt-1.5 text-sm sm:text-base font-bold text-[#3B2522]">
              {t('home.trustStats.stat1Title', 'Gazette-Verified Schemes')}
            </div>
            <div className="text-xs text-[#765E59] mt-0.5 font-medium">
              {t('home.trustStats.stat1Subtitle', 'Central & State Portfolios')}
            </div>
          </div>

          {/* Stat 2: Channel Partners */}
          <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-1 hover:border-[#D9C4BC] transition-all duration-200 p-6 flex flex-col items-center text-center group">
            <div className="w-12 h-12 rounded-xl bg-[#FFF4EC] text-[#F7AE56] border border-[#FCD9B4] flex items-center justify-center mb-3.5 group-hover:scale-110 transition-transform duration-200">
              <Building2 className="w-6 h-6" />
            </div>
            <div className="text-3xl sm:text-4xl font-black text-[#2B1810] tracking-tight">
              {stats.channelPartners}+
            </div>
            <div className="mt-1.5 text-sm sm:text-base font-bold text-[#3B2522]">
              {t('home.trustStats.stat2Title', 'Channel Partners')}
            </div>
            <div className="text-xs text-[#765E59] mt-0.5 font-medium">
              {t('home.trustStats.stat2Subtitle', 'Banks, SCAs & Facilitation Centers')}
            </div>
          </div>

          {/* Stat 3: Indian Languages */}
          <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-1 hover:border-[#D9C4BC] transition-all duration-200 p-6 flex flex-col items-center text-center group">
            <div className="w-12 h-12 rounded-xl bg-[#FFF4EC] text-[#EA717B] border border-[#FFD0CA] flex items-center justify-center mb-3.5 group-hover:scale-110 transition-transform duration-200">
              <Languages className="w-6 h-6" />
            </div>
            <div className="text-3xl sm:text-4xl font-black text-[#EA717B] tracking-tight">
              {stats.languages}
            </div>
            <div className="mt-1.5 text-sm sm:text-base font-bold text-[#3B2522]">
              {t('home.trustStats.stat3Title', 'Indian Languages')}
            </div>
            <div className="text-xs text-[#765E59] mt-0.5 font-medium">
              {t('home.trustStats.stat3Subtitle', 'Full Multilingual Support')}
            </div>
          </div>

          {/* Stat 4: Verified Financial Records */}
          <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-1 hover:border-[#D9C4BC] transition-all duration-200 p-6 flex flex-col items-center text-center group">
            <div className="w-12 h-12 rounded-xl bg-[#FFF4EC] text-[#F7AE56] border border-[#FCD9B4] flex items-center justify-center mb-3.5 group-hover:scale-110 transition-transform duration-200">
              <Database className="w-6 h-6" />
            </div>
            <div className="text-3xl sm:text-4xl font-black text-[#2B1810] tracking-tight">
              3,073+
            </div>
            <div className="mt-1.5 text-sm sm:text-base font-bold text-[#3B2522]">
              {t('home.trustStats.stat4Title', 'Verified Records')}
            </div>
            <div className="text-xs text-[#765E59] mt-0.5 font-medium">
              {t('home.trustStats.stat4Subtitle', 'RBI & Public Disclosures')}
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
          3. HOW YOJNASETU WORKS (4 VISUALLY DISTINCT STEPS)
          ============================================================ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-10 space-y-2">
          <div className="inline-flex items-center gap-2 bg-[#FFF4EC] text-[#EA717B] px-3 py-1 rounded-full text-xs font-bold border border-[#FFD0CA] uppercase tracking-wider">
            {t('home.howItWorks.processBadge', 'Simple 4-Step Process')}
          </div>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black text-[#3B2522] tracking-tight">
            {t('home.howItWorksTitle', 'How YojnaSetu Works for Citizens')}
          </h2>
          <p className="text-sm sm:text-base text-[#765E59] leading-relaxed max-w-xl mx-auto">
            {t('home.howItWorksSub', 'From discovering the right scheme to connecting with local channel partners in four clear steps.')}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {[
            {
              step: '01',
              title: t('home.stepTellUs'),
              desc: t('home.howItWorks.step1Desc', 'Share basic details like state, category, age, and employment status in complete privacy.'),
              icon: FileText,
              tileClass: 'bg-[#FFF4EC] text-[#EA717B] border-[#FFD0CA]',
            },
            {
              step: '02',
              title: t('home.stepCheckEligibility'),
              desc: t('home.howItWorks.step2Desc', 'Our deterministic rule engine evaluates statutory Gazette criteria against your profile.'),
              icon: ShieldCheck,
              tileClass: 'bg-[#FFF4EC] text-[#F7AE56] border-[#FFD0CA]',
            },
            {
              step: '03',
              title: t('home.stepDiscoverSchemes'),
              desc: t('home.howItWorks.step3Desc', 'Receive a curated list with clear match reasons, loan ceilings, and capital subsidies.'),
              icon: Sparkles,
              tileClass: 'bg-[#FFF4EC] text-[#F7AE56] border-[#FFD0CA]',
            },
            {
              step: '04',
              title: t('home.stepOfficialRoute'),
              desc: t('home.howItWorks.step4Desc', 'Apply directly on verified Ministry portals or visit nearest authorized assistance centers.'),
              icon: MapPin,
              tileClass: 'bg-[#FFF4EC] text-[#4A2525] border-[#E8D8D2]',
            },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.step}
                className="bg-white p-6 rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-1 transition-all duration-200 flex flex-col justify-between group"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center border ${item.tileClass} group-hover:scale-105 transition-transform`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-3xl font-black text-[#FFD0CA] tracking-tight group-hover:text-[#F7AE56] transition-colors">
                      {item.step}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-[#3B2522] group-hover:text-[#EA717B] transition">
                      {item.title}
                    </h3>
                    <p className="text-xs sm:text-sm text-[#765E59] leading-relaxed mt-1">
                      {item.desc}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ============================================================
          3.5. EXPLORE BY BENEFICIARY CATEGORY (6 CARDS)
          ============================================================ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl p-6 sm:p-10 border border-[#E8D8D2] shadow-warm-sm space-y-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-[#E8D8D2]/60 pb-6">
            <div className="space-y-1.5 text-left max-w-2xl">
              <span className="text-xs font-bold text-[#EA717B] tracking-wide uppercase">
                {t('home.categorySectionBadge', 'Targeted Assistance')}
              </span>
              <h2 className="text-2xl sm:text-3xl font-black text-[#3B2522] tracking-tight">
                {t('home.categorySectionTitle', 'Explore Schemes by Category')}
              </h2>
              <p className="text-sm sm:text-base text-[#765E59] leading-relaxed">
                {t('home.categorySectionSub')}
              </p>
            </div>
            <Link
              to="/explore"
              className="action-link text-sm self-start md:self-end pb-1 text-[#EA717B] font-bold flex items-center gap-1.5"
            >
              <span>{t('home.exploreAllFeatures', 'Explore All Features')}</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
            {[
              {
                title: t('home.categories.msmeTitle'),
                desc: t('home.categories.msmeDesc', 'PMEGP, MUDRA, Stand-Up India schemes for business setup and expansion.'),
                icon: Building2,
                tileClass: 'bg-[#FFF4EC] text-[#EA717B] border-[#FFD0CA]',
                count: 'PMEGP, MUDRA, Stand-Up India',
                query: 'MUDRA'
              },
              {
                title: t('home.categories.agriTitle'),
                desc: t('home.categories.agriDesc', 'Crop credit, livestock, solar pumps, and agricultural subsidies.'),
                icon: Coins,
                tileClass: 'bg-[#FFF4EC] text-[#F7AE56] border-[#FCD9B4]',
                count: 'KCC, NLM, PM-KUSUM',
                query: 'Agriculture'
              },
              {
                title: t('home.categories.artisanTitle'),
                desc: t('home.categories.artisanDesc', 'Toolkits, skill verification, and subsidized credit for 18 heritage crafts.'),
                icon: Hammer,
                tileClass: 'bg-[#FFF4EC] text-[#EA717B] border-[#FFD0CA]',
                count: 'PM Vishwakarma, NSFDC',
                query: 'Vishwakarma'
              },
              {
                title: t('home.categories.eduTitle'),
                desc: t('home.categories.eduDesc', 'Pre-matric, post-matric, higher education loans, and scholarship grants.'),
                icon: GraduationCap,
                tileClass: 'bg-[#FFF4EC] text-[#F7AE56] border-[#FCD9B4]',
                count: 'PM-YASASVI, NMMS, CSIS',
                query: 'Scholarship'
              },
              {
                title: t('home.categories.socialTitle'),
                desc: t('home.categories.socialDesc', 'Life insurance, accident protection, and old-age social security.'),
                icon: HeartHandshake,
                tileClass: 'bg-[#FFF4EC] text-[#4A2525] border-[#E8D8D2]',
                count: 'APY, PMSBY, PMJJBY',
                query: 'Pension'
              },
              {
                title: t('home.categories.healthTitle'),
                desc: t('home.categories.healthDesc', 'Maternity entitlements, health coverage, and girl-child support.'),
                icon: ShieldCheck,
                tileClass: 'bg-[#FFF4EC] text-[#F7AE56] border-[#FCD9B4]',
                count: 'AB-PMJAY, PMMVY, SSY',
                query: 'Health'
              },
            ].map((cat) => {
              const Icon = cat.icon;
              return (
                <div
                  key={cat.title}
                  onClick={() => handleTrendingClick(cat.query)}
                  className="bg-white p-5 rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-0.5 transition duration-200 cursor-pointer group flex flex-col justify-between"
                >
                  <div className="space-y-2.5">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${cat.tileClass} group-hover:scale-105 transition-transform duration-200`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-[#3B2522] group-hover:text-[#EA717B] transition">
                        {cat.title}
                      </h3>
                      <p className="text-xs text-[#765E59] mt-1 leading-relaxed">
                        {cat.desc}
                      </p>
                    </div>
                  </div>
                  <div className="pt-3 mt-3 border-t border-[#E8D8D2]/60 flex items-center justify-between text-xs">
                    <span className="text-[11px] font-medium text-[#765E59]">
                      {cat.count}
                    </span>
                    <span className="font-bold text-[#EA717B] flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                      <span>{t('schemes.viewDetails', 'View Details')}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ============================================================
          4. EVERYTHING YOU NEED IN ONE PLACE (6 FEATURE CARDS)
          ============================================================ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl p-6 sm:p-10 border border-[#E8D8D2] shadow-warm-sm space-y-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-[#E8D8D2]/60 pb-6">
            <div className="space-y-1.5 text-left max-w-2xl">
              <span className="text-xs font-bold text-[#EA717B] tracking-wide uppercase">
                {t('home.citizenCapabilities', 'Citizen Capabilities')}
              </span>
              <h2 className="text-2xl sm:text-3xl font-black text-[#3B2522] tracking-tight">
                {t('home.everythingYouNeedTitle', 'Everything You Need in One Place')}
              </h2>
              <p className="text-sm sm:text-base text-[#765E59] leading-relaxed">
                {t('home.everythingYouNeedSub', 'Integrated civic tools designed to eliminate guesswork, middle-men, and misinformation.')}
              </p>
            </div>
            <Link
              to="/explore"
              className="action-link text-sm self-start md:self-end pb-1 text-[#EA717B] font-bold flex items-center gap-1.5"
            >
              <span>{t('home.exploreAllFeatures', 'Explore All Features')}</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
            {[
              {
                icon: Search,
                title: t('home.capabilities.discoverTitle', 'Discover Schemes'),
                desc: t('home.capabilities.discoverDesc', { total: stats.totalSchemes, defaultValue: `Search and filter ${stats.totalSchemes}+ verified central and state welfare portfolios by ministry, sector, and beneficiary.` }),
                link: '/schemes',
                tileClass: 'icon-tile-blue',
              },
              {
                icon: ShieldCheck,
                title: t('home.capabilities.eligibilityTitle', 'Check Eligibility'),
                desc: t('home.capabilities.eligibilityDesc', 'Audited deterministic rules evaluate your age, income, and category against official Gazette criteria without document uploads.'),
                link: '/schemes',
                tileClass: 'icon-tile-orange',
              },
              {
                icon: Sparkles,
                title: t('home.capabilities.smartMatchingTitle', 'Smart Matching'),
                desc: t('home.capabilities.smartMatchingDesc', 'Describe your business or situation in conversational natural language to receive high-precision potential scheme matches.'),
                link: '/recommendations',
                tileClass: 'icon-tile-purple',
              },
              {
                icon: Calculator,
                title: t('home.capabilities.calculatorTitle', 'Financial Calculator'),
                desc: t('home.capabilities.calculatorDesc', 'Simulate loan EMIs, interest liabilities, capital subsidies, and evaluate household repayment affordability.'),
                link: '/calculator',
                tileClass: 'icon-tile-orange',
              },
              {
                icon: Building2,
                title: t('home.capabilities.healthTitle', 'Financial Health'),
                desc: t('home.capabilities.healthDesc', 'Statutory transparency on channel partner banks, regional rural banks, and prudential delivery capacity.'),
                link: '/financial-health',
                tileClass: 'icon-tile-amber',
              },
              {
                icon: MapPin,
                title: t('home.capabilities.partnersTitle', 'Find Nearby Partners'),
                desc: t('home.capabilities.partnersDesc', 'Locate verified bank branches, State Channelizing Agencies, and facilitation centres near your district or PIN code.'),
                link: '/channel-partners',
                tileClass: 'icon-tile-cyan',
              },
            ].map((feat) => {
              const Icon = feat.icon;
              return (
                <Link
                  key={feat.title}
                  to={feat.link}
                  className="civic-card p-6 flex flex-col justify-between group cursor-pointer"
                >
                  <div className="space-y-4">
                    <div className={`icon-tile icon-tile-lg ${feat.tileClass} group-hover:scale-105 transition-transform`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base sm:text-lg font-bold text-[#3B2522] group-hover:text-[#EA717B] transition">
                        {feat.title}
                      </h3>
                      <p className="text-xs sm:text-sm text-[#765E59] leading-relaxed mt-1">
                        {feat.desc}
                      </p>
                    </div>
                  </div>
                  <div className="pt-4 mt-4 border-t border-[#E8D8D2]/60 flex items-center">
                    <span className="action-link text-xs font-bold text-[#EA717B] flex items-center gap-1">
                      <span>{t('home.exploreFeature', 'Explore')}</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* ============================================================
          4.5. POPULAR & FEATURED SCHEMES
          ============================================================ */}
      {featuredSchemes.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 bg-[#FFF4EC] text-[#EA717B] text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider border border-[#FFD0CA] mb-2">
                {t('home.highCitizenRelevance', 'High Citizen Relevance')}
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-[#3B2522] tracking-tight">
                {t('home.popularSchemesTitle', 'Popular & Featured Schemes')}
              </h2>
              <p className="text-sm text-[#765E59] mt-1">
                {t('home.popularSchemesSub', 'Active government initiatives with statutory funding allocations and direct assistance.')}
              </p>
            </div>
            <Link
              to="/schemes"
              className="action-link text-sm font-bold flex items-center gap-1.5 self-start sm:self-end text-[#EA717B]"
            >
              <span>{t('home.exploreAllSchemes')}</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {featuredSchemes.map((scheme) => (
              <SchemeCard key={scheme.scheme_id} scheme={scheme} />
            ))}
          </div>
        </section>
      )}

      {/* ============================================================
          5. PERSONALIZED MATCHING DIFFERENTIATOR ("MATCHED TO YOU")
          (Resolves Floto Issues 4, 7, 17)
          ============================================================ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-[#4A2525] text-white rounded-3xl p-6 sm:p-10 lg:p-12 shadow-warm-xl border border-[#3B2522] relative overflow-hidden">
          {/* Subtle background glow */}
          <div className="absolute right-0 top-0 w-96 h-96 bg-[#F7AE56]/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute left-0 bottom-0 w-96 h-96 bg-[#EA717B]/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Left Narrative */}
            <div className="lg:col-span-7 space-y-4 text-left">
              <div className="inline-flex items-center gap-2 bg-white/10 text-[#F7AE56] px-3 py-1 rounded-full text-xs font-bold border border-[#F7AE56]/30">
                <Sparkles className="w-3.5 h-3.5" />
                <span>{t('home.civicMatchingBadge', 'Deterministic Civic Matching')}</span>
              </div>
              <h2 className="text-2xl sm:text-4xl font-black text-white tracking-tight leading-tight">
                {t('home.civicMatchingTitle', 'Government Schemes, Matched to You.')}
              </h2>
              <p className="text-base text-[#FFFBF0]/80 leading-relaxed max-w-xl">
                {t('home.civicMatchingDesc', 'Most portals leave citizens scrolling through hundreds of confusing PDFs. YojnaSetu uses an audited rule engine to match your profile directly with published statutory eligibility criteria.')}
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                {[
                  t('home.rankingFeature', 'Personalized Scheme Rankings'),
                  t('home.ruleFeature', 'Deterministic Rule Evaluations'),
                  t('home.guidelinesFeature', 'Official Ministry Guidelines'),
                  t('home.zeroDocFeature', 'Zero Document Upload Required'),
                ].map((item) => (
                  <div
                    key={item}
                    className="flex items-center gap-2.5 text-xs text-[#FFFBF0] bg-white/10 border border-white/15 px-3 py-2 rounded-lg"
                  >
                    <CheckCircle2 className="w-4 h-4 text-[#F7AE56] shrink-0" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>

              <div className="pt-3">
                <Link
                  to="/recommendations"
                  className="btn btn-lg btn-primary shadow-warm-md min-h-[48px] inline-flex items-center gap-2"
                >
                  <Sparkles className="w-4 h-4 text-amber-200" />
                  <span>{t('home.findForMe', 'Find Schemes for Me')}</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>

            {/* Right Visual Representation: Citizen-Friendly Visual Journey (Resolves Floto Issue 17) */}
            <div className="lg:col-span-5 bg-[#3B2522]/80 border border-[#FFD0CA]/20 rounded-2xl p-5 sm:p-6 backdrop-blur-md space-y-4 shadow-warm-lg">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <span className="text-sm font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#F7AE56]" />
                  {t('home.howWeMatchTitle', 'How We Match Your Profile')}
                </span>
                <span className="text-xs bg-[#FFD0CA]/40 text-[#4A2525] border border-[#FFD0CA] px-2.5 py-0.5 rounded-full font-semibold">
                  {t('home.instantMatch', 'Instant Match')}
                </span>
              </div>

              <div className="space-y-3">
                {/* Step 1: Your Profile */}
                <div className="bg-[#4A2525]/90 p-3.5 rounded-xl border border-[#FFD0CA]/15 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#FFD0CA]/20 text-[#FFD0CA] flex items-center justify-center shrink-0 mt-0.5">
                    <Users className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[#FFFBF0]/70">{t('home.stepTellUs', 'Your Profile')}</span>
                      <span className="text-xs font-bold text-[#FFD0CA]">{t('home.demoProfileSummary', '28 Yrs • Maharashtra • SC')}</span>
                    </div>
                    <p className="text-xs text-[#FFFBF0]/80 mt-0.5">{t('home.profileStepSub', 'Basic profile details without document upload.')}</p>
                  </div>
                </div>

                {/* Step 2: Eligibility Check */}
                <div className="bg-[#4A2525]/90 p-3.5 rounded-xl border border-[#FFD0CA]/15 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#FFF4EC] text-[#F7AE56] flex items-center justify-center shrink-0 mt-0.5">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[#FFFBF0]/70">{t('home.stepCheckEligibility', 'Eligibility Check')}</span>
                      <span className="text-xs font-bold text-[#F7AE56]">{t('home.audit100', '100% Rules Audited')}</span>
                    </div>
                    <p className="text-xs text-[#FFFBF0]/80 mt-0.5">{t('home.auditStepSub', 'Statutory Gazette criteria verified against inputs.')}</p>
                  </div>
                </div>

                {/* Step 3: Smart Scheme Matching */}
                <div className="bg-[#4A2525]/90 p-3.5 rounded-xl border border-[#FFD0CA]/15 flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#F7AE56]/20 text-[#F7AE56] flex items-center justify-center shrink-0 mt-0.5">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[#FFFBF0]/70">{t('home.stepDiscoverSchemes', 'Smart Scheme Matching')}</span>
                      <span className="text-xs font-bold text-[#F7AE56]">{t('home.eligible14', '14 Eligible Schemes')}</span>
                    </div>
                    <p className="text-xs text-[#FFFBF0]/80 mt-0.5">{t('home.matchingStepSub', 'Ranked by loan support & maximum subsidies.')}</p>
                  </div>
                </div>

                {/* Step 4: Your Opportunities */}
                <div className="bg-gradient-to-r from-[#EA717B]/25 to-[#F7AE56]/20 p-3.5 rounded-xl border border-[#EA717B]/40 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#F7AE56]">{t('home.stepOfficialRoute', 'Your Opportunities')}</span>
                    <span className="bg-[#FFD0CA]/40 text-[#4A2525] border border-[#FFD0CA] px-2 py-0.5 rounded text-xs font-bold">
                      {t('home.subsidy35', '35% Subsidy')}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-white">
                    {t('home.pmegpTitle', "Prime Minister's Employment Generation Programme (PMEGP)")}
                  </h4>
                  <div className="flex items-center gap-2 text-xs text-[#FFFBF0]/80 pt-0.5">
                    <span className="bg-white/10 px-2 py-0.5 rounded font-medium">{t('home.upTo50L', 'Up to ₹50 Lakh Loan')}</span>
                    <span>•</span>
                    <span className="text-[#F7AE56] font-semibold">{t('compare.directPortal', 'Official Direct Portal')}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
          6. AI ASSISTANT SECTION ("NOT SURE WHERE TO START?")
          (Resolves Floto Issues 7, 16)
          ============================================================ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl p-6 sm:p-10 border border-[#E8D8D2] shadow-warm-sm space-y-6">
          <div className="max-w-2xl space-y-1.5 text-left">
            <span className="text-xs font-bold text-[#EA717B] tracking-wide">
              {t('home.multilingualAssistant', 'Multilingual Assistant')}
            </span>
            <h2 className="text-2xl sm:text-3xl font-black text-[#3B2522] tracking-tight">
              {t('home.notSureTitle', 'Not sure where to start?')}
            </h2>
            <p className="text-base text-[#765E59] leading-relaxed">
              {t('home.notSureSub', 'Ask YojnaSetu in your own words and get grounded guidance backed by official notifications.')}
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-5">
            {[
              {
                query: t('home.prompt1Query', 'Which schemes can help me start a business?'),
                desc: t('home.prompt1Desc', 'PMEGP, MUDRA, Stand-Up India loan & subsidy guidance'),
              },
              {
                query: t('home.prompt2Query', 'Am I eligible for a loan without collateral?'),
                desc: t('home.prompt2Desc', 'CGTMSE and Mudra collateral-free credit rules'),
              },
              {
                query: t('home.prompt3Query', 'What documents do I need for PM Vishwakarma?'),
                desc: t('home.prompt3Desc', 'Aadhaar, artisan verification, and trade certificates'),
              },
            ].map((item) => (
              <button
                key={item.query}
                type="button"
                onClick={() => openAiPrompt(item.query)}
                className="text-left p-5 rounded-2xl bg-[#FFF4EC]/50 hover:bg-[#FFD0CA]/40 border border-[#E8D8D2] hover:border-[#F7AE56] transition group flex flex-col justify-between cursor-pointer"
              >
                <div>
                  <div className="flex items-center gap-2 text-sm font-bold text-[#3B2522] group-hover:text-[#EA717B] transition">
                    <MessageSquare className="w-4 h-4 text-[#EA717B] shrink-0" />
                    <span>"{item.query}"</span>
                  </div>
                  <p className="text-sm text-[#765E59] mt-2.5 line-clamp-2 leading-relaxed">{item.desc}</p>
                </div>
                <div className="pt-3.5 mt-3 border-t border-[#E8D8D2]/60 w-full flex items-center">
                  <span className="action-link text-sm text-[#EA717B] font-bold flex items-center gap-1">
                    <span>{t('home.askQuestion', 'Ask this question')}</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================
          7. MULTILINGUAL INDIA SECTION
          12 Scheduled Languages Inclusion Showcase (Resolves Floto Issues 3, 7)
          ============================================================ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-[#4A2525] text-white rounded-3xl p-6 sm:p-10 border border-[#3B2522] shadow-warm-lg space-y-6">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <span className="inline-flex items-center gap-1.5 text-[#F7AE56] text-xs font-bold tracking-wide">
              <Globe2 className="w-3.5 h-3.5" />
              <span>{t('home.linguisticInclusion', 'Linguistic Inclusion')}</span>
            </span>
            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              {t('home.linguisticTitle', 'Government Support, in the Language You Understand')}
            </h2>
            <p className="text-base text-[#FFFBF0]/80 leading-relaxed">
              {t('home.linguisticDesc', 'YojnaSetu provides full parity across 12 scheduled Indian languages to ensure no citizen is left behind.')}
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-2.5 max-w-4xl mx-auto">
            {[
              { code: 'hi', name: 'हिन्दी (Hindi)' },
              { code: 'en', name: 'English' },
              { code: 'bn', name: 'বাংলা (Bengali)' },
              { code: 'te', name: 'తెలుగు (Telugu)' },
              { code: 'mr', name: 'मराठी (Marathi)' },
              { code: 'ta', name: 'தமிழ் (Tamil)' },
              { code: 'gu', name: 'ગુજરાતી (Gujarati)' },
              { code: 'kn', name: 'ಕನ್ನಡ (Kannada)' },
              { code: 'ml', name: 'മലയാളം (Malayalam)' },
              { code: 'pa', name: 'ਪੰਜਾਬੀ (Punjabi)' },
              { code: 'or', name: 'ଓଡ଼ିଆ (Odia)' },
              { code: 'as', name: 'অসমীয়া (Assamese)' },
            ].map((lang) => (
              <div
                key={lang.code}
                className="bg-white/10 hover:bg-white/15 border border-[#FFD0CA]/20 text-[#FFFBF0] px-3.5 py-2 rounded-lg text-xs font-semibold backdrop-blur-sm transition"
              >
                {lang.name}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================
          8. NEARBY SUPPORT & AUTHORIZED PARTNER CHANNELS
          (Resolves Floto Issues 4, 7, 14)
          ============================================================ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl p-6 sm:p-8 lg:p-10 border border-[#E8D8D2] shadow-warm-sm">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 lg:gap-8">
            <div className="flex items-start gap-4 sm:gap-5 max-w-3xl">
              <div className="w-12 h-12 rounded-xl bg-[#FFF4EC] border border-[#FFD0CA] text-[#EA717B] flex items-center justify-center shrink-0 mt-1">
                <MapPin className="w-6 h-6" />
              </div>
              <div className="space-y-2 text-left">
                <div className="inline-flex items-center gap-1.5 text-xs font-bold text-[#4A2525] bg-[#FFD0CA]/60 px-2.5 py-0.5 rounded-md border border-[#E8D8D2]">
                  <span>{t('home.assistedNetwork', 'Assisted Delivery Network')}</span>
                </div>
                <h2 className="text-xl sm:text-2xl font-black text-[#3B2522] tracking-tight">
                  {t('home.needHelpTitle', 'Need Help Applying in Person?')}
                </h2>
                <p className="text-base text-[#765E59] leading-relaxed max-w-2xl">
                  {t('home.needHelpDesc', 'Locate authorized State Channelizing Agencies (SCAs), Public Sector Bank branches, and verified facilitation centers near your district for free physical application guidance.')}
                </p>
                <div className="flex flex-wrap gap-4 pt-1 text-xs font-medium text-[#765E59]">
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#EA717B]" />
                    {stats.channelPartners}+ {t('home.verifiedCenters', 'Verified Centers')}
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#EA717B]" />
                    {t('home.zeroCharge', 'Zero Facilitation Charge')}
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#EA717B]" />
                    {t('home.districtCoverage', 'District-Level Coverage')}
                  </span>
                </div>
              </div>
            </div>
            <div className="self-start lg:self-center shrink-0">
              <Link
                to="/channel-partners"
                className="btn btn-lg btn-dark shadow-warm-xs"
              >
                <span>{t('home.findNearbySupport', 'Find Nearby Support')}</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
          9. OFFICIAL GAZETTE & TRUST SECTION
          (Resolves Floto Issues 7, 12)
          ============================================================ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl p-6 sm:p-10 border border-[#E8D8D2] shadow-warm-sm space-y-6">
          <div className="max-w-3xl space-y-1.5 text-left">
            <div className="inline-flex items-center gap-1.5 text-xs font-bold text-[#4A2525] bg-[#FFF4EC] px-2.5 py-0.5 rounded-md border border-[#FFD0CA]">
              <ShieldCheck className="w-3.5 h-3.5 text-[#EA717B]" />
              <span>{t('home.verifiedDataArch', 'Verified Data Architecture')}</span>
            </div>
            <h2 className="text-xl sm:text-3xl font-black text-[#3B2522] tracking-tight">
              {t('home.builtAroundOfficial', 'Built Around Official Government Information')}
            </h2>
            <p className="text-base text-[#765E59] leading-relaxed">
              {t('home.independentCivicDesc', 'YojnaSetu operates as an independent civic-tech portal providing deterministic eligibility guidance derived strictly from published ministry notifications and official source citations.')}
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
            {[
              {
                icon: FileCheck2,
                title: t('home.trustPillar1'),
                desc: t('home.trustPillar1Desc', 'Every scheme mapped to published ministry notifications and official source links.'),
                color: 'text-[#EA717B]',
              },
              {
                icon: CheckCircle2,
                title: t('home.trustPillar2'),
                desc: t('home.trustPillar2Desc', 'Transparent statutory criteria evaluations with conversational AI assistance without guesswork.'),
                color: 'text-[#EA717B]',
              },
              {
                icon: Building2,
                title: t('home.trustPillar3'),
                desc: t('home.trustPillar3Desc', '171+ verified state channelizing agencies, bank branches, and facilitation centers.'),
                color: 'text-[#F7AE56]',
              },
              {
                icon: ShieldCheck,
                title: t('home.trustPillar4'),
                desc: t('home.trustPillar4Desc', 'Zero PII, Aadhaar numbers, or document uploads required to discover and compare schemes.'),
                color: 'text-[#4A2525]',
              },
            ].map((pillar) => {
              const Icon = pillar.icon;
              return (
                <div
                  key={pillar.title}
                  className="bg-[#FFF4EC]/40 p-5 rounded-2xl border border-[#E8D8D2] space-y-2.5"
                >
                  <div className={`flex items-center gap-2 font-bold text-sm ${pillar.color}`}>
                    <Icon className="w-4 h-4 shrink-0" />
                    <h3 className="text-sm sm:text-base font-bold text-[#3B2522]">{pillar.title}</h3>
                  </div>
                  <p className="text-sm text-[#765E59] leading-relaxed">{pillar.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ============================================================
          9.5. CITIZEN FREQUENTLY ASKED QUESTIONS (FAQ)
          Clear, concise answers to common citizen questions
          ============================================================ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl p-6 sm:p-10 border border-[#E8D8D2] shadow-warm-sm space-y-6">
          <div className="max-w-3xl space-y-1.5 text-left">
            <div className="inline-flex items-center gap-1.5 text-xs font-bold text-[#4A2525] bg-[#FFD0CA]/60 px-2.5 py-0.5 rounded-md border border-[#E8D8D2]">
              <HelpCircle className="w-3.5 h-3.5 text-[#EA717B]" />
              <span>{t('home.citizenAssistance', 'Citizen Assistance')}</span>
            </div>
            <h2 className="text-xl sm:text-3xl font-black text-[#3B2522] tracking-tight">
              {t('home.faqTitle', 'Frequently Asked Questions')}
            </h2>
            <p className="text-base text-[#765E59] leading-relaxed">
              {t('home.faqSubtitle', 'Clear answers about how YojnaSetu works, data privacy, and government application routes.')}
            </p>
          </div>

          <div className="space-y-3">
            {[
              {
                q: t('home.faq.q1', 'How does YojnaSetu determine my scheme eligibility?'),
                a: t('home.faq.a1', 'YojnaSetu uses a deterministic rule engine based strictly on published Gazette notifications and Ministry guidelines. When you provide details such as age, state, or enterprise stage, our engine evaluates every statutory rule without speculation or estimation.'),
              },
              {
                q: t('home.faq.q2', 'Do I need to upload Aadhaar, PAN, or financial documents to search?'),
                a: t('home.faq.a2', 'No. YojnaSetu has a strict zero-document policy for discovery. You can explore all 859+ schemes, check eligibility, and calculate EMIs without uploading any identity documents or providing sensitive personal information.'),
              },
              {
                q: t('home.faq.q3', 'Is there any fee or charge to use YojnaSetu or apply for schemes?'),
                a: t('home.faq.a3', 'Zero. YojnaSetu is a free, open civic-tech platform. Government welfare schemes do not require facilitation fees, and all official application portals linked from YojnaSetu are free to access.'),
              },
              {
                q: t('home.faq.q4', 'What is the difference between an official portal and a channel partner?'),
                a: t('home.faq.a4', 'Many schemes allow direct online application on Ministry portals (e.g., Udyam, National Scholarship Portal). For credit and loan subsidy schemes, authorized channel partners (like Public Sector Banks and State Channelizing Agencies) process applications and disburse funds.'),
              },
              {
                q: t('home.faq.q5', 'How does YojnaSetu ensure that scheme guidelines and subsidies are accurate?'),
                a: t('home.faq.a5', 'Every scheme record in YojnaSetu is mapped directly to authoritative Gazette notifications, Ministry annual reports, and official RBI data returns. Our provenance system records the source document and last verified date for complete public auditability.'),
              },
            ].map((faq, idx) => {
              const isOpen = openFaqIndex === idx;
              return (
                <div
                  key={idx}
                  className="rounded-2xl border border-[#E8D8D2] overflow-hidden transition"
                >
                  <button
                    type="button"
                    onClick={() => setOpenFaqIndex(isOpen ? null : idx)}
                    className="w-full p-4 sm:p-5 text-left flex items-center justify-between hover:bg-[#FFF4EC]/40 transition cursor-pointer"
                    aria-expanded={isOpen}
                  >
                    <span className="text-sm sm:text-base font-bold text-[#3B2522] pr-4">
                      {faq.q}
                    </span>
                    <ChevronDown
                      className={`w-4 h-4 text-[#765E59] shrink-0 transition-transform duration-200 ${
                        isOpen ? 'rotate-180 text-[#EA717B]' : ''
                      }`}
                    />
                  </button>
                  {isOpen && (
                    <div className="p-4 sm:p-5 pt-0 border-t border-[#E8D8D2] text-xs sm:text-sm text-[#765E59] leading-relaxed bg-[#FFF4EC]/30">
                      {faq.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ============================================================
          9.6. HOMEPAGE BLOG & FINANCIAL GUIDANCE PREVIEW
          ============================================================ */}
      {latestBlogs.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-3xl p-6 sm:p-10 border border-[#E8D8D2] shadow-warm-sm space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
              <div className="space-y-1 text-left">
                <div className="inline-flex items-center gap-1.5 text-xs font-bold text-[#861823] bg-[#f7e9e9] px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{t('home.editorialGuides.badge', 'Editorial Guides')}</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-black text-[#3B2522] tracking-tight">
                  {t('home.editorialGuides.title', 'Latest Financial Guides & Welfare Insights')}
                </h2>
                <p className="text-sm text-[#765E59]">
                  {t('home.editorialGuides.subtitle', 'Plain-language explanations on scheme eligibility, borrowing, subsidies, and citizen rights.')}
                </p>
              </div>
              <Link
                to="/blogs"
                className="action-link text-sm font-bold flex items-center gap-1.5 self-start sm:self-end text-[#EA717B]"
              >
                <span>{t('home.editorialGuides.exploreAll', 'Explore All Guides')}</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {latestBlogs.map((blog) => (
                <Link
                  key={blog.blog_id}
                  to={`/blogs/${blog.blog_id}`}
                  className="civic-card p-6 flex flex-col justify-between group cursor-pointer hover:shadow-warm-md hover:-translate-y-1 transition"
                >
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-xs text-[#861823] font-bold">
                      <span className="bg-[#f7e9e9] px-2.5 py-0.5 rounded-full text-[10px] uppercase tracking-wider">{t('blogs.guide', 'Financial Guide')}</span>
                      <span className="text-[#765E59] font-medium">• {Math.max(1, Math.ceil(blog.content.trim().split(/\s+/).length / 200))} {t('home.editorialGuides.minRead', 'min read')}</span>
                    </div>
                    <h3 className="text-lg font-bold text-[#3B2522] group-hover:text-[#EA717B] transition line-clamp-2">
                      {blog.title}
                    </h3>
                    <p className="text-xs text-[#765E59] leading-relaxed line-clamp-3">
                      {blog.summary}
                    </p>
                  </div>
                  <div className="pt-4 mt-4 border-t border-[#E8D8D2]/60 flex items-center justify-between text-xs">
                    <span className="text-[#765E59] font-medium">
                      {new Date(blog.updated_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </span>
                    <span className="text-[#EA717B] font-bold flex items-center gap-1">
                      <span>{t('home.editorialGuides.readArticle', 'Read Article')}</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ============================================================
          10. FINAL MINIMAL CTA STRIP
          (Resolves Floto Issues 4, 7)
          ============================================================ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-[#4A2525] text-white rounded-3xl p-8 sm:p-12 shadow-warm-xl border border-[#3B2522] flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center md:text-left">
            <h2 className="text-xl sm:text-3xl font-black text-white">
              {t('home.editorialGuides.finalCtaTitle', 'Your next opportunity may already exist.')}
            </h2>
            <p className="text-base text-[#FFFBF0]/80 max-w-xl leading-relaxed">
              {t('home.editorialGuides.finalCtaSubtitle', 'Answer a few simple questions to find the government schemes you may qualify for. Takes less than 2 minutes.')}
            </p>
          </div>
          <Link
            to="/recommendations"
            className="btn btn-lg btn-primary shadow-warm-md min-h-[48px] inline-flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4 text-amber-200" />
            <span>{t('home.finalCtaButton')}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </div>
  );
};
