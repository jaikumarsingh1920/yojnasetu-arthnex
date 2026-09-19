import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  BookOpen,
  ShieldCheck,
  Calculator,
  Landmark,
  Phone,
  FileCheck2,
  BadgeCheck,
  IndianRupee,
  PiggyBank,
  CreditCard,
  Wallet,
  Lightbulb,
  ExternalLink,
} from 'lucide-react';

const Resources: React.FC = () => {
  const resources = [
    {
      icon: ShieldCheck,
      iconBg: 'bg-[#FFD0CA]',
      iconColor: 'text-[#4A2525]',
      title: 'National Gazette Verification Standard',
      description:
        'All 90 welfare schemes indexed on YojnaSetu are validated against official Gazette of India notifications, statutory ministry guidelines, and RBI/NABARD master circulars.',
      tag: 'Scheme Verification',
      tagClass: 'bg-[#FFF4EC] text-[#4A2525] border-[#FFD0CA]',
    },
    {
      icon: Calculator,
      iconBg: 'bg-[#FFD0CA]',
      iconColor: 'text-[#4A2525]',
      title: 'Financial Calculator Methodology',
      description:
        'Calculators use standardized reducing balance EMI calculations and accurate category-specific margin money / back-ended capital subsidy formulas.',
      tag: 'Financial Tools',
      tagClass: 'bg-[#FFF4EC] text-[#4A2525] border-[#FFD0CA]',
    },
    {
      icon: Phone,
      iconBg: 'bg-[#FFD0CA]',
      iconColor: 'text-[#4A2525]',
      title: 'Grievance Redressal & Helpdesk',
      description:
        'Toll-Free National Helpline: 1800–11–2026 (9:00 AM – 6:00 PM IST, Monday to Saturday).',
      tag: 'Citizen Support',
      tagClass: 'bg-[#FFF4EC] text-[#4A2525] border-[#FFD0CA]',
    },
  ];

  const literacyArticles = [
    {
      icon: IndianRupee,
      category: 'LOANS & EMI',
      title: 'Understanding EMI Before Taking a Loan',
      description:
        'Learn how principal, interest rate, tenure and monthly EMI work together before choosing a credit scheme.',
      points: [
        'What an EMI actually includes',
        'Impact of loan tenure on total interest',
        'Reducing balance vs. flat-rate calculations',
      ],
    },
    {
      icon: PiggyBank,
      category: 'SAVINGS',
      title: 'Build a Strong Financial Safety Net',
      description:
        'Simple principles for managing income, savings and emergency funds while planning for long-term goals.',
      points: [
        'Why emergency savings matter',
        'Separating needs from wants',
        'Setting realistic savings goals',
      ],
    },
    {
      icon: CreditCard,
      category: 'CREDIT',
      title: 'Know Your Credit Before Borrowing',
      description:
        'Understand responsible borrowing, repayment discipline and the basics of maintaining a healthy credit profile.',
      points: [
        'Borrow only what you can repay',
        'Importance of timely repayment',
        'Understanding loan obligations',
      ],
    },
    {
      icon: Wallet,
      category: 'GOVERNMENT SCHEMES',
      title: 'How Subsidy & Concessional Loans Work',
      description:
        'Understand the difference between a subsidy, a concessional loan, margin money support and regular credit.',
      points: [
        'Subsidy vs. loan explained',
        'Margin money basics',
        'Why scheme-specific rules matter',
      ],
    },
    {
      icon: Lightbulb,
      category: 'FINANCIAL BASICS',
      title: 'Read the Important Numbers First',
      description:
        'Before applying for financial assistance, know which numbers and conditions deserve your attention.',
      points: [
        'Maximum loan amount',
        'Interest and repayment period',
        'Eligibility and income limits',
      ],
    },
    {
      icon: FileCheck2,
      category: 'APPLICATION GUIDANCE',
      title: 'Prepare Before You Apply',
      description:
        'A simple checklist to help citizens understand scheme requirements and avoid unnecessary application delays.',
      points: [
        'Check eligibility first',
        'Review required documents',
        'Use the correct application channel',
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-[#FFFBF0] text-[#3B2522]">

      {/* HERO */}
      <section className="relative overflow-hidden bg-gradient-to-br from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white">
        <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full bg-[#F7AE56]/15 blur-3xl" />
        <div className="absolute -bottom-32 -left-20 w-96 h-96 rounded-full bg-[#EA717B]/10 blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-5 sm:px-8 lg:px-10 py-16 sm:py-20 lg:py-24">
          <div className="max-w-4xl">

            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/15 text-xs font-bold tracking-wide mb-5">
              <BookOpen className="w-4 h-4 text-[#F7AE56]" />
              <span className="text-[#FFFBF0]">CITIZEN RESOURCES</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
              Resources &{' '}
              <span className="text-[#F7AE56]">Guidelines</span>
            </h1>

            <p className="mt-5 max-w-3xl text-sm sm:text-base lg:text-lg text-[#FFFBF0]/80 leading-relaxed">
              Trusted guidance, financial tools and practical resources to help
              you understand government welfare schemes and make informed
              financial decisions.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href="#official-resources"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-[#EA717B] text-white text-sm font-extrabold hover:bg-[#d65f69] transition shadow-warm-xs"
              >
                Explore Resources
                <ArrowRight className="w-4 h-4" />
              </a>

              <a
                href="#financial-literacy"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white/10 border border-white/20 text-[#FFFBF0] text-sm font-bold hover:bg-white/15 transition"
              >
                Financial Literacy
              </a>
            </div>

          </div>
        </div>
      </section>

      {/* TRUST STRIP */}
      <section className="border-b border-[#E8D8D2] bg-white">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 lg:px-10 py-5">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">

            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-[#FFF4EC] text-[#4A2525]">
                <BadgeCheck className="w-5 h-5 text-[#EA717B]" />
              </div>
              <div>
                <p className="text-sm font-extrabold text-[#3B2522]">
                  Verified Information
                </p>
                <p className="text-xs text-[#765E59]">
                  Government guidelines & sources
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-[#FFF4EC] text-[#4A2525]">
                <Calculator className="w-5 h-5 text-[#F7AE56]" />
              </div>
              <div>
                <p className="text-sm font-extrabold text-[#3B2522]">
                  Practical Financial Tools
                </p>
                <p className="text-xs text-[#765E59]">
                  Understand your numbers
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-[#FFF4EC] text-[#4A2525]">
                <Landmark className="w-5 h-5 text-[#4A2525]" />
              </div>
              <div>
                <p className="text-sm font-extrabold text-[#3B2522]">
                  Citizen First
                </p>
                <p className="text-xs text-[#765E59]">
                  Simple and accessible guidance
                </p>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* OFFICIAL RESOURCES */}
      <section
        id="official-resources"
        className="max-w-7xl mx-auto px-5 sm:px-8 lg:px-10 py-14 sm:py-18"
      >
        <div className="max-w-3xl mb-9">
          <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[#EA717B]">
            Official Guidance
          </p>

          <h2 className="mt-2 text-3xl sm:text-4xl font-extrabold text-[#3B2522]">
            Citizen Welfare Resources
          </h2>

          <p className="mt-3 text-sm sm:text-base text-[#765E59] leading-relaxed">
            Key standards, methodologies and support information used to make
            YojnaSetu more transparent and useful for citizens.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-5">

          {resources.map((resource) => {
            const Icon = resource.icon;

            return (
              <article
                key={resource.title}
                className="group bg-white border border-[#E8D8D2] rounded-2xl p-6 shadow-warm-xs hover:shadow-warm-md hover:border-[#FFD0CA] transition-all duration-200"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className={`p-3 rounded-xl ${resource.iconBg}`}>
                    <Icon className={`w-6 h-6 ${resource.iconColor}`} />
                  </div>

                  <span
                    className={`text-[10px] font-extrabold uppercase tracking-wide px-2.5 py-1 rounded-full border ${resource.tagClass}`}
                  >
                    {resource.tag}
                  </span>
                </div>

                <h3 className="mt-5 text-lg font-extrabold text-[#3B2522] leading-snug">
                  {resource.title}
                </h3>

                <p className="mt-3 text-sm text-[#765E59] leading-relaxed">
                  {resource.description}
                </p>

                <div className="mt-6 pt-4 border-t border-[#E8D8D2]/60 flex items-center gap-2 text-xs font-bold text-[#EA717B]">
                  <CheckCircleIcon />
                  YojnaSetu Resource
                </div>
              </article>
            );
          })}

        </div>
      </section>

      {/* FINANCIAL LITERACY */}
      <section
        id="financial-literacy"
        className="bg-[#FFF4EC]/60 border-y border-[#E8D8D2]"
      >
        <div className="max-w-7xl mx-auto px-5 sm:px-8 lg:px-10 py-14 sm:py-18">

          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5 mb-9">
            <div className="max-w-3xl">
              <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[#EA717B]">
                Learn Before You Borrow
              </p>

              <h2 className="mt-2 text-3xl sm:text-4xl font-extrabold text-[#3B2522]">
                Financial Literacy
              </h2>

              <p className="mt-3 text-sm sm:text-base text-[#765E59] leading-relaxed">
                Simple guides to help citizens understand loans, EMIs,
                subsidies, savings and responsible financial planning.
              </p>
            </div>

            <Link
              to="/calculator"
              className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-[#EA717B] text-white text-sm font-bold hover:bg-[#d65f69] transition shadow-warm-xs shrink-0"
            >
              Try Financial Calculator
              <Calculator className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">

            {literacyArticles.map((article) => {
              const Icon = article.icon;

              return (
                <article
                  key={article.title}
                  className="rounded-2xl border border-[#E8D8D2] bg-white p-5 shadow-warm-xs hover:border-[#FFD0CA] hover:shadow-warm-sm transition"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="p-2.5 rounded-xl bg-[#FFD0CA] text-[#4A2525]">
                      <Icon className="w-5 h-5" />
                    </div>

                    <span className="text-[10px] font-extrabold tracking-wider text-[#EA717B]">
                      {article.category}
                    </span>
                  </div>

                  <h3 className="mt-5 text-lg font-extrabold text-[#3B2522]">
                    {article.title}
                  </h3>

                  <p className="mt-2 text-sm text-[#765E59] leading-relaxed">
                    {article.description}
                  </p>

                  <div className="mt-4 space-y-2">
                    {article.points.map((point) => (
                      <div
                        key={point}
                        className="flex items-start gap-2 text-xs text-[#765E59]"
                      >
                        <CheckCircleIcon />
                        <span>{point}</span>
                      </div>
                    ))}
                  </div>

                  <button
                    type="button"
                    className="mt-5 inline-flex items-center gap-2 text-xs font-extrabold text-[#EA717B] hover:gap-3 transition-all"
                  >
                    Read Guide
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </article>
              );
            })}

          </div>
        </div>
      </section>

      {/* HOW TO USE YOJNASETU */}
      <section className="max-w-7xl mx-auto px-5 sm:px-8 lg:px-10 py-14">

        <div className="rounded-3xl overflow-hidden bg-gradient-to-br from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white shadow-warm-md border border-[#E8D8D2]/20">

          <div className="grid lg:grid-cols-2 gap-8 items-center p-7 sm:p-10 lg:p-12">

            <div>
              <div className="inline-flex items-center gap-2 text-[#F7AE56] text-xs font-extrabold uppercase tracking-wider">
                <BookOpen className="w-4 h-4" />
                Make Better Decisions
              </div>

              <h2 className="mt-3 text-3xl sm:text-4xl font-extrabold">
                Use the right resource at the right stage.
              </h2>

              <p className="mt-4 text-sm sm:text-base text-[#FFFBF0]/80 leading-relaxed max-w-xl">
                Start by discovering suitable schemes, understand your
                eligibility, use the financial calculator, and then review the
                application guidance before proceeding.
              </p>

              <div className="mt-7 flex flex-wrap gap-3">
                <Link
                  to="/schemes"
                  className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-[#EA717B] text-white text-sm font-extrabold hover:bg-[#d65f69] transition shadow-warm-xs"
                >
                  Explore Schemes
                  <ArrowRight className="w-4 h-4" />
                </Link>

                <Link
                  to="/recommendations"
                  className="inline-flex items-center gap-2 px-5 py-3 rounded-xl border border-white/20 bg-white/10 text-[#FFFBF0] text-sm font-bold hover:bg-white/15 transition"
                >
                  Find Matching Schemes
                  <ExternalLink className="w-4 h-4" />
                </Link>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">

              <JourneyCard
                number="01"
                title="Discover"
                description="Find schemes relevant to your needs."
              />

              <JourneyCard
                number="02"
                title="Understand"
                description="Check eligibility and scheme conditions."
              />

              <JourneyCard
                number="03"
                title="Calculate"
                description="Estimate EMI, subsidy and repayment."
              />

              <JourneyCard
                number="04"
                title="Apply"
                description="Follow the correct application route."
              />

            </div>

          </div>
        </div>
      </section>

      {/* FOOTER NOTE */}
      <section className="pb-14 px-5">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 text-xs text-[#765E59]">
            <ShieldCheck className="w-4 h-4 text-[#2D6A4F]" />
            Always verify scheme-specific terms with the concerned official
            authority before applying.
          </div>
        </div>
      </section>

    </div>
  );
};

const CheckCircleIcon = () => (
  <span className="mt-0.5 inline-flex shrink-0 w-4 h-4 rounded-full bg-[#2D6A4F]/15 text-[#2D6A4F] items-center justify-center">
    <span className="text-[9px] font-black">✓</span>
  </span>
);

interface JourneyCardProps {
  number: string;
  title: string;
  description: string;
}

const JourneyCard: React.FC<JourneyCardProps> = ({
  number,
  title,
  description,
}) => (
  <div className="rounded-2xl bg-white/10 border border-white/10 p-4">
    <span className="text-[10px] font-black text-[#F7AE56]">
      {number}
    </span>

    <h3 className="mt-2 text-sm font-extrabold text-white">
      {title}
    </h3>

    <p className="mt-1 text-[11px] leading-relaxed text-[#FFFBF0]/70">
      {description}
    </p>
  </div>
);

export default Resources;