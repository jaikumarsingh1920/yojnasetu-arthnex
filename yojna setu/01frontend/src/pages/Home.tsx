import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { schemeApi } from '../api/schemeApi';
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
  Zap,
  Shield,
  UserCheck,
  ChevronLeft,
  ChevronRight,
  Compass,
  Sparkles,
} from 'lucide-react';
import heroEntrepreneur from '../assets/hero-entrepreneur.png';
import heroFarmer from '../assets/hero-farmer.png';

const HERO_SLIDES = [
  { image: heroEntrepreneur, position: 'center right' },
  { image: heroFarmer, position: 'center right' },
  { image: heroFarmer, position: 'center center' },
  { image: heroEntrepreneur, position: 'center center' },
];

export const Home: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [activeSlide, setActiveSlide] = useState(0);
  const dragStartX = useRef<number | null>(null);

  const [stats, setStats] = useState<{
    totalSchemes: number;
    verifiedSchemes: number;
    verifiedPercentage: number;
  }>({
    totalSchemes: 90,
    verifiedSchemes: 90,
    verifiedPercentage: 100,
  });

  /*
   * Existing scheme API logic kept intact.
   * Only UI presentation has been changed.
   */
  useEffect(() => {
    schemeApi
      .getSchemes({ page_size: 100 })
      .then((res) => {
        const total = res.total || res.items.length || 90;

        const verified =
          res.items.filter((s) => {
            const st = (s.verification_status || '').toUpperCase();

            return (
              st === 'VERIFIED' ||
              st === 'VERIFIED_OFFICIAL' ||
              st === 'SOURCE_VERIFIED'
            );
          }).length || total;

        const pct =
          total > 0 ? Math.round((verified / total) * 100) : 100;

        setStats({
          totalSchemes: total,
          verifiedSchemes: verified,
          verifiedPercentage: pct,
        });
      })
      .catch((err) => {
        console.error('Failed to load scheme statistics:', err);
      });
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (searchQuery.trim()) {
      navigate(
        `/schemes?search=${encodeURIComponent(searchQuery.trim())}`
      );
    } else {
      navigate('/schemes');
    }
  };

  const handleTrendingClick = (tag: string) => {
    navigate(`/schemes?search=${encodeURIComponent(tag)}`);
  };

  /*
   * Hero subtitle:
   * farmers -> communities
   */
  const heroSubtitle = t('home.heroSubtitle').replace(
    /farmers/gi,
    'communities'
  );

  useEffect(() => {
    const interval = window.setInterval(() => {
      setActiveSlide((current) => (current + 1) % HERO_SLIDES.length);
    }, 6000);

    return () => window.clearInterval(interval);
  }, []);

  const showPreviousSlide = () => {
    setActiveSlide((current) => (current - 1 + HERO_SLIDES.length) % HERO_SLIDES.length);
  };

  const showNextSlide = () => {
    setActiveSlide((current) => (current + 1) % HERO_SLIDES.length);
  };

  const handleHeroPointerDown = (event: React.PointerEvent<HTMLElement>) => {
    dragStartX.current = event.clientX;
  };

  const handleHeroPointerUp = (event: React.PointerEvent<HTMLElement>) => {
    if (dragStartX.current === null) return;

    const dragDistance = event.clientX - dragStartX.current;
    if (Math.abs(dragDistance) > 45) {
      dragDistance > 0 ? showPreviousSlide() : showNextSlide();
    }
    dragStartX.current = null;
  };

  return (
    <div className="space-y-10 sm:space-y-14 lg:space-y-16 pb-16 bg-[#fef9f3] min-h-screen">

      {/* ============================================================
          1. HERO SECTION
      ============================================================ */}

      <section
        className="text-white min-h-[420px] sm:min-h-[480px] lg:min-h-[520px] px-3.5 sm:px-6 lg:px-8 border-b-4 border-gov-saffron relative overflow-hidden flex items-center touch-pan-y select-none"
        onPointerDown={handleHeroPointerDown}
        onPointerUp={handleHeroPointerUp}
        onPointerCancel={() => { dragStartX.current = null; }}
      >

        {HERO_SLIDES.map((slide, index) => (
          <div
            key={index}
            aria-hidden={index !== activeSlide}
            className={`absolute inset-0 bg-cover bg-no-repeat transition-opacity duration-700 ${index === activeSlide ? 'opacity-100' : 'opacity-0'}`}
            style={{ backgroundImage: `url(${slide.image})`, backgroundPosition: slide.position }}
          />
        ))}

        <div className="absolute inset-0 bg-gradient-to-r from-[#861823]/95 via-[#861823]/78 to-[#861823]/35" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#4f0e16]/60 via-transparent to-transparent" />

        {/* Ambient Glow */}
        <div className="absolute top-1/4 left-10 w-72 sm:w-96 h-72 sm:h-96 bg-gov-saffron/20 rounded-full blur-3xl pointer-events-none" />

        <div className="absolute bottom-5 right-5 w-72 sm:w-96 h-72 sm:h-96 bg-[#d7832d]/20 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-4xl mx-auto text-center space-y-3 sm:space-y-6 relative z-10">

          {/* Status Indicator */}
          <div className="inline-flex items-center gap-1.5 sm:gap-2 bg-slate-800/90 border border-slate-600/80 px-2.5 sm:px-3.5 py-0.5 sm:py-1 rounded-full text-slate-200 text-[11px] sm:text-xs font-semibold backdrop-blur-md shadow-xs">

            <span className="flex h-2 w-2 relative shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />

              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>

            <span className="text-gov-saffron font-bold">
              {t('home.portalBadge')}
            </span>

            <span className="text-slate-400">•</span>

            <span>
              {stats.totalSchemes}{' '}
              {t('home.verifiedSchemesCount')}
            </span>
          </div>

          {/* Main Heading */}
          <h1 className="text-xl sm:text-3xl lg:text-5xl font-extrabold tracking-tight leading-snug sm:leading-tight text-white">
            {t(
              'home.heroCompactTitle',
              'Find Government Schemes That Fit You'
            )}
          </h1>

          {/* Subtitle
              farmers changed to communities */}
          <p className="text-slate-200 text-xs sm:text-sm lg:text-base leading-relaxed font-normal max-w-2xl mx-auto">
            {heroSubtitle}
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-2.5 sm:gap-3 pt-1 sm:pt-2 max-w-md sm:max-w-none mx-auto w-full">

            {/* Primary CTA */}
            <Link
              to="/recommendations"
              className="w-full sm:w-auto bg-gradient-to-r from-gov-saffron via-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white px-6 sm:px-7 py-3 sm:py-3.5 rounded-xl font-extrabold text-sm sm:text-base shadow-lg hover:shadow-orange-500/30 transition-all flex items-center justify-center gap-2 sm:gap-2.5 hover:-translate-y-0.5 min-h-[44px] sm:min-h-[48px] text-center"
            >
              {/* Font Awesome compatible icon */}
              <i className="fa-solid fa-wand-magic-sparkles text-amber-100 text-base sm:text-lg" />

              <span>
                {t('home.findMatchingSchemes')}
              </span>

              <ArrowRight className="w-4 h-4 text-white/90" />
            </Link>

            {/* Secondary CTA */}
            <Link
              to="/schemes"
              className="w-full sm:w-auto bg-slate-900/80 hover:bg-slate-800 text-slate-200 hover:text-white border border-slate-600 hover:border-slate-500 px-5 sm:px-6 py-2.5 sm:py-3.5 rounded-xl font-semibold text-xs sm:text-sm transition-all flex items-center justify-center gap-1.5 sm:gap-2 hover:-translate-y-0.5 min-h-[42px] sm:min-h-[48px] text-center"
            >
              <Search className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-sky-400" />

              <span>
                {t('home.exploreAllSchemes')}
              </span>
            </Link>
          </div>
        </div>

        <button
          type="button"
          onClick={showPreviousSlide}
          aria-label="Previous hero slide"
          className="absolute z-20 left-3 sm:left-6 lg:left-10 top-1/2 -translate-y-1/2 w-10 h-10 sm:w-12 sm:h-12 rounded-full border border-white/60 bg-[#861823]/70 hover:bg-[#861823] text-white flex items-center justify-center backdrop-blur-sm transition"
        >
          <ChevronLeft className="w-5 h-5 sm:w-6 sm:h-6" />
        </button>

        <button
          type="button"
          onClick={showNextSlide}
          aria-label="Next hero slide"
          className="absolute z-20 right-3 sm:right-6 lg:right-10 top-1/2 -translate-y-1/2 w-10 h-10 sm:w-12 sm:h-12 rounded-full border border-white/60 bg-[#861823]/70 hover:bg-[#861823] text-white flex items-center justify-center backdrop-blur-sm transition"
        >
          <ChevronRight className="w-5 h-5 sm:w-6 sm:h-6" />
        </button>

        <div className="absolute z-20 bottom-5 left-1/2 -translate-x-1/2 flex items-center gap-2">
          {HERO_SLIDES.map((_, index) => (
            <button
              key={index}
              type="button"
              onClick={() => setActiveSlide(index)}
              aria-label={`Show slide ${index + 1}`}
              aria-current={index === activeSlide}
              className={`h-2.5 rounded-full transition-all ${index === activeSlide ? 'w-7 bg-[#d7832d]' : 'w-2.5 bg-white/60 hover:bg-white'}`}
            />
          ))}
        </div>
      </section>


      {/* ============================================================
          2. HOME PAGE STATS
          90 Schemes / 128 Channel Partners / 12 Languages
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">

          {/* 90 Government Schemes */}
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs p-5 sm:p-6 text-center hover:shadow-md transition">

            <div className="text-3xl sm:text-4xl font-extrabold text-slate-900">
              90
            </div>

            <div className="mt-1 text-sm font-medium text-slate-500">
              Government Schemes
            </div>
          </div>


          {/* 128 Channel Partners */}
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs p-5 sm:p-6 text-center hover:shadow-md transition">

            <div className="text-3xl sm:text-4xl font-extrabold text-gov-saffron">
              128
            </div>

            <div className="mt-1 text-sm font-medium text-slate-500">
              Channel Partners
            </div>
          </div>


          {/* 12 Indian Languages */}
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs p-5 sm:p-6 text-center hover:shadow-md transition">

            <div className="text-3xl sm:text-4xl font-extrabold text-sky-600">
              12
            </div>

            <div className="mt-1 text-sm font-medium text-slate-500">
              Indian Languages
            </div>
          </div>

        </div>
      </section>


      

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <div className="bg-gradient-to-br from-[#861525] via-[#351827] to-[#071b2b] text-white rounded-3xl p-5 sm:p-8 lg:p-10 border border-[#a52a38]/60 shadow-xl relative overflow-hidden">
    {/* Background Glows */}
    <div className="absolute -right-16 -top-16 w-64 h-64 bg-[#d95f24]/15 rounded-full blur-3xl pointer-events-none" />
    <div className="absolute -left-16 -bottom-16 w-64 h-64 bg-[#8b1e2d]/25 rounded-full blur-3xl pointer-events-none" />

    <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-center">
      {/* Left Content */}
      <div className="lg:col-span-8 space-y-4 text-left">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 bg-white/10 text-[#ffb347] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border border-[#ff9d2e]/30">
          {/* Font Awesome */}
          <i className="fa-solid fa-user-check text-xs" />
          <span>
            {t('home.matchingFlow')}
          </span>
        </div>

        {/* Heading */}
        <h2 className="text-xl sm:text-3xl font-extrabold text-white tracking-tight">
          {t('home.smartMatchingTitle')}
        </h2>

        {/* Four Pillars */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
          {/* Personalized Matching */}
          <div className="flex items-center gap-2.5 text-xs text-slate-100 bg-white/5 border border-white/10 px-3.5 py-2 rounded-xl">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              {t('home.personalizedMatching')}
            </span>
          </div>

          {/* Rule Based Eligibility */}
          <div className="flex items-center gap-2.5 text-xs text-slate-100 bg-white/5 border border-white/10 px-3.5 py-2 rounded-xl">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              {t('home.ruleBasedEligibility')}
            </span>
          </div>

          {/* Official Sources */}
          <div className="flex items-center gap-2.5 text-xs text-slate-100 bg-white/5 border border-white/10 px-3.5 py-2 rounded-xl">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              {t('home.officialSources')}
            </span>
          </div>

          {/* No Document Upload */}
          <div className="flex items-center gap-2.5 text-xs text-slate-100 bg-white/5 border border-white/10 px-3.5 py-2 rounded-xl">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              {t('home.noDocumentUpload')}
            </span>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="lg:col-span-4 flex flex-col items-center lg:items-end justify-center pt-2 lg:pt-0">
        <Link
          to="/recommendations"
          className="w-full sm:w-auto bg-gov-saffron hover:bg-orange-600 text-white px-7 py-3.5 rounded-2xl font-extrabold text-sm sm:text-base shadow-xl hover:shadow-orange-500/30 transition-all flex items-center justify-center gap-2.5 hover:-translate-y-0.5 text-center min-h-[48px]"
        >
          {/* Font Awesome AI Icon */}
          <i className="fa-solid fa-wand-magic-sparkles text-amber-200 text-base" />
          <span>
            {t('home.findMatchingSchemes')}
          </span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  </div>
</section>


       <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-8 space-y-2">
          <div className="inline-flex items-center gap-1.5 bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border border-slate-200">
            <Compass className="w-3.5 h-3.5 text-gov-blue" />
            <span>{t('home.howItWorks.badge')}</span>
          </div>
          <h2 className="text-xl sm:text-3xl font-extrabold text-slate-900">{t('home.howItWorksTitle')}</h2>
          <p className="text-xs sm:text-sm text-slate-500">
            {t('home.howItWorksSub')}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              step: "01",
              title: t('home.stepTellUs'),
              desc: t('home.stepTellUsDesc'),
              icon: FileText,
              color: "text-amber-600 bg-amber-50 border-amber-200",
            },
            {
              step: "02",
              title: t('home.stepCheckEligibility'),
              desc: t('home.stepCheckEligibilityDesc'),
              icon: ShieldCheck,
              color: "text-blue-600 bg-blue-50 border-blue-200",
            },
            {
              step: "03",
              title: t('home.stepDiscoverSchemes'),
              desc: t('home.stepDiscoverSchemesDesc'),
              icon: Sparkles,
              color: "text-gov-saffron bg-orange-50 border-orange-200",
            },
            {
              step: "04",
              title: t('home.stepOfficialRoute'),
              desc: t('home.stepOfficialRouteDesc'),
              icon: MapPin,
              color: "text-emerald-600 bg-emerald-50 border-emerald-200",
            },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.step}
                className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs space-y-3 hover:shadow-md hover:-translate-y-0.5 transition duration-200 flex flex-col justify-between"
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xl font-black text-slate-300 tracking-tight">
                      {item.step}
                    </span>
                    <div className={`p-2 rounded-xl border ${item.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>
                  <h3 className="text-sm sm:text-base font-bold text-slate-900">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed font-normal">
                    {item.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>


      {/* ============================================================
          4. SEARCH & POPULAR FOCUS AREAS
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="bg-white rounded-3xl p-5 sm:p-8 border border-slate-200/90 shadow-xs space-y-5">

          {/* Heading */}
          <div className="text-left space-y-1">

            <h3 className="text-base sm:text-lg font-extrabold text-slate-900 flex items-center gap-2">

              <Search className="w-4 h-4 text-sky-600" />

              <span>
                {t(
                  'home.searchHeading',
                  'Search Schemes by Keyword or Focus Area'
                )}
              </span>
            </h3>

            <p className="text-xs text-slate-500">
              {t(
                'home.searchSubheading',
                'Quickly explore schemes using direct keywords or popular welfare topics'
              )}
            </p>

          </div>


          {/* Search Form */}
          <form
            onSubmit={handleSearchSubmit}
            className="max-w-3xl"
          >

            <div className="flex items-center bg-slate-50 rounded-2xl p-1.5 border border-slate-300 focus-within:border-sky-500 focus-within:ring-2 focus-within:ring-sky-200 transition">

              <div className="pl-3 text-slate-400">
                <Search className="w-4 h-4 sm:w-5 sm:h-5" />
              </div>

              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t('home.searchPlaceholder')}
                className="w-full min-w-0 flex-1 px-2.5 sm:px-3 py-2 text-xs sm:text-sm text-slate-900 bg-transparent outline-none placeholder:text-slate-400 font-medium"
              />

              <button
                type="submit"
                className="bg-gov-blue hover:bg-slate-800 text-white px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition flex items-center gap-1.5 shrink-0"
              >

                <span>
                  {t('home.searchButton')}
                </span>

                <ArrowRight className="w-3.5 h-3.5" />

              </button>

            </div>

          </form>


          {/* Popular Focus */}
          <div className="space-y-2 pt-1 border-t border-slate-100">

            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">

              <TrendingUp className="w-3.5 h-3.5 text-amber-600" />

              <span>
                {t('home.popularFocus')}
              </span>

            </div>


            <div className="flex flex-wrap gap-2">

              {[
                {
                  label: 'MUDRA Loan',
                  query: 'MUDRA',
                },
                {
                  label: 'Women Entrepreneurs',
                  query: 'Women',
                },
                {
                  label: 'PM Vishwakarma',
                  query: 'Vishwakarma',
                },
                {
                  label: 'Agriculture & Dairy',
                  query: 'Agriculture',
                },
                {
                  label: 'Scholarships',
                  query: 'Scholarship',
                },
                {
                  label: 'Ayushman Bharat',
                  query: 'Ayushman',
                },
              ].map((chip) => (

                <button
                  key={chip.label}
                  type="button"
                  onClick={() =>
                    handleTrendingClick(chip.query)
                  }
                  className="bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-slate-900 border border-slate-200 px-3 py-1.5 rounded-lg text-xs font-medium transition shadow-2xs flex items-center gap-1"
                >
                  <span>
                    {chip.label}
                  </span>
                </button>

              ))}

            </div>
          </div>

        </div>
      </section>


      {/* ============================================================
          5. EXPLORE BY CATEGORY
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="mb-6">

          <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-gov-saffron bg-amber-50 px-2.5 py-0.5 rounded border border-amber-200 mb-1.5">

            <Zap className="w-3.5 h-3.5" />

            <span>
              {t('home.categorySectionBadge')}
            </span>

          </div>

          <h2 className="text-xl sm:text-3xl font-extrabold text-slate-900">
            {t('home.exploreByCategory')}
          </h2>

          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            {t('home.exploreByCategorySub')}
          </p>

        </div>


        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">

          {[
            {
              title: t('home.categories.msmeTitle'),
              desc: t('home.categories.msmeDesc'),
              icon: Building2,
              color:
                'text-blue-600 bg-blue-50 border-blue-200',
              count: 'PMEGP, MUDRA, Stand-Up India',
              query: 'MUDRA',
            },
            {
              title: t('home.categories.agriTitle'),
              desc: t('home.categories.agriDesc'),
              icon: Coins,
              color:
                'text-emerald-600 bg-emerald-50 border-emerald-200',
              count: 'KCC, NLM, PM-KUSUM',
              query: 'Agriculture',
            },
            {
              title: t('home.categories.artisanTitle'),
              desc: t('home.categories.artisanDesc'),
              icon: Hammer,
              color:
                'text-amber-600 bg-amber-50 border-amber-200',
              count: 'PM Vishwakarma, NSFDC',
              query: 'Vishwakarma',
            },
            {
              title: t('home.categories.eduTitle'),
              desc: t('home.categories.eduDesc'),
              icon: GraduationCap,
              color:
                'text-indigo-600 bg-indigo-50 border-indigo-200',
              count: 'PM-YASASVI, NMMS',
              query: 'Scholarship',
            },
            {
              title: t('home.categories.socialTitle'),
              desc: t('home.categories.socialDesc'),
              icon: HeartHandshake,
              color:
                'text-rose-600 bg-rose-50 border-rose-200',
              count: 'APY, PMSBY, PMJJBY',
              query: 'Pension',
            },
            {
              title: t('home.categories.healthTitle'),
              desc: t('home.categories.healthDesc'),
              icon: ShieldCheck,
              color:
                'text-teal-600 bg-teal-50 border-teal-200',
              count: 'AB-PMJAY, PMMVY, SSY',
              query: 'Health',
            },
          ].map((cat) => {

            const Icon = cat.icon;

            return (
              <div
                key={cat.title}
                onClick={() =>
                  handleTrendingClick(cat.query)
                }
                className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs hover:shadow-md hover:-translate-y-0.5 transition duration-200 cursor-pointer group flex flex-col justify-between"
              >

                <div className="space-y-2.5">

                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center border ${cat.color} group-hover:scale-105 transition-transform duration-200`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>

                  <h3 className="text-sm sm:text-base font-extrabold text-slate-900 group-hover:text-sky-700 transition">
                    {cat.title}
                  </h3>

                  <p className="text-xs text-slate-600 leading-relaxed font-normal">
                    {cat.desc}
                  </p>

                </div>


                <div className="pt-3 border-t border-slate-100 flex items-center justify-between mt-3">

                  <span className="text-[11px] font-semibold text-slate-500">
                    {cat.count}
                  </span>

                  <span className="text-xs font-bold text-sky-700 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">

                    <span>
                      {t(
                        'schemes.viewDetails',
                        'View Details'
                      )}
                    </span>

                    <ArrowRight className="w-3.5 h-3.5" />

                  </span>

                </div>

              </div>
            );
          })}

        </div>
      </section>


      {/* ============================================================
          6. TRUST & OFFICIAL PROVENANCE
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="bg-white rounded-3xl p-5 sm:p-8 lg:p-10 border border-slate-200/90 shadow-xs space-y-6">

          {/* Trust Heading */}
          <div className="max-w-3xl space-y-1.5 text-left">

            <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">

              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />

              <span>
                {t('home.trustBadge')}
              </span>

            </div>

            <h2 className="text-xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {t('home.trustTitle')}
            </h2>

            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed font-normal">
              {t('home.trustDesc')}
            </p>

          </div>


          {/* Trust Pillars */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

            {/* Pillar 1 */}
            <div className="bg-slate-50 p-4 sm:p-5 rounded-2xl border border-slate-200/80 space-y-1.5">

              <div className="flex items-center gap-2 text-sky-700 font-bold text-xs sm:text-sm">

                <FileCheck2 className="w-4 h-4 shrink-0" />

                <h4>
                  {t('home.trustPillar1')}
                </h4>

              </div>

              <p className="text-xs text-slate-600 leading-relaxed font-normal">
                {t('home.trustPillar1Desc')}
              </p>

            </div>


            {/* Pillar 2 */}
            <div className="bg-slate-50 p-4 sm:p-5 rounded-2xl border border-slate-200/80 space-y-1.5">

              <div className="flex items-center gap-2 text-emerald-700 font-bold text-xs sm:text-sm">

                <CheckCircle2 className="w-4 h-4 shrink-0" />

                <h4>
                  {t('home.trustPillar2')}
                </h4>

              </div>

              <p className="text-xs text-slate-600 leading-relaxed font-normal">
                {t('home.trustPillar2Desc')}
              </p>

            </div>


            {/* Pillar 3 */}
            <div className="bg-slate-50 p-4 sm:p-5 rounded-2xl border border-slate-200/80 space-y-1.5">

              <div className="flex items-center gap-2 text-amber-700 font-bold text-xs sm:text-sm">

                <Building2 className="w-4 h-4 shrink-0" />

                <h4>
                  {t('home.trustPillar3')}
                </h4>

              </div>

              <p className="text-xs text-slate-600 leading-relaxed font-normal">
                {t('home.trustPillar3Desc')}
              </p>

            </div>


            {/* Pillar 4 */}
            <div className="bg-slate-50 p-4 sm:p-5 rounded-2xl border border-slate-200/80 space-y-1.5">

              <div className="flex items-center gap-2 text-indigo-700 font-bold text-xs sm:text-sm">

                <Shield className="w-4 h-4 shrink-0" />

                <h4>
                  {t('home.trustPillar4')}
                </h4>

              </div>

              <p className="text-xs text-slate-600 leading-relaxed font-normal">
                {t('home.trustPillar4Desc')}
              </p>

            </div>

          </div>


          {/* Existing Trust Stats removed.
              New 90 / 128 / 12 stats are already placed
              near the top of the Home page. */}

        </div>
      </section>


      {/* ============================================================
          FINAL CTA REMOVED
          
          "Ready to Discover Schemes You May Be Eligible For?"
          removed because the same Find Matching Schemes CTA
          already exists above.
      ============================================================ */}

    </div>
  );
};
