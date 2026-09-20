import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { Alert } from '../components/Alert';
import { GoogleAuthButton } from '../components/GoogleAuthButton';
import {
  UserPlus,
  Mail,
  Lock,
  Phone,
  User,
  ShieldCheck,
  Eye,
  EyeOff,
  CheckCircle2,
  ArrowRight,
  Landmark,
  Sparkles,
} from 'lucide-react';

export const Register: React.FC = () => {
  const { t } = useTranslation();
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [agreeTerms, setAgreeTerms] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone && !email) {
      setErrorMsg('Please provide either a mobile number or email address.');
      return;
    }
    if (!password || password.length < 8) {
      setErrorMsg('Password must be at least 8 characters long.');
      return;
    }
    if (!agreeTerms) {
      setErrorMsg('Please agree to the Terms & Conditions to proceed.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      await register({
        email: email ? email.trim() : undefined,
        phone: phone ? phone.trim() : undefined,
        password,
      });
      navigate('/dashboard');
    } catch (err: any) {
      let detail = 'Registration failed. An account with this mobile/email may already exist.';
      if (!err.response) {
        detail = 'Unable to connect to YojnaSetu server. Please check your internet connection.';
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
        
        {/* Left Column: Brand & Citizen Benefits Showcase */}
        <div className="hidden lg:flex lg:col-span-5 flex-col justify-between space-y-6 pr-4">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FFF4EC] border border-[#FFD0CA] text-xs font-bold text-[#4A2525]">
              <span className="w-2 h-2 rounded-full bg-[#2E7D32] animate-pulse" />
              <span>{t('auth.freeRegistrationBadge', 'Free Citizen Registration')}</span>
            </div>

            <h1 className="text-3xl font-black text-[#2B1810] tracking-tight leading-snug">
              {t('auth.unlockBenefitsTitle', 'Unlock Verified Benefits Tailored For You')}
            </h1>

            <p className="text-sm text-[#765E59] leading-relaxed">
              {t('auth.unlockBenefitsSubtitle', 'Create your free citizen profile to automatically evaluate your eligibility across 850+ welfare programs and discover nearest facilitation centers.')}
            </p>
          </div>

          {/* Value Props */}
          <div className="space-y-3 pt-2 border-t border-[#E8D8D2]">
            <div className="flex items-start gap-3 p-3 rounded-xl bg-white/70 border border-[#E8D8D2]">
              <ShieldCheck className="w-5 h-5 text-[#2E7D32] shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-bold text-[#3B2522] block">{t('about.ruleBasedEligibility', 'Deterministic Eligibility Check')}</span>
                <span className="text-[11px] text-[#765E59]">{t('footer.enginePolicyDesc', 'Evaluated directly against official gazettes')}</span>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-xl bg-white/70 border border-[#E8D8D2]">
              <Landmark className="w-5 h-5 text-[#EA717B] shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-bold text-[#3B2522] block">{t('footer.governanceTitle', 'Zero Red Tape & Direct Links')}</span>
                <span className="text-[11px] text-[#765E59]">{t('schemeDetail.applyOfficial', 'Direct application to ministry portals')}</span>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-xl bg-white/70 border border-[#E8D8D2]">
              <Sparkles className="w-5 h-5 text-[#F7AE56] shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-bold text-[#3B2522] block">{t('about.multilingualAccess', '12 Indian Languages')}</span>
                <span className="text-[11px] text-[#765E59]">{t('home.heroChipsLanguages', 'Instant guidance in 12 languages')}</span>
              </div>
            </div>
          </div>

          <div className="text-[11px] text-[#765E59] flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-[#2E7D32]" />
            <span>{t('auth.encryptedPlatform', 'Encrypted, Private & Citizen-First Platform')}</span>
          </div>
        </div>

        {/* Right Column: Modern Civic Registration Card */}
        <div className="w-full lg:col-span-7 max-w-md mx-auto">
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-[#E8D8D2] shadow-warm-md space-y-5">
            
            {/* Top Icon Emblem */}
            <div className="text-center space-y-2">
              <div className="w-14 h-14 rounded-2xl mx-auto flex items-center justify-center bg-[#FFF4EC] text-[#EA717B] border border-[#FFD0CA] shadow-xs">
                <UserPlus className="w-7 h-7" />
              </div>
              <h2 className="text-2xl font-black text-[#2B1810] tracking-tight">
                {t('auth.createAccount', 'Create Your Account')}
              </h2>
              <p className="text-xs text-[#765E59] font-medium">
                {t('auth.createAccountSubtitle', 'Join YojnaSetu and access government schemes')}
              </p>
            </div>

            {errorMsg && <Alert type="error">{errorMsg}</Alert>}

            {/* Registration Form */}
            <form onSubmit={handleSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1">
                  {t('auth.fullName', 'Full Name')}
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Ramesh Kumar"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E8D8D2] bg-[#FFFBF0]/30 text-sm text-[#3B2522] placeholder:text-[#9B817A] focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] focus:bg-white outline-none transition"
                  />
                  <User className="w-4 h-4 text-[#765E59] absolute left-3.5 top-3.5" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1">
                  {t('auth.phoneLabel', 'Mobile Number')} <span className="text-[#EA717B]">*</span>
                </label>
                <div className="relative">
                  <input
                    type="tel"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="9876543210"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E8D8D2] bg-[#FFFBF0]/30 text-sm text-[#3B2522] placeholder:text-[#9B817A] focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] focus:bg-white outline-none transition"
                  />
                  <Phone className="w-4 h-4 text-[#765E59] absolute left-3.5 top-3.5" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1">
                  {t('auth.email', 'Email')} <span className="text-[#765E59] font-normal lowercase">{t('auth.optional', '(optional)')}</span>
                </label>
                <div className="relative">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E8D8D2] bg-[#FFFBF0]/30 text-sm text-[#3B2522] placeholder:text-[#9B817A] focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] focus:bg-white outline-none transition"
                  />
                  <Mail className="w-4 h-4 text-[#765E59] absolute left-3.5 top-3.5" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1">
                  {t('auth.password', 'Password')} <span className="text-[#EA717B]">*</span>
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={t('auth.newPasswordPlaceholder', 'At least 8 characters')}
                    className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-[#E8D8D2] bg-[#FFFBF0]/30 text-sm text-[#3B2522] placeholder:text-[#9B817A] focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] focus:bg-white outline-none transition"
                  />
                  <Lock className="w-4 h-4 text-[#765E59] absolute left-3.5 top-3.5" />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-3.5 text-[#765E59] hover:text-[#3B2522] cursor-pointer"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Consent Checkbox */}
              <div className="pt-1 flex items-start gap-2">
                <input
                  type="checkbox"
                  id="agreeTerms"
                  checked={agreeTerms}
                  onChange={(e) => setAgreeTerms(e.target.checked)}
                  className="mt-0.5 w-4 h-4 rounded text-[#EA717B] focus:ring-[#EA717B] border-[#E8D8D2]"
                />
                <label htmlFor="agreeTerms" className="text-xs text-[#765E59] leading-relaxed cursor-pointer">
                  {t('auth.agreeTerms', 'I agree to the Terms & Conditions and Privacy Policy')}
                </label>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold py-3 px-4 rounded-xl text-sm shadow-warm-xs hover:shadow-warm-sm transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer mt-2"
              >
                {isSubmitting ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <span>{t('auth.registerBtn', 'Create Account')}</span>
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

            {/* Google Authentication */}
            <GoogleAuthButton
              buttonText={t('auth.continueWithGoogle', 'Continue with Google')}
              onError={(error) => setErrorMsg(error)}
            />

            {/* Login Link Footer */}
            <div className="text-center pt-2 text-xs text-[#765E59]">
              {t('auth.hasAccount', 'Already registered?')}{' '}
              <Link
                to="/login"
                className="font-bold text-[#EA717B] hover:text-[#D65D67] underline ml-1 cursor-pointer"
              >
                {t('auth.loginNow', 'Login Now')}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
