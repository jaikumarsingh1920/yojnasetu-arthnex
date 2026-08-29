import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { SUPPORTED_LANGUAGES } from '../i18n';
import {
  Building2,
  FileText,
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
  ChevronDown
} from 'lucide-react';

import { NotificationBell } from './NotificationBell';

export const Navbar: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { user, isAuthenticated, logout, role } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleLanguageChange = (code: string) => {
    i18n.changeLanguage(code);
    setLangMenuOpen(false);
  };

  const currentLang = SUPPORTED_LANGUAGES.find((l) => l.code === i18n.language) || SUPPORTED_LANGUAGES[0];

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="bg-gov-blue text-white shadow-md border-b-4 border-gov-saffron sticky top-0 z-50">
      {/* Top Emblem Bar */}
      <div className="bg-gov-navy px-4 py-1 text-xs font-medium text-slate-300 flex justify-between items-center border-b border-slate-700">
        <div className="flex items-center gap-2">
          <span className="bg-gov-saffron text-white px-1.5 py-0.5 rounded font-bold text-[10px]">GOVT OF INDIA</span>
          <span>Official National Welfare Portal | yojnasetu.gov.in</span>
        </div>
        <div className="flex items-center gap-4 text-slate-300">
          <span className="hidden sm:inline">Helpline: 1800-11-2026 (Toll-Free)</span>
          
          {/* Language Selector Dropdown */}
          <div className="relative">
            <button
              onClick={() => setLangMenuOpen(!langMenuOpen)}
              className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-white px-2.5 py-1 rounded text-xs font-medium transition border border-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-400"
              aria-label="Select Language"
            >
              <Globe className="w-3.5 h-3.5 text-sky-400" />
              <span>{currentLang.nativeName}</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {langMenuOpen && (
              <div className="absolute right-0 mt-1 w-44 bg-slate-900 border border-slate-700 rounded-md shadow-xl py-1 z-50 max-h-80 overflow-y-auto">
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => handleLanguageChange(lang.code)}
                    className={`w-full text-left px-3 py-1.5 text-xs flex items-center justify-between hover:bg-sky-800 transition ${
                      i18n.language === lang.code ? 'bg-sky-900 text-sky-200 font-bold' : 'text-slate-200'
                    }`}
                  >
                    <span>{lang.nativeName}</span>
                    <span className="text-[10px] text-slate-400">{lang.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center gap-3">
            <img
              src="/logo.png"
              alt="YojnaSetu Logo"
              className="w-10 h-10 rounded-lg object-contain bg-slate-950 p-0.5 border border-slate-700 shadow"
            />
            <div>
              <div className="font-extrabold text-xl tracking-tight text-white flex items-center gap-1.5">
                {t('nav.title')}
                <span className="text-[10px] bg-sky-600 text-white px-2 py-0.5 rounded-full font-semibold uppercase tracking-wider">OFFICIAL</span>
              </div>
              <p className="text-[11px] text-slate-300 font-medium">{t('nav.subtitle')}</p>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-1">
            <Link
              to="/schemes"
              className={`px-3 py-2 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
                isActive('/schemes') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-gov-navy hover:text-white'
              }`}
            >
              <Search className="w-4 h-4 text-sky-400" />
              {t('nav.schemes')}
            </Link>

            <Link
              to="/recommendations"
              className={`px-3 py-2 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
                isActive('/recommendations') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-gov-navy hover:text-white'
              }`}
            >
              <Sparkles className="w-4 h-4 text-gov-saffron" />
              {t('nav.recommendations')}
            </Link>

            <Link
              to="/calculator"
              className={`px-3 py-2 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
                isActive('/calculator') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-gov-navy hover:text-white'
              }`}
            >
              <Calculator className="w-4 h-4 text-emerald-400" />
              {t('nav.calculator')}
            </Link>

            {isAuthenticated && role === 'BENEFICIARY' && (
              <>
                <Link
                  to="/applications"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
                    isActive('/applications') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-gov-navy hover:text-white'
                  }`}
                >
                  <FileText className="w-4 h-4 text-sky-400" />
                  {t('nav.applications')}
                </Link>

                <Link
                  to="/saved-schemes"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
                    isActive('/saved-schemes') ? 'bg-sky-700 text-white' : 'text-slate-200 hover:bg-gov-navy hover:text-white'
                  }`}
                >
                  <Bookmark className="w-4 h-4 text-rose-400" />
                  {t('nav.savedSchemes')}
                </Link>
              </>
            )}

            {isAuthenticated && (role === 'PARTNER_USER' || role === 'PARTNER_ADMIN') && (
              <Link
                to="/partner"
                className={`px-3 py-2 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
                  isActive('/partner') ? 'bg-amber-700 text-white' : 'text-amber-200 hover:bg-amber-900'
                }`}
              >
                <Building2 className="w-4 h-4 text-amber-400" />
                {t('nav.admin')}
              </Link>
            )}

            {isAuthenticated && role === 'SYSTEM_ADMIN' && (
              <Link
                to="/admin"
                className={`px-3 py-2 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
                  isActive('/admin') ? 'bg-rose-700 text-white' : 'text-rose-200 hover:bg-rose-900'
                }`}
              >
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                {t('nav.admin')}
              </Link>
            )}
          </nav>

          {/* User Auth Buttons */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated && user ? (
              <div className="flex items-center gap-3">
                <NotificationBell />
                <div className="flex items-center gap-3 bg-gov-navy px-3 py-1.5 rounded-lg border border-slate-700">
                  <div className="text-right">
                    <p className="text-xs font-bold text-white">{user.email || user.phone}</p>
                    <span className="text-[10px] bg-slate-800 text-sky-300 px-1.5 py-0.5 rounded font-mono uppercase">
                      {user.role}
                    </span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="p-1.5 rounded-md hover:bg-rose-900/60 text-slate-300 hover:text-rose-300 transition"
                    title={t('nav.logout')}
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-gov-navy hover:bg-slate-800 rounded-md border border-slate-600 transition flex items-center gap-1"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  {t('nav.login')}
                </Link>
                <Link
                  to="/register"
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-gov-saffron hover:bg-orange-600 rounded-md shadow transition flex items-center gap-1"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  {t('nav.register')}
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-md text-slate-300 hover:text-white hover:bg-gov-navy"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-gov-navy px-4 pt-2 pb-4 border-t border-slate-700 space-y-2">
          <Link
            to="/schemes"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-base font-medium text-slate-200 hover:bg-slate-800"
          >
            Find Schemes
          </Link>
          <Link
            to="/recommendations"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-base font-medium text-slate-200 hover:bg-slate-800"
          >
            For You
          </Link>
          <Link
            to="/calculator"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-base font-medium text-slate-200 hover:bg-slate-800"
          >
            Loan Calculator
          </Link>
          {isAuthenticated && role === 'BENEFICIARY' && (
            <>
              <Link
                to="/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-base font-medium text-slate-200 hover:bg-slate-800"
              >
                Dashboard
              </Link>
              <Link
                to="/applications"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-base font-medium text-slate-200 hover:bg-slate-800"
              >
                My Applications
              </Link>
            </>
          )}
          {isAuthenticated && (role === 'PARTNER_USER' || role === 'PARTNER_ADMIN') && (
            <Link
              to="/partner"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-md text-base font-medium text-amber-300 hover:bg-amber-900"
            >
              Partner Portal
            </Link>
          )}
          {isAuthenticated && role === 'SYSTEM_ADMIN' && (
            <Link
              to="/admin"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-md text-base font-medium text-rose-300 hover:bg-rose-900"
            >
              Admin Dashboard
            </Link>
          )}

          <div className="pt-4 border-t border-slate-700">
            {isAuthenticated ? (
              <button
                onClick={() => {
                  handleLogout();
                  setMobileMenuOpen(false);
                }}
                className="w-full text-left px-3 py-2 text-rose-400 font-semibold flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Logout ({user?.email || user?.phone})
              </button>
            ) : (
              <div className="flex flex-col gap-2 pt-2">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center px-4 py-2 bg-slate-800 text-white font-semibold rounded-md"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center px-4 py-2 bg-gov-saffron text-white font-semibold rounded-md"
                >
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
