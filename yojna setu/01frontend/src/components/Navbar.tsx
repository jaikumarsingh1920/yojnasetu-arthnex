import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
} from 'react';
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
  PhoneCall,
  Check,
  FileText,
  HelpCircle,
  ExternalLink,
  Activity,
} from 'lucide-react';
import { NotificationBell } from './NotificationBell';

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
  const { textSize, decreaseText, resetText, increaseText } = useTextSize();

  const navigate = useNavigate();
  const location = useLocation();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const [megaMenuOpen, setMegaMenuOpen] = useState(false);
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const [citizenMenuOpen, setCitizenMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const langMenuRef = useRef<HTMLDivElement>(null);
  const megaMenuRef = useRef<HTMLDivElement>(null);
  const moreMenuRef = useRef<HTMLDivElement>(null);
  const citizenMenuRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLElement>(null);

  const [schemeSearch, setSchemeSearch] = useState('');

  const handleLogout = () => {
    logout();
    navigate('/login');
    setUserMenuOpen(false);
    setMobileMenuOpen(false);
  };

  const handleSchemeSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const query = schemeSearch.trim();
    navigate(query ? `/schemes?search=${encodeURIComponent(query)}` : '/schemes');
    setSchemeSearch('');
    setMobileMenuOpen(false);
  };

  const handleLanguageChange = (code: string) => {
    i18n.changeLanguage(code);
    setLangMenuOpen(false);
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (langMenuRef.current && !langMenuRef.current.contains(target)) setLangMenuOpen(false);
      if (megaMenuRef.current && !megaMenuRef.current.contains(target)) setMegaMenuOpen(false);
      if (moreMenuRef.current && !moreMenuRef.current.contains(target)) setMoreMenuOpen(false);
      if (citizenMenuRef.current && !citizenMenuRef.current.contains(target)) setCitizenMenuOpen(false);
      if (userMenuRef.current && !userMenuRef.current.contains(target)) setUserMenuOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
      document.documentElement.style.overflow = 'hidden';

      const handleTouchMove = (e: TouchEvent) => {
        const drawer = document.getElementById('mobile-navigation-drawer');
        if (drawer && !drawer.contains(e.target as Node)) {
          e.preventDefault();
        }
      };

      document.addEventListener('touchmove', handleTouchMove, { passive: false });
      return () => {
        document.body.style.overflow = '';
        document.documentElement.style.overflow = '';
        document.removeEventListener('touchmove', handleTouchMove);
      };
    } else {
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    }
  }, [mobileMenuOpen]);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      setMegaMenuOpen(false);
      setMoreMenuOpen(false);
      setCitizenMenuOpen(false);
      setUserMenuOpen(false);
      setLangMenuOpen(false);
      setMobileMenuOpen(false);
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  useEffect(() => {
    setMobileMenuOpen(false);
    setMegaMenuOpen(false);
    setMoreMenuOpen(false);
    setCitizenMenuOpen(false);
    setUserMenuOpen(false);
    setLangMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
      document.documentElement.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    };
  }, [mobileMenuOpen]);

  const currentLang =
    SUPPORTED_LANGUAGES.find((l) => l.code === i18n.language) || SUPPORTED_LANGUAGES[0];

  const isActive = (path: string) => location.pathname === path;
  const isCitizenPathActive = ['/profile', '/dashboard', '/applications', '/saved-schemes'].includes(
    location.pathname
  );
  const isSchemesPathActive = location.pathname.startsWith('/schemes');
  const isFinancialHealthActive = location.pathname.startsWith('/financial-health');

  return (
    <header
      ref={headerRef}
      className="yojnasetu-navbar sticky top-0 z-[100] w-full max-w-full overflow-visible select-none bg-white/95 backdrop-blur-md text-[#3B2522] border-b border-[#E8D8D2] shadow-warm-xs"
    >
      {/* =========================================================
          TIER 1: GOVERNMENT OF INDIA UTILITY STRIP
          Warm, minimal, authoritative
          ========================================================= */}
      <div className="bg-[#FFF4EC] w-full max-w-full px-3 sm:px-6 lg:px-8 py-1.5 text-xs font-medium text-[#765E59] flex justify-between items-center border-b border-[#E8D8D2] gap-2">
        {/* Left: Ministry & Portal Identity */}
        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1 overflow-hidden">
          <span className="inline-flex items-center gap-1.5 bg-white text-[#EA717B] border border-[#E8D8D2] px-2.5 py-0.5 rounded-lg text-xs font-bold tracking-wide shrink-0 shadow-2xs">
            <ShieldCheck className="w-3.5 h-3.5 text-[#EA717B] shrink-0" />
            <span>{t('nav.govIndia', 'GOVT OF INDIA')}</span>
          </span>

          <span className="hidden md:inline font-medium text-[#4A2525] text-xs sm:text-sm truncate min-w-0">
            {t('nav.portalSub', 'Ministry of Social Justice and Empowerment')}
          </span>
        </div>

        {/* Right: Helpline, Accessibility Resizer, Language */}
        <div className="flex items-center gap-2 sm:gap-3 text-[#765E59] shrink-0">
          <a
            href="tel:1800112026"
            className="hidden xl:inline-flex items-center gap-1.5 text-xs text-[#765E59] hover:text-[#EA717B] transition whitespace-nowrap font-medium"
          >
            <PhoneCall className="w-3.5 h-3.5 text-[#2E7D32] shrink-0" />
            <span>1800-11-2026 (Toll-free helpline)</span>
          </a>

          <span className="hidden xl:inline text-[#E8D8D2]">|</span>

          {/* Text Size Accessibility Controls */}
          <div
            className="hidden sm:flex items-center bg-white border border-[#E8D8D2] rounded-lg p-0.5 gap-0.5 shrink-0 shadow-2xs"
            role="group"
            aria-label={t('accessibility.textSize', 'Text size')}
          >
            <button
              type="button"
              onClick={decreaseText}
              title="Decrease text size"
              className={`min-w-[22px] h-[22px] px-1 text-xs font-bold rounded-md flex items-center justify-center transition ${
                textSize === 'small'
                  ? 'bg-[#EA717B] text-white'
                  : 'text-[#765E59] hover:bg-[#FFF4EC]'
              }`}
            >
              A−
            </button>
            <button
              type="button"
              onClick={resetText}
              title="Normal text size"
              className={`min-w-[20px] h-[22px] px-1 text-xs font-bold rounded-md flex items-center justify-center transition ${
                textSize === 'default'
                  ? 'bg-[#EA717B] text-white'
                  : 'text-[#765E59] hover:bg-[#FFF4EC]'
              }`}
            >
              A
            </button>
            <button
              type="button"
              onClick={increaseText}
              title="Increase text size"
              className={`min-w-[22px] h-[22px] px-1 text-xs font-bold rounded-md flex items-center justify-center transition ${
                textSize === 'large'
                  ? 'bg-[#EA717B] text-white'
                  : 'text-[#765E59] hover:bg-[#FFF4EC]'
              }`}
            >
              A+
            </button>
          </div>

          <span className="hidden sm:inline text-[#E8D8D2]">|</span>

          {/* Language Selector Dropdown */}
          <div className="relative shrink-0" ref={langMenuRef}>
            <button
              onClick={() => setLangMenuOpen(!langMenuOpen)}
              className="flex items-center gap-1.5 bg-white border border-[#E8D8D2] hover:border-[#D9C4BC] text-[#3B2522] px-2.5 py-1 rounded-lg text-xs font-semibold transition shadow-2xs whitespace-nowrap"
              aria-expanded={langMenuOpen}
              aria-haspopup="true"
            >
              <Globe className="w-3.5 h-3.5 text-[#EA717B] shrink-0" />
              <span className="hidden sm:inline text-[#3B2522]">{currentLang.nativeName}</span>
              <span className="sm:hidden uppercase">{currentLang.code}</span>
              <ChevronDown
                className={`w-3 h-3 text-[#9B817A] transition-transform ${
                  langMenuOpen ? 'rotate-180' : ''
                }`}
              />
            </button>

            {langMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white border border-[#E8D8D2] rounded-2xl shadow-warm-lg py-2 z-[120] max-h-80 overflow-y-auto">
                <div className="px-3.5 py-1.5 text-[10px] uppercase font-bold text-[#9B817A] tracking-wider border-b border-[#E8D8D2]">
                  Select Official Language (12)
                </div>
                {SUPPORTED_LANGUAGES.map((lang) => {
                  const isSelected = i18n.language === lang.code;
                  return (
                    <button
                      key={lang.code}
                      onClick={() => handleLanguageChange(lang.code)}
                      className={`w-full text-left px-3.5 py-2 text-xs flex items-center justify-between transition ${
                        isSelected
                          ? 'bg-[#FFF0EE] text-[#EA717B] font-bold'
                          : 'text-[#3B2522] hover:bg-[#FFF4EC]'
                      }`}
                    >
                      <div className="flex flex-col">
                        <span className="font-semibold">{lang.nativeName}</span>
                        <span className="text-[10px] text-[#765E59]">{lang.name}</span>
                      </div>
                      {isSelected && <Check className="w-3.5 h-3.5 text-[#EA717B]" />}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* =========================================================
          TIER 2: MAIN NAVIGATION BAR
          Warm white, minimal, modern typography
          ========================================================= */}
      <div className="w-full max-w-full px-3 sm:px-6 lg:px-8 py-2.5 sm:py-3">
        <div className="w-full max-w-[1600px] mx-auto flex items-center justify-between gap-3 lg:gap-6 min-w-0">
          {/* Logo & Brand Identity */}
          <Link
            to="/"
            className="flex items-center gap-2.5 shrink-0 group rounded-xl"
            aria-label={t('nav.homeAria', 'YojnaSetu Home')}
          >
            <img
              src="/logo.png"
              alt="YojnaSetu Emblem"
              className="w-8 h-8 sm:w-9 sm:h-9 object-contain transition group-hover:scale-105"
            />
            <div className="flex flex-col">
              <span className="text-xl sm:text-2xl font-bold tracking-tight text-[#3B2522] whitespace-nowrap">
                Yojna<span className="text-[#EA717B] font-black">Setu</span>
              </span>
              <span className="hidden sm:block text-xs font-medium text-[#765E59] normal-case">
                National civic-tech platform
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1 bg-[#FFF4EC] p-1 rounded-full border border-[#E8D8D2]">
            {/* Home */}
            <Link
              to="/"
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition flex items-center gap-1.5 ${
                isActive('/')
                  ? 'bg-[#EA717B] text-white shadow-warm-sm font-bold'
                  : 'text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFD0CA]/40'
              }`}
            >
              <Home className={`w-3.5 h-3.5 ${isActive('/') ? 'text-white' : 'text-[#765E59]'}`} />
              <span>{t('nav.home', 'Home')}</span>
            </Link>

            {/* Explore Schemes (Mega Menu) */}
            <div className="relative" ref={megaMenuRef}>
              <button
                type="button"
                onClick={() => setMegaMenuOpen(!megaMenuOpen)}
                className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition flex items-center gap-1.5 ${
                  isSchemesPathActive || megaMenuOpen
                    ? 'bg-white text-[#EA717B] shadow-2xs font-bold border border-[#E8D8D2]'
                    : 'text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFD0CA]/40'
                }`}
                aria-expanded={megaMenuOpen}
                aria-haspopup="true"
              >
                <Search className={`w-3.5 h-3.5 ${isSchemesPathActive || megaMenuOpen ? 'text-[#EA717B]' : 'text-[#765E59]'}`} />
                <span>{t('nav.schemes', 'Explore Schemes')}</span>
                <ChevronDown
                  className={`w-3 h-3 text-[#9B817A] transition-transform ${
                    megaMenuOpen ? 'rotate-180' : ''
                  }`}
                />
              </button>

              {megaMenuOpen && (
                <div className="absolute left-0 mt-3 w-[min(90vw,760px)] bg-white border border-[#E8D8D2] rounded-2xl shadow-warm-lg p-5 z-[120]">
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
                    {/* Browse Routes */}
                    <div className="md:col-span-4 space-y-2 md:border-r border-[#E8D8D2] md:pr-4">
                      <div className="text-[10px] font-extrabold uppercase text-[#9B817A] tracking-wider flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-[#EA717B]" />
                        <span>{t('nav.browseSchemes', 'Browse Schemes')}</span>
                      </div>
                      <div className="space-y-1">
                        <Link
                          to="/schemes"
                          onClick={() => setMegaMenuOpen(false)}
                          className="block px-2.5 py-1.5 rounded-lg text-xs font-semibold text-[#3B2522] hover:bg-[#FFF4EC] hover:text-[#EA717B] transition"
                        >
                          {t('nav.allSchemes', 'All Schemes Directory')}
                        </Link>
                        <Link
                          to="/schemes?sort_by=ministry"
                          onClick={() => setMegaMenuOpen(false)}
                          className="block px-2.5 py-1.5 rounded-lg text-xs text-[#765E59] hover:bg-[#FFF4EC] hover:text-[#3B2522] transition"
                        >
                          {t('nav.byMinistry', 'By Ministry')}
                        </Link>
                        <Link
                          to="/schemes?sort_by=category"
                          onClick={() => setMegaMenuOpen(false)}
                          className="block px-2.5 py-1.5 rounded-lg text-xs text-[#765E59] hover:bg-[#FFF4EC] hover:text-[#3B2522] transition"
                        >
                          {t('nav.byCategory', 'By Category')}
                        </Link>
                        <Link
                          to="/schemes?sort_by=sector"
                          onClick={() => setMegaMenuOpen(false)}
                          className="block px-2.5 py-1.5 rounded-lg text-xs text-[#765E59] hover:bg-[#FFF4EC] hover:text-[#3B2522] transition"
                        >
                          {t('nav.bySector', 'By Sector')}
                        </Link>
                      </div>
                    </div>

                    {/* Popular National Schemes */}
                    <div className="md:col-span-8 space-y-2">
                      <div className="text-[10px] font-extrabold uppercase text-[#9B817A] tracking-wider flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-[#F7AE56]" />
                        <span>{t('nav.popularSchemes', 'Popular National Schemes')}</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {POPULAR_NATIONAL_SCHEMES.slice(0, 4).map((scheme) => (
                          <Link
                            key={scheme.id}
                            to={scheme.query}
                            onClick={() => setMegaMenuOpen(false)}
                            className="block p-2.5 rounded-xl border border-[#E8D8D2] hover:border-[#FFD0CA] hover:bg-[#FFF4EC]/60 transition group"
                          >
                            <span className="text-xs font-bold text-[#3B2522] group-hover:text-[#EA717B] transition block truncate">
                              {scheme.shortName}
                            </span>
                            <p className="text-[10px] text-[#765E59] line-clamp-1 mt-0.5">
                              {scheme.tag}
                            </p>
                          </Link>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-[#E8D8D2] flex items-center justify-between">
                    <span className="text-[11px] text-[#765E59]">
                      Grounded in published official Gazette guidelines.
                    </span>
                    <Link
                      to="/schemes"
                      onClick={() => setMegaMenuOpen(false)}
                      className="text-xs font-bold text-[#EA717B] hover:text-[#D65D67] flex items-center gap-1"
                    >
                      <span>Explore all schemes</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Smart Matching */}
            <Link
              to="/recommendations"
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition flex items-center gap-1.5 ${
                isActive('/recommendations')
                  ? 'bg-[#EA717B] text-white shadow-warm-sm font-bold'
                  : 'text-[#765E59] hover:text-[#EA717B] hover:bg-[#FFD0CA]/40'
              }`}
            >
              <Sparkles className={`w-3.5 h-3.5 ${isActive('/recommendations') ? 'text-[#FFF0EE]' : 'text-[#EA717B]'}`} />
              <span>{t('nav.recommendations', 'Smart Matching')}</span>
            </Link>

            {/* Financial Health Hub */}
            <Link
              to="/financial-health"
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition flex items-center gap-1.5 ${
                isFinancialHealthActive
                  ? 'bg-white text-[#EA717B] shadow-2xs font-bold border border-[#E8D8D2]'
                  : 'text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFD0CA]/40'
              }`}
              aria-current={isFinancialHealthActive ? 'page' : undefined}
            >
              <Activity className={`w-3.5 h-3.5 ${isFinancialHealthActive ? 'text-[#EA717B]' : 'text-[#765E59]'}`} />
              <span>{t('nav.financialHealth', 'Financial Health')}</span>
            </Link>

            {/* Financial Calculator */}
            <Link
              to="/calculator"
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition flex items-center gap-1.5 ${
                isActive('/calculator')
                  ? 'bg-white text-[#EA717B] shadow-2xs font-bold border border-[#E8D8D2]'
                  : 'text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFD0CA]/40'
              }`}
            >
              <Calculator className="w-3.5 h-3.5 text-[#765E59]" />
              <span>{t('nav.calculator', 'Financial Calculator')}</span>
            </Link>

            {/* Nearby Partners */}
            <Link
              to="/channel-partners"
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition flex items-center gap-1.5 ${
                isActive('/channel-partners')
                  ? 'bg-white text-[#EA717B] shadow-2xs font-bold border border-[#E8D8D2]'
                  : 'text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFD0CA]/40'
              }`}
            >
              <MapPin className="w-3.5 h-3.5 text-[#765E59]" />
              <span>{t('nav.partnerLocator', 'Nearby Partners')}</span>
            </Link>

            {/* More Dropdown */}
            <div className="relative" ref={moreMenuRef}>
              <button
                type="button"
                onClick={() => setMoreMenuOpen(!moreMenuOpen)}
                className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition flex items-center gap-1.5 ${
                  moreMenuOpen
                    ? 'bg-white text-[#EA717B] shadow-2xs font-bold border border-[#E8D8D2]'
                    : 'text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFD0CA]/40'
                }`}
                aria-expanded={moreMenuOpen}
                aria-haspopup="true"
              >
                <BookOpen className="w-3.5 h-3.5 text-[#765E59]" />
                <span>{t('nav.more', 'More')}</span>
                <ChevronDown
                  className={`w-3 h-3 text-[#9B817A] transition-transform ${
                    moreMenuOpen ? 'rotate-180' : ''
                  }`}
                />
              </button>

              {moreMenuOpen && (
                <div className="absolute right-0 mt-3 w-64 bg-white border border-[#E8D8D2] rounded-2xl shadow-warm-lg py-2 z-[120]">
                  <div className="px-4 py-1.5 text-[10px] uppercase font-bold text-[#9B817A]">
                    {t('nav.infoHelp', 'Information & Tools')}
                  </div>
                  <Link
                    to="/compare"
                    onClick={() => setMoreMenuOpen(false)}
                    className="w-full text-left px-4 py-2 text-xs flex items-center gap-3 text-[#3B2522] hover:bg-[#FFF4EC]"
                  >
                    <Layers className="w-4 h-4 text-[#EA717B]" />
                    <div>
                      <div className="font-bold text-[#3B2522]">{t('nav.compare', 'Compare Schemes')}</div>
                      <span className="text-[10px] text-[#765E59]">{t('nav.compareSubtitle', 'Side-by-side eligibility check')}</span>
                    </div>
                  </Link>
                  <Link
                    to="/resources"
                    onClick={() => setMoreMenuOpen(false)}
                    className="w-full text-left px-4 py-2 text-xs flex items-center gap-3 text-[#3B2522] hover:bg-[#FFF4EC]"
                  >
                    <BookOpen className="w-4 h-4 text-[#F7AE56]" />
                    <div>
                      <div className="font-bold text-[#3B2522]">{t('nav.resources', 'Resources & Guidelines')}</div>
                      <span className="text-[10px] text-[#765E59]">{t('nav.gazetteVerified', 'Gazette rules & circulars')}</span>
                    </div>
                  </Link>
                  <Link
                    to="/blogs"
                    onClick={() => setMoreMenuOpen(false)}
                    className="w-full text-left px-4 py-2 text-xs flex items-center gap-3 text-[#3B2522] hover:bg-[#FFF4EC]"
                  >
                    <BookOpen className="w-4 h-4 text-[#EA717B]" />
                    <div>
                      <div className="font-bold text-[#3B2522]">Blog</div>
                      <span className="text-[10px] text-[#765E59]">Financial guidance & insights</span>
                    </div>
                  </Link>
                  <Link
                    to="/faq"
                    onClick={() => setMoreMenuOpen(false)}
                    className="w-full text-left px-4 py-2 text-xs flex items-center gap-3 text-[#3B2522] hover:bg-[#FFF4EC]"
                  >
                    <HelpCircle className="w-4 h-4 text-[#2E7D32]" />
                    <div>
                      <div className="font-bold text-[#3B2522]">{t('nav.faq', 'FAQs')}</div>
                      <span className="text-[10px] text-[#765E59]">{t('nav.faqSubtitle', 'Frequently asked questions')}</span>
                    </div>
                  </Link>
                  <Link
                    to="/about"
                    onClick={() => setMoreMenuOpen(false)}
                    className="w-full text-left px-4 py-2 text-xs flex items-center gap-3 text-[#3B2522] hover:bg-[#FFF4EC]"
                  >
                    <Info className="w-4 h-4 text-[#EA717B]" />
                    <div>
                      <div className="font-bold text-[#3B2522]">{t('nav.about', 'About YojnaSetu')}</div>
                      <span className="text-[10px] text-[#765E59]">{t('nav.aboutSubtitle', 'Zero PII Policy & Civic Mission')}</span>
                    </div>
                  </Link>

                  {isAuthenticated && role === 'SYSTEM_ADMIN' && (
                    <Link
                      to="/admin"
                      onClick={() => setMoreMenuOpen(false)}
                      className="flex items-center gap-3 px-4 py-2 text-xs text-[#B91C1C] bg-[#FDECEF] hover:bg-[#FFD0CA]/50 border-t border-[#E8D8D2] font-semibold"
                    >
                      <ShieldAlert className="w-4 h-4 text-[#B91C1C]" />
                      <span>{t('nav.adminControlCenter', 'Admin Control Center')}</span>
                    </Link>
                  )}
                </div>
              )}
            </div>
          </nav>

          {/* Right Section: Compact Search & Auth Actions */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            {/* Desktop Search Bar */}
            <form
              onSubmit={handleSchemeSearch}
              className="hidden md:flex items-center bg-white hover:bg-[#FFF4EC]/50 focus-within:bg-white border border-[#E8D8D2] focus-within:border-[#EA717B] focus-within:ring-2 focus-within:ring-[#EA717B]/20 rounded-full px-3 py-1.5 transition max-w-[220px] xl:max-w-[260px] shadow-2xs"
            >
              <Search className="w-3.5 h-3.5 text-[#9B817A] shrink-0 mr-1.5" />
              <input
                type="text"
                value={schemeSearch}
                onChange={(e) => setSchemeSearch(e.target.value)}
                placeholder="Search schemes..."
                className="w-full text-xs bg-transparent outline-none text-[#3B2522] placeholder:text-[#9B817A]"
              />
            </form>

            {/* Authenticated User or Login/Register */}
            {isAuthenticated && user ? (
              <div className="flex items-center gap-2">
                <NotificationBell />

                {/* User Dropdown */}
                <div className="relative" ref={userMenuRef}>
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center gap-2 bg-white hover:bg-[#FFF4EC] border border-[#E8D8D2] px-2.5 py-1.5 rounded-full text-xs font-semibold text-[#3B2522] transition shadow-2xs"
                  >
                    <div className="w-6 h-6 rounded-full bg-[#EA717B] text-white flex items-center justify-center font-bold text-[11px]">
                      {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
                    </div>
                    <span className="hidden sm:inline max-w-[100px] truncate">{user.full_name || 'User'}</span>
                    <ChevronDown className="w-3 h-3 text-[#9B817A]" />
                  </button>

                  {userMenuOpen && (
                    <div className="absolute right-0 mt-2 w-52 bg-white border border-[#E8D8D2] rounded-2xl shadow-warm-lg py-2 z-[120]">
                      <div className="px-3.5 py-2 border-b border-[#E8D8D2]">
                        <p className="text-xs font-bold text-[#3B2522] truncate">{user.full_name}</p>
                        <p className="text-[10px] text-[#765E59] truncate">{user.email || user.phone}</p>
                      </div>
                      <Link
                        to="/profile"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-2.5 px-3.5 py-2 text-xs text-[#3B2522] hover:bg-[#FFF4EC]"
                      >
                        <User className="w-3.5 h-3.5 text-[#9B817A]" />
                        <span>{t('nav.profile', 'My Profile')}</span>
                      </Link>
                      <Link
                        to="/dashboard"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-2.5 px-3.5 py-2 text-xs text-[#3B2522] hover:bg-[#FFF4EC]"
                      >
                        <LayoutDashboard className="w-3.5 h-3.5 text-[#9B817A]" />
                        <span>{t('nav.dashboard', 'Citizen Dashboard')}</span>
                      </Link>
                      <Link
                        to="/applications"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-2.5 px-3.5 py-2 text-xs text-[#3B2522] hover:bg-[#FFF4EC]"
                      >
                        <FileText className="w-3.5 h-3.5 text-[#9B817A]" />
                        <span>{t('nav.applications', 'Applications')}</span>
                      </Link>
                      <Link
                        to="/saved-schemes"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-2.5 px-3.5 py-2 text-xs text-[#3B2522] hover:bg-[#FFF4EC]"
                      >
                        <Bookmark className="w-3.5 h-3.5 text-[#9B817A]" />
                        <span>{t('nav.savedSchemes', 'Saved Schemes')}</span>
                      </Link>
                      <div className="border-t border-[#E8D8D2] mt-1 pt-1">
                        <button
                          onClick={handleLogout}
                          className="w-full text-left flex items-center gap-2.5 px-3.5 py-2 text-xs text-[#B91C1C] hover:bg-[#FDECEF]"
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
              <div className="flex items-center gap-2">
                <Link
                  to="/register"
                  className="hidden sm:inline-flex items-center justify-center px-3.5 py-1.5 rounded-xl bg-[#FFD0CA] hover:bg-[#F5B8B0] text-[#4A2525] border border-[#E8D8D2] font-bold text-xs shadow-2xs transition"
                >
                  {t('nav.register', 'Register')}
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center px-4 py-1.5 rounded-xl bg-[#EA717B] hover:bg-[#D65D67] text-white text-xs font-bold shadow-warm-sm transition"
                >
                  {t('nav.login', 'Citizen Login')}
                </Link>
              </div>
            )}

            {/* Mobile Menu Toggle Button */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-xl text-[#3B2522] hover:bg-[#FFF4EC] transition"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* =========================================================
          MOBILE NAVIGATION DRAWER
          ========================================================= */}
      {mobileMenuOpen && (
        <div
          id="mobile-navigation-drawer"
          className="lg:hidden fixed left-0 right-0 w-full top-[var(--nav-height,90px)] bottom-0 bg-slate-900/30 backdrop-blur-xs z-50 overflow-y-auto"
          onClick={() => setMobileMenuOpen(false)}
        >
          <div
            className="bg-[#FFFBF0] w-full max-w-md ml-auto min-h-full p-5 space-y-5 shadow-warm-xl border-l border-[#E8D8D2]"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Mobile Search */}
            <form onSubmit={handleSchemeSearch} className="flex items-center bg-white border border-[#E8D8D2] rounded-xl px-3 py-2 shadow-2xs">
              <Search className="w-4 h-4 text-[#9B817A] mr-2 shrink-0" />
              <input
                type="text"
                value={schemeSearch}
                onChange={(e) => setSchemeSearch(e.target.value)}
                placeholder="Search government schemes..."
                className="w-full text-xs bg-transparent outline-none text-[#3B2522]"
              />
              <button type="submit" className="text-xs font-bold text-[#EA717B] shrink-0">
                Go
              </button>
            </form>

            {/* Nav Links */}
            <div className="space-y-1">
              <Link
                to="/"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-[#3B2522] hover:bg-white"
              >
                <Home className="w-4 h-4 text-[#EA717B]" />
                <span>{t('nav.home', 'Home')}</span>
              </Link>
              <Link
                to="/schemes"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-[#3B2522] hover:bg-white"
              >
                <Search className="w-4 h-4 text-[#F7AE56]" />
                <span>{t('nav.schemes', 'Explore All Schemes')}</span>
              </Link>
              <Link
                to="/recommendations"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-bold text-[#EA717B] bg-[#FFF0EE] border border-[#FFD0CA]"
              >
                <Sparkles className="w-4 h-4 text-[#EA717B]" />
                <span>{t('nav.recommendations', 'Smart Matching (For You)')}</span>
              </Link>
              <Link
                to="/financial-health"
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition ${
                  isFinancialHealthActive
                    ? 'text-[#EA717B] bg-[#FFF0EE] font-bold border border-[#FFD0CA]'
                    : 'text-[#3B2522] hover:bg-white'
                }`}
                aria-current={isFinancialHealthActive ? 'page' : undefined}
              >
                <Activity className={`w-4 h-4 ${isFinancialHealthActive ? 'text-[#EA717B]' : 'text-[#2E7D32]'}`} />
                <span>{t('nav.financialHealth', 'Financial Health')}</span>
              </Link>
              <Link
                to="/calculator"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-[#3B2522] hover:bg-white"
              >
                <Calculator className="w-4 h-4 text-[#2E7D32]" />
                <span>{t('nav.calculator', 'Financial Calculator')}</span>
              </Link>
              <Link
                to="/channel-partners"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-[#3B2522] hover:bg-white"
              >
                <MapPin className="w-4 h-4 text-[#EA717B]" />
                <span>{t('nav.channelPartners', 'Nearby Partner Centers')}</span>
              </Link>
              <Link
                to="/compare"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-[#3B2522] hover:bg-white"
              >
                <Layers className="w-4 h-4 text-[#EA717B]" />
                <span>{t('nav.compare', 'Compare Schemes')}</span>
              </Link>
              <Link
                to="/resources"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-[#3B2522] hover:bg-white"
              >
                <BookOpen className="w-4 h-4 text-[#F7AE56]" />
                <span>{t('nav.resources', 'Resources & Guidelines')}</span>
              </Link>
              <Link
                to="/about"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-[#3B2522] hover:bg-white"
              >
                <Info className="w-4 h-4 text-[#765E59]" />
                <span>{t('nav.about', 'About YojnaSetu')}</span>
              </Link>
            </div>

            {/* Mobile Auth actions */}
            {!isAuthenticated && (
              <div className="pt-4 border-t border-[#E8D8D2] flex flex-col gap-2">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2.5 rounded-xl bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold text-xs shadow-warm-sm"
                >
                  {t('nav.login', 'Citizen Login')}
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2.5 rounded-xl bg-[#FFD0CA] hover:bg-[#F5B8B0] border border-[#E8D8D2] text-[#4A2525] font-bold text-xs shadow-2xs"
                >
                  {t('nav.register', 'Register New Account')}
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
