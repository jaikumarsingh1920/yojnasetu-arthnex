import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { useTextSize } from '../context/TextSizeContext';
import { SUPPORTED_LANGUAGES } from '../i18n';
import {
  Search,
  Sparkles,
  Calculator,
  ShieldAlert,
  Bookmark,
  LogOut,
  LogIn,
  UserPlus,
  Menu,
  X,
  LayoutDashboard,
  Globe,
  ChevronDown,
  MapPin,
  User,
  ShieldCheck,
  Home,
  BookOpen,
  Info,
  ArrowRight,
  Layers,
  Banknote,
  Shield,
  PhoneCall,
  Check,
  Flame,
  FileText,
} from 'lucide-react';

import { NotificationBell } from './NotificationBell';

// ─────────────────────────────────────────────────────────────
// Real Popular Schemes from the 90-Scheme Database
// ─────────────────────────────────────────────────────────────
const POPULAR_NATIONAL_SCHEMES = [
  {
    id: 'SIH26092-001',
    name: "Prime Minister's Employment Generation Programme (PMEGP)",
    shortName: 'PMEGP Scheme',
    category: 'MSME & Self Employment',
    tag: 'Up to ₹50L Loan + 35% Subsidy',
    query: '/schemes/SIH26092-001',
  },
  {
    id: 'SIH26092-002',
    name: 'Pradhan Mantri Mudra Yojana (PMMY)',
    shortName: 'PM Mudra Yojana',
    category: 'Micro Enterprises & Small Business',
    tag: 'Shishu / Kishore / Tarun up to ₹20L',
    query: '/schemes/SIH26092-002',
  },
  {
    id: 'SIH26092-003',
    name: 'Stand-Up India Scheme',
    shortName: 'Stand-Up India',
    category: 'SC / ST / Women Entrepreneurs',
    tag: 'Greenfield Loans ₹10L - ₹1 Crore',
    query: '/schemes/SIH26092-003',
  },
  {
    id: 'SIH26092-010',
    name: "PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)",
    shortName: 'PM SVANidhi',
    category: 'Urban Street Vendors',
    tag: 'Working Capital ₹10k / ₹20k / ₹50k',
    query: '/schemes/SIH26092-010',
  },
  {
    id: 'SIH26092-012',
    name: 'PM Vishwakarma Scheme',
    shortName: 'PM Vishwakarma',
    category: 'Traditional Artisans & Craftsmen',
    tag: 'Toolkits + ₹3L Loan @ 5% Concession',
    query: '/schemes/SIH26092-012',
  },
  {
    id: 'SIH26092-013',
    name: 'Credit Guarantee Fund Trust for Micro and Small Enterprises (CGTMSE)',
    shortName: 'CGTMSE MSME Guarantee',
    category: 'Credit & Collateral Support',
    tag: 'Collateral-free credit guarantee',
    query: '/schemes/SIH26092-013',
  },
];

