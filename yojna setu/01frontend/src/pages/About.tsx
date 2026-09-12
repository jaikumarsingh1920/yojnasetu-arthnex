import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  Database,
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
  Building2,
  BadgeCheck,
  Globe2,
  LockKeyhole,
  CircleCheck,
  Shield,
} from 'lucide-react';

export const About: React.FC = () => {
  return (
    <div className="space-y-10 sm:space-y-14 lg:space-y-16 pb-16 bg-[#fef9f3] min-h-screen">

      {/* ============================================================
          1. ABOUT HERO
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 sm:pt-8">

        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#861823] via-[#521827] to-[#071b2b] text-white border border-[#a52a38]/60 shadow-xl">

          {/* Background Glows */}
          <div className="absolute -right-24 -top-24 w-80 h-80 bg-gov-saffron/20 rounded-full blur-3xl pointer-events-none" />

          <div className="absolute -left-24 -bottom-24 w-80 h-80 bg-[#8b1e2d]/30 rounded-full blur-3xl pointer-events-none" />

          <div className="absolute right-20 bottom-0 w-56 h-56 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 px-5 py-8 sm:px-8 sm:py-12 lg:px-12 lg:py-14">

            <div className="max-w-4xl">

              {/* Badge */}
              <div className="inline-flex items-center gap-2 bg-white/10 text-[#ffb347] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border border-[#ff9d2e]/30 mb-5">

                <Landmark className="w-3.5 h-3.5" />

                <span>
                  Government Citizen Platform
                </span>

              </div>

              {/* Heading */}
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight leading-tight">
                About YojnaSetu
              </h1>

              {/* Description */}
              <p className="mt-4 text-sm sm:text-base lg:text-lg text-slate-200 leading-relaxed max-w-3xl">
                YojnaSetu is a national civic-tech welfare guidance platform
                designed to bridge the gap between Indian citizens and
                government welfare, credit, and subsidy programs.
              </p>

              {/* Trust Chips */}
              <div className="flex flex-wrap gap-2.5 mt-7">

                <div className="inline-flex items-center gap-2 bg-white/10 border border-white/15 px-3.5 py-2 rounded-xl text-xs sm:text-sm">
                  <BadgeCheck className="w-4 h-4 text-emerald-400" />
                  <span>Verified Government Schemes</span>
                </div>

                <div className="inline-flex items-center gap-2 bg-white/10 border border-white/15 px-3.5 py-2 rounded-xl text-xs sm:text-sm">
                  <ShieldCheck className="w-4 h-4 text-sky-300" />
                  <span>Rule-Based Eligibility</span>
                </div>

                <div className="inline-flex items-center gap-2 bg-white/10 border border-white/15 px-3.5 py-2 rounded-xl text-xs sm:text-sm">
                  <Languages className="w-4 h-4 text-[#ffb347]" />
                  <span>Multilingual Access</span>
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
          <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200/90 shadow-xs p-5 sm:p-8">

            <div className="flex items-start gap-3 mb-5">

              <div className="w-11 h-11 rounded-xl bg-[#861823]/10 border border-[#861823]/10 flex items-center justify-center shrink-0">
                <Users className="w-5 h-5 text-[#861823]" />
              </div>

              <div>
                <div className="text-[11px] sm:text-xs font-bold uppercase tracking-wider text-gov-saffron mb-1">
                  Who We Are
                </div>

                <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
                  Connecting Citizens With Welfare Opportunities
                </h2>
              </div>

            </div>

            <div className="space-y-4 text-sm text-slate-600 leading-relaxed">

              <p>
                Government welfare schemes can provide valuable support in
                areas such as entrepreneurship, agriculture, education,
                healthcare, social security, and financial assistance.
              </p>

              <p>
                However, citizens often have to navigate multiple portals,
                eligibility conditions, application procedures, and official
                guidelines to identify the schemes relevant to them.
              </p>

              <p>
                YojnaSetu brings this discovery journey together through a
                citizen-focused interface that helps users explore schemes,
                understand eligibility requirements, calculate financial
                benefits, and find official assistance channels.
              </p>

            </div>

          </div>


          {/* Mission Card */}
          <div className="bg-gradient-to-br from-[#861823] via-[#5b1726] to-[#241626] rounded-3xl p-6 sm:p-7 text-white shadow-lg border border-[#a52a38]/60 relative overflow-hidden">

            <div className="absolute -right-16 -top-16 w-44 h-44 bg-gov-saffron/15 rounded-full blur-3xl pointer-events-none" />

            <div className="relative z-10">

              <div className="w-11 h-11 rounded-xl bg-white/10 border border-white/15 flex items-center justify-center mb-5">
                <HeartHandshake className="w-5 h-5 text-[#ffb347]" />
              </div>

              <p className="text-[11px] font-bold uppercase tracking-wider text-[#ffb347]">
                Our Mission
              </p>

              <h3 className="text-xl sm:text-2xl font-extrabold mt-2 leading-tight">
                Making welfare discovery simpler for every citizen.
              </h3>

              <p className="text-xs sm:text-sm text-slate-200 leading-relaxed mt-4">
                One platform to discover relevant schemes, understand
                eligibility, and reach official channels with confidence.
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

          <div className="inline-flex items-center gap-1.5 bg-amber-50 text-amber-800 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border border-amber-200">

            <Sparkles className="w-3.5 h-3.5 text-gov-saffron" />

            <span>
              Platform Capabilities
            </span>

          </div>

          <h2 className="text-xl sm:text-3xl font-extrabold text-slate-900">
            Everything You Need to Navigate Welfare Schemes
          </h2>

          <p className="text-xs sm:text-sm text-slate-500">
            Simple tools and guidance designed around the needs of citizens.
          </p>

        </div>


        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">

          {/* Scheme Discovery */}
          <div className="bg-white p-5 sm:p-6 rounded-2xl border border-slate-200/90 shadow-xs hover:shadow-md hover:-translate-y-0.5 transition duration-200">

            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-blue-50 border border-blue-200 text-blue-600 mb-4">
              <Search className="w-5 h-5" />
            </div>

            <h3 className="text-sm sm:text-base font-extrabold text-slate-900">
              Scheme Discovery
            </h3>

            <p className="text-xs text-slate-600 leading-relaxed mt-2">
              Search and explore government schemes using keywords,
              categories, ministries, and welfare focus areas.
            </p>

          </div>


          {/* Smart Matching */}
          <div className="bg-white p-5 sm:p-6 rounded-2xl border border-slate-200/90 shadow-xs hover:shadow-md hover:-translate-y-0.5 transition duration-200">

            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-amber-50 border border-amber-200 text-amber-600 mb-4">
              <Sparkles className="w-5 h-5" />
            </div>

            <h3 className="text-sm sm:text-base font-extrabold text-slate-900">
              Smart Scheme Matching
            </h3>

            <p className="text-xs text-slate-600 leading-relaxed mt-2">
              Discover schemes that may match a citizen's demographic,
              financial, and occupational profile.
            </p>

          </div>


          {/* Eligibility */}
          <div className="bg-white p-5 sm:p-6 rounded-2xl border border-slate-200/90 shadow-xs hover:shadow-md hover:-translate-y-0.5 transition duration-200">

            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-emerald-50 border border-emerald-200 text-emerald-600 mb-4">
              <ShieldCheck className="w-5 h-5" />
            </div>

            <h3 className="text-sm sm:text-base font-extrabold text-slate-900">
              Eligibility Guidance
            </h3>

            <p className="text-xs text-slate-600 leading-relaxed mt-2">
              Understand eligibility requirements through explicit,
              rule-based scheme conditions.
            </p>

          </div>


          {/* Financial Calculator */}
          <div className="bg-white p-5 sm:p-6 rounded-2xl border border-slate-200/90 shadow-xs hover:shadow-md hover:-translate-y-0.5 transition duration-200">

            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-orange-50 border border-orange-200 text-orange-600 mb-4">
              <Calculator className="w-5 h-5" />
            </div>

            <h3 className="text-sm sm:text-base font-extrabold text-slate-900">
              Financial Calculator
            </h3>

            <p className="text-xs text-slate-600 leading-relaxed mt-2">
              Estimate loan EMIs, interest burden, payable amounts, and
              applicable subsidy benefits.
            </p>

          </div>


          {/* Nearby Partners */}
          <div className="bg-white p-5 sm:p-6 rounded-2xl border border-slate-200/90 shadow-xs hover:shadow-md hover:-translate-y-0.5 transition duration-200">

            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-indigo-50 border border-indigo-200 text-indigo-600 mb-4">
              <MapPin className="w-5 h-5" />
            </div>

            <h3 className="text-sm sm:text-base font-extrabold text-slate-900">
              Nearby Assistance
            </h3>

            <p className="text-xs text-slate-600 leading-relaxed mt-2">
              Locate authorized banks, channel partners, and assistance
              centres supporting welfare schemes.
            </p>

          </div>


          {/* Multilingual */}
          <div className="bg-white p-5 sm:p-6 rounded-2xl border border-slate-200/90 shadow-xs hover:shadow-md hover:-translate-y-0.5 transition duration-200">

            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-sky-50 border border-sky-200 text-sky-600 mb-4">
              <Globe2 className="w-5 h-5" />
            </div>

            <h3 className="text-sm sm:text-base font-extrabold text-slate-900">
              Multilingual Access
            </h3>

            <p className="text-xs text-slate-600 leading-relaxed mt-2">
              Access welfare information through multilingual support designed
              to make the platform easier to use across India.
            </p>

          </div>

        </div>

      </section>


      {/* ============================================================
          4. TRUST & TRANSPARENCY
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="bg-white rounded-3xl border border-slate-200/90 shadow-xs overflow-hidden">

          <div className="grid grid-cols-1 lg:grid-cols-2">

            {/* Left */}
            <div className="p-6 sm:p-8 lg:p-10">

              <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded border border-emerald-200 mb-4">

                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />

                <span>
                  Trust & Transparency
                </span>

              </div>

              <h2 className="text-xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Designed Around Citizen Trust
              </h2>

              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed mt-3 max-w-xl">
                YojnaSetu focuses on clear eligibility guidance, official
                scheme information, transparent routes, and a simple citizen
                experience.
              </p>

              <div className="space-y-3 mt-6">

                <div className="flex items-start gap-3">

                  <div className="w-8 h-8 rounded-lg bg-sky-50 border border-sky-200 flex items-center justify-center shrink-0">
                    <FileCheck2 className="w-4 h-4 text-sky-600" />
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-slate-900">
                      Explicit Eligibility Rules
                    </h4>

                    <p className="text-xs text-slate-500 mt-0.5">
                      Eligibility guidance is based on defined scheme
                      conditions rather than arbitrary recommendations.
                    </p>
                  </div>

                </div>


                <div className="flex items-start gap-3">

                  <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center shrink-0">
                    <CircleCheck className="w-4 h-4 text-emerald-600" />
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-slate-900">
                      Official Scheme Information
                    </h4>

                    <p className="text-xs text-slate-500 mt-0.5">
                      The platform is built around official scheme details
                      and government sources.
                    </p>
                  </div>

                </div>


                <div className="flex items-start gap-3">

                  <div className="w-8 h-8 rounded-lg bg-amber-50 border border-amber-200 flex items-center justify-center shrink-0">
                    <LockKeyhole className="w-4 h-4 text-amber-600" />
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-slate-900">
                      Privacy-Conscious Experience
                    </h4>

                    <p className="text-xs text-slate-500 mt-0.5">
                      The platform is designed to minimize unnecessary
                      document and personal-data handling.
                    </p>
                  </div>

                </div>

              </div>

            </div>


            {/* Right Dark Panel */}
            <div className="bg-gradient-to-br from-[#071b2b] via-[#0d2234] to-[#321625] p-6 sm:p-8 lg:p-10 text-white relative overflow-hidden">

              <div className="absolute -right-20 -top-20 w-64 h-64 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

              <div className="absolute -left-20 -bottom-20 w-64 h-64 bg-[#861823]/30 rounded-full blur-3xl pointer-events-none" />

              <div className="relative z-10">

                <div className="w-12 h-12 rounded-xl bg-white/10 border border-white/15 flex items-center justify-center mb-5">
                  <Shield className="w-6 h-6 text-sky-300" />
                </div>

                <h3 className="text-xl sm:text-2xl font-extrabold">
                  Clear. Guided. Citizen-Focused.
                </h3>

                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mt-3">
                  From discovering a scheme to finding the right assistance
                  channel, YojnaSetu aims to make every step easier to
                  understand.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-6">

                  <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-3 py-2.5 rounded-xl text-xs">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    Verified information
                  </div>

                  <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-3 py-2.5 rounded-xl text-xs">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    Rule-based guidance
                  </div>

                  <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-3 py-2.5 rounded-xl text-xs">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    Official routes
                  </div>

                  <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-3 py-2.5 rounded-xl text-xs">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    Citizen-first design
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

          <div className="inline-flex items-center gap-1.5 bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border border-slate-200">

            <CompassIcon />

            <span>
              Citizen Journey
            </span>

          </div>

          <h2 className="text-xl sm:text-3xl font-extrabold text-slate-900">
            From Discovery to Action
          </h2>

          <p className="text-xs sm:text-sm text-slate-500">
            A straightforward journey to help citizens find and understand
            relevant welfare opportunities.
          </p>

        </div>


        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

          {/* Step 1 */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs">

            <div className="flex items-center justify-between mb-4">

              <span className="text-xl font-black text-slate-200">
                01
              </span>

              <div className="w-9 h-9 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center">
                <Search className="w-4 h-4 text-amber-600" />
              </div>

            </div>

            <h3 className="text-sm font-bold text-slate-900">
              Discover
            </h3>

            <p className="text-xs text-slate-600 leading-relaxed mt-2">
              Search or browse government schemes based on your area of
              interest.
            </p>

          </div>


          {/* Step 2 */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs">

            <div className="flex items-center justify-between mb-4">

              <span className="text-xl font-black text-slate-200">
                02
              </span>

              <div className="w-9 h-9 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center">
                <ShieldCheck className="w-4 h-4 text-blue-600" />
              </div>

            </div>

            <h3 className="text-sm font-bold text-slate-900">
              Check Eligibility
            </h3>

            <p className="text-xs text-slate-600 leading-relaxed mt-2">
              Understand whether the scheme conditions align with your
              profile.
            </p>

          </div>


          {/* Step 3 */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs">

            <div className="flex items-center justify-between mb-4">

              <span className="text-xl font-black text-slate-200">
                03
              </span>

              <div className="w-9 h-9 rounded-xl bg-orange-50 border border-orange-200 flex items-center justify-center">
                <FileCheck2 className="w-4 h-4 text-orange-600" />
              </div>

            </div>

            <h3 className="text-sm font-bold text-slate-900">
              Understand Benefits
            </h3>

            <p className="text-xs text-slate-600 leading-relaxed mt-2">
              Review scheme benefits, requirements, and important details in
              one place.
            </p>

          </div>


          {/* Step 4 */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs">

            <div className="flex items-center justify-between mb-4">

              <span className="text-xl font-black text-slate-200">
                04
              </span>

              <div className="w-9 h-9 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center">
                <MapPin className="w-4 h-4 text-emerald-600" />
              </div>

            </div>

            <h3 className="text-sm font-bold text-slate-900">
              Reach the Official Route
            </h3>

            <p className="text-xs text-slate-600 leading-relaxed mt-2">
              Find official application routes and nearby assistance
              partners when required.
            </p>

          </div>

        </div>

      </section>


      {/* ============================================================
          6. PLATFORM PRINCIPLES
      ============================================================ */}

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="bg-gradient-to-br from-[#861823] via-[#4b1727] to-[#071b2b] rounded-3xl p-6 sm:p-8 lg:p-10 text-white border border-[#a52a38]/60 shadow-xl relative overflow-hidden">

          <div className="absolute -right-20 -top-20 w-72 h-72 bg-gov-saffron/15 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10">

            <div className="max-w-3xl mb-7">

              <div className="inline-flex items-center gap-1.5 bg-white/10 text-[#ffb347] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border border-[#ff9d2e]/30">

                <ShieldCheck className="w-3.5 h-3.5" />

                <span>
                  Our Principles
                </span>

              </div>

              <h2 className="text-xl sm:text-3xl font-extrabold tracking-tight mt-3">
                Built for Simplicity, Transparency & Access
              </h2>

              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mt-2">
                The platform experience is centered around making welfare
                information easier to discover and understand.
              </p>

            </div>


            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">

              <div className="bg-white/5 border border-white/10 rounded-2xl p-4">

                <ShieldCheck className="w-5 h-5 text-sky-300 mb-3" />

                <h3 className="text-sm font-bold">
                  Trust
                </h3>

                <p className="text-xs text-slate-300 leading-relaxed mt-1.5">
                  Clear information and transparent guidance.
                </p>

              </div>


              <div className="bg-white/5 border border-white/10 rounded-2xl p-4">

                <Users className="w-5 h-5 text-emerald-400 mb-3" />

                <h3 className="text-sm font-bold">
                  Accessibility
                </h3>

                <p className="text-xs text-slate-300 leading-relaxed mt-1.5">
                  Designed around diverse citizen needs.
                </p>

              </div>


              <div className="bg-white/5 border border-white/10 rounded-2xl p-4">

                <Languages className="w-5 h-5 text-[#ffb347] mb-3" />

                <h3 className="text-sm font-bold">
                  Inclusion
                </h3>

                <p className="text-xs text-slate-300 leading-relaxed mt-1.5">
                  Multilingual access for wider reach.
                </p>

              </div>


              <div className="bg-white/5 border border-white/10 rounded-2xl p-4">

                <FileCheck2 className="w-5 h-5 text-orange-300 mb-3" />

                <h3 className="text-sm font-bold">
                  Clarity
                </h3>

                <p className="text-xs text-slate-300 leading-relaxed mt-1.5">
                  Simple presentation of complex scheme information.
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

        <div className="bg-white rounded-3xl border border-slate-200/90 shadow-xs p-6 sm:p-8 lg:p-10">

          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">

            <div className="max-w-2xl">

              <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-gov-saffron bg-amber-50 px-2.5 py-1 rounded border border-amber-200 mb-3">

                <Sparkles className="w-3.5 h-3.5" />

                <span>
                  Get Started
                </span>

              </div>

              <h2 className="text-xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Find Government Schemes That Fit You
              </h2>

              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed mt-2">
                Explore schemes, check eligibility, and discover relevant
                government welfare opportunities.
              </p>

            </div>


            <div className="flex flex-col sm:flex-row gap-2.5 w-full lg:w-auto">

              <Link
                to="/recommendations"
                className="w-full sm:w-auto bg-gov-saffron hover:bg-orange-600 text-white px-6 py-3 rounded-xl font-extrabold text-sm shadow-lg hover:shadow-orange-500/30 transition-all flex items-center justify-center gap-2 hover:-translate-y-0.5"
              >
                <Sparkles className="w-4 h-4" />

                <span>
                  Find Matching Schemes
                </span>

                <ArrowRight className="w-4 h-4" />
              </Link>


              <Link
                to="/schemes"
                className="w-full sm:w-auto bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2"
              >
                <Search className="w-4 h-4" />

                <span>
                  Explore Schemes
                </span>

              </Link>

            </div>

          </div>

        </div>

      </section>

    </div>
  );
};


/* ================================================================
   SMALL REUSABLE ICON
   Keeps the JSX clean and avoids another dependency.
================================================================ */

const CompassIcon: React.FC = () => (
  <span className="inline-flex items-center justify-center">
    <span className="w-3.5 h-3.5 rounded-full border-2 border-slate-500 relative">
      <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-1 h-1 bg-slate-500 rounded-full" />
    </span>
  </span>
);