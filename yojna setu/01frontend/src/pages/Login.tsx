import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { Alert } from '../components/Alert';
import { GoogleAuthButton } from '../components/GoogleAuthButton';
import {
  LogIn,
  Lock,
  Mail,
  ShieldCheck,
  Eye,
  EyeOff,
  CheckCircle2,
  ArrowRight,
  Landmark,
  Sparkles,
} from 'lucide-react';

export const Login: React.FC = () => {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setErrorMsg('Please provide both email/phone and password.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const loginRes = await login({ username: username.trim(), password });
      const userRole = loginRes?.user?.role;
      const loggedEmail = (loginRes?.user?.email || '').toLowerCase();
      const typedUser = username.trim().toLowerCase();

      // Demo-admin check takes priority over any redirect destination
      const isDemoAccount =
        loggedEmail === 'demo-admin@yojnasetu.gov.in' ||
        typedUser === 'demo-admin' ||
        typedUser === 'admin-demo' ||
        typedUser === 'demo-admin@yojnasetu.gov.in';

      if (isDemoAccount && userRole === 'SYSTEM_ADMIN') {
        sessionStorage.setItem('yojnasetu_demo_admin_authenticated', 'true');
        navigate('/demo-admin', { replace: true });
      } else {
        const searchParams = new URLSearchParams(location.search);
        const queryRedirect = searchParams.get('redirect');
        const targetFrom = (location.state as any)?.from?.pathname;
        const destination =
          queryRedirect ||
          (targetFrom && targetFrom !== '/' && targetFrom !== '/login' ? targetFrom : null);

        if (destination) {
          navigate(destination, { replace: true });
        } else if (userRole === 'SYSTEM_ADMIN') {
          navigate('/admin', { replace: true });
        } else {
          navigate('/dashboard', { replace: true });
        }
      }
    } catch (err: any) {
      let detail = 'Invalid email/phone or password.';
      if (!err.response) {
        detail = 'Unable to connect to YojnaSetu server. Please check your internet connection.';
      } else if (err.response.status === 401) {
        detail = 'Invalid email/phone or password.';
      } else if (err.response.status === 403) {
        detail = 'User account is deactivated.';
      } else if (typeof err.response?.data?.detail === 'string') {
        detail = err.response.data.detail;
      } else if (Array.isArray(err.response?.data?.detail)) {
        detail = err.response.data.detail.map((d: any) => d.msg).join(', ');
      }
      setErrorMsg(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-140px)] bg-[#FFFBF0] flex items-center justify-center px-4 py-8 sm:py-14">
      <div className="max-w-4xl w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        
        {/* Left Column: Civic Brand & Trust Showcase (Visible on Large Screens) */}
        <div className="hidden lg:flex lg:col-span-5 flex-col justify-between space-y-6 pr-4">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FFF4EC] border border-[#FFD0CA] text-xs font-bold text-[#4A2525]">
              <span className="w-2 h-2 rounded-full bg-[#EA717B] animate-pulse" />
              <span>{t('auth.gatewayBadge', 'National Welfare Gateway')}</span>
            </div>

            <h1 className="text-3xl font-black text-[#2B1810] tracking-tight leading-snug">
              {t('auth.gatewayTitle', 'Direct Civic Access for Every Citizen')}
            </h1>

            <p className="text-sm text-[#765E59] leading-relaxed">
              {t('auth.gatewaySubtitle', 'Log in to track your government scheme applications, explore personalized eligibility matches, and verify partner transparency.')}
            </p>
          </div>

          {/* Trust Highlights */}
          <div className="space-y-3 pt-2 border-t border-[#E8D8D2]">
            <div className="flex items-start gap-3 p-3 rounded-xl bg-white/70 border border-[#E8D8D2]">
              <ShieldCheck className="w-5 h-5 text-[#2E7D32] shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-bold text-[#3B2522] block">{t('footer.gazetteVerified', '859+ Gazette Verified Schemes')}</span>
                <span className="text-[11px] text-[#765E59]">{t('footer.allSchemes', 'Central and state government portfolios')}</span>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-xl bg-white/70 border border-[#E8D8D2]">
              <Landmark className="w-5 h-5 text-[#EA717B] shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-bold text-[#3B2522] block">{t('footer.governanceTitle', 'Statutory Institutional Transparency')}</span>
                <span className="text-[11px] text-[#765E59]">{t('footer.governanceDesc', 'Official RBI & public registry reporting')}</span>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-xl bg-white/70 border border-[#E8D8D2]">
              <Sparkles className="w-5 h-5 text-[#F7AE56] shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-bold text-[#3B2522] block">{t('about.multilingualAccess', '12 Indian Languages')}</span>
                <span className="text-[11px] text-[#765E59]">{t('home.heroChipsLanguages', 'Complete regional accessibility')}</span>
              </div>
            </div>
          </div>

          <div className="text-[11px] text-[#765E59] flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-[#2E7D32]" />
            <span>{t('auth.dpiReference', 'Official Digital Public Infrastructure Reference')}</span>
          </div>
        </div>

        {/* Right Column: Modern Civic Login Card */}
        <div className="w-full lg:col-span-7 max-w-md mx-auto">
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-[#E8D8D2] shadow-warm-md space-y-5">
            
            {/* Top Icon Emblem */}
            <div className="text-center space-y-2">
              <div className="w-14 h-14 rounded-2xl mx-auto flex items-center justify-center bg-[#FFF4EC] text-[#EA717B] border border-[#FFD0CA] shadow-xs">
                <LogIn className="w-7 h-7" />
              </div>
              <h2 className="text-2xl font-black text-[#2B1810] tracking-tight">
                {t('auth.welcomeBack', 'Welcome Back')}
              </h2>
              <p className="text-xs text-[#765E59] font-medium">
                {t('auth.accessAccount', 'Access your YojnaSetu account')}
              </p>
            </div>

            {errorMsg && <Alert type="error">{errorMsg}</Alert>}

            {/* Login Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1.5">
                  {t('auth.emailOrPhone', 'Email or Mobile')}
                </label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder={t('auth.emailOrPhonePlaceholder', 'e.g. citizen@example.com or 9876543210')}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E8D8D2] bg-[#FFFBF0]/30 text-sm text-[#3B2522] placeholder:text-[#9B817A] focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] focus:bg-white outline-none transition"
                  />
                  <Mail className="w-4 h-4 text-[#765E59] absolute left-3.5 top-3.5" />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider">
                    {t('auth.password', 'Password')}
                  </label>
                  <Link
                    to="/forgot-password"
                    className="text-[11px] font-semibold text-[#EA717B] hover:underline cursor-pointer"
                  >
                    {t('auth.forgotPassword', 'Forgot password?')}
                  </Link>
                </div>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-[#E8D8D2] bg-[#FFFBF0]/30 text-sm text-[#3B2522] placeholder:text-[#9B817A] focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] focus:bg-white outline-none transition"
                  />
                  <Lock className="w-4 h-4 text-[#765E59] absolute left-3.5 top-3.5" />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-3.5 text-[#765E59] hover:text-[#3B2522] cursor-pointer"
                    aria-label={showPassword ? t('auth.hidePassword', 'Hide password') : t('auth.showPassword', 'Show password')}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold py-3 px-4 rounded-xl text-sm shadow-warm-xs hover:shadow-warm-sm transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
              >
                {isSubmitting ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <span>{t('auth.signInBtn', 'Sign In')}</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="relative flex items-center justify-center my-2">
              <div className="border-t border-[#E8D8D2] w-full" />
              <span className="bg-white px-3 text-[11px] font-bold text-[#765E59] uppercase tracking-widest absolute">
                {t('common.or', 'or')}
              </span>
            </div>

            {/* Google Authentication Button */}
            <div>
              <GoogleAuthButton
                mode="login"
                onSuccess={() => {
                  const targetFrom = (location.state as any)?.from?.pathname;
                  if (targetFrom && targetFrom !== '/' && targetFrom !== '/login') {
                    navigate(targetFrom, { replace: true });
                  } else {
                    navigate('/dashboard', { replace: true });
                  }
                }}
                onError={(msg) => setErrorMsg(msg)}
              />
            </div>

            {/* Register Link */}
            <div className="text-center pt-3 border-t border-[#E8D8D2] text-xs text-[#765E59]">
              {t('auth.noAccount', "Don't have an account?")}{' '}
              <Link to="/register" className="font-bold text-[#EA717B] hover:underline">
                {t('nav.register', 'Register')}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
