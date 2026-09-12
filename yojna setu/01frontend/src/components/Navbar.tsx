import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
} from 'react';

import {
  Link,
  useNavigate,
  useLocation,
} from 'react-router-dom';

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
  Shield,
  Home,
  BookOpen,
  Info,
  ArrowRight,
  Layers,
  Banknote,
  PhoneCall,
  Check,
  Flame,
  FileText,
  HelpCircle,
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

  const {
    user,
    isAuthenticated,
    logout,
    role,
  } = useAuth();

  const {
    textSize,
    setTextSize,
    decreaseText,
    resetText,
    increaseText,
  } = useTextSize();

  const navigate = useNavigate();
  const location = useLocation();


  // ─────────────────────────────────────────────────────────────
  // Navigation UI State
  // ─────────────────────────────────────────────────────────────

  const [mobileMenuOpen, setMobileMenuOpen] =
    useState(false);

  const [langMenuOpen, setLangMenuOpen] =
    useState(false);

  const [megaMenuOpen, setMegaMenuOpen] =
    useState(false);

  const [moreMenuOpen, setMoreMenuOpen] =
    useState(false);

  const [citizenMenuOpen, setCitizenMenuOpen] =
    useState(false);

  const [userMenuOpen, setUserMenuOpen] =
    useState(false);

  

  


  // ─────────────────────────────────────────────────────────────
  // Dropdown Refs
  // ─────────────────────────────────────────────────────────────

  const langMenuRef =
    useRef<HTMLDivElement>(null);

  const megaMenuRef =
    useRef<HTMLDivElement>(null);

  const moreMenuRef =
    useRef<HTMLDivElement>(null);

  const citizenMenuRef =
    useRef<HTMLDivElement>(null);

  const userMenuRef =
    useRef<HTMLDivElement>(null);

  const headerRef =
    useRef<HTMLElement>(null);


  const [navHeight, setNavHeight] =
    useState<number>(76);

  const [schemeSearch, setSchemeSearch] =
    useState('');


  // ─────────────────────────────────────────────────────────────
  // LOGOUT
  // ─────────────────────────────────────────────────────────────

  const handleLogout = () => {

    logout();

    navigate('/login');

    setUserMenuOpen(false);
    setMobileMenuOpen(false);
  };

  const handleSchemeSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const query = schemeSearch.trim();

    navigate(
      query
        ? `/schemes?search=${encodeURIComponent(query)}`
        : '/schemes'
    );

    setSchemeSearch('');
  };


  // ─────────────────────────────────────────────────────────────
  // LANGUAGE
  // ─────────────────────────────────────────────────────────────

  const handleLanguageChange = (code: string) => {

    i18n.changeLanguage(code);

    setLangMenuOpen(false);
  };


  // ─────────────────────────────────────────────────────────────
  // CLOSE MENUS ON OUTSIDE CLICK
  // ─────────────────────────────────────────────────────────────

  useEffect(() => {

    const handleClickOutside = (e: MouseEvent) => {

      const target = e.target as Node;


      if (
        langMenuRef.current &&
        !langMenuRef.current.contains(target)
      ) {
        setLangMenuOpen(false);
      }


      if (
        megaMenuRef.current &&
        !megaMenuRef.current.contains(target)
      ) {
        setMegaMenuOpen(false);
      }


      if (
        moreMenuRef.current &&
        !moreMenuRef.current.contains(target)
      ) {
        setMoreMenuOpen(false);
      }


      if (
        citizenMenuRef.current &&
        !citizenMenuRef.current.contains(target)
      ) {
        setCitizenMenuOpen(false);
      }


      if (
        userMenuRef.current &&
        !userMenuRef.current.contains(target)
      ) {
        setUserMenuOpen(false);
      }
    };


    document.addEventListener(
      'mousedown',
      handleClickOutside
    );


    return () => {

      document.removeEventListener(
        'mousedown',
        handleClickOutside
      );

    };

  }, []);


  // ─────────────────────────────────────────────────────────────
  // ESCAPE KEY
  // ─────────────────────────────────────────────────────────────

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {

      if (e.key === 'Escape') {

        setMegaMenuOpen(false);
        setMoreMenuOpen(false);
        setCitizenMenuOpen(false);
        setUserMenuOpen(false);
        setLangMenuOpen(false);
        setMobileMenuOpen(false);
      }

    },
    []
  );


  useEffect(() => {

    window.addEventListener(
      'keydown',
      handleKeyDown
    );

    return () => {

      window.removeEventListener(
        'keydown',
        handleKeyDown
      );

    };

  }, [handleKeyDown]);


  // ─────────────────────────────────────────────────────────────
  // CLOSE MENUS ON ROUTE CHANGE
  // ─────────────────────────────────────────────────────────────

  useEffect(() => {

    setMobileMenuOpen(false);
    setMegaMenuOpen(false);
    setMoreMenuOpen(false);
    setCitizenMenuOpen(false);
    setUserMenuOpen(false);
    setLangMenuOpen(false);

  }, [location.pathname]);


  // ─────────────────────────────────────────────────────────────
  // NAVBAR HEIGHT
  // ─────────────────────────────────────────────────────────────

  useEffect(() => {

    const updateNavHeight = () => {

      if (headerRef.current) {

        setNavHeight(
          headerRef.current.offsetHeight
        );

      }

    };


    updateNavHeight();

    window.addEventListener(
      'resize',
      updateNavHeight
    );


    return () => {

      window.removeEventListener(
        'resize',
        updateNavHeight
      );

    };

  }, []);


  // ─────────────────────────────────────────────────────────────
  // MOBILE SCROLL LOCK
  // ─────────────────────────────────────────────────────────────

  useEffect(() => {

    if (mobileMenuOpen) {

      if (headerRef.current) {

        setNavHeight(
          headerRef.current.offsetHeight
        );

      }


      const originalBodyOverflow =
        document.body.style.overflow;

      const originalHtmlOverflow =
        document.documentElement.style.overflow;


      document.body.style.overflow = 'hidden';

      document.documentElement.style.overflow =
        'hidden';


      const handleTouchMove = (
        e: TouchEvent
      ) => {

        const drawer =
          document.getElementById(
            'mobile-navigation-drawer'
          );


        if (
          !drawer ||
          !drawer.contains(
            e.target as Node
          )
        ) {

          if (e.cancelable) {
            e.preventDefault();
          }

        }

      };


      document.addEventListener(
        'touchmove',
        handleTouchMove,
        { passive: false }
      );


      return () => {

        document.body.style.overflow =
          originalBodyOverflow;

        document.documentElement.style.overflow =
          originalHtmlOverflow;


        document.removeEventListener(
          'touchmove',
          handleTouchMove
        );

      };

    } else {

      document.body.style.overflow = '';

      document.documentElement.style.overflow = '';

    }

  }, [mobileMenuOpen]);


  // ─────────────────────────────────────────────────────────────
  // CURRENT LANGUAGE
  // ─────────────────────────────────────────────────────────────

  const currentLang =
    SUPPORTED_LANGUAGES.find(
      (l) => l.code === i18n.language
    ) || SUPPORTED_LANGUAGES[0];


  // ─────────────────────────────────────────────────────────────
  // ACTIVE STATES
  // ─────────────────────────────────────────────────────────────

  const isActive = (path: string) =>
    location.pathname === path;


  const isCitizenPathActive =
    [
      '/profile',
      '/dashboard',
      '/applications',
      '/saved-schemes',
    ].includes(location.pathname);


  const isSchemesPathActive =
    location.pathname.startsWith('/schemes');


  return (

    <header
      ref={headerRef}
      className="
        sticky
        top-0
        z-[100]
        w-full
        max-w-full
        overflow-visible
        select-none
        bg-[#861823]
        text-white
        border-b
        border-white/10
      "
    >

      {/* =========================================================
          TOP GOVERNMENT STRIP
          ========================================================= */}

      <div
        className="
          bg-[#6f1420]
          w-full
          max-w-full
          px-3
          sm:px-6
          lg:px-8
          2xl:px-10
          py-1.5
          sm:py-2
          text-xs
          font-medium
          text-slate-300
          flex
          justify-between
          items-center
          border-b
          border-white/5
          gap-2
          overflow-visible
        "
      >

        {/* LEFT */}

        <div
          className="
            flex
            items-center
            gap-2
            sm:gap-3
            min-w-0
            flex-1
            overflow-hidden
          "
        >

          {/* Government Department */}

          <span
            className="
              bg-[#f58220]
              text-white
              px-2
              sm:px-2.5
              py-1
              rounded-md
              font-extrabold
              text-[8px]
              sm:text-[10px]
              tracking-wide
              shadow-sm
              flex
              items-center
              gap-1.5
              shrink-0
              uppercase
              max-w-full
            "
          >

            <ShieldCheck
              className="
                w-3
                h-3
                shrink-0
              "
            />

            <span className="truncate">
              {t(
                'nav.govIndia',
                'MINISTRY OF SOCIAL JUSTICE AND EMPOWERMENT'
              )}
            </span>

          </span>


          <span
            className="
              hidden
              md:inline
              font-medium
              text-slate-300
              text-[11px]
              truncate
              min-w-0
            "
          >
            {t(
              'nav.portalSub',
              'National Welfare & Credit Guidance Platform'
            )}
          </span>


          <span
            className="
              hidden
              md:inline
              text-slate-600
              shrink-0
            "
          >
            •
          </span>


          <span
            className="
              hidden
              sm:inline
              text-slate-400
              text-[10px]
              sm:text-[11px]
              font-mono
              shrink-0
            "
          >
            yojnasetu.gov.in
          </span>

        </div>


        {/* RIGHT */}

        <div
          className="
            flex
            items-center
            gap-2
            sm:gap-3
            text-slate-300
            shrink-0
          "
        >

          {/* HELPLINE */}

          <a
            href="tel:1800112026"
            className="
              hidden
              xl:inline-flex
              items-center
              gap-1.5
              text-[11px]
              text-slate-300
              hover:text-sky-300
              transition
              whitespace-nowrap
            "
          >

            <PhoneCall
              className="
                w-3
                h-3
                text-emerald-400
              "
            />

            <span>
              {t(
                'nav.helpline',
                'Helpline: 1800–11–2026 (Toll-Free)'
              )}
            </span>

          </a>


          <span
            className="
              hidden
              xl:inline
              text-slate-700
            "
          >
            |
          </span>


          {/* TEXT SIZE */}

          <div
            className="
              hidden
              sm:flex
              items-center
              bg-white/5
              border
              border-white/10
              rounded-lg
              p-0.5
              gap-0.5
              shrink-0
            "
            role="group"
            aria-label={t(
              'accessibility.textSize',
              'Text size'
            )}
          >

            <button
              type="button"
              onClick={decreaseText}
              className={`
                min-w-[22px]
                h-[21px]
                px-1
                text-[10px]
                font-bold
                rounded
                flex
                items-center
                justify-center
                transition
                ${
                  textSize === 'small'
                    ? 'bg-sky-600 text-white'
                    : 'text-slate-300 hover:bg-white/10'
                }
              `}
            >
              A−
            </button>


            <button
              type="button"
              onClick={resetText}
              className={`
                min-w-[20px]
                h-[21px]
                px-1
                text-[10px]
                font-bold
                rounded
                flex
                items-center
                justify-center
                transition
                ${
                  textSize === 'default'
                    ? 'bg-sky-600 text-white'
                    : 'text-slate-300 hover:bg-white/10'
                }
              `}
            >
              A
            </button>


            <button
              type="button"
              onClick={increaseText}
              className={`
                min-w-[22px]
                h-[21px]
                px-1
                text-[10px]
                font-bold
                rounded
                flex
                items-center
                justify-center
                transition
                ${
                  textSize === 'large'
                    ? 'bg-sky-600 text-white'
                    : 'text-slate-300 hover:bg-white/10'
                }
              `}
            >
              A+
            </button>

          </div>


          {/* LANGUAGE */}

          <div
            className="relative shrink-0"
            ref={langMenuRef}
          >

            <button
              onClick={() =>
                setLangMenuOpen(
                  !langMenuOpen
                )
              }
              className="
                flex
                items-center
                gap-1.5
                bg-transparent
                hover:bg-white/5
                text-white
                px-1.5
                py-1
                rounded-lg
                text-xs
                font-semibold
                transition
                whitespace-nowrap
              "
              aria-expanded={langMenuOpen}
              aria-haspopup="true"
            >

              <Globe
                className="
                  w-3.5
                  h-3.5
                  text-sky-400
                "
              />

              <span className="hidden sm:inline">
                {currentLang.nativeName}
              </span>

              <span className="sm:hidden uppercase">
                {currentLang.code}
              </span>

              <ChevronDown
                className={`
                  w-3
                  h-3
                  text-slate-400
                  transition-transform
                  ${
                    langMenuOpen
                      ? 'rotate-180'
                      : ''
                  }
                `}
              />

            </button>


            {langMenuOpen && (

              <div
                className="
                  absolute
                  right-0
                  mt-2
                  w-52
                  bg-[#6f1420]
                  border
                  border-white/10
                  rounded-2xl
                  shadow-2xl
                  py-2
                  z-[120]
                  max-h-80
                  overflow-y-auto
                "
              >

                <div
                  className="
                    px-3
                    py-1.5
                    text-[10px]
                    uppercase
                    font-bold
                    text-slate-400
                    tracking-wider
                  "
                >
                  Select Official Language (12)
                </div>


                {SUPPORTED_LANGUAGES.map(
                  (lang) => {

                    const isSelected =
                      i18n.language ===
                      lang.code;


                    return (

                      <button
                        key={lang.code}
                        onClick={() =>
                          handleLanguageChange(
                            lang.code
                          )
                        }
                        className={`
                          w-full
                          text-left
                          px-3.5
                          py-2
                          text-xs
                          flex
                          items-center
                          justify-between
                          transition
                          ${
                            isSelected
                              ? 'bg-sky-800/80 text-white'
                              : 'text-slate-200 hover:bg-white/5'
                          }
                        `}
                      >

                        <div
                          className="
                            flex
                            items-center
                            gap-2
                          "
                        >

                          {isSelected && (

                            <Check
                              className="
                                w-3.5
                                h-3.5
                                text-sky-400
                              "
                            />

                          )}

                          <span>
                            {lang.nativeName}
                          </span>

                        </div>


                        <span
                          className="
                            text-[10px]
                            text-slate-400
                            font-mono
                            uppercase
                          "
                        >
                          {lang.code}
                        </span>

                      </button>

                    );

                  }
                )}

              </div>

            )}

          </div>

        </div>

      </div>


      {/* =========================================================
          MAIN NAVIGATION
          RESPONSIVE DESKTOP / TABLET
          ========================================================= */}

      <div
        className="
          w-full
          max-w-full
          px-3
          sm:px-5
          lg:px-6
          2xl:px-10
          py-2.5
          lg:py-3
          2xl:py-4
          overflow-visible
        "
      >

        <div
          className="
            w-full
            max-w-[1600px]
            mx-auto
            flex
            items-center
            gap-3
            lg:gap-4
            2xl:gap-5
            min-w-0
          "
        >


          {/* =====================================================
              LOGO
              ===================================================== */}

          <Link
            to="/"
            className="
              flex
              items-center
              gap-2
              lg:gap-2.5
              shrink-0
              group
              rounded-xl
            "
            aria-label={t(
              'nav.homeAria',
              'YojnaSetu Home'
            )}
          >

            <img
              src="/logo.png"
              alt="YojnaSetu Emblem"
              className="
                w-8
                h-8
                sm:w-9
                sm:h-9
                lg:w-10
                lg:h-10
                object-contain
                transition
                group-hover:scale-105
              "
            />


            <div
              className="
                flex
                items-center
              "
            >

              <span
                className="
                  text-lg
                  sm:text-xl
                  lg:text-2xl
                  font-semibold
                  tracking-tight
                  text-white
                  whitespace-nowrap
                "
              >
                {t(
                  'nav.title',
                  'YojnaSetu'
                )}
              </span>

            </div>

          </Link>


          {/* =====================================================
              DESKTOP PILL NAVIGATION
              ===================================================== */}

          <nav
            className="
              hidden
              xl:flex
              flex-1
              min-w-0
              items-center
              justify-center
              rounded-full
              border
              border-white/60
              bg-white/[0.035]
              backdrop-blur-md
              p-1
              shadow-sm
              overflow-visible
            "
          >


            {/* HOME */}

            <Link
              to="/"
              className={`
                shrink
                px-2
                2xl:px-3
                py-2
                2xl:py-2.5
                rounded-full
                text-[11px]
                2xl:text-[13px]
                font-medium
                transition
                whitespace-nowrap
                flex
                items-center
                justify-center
                gap-1
                2xl:gap-1.5
                ${
                  isActive('/')
                    ? 'bg-white/15 text-white shadow-sm'
                    : 'text-white/80 hover:bg-white/10 hover:text-white'
                }
              `}
            >

              <Home
                className="
                  w-3
                  h-3
                  2xl:w-3.5
                  2xl:h-3.5
                  text-white/80
                  shrink-0
                "
              />

              <span>
                {t(
                  'nav.home',
                  'Home'
                )}
              </span>

            </Link>


            {/* EXPLORE SCHEMES */}

            <div
              className="relative shrink min-w-0"
              ref={megaMenuRef}
            >

              <button
                type="button"
                onClick={() =>
                  setMegaMenuOpen(
                    !megaMenuOpen
                  )
                }
                className={`
                  px-2
                  2xl:px-3
                  py-2
                  2xl:py-2.5
                  rounded-full
                  text-[11px]
                  2xl:text-[13px]
                  font-medium
                  transition
                  whitespace-nowrap
                  flex
                  items-center
                  justify-center
                  gap-1
                  2xl:gap-1.5
                  ${
                    isSchemesPathActive ||
                    megaMenuOpen
                      ? 'bg-white/15 text-white'
                      : 'text-white/80 hover:bg-white/10 hover:text-white'
                  }
                `}
                aria-expanded={
                  megaMenuOpen
                }
                aria-haspopup="true"
              >

                <Search
                  className="
                    w-3
                    h-3
                    2xl:w-3.5
                    2xl:h-3.5
                    text-white/80
                    shrink-0
                  "
                />

                <span>
                  {t(
                    'nav.schemes',
                    'Explore Schemes'
                  )}
                </span>

                <ChevronDown
                  className={`
                    w-3
                    h-3
                    2xl:w-3.5
                    2xl:h-3.5
                    text-white/60
                    transition-transform
                    ${
                      megaMenuOpen
                        ? 'rotate-180'
                        : ''
                    }
                  `}
                />

              </button>


              {/* =================================================
                  MEGA MENU
                  ================================================= */}

              {megaMenuOpen && (

                <div
                  className="
                    absolute
                    left-0
                    mt-3
                    w-[min(90vw,780px)]
                    max-w-[calc(100vw-2rem)]
                    bg-[#6f1420]
                    border
                    border-white/10
                    rounded-2xl
                    shadow-2xl
                    p-5
                    z-[120]
                    max-h-[80vh]
                    overflow-y-auto
                  "
                >

                  <div
                    className="
                      grid
                      grid-cols-1
                      md:grid-cols-12
                      gap-5
                    "
                  >

                    {/* BROWSE */}

                    <div
                      className="
                        md:col-span-3
                        space-y-2
                        md:border-r
                        border-white/10
                        md:pr-4
                      "
                    >

                      <div
                        className="
                          text-[10px]
                          font-extrabold
                          uppercase
                          text-sky-400
                          tracking-wider
                          flex
                          items-center
                          gap-1.5
                        "
                      >

                        <Layers
                          className="w-3.5 h-3.5"
                        />

                        {t(
                          'nav.browseSchemes',
                          'Browse Schemes'
                        )}

                      </div>


                      <div className="space-y-1">

                        <Link
                          to="/schemes"
                          onClick={() =>
                            setMegaMenuOpen(false)
                          }
                          className="
                            block
                            px-2
                            py-1.5
                            rounded-lg
                            text-xs
                            font-semibold
                            text-slate-200
                            hover:bg-white/5
                            hover:text-sky-300
                          "
                        >
                          {t(
                            'nav.allSchemes',
                            'All Schemes (90)'
                          )}
                        </Link>


                        <Link
                          to="/schemes?sort_by=ministry"
                          onClick={() =>
                            setMegaMenuOpen(false)
                          }
                          className="
                            block
                            px-2
                            py-1.5
                            rounded-lg
                            text-xs
                            text-slate-300
                            hover:bg-white/5
                            hover:text-white
                          "
                        >
                          {t(
                            'nav.byMinistry',
                            'By Ministry'
                          )}
                        </Link>


                        <Link
                          to="/schemes?sort_by=category"
                          onClick={() =>
                            setMegaMenuOpen(false)
                          }
                          className="
                            block
                            px-2
                            py-1.5
                            rounded-lg
                            text-xs
                            text-slate-300
                            hover:bg-white/5
                            hover:text-white
                          "
                        >
                          {t(
                            'nav.byCategory',
                            'By Category'
                          )}
                        </Link>


                        <Link
                          to="/schemes?sort_by=sector"
                          onClick={() =>
                            setMegaMenuOpen(false)
                          }
                          className="
                            block
                            px-2
                            py-1.5
                            rounded-lg
                            text-xs
                            text-slate-300
                            hover:bg-white/5
                            hover:text-white
                          "
                        >
                          {t(
                            'nav.bySector',
                            'By Sector'
                          )}
                        </Link>


                        <Link
                          to="/schemes?sort_by=state"
                          onClick={() =>
                            setMegaMenuOpen(false)
                          }
                          className="
                            block
                            px-2
                            py-1.5
                            rounded-lg
                            text-xs
                            text-slate-300
                            hover:bg-white/5
                            hover:text-white
                          "
                        >
                          {t(
                            'nav.byState',
                            'By State Restrictions'
                          )}
                        </Link>

                      </div>

                    </div>


                    {/* FINANCIAL */}

                    <div
                      className="
                        md:col-span-4
                        space-y-2
                        md:border-r
                        border-white/10
                        md:pr-4
                      "
                    >

                      <div
                        className="
                          text-[10px]
                          font-extrabold
                          uppercase
                          text-emerald-400
                          tracking-wider
                          flex
                          items-center
                          gap-1.5
                        "
                      >

                        <Banknote
                          className="w-3.5 h-3.5"
                        />

                        {t(
                          'nav.financialType',
                          'Financial Type'
                        )}

                      </div>


                      <div className="space-y-1">

                        {[
                          {
                            href: '/schemes?financial_type=LOAN',
                            label: 'Loan / Credit Schemes',
                            tag: 'PMMY',
                          },
                          {
                            href: '/schemes?financial_type=SUBSIDY',
                            label: 'Subsidy / Capital Grant',
                            tag: 'PMEGP',
                          },
                          {
                            href: '/schemes?financial_type=SCHOLARSHIP',
                            label: 'Scholarship / Education',
                            tag: 'NSP',
                          },
                          {
                            href: '/schemes?financial_type=TRAINING',
                            label: 'Skill & Training Grants',
                            tag: 'PMKVY',
                          },
                          {
                            href: '/schemes?financial_type=GUARANTEE',
                            label: 'Credit Guarantee Cover',
                            tag: 'CGTMSE',
                          },
                        ].map((item) => (

                          <Link
                            key={item.href}
                            to={item.href}
                            onClick={() =>
                              setMegaMenuOpen(false)
                            }
                            className="
                              flex
                              items-center
                              justify-between
                              px-2
                              py-1.5
                              rounded-lg
                              text-xs
                              text-slate-300
                              hover:bg-white/5
                              hover:text-emerald-300
                            "
                          >

                            <span>
                              {item.label}
                            </span>

                            <span
                              className="
                                text-[9px]
                                bg-white/5
                                px-1.5
                                py-0.5
                                rounded
                                text-slate-400
                                font-mono
                              "
                            >
                              {item.tag}
                            </span>

                          </Link>

                        ))}

                      </div>

                    </div>


                    {/* POPULAR */}

                    <div
                      className="
                        md:col-span-5
                        space-y-2
                      "
                    >

                      <div
                        className="
                          text-[10px]
                          font-extrabold
                          uppercase
                          text-gov-saffron
                          tracking-wider
                          flex
                          items-center
                          gap-1.5
                        "
                      >

                        <Flame
                          className="
                            w-3.5
                            h-3.5
                            text-gov-saffron
                          "
                        />

                        {t(
                          'nav.popularSearches',
                          'Popular Searches'
                        )}

                      </div>


                      <div className="space-y-1">

                        {POPULAR_NATIONAL_SCHEMES
                          .slice(0, 4)
                          .map((scheme) => (

                            <Link
                              key={scheme.id}
                              to={scheme.query}
                              onClick={() =>
                                setMegaMenuOpen(false)
                              }
                              className="
                                block
                                p-2
                                rounded-lg
                                bg-white/[0.035]
                                hover:bg-white/[0.07]
                                border
                                border-transparent
                                hover:border-white/10
                                transition
                              "
                            >

                              <span
                                className="
                                  text-xs
                                  font-bold
                                  text-white
                                "
                              >
                                {scheme.shortName}
                              </span>


                              <p
                                className="
                                  text-[9px]
                                  text-slate-400
                                  line-clamp-1
                                  mt-0.5
                                "
                              >
                                {scheme.tag}
                              </p>

                            </Link>

                          ))}

                      </div>

                    </div>

                  </div>


                  {/* MENU FOOTER */}

                  <div
                    className="
                      mt-4
                      pt-3
                      border-t
                      border-white/10
                      flex
                      items-center
                      justify-between
                      gap-2
                    "
                  >

                    <Link
                      to="/schemes"
                      onClick={() =>
                        setMegaMenuOpen(false)
                      }
                      className="
                        font-bold
                        text-sky-400
                        hover:text-sky-300
                        flex
                        items-center
                        gap-1
                        text-xs
                      "
                    >
                      {t(
                        'nav.advancedSearch',
                        'Advanced Scheme Search'
                      )}

                      <ArrowRight
                        className="w-3.5 h-3.5"
                      />

                    </Link>

                  </div>

                </div>

              )}

            </div>


            {/* SMART MATCHING */}

            <Link
              to="/recommendations"
              className={`
                shrink
                px-2
                2xl:px-3
                py-2
                2xl:py-2.5
                rounded-full
                text-[11px]
                2xl:text-[13px]
                font-medium
                transition
                whitespace-nowrap
                flex
                items-center
                justify-center
                gap-1
                2xl:gap-1.5
                ${
                  isActive('/recommendations')
                    ? 'bg-white/15 text-white'
                    : 'text-white hover:bg-white/10'
                }
              `}
            >

              <Sparkles
                className="
                  w-3
                  h-3
                  2xl:w-3.5
                  2xl:h-3.5
                  text-white
                  shrink-0
                "
              />

              <span>
                {t(
                  'nav.recommendations',
                  'Smart Matching'
                )}
              </span>

            </Link>


            {/* CALCULATOR */}

            <Link
              to="/calculator"
              className={`
                shrink
                px-2
                2xl:px-3
                py-2
                2xl:py-2.5
                rounded-full
                text-[11px]
                2xl:text-[13px]
                font-medium
                transition
                whitespace-nowrap
                flex
                items-center
                justify-center
                gap-1
                2xl:gap-1.5
                ${
                  isActive('/calculator')
                    ? 'bg-white/15 text-white'
                    : 'text-white/80 hover:bg-white/10 hover:text-white'
                }
              `}
            >

              <Calculator
                className="
                  w-3
                  h-3
                  2xl:w-3.5
                  2xl:h-3.5
                  text-white/80
                  shrink-0
                "
              />

              <span>
                {t(
                  'nav.calculator',
                  'Financial Calculator'
                )}
              </span>

            </Link>


            {/* PARTNER */}

            <Link
              to="/channel-partners"
              className={`
                shrink
                px-2
                2xl:px-3
                py-2
                2xl:py-2.5
                rounded-full
                text-[11px]
                2xl:text-[13px]
                font-medium
                transition
                whitespace-nowrap
                flex
                items-center
                justify-center
                gap-1
                2xl:gap-1.5
                ${
                  isActive('/channel-partners')
                    ? 'bg-white/15 text-white'
                    : 'text-white/80 hover:bg-white/10 hover:text-white'
                }
              `}
            >

              <MapPin
                className="
                  w-3
                  h-3
                  2xl:w-3.5
                  2xl:h-3.5
                  text-white/80
                  shrink-0
                "
              />

              <span>
                {t(
                  'nav.partnerLocator',
                  'Find Nearby Partner'
                )}
              </span>

            </Link>


            {/* MORE */}

            <div
              className="relative shrink min-w-0"
              ref={moreMenuRef}
            >

              <button
                type="button"
                onClick={() =>
                  setMoreMenuOpen(
                    !moreMenuOpen
                  )
                }
                className={`
                  px-2
                  2xl:px-3
                  py-2
                  2xl:py-2.5
                  rounded-full
                  text-[11px]
                  2xl:text-[13px]
                  font-medium
                  transition
                  whitespace-nowrap
                  flex
                  items-center
                  justify-center
                  gap-1
                  2xl:gap-1.5
                  ${
                    moreMenuOpen
                      ? 'bg-white/15 text-white'
                      : 'text-white/80 hover:bg-white/10 hover:text-white'
                  }
                `}
                aria-expanded={moreMenuOpen}
                aria-haspopup="true"
              >

                <BookOpen
                  className="
                    w-3
                    h-3
                    2xl:w-3.5
                    2xl:h-3.5
                    text-white/80
                    shrink-0
                  "
                />

                <span>
                  {t(
                    'nav.more',
                    'More'
                  )}
                </span>

                <ChevronDown
                  className={`
                    w-3
                    h-3
                    2xl:w-3.5
                    2xl:h-3.5
                    text-white/60
                    transition-transform
                    ${
                      moreMenuOpen
                        ? 'rotate-180'
                        : ''
                    }
                  `}
                />

              </button>


              {moreMenuOpen && (

                <div
                  className="
                    absolute
                    right-0
                    mt-3
                    w-64
                    bg-[#6f1420]
                    border
                    border-white/10
                    rounded-2xl
                    shadow-2xl
                    py-2
                    z-[120]
                  "
                >

                  <div
                    className="
                      px-4
                      py-2
                      text-[10px]
                      uppercase
                      font-bold
                      text-slate-400
                    "
                  >
                    {t(
                      'nav.infoHelp',
                      'Information & Help'
                    )}
                  </div>


                  <Link
  to="/resources"
  onClick={() => setMoreMenuOpen(false)}
  className="w-full text-left px-4 py-2.5 text-xs flex items-center gap-3 text-slate-200 hover:bg-white/5"
>
  <BookOpen className="w-4 h-4 text-amber-400" />
  <div>
    <div className="text-white font-bold">
      Resources & Guidelines
    </div>
    <span className="text-[10px] text-slate-400">
      Official tools & national guidance
    </span>
  </div>
</Link>

<Link
  to="/faq"
  onClick={() => setMoreMenuOpen(false)}
  className="w-full text-left px-4 py-2.5 text-xs flex items-center gap-3 text-slate-200 hover:bg-white/5"
>
  <HelpCircle className="w-4 h-4 text-emerald-400" />
  <div>
    <div className="text-white font-bold">
      FAQs
    </div>
    <span className="text-[10px] text-slate-400">
      Frequently asked questions
    </span>
  </div>
</Link>



                  <Link
  to="/about"
  onClick={() => setMoreMenuOpen(false)}
  className="
    w-full
    text-left
    px-4
    py-2.5
    text-xs
    flex
    items-center
    gap-3
    text-slate-200
    hover:bg-white/5
  "
>
  <Info
    className="
      w-4
      h-4
      text-sky-400
    "
  />

  <div>
    <div
      className="
        text-white
        font-bold
      "
    >
      {t(
        'nav.aboutYojnaSetu',
        'About YojnaSetu'
      )}
    </div>

    <span
      className="
        text-[10px]
        text-slate-400
      "
    >
      {t(
        'nav.aboutDesc',
        'Zero PII Policy & Engine'
      )}
    </span>
  </div>
</Link>


                  {/* ADMIN */}

                  {isAuthenticated &&
                    role === 'SYSTEM_ADMIN' && (

                      <Link
                        to="/admin"
                        onClick={() =>
                          setMoreMenuOpen(false)
                        }
                        className="
                          flex
                          items-center
                          gap-3
                          px-4
                          py-2.5
                          text-xs
                          text-rose-300
                          hover:bg-rose-950/50
                        "
                      >

                        <ShieldAlert
                          className="
                            w-4
                            h-4
                            text-rose-400
                          "
                        />

                        <span>
                          {t(
                            'nav.adminControlCenter',
                            'Admin Control Center'
                          )}
                        </span>

                      </Link>

                    )}

                </div>

              )}

            </div>


            {/* CITIZEN HUB */}

            {isAuthenticated &&
              role === 'BENEFICIARY' && (

                <div
                  className="relative shrink"
                  ref={citizenMenuRef}
                >

                  <button
                    type="button"
                    onClick={() =>
                      setCitizenMenuOpen(
                        !citizenMenuOpen
                      )
                    }
                    className={`
                      px-2.5
                      2xl:px-4
                      py-2
                      2xl:py-2.5
                      rounded-full
                      text-[12px]
                      2xl:text-sm
                      font-medium
                      transition
                      whitespace-nowrap
                      flex
                      items-center
                      justify-center
                      gap-1.5
                      2xl:gap-2
                      ${
                        isCitizenPathActive ||
                        citizenMenuOpen
                          ? 'bg-white/15 text-white'
                          : 'text-white/80 hover:bg-white/10 hover:text-white'
                      }
                    `}
                  >

                    <User
                      className="
                        w-3.5
                        h-3.5
                        2xl:w-4
                        2xl:h-4
                        shrink-0
                      "
                    />

                    <span>
                      {t(
                        'nav.citizenHub',
                        'Citizen Hub'
                      )}
                    </span>

                    <ChevronDown
                      className={`
                        w-3
                        h-3
                        2xl:w-3.5
                        2xl:h-3.5
                        transition-transform
                        ${
                          citizenMenuOpen
                            ? 'rotate-180'
                            : ''
                        }
                      `}
                    />

                  </button>


                  {citizenMenuOpen && (

                    <div
                      className="
                        absolute
                        right-0
                        mt-3
                        w-60
                        bg-[#6f1420]
                        border
                        border-white/10
                        rounded-2xl
                        shadow-2xl
                        py-2
                        z-[120]
                      "
                    >

                      {[
                        {
                          to: '/profile',
                          icon: User,
                          label: 'My Profile',
                        },
                        {
                          to: '/dashboard',
                          icon: LayoutDashboard,
                          label: 'Citizen Dashboard',
                        },
                        {
                          to: '/applications',
                          icon: FileText,
                          label: 'Applications & Guidance',
                        },
                        {
                          to: '/saved-schemes',
                          icon: Bookmark,
                          label: 'Saved Schemes',
                        },
                      ].map((item) => {

                        const Icon = item.icon;

                        return (

                          <Link
                            key={item.to}
                            to={item.to}
                            onClick={() =>
                              setCitizenMenuOpen(false)
                            }
                            className="
                              flex
                              items-center
                              gap-3
                              px-4
                              py-2.5
                              text-xs
                              text-slate-200
                              hover:bg-white/5
                            "
                          >

                            <Icon
                              className="
                                w-4
                                h-4
                                text-sky-400
                              "
                            />

                            <span>
                              {t(
                                `nav.${item.label
                                  .toLowerCase()
                                  .replaceAll(
                                    ' ',
                                    ''
                                  )}`,
                                item.label
                              )}
                            </span>

                          </Link>

                        );

                      })}

                    </div>

                  )}

                </div>

              )}

          </nav>


          {/* =====================================================
              RIGHT SIDE
              ===================================================== */}

          <div
            className="
              flex
              items-center
              gap-1.5
              lg:gap-2
              2xl:gap-2
              shrink-0
              ml-auto
            "
          >

            {/* ===================================================
                AUTHENTICATED
                =================================================== */}

            {isAuthenticated && user ? (

              <div
                className="
                  flex
                  items-center
                  gap-2
                "
              >

                <NotificationBell />


                <div
                  className="
                    relative
                    hidden
                    md:block
                  "
                  ref={userMenuRef}
                >

                  <button
                    type="button"
                    onClick={() =>
                      setUserMenuOpen(
                        !userMenuOpen
                      )
                    }
                    className="
                      flex
                      items-center
                      gap-2
                      px-2
                      py-1.5
                      rounded-full
                      border
                      border-white/40
                      bg-white/5
                      hover:bg-white/10
                      transition
                    "
                  >

                    <div
                      className="
                        w-8
                        h-8
                        rounded-full
                        bg-[#d7832d]
                        text-[#861823]
                        flex
                        items-center
                        justify-center
                        font-bold
                        text-sm
                        shrink-0
                      "
                    >
                      {user.full_name
                        ? user.full_name
                            .charAt(0)
                            .toUpperCase()
                        : (
                          <User
                            className="
                              w-4
                              h-4
                            "
                          />
                        )}
                    </div>


                    <span
                      className="
                        hidden
                        2xl:block
                        text-sm
                        font-semibold
                        text-white
                        max-w-[120px]
                        truncate
                      "
                    >
                      {user.full_name ||
                        user.email ||
                        user.phone}
                    </span>


                    <ChevronDown
                      className={`
                        w-3.5
                        h-3.5
                        text-white/60
                        transition-transform
                        ${
                          userMenuOpen
                            ? 'rotate-180'
                            : ''
                        }
                      `}
                    />

                  </button>


                  {/* USER DROPDOWN */}

                  {userMenuOpen && (

                    <div
                      className="
                        absolute
                        right-0
                        mt-3
                        w-56
                        bg-[#6f1420]
                        border
                        border-white/10
                        rounded-2xl
                        shadow-2xl
                        py-2
                        z-[120]
                      "
                    >

                      <div
                        className="
                          px-4
                          py-2
                          border-b
                          border-white/10
                        "
                      >

                        <p
                          className="
                            text-xs
                            font-bold
                            text-white
                            truncate
                          "
                        >
                          {user.email ||
                            user.phone}
                        </p>

                        <span
                          className="
                            text-[9px]
                            text-sky-300
                            uppercase
                            font-bold
                          "
                        >
                          {user.role}
                        </span>

                      </div>


                      {role ===
                        'BENEFICIARY' && (

                        <>

                          <Link
                            to="/profile"
                            onClick={() =>
                              setUserMenuOpen(false)
                            }
                            className="
                              flex
                              items-center
                              gap-2.5
                              px-4
                              py-2.5
                              text-xs
                              text-slate-200
                              hover:bg-white/5
                            "
                          >

                            <User
                              className="
                                w-4
                                h-4
                                text-amber-400
                              "
                            />

                            My Profile

                          </Link>


                          <Link
                            to="/dashboard"
                            onClick={() =>
                              setUserMenuOpen(false)
                            }
                            className="
                              flex
                              items-center
                              gap-2.5
                              px-4
                              py-2.5
                              text-xs
                              text-slate-200
                              hover:bg-white/5
                            "
                          >

                            <LayoutDashboard
                              className="
                                w-4
                                h-4
                                text-sky-400
                              "
                            />

                            Citizen Dashboard

                          </Link>

                        </>

                      )}


                      {role ===
                        'SYSTEM_ADMIN' && (

                        <Link
                          to="/admin"
                          onClick={() =>
                            setUserMenuOpen(false)
                          }
                          className="
                            flex
                            items-center
                            gap-2.5
                            px-4
                            py-2.5
                            text-xs
                            text-rose-300
                            hover:bg-rose-950/50
                          "
                        >

                          <ShieldAlert
                            className="
                              w-4
                              h-4
                            "
                          />

                          Admin Control

                        </Link>

                      )}


                      <button
                        type="button"
                        onClick={handleLogout}
                        className="
                          w-full
                          flex
                          items-center
                          gap-2.5
                          px-4
                          py-2.5
                          text-xs
                          text-rose-400
                          hover:bg-rose-950/50
                          border-t
                          border-white/10
                        "
                      >

                        <LogOut
                          className="
                            w-4
                            h-4
                          "
                        />

                        {t(
                          'nav.logout',
                          'Sign Out'
                        )}

                      </button>

                    </div>

                  )}

                </div>

              </div>

            ) : (

              /* =================================================
                 GUEST
                 ================================================= */

              <div
                className="
                  hidden
                  md:flex
                  items-center
                  gap-1.5
                  lg:gap-2
                "
              >

                <form
                  onSubmit={handleSchemeSearch}
                  className="
                    hidden
                    xl:flex
                    items-center
                    w-40
                    2xl:w-48
                    h-9
                    2xl:h-10
                    rounded-full
                    border
                    border-white/35
                    bg-white
                    text-[#861823]
                    overflow-hidden
                    focus-within:ring-2
                    focus-within:ring-[#d7832d]
                    focus-within:ring-offset-2
                    focus-within:ring-offset-[#861823]
                  "
                  role="search"
                >

                  <label
                    htmlFor="navbar-scheme-search"
                    className="sr-only"
                  >
                    Search schemes
                  </label>

                  <input
                    id="navbar-scheme-search"
                    type="search"
                    value={schemeSearch}
                    onChange={(event) =>
                      setSchemeSearch(
                        event.target.value
                      )
                    }
                    placeholder="Search schemes..."
                    className="
                      min-w-0
                      flex-1
                      h-full
                      bg-transparent
                      px-3
                      text-xs
                      2xl:text-[13px]
                      font-medium
                      placeholder:text-slate-500
                      outline-none
                    "
                  />

                  <button
                    type="submit"
                    className="
                      h-full
                      px-2.5
                      2xl:px-3
                      text-[#861823]
                      hover:text-gov-sky
                      transition-colors
                      shrink-0
                    "
                    aria-label="Search schemes"
                  >

                    <Search
                      className="
                        w-4
                        h-4
                        2xl:w-5
                        2xl:h-5
                      "
                    />

                  </button>

                </form>


                {/* SIGN UP */}

                <Link
                  to="/register"
                  className="
                    px-3
                    lg:px-4
                    2xl:px-5
                    py-2
                    2xl:py-2.5
                    rounded-full
                    bg-white
                    text-[#861823]
                    text-xs
                    2xl:text-sm
                    font-semibold
                    hover:bg-[#d7832d]
                    transition
                    whitespace-nowrap
                    shrink-0
                  "
                >
                  {t(
                    'nav.register',
                    'Sign up'
                  )}
                </Link>


                {/* LOG IN */}

                <Link
                  to="/login"
                  className="
                    px-3
                    lg:px-4
                    2xl:px-5
                    py-2
                    2xl:py-2.5
                    rounded-full
                    border
                    border-white
                    text-white
                    text-xs
                    2xl:text-sm
                    font-semibold
                    hover:bg-white
                    hover:text-[#861823]
                    transition
                    whitespace-nowrap
                    shrink-0
                  "
                >
                  {t(
                    'nav.login',
                    'Log in'
                  )}
                </Link>

              </div>

            )}


            {/* MOBILE MATCH */}

            {!isAuthenticated && (

              <Link
                to="/recommendations"
                className="
                  hidden
                  min-[360px]:flex
                  md:hidden
                  items-center
                  gap-1.5
                  bg-gov-saffron
                  text-white
                  px-3
                  py-2
                  rounded-full
                  text-[11px]
                  font-bold
                  shrink-0
                "
              >

                <Sparkles
                  className="w-3 h-3"
                />

                Match

              </Link>

            )}


            {/* MOBILE MENU */}

            <button
              type="button"
              onClick={() =>
                setMobileMenuOpen(
                  !mobileMenuOpen
                )
              }
              className="
                xl:hidden
                p-2.5
                rounded-full
                text-white
                bg-white/5
                hover:bg-white/10
                border
                border-white/20
                min-h-[42px]
                min-w-[42px]
                flex
                items-center
                justify-center
                shrink-0
              "
              aria-expanded={
                mobileMenuOpen
              }
            >

              {mobileMenuOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}

            </button>

          </div>

        </div>

      </div>


      {/* =========================================================
          MOBILE / TABLET DRAWER
          ========================================================= */}

      {mobileMenuOpen && (

        <>

          <div
            className="
              fixed
              inset-0
              bg-slate-950/70
              backdrop-blur-sm
              z-[99]
              xl:hidden
            "
            style={{
              top: `${navHeight}px`,
            }}
            onClick={() =>
              setMobileMenuOpen(false)
            }
          />


          <div
            id="mobile-navigation-drawer"
            className="
              xl:hidden
              fixed
              left-0
              right-0
              w-full
              bg-[#861823]
              px-4
              sm:px-6
              pt-4
              pb-6
              border-t
              border-white/10
              space-y-4
              overflow-y-auto
              shadow-2xl
              z-[100]
            "
            style={{
              top: `${navHeight}px`,
              maxHeight:
                `calc(100dvh - ${navHeight}px)`,
            }}
          >

            {/* PUBLIC NAV */}

            <div
              className="
                rounded-2xl
                border
                border-white/10
                bg-white/[0.025]
                p-2
              "
            >

              <div
                className="
                  px-3
                  py-2
                  text-[10px]
                  font-bold
                  uppercase
                  text-slate-500
                  tracking-wider
                "
              >
                {t(
                  'nav.publicNav',
                  'Public Navigation'
                )}
              </div>


              {[
                {
                  to: '/',
                  icon: Home,
                  label: 'Home',
                },
                {
                  to: '/schemes',
                  icon: Search,
                  label: 'Explore Schemes',
                },
                {
                  to: '/calculator',
                  icon: Calculator,
                  label: 'Financial Calculator',
                },
                {
                  to: '/channel-partners',
                  icon: MapPin,
                  label: 'Find Nearby Partner',
                },
              ].map((item) => {

                const Icon = item.icon;

                return (

                  <Link
                    key={item.to}
                    to={item.to}
                    onClick={() =>
                      setMobileMenuOpen(false)
                    }
                    className="
                      flex
                      items-center
                      gap-3
                      px-3
                      py-3
                      rounded-xl
                      text-sm
                      font-medium
                      text-white/85
                      hover:bg-white/5
                      hover:text-white
                    "
                  >

                    <Icon
                      className="
                        w-4
                        h-4
                        text-sky-400
                      "
                    />

                    <span>
                      {item.label}
                    </span>

                  </Link>

                );

              })}

            </div>


            {/* CITIZEN */}

            {isAuthenticated &&
              role === 'BENEFICIARY' && (

                <div
                  className="
                    border-t
                    border-white/10
                    pt-3
                    space-y-1
                  "
                >

                  <div
                    className="
                      px-3
                      text-[10px]
                      font-bold
                      uppercase
                      text-amber-400
                      tracking-wider
                    "
                  >
                    Citizen Account
                  </div>


                  <Link
                    to="/profile"
                    onClick={() =>
                      setMobileMenuOpen(false)
                    }
                    className="
                      flex
                      items-center
                      gap-3
                      px-3
                      py-2.5
                      rounded-xl
                      text-sm
                      text-white/85
                      hover:bg-white/5
                    "
                  >

                    <User
                      className="
                        w-4
                        h-4
                        text-amber-400
                      "
                    />

                    My Profile

                  </Link>


                  <Link
                    to="/dashboard"
                    onClick={() =>
                      setMobileMenuOpen(false)
                    }
                    className="
                      flex
                      items-center
                      gap-3
                      px-3
                      py-2.5
                      rounded-xl
                      text-sm
                      text-white/85
                      hover:bg-white/5
                    "
                  >

                    <LayoutDashboard
                      className="
                        w-4
                        h-4
                        text-sky-400
                      "
                    />

                    Citizen Dashboard

                  </Link>


                  <Link
                    to="/applications"
                    onClick={() =>
                      setMobileMenuOpen(false)
                    }
                    className="
                      flex
                      items-center
                      gap-3
                      px-3
                      py-2.5
                      rounded-xl
                      text-sm
                      text-white/85
                      hover:bg-white/5
                    "
                  >

                    <FileText
                      className="
                        w-4
                        h-4
                        text-emerald-400
                      "
                    />

                    Applications & Guidance

                  </Link>


                  <Link
                    to="/saved-schemes"
                    onClick={() =>
                      setMobileMenuOpen(false)
                    }
                    className="
                      flex
                      items-center
                      gap-3
                      px-3
                      py-2.5
                      rounded-xl
                      text-sm
                      text-white/85
                      hover:bg-white/5
                    "
                  >

                    <Bookmark
                      className="
                        w-4
                        h-4
                        text-rose-400
                      "
                    />

                    Saved Schemes

                  </Link>

                </div>

              )}


            {/* ADMIN */}

            {isAuthenticated &&
              role === 'SYSTEM_ADMIN' && (

                <div
                  className="
                    border-t
                    border-white/10
                    pt-3
                  "
                >

                  <Link
                    to="/admin"
                    onClick={() =>
                      setMobileMenuOpen(false)
                    }
                    className="
                      flex
                      items-center
                      gap-3
                      px-3
                      py-3
                      rounded-xl
                      text-sm
                      text-rose-300
                      hover:bg-rose-950/50
                    "
                  >

                    <ShieldAlert
                      className="
                        w-4
                        h-4
                      "
                    />

                    Admin Control Center

                  </Link>

                </div>

              )}


            {/* INFORMATION */}

            <div
              className="
                border-t
                border-white/10
                pt-3
                space-y-1
              "
            >

              <div
                className="
                  px-3
                  text-[10px]
                  font-bold
                  uppercase
                  text-slate-500
                "
              >
                Information & Help
              </div>


              <Link
  to="/resources"
  onClick={() => setMobileMenuOpen(false)}
  className="w-full text-left flex items-center gap-3 px-3 py-3 rounded-xl text-sm text-white/85 hover:bg-white/5"
>
  <BookOpen className="w-4 h-4 text-amber-400" />
  Resources & Guidelines
</Link>


              <Link
  to="/about"
  onClick={() => setMobileMenuOpen(false)}
  className="
    w-full
    text-left
    flex
    items-center
    gap-3
    px-3
    py-3
    rounded-xl
    text-sm
    text-white/85
    hover:bg-white/5
  "
>
  <Info
    className="
      w-4
      h-4
      text-sky-400
    "
  />

  About YojnaSetu
</Link>

            </div>


            {/* TEXT SIZE */}

            <div
              className="
                border-t
                border-white/10
                pt-3
              "
            >

              <div
                className="
                  px-3
                  mb-2
                  text-[10px]
                  font-bold
                  uppercase
                  text-slate-500
                "
              >
                Text Size
              </div>


              <div
                className="
                  grid
                  grid-cols-3
                  gap-2
                "
              >

                <button
                  type="button"
                  onClick={() =>
                    setTextSize('small')
                  }
                  className="
                    py-2.5
                    rounded-xl
                    bg-white/5
                    border
                    border-white/10
                    text-white
                    font-bold
                  "
                >
                  A−
                </button>


                <button
                  type="button"
                  onClick={() =>
                    setTextSize('default')
                  }
                  className="
                    py-2.5
                    rounded-xl
                    bg-white/5
                    border
                    border-white/10
                    text-white
                    font-bold
                  "
                >
                  A
                </button>


                <button
                  type="button"
                  onClick={() =>
                    setTextSize('large')
                  }
                  className="
                    py-2.5
                    rounded-xl
                    bg-white/5
                    border
                    border-white/10
                    text-white
                    font-bold
                  "
                >
                  A+
                </button>

              </div>

            </div>


            {/* AUTH */}

            <div
              className="
                border-t
                border-white/10
                pt-3
              "
            >

              {isAuthenticated ? (

                <div
                  className="
                    flex
                    items-center
                    justify-between
                    gap-3
                    p-3
                    rounded-xl
                    bg-white/[0.035]
                    border
                    border-white/10
                  "
                >

                  <div
                    className="
                      min-w-0
                    "
                  >

                    <p
                      className="
                        text-xs
                        font-bold
                        text-white
                        truncate
                      "
                    >
                      {user?.email ||
                        user?.phone}
                    </p>

                    <span
                      className="
                        text-[9px]
                        text-sky-400
                        uppercase
                        font-bold
                      "
                    >
                      {user?.role}
                    </span>

                  </div>


                  <button
                    type="button"
                    onClick={handleLogout}
                    className="
                      px-3
                      py-2
                      rounded-lg
                      bg-rose-950
                      text-rose-300
                      border
                      border-rose-800
                      text-xs
                      font-bold
                      shrink-0
                    "
                  >

                    <LogOut
                      className="
                        w-3.5
                        h-3.5
                        inline
                        mr-1
                      "
                    />

                    Sign Out

                  </button>

                </div>

              ) : (

                <div
                  className="
                    grid
                    grid-cols-2
                    gap-2
                  "
                >

                  <Link
                    to="/login"
                    onClick={() =>
                      setMobileMenuOpen(false)
                    }
                    className="
                      py-3
                      rounded-xl
                      border
                      border-white/30
                      text-white
                      text-center
                      text-sm
                      font-semibold
                    "
                  >
                    Log in
                  </Link>


                  <Link
                    to="/register"
                    onClick={() =>
                      setMobileMenuOpen(false)
                    }
                    className="
                      py-3
                      rounded-xl
                      bg-white
                      text-[#861823]
                      text-center
                      text-sm
                      font-semibold
                    "
                  >
                    Sign up
                  </Link>

                </div>

              )}

            </div>

          </div>

        </>

      )}


      


</header>
  );
};