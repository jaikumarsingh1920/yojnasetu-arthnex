import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  HelpCircle,
  ChevronDown,
  Search,
  ShieldCheck,
  ArrowRight,
  BookOpen,
  Calculator,
  UserCheck,
} from 'lucide-react';

interface FAQItem {
  question: string;
  answer: string;
  category: string;
}

const faqs: FAQItem[] = [
  {
    category: 'GENERAL',
    question: 'What is YojnaSetu?',
    answer:
      'YojnaSetu is a citizen-focused platform that helps users discover government welfare schemes, understand their eligibility, compare suitable schemes, and access useful financial and application guidance.',
  },
  {
    category: 'GENERAL',
    question: 'Who can use YojnaSetu?',
    answer:
      'Any citizen looking for information about government welfare schemes can use YojnaSetu to explore schemes, understand eligibility requirements, and access relevant resources.',
  },
  {
    category: 'SCHEMES',
    question: 'How can I find a suitable government scheme?',
    answer:
      'You can explore the Schemes section to browse available welfare schemes. You can also use the matching and recommendation features to find schemes based on your requirements and eligibility information.',
  },
  {
    category: 'SCHEMES',
    question: 'How do I know if I am eligible for a scheme?',
    answer:
      'Each scheme has its own eligibility conditions. Open the scheme details page to review requirements such as age, income, occupation, category, location, or other scheme-specific conditions.',
  },
  {
    category: 'SCHEMES',
    question: 'Can I compare different schemes?',
    answer:
      'Yes. YojnaSetu provides a comparison feature that allows you to compare relevant schemes and understand their important differences before making a decision.',
  },
  {
    category: 'APPLICATIONS',
    question: 'Does YojnaSetu submit my application for me?',
    answer:
      'YojnaSetu primarily helps citizens discover and understand schemes. Application submission depends on the concerned government department or official application channel specified for the scheme.',
  },
  {
    category: 'APPLICATIONS',
    question: 'What documents do I need to apply?',
    answer:
      'Required documents vary from scheme to scheme. Always check the specific scheme details and the concerned official authority for the latest document requirements before applying.',
  },
  {
    category: 'FINANCE',
    question: 'Can I calculate my EMI on YojnaSetu?',
    answer:
      'Yes. The Financial Calculator can help you estimate your EMI using standard reducing-balance loan calculations and understand how loan amount, interest rate, and tenure affect repayment.',
  },
  {
    category: 'FINANCE',
    question: 'What is the difference between a subsidy and a loan?',
    answer:
      'A loan is borrowed money that generally needs to be repaid with applicable interest. A subsidy is financial assistance provided under a scheme according to its specific terms and conditions. Some schemes may combine credit with subsidy support.',
  },
  {
    category: 'PRIVACY',
    question: 'Does YojnaSetu store my personal information?',
    answer:
      'YojnaSetu follows a privacy-conscious approach and is designed to minimize unnecessary collection of personally identifiable information. Always review the platform and applicable service policies for the exact information handled by a particular feature.',
  },
  {
    category: 'PRIVACY',
    question: 'Is the information on YojnaSetu official?',
    answer:
      'YojnaSetu is designed around verified government scheme information and official guidance. However, scheme rules and application requirements can change, so users should verify the latest terms with the concerned official authority before applying.',
  },
  {
    category: 'SUPPORT',
    question: 'Where can I get help if I have a problem?',
    answer:
      'You can refer to the Resources & Guidelines section for citizen support and grievance information. For scheme-specific issues, contact the concerned government department or official helpdesk.',
  },
];

const categories = ['ALL', 'GENERAL', 'SCHEMES', 'APPLICATIONS', 'FINANCE', 'PRIVACY', 'SUPPORT'];

