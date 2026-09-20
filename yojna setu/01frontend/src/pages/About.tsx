import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  ShieldCheck,
  Languages,
  ArrowRight,
  CheckCircle2,
  Landmark,
  Users,
  FileCheck2,
  Sparkles,
  MapPin,
  Calculator,
  Search,
  HeartHandshake,
  BadgeCheck,
  Globe2,
  LockKeyhole,
  CircleCheck,
  Shield,
} from 'lucide-react';

export const About: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="space-y-10 sm:space-y-14 lg:space-y-16 pb-16 bg-[#FFFBF0] min-h-screen">

      {/* ============================================================
          1. ABOUT HERO
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 sm:pt-8">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white border border-[#E8D8D2]/20 shadow-warm-md">
          {/* Background Glows */}
          <div className="absolute -right-24 -top-24 w-80 h-80 bg-[#F7AE56]/15 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -left-24 -bottom-24 w-80 h-80 bg-[#EA717B]/20 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 px-5 py-8 sm:px-8 sm:py-12 lg:px-12 lg:py-14">
            <div className="max-w-4xl">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 bg-white/10 text-[#FFD0CA] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border border-[#FFD0CA]/25 mb-5">
                <Landmark className="w-3.5 h-3.5 text-[#F7AE56]" />
                <span>{t('about.heroBadge', 'Government Citizen Platform')}</span>
              </div>

              {/* Heading */}
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight leading-tight text-white">
                {t('about.heroTitle', 'About YojnaSetu')}
              </h1>

              {/* Description */}
              <p className="mt-4 text-sm sm:text-base lg:text-lg text-[#FFD0CA] leading-relaxed max-w-3xl">
                {t('about.heroDesc', 'YojnaSetu is a national civic-tech welfare guidance platform designed to bridge the gap between Indian citizens and government welfare, credit, and subsidy programs.')}
              </p>

              {/* Trust Chips */}
              <div className="flex flex-wrap gap-2.5 mt-7">
                <div className="inline-flex items-center gap-2 bg-white/10 border border-white/15 px-3.5 py-2 rounded-xl text-xs sm:text-sm text-white">
                  <BadgeCheck className="w-4 h-4 text-[#F7AE56]" />
                  <span>{t('about.verifiedSchemes', 'Verified Government Schemes')}</span>
                </div>

                <div className="inline-flex items-center gap-2 bg-white/10 border border-white/15 px-3.5 py-2 rounded-xl text-xs sm:text-sm text-white">
                  <ShieldCheck className="w-4 h-4 text-emerald-300" />
                  <span>{t('about.ruleBasedEligibility', 'Rule-Based Eligibility')}</span>
                </div>

                <div className="inline-flex items-center gap-2 bg-white/10 border border-white/15 px-3.5 py-2 rounded-xl text-xs sm:text-sm text-white">
                  <Languages className="w-4 h-4 text-[#FFD0CA]" />
                  <span>{t('about.multilingualAccess', 'Multilingual Access')}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
          2. WHO WE ARE
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 sm:gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs p-5 sm:p-8">
            <div className="flex items-start gap-3 mb-5">
              <div className="w-11 h-11 rounded-xl bg-[#FFF4EC] border border-[#FFD0CA] flex items-center justify-center shrink-0">
                <Users className="w-5 h-5 text-[#EA717B]" />
              </div>

              <div>
                <div className="text-[11px] sm:text-xs font-bold uppercase tracking-wider text-[#EA717B] mb-1">
                  {t('about.whoWeAreBadge', 'Who We Are')}
                </div>

                <h2 className="text-xl sm:text-2xl font-extrabold text-[#3B2522] tracking-tight">
                  {t('about.whoWeAreTitle', 'Connecting Citizens With Welfare Opportunities')}
                </h2>
              </div>
            </div>

            <div className="space-y-4 text-sm text-[#765E59] leading-relaxed">
              <p>
                {t('about.whoWeAreP1', 'Government welfare schemes can provide valuable support in areas such as entrepreneurship, agriculture, education, healthcare, social security, and financial assistance.')}
              </p>
              <p>
                {t('about.whoWeAreP2', 'However, citizens often have to navigate multiple portals, eligibility conditions, application procedures, and official guidelines to identify the schemes relevant to them.')}
              </p>
              <p>
                {t('about.whoWeAreP3', 'YojnaSetu brings this discovery journey together through a citizen-focused interface that helps users explore schemes, understand eligibility requirements, calculate financial benefits, and find official assistance channels.')}
              </p>
            </div>
          </div>

          {/* Mission Card */}
          <div className="bg-gradient-to-br from-[#4A2525] via-[#3B2522] to-[#4A2525] rounded-3xl p-6 sm:p-7 text-white shadow-warm-md border border-[#E8D8D2]/20 relative overflow-hidden">
            <div className="absolute -right-16 -top-16 w-44 h-44 bg-[#F7AE56]/15 rounded-full blur-3xl pointer-events-none" />

            <div className="relative z-10">
              <div className="w-11 h-11 rounded-xl bg-white/10 border border-white/15 flex items-center justify-center mb-5">
                <HeartHandshake className="w-5 h-5 text-[#FFD0CA]" />
              </div>

              <p className="text-[11px] font-bold uppercase tracking-wider text-[#FFD0CA]">
                {t('about.missionBadge', 'Our Mission')}
              </p>

              <h3 className="text-xl sm:text-2xl font-extrabold mt-2 leading-tight text-white">
                {t('about.missionTitle', 'Making welfare discovery simpler for every citizen.')}
              </h3>

              <p className="text-xs sm:text-sm text-[#FFD0CA] leading-relaxed mt-4">
                {t('about.missionDesc', 'One platform to discover relevant schemes, understand eligibility, and reach official channels with confidence.')}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
          3. WHAT YOJNASETU OFFERS
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-7 space-y-2">
          <div className="inline-flex items-center gap-1.5 bg-[#FFF4EC] text-[#4A2525] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border border-[#FFD0CA]">
            <Sparkles className="w-3.5 h-3.5 text-[#F7AE56]" />
            <span>{t('about.capabilitiesBadge', 'Platform Capabilities')}</span>
          </div>

          <h2 className="text-xl sm:text-3xl font-extrabold text-[#3B2522]">
            {t('about.capabilitiesTitle', 'Everything You Need to Navigate Welfare Schemes')}
          </h2>

          <p className="text-xs sm:text-sm text-[#765E59]">
            {t('about.capabilitiesDesc', 'Simple tools and guidance designed around the needs of citizens.')}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Scheme Discovery */}
          <div className="bg-white p-5 sm:p-6 rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-0.5 transition duration-200">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#FFF4EC] border border-[#FFD0CA] text-[#EA717B] mb-4">
              <Search className="w-5 h-5" />
            </div>

            <h3 className="text-sm sm:text-base font-extrabold text-[#3B2522]">
              {t('about.schemeDiscoveryTitle', 'Scheme Discovery')}
            </h3>

            <p className="text-xs text-[#765E59] leading-relaxed mt-2">
              {t('about.schemeDiscoveryDesc', 'Search and explore government schemes using keywords, categories, ministries, and welfare focus areas.')}
            </p>
          </div>

          {/* Smart Matching */}
          <div className="bg-white p-5 sm:p-6 rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-0.5 transition duration-200">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#FFF4EC] border border-[#FFD0CA] text-[#F7AE56] mb-4">
              <Sparkles className="w-5 h-5" />
            </div>

            <h3 className="text-sm sm:text-base font-extrabold text-[#3B2522]">
              {t('about.smartMatchingTitle', 'Smart Scheme Matching')}
            </h3>

            <p className="text-xs text-[#765E59] leading-relaxed mt-2">
              {t('about.smartMatchingDesc', "Discover schemes that may match a citizen's demographic, financial, and occupational profile.")}
            </p>
          </div>

          {/* Eligibility */}
          <div className="bg-white p-5 sm:p-6 rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-0.5 transition duration-200">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-emerald-50 border border-emerald-200 text-emerald-600 mb-4">
              <ShieldCheck className="w-5 h-5" />
            </div>

            <h3 className="text-sm sm:text-base font-extrabold text-[#3B2522]">
              {t('about.eligibilityGuidanceTitle', 'Eligibility Guidance')}
            </h3>

            <p className="text-xs text-[#765E59] leading-relaxed mt-2">
              {t('about.eligibilityGuidanceDesc', 'Understand eligibility requirements through explicit, deterministic rules based on official scheme guidelines.')}
            </p>
          </div>

          {/* Financial Calculator */}
          <div className="bg-white p-5 sm:p-6 rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-0.5 transition duration-200">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#FFF4EC] border border-[#FFD0CA] text-[#EA717B] mb-4">
              <Calculator className="w-5 h-5" />
            </div>

            <h3 className="text-sm sm:text-base font-extrabold text-[#3B2522]">
              {t('about.financialCalcTitle', 'Financial Calculators')}
            </h3>

            <p className="text-xs text-[#765E59] leading-relaxed mt-2">
              {t('about.financialCalcDesc', 'Estimate loan EMIs, interest costs, and subsidy benefits before applying for credit-linked schemes.')}
            </p>
          </div>

          {/* Nearby Assistance */}
          <div className="bg-white p-5 sm:p-6 rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-0.5 transition duration-200">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#FFF4EC] border border-[#FFD0CA] text-[#F7AE56] mb-4">
              <MapPin className="w-5 h-5" />
            </div>

            <h3 className="text-sm sm:text-base font-extrabold text-[#3B2522]">
              {t('about.partnerCentersTitle', 'Nearby Partner Centers')}
            </h3>

            <p className="text-xs text-[#765E59] leading-relaxed mt-2">
              {t('about.partnerCentersDesc', 'Locate authorized CSC centers, bank branches, and implementation partner offices near your location.')}
            </p>
          </div>

          {/* Multilingual Access */}
          <div className="bg-white p-5 sm:p-6 rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:-translate-y-0.5 transition duration-200">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#FFF4EC] border border-[#FFD0CA] text-[#EA717B] mb-4">
              <Globe2 className="w-5 h-5" />
            </div>

            <h3 className="text-sm sm:text-base font-extrabold text-[#3B2522]">
              {t('about.multilingualAccess', 'Multilingual Access')}
            </h3>

            <p className="text-xs text-[#765E59] leading-relaxed mt-2">
              {t('home.heroChipsLanguages', 'Full parity across 12 scheduled Indian languages with instant switching.')}
            </p>
          </div>
        </div>
      </section>

      {/* ============================================================
          4. TRUST & TRANSPARENCY
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-2">
            {/* Left */}
            <div className="p-6 sm:p-8 lg:p-10">
              <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 mb-4">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>{t('footer.governanceTitle', 'Trust & Transparency')}</span>
              </div>

              <h2 className="text-xl sm:text-3xl font-extrabold text-[#3B2522] tracking-tight">
                {t('footer.governanceDesc', 'Designed Around Citizen Trust')}
              </h2>

              <p className="text-xs sm:text-sm text-[#765E59] leading-relaxed mt-3 max-w-xl">
                {t('footer.aboutDesc', 'YojnaSetu focuses on clear eligibility guidance, official scheme information, transparent routes, and a simple citizen experience.')}
              </p>

              <div className="space-y-3 mt-6">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#FFF4EC] border border-[#FFD0CA] flex items-center justify-center shrink-0">
                    <FileCheck2 className="w-4 h-4 text-[#EA717B]" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[#3B2522]">
                      {t('about.deterministicTitle', '100% Deterministic Engine')}
                    </h4>
                    <p className="text-xs text-[#765E59] mt-0.5">
                      {t('about.deterministicDesc', 'Eligibility criteria are verified against statutory government gazettes using deterministic logic—never arbitrary generative AI assumptions.')}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center shrink-0">
                    <CircleCheck className="w-4 h-4 text-emerald-600" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[#3B2522]">
                      {t('about.provenanceTitle', 'Gazette Provenance')}
                    </h4>
                    <p className="text-xs text-[#765E59] mt-0.5">
                      {t('about.provenanceDesc', 'Review official circulars, notifications, and statutory sources backing each indexed welfare scheme.')}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#FFF4EC] border border-[#FFD0CA] flex items-center justify-center shrink-0">
                    <LockKeyhole className="w-4 h-4 text-[#F7AE56]" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[#3B2522]">
                      {t('about.zeroPiiTitle', 'Zero PII Storage Policy')}
                    </h4>
                    <p className="text-xs text-[#765E59] mt-0.5">
                      {t('about.zeroPiiDesc', 'YojnaSetu strictly adheres to a Zero Personally Identifiable Information storage model. We never store Aadhaar numbers, PAN cards, or sensitive identity documents.')}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Dark Panel */}
            <div className="bg-gradient-to-br from-[#4A2525] via-[#3B2522] to-[#4A2525] p-6 sm:p-8 lg:p-10 text-white relative overflow-hidden">
              <div className="absolute -right-20 -top-20 w-64 h-64 bg-[#F7AE56]/10 rounded-full blur-3xl pointer-events-none" />

              <div className="relative z-10">
                <div className="w-12 h-12 rounded-xl bg-white/10 border border-white/15 flex items-center justify-center mb-5">
                  <Shield className="w-6 h-6 text-[#FFD0CA]" />
                </div>

                <h3 className="text-xl sm:text-2xl font-extrabold text-white">
                  {t('home.heroSub', 'Clear. Guided. Citizen-Focused.')}
                </h3>

                <p className="text-xs sm:text-sm text-[#FFD0CA] leading-relaxed mt-3">
                  {t('about.heroDesc', 'From discovering a scheme to finding the right assistance channel, YojnaSetu aims to make every step easier to understand.')}
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-6">
                  <div className="flex items-center gap-2 bg-white/10 border border-white/15 px-3 py-2.5 rounded-xl text-xs text-white font-medium">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>{t('about.verifiedSchemes', 'Verified information')}</span>
                  </div>

                  <div className="flex items-center gap-2 bg-white/10 border border-white/15 px-3 py-2.5 rounded-xl text-xs text-white font-medium">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>{t('about.ruleBasedEligibility', 'Rule-based guidance')}</span>
                  </div>

                  <div className="flex items-center gap-2 bg-white/10 border border-white/15 px-3 py-2.5 rounded-xl text-xs text-white font-medium">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>{t('schemeDetail.applyOfficial', 'Official routes')}</span>
                  </div>

                  <div className="flex items-center gap-2 bg-white/10 border border-white/15 px-3 py-2.5 rounded-xl text-xs text-white font-medium">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>{t('about.heroBadge', 'Citizen-first design')}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
          5. HOW YOJNASETU HELPS
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-7 space-y-2">
          <div className="inline-flex items-center gap-1.5 bg-[#FFF4EC] text-[#4A2525] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border border-[#FFD0CA]">
            <CompassIcon />
            <span>{t('nav.howYojnaSetuWorks', 'Citizen Journey')}</span>
          </div>

          <h2 className="text-xl sm:text-3xl font-extrabold text-[#3B2522]">
            {t('home.howItWorksTitle', 'From Discovery to Action')}
          </h2>

          <p className="text-xs sm:text-sm text-[#765E59]">
            {t('home.howItWorksSubtitle', 'A straightforward journey to help citizens find and understand relevant welfare opportunities.')}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Step 1 */}
          <div className="bg-white p-5 rounded-2xl border border-[#E8D8D2] shadow-warm-xs">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xl font-black text-[#E8D8D2]">01</span>
              <div className="w-9 h-9 rounded-xl bg-[#FFF4EC] border border-[#FFD0CA] flex items-center justify-center">
                <Search className="w-4 h-4 text-[#EA717B]" />
              </div>
            </div>

            <h3 className="text-sm font-bold text-[#3B2522]">
              {t('home.step1Title', 'Discover')}
            </h3>

            <p className="text-xs text-[#765E59] leading-relaxed mt-2">
              {t('home.step1Desc', 'Search or browse government schemes based on your area of interest.')}
            </p>
          </div>

          {/* Step 2 */}
          <div className="bg-white p-5 rounded-2xl border border-[#E8D8D2] shadow-warm-xs">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xl font-black text-[#E8D8D2]">02</span>
              <div className="w-9 h-9 rounded-xl bg-[#FFF4EC] border border-[#FFD0CA] flex items-center justify-center">
                <ShieldCheck className="w-4 h-4 text-[#F7AE56]" />
              </div>
            </div>

            <h3 className="text-sm font-bold text-[#3B2522]">
              {t('home.step2Title', 'Check Eligibility')}
            </h3>

            <p className="text-xs text-[#765E59] leading-relaxed mt-2">
              {t('home.step2Desc', 'Understand whether the scheme conditions align with your profile.')}
            </p>
          </div>

          {/* Step 3 */}
          <div className="bg-white p-5 rounded-2xl border border-[#E8D8D2] shadow-warm-xs">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xl font-black text-[#E8D8D2]">03</span>
              <div className="w-9 h-9 rounded-xl bg-[#FFF4EC] border border-[#FFD0CA] flex items-center justify-center">
                <FileCheck2 className="w-4 h-4 text-[#EA717B]" />
              </div>
            </div>

            <h3 className="text-sm font-bold text-[#3B2522]">
              {t('home.step3Title', 'Understand Benefits')}
            </h3>

            <p className="text-xs text-[#765E59] leading-relaxed mt-2">
              {t('home.step3Desc', 'Review scheme benefits, requirements, and important details in one place.')}
            </p>
          </div>

          {/* Step 4 */}
          <div className="bg-white p-5 rounded-2xl border border-[#E8D8D2] shadow-warm-xs">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xl font-black text-[#E8D8D2]">04</span>
              <div className="w-9 h-9 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center">
                <MapPin className="w-4 h-4 text-emerald-600" />
              </div>
            </div>

            <h3 className="text-sm font-bold text-[#3B2522]">
              {t('home.step4Title', 'Reach the Official Route')}
            </h3>

            <p className="text-xs text-[#765E59] leading-relaxed mt-2">
              {t('home.step4Desc', 'Find official application routes and nearby assistance partners when required.')}
            </p>
          </div>
        </div>
      </section>

      {/* ============================================================
          6. PLATFORM PRINCIPLES
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-br from-[#4A2525] via-[#3B2522] to-[#4A2525] rounded-3xl p-6 sm:p-8 lg:p-10 text-white border border-[#E8D8D2]/20 shadow-warm-md relative overflow-hidden">
          <div className="absolute -right-20 -top-20 w-72 h-72 bg-[#F7AE56]/15 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10">
            <div className="max-w-3xl mb-7">
              <div className="inline-flex items-center gap-1.5 bg-white/10 text-[#FFD0CA] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border border-[#FFD0CA]/25">
                <ShieldCheck className="w-3.5 h-3.5 text-[#F7AE56]" />
                <span>{t('footer.governanceTitle', 'Our Principles')}</span>
              </div>

              <h2 className="text-xl sm:text-3xl font-extrabold tracking-tight mt-3 text-white">
                {t('home.heroSub', 'Built for Simplicity, Transparency & Access')}
              </h2>

              <p className="text-xs sm:text-sm text-[#FFD0CA] leading-relaxed mt-2">
                {t('about.heroDesc', 'The platform experience is centered around making welfare information easier to discover and understand.')}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <div className="bg-white/10 border border-white/15 rounded-2xl p-4">
                <ShieldCheck className="w-5 h-5 text-emerald-400 mb-3" />
                <h3 className="text-sm font-bold text-white">{t('common.trust', 'Trust')}</h3>
                <p className="text-xs text-[#FFFBF0]/90 leading-relaxed mt-1.5">
                  {t('about.deterministicDesc', 'Clear information and transparent guidance.')}
                </p>
              </div>

              <div className="bg-white/10 border border-white/15 rounded-2xl p-4">
                <Users className="w-5 h-5 text-[#F7AE56] mb-3" />
                <h3 className="text-sm font-bold text-white">{t('common.accessibility', 'Accessibility')}</h3>
                <p className="text-xs text-[#FFFBF0]/90 leading-relaxed mt-1.5">
                  {t('about.capabilitiesDesc', 'Designed around diverse citizen needs.')}
                </p>
              </div>

              <div className="bg-white/10 border border-white/15 rounded-2xl p-4">
                <Languages className="w-5 h-5 text-[#FFD0CA] mb-3" />
                <h3 className="text-sm font-bold text-white">{t('about.multilingualAccess', 'Inclusion')}</h3>
                <p className="text-xs text-[#FFFBF0]/90 leading-relaxed mt-1.5">
                  {t('home.heroChipsLanguages', 'Multilingual access for wider reach across all 12 scheduled Indian languages.')}
                </p>
              </div>

              <div className="bg-white/10 border border-white/15 rounded-2xl p-4">
                <FileCheck2 className="w-5 h-5 text-[#EA717B] mb-3" />
                <h3 className="text-sm font-bold text-white">{t('common.clarity', 'Clarity')}</h3>
                <p className="text-xs text-[#FFFBF0]/90 leading-relaxed mt-1.5">
                  {t('about.whoWeAreP3', 'Simple presentation of complex scheme information.')}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================
          7. FINAL CTA
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs p-6 sm:p-8 lg:p-10">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#EA717B] bg-[#FFF4EC] px-2.5 py-1 rounded-full border border-[#FFD0CA] mb-3">
                <Sparkles className="w-3.5 h-3.5 text-[#F7AE56]" />
                <span>{t('home.heroBadge', 'Get Started')}</span>
              </div>

              <h2 className="text-xl sm:text-3xl font-extrabold text-[#3B2522] tracking-tight">
                {t('home.heroHeading', 'Find Government Schemes That Fit You')}
              </h2>

              <p className="text-xs sm:text-sm text-[#765E59] leading-relaxed mt-2">
                {t('home.heroDesc', 'Explore schemes, check eligibility, and discover relevant government welfare opportunities.')}
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-2.5 w-full lg:w-auto">
              <Link
                to="/recommendations"
                className="w-full sm:w-auto bg-[#EA717B] hover:bg-[#d65f69] text-white px-6 py-3 rounded-xl font-extrabold text-sm shadow-warm-xs transition-all flex items-center justify-center gap-2 hover:-translate-y-0.5"
              >
                <Sparkles className="w-4 h-4" />
                <span>{t('about.checkEligibilityCta', 'Find Matching Schemes')}</span>
                <ArrowRight className="w-4 h-4" />
              </Link>

              <Link
                to="/schemes"
                className="w-full sm:w-auto bg-[#FFD0CA] hover:bg-[#fca59d] text-[#4A2525] px-6 py-3 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2"
              >
                <Search className="w-4 h-4" />
                <span>{t('about.exploreCta', 'Explore Schemes')}</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
};

const CompassIcon: React.FC = () => (
  <span className="inline-flex items-center justify-center">
    <span className="w-3.5 h-3.5 rounded-full border-2 border-[#765E59] relative">
      <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-1 h-1 bg-[#765E59] rounded-full" />
    </span>
  </span>
);