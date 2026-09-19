import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { Alert } from '../components/Alert';
import { GoogleAuthButton } from '../components/GoogleAuthButton';
import { LogIn, Lock, Mail, ShieldCheck } from 'lucide-react';

export const Login: React.FC = () => {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
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
      const targetFrom = (location.state as any)?.from?.pathname;

      if (targetFrom && targetFrom !== '/' && targetFrom !== '/login') {
        navigate(targetFrom, { replace: true });
      } else if (userRole === 'SYSTEM_ADMIN') {
        navigate('/admin', { replace: true });
      } else {
        navigate('/dashboard', { replace: true });
      }
    } catch (err: any) {
      let detail = 'Invalid email/phone or password.';
      if (!err.response) {
        detail = 'Unable to connect to YojnaSetu server. Please try again.';
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
    <div className="max-w-md mx-auto my-6 sm:my-12 px-3 sm:px-4">
      <div className="bg-white p-5 sm:p-8 rounded-2xl border border-[#E8D8D2] shadow-warm-md space-y-5 sm:space-y-6">
        <div className="text-center space-y-2">
          <div className="w-16 h-16 rounded-2xl mx-auto flex items-center justify-center bg-[#FFF4EC] p-2 shadow-warm-xs border border-[#E8D8D2]">
            <img
              src="/logo.png"
              alt="YojnaSetu Logo"
              className="w-full h-full object-contain"
            />
          </div>
          <h2 className="text-2xl font-extrabold text-[#3B2522]">{t('auth.loginTitle')}</h2>
          <p className="text-xs text-[#765E59]">{t('auth.loginSubtitle')}</p>
        </div>

        {errorMsg && <Alert type="error">{errorMsg}</Alert>}

        {/* Google Authentication Button */}
        <div className="space-y-4">
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

          <div className="relative flex items-center justify-center">
            <div className="border-t border-[#E8D8D2] w-full" />
            <span className="bg-white px-3 text-[11px] font-bold text-[#765E59] uppercase tracking-widest absolute">
              {t('common.or', 'OR')}
            </span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1">
              {t('auth.emailOrPhone')}
            </label>
            <div className="relative">
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={t('auth.emailOrPhonePlaceholder', 'e.g. ben10@example.com or 9876543210')}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E8D8D2] bg-[#FFFBF0]/40 text-sm text-[#3B2522] placeholder:text-[#9B817A] focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] outline-none transition"
              />
              <Mail className="w-4 h-4 text-[#765E59] absolute left-3 top-3.5" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1">
              {t('auth.password')}
            </label>
            <div className="relative">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E8D8D2] bg-[#FFFBF0]/40 text-sm text-[#3B2522] placeholder:text-[#9B817A] focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] outline-none transition"
              />
              <Lock className="w-4 h-4 text-[#765E59] absolute left-3 top-3.5" />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-[#EA717B] hover:bg-[#d65f69] text-white font-bold py-3 px-4 rounded-xl text-sm shadow-warm-xs transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isSubmitting ? (
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                {t('auth.signInBtn', 'Sign In')}
              </>
            )}
          </button>
        </form>

        <div className="text-center pt-2 border-t border-[#E8D8D2] text-xs text-[#765E59]">
          {t('auth.noAccount')}{' '}
          <Link to="/register" className="font-bold text-[#EA717B] hover:underline">
            {t('auth.registerBtn')}
          </Link>
        </div>
      </div>
    </div>
  );
};
