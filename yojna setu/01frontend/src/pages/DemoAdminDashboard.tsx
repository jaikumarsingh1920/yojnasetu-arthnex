import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  ShieldCheck,
  Info,
  User,
  Lock,
  Eye,
  EyeOff,
  Sparkles,
} from 'lucide-react';
import { AdminDashboard } from './AdminDashboard';
import { Navbar } from '../components/Navbar';
import { Footer } from '../components/Footer';
import { useAuth } from '../context/AuthContext';

export const DemoAdminDashboard: React.FC = () => {
  const { t } = useTranslation();
  const { user, login } = useAuth();

  const [isAuthenticatedDemo, setIsAuthenticatedDemo] = useState<boolean>(() => {
    // Only allow if sessionStorage flag AND user is SYSTEM_ADMIN
    return (
      typeof window !== 'undefined' &&
      sessionStorage.getItem('yojnasetu_demo_admin_authenticated') === 'true' &&
      (() => {
        try {
          const saved = localStorage.getItem('yojnasetu_user');
          if (!saved) return false;
          const u = JSON.parse(saved);
          return u?.role === 'SYSTEM_ADMIN';
        } catch {
          return false;
        }
      })()
    );
  });

  const [adminUsername, setAdminUsername] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [showAdminPassword, setShowAdminPassword] = useState(false);
  const [adminLoginError, setAdminLoginError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Sync if auth state changes externally (e.g., page refresh with existing session)
  useEffect(() => {
    if (user?.role === 'SYSTEM_ADMIN') {
      sessionStorage.setItem('yojnasetu_demo_admin_authenticated', 'true');
      setIsAuthenticatedDemo(true);
    }
  }, [user]);

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminUsername.trim() || !adminPassword) {
      setAdminLoginError('Please enter your Demo Admin email and password.');
      return;
    }

    setAdminLoginError(null);
    setIsLoggingIn(true);

    try {
      // Always use the exact credentials typed by the user — no bypass
      const res = await login({
        username: adminUsername.trim(),
        password: adminPassword,
      });

      if (res.user?.role !== 'SYSTEM_ADMIN') {
        // Only SYSTEM_ADMIN role is allowed in Demo Admin
        setAdminLoginError('Access denied. Demo Admin requires a SYSTEM_ADMIN account.');
        return;
      }

      sessionStorage.setItem('yojnasetu_demo_admin_authenticated', 'true');
      setIsAuthenticatedDemo(true);
    } catch (err: any) {
      let detail = 'Invalid email or password.';
      if (!err.response) {
        detail = 'Unable to connect to the server. Please check your internet connection.';
      } else if (err.response.status === 401) {
        detail = 'Invalid email or password.';
      } else if (err.response.status === 403) {
        detail = 'Account is deactivated.';
      } else if (typeof err.response?.data?.detail === 'string') {
        detail = err.response.data.detail;
      }
      setAdminLoginError(detail);
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem('yojnasetu_demo_admin_authenticated');
    setIsAuthenticatedDemo(false);
    setAdminUsername('');
    setAdminPassword('');
  };

  if (!isAuthenticatedDemo) {
    return (
      <div className="min-h-screen bg-[#FFFBF0] flex flex-col justify-between">
        <div className="flex-1 flex items-center justify-center p-4 sm:p-6">
          <div className="max-w-md w-full bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-md p-6 sm:p-8 space-y-6">
            <div className="text-center space-y-2">
              <div className="w-14 h-14 rounded-2xl mx-auto flex items-center justify-center bg-[#FFF4EC] text-[#EA717B] border border-[#FFD0CA] shadow-xs">
                <ShieldCheck className="w-7 h-7" />
              </div>
              <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-[#FFF4EC] text-[#4A2525] border border-[#FFD0CA] text-[11px] font-bold">
                <Sparkles className="w-3 h-3 text-[#EA717B]" />
                <span>{t('demoAdmin.demoEnvBadge', 'Interactive Demo Sandbox')}</span>
              </div>
              <h1 className="text-2xl font-black text-[#2B1810] tracking-tight">
                {t('demoAdmin.adminPortalTitle', 'Demo Admin Gateway')}
              </h1>
              <p className="text-xs text-[#765E59] font-medium">
                {t(
                  'demoAdmin.adminSubtitle',
                  'Experience the full System Admin Dashboard. All changes are visually simulated — database writes are blocked.'
                )}
              </p>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#FFF4EC] border border-[#F7AE56]/30 text-xs text-[#4A2525] space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-[#3B2522]">
                <Info className="w-3.5 h-3.5 text-[#EA717B]" />
                <span>Demo Admin Credentials:</span>
              </div>
              <p className="text-[11px] text-[#765E59] font-mono leading-relaxed">
                ID: <span className="font-bold text-[#3B2522]">demo-admin@yojnasetu.gov.in</span>
                <br />
                Pass: <span className="font-bold text-[#3B2522]">Secret123!</span>
              </p>
            </div>

            {adminLoginError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium">
                {adminLoginError}
              </div>
            )}

            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1.5">
                  {t('demoAdmin.emailOrUsername', 'Email or Username')}
                </label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    value={adminUsername}
                    onChange={(e) => setAdminUsername(e.target.value)}
                    placeholder="demo-admin@yojnasetu.gov.in"
                    autoComplete="username"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E8D8D2] bg-[#FFFBF0]/30 text-sm text-[#3B2522] placeholder:text-[#9B817A] focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] focus:bg-white outline-none transition"
                  />
                  <User className="w-4 h-4 text-[#765E59] absolute left-3.5 top-3.5" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1.5">
                  {t('demoAdmin.passwordLabel', 'Password')}
                </label>
                <div className="relative">
                  <input
                    type={showAdminPassword ? 'text' : 'password'}
                    required
                    value={adminPassword}
                    onChange={(e) => setAdminPassword(e.target.value)}
                    placeholder="••••••••••••"
                    autoComplete="current-password"
                    className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-[#E8D8D2] bg-[#FFFBF0]/30 text-sm text-[#3B2522] placeholder:text-[#9B817A] focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] focus:bg-white outline-none transition"
                  />
                  <Lock className="w-4 h-4 text-[#765E59] absolute left-3.5 top-3.5" />
                  <button
                    type="button"
                    onClick={() => setShowAdminPassword(!showAdminPassword)}
                    className="absolute right-3.5 top-3 text-[#765E59] hover:text-[#3B2522] transition"
                    aria-label={showAdminPassword ? 'Hide password' : 'Show password'}
                  >
                    {showAdminPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoggingIn}
                className="w-full py-2.5 px-4 rounded-xl bg-[#EA717B] hover:bg-[#d65f69] text-white text-sm font-bold shadow-warm-sm transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-70"
              >
                {isLoggingIn ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <span>{t('demoAdmin.signInBtn', 'Sign In to Demo Admin')}</span>
                )}
              </button>
            </form>

            <div className="text-center pt-2 border-t border-[#E8D8D2]">
              <Link
                to="/"
                className="text-xs text-[#765E59] hover:text-[#EA717B] font-medium transition"
              >
                {t('demoAdmin.returnToCitizen', 'Return to Citizen Portal')}
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#FFFBF0] text-[#3B2522] w-full max-w-full">
      <Navbar />
      <main className="flex-grow w-full max-w-full min-w-0">
        <AdminDashboard isDemoMode={true} onDemoLogout={handleLogout} />
      </main>
      <Footer />
    </div>
  );
};