export const Navbar: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { user, isAuthenticated, logout, role } = useAuth();
  const { textSize, setTextSize, decreaseText, resetText, increaseText } = useTextSize();
  const navigate = useNavigate();
  const location = useLocation();

  // Navigation UI State
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const [megaMenuOpen, setMegaMenuOpen] = useState(false);
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const [citizenMenuOpen, setCitizenMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [resourcesModalOpen, setResourcesModalOpen] = useState(false);
  const [aboutModalOpen, setAboutModalOpen] = useState(false);

  // Dropdown Refs for Outside Click Handling
  const langMenuRef = useRef<HTMLDivElement>(null);
  const megaMenuRef = useRef<HTMLDivElement>(null);
  const moreMenuRef = useRef<HTMLDivElement>(null);
  const citizenMenuRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLElement>(null);
  const [navHeight, setNavHeight] = useState<number>(72);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setUserMenuOpen(false);
    setMobileMenuOpen(false);
  };

  const handleLanguageChange = (code: string) => {
    i18n.changeLanguage(code);
    setLangMenuOpen(false);
  };

  // Close all menus on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (langMenuRef.current && !langMenuRef.current.contains(target)) {
        setLangMenuOpen(false);
      }
      if (megaMenuRef.current && !megaMenuRef.current.contains(target)) {
        setMegaMenuOpen(false);
      }
      if (moreMenuRef.current && !moreMenuRef.current.contains(target)) {
        setMoreMenuOpen(false);
      }
      if (citizenMenuRef.current && !citizenMenuRef.current.contains(target)) {
        setCitizenMenuOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(target)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard accessibility: Escape key closes all open dropdowns and modals
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setMegaMenuOpen(false);
        setMoreMenuOpen(false);
        setCitizenMenuOpen(false);
        setUserMenuOpen(false);
        setLangMenuOpen(false);
        setMobileMenuOpen(false);
        setResourcesModalOpen(false);
        setAboutModalOpen(false);
      }
    },
    []
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Close all menus on route change
  useEffect(() => {
    setMobileMenuOpen(false);
    setMegaMenuOpen(false);
    setMoreMenuOpen(false);
    setCitizenMenuOpen(false);
    setUserMenuOpen(false);
    setLangMenuOpen(false);
  }, [location.pathname]);

  // Keep track of header height for precise fixed drawer positioning
  useEffect(() => {
    const updateNavHeight = () => {
      if (headerRef.current) {
        setNavHeight(headerRef.current.offsetHeight);
      }
    };
    updateNavHeight();
    window.addEventListener('resize', updateNavHeight);
    return () => window.removeEventListener('resize', updateNavHeight);
  }, []);

  // Prevent background page scrolling while mobile menu drawer is open
  useEffect(() => {
    if (mobileMenuOpen) {
      if (headerRef.current) {
        setNavHeight(headerRef.current.offsetHeight);
      }
      const originalBodyOverflow = document.body.style.overflow;
      const originalHtmlOverflow = document.documentElement.style.overflow;

      document.body.style.overflow = 'hidden';
      document.documentElement.style.overflow = 'hidden';

      // Block touchmove on background to prevent mobile rubber-band scrolling of the document
      const handleTouchMove = (e: TouchEvent) => {
        const drawer = document.getElementById('mobile-navigation-drawer');
        if (!drawer || !drawer.contains(e.target as Node)) {
          if (e.cancelable) {
            e.preventDefault();
          }
        }
      };

      document.addEventListener('touchmove', handleTouchMove, { passive: false });

      return () => {
        document.body.style.overflow = originalBodyOverflow;
        document.documentElement.style.overflow = originalHtmlOverflow;
        document.removeEventListener('touchmove', handleTouchMove);
      };
    } else {
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    }
  }, [mobileMenuOpen]);

  const currentLang = SUPPORTED_LANGUAGES.find((l) => l.code === i18n.language) || SUPPORTED_LANGUAGES[0];

  const isActive = (path: string) => location.pathname === path;
  const isCitizenPathActive = ['/profile', '/dashboard', '/applications', '/saved-schemes'].includes(location.pathname);
  const isSchemesPathActive = location.pathname.startsWith('/schemes');

  return (
    <header ref={headerRef} className="bg-gov-blue text-white shadow-md sticky top-0 z-[100] relative select-none border-b border-slate-800/60 w-full">
      {/* Tri-color National Accent Line */}
      <div className="gov-tricolor-bar" />

      {/* ─────────────────────────────────────────────────────────────
          1. TOP GOVERNMENT HEADER STRIP (Edge-to-Edge Responsive)
      ───────────────────────────────────────────────────────────── */}
      <div className="bg-slate-950/95 w-full px-2.5 sm:px-6 lg:px-8 py-1 sm:py-1.5 text-xs font-medium text-slate-300 flex justify-between items-center border-b border-slate-800/80 gap-1.5">
        
        {/* Left: Emblem Badge & Subtitle */}
        <div className="flex items-center gap-1.5 sm:gap-2.5 min-w-0 shrink">
          <span className="bg-gov-saffron text-white px-1.5 sm:px-2 py-0.5 rounded font-extrabold text-[9px] sm:text-[10px] tracking-wider shadow-xs flex items-center gap-1 shrink-0">
            <ShieldCheck className="w-2.5 h-2.5 sm:w-3 sm:h-3 shrink-0" />
            <span>{t('nav.govIndia', 'GOVT OF INDIA')}</span>
          </span>
          <span className="hidden md:inline font-medium text-slate-300 text-[11px] truncate">
            {t('nav.portalSub', 'National Welfare & Credit Guidance Platform')}
          </span>
          <span className="hidden md:inline text-slate-600">•</span>
          <span className="hidden sm:inline text-slate-400 text-[10px] sm:text-[11px] font-mono shrink-0">yojnasetu.gov.in</span>
        </div>

        {/* Right: Helpline + Accessible Text Size (A- A A+) + 12-Language Dropdown */}
        <div className="flex items-center gap-1 sm:gap-2.5 text-slate-300 shrink-0">
          <a
            href="tel:1800112026"
            className="hidden xl:inline-flex items-center gap-1.5 text-[11px] text-slate-300 hover:text-sky-300 transition"
          >
            <PhoneCall className="w-3 h-3 text-emerald-400 shrink-0" />
            <span>{t('nav.helpline', 'Helpline: 1800–11–2026 (Toll-Free)')}</span>
          </a>

          <span className="hidden xl:inline text-slate-700">|</span>

          {/* Accessible Text Size Control (A- A A+) */}
          <div
            className="flex items-center bg-slate-900/90 border border-slate-700/80 rounded-md sm:rounded-lg p-0.5 gap-0.5 shrink-0"
            role="group"
            aria-label={t('accessibility.textSize', 'Text size')}
          >
            <button
              type="button"
              onClick={decreaseText}
              className={`min-w-[19px] sm:min-w-[22px] h-[19px] sm:h-[21px] px-1 text-[9px] sm:text-[10px] font-bold rounded flex items-center justify-center transition leading-none ${
                textSize === 'small'
                  ? 'bg-sky-600 text-white shadow-xs font-black'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
              title={t('accessibility.decreaseText', 'Decrease text size')}
              aria-label={t('accessibility.decreaseText', 'Decrease text size')}
              aria-pressed={textSize === 'small'}
            >
              A−
            </button>
            <button
              type="button"
              onClick={resetText}
              className={`min-w-[17px] sm:min-w-[20px] h-[19px] sm:h-[21px] px-1 text-[9px] sm:text-[10px] font-bold rounded flex items-center justify-center transition leading-none ${
                textSize === 'default'
                  ? 'bg-sky-600 text-white shadow-xs font-black'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
              title={t('accessibility.defaultText', 'Default text size')}
              aria-label={t('accessibility.defaultText', 'Default text size')}
              aria-pressed={textSize === 'default'}
            >
              A
            </button>
            <button
              type="button"
              onClick={increaseText}
              className={`min-w-[19px] sm:min-w-[22px] h-[19px] sm:h-[21px] px-1 text-[9px] sm:text-[10px] font-bold rounded flex items-center justify-center transition leading-none ${
                textSize === 'large'
                  ? 'bg-sky-600 text-white shadow-xs font-black'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
              title={t('accessibility.increaseText', 'Increase text size')}
              aria-label={t('accessibility.increaseText', 'Increase text size')}
              aria-pressed={textSize === 'large'}
            >
              A+
            </button>
          </div>

          <span className="text-slate-700">|</span>

          {/* Global 12-Language Selector */}
          <div className="relative shrink-0" ref={langMenuRef}>
            <button
              onClick={() => setLangMenuOpen(!langMenuOpen)}
              className="flex items-center gap-1 sm:gap-1.5 bg-slate-800/90 hover:bg-slate-700 text-white px-1.5 sm:px-2.5 py-0.5 sm:py-1 rounded-md sm:rounded-lg text-[10px] sm:text-xs font-semibold transition border border-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-400"
              aria-label={t('nav.language', 'Select Platform Language')}
              aria-expanded={langMenuOpen}
              aria-haspopup="true"
            >
              <Globe className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-sky-400 shrink-0" />
              <span className="hidden sm:inline truncate max-w-[80px]">{currentLang.nativeName}</span>
              <span className="sm:hidden font-mono text-[9px] uppercase">{currentLang.code}</span>
              <ChevronDown className={`w-2.5 h-2.5 sm:w-3 sm:h-3 text-slate-400 transition-transform shrink-0 ${langMenuOpen ? 'rotate-180' : ''}`} />
            </button>

            {langMenuOpen && (
              <div
                className="absolute right-0 mt-1.5 w-52 max-w-[calc(100vw-1.5rem)] bg-slate-900 border border-slate-700 rounded-xl shadow-2xl py-1.5 z-[120] max-h-80 overflow-y-auto divide-y divide-slate-800/60 animate-in fade-in slide-in-from-top-1 duration-150"
                role="menu"
              >
                <div className="px-3 py-1 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                  Select Official Language (12)
                </div>
                <div className="py-1">
                  {SUPPORTED_LANGUAGES.map((lang) => {
                    const isSelected = i18n.language === lang.code;
                    return (
                      <button
                        key={lang.code}
                        onClick={() => handleLanguageChange(lang.code)}
                        className={`w-full text-left px-3.5 py-2 text-xs flex items-center justify-between transition ${
                          isSelected
                            ? 'bg-sky-800/80 text-sky-100 font-bold'
                            : 'text-slate-200 hover:bg-slate-800 hover:text-white'
                        }`}
                        role="menuitem"
                      >
                        <div className="flex items-center gap-2">
                          {isSelected && <Check className="w-3.5 h-3.5 text-sky-400 shrink-0" />}
                          <span className={isSelected ? 'font-bold' : 'font-medium'}>{lang.nativeName}</span>
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono uppercase">{lang.code}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          2. MAIN NAVIGATION BAR (Responsive Tiers: Mobile, Tablet, Desktop)
      ───────────────────────────────────────────────────────────── */}
      <div className="w-full px-2.5 sm:px-6 lg:px-8">
        <div className="flex justify-between h-13 sm:h-15 items-center gap-1.5 sm:gap-3 w-full">
          
          {/* Brand Identity Area (Pinned completely to the Left with shrink-0) */}
          <Link
            to="/"
            className="flex items-center gap-1.5 sm:gap-2.5 shrink-0 group focus:outline-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/80 rounded-xl p-1 -m-1"
            aria-label={t('nav.homeAria', 'YojnaSetu Home')}
          >
            <img
              src="/logo.png"
              alt="YojnaSetu Emblem"
              className="w-7 h-7 sm:w-8 sm:h-8 md:w-9 md:h-9 rounded-lg sm:rounded-xl object-contain bg-slate-950 p-1 border border-slate-700/80 shadow-md transition group-hover:scale-105 shrink-0"
            />
            <div className="flex flex-col text-left">
              <div className="flex items-center gap-1 sm:gap-1.5">
                <span className="font-extrabold text-base sm:text-lg md:text-xl tracking-tight text-white group-hover:text-sky-300 transition leading-tight">
                  {t('nav.title', 'YojnaSetu')}
                </span>
                <span className="hidden min-[375px]:inline-block text-[8px] sm:text-[9px] bg-sky-600/90 text-white font-extrabold px-1 sm:px-1.5 py-0.2 rounded uppercase tracking-wider shadow-xs">
                  OFFICIAL
                </span>
              </div>
              <p className="hidden sm:block text-[9px] sm:text-[10px] text-slate-300 font-medium tracking-tight leading-tight">
                {t('nav.subtitle', 'Government Citizen Platform')}
              </p>
            </div>
          </Link>

          {/* ─────────────────────────────────────────────────────────────
              3. DESKTOP FULL NAVIGATION (Screen width >= 1200px / xl)
          ───────────────────────────────────────────────────────────── */}
          <nav className="hidden xl:flex items-center gap-1 2xl:gap-1.5 ml-2">
            {/* Home Link */}
            <Link
              to="/"
              className={`px-2 py-1.5 rounded-xl text-xs 2xl:text-sm font-semibold transition whitespace-nowrap flex items-center gap-1.5 ${
                isActive('/')
                  ? 'bg-sky-700 text-white shadow-sm'
                  : 'text-slate-200 hover:bg-gov-navy/80 hover:text-white'
              }`}
            >
              <Home className="w-3.5 h-3.5 text-sky-400 shrink-0" />
              <span>{t('nav.home', 'Home')}</span>
            </Link>

            {/* Explore Schemes with Interactive Mega Menu */}
            <div className="relative" ref={megaMenuRef}>
              <button
                type="button"
                onClick={() => setMegaMenuOpen(!megaMenuOpen)}
                className={`px-2 py-1.5 rounded-xl text-xs 2xl:text-sm font-semibold transition whitespace-nowrap flex items-center gap-1.5 ${
                  isSchemesPathActive || megaMenuOpen
                    ? 'bg-sky-700 text-white shadow-sm'
                    : 'text-slate-200 hover:bg-gov-navy/80 hover:text-white'
                }`}
                aria-expanded={megaMenuOpen}
                aria-haspopup="true"
              >
                <Search className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                <span>{t('nav.schemes', 'Explore Schemes')}</span>
                <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${megaMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Mega Menu Dropdown */}
              {megaMenuOpen && (
                <div
                  className="absolute left-0 mt-2 w-[min(90vw,780px)] max-w-[calc(100vw-2rem)] bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl p-4 sm:p-5 z-[120] text-slate-200 animate-in fade-in slide-in-from-top-2 duration-150 max-h-[80vh] overflow-y-auto"
                  role="region"
                  aria-label={t('nav.schemesAria', 'Schemes Directory Mega Menu')}
                >
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
                    
                    {/* Column 1: Browse Schemes */}
                    <div className="md:col-span-3 space-y-2 md:border-r border-slate-800 md:pr-3">
                      <div className="text-[10px] font-extrabold uppercase text-sky-400 tracking-wider flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 shrink-0" />
                        {t('nav.browseSchemes', 'Browse Schemes')}
                      </div>
                      <div className="space-y-1">
                        <Link
                          to="/schemes"
                          onClick={() => setMegaMenuOpen(false)}
                          className="block px-2 py-1 rounded-lg text-xs font-semibold hover:bg-slate-800 hover:text-sky-300 transition"
                        >
                          {t('nav.allSchemes', 'All Schemes (90)')}
                        </Link>
                        <Link
                          to="/schemes?sort_by=ministry"
                          onClick={() => setMegaMenuOpen(false)}
                          className="block px-2 py-1 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition"
                        >
                          {t('nav.byMinistry', 'By Ministry')}
                        </Link>
                        <Link
                          to="/schemes?sort_by=category"
                          onClick={() => setMegaMenuOpen(false)}
                          className="block px-2 py-1 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition"
                        >
                          {t('nav.byCategory', 'By Category')}
                        </Link>
                        <Link
                          to="/schemes?sort_by=sector"
                          onClick={() => setMegaMenuOpen(false)}
                          className="block px-2 py-1 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition"
                        >
                          {t('nav.bySector', 'By Sector')}
                        </Link>
                        <Link
                          to="/schemes?sort_by=state"
                          onClick={() => setMegaMenuOpen(false)}
                          className="block px-2 py-1 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition"
                        >
                          {t('nav.byState', 'By State Restrictions')}
                        </Link>
                      </div>
                    </div>

                    {/* Column 2: Financial Benefit Types */}
                    <div className="md:col-span-4 space-y-2 md:border-r border-slate-800 md:pr-3">
                      <div className="text-[10px] font-extrabold uppercase text-emerald-400 tracking-wider flex items-center gap-1.5">
                        <Banknote className="w-3.5 h-3.5 shrink-0" />
                        {t('nav.financialType', 'Financial Type')}
                      </div>
                      <div className="space-y-1">
                        <Link
                          to="/schemes?financial_type=LOAN"
                          onClick={() => setMegaMenuOpen(false)}
                          className="flex items-center justify-between px-2 py-1 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-emerald-300 transition"
                        >
                          <span>{t('nav.loanCreditSchemes', 'Loan / Credit Schemes')}</span>
                          <span className="text-[9px] bg-slate-800 px-1 py-0.5 rounded text-slate-400 font-mono">PMMY</span>
                        </Link>
                        <Link
                          to="/schemes?financial_type=SUBSIDY"
                          onClick={() => setMegaMenuOpen(false)}
                          className="flex items-center justify-between px-2 py-1 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-emerald-300 transition"
                        >
                          <span>{t('nav.subsidyGrant', 'Subsidy / Capital Grant')}</span>
                          <span className="text-[9px] bg-slate-800 px-1 py-0.5 rounded text-slate-400 font-mono">PMEGP</span>
                        </Link>
                        <Link
                          to="/schemes?financial_type=SCHOLARSHIP"
                          onClick={() => setMegaMenuOpen(false)}
                          className="flex items-center justify-between px-2 py-1 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-emerald-300 transition"
                        >
                          <span>{t('nav.scholarshipEdu', 'Scholarship / Education')}</span>
                          <span className="text-[9px] bg-slate-800 px-1 py-0.5 rounded text-slate-400 font-mono">NSP</span>
                        </Link>
                        <Link
                          to="/schemes?financial_type=TRAINING"
                          onClick={() => setMegaMenuOpen(false)}
                          className="flex items-center justify-between px-2 py-1 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-emerald-300 transition"
                        >
                          <span>{t('nav.skillTraining', 'Skill & Training Grants')}</span>
                          <span className="text-[9px] bg-slate-800 px-1 py-0.5 rounded text-slate-400 font-mono">PMKVY</span>
                        </Link>
                        <Link
                          to="/schemes?financial_type=GUARANTEE"
                          onClick={() => setMegaMenuOpen(false)}
                          className="flex items-center justify-between px-2 py-1 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-emerald-300 transition"
                        >
                          <span>{t('nav.creditGuarantee', 'Credit Guarantee Cover')}</span>
                          <span className="text-[9px] bg-slate-800 px-1 py-0.5 rounded text-slate-400 font-mono">CGTMSE</span>
                        </Link>
                      </div>
                    </div>

                    {/* Column 3: Popular Schemes */}
                    <div className="md:col-span-5 space-y-2">
                      <div className="text-[10px] font-extrabold uppercase text-gov-saffron tracking-wider flex items-center gap-1.5">
                        <Flame className="w-3.5 h-3.5 text-gov-saffron shrink-0" />
                        {t('nav.popularSearches', 'Popular Searches')}
                      </div>
                      <div className="space-y-1">
                        {POPULAR_NATIONAL_SCHEMES.slice(0, 4).map((scheme) => (
                          <Link
                            key={scheme.id}
                            to={scheme.query}
                            onClick={() => setMegaMenuOpen(false)}
                            className="block p-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-transparent hover:border-slate-600 transition group"
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-white group-hover:text-sky-300">
                                {scheme.shortName}
                              </span>
                              <span className="text-[9px] text-slate-400 font-mono font-bold">
                                {scheme.id}
                              </span>
                            </div>
                            <p className="text-[9px] text-slate-300 line-clamp-1 mt-0.5">
                              {scheme.tag}
                            </p>
                          </Link>
                        ))}
                      </div>
                    </div>

                  </div>

                  {/* Mega Menu Footer CTAs */}
                  <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between gap-2 text-xs">
                    <Link
                      to="/schemes"
                      onClick={() => setMegaMenuOpen(false)}
                      className="font-bold text-sky-400 hover:text-sky-300 flex items-center gap-1"
                    >
                      {t('nav.advancedSearch', 'Advanced Scheme Search')} <ArrowRight className="w-3.5 h-3.5" />
                    </Link>

                    <Link
                      to="/recommendations"
                      onClick={() => setMegaMenuOpen(false)}
                      className="bg-gov-saffron hover:bg-orange-600 text-white font-bold px-3 py-1.5 rounded-xl shadow transition flex items-center gap-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{t('nav.findMatchingCta', 'Find Matching Schemes →')}</span>
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Smart Matching Link (Core Highlight) */}
            <Link
              to="/recommendations"
              className={`px-2 py-1.5 rounded-xl text-xs 2xl:text-sm font-semibold transition whitespace-nowrap flex items-center gap-1.5 ${
                isActive('/recommendations')
                  ? 'bg-gov-saffron text-white shadow-sm font-bold'
                  : 'text-amber-300 hover:bg-gov-navy/80 hover:text-white'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-gov-saffron shrink-0" />
              <span>{t('nav.recommendations', 'Smart Matching')}</span>
            </Link>

            {/* Financial Calculator Link */}
            <Link
              to="/calculator"
              className={`px-2 py-1.5 rounded-xl text-xs 2xl:text-sm font-semibold transition whitespace-nowrap flex items-center gap-1.5 ${
                isActive('/calculator')
                  ? 'bg-sky-700 text-white shadow-sm'
                  : 'text-slate-200 hover:bg-gov-navy/80 hover:text-white'
              }`}
            >
              <Calculator className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>{t('nav.calculator', 'Calculator')}</span>
            </Link>

            {/* Find Nearby Partner Link */}
            <Link
              to="/channel-partners"
              className={`px-2 py-1.5 rounded-xl text-xs 2xl:text-sm font-semibold transition whitespace-nowrap flex items-center gap-1.5 ${
                isActive('/channel-partners')
                  ? 'bg-sky-700 text-white shadow-sm'
                  : 'text-slate-200 hover:bg-gov-navy/80 hover:text-white'
              }`}
            >
              <MapPin className="w-3.5 h-3.5 text-rose-400 shrink-0" />
              <span>{t('nav.partnerLocator', 'Find Partner')}</span>
            </Link>

            {/* Compiled More & Info Dropdown */}
            <div className="relative" ref={moreMenuRef}>
              <button
                type="button"
                onClick={() => setMoreMenuOpen(!moreMenuOpen)}
                className={`px-2 py-1.5 rounded-xl text-xs 2xl:text-sm font-semibold transition whitespace-nowrap flex items-center gap-1.5 ${
                  moreMenuOpen
                    ? 'bg-sky-700 text-white shadow-sm'
                    : 'text-slate-200 hover:bg-gov-navy/80 hover:text-white'
                }`}
                aria-expanded={moreMenuOpen}
                aria-haspopup="true"
              >
                <BookOpen className="w-3.5 h-3.5 text-amber-300 shrink-0" />
                <span>{t('nav.more', 'More')}</span>
                <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${moreMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {moreMenuOpen && (
                <div
                  className="absolute left-0 mt-2 w-64 bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl py-1.5 z-[120] animate-in fade-in slide-in-from-top-2 duration-150 divide-y divide-slate-800/80"
                  role="menu"
                >
                  <div className="px-3.5 py-1 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                    {t('nav.infoHelp', 'Information & Help')}
                  </div>

                  <div className="py-1">
                    <button
                      type="button"
                      onClick={() => {
                        setResourcesModalOpen(true);
                        setMoreMenuOpen(false);
                      }}
                      className="w-full text-left px-3.5 py-2 text-xs font-semibold flex items-center gap-2.5 text-slate-200 hover:bg-slate-800 hover:text-white transition"
                      role="menuitem"
                    >
                      <div className="p-1.5 rounded-lg bg-amber-950 text-amber-400 border border-amber-800/60 shrink-0">
                        <BookOpen className="w-3.5 h-3.5" />
                      </div>
                      <div>
                        <div className="leading-none text-white font-bold">{t('nav.resourcesGuidelines', 'Resources & Guidelines')}</div>
                        <span className="text-[10px] text-slate-400 font-normal">{t('nav.resourcesDesc', 'Gazette rules, Helpline')}</span>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setAboutModalOpen(true);
                        setMoreMenuOpen(false);
                      }}
                      className="w-full text-left px-3.5 py-2 text-xs font-semibold flex items-center gap-2.5 text-slate-200 hover:bg-slate-800 hover:text-white transition"
                      role="menuitem"
                    >
                      <div className="p-1.5 rounded-lg bg-sky-950 text-sky-400 border border-sky-800/60 shrink-0">
                        <Info className="w-3.5 h-3.5" />
                      </div>
                      <div>
                        <div className="leading-none text-white font-bold">{t('nav.aboutYojnaSetu', 'About YojnaSetu')}</div>
                        <span className="text-[10px] text-slate-400 font-normal">{t('nav.aboutDesc', 'Zero PII Policy & Engine')}</span>
                      </div>
                    </button>
                  </div>

                  {/* Role-Specific Admin Link */}
                  {isAuthenticated && role === 'SYSTEM_ADMIN' && (
                    <div className="py-1">
                      <Link
                        to="/admin"
                        onClick={() => setMoreMenuOpen(false)}
                        className={`px-3.5 py-2 text-xs font-semibold flex items-center gap-2.5 transition ${
                          isActive('/admin') ? 'bg-rose-900/60 text-rose-200' : 'text-slate-200 hover:bg-slate-800 hover:text-white'
                        }`}
                        role="menuitem"
                      >
                        <div className="p-1.5 rounded-lg bg-rose-950 text-rose-400 border border-rose-800/60 shrink-0">
                          <ShieldAlert className="w-3.5 h-3.5" />
                        </div>
                        <div>
                          <div className="leading-none text-rose-300 font-bold">{t('nav.adminControlCenter', 'Admin Control Center')}</div>
                          <span className="text-[10px] text-slate-400 font-normal">{t('nav.adminAuditDesc', 'Audit Logs & Governance')}</span>
                        </div>
                      </Link>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Citizen Hub (if Beneficiary) */}
            {isAuthenticated && role === 'BENEFICIARY' && (
              <div className="relative" ref={citizenMenuRef}>
                <button
                  type="button"
                  onClick={() => setCitizenMenuOpen(!citizenMenuOpen)}
                  className={`px-2 py-1.5 rounded-xl text-xs 2xl:text-sm font-semibold transition whitespace-nowrap flex items-center gap-1.5 ${
                    isCitizenPathActive || citizenMenuOpen
                      ? 'bg-gov-navy text-white ring-1 ring-sky-400 shadow-sm'
                      : 'text-slate-200 hover:bg-gov-navy/80 hover:text-white'
                  }`}
                  aria-expanded={citizenMenuOpen}
                  aria-haspopup="true"
                >
                  <User className="w-3.5 h-3.5 text-amber-300 shrink-0" />
                  <span>{t('nav.citizenHub', 'Citizen Hub')}</span>
                  <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${citizenMenuOpen ? 'rotate-180' : ''}`} />
                </button>

                {citizenMenuOpen && (
                  <div
                    className="absolute left-0 mt-2 w-60 bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl py-1.5 z-[120] animate-in fade-in slide-in-from-top-2 duration-150 divide-y divide-slate-800/80"
                    role="menu"
                  >
                    <div className="px-3 py-1 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                      {t('nav.beneficiaryServices', 'Beneficiary Services')}
                    </div>
                    
                    <div className="py-1">
                      <Link
                        to="/profile"
                        onClick={() => setCitizenMenuOpen(false)}
                        className={`px-3 py-1.5 text-xs font-semibold flex items-center gap-2 transition ${
                          isActive('/profile') ? 'bg-sky-800 text-white font-bold' : 'text-slate-200 hover:bg-slate-800 hover:text-white'
                        }`}
                        role="menuitem"
                      >
                        <User className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                        <span>{t('nav.profile', 'My Profile')}</span>
                      </Link>

                      <Link
                        to="/dashboard"
                        onClick={() => setCitizenMenuOpen(false)}
                        className={`px-3 py-1.5 text-xs font-semibold flex items-center gap-2 transition ${
                          isActive('/dashboard') ? 'bg-sky-800 text-white font-bold' : 'text-slate-200 hover:bg-slate-800 hover:text-white'
                        }`}
                        role="menuitem"
                      >
                        <LayoutDashboard className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                        <span>{t('nav.dashboard', 'Citizen Dashboard')}</span>
                      </Link>

                      <Link
                        to="/applications"
                        onClick={() => setCitizenMenuOpen(false)}
                        className={`px-3 py-1.5 text-xs font-semibold flex items-center gap-2 transition ${
                          isActive('/applications') ? 'bg-sky-800 text-white font-bold' : 'text-slate-200 hover:bg-slate-800 hover:text-white'
                        }`}
                        role="menuitem"
                      >
                        <FileText className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        <span>{t('nav.applications', 'Applications & Guidance')}</span>
                      </Link>

                      <Link
                        to="/saved-schemes"
                        onClick={() => setCitizenMenuOpen(false)}
                        className={`px-3 py-1.5 text-xs font-semibold flex items-center gap-2 transition ${
                          isActive('/saved-schemes') ? 'bg-sky-800 text-white font-bold' : 'text-slate-200 hover:bg-slate-800 hover:text-white'
                        }`}
                        role="menuitem"
                      >
                        <Bookmark className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                        <span>{t('nav.savedSchemes', 'Saved Schemes')}</span>
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            )}
          </nav>

          {/* ─────────────────────────────────────────────────────────────
              4. TABLET COMPACT TIER (768px – 1199px / md & lg)
          ───────────────────────────────────────────────────────────── */}
          <div className="hidden md:flex xl:hidden items-center gap-1.5">
            {/* Direct Smart Matching Core Highlight */}
            <Link
              to="/recommendations"
              className="bg-gov-saffron hover:bg-orange-600 text-white text-xs font-bold px-2.5 py-1.5 rounded-xl shadow-xs transition flex items-center gap-1.5 shrink-0"
            >
              <Sparkles className="w-3.5 h-3.5 shrink-0" />
              <span>{t('nav.recommendations', 'Smart Matching')}</span>
            </Link>

            {/* Direct Schemes Link */}
            <Link
              to="/schemes"
              className={`px-2 py-1.5 rounded-xl text-xs font-semibold transition whitespace-nowrap flex items-center gap-1 ${
                isSchemesPathActive ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-gov-navy/80'
              }`}
            >
              <Search className="w-3.5 h-3.5 text-sky-400 shrink-0" />
              <span className="hidden lg:inline">{t('nav.schemes', 'Explore Schemes')}</span>
              <span className="lg:hidden">Schemes</span>
            </Link>

            {/* Direct Calculator Link (Visible on lg >= 1024px) */}
            <Link
              to="/calculator"
              className={`hidden lg:flex px-2 py-1.5 rounded-xl text-xs font-semibold transition whitespace-nowrap items-center gap-1 ${
                isActive('/calculator') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-gov-navy/80'
              }`}
            >
              <Calculator className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>{t('nav.calculator', 'Calculator')}</span>
            </Link>
          </div>

          {/* ─────────────────────────────────────────────────────────────
              5. RIGHT-SIDE ACTIONS & AUTH AREA
          ───────────────────────────────────────────────────────────── */}
          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0 ml-auto">
            {/* Authenticated State */}
            {isAuthenticated && user ? (
              <div className="flex items-center gap-1.5 sm:gap-2">
                <NotificationBell />

                {/* User Menu Dropdown (Desktop & Tablet) */}
                <div className="relative hidden md:block" ref={userMenuRef}>
                  <button
                    type="button"
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center gap-1.5 bg-gov-navy/90 hover:bg-slate-800 px-2 py-1 sm:px-2.5 sm:py-1.5 rounded-xl border border-slate-700/90 transition shadow-xs focus:outline-none focus:ring-2 focus:ring-sky-400"
                    aria-expanded={userMenuOpen}
                    aria-haspopup="true"
                  >
                    <div className="w-6 h-6 sm:w-7 sm:h-7 rounded-full bg-slate-800 border border-slate-600 flex items-center justify-center text-sky-400 shrink-0 font-bold text-xs">
                      {user.full_name ? user.full_name.charAt(0).toUpperCase() : <User className="w-3.5 h-3.5" />}
                    </div>
                    <div className="text-left hidden 2xl:block">
                      <p className="text-xs font-bold text-white max-w-[120px] truncate leading-tight">
                        {user.full_name || user.email || user.phone}
                      </p>
                    </div>
                    <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
                  </button>

                  {userMenuOpen && (
                    <div
                      className="absolute right-0 mt-2 w-56 bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl py-1.5 z-[120] animate-in fade-in slide-in-from-top-2 duration-150 divide-y divide-slate-800"
                      role="menu"
                    >
                      <div className="px-3.5 py-1.5 text-xs">
                        <p className="font-bold text-white truncate">{user.email || user.phone}</p>
                        <span className="text-[9px] bg-sky-900/80 text-sky-200 px-1.5 py-0.5 rounded font-mono uppercase font-bold">
                          {user.role}
                        </span>
                      </div>

                      {role === 'BENEFICIARY' && (
                        <div className="py-1">
                          <Link
                            to="/profile"
                            onClick={() => setUserMenuOpen(false)}
                            className="flex items-center gap-2 px-3.5 py-1.5 text-xs text-slate-200 hover:bg-slate-800 hover:text-white transition"
                            role="menuitem"
                          >
                            <User className="w-3.5 h-3.5 text-amber-400" />
                            <span>{t('nav.profile', 'My Profile')}</span>
                          </Link>
                          <Link
                            to="/dashboard"
                            onClick={() => setUserMenuOpen(false)}
                            className="flex items-center gap-2 px-3.5 py-1.5 text-xs text-slate-200 hover:bg-slate-800 hover:text-white transition"
                            role="menuitem"
                          >
                            <LayoutDashboard className="w-3.5 h-3.5 text-sky-400" />
                            <span>{t('nav.dashboard', 'Citizen Dashboard')}</span>
                          </Link>
                        </div>
                      )}

                      {role === 'SYSTEM_ADMIN' && (
                        <div className="py-1">
                          <Link
                            to="/admin"
                            onClick={() => setUserMenuOpen(false)}
                            className="flex items-center gap-2 px-3.5 py-1.5 text-xs text-rose-200 hover:bg-rose-950/60 transition"
                            role="menuitem"
                          >
                            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                            <span>{t('nav.adminControlCenter', 'Admin Control')}</span>
                          </Link>
                        </div>
                      )}

                      <div className="py-1">
                        <button
                          type="button"
                          onClick={handleLogout}
                          className="w-full text-left flex items-center gap-2 px-3.5 py-1.5 text-xs text-rose-400 hover:bg-rose-950/70 hover:text-rose-200 transition font-bold"
                          role="menuitem"
                        >
                          <LogOut className="w-3.5 h-3.5" />
                          <span>{t('nav.logout', 'Sign Out')}</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* Guest Auth Buttons (Desktop & Tablet) */
              <div className="hidden md:flex items-center gap-1.5 sm:gap-2">
                <Link
                  to="/login"
                  className="px-2.5 sm:px-3 py-1.5 text-xs font-bold text-white bg-gov-navy hover:bg-slate-800 rounded-xl border border-slate-700 transition flex items-center gap-1 shadow-xs whitespace-nowrap"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span>{t('nav.login', 'Sign In')}</span>
                </Link>
                <Link
                  to="/register"
                  className="hidden lg:flex px-3 py-1.5 text-xs font-bold text-white bg-gov-saffron hover:bg-orange-600 rounded-xl shadow-md transition items-center gap-1 whitespace-nowrap"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>{t('nav.register', 'Register')}</span>
                </Link>
              </div>
            )}

            {/* Mobile Quick Action for Unauthenticated Users (>= 360px) */}
            {!isAuthenticated && (
              <Link
                to="/recommendations"
                className="hidden min-[360px]:flex md:hidden items-center gap-1 bg-gov-saffron hover:bg-orange-600 text-white px-2 py-1 rounded-lg text-[11px] font-bold shadow-xs shrink-0"
              >
                <Sparkles className="w-3 h-3 shrink-0" />
                <span>Match</span>
              </Link>
            )}

            {/* ─────────────────────────────────────────────────────────────
                6. MOBILE & TABLET HAMBURGER BUTTON (Visible < 1200px / xl)
            ───────────────────────────────────────────────────────────── */}
            <div className="xl:hidden flex items-center">
              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-xl text-slate-200 hover:text-white bg-slate-900/90 hover:bg-slate-800 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-400 shrink-0 min-h-[44px] min-w-[44px] flex items-center justify-center transition"
                aria-label={t('nav.toggleMobileNav', 'Toggle mobile navigation menu')}
                aria-expanded={mobileMenuOpen}
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          7. RESPONSIVE MOBILE & TABLET DRAWER
      ───────────────────────────────────────────────────────────── */}
      {mobileMenuOpen && (
        <>
          {/* Full viewport backdrop behind mobile drawer - fixed to viewport */}
          <div
            className="fixed inset-0 bg-slate-950/70 backdrop-blur-xs z-[99] xl:hidden pointer-events-auto touch-none"
            style={{ top: `${navHeight}px` }}
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true"
          />

          {/* Mobile navigation drawer - FIXED relative to viewport */}
          <div
            id="mobile-navigation-drawer"
            className="xl:hidden fixed left-0 right-0 w-full bg-slate-950/98 backdrop-blur-xl px-3 sm:px-6 pt-3 pb-6 border-t border-slate-800/90 space-y-3.5 overflow-y-auto overscroll-contain shadow-2xl z-[100] animate-in slide-in-from-top-1 duration-150"
            style={{
              top: `${navHeight}px`,
              maxHeight: `calc(100dvh - ${navHeight}px)`,
              height: 'auto'
            }}
          >
          
          {/* Top Primary Smart Matching Feature Card */}
          <Link
            to="/recommendations"
            onClick={() => setMobileMenuOpen(false)}
            className="block p-3 rounded-2xl bg-gradient-to-r from-gov-saffron via-orange-500 to-amber-600 text-white shadow-lg border border-orange-400/40 hover:brightness-110 transition"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-white/20 text-white">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="font-extrabold text-xs sm:text-sm">{t('nav.findMatchingCta', 'Find Matching Schemes (AI Smart Match)')}</h4>
                  <p className="text-[10px] text-white/85">Instant personalized eligibility & fit analysis</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-white shrink-0" />
            </div>
          </Link>

          {/* Public Navigation */}
          <div className="space-y-1">
            <span className="px-3 text-[10px] font-extrabold uppercase text-slate-500 tracking-wider">
              {t('nav.publicNav', 'Public Navigation')}
            </span>
            <Link
              to="/"
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
                isActive('/') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-slate-800'
              }`}
            >
              <Home className="w-4 h-4 text-sky-400 shrink-0" />
              <span>{t('nav.home', 'Home')}</span>
            </Link>
            <Link
              to="/schemes"
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
                isActive('/schemes') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-slate-800'
              }`}
            >
              <Search className="w-4 h-4 text-sky-400 shrink-0" />
              <span>{t('nav.schemes', 'Explore Schemes (90 Programs)')}</span>
            </Link>
            <Link
              to="/calculator"
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
                isActive('/calculator') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-slate-800'
              }`}
            >
              <Calculator className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{t('nav.calculator', 'Financial Calculator & EMI')}</span>
            </Link>
            <Link
              to="/channel-partners"
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
                isActive('/channel-partners') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-slate-800'
              }`}
            >
              <MapPin className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{t('nav.partnerLocator', 'Find Nearby Partner Branch')}</span>
            </Link>
          </div>

          {/* Citizen Services (Authenticated Beneficiary) */}
          {isAuthenticated && role === 'BENEFICIARY' && (
            <div className="pt-2 border-t border-slate-800 space-y-1">
              <span className="px-3 text-[10px] font-extrabold uppercase text-amber-400 tracking-wider">
                {t('nav.citizenAccount', 'Citizen Account')}
              </span>
              <Link
                to="/profile"
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
                  isActive('/profile') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-slate-800'
                }`}
              >
                <User className="w-4 h-4 text-amber-400 shrink-0" />
                <span>{t('nav.profile', 'My Profile')}</span>
              </Link>
              <Link
                to="/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
                  isActive('/dashboard') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-slate-800'
                }`}
              >
                <LayoutDashboard className="w-4 h-4 text-sky-400 shrink-0" />
                <span>{t('nav.dashboard', 'Citizen Dashboard')}</span>
              </Link>
              <Link
                to="/applications"
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
                  isActive('/applications') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-slate-800'
                }`}
              >
                <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{t('nav.applications', 'Applications & Guidance')}</span>
              </Link>
              <Link
                to="/saved-schemes"
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold transition ${
                  isActive('/saved-schemes') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-slate-800'
                }`}
              >
                <Bookmark className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{t('nav.savedSchemes', 'Saved Schemes')}</span>
              </Link>
            </div>
          )}

          {/* System Governance (Authenticated Admin) */}
          {isAuthenticated && role === 'SYSTEM_ADMIN' && (
            <div className="pt-2 border-t border-slate-800 space-y-1">
              <span className="px-3 text-[10px] font-extrabold uppercase text-rose-400 tracking-wider">
                {t('nav.adminControlCenter', 'Admin Control Center')}
              </span>
              <Link
                to="/admin"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold text-rose-300 hover:bg-rose-900/60 transition"
              >
                <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{t('nav.adminControlCenter', 'Admin Governance & Audit')}</span>
              </Link>
            </div>
          )}

          {/* Resources & Information */}
          <div className="pt-2 border-t border-slate-800 space-y-1">
            <span className="px-3 text-[10px] font-extrabold uppercase text-slate-500 tracking-wider">
              {t('nav.infoHelp', 'Information & Help')}
            </span>
            <button
              type="button"
              onClick={() => {
                setResourcesModalOpen(true);
                setMobileMenuOpen(false);
              }}
              className="w-full text-left flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold text-slate-200 hover:bg-slate-800 transition"
            >
              <BookOpen className="w-4 h-4 text-amber-300 shrink-0" />
              <span>{t('nav.resourcesGuidelines', 'Resources & Guidelines')}</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setAboutModalOpen(true);
                setMobileMenuOpen(false);
              }}
              className="w-full text-left flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold text-slate-200 hover:bg-slate-800 transition"
            >
              <Info className="w-4 h-4 text-sky-400 shrink-0" />
              <span>{t('nav.aboutYojnaSetu', 'About YojnaSetu (Zero PII Policy)')}</span>
            </button>
          </div>

          {/* Mobile Text Size Control */}
          <div className="pt-2 border-t border-slate-800 space-y-2">
            <span className="px-3 text-[10px] font-extrabold uppercase text-slate-400 tracking-wider flex items-center justify-between">
              <span>{t('accessibility.textSize', 'Text size')}</span>
              <span className="font-mono text-sky-400 uppercase text-[9px]">{textSize}</span>
            </span>
            <div className="grid grid-cols-3 gap-2 px-1">
              <button
                type="button"
                onClick={() => setTextSize('small')}
                className={`py-2 rounded-xl text-xs font-bold border transition flex items-center justify-center gap-1 ${
                  textSize === 'small'
                    ? 'bg-sky-600 text-white border-sky-400 shadow-sm'
                    : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800'
                }`}
                aria-label={t('accessibility.decreaseText', 'Decrease text size')}
                aria-pressed={textSize === 'small'}
              >
                <span>A−</span>
                <span className="text-[10px] font-medium text-slate-200">({t('accessibility.decreaseText', 'Small')})</span>
              </button>
              <button
                type="button"
                onClick={() => setTextSize('default')}
                className={`py-2 rounded-xl text-xs font-bold border transition flex items-center justify-center gap-1 ${
                  textSize === 'default'
                    ? 'bg-sky-600 text-white border-sky-400 shadow-sm'
                    : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800'
                }`}
                aria-label={t('accessibility.defaultText', 'Default text size')}
                aria-pressed={textSize === 'default'}
              >
                <span>A</span>
                <span className="text-[10px] font-medium text-slate-200">({t('accessibility.defaultText', 'Default')})</span>
              </button>
              <button
                type="button"
                onClick={() => setTextSize('large')}
                className={`py-2 rounded-xl text-xs font-bold border transition flex items-center justify-center gap-1 ${
                  textSize === 'large'
                    ? 'bg-sky-600 text-white border-sky-400 shadow-sm'
                    : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800'
                }`}
                aria-label={t('accessibility.increaseText', 'Increase text size')}
                aria-pressed={textSize === 'large'}
              >
                <span>A+</span>
                <span className="text-[10px] font-medium text-slate-200">({t('accessibility.increaseText', 'Large')})</span>
              </button>
            </div>
          </div>

          {/* Authentication Actions */}
          <div className="pt-2 border-t border-slate-800">
            {isAuthenticated ? (
              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between gap-2">
                <div className="truncate min-w-0">
                  <p className="text-xs font-bold text-white truncate">{user?.email || user?.phone}</p>
                  <span className="text-[9px] font-mono text-sky-400 uppercase font-bold">{user?.role}</span>
                </div>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="px-3 py-1.5 rounded-lg bg-rose-950 text-rose-300 hover:bg-rose-900 border border-rose-800 text-xs font-bold flex items-center gap-1 shrink-0"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>{t('nav.logout', 'Sign Out')}</span>
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl border border-slate-700 transition min-h-[44px] flex items-center justify-center"
                >
                  {t('nav.login', 'Sign In')}
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2.5 bg-gov-saffron hover:bg-orange-600 text-white font-bold text-xs rounded-xl shadow transition min-h-[44px] flex items-center justify-center"
                >
                  {t('nav.register', 'Register')}
                </Link>
              </div>
            )}
          </div>
        </div>
        </>
      )}

      {/* ─────────────────────────────────────────────────────────────
          8. RESOURCES GUIDANCE MODAL
      ───────────────────────────────────────────────────────────── */}
      {resourcesModalOpen && (
        <div
          className="fixed inset-0 z-[150] bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4"
          onClick={() => setResourcesModalOpen(false)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="resources-modal-title"
        >
          <div
            className="bg-slate-900 border border-slate-700 rounded-3xl max-w-[min(92vw,36rem)] max-h-[calc(100dvh-2rem)] overflow-y-auto w-full p-4 sm:p-6 text-white shadow-2xl space-y-4 sm:space-y-5 animate-in zoom-in-95 duration-150"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <div className="bg-amber-500/20 p-2 rounded-xl text-amber-400">
                  <BookOpen className="w-5 h-5" />
                </div>
                <div>
                  <h3 id="resources-modal-title" className="font-extrabold text-sm sm:text-base text-white">
                    {t('nav.resourcesModalTitle', 'Citizen Welfare Resources & Guidelines')}
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    {t('nav.resourcesModalSub', 'Official tools & national guidance')}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setResourcesModalOpen(false)}
                className="p-1.5 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700 space-y-1">
                <h4 className="font-bold text-sky-300 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-sky-400" />
                  {t('nav.resourcesGazetteTitle', 'National Gazette Verification Standard')}
                </h4>
                <p className="text-slate-300 text-[11px] leading-relaxed">
                  {t('nav.resourcesGazetteDesc', 'All 90 welfare schemes indexed on YojnaSetu are validated against official Gazette of India notifications, statutory ministry guidelines, and RBI/NABARD master circulars.')}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700 space-y-1">
                <h4 className="font-bold text-emerald-300 flex items-center gap-1.5">
                  <Banknote className="w-4 h-4 text-emerald-400" />
                  {t('nav.resourcesCalcTitle', 'Financial Calculator Methodology')}
                </h4>
                <p className="text-slate-300 text-[11px] leading-relaxed">
                  {t('nav.resourcesCalcDesc', 'Calculators use standardized reducing balance EMI calculations and accurate category-specific margin money / back-ended capital subsidy formulas.')}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700 space-y-1">
                <h4 className="font-bold text-amber-300 flex items-center gap-1.5">
                  <PhoneCall className="w-4 h-4 text-amber-400" />
                  {t('nav.resourcesGrievanceTitle', 'Grievance Redressal & Helpdesk')}
                </h4>
                <p className="text-slate-300 text-[11px] leading-relaxed">
                  {t('nav.resourcesGrievanceDesc', 'Toll-Free National Helpline: 1800–11–2026 (9:00 AM – 6:00 PM IST, Monday to Saturday).')}
                </p>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => setResourcesModalOpen(false)}
                className="bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs px-5 py-2 rounded-xl transition"
              >
                {t('common.close', 'Close')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          9. ABOUT YOJNASETU MODAL
      ───────────────────────────────────────────────────────────── */}
      {aboutModalOpen && (
        <div
          className="fixed inset-0 z-[150] bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4"
          onClick={() => setAboutModalOpen(false)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="about-modal-title"
        >
          <div
            className="bg-slate-900 border border-slate-700 rounded-3xl max-w-[min(92vw,32rem)] max-h-[calc(100dvh-2rem)] overflow-y-auto w-full p-4 sm:p-6 text-white shadow-2xl space-y-4 sm:space-y-5 animate-in zoom-in-95 duration-150"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <img src="/logo.png" alt="Logo" className="w-8 h-8 rounded-lg bg-slate-950 p-1 border border-slate-700" />
                <div>
                  <h3 id="about-modal-title" className="font-extrabold text-sm sm:text-base text-white">
                    {t('nav.aboutModalTitle', 'About YojnaSetu')}
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    {t('nav.aboutModalSub', 'Government Citizen Platform')}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setAboutModalOpen(false)}
                className="p-1.5 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
              <p>
                {t('nav.aboutPlatformDesc', 'YojnaSetu is a national civic-tech welfare guidance platform designed to bridge the gap between Indian citizens and government welfare, credit, and subsidy programs.')}
              </p>

              <div className="space-y-2 pt-1">
                <div className="flex items-start gap-2">
                  <ShieldCheck className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                  <span><strong>{t('nav.aboutRuleTitle', 'Deterministic Eligibility:')}</strong> {t('nav.aboutRuleDesc', 'Eligibility decisions are based on explicit deterministic rules rather than AI-generated decisions.')}</span>
                </div>
                <div className="flex items-start gap-2">
                  <Shield className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span><strong>{t('nav.aboutPiiTitle', 'Zero PII Storage Guarantee:')}</strong> {t('nav.aboutPiiDesc', 'YojnaSetu strictly never requires, uploads, or stores Aadhaar cards, bank credentials, or certificates.')}</span>
                </div>
                <div className="flex items-start gap-2">
                  <Globe className="w-4 h-4 text-gov-saffron shrink-0 mt-0.5" />
                  <span><strong>{t('nav.aboutMultiTitle', 'Multilingual Access:')}</strong> {t('nav.aboutMultiDesc', 'Full parity across 12 scheduled Indian languages.')}</span>
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => setAboutModalOpen(false)}
                className="bg-gov-saffron hover:bg-orange-600 text-white font-bold text-xs px-5 py-2 rounded-xl transition shadow"
              >
                {t('common.gotIt', 'Got It')}
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
