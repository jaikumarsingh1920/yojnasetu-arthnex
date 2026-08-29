import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Search,
  Sparkles,
  Calculator,
  ShieldCheck,
  Building2,
  FileCheck2,
  ArrowRight,
  Award,
  Lock,
  FileText
} from 'lucide-react';

export const Home: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="space-y-12 pb-12">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-gov-blue via-gov-navy to-slate-900 text-white pt-12 pb-16 px-4 sm:px-6 lg:px-8 border-b-4 border-gov-saffron relative overflow-hidden">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 bg-gov-saffron/20 border border-gov-saffron/40 px-3.5 py-1 rounded-full text-gov-saffron text-xs font-bold tracking-wide">
              <ShieldCheck className="w-4 h-4" />
              Government Schemes • Loans • Benefits
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight">
              {t('home.heroTitle')}
            </h1>

            <p className="text-slate-300 text-base sm:text-lg leading-relaxed font-normal max-w-2xl">
              {t('home.heroSubtitle')}
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap gap-3 pt-2">
              <Link
                to="/recommendations"
                className="bg-gov-saffron hover:bg-orange-600 text-white px-6 py-3.5 rounded-xl font-bold text-sm shadow-lg hover:shadow-orange-500/20 transition flex items-center gap-2"
              >
                <Sparkles className="w-4.5 h-4.5 text-amber-200" />
                Find Schemes for Me
              </Link>

              <Link
                to="/schemes"
                className="bg-slate-800/90 hover:bg-slate-700 text-white border border-slate-600 px-6 py-3.5 rounded-xl font-semibold text-sm transition flex items-center gap-2"
              >
                <Search className="w-4.5 h-4.5 text-sky-400" />
                Browse All Schemes
              </Link>
            </div>
          </div>

          {/* Banner Stats Card */}
          <div className="lg:col-span-5 bg-white/10 backdrop-blur-md p-6 rounded-2xl border border-white/20 shadow-xl space-y-4 text-white">
            <h3 className="text-xs font-bold uppercase tracking-wider text-amber-300 flex items-center gap-2">
              <Award className="w-4 h-4" />
              Government Welfare Portal
            </h3>

            <div className="grid grid-cols-2 gap-4 pt-2">
              <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-700">
                <span className="text-3xl font-extrabold text-white block">56</span>
                <span className="text-xs text-slate-300 font-medium">Verified Schemes</span>
              </div>

              <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-700">
                <span className="text-3xl font-extrabold text-gov-saffron block">100%</span>
                <span className="text-xs text-slate-300 font-medium">Government-Verified Information</span>
              </div>

              <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-700">
                <span className="text-3xl font-extrabold text-emerald-400 block">Clear</span>
                <span className="text-xs text-slate-300 font-medium">Eligibility Guidance</span>
              </div>

              <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-700">
                <span className="text-3xl font-extrabold text-sky-400 block">Secure</span>
                <span className="text-xs text-slate-300 font-medium">Transparent & Trusted</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Pillar Cards */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-10 space-y-2">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Key Platform Services</h2>
          <p className="text-sm text-slate-600">Everything you need to discover schemes, check eligibility, and plan your loan in one place.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition space-y-4">
            <div className="w-12 h-12 bg-sky-100 rounded-xl flex items-center justify-center text-sky-700">
              <Search className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Find Government Schemes</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Explore government schemes based on your needs, location, work, income and other eligibility factors.
            </p>
            <Link to="/schemes" className="text-xs font-bold text-sky-700 flex items-center gap-1 hover:underline pt-2">
              Explore Schemes <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition space-y-4">
            <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center text-gov-saffron">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Get Personalized Recommendations</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Answer a few simple questions and discover schemes that best match your situation.
            </p>
            <Link to="/recommendations" className="text-xs font-bold text-gov-saffron flex items-center gap-1 hover:underline pt-2">
              Get Recommendations <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition space-y-4">
            <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center text-emerald-700">
              <Calculator className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Plan Your Loan</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Estimate your monthly EMI, repayment amount, loan contribution and other financing details.
            </p>
            <Link to="/calculator" className="text-xs font-bold text-emerald-700 flex items-center gap-1 hover:underline pt-2">
              Use Loan Calculator <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Target Beneficiary & Channelizing Agencies Banner */}
      <section className="bg-slate-100 py-12 border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch">
          <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-6">
            <div className="space-y-3">
              <span className="text-xs font-bold text-sky-700 uppercase tracking-wider bg-sky-50 px-2.5 py-1 rounded border border-sky-200">
                FOR CITIZENS & ENTREPRENEURS
              </span>
              <h3 className="text-2xl font-extrabold text-slate-900 pt-1">Support That Fits Your Needs</h3>
              <ul className="space-y-3 text-xs text-slate-700 pt-2">
                <li className="flex items-center gap-2.5">
                  <FileCheck2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  Find schemes you may be eligible for
                </li>
                <li className="flex items-center gap-2.5">
                  <FileCheck2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  Understand eligibility and required documents
                </li>
                <li className="flex items-center gap-2.5">
                  <FileCheck2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  Apply and track your application online
                </li>
                <li className="flex items-center gap-2.5">
                  <FileCheck2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  Get clear information before making a decision
                </li>
              </ul>
            </div>
            <div>
              <Link to="/recommendations" className="bg-gov-blue hover:bg-gov-navy text-white px-6 py-3 rounded-xl text-xs font-bold shadow transition inline-flex items-center gap-2">
                Get Started <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-6">
            <div className="space-y-3">
              <span className="text-xs font-bold text-amber-700 uppercase tracking-wider bg-amber-50 px-2.5 py-1 rounded border border-amber-200">
                FOR GOVERNMENT & CHANNEL PARTNERS
              </span>
              <h3 className="text-2xl font-extrabold text-slate-900 pt-1">Review Applications With Confidence</h3>
              <ul className="space-y-3 text-xs text-slate-700 pt-2">
                <li className="flex items-center gap-2.5">
                  <Building2 className="w-4 h-4 text-amber-600 shrink-0" />
                  Review submitted applications efficiently
                </li>
                <li className="flex items-center gap-2.5">
                  <Building2 className="w-4 h-4 text-amber-600 shrink-0" />
                  Verify documents and applicant information
                </li>
                <li className="flex items-center gap-2.5">
                  <Building2 className="w-4 h-4 text-amber-600 shrink-0" />
                  Request corrections when needed
                </li>
                <li className="flex items-center gap-2.5">
                  <Building2 className="w-4 h-4 text-amber-600 shrink-0" />
                  Approve or reject applications according to your authority
                </li>
              </ul>
            </div>
            <div>
              <Link to="/login" className="bg-gov-navy hover:bg-slate-900 text-white px-6 py-3 rounded-xl text-xs font-bold shadow transition inline-flex items-center gap-2">
                Partner Sign In <Lock className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
