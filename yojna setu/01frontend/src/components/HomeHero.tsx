import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Search,
  Building2,
  Tractor,
  GraduationCap,
  Users,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';

import heroEntrepreneur from '../assets/hero-entrepreneur.png';
import heroFarmer from '../assets/hero-farmer.png';

export interface WarmHeroSlide {
  id: string;
  image: string;
  position?: string;
  badgeText: string;
  badgeIcon: React.ElementType;
  title: string;
  highlightWord?: string;
  subtitle: string;
  primaryCtaText: string;
  primaryCtaLink: string;
  secondaryCtaText: string;
  secondaryCtaLink: string;
  accentColor: string;
  features: string[];
  storyTag: string;
}

export const HomeHero: React.FC<{ totalSchemes?: number }> = ({ totalSchemes = 859 }) => {
  const { t } = useTranslation();
  const [activeSlide, setActiveSlide] = useState<number>(0);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);
  const autoplayTimerRef = useRef<NodeJS.Timeout | null>(null);

  const slides: WarmHeroSlide[] = [
    {
      id: 'digital-civic',
      image: heroEntrepreneur,
      position: 'center center',
      badgeText: 'National Welfare & Credit Guidance Portal',
      badgeIcon: ShieldCheck,
      title: 'Smart Civic Matching for Every Indian Citizen',
      highlightWord: 'Every Indian Citizen',
      subtitle:
        'Discover, evaluate and access 850+ verified Central and State welfare schemes with statutory eligibility rules and zero red tape.',
      primaryCtaText: 'Find Schemes for Me',
      primaryCtaLink: '/recommendations',
      secondaryCtaText: 'Browse All Schemes',
      secondaryCtaLink: '/schemes',
      accentColor: '#EA717B',
      features: ['Statutory Rule Engine', '12 Indian Languages', '100% Free Public Portal'],
      storyTag: 'Digital Civic Access',
    },
    {
      id: 'women-empowerment',
      image: heroFarmer,
      position: 'center center',
      badgeText: 'Women Welfare • Self-Help Groups • Direct Subsidy',
      badgeIcon: Users,
      title: 'Direct Welfare Support for Families & Women SHGs',
      highlightWord: 'Families & Women SHGs',
      subtitle:
        'Access tailored maternity assistance, livelihood capital subsidies, micro-enterprise loans, and healthcare protections designed for women.',
      primaryCtaText: 'Explore Women Schemes',
      primaryCtaLink: '/schemes?search=Women',
      secondaryCtaText: 'Check Eligibility',
      secondaryCtaLink: '/recommendations',
      accentColor: '#F7AE56',
      features: ['Mudra Mahila Loans', 'Stand-Up India Cover', 'Direct Bank Transfer'],
      storyTag: 'Women & Self-Help Groups',
    },
    {
      id: 'entrepreneurs',
      image: heroEntrepreneur,
      position: 'center right',
      badgeText: 'Micro & Small Enterprises • Business Credit',
      badgeIcon: Building2,
      title: 'Capital Subsidies & Collateral-Free Business Loans',
      highlightWord: 'Collateral-Free Business Loans',
      subtitle:
        'Discover capital subsidies up to 35% under PMEGP, collateral-free credit under MUDRA, and technology upgradation support for your enterprise.',
      primaryCtaText: 'Calculate Loan Subsidy',
      primaryCtaLink: '/calculator',
      secondaryCtaText: 'Explore MSME Credit',
      secondaryCtaLink: '/schemes?search=Mudra',
      accentColor: '#EA717B',
      features: ['PMEGP & MUDRA', 'Zero Collateral Cover', 'Direct Channel Partners'],
      storyTag: 'Enterprise & Startups',
    },
    {
      id: 'farmers',
      image: heroFarmer,
      position: 'center center',
      badgeText: 'Agriculture & Rural Livelihood • Kisan Welfare',
      badgeIcon: Tractor,
      title: 'Empowering Farming Families with Direct Welfare',
      highlightWord: 'Direct Welfare',
      subtitle:
        'Explore verified government assistance for farm machinery, solar agri-pumps (PM-KUSUM), livestock development, and concessional Kisan Credit.',
      primaryCtaText: 'Explore Agri Schemes',
      primaryCtaLink: '/schemes?search=Agriculture',
      secondaryCtaText: 'Check Kisan Eligibility',
      secondaryCtaLink: '/recommendations',
      accentColor: '#F7AE56',
      features: ['Kisan Credit Card (KCC)', 'PM-KUSUM Solar', 'Direct Input Subsidy'],
      storyTag: 'Farmers & Agri-Allied',
    },
    {
      id: 'students',
      image: heroEntrepreneur,
      position: 'center center',
      badgeText: 'Youth & Higher Education • Fellowships & Grants',
      badgeIcon: GraduationCap,
      title: 'Opportunities for Every Stage of Your Education',
      highlightWord: 'Your Education',
      subtitle:
        'Discover pre-matric and post-matric scholarships, skill certification stipends, higher study fellowships, and coaching assistance.',
      primaryCtaText: 'Find Scholarships',
      primaryCtaLink: '/schemes?search=Scholarship',
      secondaryCtaText: 'Skill India Programs',
      secondaryCtaLink: '/schemes?search=Skill',
      accentColor: '#EA717B',
      features: ['National Scholarships', 'Skill India Grants', 'Fee Reimbursements'],
      storyTag: 'Students & Youth',
    },
  ];

  const totalSlides = slides.length;

  const handleNext = useCallback(() => {
    setActiveSlide((prev) => (prev + 1) % totalSlides);
  }, [totalSlides]);

  const handlePrev = useCallback(() => {
    setActiveSlide((prev) => (prev - 1 + totalSlides) % totalSlides);
  }, [totalSlides]);

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > 50;
    const isRightSwipe = distance < -50;
    if (isLeftSwipe) handleNext();
    if (isRightSwipe) handlePrev();
  };

  useEffect(() => {
    if (isPaused) {
      if (autoplayTimerRef.current) clearInterval(autoplayTimerRef.current);
      return;
    }
    autoplayTimerRef.current = setInterval(() => {
      handleNext();
    }, 6000);
    return () => {
      if (autoplayTimerRef.current) clearInterval(autoplayTimerRef.current);
    };
  }, [isPaused, handleNext]);

  return (
    <div className="w-full relative bg-[#FFFBF0]">
      {/* ============================================================
          1. FULL-WIDTH EDGE-TO-EDGE SLIDING CAROUSEL VIEWPORT
          ============================================================ */}
      <div
        className="w-full relative overflow-hidden select-none"
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        aria-label="YojnaSetu National Welfare Hero Carousel"
      >
        {/* Horizontal Sliding Track with Smooth Motion */}
        <div
          className="flex w-full transition-transform duration-700 ease-in-out"
          style={{ transform: `translateX(-${activeSlide * 100}%)` }}
        >
          {slides.map((slide, idx) => {
            const BadgeIcon = slide.badgeIcon;
            return (
              <div
                key={slide.id}
                className="w-full flex-shrink-0 relative h-[420px] sm:h-[480px] md:h-[520px] lg:h-[560px] xl:h-[600px] overflow-hidden bg-[#FAF6EE]"
              >
                {/* Full Width Background Image from assets */}
                <img
                  src={slide.image}
                  alt={slide.title}
                  className="w-full h-full object-cover object-center"
                  style={{ objectPosition: slide.position || 'center center' }}
                  loading={idx === 0 ? 'eager' : 'lazy'}
                />

                {/* Warm Pastel Scrim Overlay: Soft Vanilla Scrim on Left for pristine typography contrast */}
                <div className="absolute inset-0 bg-gradient-to-r from-[#FFFBF0]/95 via-[#FFFBF0]/85 sm:via-[#FFFBF0]/75 to-transparent max-w-3xl pointer-events-none" />
                <div className="absolute inset-0 bg-gradient-to-t from-[#FFFBF0]/90 via-transparent to-transparent sm:hidden pointer-events-none" />

                {/* Left Content Container */}
                <div className="absolute inset-0 flex items-center z-10">
                  <div className="max-w-7xl mx-auto px-4 sm:px-8 lg:px-12 w-full">
                    <div className="max-w-xl sm:max-w-2xl space-y-3 sm:space-y-4 text-left">
                      
                      {/* Eyebrow Pill Badge */}
                      <div className="inline-flex items-center gap-2 bg-[#FFF4EC] px-3.5 py-1.5 rounded-full border border-[#FFD0CA] shadow-sm">
                        <BadgeIcon className="w-3.5 h-3.5 text-[#F7AE56] shrink-0" aria-hidden="true" />
                        <span className="text-[11px] sm:text-xs font-bold tracking-wider text-[#4A2525] uppercase">
                          {slide.badgeText}
                        </span>
                      </div>

                      {/* Large Headline */}
                      <h1 className="text-2xl sm:text-4xl lg:text-5xl font-black text-[#3B2522] leading-[1.15] tracking-tight">
                        {slide.title}
                      </h1>

                      {/* Subtitle */}
                      <p className="text-xs sm:text-base text-[#765E59] font-medium leading-relaxed max-w-lg line-clamp-3 sm:line-clamp-none">
                        {slide.subtitle}
                      </p>

                      {/* Feature Chips */}
                      <div className="flex flex-wrap gap-2 pt-1">
                        {slide.features.map((feat, fIdx) => (
                          <div
                            key={fIdx}
                            className="inline-flex items-center gap-1.5 bg-[#FFF4EC] border border-[#E8D8D2] text-[#3B2522] px-3 py-1 rounded-xl text-xs font-semibold shadow-xs"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5 text-[#EA717B] shrink-0" aria-hidden="true" />
                            <span>{feat}</span>
                          </div>
                        ))}
                      </div>

                      {/* Call to Actions - Strictly in Warm Pastel Palette (NO green) */}
                      <div className="flex flex-wrap items-center gap-3 pt-2 sm:pt-3">
                        <Link
                          to={slide.primaryCtaLink}
                          className="inline-flex items-center gap-2 px-6 sm:px-8 py-3 sm:py-3.5 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#EA717B] hover:bg-[#D65D67] shadow-sm hover:shadow-md transition-all duration-200 transform hover:-translate-y-0.5"
                        >
                          <Sparkles className="w-4 h-4 text-[#FFF0EE]" aria-hidden="true" />
                          <span>{slide.primaryCtaText}</span>
                          <ArrowRight className="w-4 h-4" />
                        </Link>

                        <Link
                          to={slide.secondaryCtaLink}
                          className="inline-flex items-center gap-2 px-5 sm:px-6 py-3 sm:py-3.5 rounded-xl bg-[#FFD0CA] hover:bg-[#F5B8B0] text-[#4A2525] font-bold text-xs sm:text-sm border border-[#E8D8D2] shadow-xs transition-all duration-200"
                        >
                          <Search className="w-4 h-4 text-[#4A2525]" aria-hidden="true" />
                          <span>{slide.secondaryCtaText}</span>
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* LEFT NAV ARROW (Pinned to Left Edge - Warm Mahogany & Coral, NO green) */}
        <button
          type="button"
          onClick={handlePrev}
          aria-label="Previous Slide"
          className="absolute left-2 sm:left-4 top-1/2 -translate-y-1/2 z-30 w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-[#4A2525]/85 hover:bg-[#EA717B] text-white flex items-center justify-center shadow-md transition-all duration-200 active:scale-90 hover:scale-105"
        >
          <ChevronLeft className="w-5 h-5 sm:w-6 sm:h-6" />
        </button>

        {/* RIGHT NAV ARROW (Pinned to Right Edge - Warm Mahogany & Coral, NO green) */}
        <button
          type="button"
          onClick={handleNext}
          aria-label="Next Slide"
          className="absolute right-2 sm:right-4 top-1/2 -translate-y-1/2 z-30 w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-[#4A2525]/85 hover:bg-[#EA717B] text-white flex items-center justify-center shadow-md transition-all duration-200 active:scale-90 hover:scale-105"
        >
          <ChevronRight className="w-5 h-5 sm:w-6 sm:h-6" />
        </button>

        {/* BOTTOM PAGINATION DOTS & COUNTER */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-30 flex items-center gap-2 bg-[#4A2525]/75 backdrop-blur-md px-4 py-1.5 rounded-full border border-[#E8D8D2]/25 shadow-sm">
          {slides.map((_, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setActiveSlide(idx)}
              aria-label={`Go to slide ${idx + 1}`}
              className={`h-2 rounded-full transition-all duration-300 ${
                idx === activeSlide
                  ? 'w-7 bg-[#EA717B]'
                  : 'w-2 bg-[#FFD0CA]/60 hover:bg-[#FFD0CA]'
              }`}
            />
          ))}
          <span className="text-[11px] font-mono font-bold text-[#FFFBF0] ml-1.5">
            0{activeSlide + 1} / 0{totalSlides}
          </span>
        </div>
      </div>

      {/* ============================================================
          2. MANGO ACCENT STRIP & ACTION CALLOUT (WARM PALETTE - NO GREEN)
          ============================================================ */}
      <div className="w-full bg-[#F7AE56] h-2 sm:h-2.5 shadow-xs" />

      <div className="w-full bg-white border-b border-[#E8D8D2] py-6 sm:py-8 px-4 text-center shadow-xs">
        <div className="max-w-4xl mx-auto flex flex-col items-center justify-center space-y-4">
          {/* Tagline */}
          <div className="text-base sm:text-xl lg:text-2xl font-black text-[#3B2522] tracking-wider uppercase">
            #GOVERNMENTSCHEMES / #SCHEMESFORYOU
          </div>

          {/* Tropical Punch Coral Action Button (NO GREEN) */}
          <Link
            to="/recommendations"
            className="inline-flex items-center justify-center gap-3 px-8 sm:px-10 py-3.5 sm:py-4 rounded-xl bg-[#EA717B] hover:bg-[#D65D67] text-white font-black text-base sm:text-lg shadow-sm hover:shadow-md transition-all duration-200 transform hover:-translate-y-0.5 active:scale-95 group"
          >
            <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 text-[#FFF0EE]" />
            <span>Find Schemes For You</span>
            <ArrowRight className="w-5 h-5 sm:w-6 sm:h-6 group-hover:translate-x-1.5 transition-transform" />
          </Link>

          <p className="text-xs sm:text-sm text-[#765E59] font-medium">
            Discover verified benefits tailored to your state, occupation, income & category in 3 simple questions.
          </p>
        </div>
      </div>
    </div>
  );
};