export const Faq: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('ALL');

  const filteredFaqs = faqs.filter((faq) => {
    const matchesCategory =
      activeCategory === 'ALL' || faq.category === activeCategory;

    const query = searchQuery.toLowerCase().trim();

    const matchesSearch =
      !query ||
      faq.question.toLowerCase().includes(query) ||
      faq.answer.toLowerCase().includes(query) ||
      faq.category.toLowerCase().includes(query);

    return matchesCategory && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-[#fef9f3] text-slate-800">

      {/* HERO */}
      <section className="relative overflow-hidden bg-gradient-to-br from-[#861823] via-[#5b1827] to-[#071b2b] text-white">
        <div className="absolute -top-28 -right-28 w-96 h-96 rounded-full bg-gov-saffron/10 blur-3xl" />
        <div className="absolute -bottom-32 -left-24 w-[28rem] h-[28rem] rounded-full bg-sky-500/10 blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-5 sm:px-8 lg:px-10 py-16 sm:py-20">
          <div className="max-w-4xl">

            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/15 text-xs font-bold tracking-wide mb-5">
              <HelpCircle className="w-4 h-4 text-gov-saffron" />
              CITIZEN SUPPORT
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
              Frequently Asked{' '}
              <span className="text-gov-saffron">Questions</span>
            </h1>

            <p className="mt-5 max-w-3xl text-sm sm:text-base lg:text-lg text-white/75 leading-relaxed">
              Find quick answers about YojnaSetu, government schemes,
              eligibility, applications, financial tools and privacy.
            </p>

            {/* SEARCH */}
            <div className="mt-8 max-w-2xl relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />

              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search your question..."
                className="w-full pl-12 pr-5 py-4 rounded-2xl bg-white text-slate-800 placeholder:text-slate-400 outline-none border border-white/20 shadow-xl text-sm"
              />
            </div>

          </div>
        </div>
      </section>

      {/* CATEGORY FILTER */}
      <section className="bg-white border-b border-slate-200 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 lg:px-10 py-4 overflow-x-auto">
          <div className="flex items-center gap-2 min-w-max">
            {categories.map((category) => (
              <button
                key={category}
                type="button"
                onClick={() => setActiveCategory(category)}
                className={`px-4 py-2 rounded-full text-xs font-extrabold tracking-wide transition ${
                  activeCategory === category
                    ? 'bg-[#861823] text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ CONTENT */}
      <main className="max-w-5xl mx-auto px-5 sm:px-8 py-12 sm:py-16">

        <div className="text-center mb-10">
          <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[#861823]">
            Help Centre
          </p>

          <h2 className="mt-2 text-3xl sm:text-4xl font-extrabold text-slate-900">
            How can we help?
          </h2>

          <p className="mt-3 text-sm text-slate-600">
            {filteredFaqs.length} question
            {filteredFaqs.length !== 1 ? 's' : ''} found
          </p>
        </div>

        {filteredFaqs.length > 0 ? (
          <div className="space-y-3">
            {filteredFaqs.map((faq, index) => {
              const isOpen = openIndex === index;

              return (
                <div
                  key={`${faq.question}-${index}`}
                  className={`bg-white border rounded-2xl overflow-hidden transition-all ${
                    isOpen
                      ? 'border-[#861823]/30 shadow-md'
                      : 'border-slate-200 shadow-sm'
                  }`}
                >
                  <button
                    type="button"
                    onClick={() =>
                      setOpenIndex(isOpen ? null : index)
                    }
                    className="w-full flex items-center justify-between gap-5 text-left px-5 sm:px-6 py-5"
                  >
                    <div className="flex items-start gap-4 min-w-0">
                      <div
                        className={`shrink-0 w-9 h-9 rounded-xl flex items-center justify-center ${
                          isOpen
                            ? 'bg-[#861823] text-white'
                            : 'bg-[#861823]/10 text-[#861823]'
                        }`}
                      >
                        <HelpCircle className="w-4 h-4" />
                      </div>

                      <div className="min-w-0">
                        <span className="inline-block text-[9px] font-extrabold tracking-wider text-[#861823] mb-1">
                          {faq.category}
                        </span>

                        <h3 className="text-sm sm:text-base font-extrabold text-slate-900 leading-relaxed">
                          {faq.question}
                        </h3>
                      </div>
                    </div>

                    <ChevronDown
                      className={`w-5 h-5 shrink-0 text-slate-400 transition-transform ${
                        isOpen ? 'rotate-180 text-[#861823]' : ''
                      }`}
                    />
                  </button>

                  {isOpen && (
                    <div className="px-5 sm:px-6 pb-5">
                      <div className="ml-13 pl-13 sm:pl-[52px]">
                        <p className="text-sm text-slate-600 leading-relaxed">
                          {faq.answer}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-2xl p-10 text-center">
            <div className="mx-auto w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center">
              <Search className="w-5 h-5 text-slate-400" />
            </div>

            <h3 className="mt-4 text-lg font-extrabold text-slate-900">
              No questions found
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Try a different search term or category.
            </p>
          </div>
        )}

        {/* QUICK LINKS */}
        <section className="mt-14">
          <div className="text-center mb-7">
            <p className="text-xs font-extrabold uppercase tracking-wider text-gov-saffron">
              Need More Information?
            </p>

            <h2 className="mt-2 text-2xl sm:text-3xl font-extrabold text-slate-900">
              Explore YojnaSetu
            </h2>
          </div>

          <div className="grid sm:grid-cols-3 gap-4">

            <Link
              to="/schemes"
              className="group bg-white border border-slate-200 rounded-2xl p-5 hover:shadow-lg hover:-translate-y-0.5 transition"
            >
              <BookOpen className="w-6 h-6 text-[#861823]" />

              <h3 className="mt-4 font-extrabold text-slate-900">
                Explore Schemes
              </h3>

              <p className="mt-1 text-xs text-slate-500 leading-relaxed">
                Browse government welfare schemes and understand their
                eligibility.
              </p>

              <span className="mt-4 inline-flex items-center gap-2 text-xs font-extrabold text-[#861823]">
                View Schemes
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
              </span>
            </Link>

            <Link
              to="/resources"
              className="group bg-white border border-slate-200 rounded-2xl p-5 hover:shadow-lg hover:-translate-y-0.5 transition"
            >
              <ShieldCheck className="w-6 h-6 text-emerald-700" />

              <h3 className="mt-4 font-extrabold text-slate-900">
                Resources & Guidelines
              </h3>

              <p className="mt-1 text-xs text-slate-500 leading-relaxed">
                Access official guidance, financial literacy and citizen
                support resources.
              </p>

              <span className="mt-4 inline-flex items-center gap-2 text-xs font-extrabold text-[#861823]">
                View Resources
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
              </span>
            </Link>

            <Link
              to="/calculator"
              className="group bg-white border border-slate-200 rounded-2xl p-5 hover:shadow-lg hover:-translate-y-0.5 transition"
            >
              <Calculator className="w-6 h-6 text-amber-600" />

              <h3 className="mt-4 font-extrabold text-slate-900">
                Financial Calculator
              </h3>

              <p className="mt-1 text-xs text-slate-500 leading-relaxed">
                Estimate EMI and understand your potential repayment
                obligations.
              </p>

              <span className="mt-4 inline-flex items-center gap-2 text-xs font-extrabold text-[#861823]">
                Open Calculator
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition" />
              </span>
            </Link>

          </div>
        </section>

        {/* FINAL SUPPORT CARD */}
        <section className="mt-10">
          <div className="rounded-3xl bg-gradient-to-br from-[#861823] via-[#5b1827] to-[#071b2b] text-white p-7 sm:p-9">

            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">

              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-white/10 border border-white/10">
                  <UserCheck className="w-6 h-6 text-gov-saffron" />
                </div>

                <div>
                  <h3 className="text-lg sm:text-xl font-extrabold">
                    Still have questions?
                  </h3>

                  <p className="mt-1 text-sm text-white/65 max-w-xl">
                    Check the relevant scheme details or refer to the official
                    authority before submitting an application.
                  </p>
                </div>
              </div>

              <Link
                to="/schemes"
                className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-white text-[#861823] text-sm font-extrabold hover:bg-orange-50 transition shrink-0"
              >
                Find a Scheme
                <ArrowRight className="w-4 h-4" />
              </Link>

            </div>

          </div>
        </section>

      </main>
    </div>
  );
};

export default Faq;