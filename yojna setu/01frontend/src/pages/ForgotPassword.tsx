import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Mail, ArrowLeft, ArrowRight, ShieldCheck, CheckCircle2, KeyRound } from 'lucide-react';
import { authApi } from '../api/authApi';

export const ForgotPassword: React.FC = () => {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const validateEmail = (val: string): boolean => {
    const trimmed = val.trim();
    if (!trimmed) {
      setInlineError(t('auth.enterEmailError', 'Please enter your email address.'));
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmed)) {
      setInlineError(t('auth.validEmailError', 'Please enter a valid email address.'));
      return false;
    }
    setInlineError(null);
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError(null);

    const trimmed = email.trim();
    if (!validateEmail(trimmed)) {
      return;
    }

    setIsSubmitting(true);
    try {
      await authApi.forgotPassword(trimmed);
      setIsSuccess(true);
    } catch (err: any) {
      let msg = t('errors.generalError', 'Unable to process your request at this moment. Please check your connection and try again.');
      if (err?.userFriendlyMessage) {
        msg = err.userFriendlyMessage;
      }
      setServerError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-140px)] bg-[#FFFBF0] flex items-center justify-center px-4 py-8 sm:py-14">
      <div className="max-w-4xl w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left Column: Authoritative Civic Trust & Security Overview */}
        <div className="hidden lg:flex lg:col-span-5 flex-col justify-between space-y-6 pr-4">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FFF4EC] border border-[#FFD0CA] text-xs font-bold text-[#4A2525]">
              <ShieldCheck className="w-4 h-4 text-[#EA717B]" />
              <span>{t('auth.accountRecovery', 'Secure Account Recovery')}</span>
            </div>

            <h1 className="text-3xl font-black text-[#2B1810] tracking-tight leading-snug">
              {t('auth.secureRecoveryTitle', 'Protected Access to Government Support')}
            </h1>

            <p className="text-sm text-[#765E59] leading-relaxed">
              {t('auth.secureRecoveryDesc', 'Your security and privacy are our top priority. YojnaSetu uses time-limited, encrypted reset links to safeguard citizen welfare access.')}
            </p>
          </div>

          <div className="space-y-3 pt-2 border-t border-[#E8D8D2]">
            <div className="flex items-start gap-3 p-3 rounded-xl bg-white/70 border border-[#E8D8D2]">
              <CheckCircle2 className="w-5 h-5 text-[#2E7D32] shrink-0 mt-0.5" />
              <div>
                <h2 className="text-xs font-bold text-[#3B2522]">{t('auth.expiryNoticeTitle', '15-Minute Expiry')}</h2>
                <p className="text-[11px] text-[#765E59]">{t('auth.expiryNoticeDesc', 'Password reset links expire quickly for your protection.')}</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-xl bg-white/70 border border-[#E8D8D2]">
              <CheckCircle2 className="w-5 h-5 text-[#2E7D32] shrink-0 mt-0.5" />
              <div>
                <h2 className="text-xs font-bold text-[#3B2522]">{t('auth.oneTimeTokenTitle', 'One-Time Token')}</h2>
                <p className="text-[11px] text-[#765E59]">{t('auth.oneTimeTokenDesc', 'Tokens are invalidated immediately upon first use.')}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Clean Card */}
        <div className="w-full lg:col-span-7 max-w-md mx-auto">
          <div className="bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-md p-6 sm:p-8">
            {isSuccess ? (
              /* Success State */
              <div className="text-center py-4">
                <div className="w-14 h-14 bg-[#E8F5E9] border border-[#C8E6C9] rounded-2xl flex items-center justify-center mx-auto mb-5 shadow-xs">
                  <Mail className="w-7 h-7 text-[#2E7D32]" />
                </div>

                <h2 className="text-2xl font-black text-[#2B1810] tracking-tight mb-2">
                  {t('auth.checkYourEmail', 'Check your email')}
                </h2>

                <p className="text-sm text-[#765E59] leading-relaxed mb-6 max-w-sm mx-auto">
                  {t('auth.checkEmailDesc', { email: email.trim(), defaultValue: `If an account exists for ${email.trim()}, we've sent password reset instructions.` })}
                </p>

                <div className="p-3.5 bg-[#FFF4EC] border border-[#FFD0CA] rounded-xl text-xs text-[#765E59] text-left mb-6 leading-relaxed">
                  <p className="font-bold text-[#4A2525] mb-1">{t('auth.didntReceiveEmail', "Didn't receive an email?")}</p>
                  <p>{t('auth.spamNotice', 'Check your spam folder or wait a few minutes before trying again. For urgent assistance, reach out to our toll-free helpdesk at 1800-11-2026.')}</p>
                </div>

                <Link
                  to="/login"
                  className="w-full inline-flex items-center justify-center gap-2 py-3 px-4 bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold text-sm rounded-xl shadow-xs transition transform hover:-translate-y-0.5 active:scale-98"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>{t('auth.backToLogin', 'Back to Login')}</span>
                </Link>
              </div>
            ) : (
              /* Initial Form State */
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded-xl bg-[#FFF0EE] border border-[#FFD0CA] flex items-center justify-center">
                    <KeyRound className="w-4 h-4 text-[#EA717B]" />
                  </div>
                  <span className="text-xs font-bold text-[#765E59] uppercase tracking-wider">{t('auth.accountRecovery', 'Account Recovery')}</span>
                </div>

                <h2 className="text-2xl sm:text-3xl font-black text-[#2B1810] tracking-tight mb-2">
                  {t('auth.forgotPasswordTitle', 'Forgot your password?')}
                </h2>
                <p className="text-sm text-[#765E59] leading-relaxed mb-6">
                  {t('auth.forgotPasswordSubtitle', "Enter the email address associated with your YojnaSetu account and we'll help you reset your password.")}
                </p>

                {serverError && (
                  <div className="mb-5 p-3.5 rounded-xl bg-[#FFEBEE] border border-[#FFCDD2] text-[#B71C1C] text-xs font-medium flex items-start gap-2">
                    <span className="font-bold">{t('common.error', 'Error')}:</span> {serverError}
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                  <div>
                    <label htmlFor="email" className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1.5">
                      {t('auth.email', 'Email Address')}
                    </label>
                    <div className="relative">
                      <input
                        id="email"
                        type="email"
                        autoComplete="email"
                        value={email}
                        onChange={(e) => {
                          setEmail(e.target.value);
                          if (inlineError) validateEmail(e.target.value);
                        }}
                        onBlur={() => {
                          if (email) validateEmail(email);
                        }}
                        placeholder="e.g. citizen@example.com"
                        className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${
                          inlineError ? 'border-[#D32F2F] bg-red-50/20' : 'border-[#E8D8D2] bg-[#FFFBF0]/30'
                        } text-sm text-[#3B2522] placeholder:text-[#9B817A] focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] focus:bg-white outline-none transition`}
                      />
                      <Mail className="w-4 h-4 text-[#765E59] absolute left-3.5 top-3.5" />
                    </div>
                    {inlineError && (
                      <p className="mt-1.5 text-xs text-[#D32F2F] font-medium flex items-center gap-1">
                        {inlineError}
                      </p>
                    )}
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full mt-2 py-3 px-4 bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold text-sm rounded-xl shadow-xs transition duration-200 transform hover:-translate-y-0.5 active:scale-98 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    {isSubmitting ? (
                      <span>{t('auth.sending', 'Sending...')}</span>
                    ) : (
                      <>
                        <span>{t('auth.sendResetLink', 'Send Reset Link')}</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </form>

                <div className="mt-6 pt-5 border-t border-[#E8D8D2] text-center">
                  <Link
                    to="/login"
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-[#765E59] hover:text-[#EA717B] transition"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>{t('auth.backToLogin', 'Back to Login')}</span>
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
