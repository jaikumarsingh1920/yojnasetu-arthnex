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

import heroDigital from '../assets/hero-digital.jpg';
import heroWomen from '../assets/hero-women.jpg';
import heroEntrepreneur from '../assets/hero-entrepreneur.png';
import heroFarmer from '../assets/hero-farmer.png';
import heroStudent from '../assets/hero-student.jpg';

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
      image: heroDigital,
      position: '85% center',
      badgeText: t('home.hero.slide1_badge', 'National Welfare & Citizen Empowerment'),
      badgeIcon: ShieldCheck,
      title: t('home.hero.slide1_title', 'Smart Civic Matching for Every Indian Citizen'),
      highlightWord: 'Every Indian Citizen',
      subtitle: t(
        'home.hero.slide1_subtitle',
        'Discover, evaluate and access verified government schemes with clear eligibility, real-time guidance and local support.'
      ),
      primaryCtaText: t('home.hero.slide1_primaryCta', 'Find Schemes for You'),
      primaryCtaLink: '/recommendations',
      secondaryCtaText: t('home.hero.slide1_secondaryCta', 'Check Eligibility'),
      secondaryCtaLink: '/recommendations',
      accentColor: '#EA717B',
      features: [
        t('home.hero.slide1_feature1', 'Verified Schemes'),
        t('home.hero.slide1_feature2', 'AI-Powered Matching'),
        t('home.hero.slide1_feature3', 'Multi-Language Support'),
      ],
      storyTag: t('home.hero.slide1_storyTag', 'Digital Civic Access'),
    },
    {
      id: 'women-empowerment',
      image: heroWomen,
      position: '85% center',
      badgeText: t('home.hero.slide2_badge', 'Women Welfare • Self-Help Groups • Direct Subsidy'),
      badgeIcon: Users,
      title: t('home.hero.slide2_title', 'Direct Welfare Support for Families & Women SHGs'),
      highlightWord: 'Families & Women SHGs',
      subtitle: t(
        'home.hero.slide2_subtitle',
        'Access tailored maternity assistance, livelihood capital subsidies, micro-enterprise loans, and healthcare protections designed for women.'
      ),
      primaryCtaText: t('home.hero.slide2_primaryCta', 'Explore Women Schemes'),
      primaryCtaLink: '/schemes?search=Women',
      secondaryCtaText: t('home.hero.slide2_secondaryCta', 'Check Eligibility'),
      secondaryCtaLink: '/recommendations',
      accentColor: '#F7AE56',
      features: [
        t('home.hero.slide2_feature1', 'Mudra Mahila Loans'),
        t('home.hero.slide2_feature2', 'Stand-Up India Cover'),
        t('home.hero.slide2_feature3', 'Direct Bank Transfer'),
      ],
      storyTag: t('home.hero.slide2_storyTag', 'Women & Self-Help Groups'),
    },
    {
      id: 'entrepreneurs',
      image: heroEntrepreneur,
      position: '85% center',
      badgeText: t('home.hero.slide3_badge', 'Micro & Small Enterprises • Business Credit'),
      badgeIcon: Building2,
      title: t('home.hero.slide3_title', 'Capital Subsidies & Collateral-Free Business Loans'),
      highlightWord: 'Collateral-Free Business Loans',
      subtitle: t(
        'home.hero.slide3_subtitle',
        'Discover capital subsidies up to 35% under PMEGP, collateral-free credit under MUDRA, and technology upgradation support for your enterprise.'
      ),
      primaryCtaText: t('home.hero.slide3_primaryCta', 'Calculate Loan Subsidy'),
      primaryCtaLink: '/calculator',
      secondaryCtaText: t('home.hero.slide3_secondaryCta', 'Explore MSME Credit'),
      secondaryCtaLink: '/schemes?search=Mudra',
      accentColor: '#EA717B',
      features: [
        t('home.hero.slide3_feature1', 'PMEGP 35% Margin'),
        t('home.hero.slide3_feature2', 'CGTMSE Guarantee'),
        t('home.hero.slide3_feature3', 'Subsidized Interest'),
      ],
      storyTag: t('home.hero.slide3_storyTag', 'Micro & Small Business'),
    },
    {
      id: 'farmers',
      image: heroFarmer,
      position: '85% center',
      badgeText: t('home.hero.slide4_badge', 'Farmer Livelihood • Agritech • Direct Income Support'),
      badgeIcon: Tractor,
      title: t('home.hero.slide4_title', 'Agricultural Subsidies & Direct Income Support'),
      highlightWord: 'Direct Welfare',
      subtitle: t(
        'home.hero.slide4_subtitle',
        'Connect with PM-KISAN income support, solar pump subsidies under KUSUM, Kisan Credit Card loans, and crop insurance protections.'
      ),
      primaryCtaText: t('home.hero.slide4_primaryCta', 'Explore Agriculture Schemes'),
      primaryCtaLink: '/schemes?search=Agriculture',
      secondaryCtaText: t('home.hero.slide4_secondaryCta', 'Calculate Farm Subsidy'),
      secondaryCtaLink: '/recommendations',
      accentColor: '#F7AE56',
      features: [
        t('home.hero.slide4_feature1', 'PM-KISAN ₹6,000/yr'),
        t('home.hero.slide4_feature2', 'PM-KUSUM Solar Subsidy'),
        t('home.hero.slide4_feature3', 'KCC @ 4% Interest'),
      ],
      storyTag: t('home.hero.slide4_storyTag', 'Agriculture & Rural'),
    },
    {
      id: 'students',
      image: heroStudent,
      position: '85% center',
      badgeText: t('home.hero.slide5_badge', 'Higher Education • Merit Scholarships • Skill Development'),
      badgeIcon: GraduationCap,
      title: t('home.hero.slide5_title', 'Higher Education Scholarships & Concession Loans'),
      highlightWord: 'Your Education',
      subtitle: t(
        'home.hero.slide5_subtitle',
        'Find central merit scholarships, education loan interest subsidies, and professional skill training allowances for students.'
      ),
      primaryCtaText: t('home.hero.slide5_primaryCta', 'Explore Student Schemes'),
      primaryCtaLink: '/schemes?search=Scholarship',
      secondaryCtaText: t('home.hero.slide5_secondaryCta', 'Check Scholarship Eligibility'),
      secondaryCtaLink: '/schemes?search=Skill',
      accentColor: '#EA717B',
      features: [
        t('home.hero.slide5_feature1', 'National Scholarship Portal'),
        t('home.hero.slide5_feature2', 'Education Loan Subsidy'),
        t('home.hero.slide5_feature3', 'Skill Training Stipends'),
      ],
      storyTag: t('home.hero.slide5_storyTag', 'Education & Students'),
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
                className="w-full flex-shrink-0 relative h-[430px] sm:h-[490px] md:h-[530px] lg:h-[570px] xl:h-[610px] overflow-hidden bg-[#FAF6EE]"
              >
                {/* Full Width Background Image anchored to right to keep human subjects visible */}
                <img
                  src={slide.image}
                  alt={slide.title}
                  className="w-full h-full object-cover"
                  style={{ objectPosition: slide.position || '80% center' }}
                  loading={idx === 0 ? 'eager' : 'lazy'}
                />

                {/* Responsive Left-to-Right Warm Scrim Overlay (YojnaSetu #FFFBF0 Palette) */}
                <div className="hero-gradient-scrim" aria-hidden="true" />

                {/* Left Content Container strictly above overlay (z-20) */}
                <div className="absolute inset-0 flex items-center z-20 pointer-events-none">
                  <div className="w-full pl-12 sm:pl-16 md:pl-20 lg:pl-24 xl:pl-28 pr-4 sm:pr-8 pointer-events-auto">
                    <div className="max-w-[480px] sm:max-w-[520px] lg:max-w-[540px] space-y-3 sm:space-y-4 text-left">
                      
                      {/* Eyebrow Pill Badge */}
                      <div className="inline-flex items-center gap-2 bg-[#FFF4EC] px-3 py-1 sm:px-3.5 sm:py-1.5 rounded-full border border-[#FFD0CA] shadow-xs">
                        <span className="w-2 h-2 rounded-full bg-[#EA717B] animate-pulse" />
                        <BadgeIcon className="w-3.5 h-3.5 text-[#F7AE56] shrink-0" aria-hidden="true" />
                        <span className="text-[10px] sm:text-xs font-extrabold tracking-wider text-[#4A2525] uppercase">
                          {slide.badgeText}
                        </span>
                      </div>

                      {/* Large Bold Headline with Controlled Line Wrapping */}
                      <h1 className="text-2xl sm:text-4xl lg:text-[44px] font-black text-[#2B1810] leading-[1.12] tracking-tight">
                        {slide.title}
                      </h1>

                      {/* Subtitle */}
                      <p className="text-xs sm:text-sm lg:text-[15px] text-[#6B5550] font-medium leading-relaxed max-w-[480px]">
                        {slide.subtitle}
                      </p>

                      {/* Trust Badges / Feature Chips */}
                      <div className="flex flex-wrap gap-2 pt-0.5">
                        {slide.features.map((feat, fIdx) => (
                          <div
                            key={fIdx}
                            className="inline-flex items-center gap-1.5 bg-white/90 backdrop-blur-xs border border-[#E8D8D2] text-[#3B2522] px-2.5 sm:px-3 py-1 rounded-full text-[11px] sm:text-xs font-semibold shadow-xs"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5 text-[#2E7D32] shrink-0" aria-hidden="true" />
                            <span>{feat}</span>
                          </div>
                        ))}
                      </div>

                      {/* Call to Actions */}
                      <div className="flex flex-wrap items-center gap-2.5 sm:gap-3.5 pt-2 sm:pt-3">
                        <Link
                          to={slide.primaryCtaLink}
                          className="inline-flex items-center justify-center gap-2 px-6 sm:px-7 py-3 rounded-full font-bold text-xs sm:text-sm text-white bg-[#EA717B] hover:bg-[#D65D67] shadow-sm hover:shadow-md transition-all duration-200 transform hover:-translate-y-0.5 active:scale-95"
                        >
                          <Sparkles className="w-4 h-4 text-[#FFF0EE]" aria-hidden="true" />
                          <span>{slide.primaryCtaText}</span>
                          <ArrowRight className="w-4 h-4" />
                        </Link>

                        <Link
                          to={slide.secondaryCtaLink}
                          className="inline-flex items-center justify-center gap-2 px-5 sm:px-6 py-3 rounded-full bg-white hover:bg-[#FFF4EC] text-[#3B2522] font-bold text-xs sm:text-sm border border-[#E8D8D2] shadow-xs hover:border-[#D9C4BC] transition-all duration-200 transform hover:-translate-y-0.5"
                        >
                          <Search className="w-4 h-4 text-[#765E59]" aria-hidden="true" />
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

        {/* LEFT NAV ARROW */}
        <button
          type="button"
          onClick={handlePrev}
          aria-label={t('home.hero.prevSlide', 'Previous slide')}
          className="absolute left-2 sm:left-4 top-1/2 -translate-y-1/2 z-30 w-9 h-9 sm:w-11 sm:h-11 rounded-full bg-[#3B2522]/80 hover:bg-[#EA717B] text-white flex items-center justify-center shadow-md transition-all duration-200 active:scale-90 hover:scale-105"
        >
          <ChevronLeft className="w-5 h-5 sm:w-6 sm:h-6" />
        </button>

        {/* RIGHT NAV ARROW */}
        <button
          type="button"
          onClick={handleNext}
          aria-label={t('home.hero.nextSlide', 'Next slide')}
          className="absolute right-2 sm:right-4 top-1/2 -translate-y-1/2 z-30 w-9 h-9 sm:w-11 sm:h-11 rounded-full bg-[#3B2522]/80 hover:bg-[#EA717B] text-white flex items-center justify-center shadow-md transition-all duration-200 active:scale-90 hover:scale-105"
        >
          <ChevronRight className="w-5 h-5 sm:w-6 sm:h-6" />
        </button>

        {/* BOTTOM PAGINATION INDICATOR */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-30 flex items-center gap-2 bg-[#2B1810]/80 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-white/20 shadow-sm">
          {slides.map((_, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setActiveSlide(idx)}
              aria-label={t('home.hero.slideIndicator', 'Go to slide {{slide}}', { slide: idx + 1 })}
              className={`h-2 rounded-full transition-all duration-300 ${
                idx === activeSlide
                  ? 'w-6 bg-[#EA717B]'
                  : 'w-2 bg-white/50 hover:bg-white/80'
              }`}
            />
          ))}
          <span className="text-[11px] font-mono font-bold text-white ml-1">
            0{activeSlide + 1} / 0{totalSlides}
          </span>
        </div>
      </div>
    </div>
  );
};
