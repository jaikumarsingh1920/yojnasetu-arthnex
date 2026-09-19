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
    <div className="space-y-8 pb-16 bg-[#FFFBF0] min-h-screen">
      {/* HERO */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 sm:pt-8">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white border border-[#E8D8D2]/20 shadow-warm-md p-6 sm:p-8 lg:p-10">
          <div className="relative z-10 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/15 text-xs font-bold tracking-wide mb-3">
              <HelpCircle className="w-4 h-4 text-[#F7AE56]" aria-hidden="true" />
              <span className="text-[#FFFBF0]">CITIZEN SUPPORT & GUIDELINES</span>
            </div>

            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight leading-tight text-white">
              Help & Support
            </h1>

            <p className="mt-2 text-sm sm:text-base text-[#FFFBF0]/85 leading-relaxed">
              Find answers, guidelines and official government resources to navigate welfare schemes and financial tools.
            </p>

            {/* Quick Search */}
            <div className="relative mt-5 max-w-xl">
              <Search className="w-5 h-5 text-[#765E59] absolute left-4 top-3.5" aria-hidden="true" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search questions (e.g., eligibility, documents, loans, partners)..."
                className="w-full pl-12 pr-5 py-3 rounded-2xl bg-white text-[#3B2522] placeholder:text-[#765E59]/60 outline-none border border-[#E8D8D2] focus:border-[#EA717B] focus:ring-2 focus:ring-[#EA717B]/20 shadow-warm-sm text-xs sm:text-sm font-medium transition"
              />
            </div>
          </div>
        </div>
      </section>

      {/* TABS ROW */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-2xl border border-[#E8D8D2] p-2 shadow-warm-xs flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 overflow-x-auto">
            <button
              type="button"
              className="px-4 py-2 rounded-xl text-xs font-extrabold bg-[#EA717B] text-white shadow-warm-xs"
            >
              Frequently Asked Questions
            </button>
            <Link
              to="/resources"
              className="px-4 py-2 rounded-xl text-xs font-bold text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFF4EC] transition"
            >
              Guidelines
            </Link>
            <Link
              to="/resources"
              className="px-4 py-2 rounded-xl text-xs font-bold text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFF4EC] transition"
            >
              Resources & Data Policy
            </Link>
          </div>
        </div>
      </section>

      {/* 2-COLUMN MAIN CONTENT */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: FAQ Items & Categories (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            {/* Category Filter Pills */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1">
              {categories.map((category) => (
                <button
                  key={category}
                  type="button"
                  onClick={() => setActiveCategory(category)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap ${
                    activeCategory === category
                      ? 'bg-[#EA717B] text-white shadow-warm-xs'
                      : 'bg-white text-[#765E59] hover:bg-[#FFF4EC] border border-[#E8D8D2]'
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>

            {/* Questions List */}
            {filteredFaqs.length > 0 ? (
              <div className="space-y-3">
                {filteredFaqs.map((faq, index) => {
                  const isOpen = openIndex === index;

                  return (
                    <div
                      key={`${faq.question}-${index}`}
                      className={`bg-white border rounded-2xl overflow-hidden transition-all ${
                        isOpen
                          ? 'border-[#EA717B]/60 shadow-warm-sm ring-1 ring-[#EA717B]/20'
                          : 'border-[#E8D8D2] shadow-warm-xs hover:border-[#FFD0CA]'
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => setOpenIndex(isOpen ? null : index)}
                        className={`w-full text-left p-4 sm:p-5 flex items-start justify-between gap-4 transition ${
                          isOpen ? 'bg-[#FFF4EC]' : 'bg-white'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div
                            className={`mt-0.5 p-2 rounded-xl shrink-0 transition ${
                              isOpen
                                ? 'bg-[#EA717B] text-white'
                                : 'bg-[#FFD0CA] text-[#4A2525]'
                            }`}
                          >
                            <HelpCircle className="w-4 h-4" aria-hidden="true" />
                          </div>

                          <div>
                            <span className="inline-block text-[9px] font-extrabold tracking-wider text-[#EA717B] uppercase mb-0.5">
                              {faq.category}
                            </span>
                            <h3 className="text-sm sm:text-base font-bold text-[#3B2522] leading-snug">
                              {faq.question}
                            </h3>
                          </div>
                        </div>

                        <ChevronDown
                          aria-hidden="true"
                          className={`w-4 h-4 text-[#765E59] shrink-0 transition-transform duration-200 mt-1 ${
                            isOpen ? 'rotate-180 text-[#EA717B]' : ''
                          }`}
                        />
                      </button>

                      {isOpen && (
                        <div className="px-5 pb-5 pt-0 bg-[#FFF4EC]">
                          <div className="pl-11">
                            <p className="text-xs sm:text-sm text-[#765E59] leading-relaxed">
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
              <div className="bg-white border border-[#E8D8D2] rounded-2xl p-10 text-center shadow-warm-xs">
                <div className="mx-auto w-12 h-12 rounded-full bg-[#FFF4EC] flex items-center justify-center">
                  <Search className="w-5 h-5 text-[#765E59]" aria-hidden="true" />
                </div>
                <h3 className="mt-4 text-base font-extrabold text-[#3B2522]">
                  No questions found
                </h3>
                <p className="mt-1 text-xs text-[#765E59]">
                  Try a different search term or select "ALL".
                </p>
              </div>
            )}
          </div>

          {/* Right Column: "Need More Help?" Card (4 cols) */}
          <div className="lg:col-span-4 space-y-5">
            <div className="bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs p-6 space-y-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-[#FFD0CA] text-[#4A2525] flex items-center justify-center shrink-0">
                  <HelpCircle className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-[#3B2522]">Need More Help?</h3>
                  <p className="text-xs text-[#765E59]">Official citizen assistance</p>
                </div>
              </div>

              <div className="space-y-4 pt-1 text-xs text-[#765E59]">
                <div className="flex items-start gap-3 bg-[#FFF4EC] p-3.5 rounded-2xl border border-[#FFD0CA]">
                  <div className="w-8 h-8 rounded-xl bg-[#2D6A4F]/10 text-[#2D6A4F] flex items-center justify-center shrink-0 text-sm">
                    📞
                  </div>
                  <div>
                    <div className="text-[10px] uppercase font-bold text-[#765E59]/70">Toll-Free Helpline</div>
                    <a href="tel:1800112026" className="text-sm font-black text-[#3B2522] hover:text-[#EA717B] transition">
                      1800-11-2026
                    </a>
                    <div className="text-[11px] text-[#765E59]">9 AM – 6 PM (IST), Mon – Fri</div>
                  </div>
                </div>

                <div className="flex items-start gap-3 bg-[#FFF4EC] p-3.5 rounded-2xl border border-[#FFD0CA]">
                  <div className="w-8 h-8 rounded-xl bg-[#EA717B]/10 text-[#EA717B] flex items-center justify-center shrink-0 text-sm">
                    ✉️
                  </div>
                  <div>
                    <div className="text-[10px] uppercase font-bold text-[#765E59]/70">Citizen Support Email</div>
                    <a href="mailto:support@yojnasetu.gov.in" className="text-xs font-bold text-[#EA717B] hover:underline">
                      support@yojnasetu.gov.in
                    </a>
                    <div className="text-[11px] text-[#765E59]">Responses within 24–48 hours</div>
                  </div>
                </div>

                <div className="flex items-start gap-3 bg-[#FFF4EC] p-3.5 rounded-2xl border border-[#FFD0CA]">
                  <div className="w-8 h-8 rounded-xl bg-[#F7AE56]/20 text-[#4A2525] flex items-center justify-center shrink-0 text-sm">
                    🏛️
                  </div>
                  <div>
                    <div className="text-[10px] uppercase font-bold text-[#765E59]/70">Department Address</div>
                    <div className="text-xs font-bold text-[#3B2522]">
                      Ministry of Social Justice and Empowerment
                    </div>
                    <div className="text-[11px] text-[#765E59]">Shastri Bhawan, New Delhi – 110001</div>
                  </div>
                </div>
              </div>

              <a
                href="tel:1800112026"
                className="w-full py-2.5 text-xs font-bold rounded-xl flex items-center justify-center gap-2 shadow-warm-xs bg-[#EA717B] text-white hover:bg-[#d65f69] transition"
              >
                <span>Contact Official Support</span>
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>

            {/* Quick Tools Box */}
            <div className="bg-gradient-to-br from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white rounded-3xl p-5 space-y-3 shadow-warm-md border border-[#E8D8D2]/20">
              <div className="text-xs font-bold text-[#F7AE56] uppercase tracking-wider">
                Explore YojnaSetu Tools
              </div>
              <div className="space-y-2">
                <Link
                  to="/recommendations"
                  className="flex items-center justify-between p-2.5 rounded-xl bg-white/10 hover:bg-white/15 transition text-xs font-bold text-[#FFFBF0]"
                >
                  <span>Smart Scheme Matching</span>
                  <ArrowRight className="w-3.5 h-3.5 text-[#F7AE56]" />
                </Link>
                <Link
                  to="/calculator"
                  className="flex items-center justify-between p-2.5 rounded-xl bg-white/10 hover:bg-white/15 transition text-xs font-bold text-[#FFFBF0]"
                >
                  <span>Financial Calculator</span>
                  <ArrowRight className="w-3.5 h-3.5 text-[#F7AE56]" />
                </Link>
                <Link
                  to="/channel-partners"
                  className="flex items-center justify-between p-2.5 rounded-xl bg-white/10 hover:bg-white/15 transition text-xs font-bold text-[#FFFBF0]"
                >
                  <span>Find Nearby Partner</span>
                  <ArrowRight className="w-3.5 h-3.5 text-[#F7AE56]" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Faq;