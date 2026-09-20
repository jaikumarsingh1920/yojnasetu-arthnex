import React, { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Lock, Eye, EyeOff, ShieldCheck, CheckCircle2, ArrowRight, AlertTriangle, KeyRound, Check } from 'lucide-react';
import { authApi } from '../api/authApi';

export const ResetPassword: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const navigate = useNavigate();

  // Verification state on load
  const [isVerifying, setIsVerifying] = useState(true);
  const [isTokenValid, setIsTokenValid] = useState(false);
  const [tokenErrorMsg, setTokenErrorMsg] = useState<string | null>(null);
  const [maskedEmail, setMaskedEmail] = useState<string | null>(null);

  // Form states
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // Validate token on mount
  useEffect(() => {
    let isMounted = true;

    const checkToken = async () => {
      if (!token || token.trim().length < 16) {
        if (isMounted) {
          setIsTokenValid(false);
          setTokenErrorMsg(t('auth.invalidLinkTitle', 'This reset link is missing or malformed.'));
          setIsVerifying(false);
        }
        return;
      }

      try {
        const res = await authApi.verifyResetToken(token.trim());
        if (isMounted) {
          if (res.valid) {
            setIsTokenValid(true);
            setMaskedEmail(res.email || null);
          } else {
            setIsTokenValid(false);
            setTokenErrorMsg(res.message || t('auth.invalidLinkTitle', 'Reset link has expired or is invalid.'));
          }
        }
      } catch (err: any) {
        if (isMounted) {
          setIsTokenValid(false);
          setTokenErrorMsg(t('errors.networkError', 'Unable to verify this reset link. Please check your network connection.'));
        }
      } finally {
        if (isMounted) {
          setIsVerifying(false);
        }
      }
    };

    checkToken();

    return () => {
      isMounted = false;
    };
  }, [token]);

  const hasMinLength = newPassword.length >= 8;
  const passwordsMatch = newPassword.length > 0 && newPassword === confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!hasMinLength) {
      setFormError(t('auth.minPasswordLengthError', 'Password must be at least 8 characters long.'));
      return;
    }

    if (!passwordsMatch) {
      setFormError(t('auth.passwordMismatchError', 'Passwords do not match. Please re-enter your password.'));
      return;
    }

    setIsSubmitting(true);
    try {
      await authApi.resetPassword(token.trim(), newPassword);
      setIsSuccess(true);
    } catch (err: any) {
      let msg = t('errors.generalError', 'Failed to reset password. The link may have expired or already been used.');
      if (err?.response?.data?.detail) {
        msg = err.response.data.detail;
      } else if (err?.userFriendlyMessage) {
        msg = err.userFriendlyMessage;
      }
      setFormError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-140px)] bg-[#FFFBF0] flex items-center justify-center px-4 py-8 sm:py-14">
      <div className="max-w-4xl w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left Column: Trust Showcase */}
        <div className="hidden lg:flex lg:col-span-5 flex-col justify-between space-y-6 pr-4">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FFF4EC] border border-[#FFD0CA] text-xs font-bold text-[#4A2525]">
              <ShieldCheck className="w-4 h-4 text-[#EA717B]" />
              <span>{t('auth.accountRecovery', 'Identity Protection')}</span>
            </div>

            <h1 className="text-3xl font-black text-[#2B1810] tracking-tight leading-snug">
              {t('auth.secureRecoveryTitle', 'Secure Your YojnaSetu Citizen Portal')}
            </h1>

            <p className="text-sm text-[#765E59] leading-relaxed">
              {t('auth.secureRecoveryDesc', 'Create a strong, unique password to protect your citizen profile, scheme applications, and eligibility data.')}
            </p>
          </div>

          <div className="space-y-3 pt-2 border-t border-[#E8D8D2]">
            <div className="flex items-start gap-3 p-3 rounded-xl bg-white/70 border border-[#E8D8D2]">
              <CheckCircle2 className="w-5 h-5 text-[#2E7D32] shrink-0 mt-0.5" />
              <div>
                <h2 className="text-xs font-bold text-[#3B2522]">{t('auth.encryptedPlatform', 'Encrypted Storage')}</h2>
                <p className="text-[11px] text-[#765E59]">{t('auth.oneTimeTokenDesc', 'Passwords are hashed with standard bcrypt encryption.')}</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-xl bg-white/70 border border-[#E8D8D2]">
              <CheckCircle2 className="w-5 h-5 text-[#2E7D32] shrink-0 mt-0.5" />
              <div>
                <h2 className="text-xs font-bold text-[#3B2522]">{t('auth.dpiReference', 'Immediate Sync')}</h2>
                <p className="text-[11px] text-[#765E59]">{t('auth.secureRecoveryDesc', 'Your new password takes effect immediately across all sessions.')}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Card */}
        <div className="w-full lg:col-span-7 max-w-md mx-auto">
          <div className="bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-md p-6 sm:p-8">
            {isVerifying ? (
              /* Loading / Verifying Token State */
              <div className="text-center py-10">
                <div className="w-10 h-10 border-3 border-[#EA717B] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-sm font-semibold text-[#765E59]">{t('auth.verifyingLink', 'Verifying your reset link...')}</p>
              </div>
            ) : !isTokenValid ? (
              /* Invalid or Expired Token State */
              <div className="text-center py-4">
                <div className="w-14 h-14 bg-[#FFEBEE] border border-[#FFCDD2] rounded-2xl flex items-center justify-center mx-auto mb-5 shadow-xs">
                  <AlertTriangle className="w-7 h-7 text-[#D32F2F]" />
                </div>

                <h2 className="text-2xl font-black text-[#2B1810] tracking-tight mb-2">
                  {t('auth.invalidLinkTitle', 'Reset link expired or invalid')}
                </h2>

                <p className="text-sm text-[#765E59] leading-relaxed mb-6">
                  {tokenErrorMsg || t('auth.returnToForgot', 'Please request a new password reset link.')}
                </p>

                <div className="p-3.5 bg-[#FFF4EC] border border-[#FFD0CA] rounded-xl text-xs text-[#765E59] text-left mb-6 leading-relaxed">
                  <p className="font-bold text-[#4A2525] mb-1">{t('auth.didntReceiveEmail', 'Why did this happen?')}</p>
                  <p>{t('auth.spamNotice', 'Reset links are time-limited to 15 minutes and can only be used once to ensure your account security.')}</p>
                </div>

                <Link
                  to="/forgot-password"
                  className="w-full inline-flex items-center justify-center gap-2 py-3 px-4 bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold text-sm rounded-xl shadow-xs transition transform hover:-translate-y-0.5 active:scale-98"
                >
                  <span>{t('auth.returnToForgot', 'Request New Reset Link')}</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            ) : isSuccess ? (
              /* Success State */
              <div className="text-center py-4">
                <div className="w-14 h-14 bg-[#E8F5E9] border border-[#C8E6C9] rounded-2xl flex items-center justify-center mx-auto mb-5 shadow-xs">
                  <CheckCircle2 className="w-7 h-7 text-[#2E7D32]" />
                </div>

                <h2 className="text-2xl font-black text-[#2B1810] tracking-tight mb-2">
                  {t('auth.passwordResetSuccessTitle', 'Password reset successfully')}
                </h2>

                <p className="text-sm text-[#765E59] leading-relaxed mb-6 max-w-sm mx-auto">
                  {t('auth.passwordResetSuccessDesc', 'Your password has been updated. You can now sign in with your new password.')}
                </p>

                <Link
                  to="/login"
                  className="w-full inline-flex items-center justify-center gap-2 py-3 px-4 bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold text-sm rounded-xl shadow-xs transition transform hover:-translate-y-0.5 active:scale-98"
                >
                  <span>{t('auth.backToLogin', 'Continue to Login')}</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            ) : (
              /* Valid Form State */
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded-xl bg-[#FFF0EE] border border-[#FFD0CA] flex items-center justify-center">
                    <KeyRound className="w-4 h-4 text-[#EA717B]" />
                  </div>
                  <span className="text-xs font-bold text-[#765E59] uppercase tracking-wider">{t('auth.resetPasswordTitle', 'Set New Password')}</span>
                </div>

                <h2 className="text-2xl sm:text-3xl font-black text-[#2B1810] tracking-tight mb-2">
                  {t('auth.resetPasswordTitle', 'Create a new password')}
                </h2>

                <p className="text-sm text-[#765E59] leading-relaxed mb-5">
                  {maskedEmail ? (
                    <>{t('auth.resetPasswordSubtitle', 'Choose a new password for account')} <span className="font-semibold text-[#3B2522]">{maskedEmail}</span>.</>
                  ) : (
                    <>{t('auth.resetPasswordSubtitle', 'Choose a new secure password for your account.')}</>
                  )}
                </p>

                {formError && (
                  <div className="mb-5 p-3.5 rounded-xl bg-[#FFEBEE] border border-[#FFCDD2] text-[#B71C1C] text-xs font-medium flex items-start gap-2">
                    <span className="font-bold">{t('common.error', 'Error')}:</span> {formError}
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                  {/* New Password */}
                  <div>
                    <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1.5">
                      {t('auth.newPassword', 'New Password')}
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        required
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="At least 8 characters"
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

                  {/* Confirm Password */}
                  <div>
                    <label className="block text-xs font-bold text-[#3B2522] uppercase tracking-wider mb-1.5">
                      {t('auth.confirmPassword', 'Confirm New Password')}
                    </label>
                    <div className="relative">
                      <input
                        type={showConfirmPassword ? 'text' : 'password'}
                        required
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="Re-enter your password"
                        className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-[#E8D8D2] bg-[#FFFBF0]/30 text-sm text-[#3B2522] placeholder:text-[#9B817A] focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] focus:bg-white outline-none transition"
                      />
                      <Lock className="w-4 h-4 text-[#765E59] absolute left-3.5 top-3.5" />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3.5 top-3.5 text-[#765E59] hover:text-[#3B2522] cursor-pointer"
                        aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                      >
                        {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Requirement Indicators */}
                  <div className="p-3 bg-[#FFF4EC]/50 border border-[#E8D8D2] rounded-xl space-y-1.5 text-xs">
                    <div className="flex items-center gap-2">
                      <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                        hasMinLength ? 'bg-[#2E7D32] text-white' : 'bg-[#E8D8D2] text-[#765E59]'
                      }`}>
                        <Check className="w-2.5 h-2.5" />
                      </span>
                      <span className={hasMinLength ? 'text-[#2E7D32] font-semibold' : 'text-[#765E59]'}>
                        {t('auth.newPasswordPlaceholder', 'Minimum 8 characters')}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                        passwordsMatch ? 'bg-[#2E7D32] text-white' : 'bg-[#E8D8D2] text-[#765E59]'
                      }`}>
                        <Check className="w-2.5 h-2.5" />
                      </span>
                      <span className={passwordsMatch ? 'text-[#2E7D32] font-semibold' : 'text-[#765E59]'}>
                        {t('auth.confirmPassword', 'Passwords match')}
                      </span>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmitting || !hasMinLength || !passwordsMatch}
                    className="w-full mt-2 py-3 px-4 bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold text-sm rounded-xl shadow-xs transition duration-200 transform hover:-translate-y-0.5 active:scale-98 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    {isSubmitting ? (
                      <span>{t('auth.updating', 'Resetting Password...')}</span>
                    ) : (
                      <>
                        <span>{t('auth.resetButton', 'Reset Password')}</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </form>

                <div className="mt-6 pt-5 border-t border-[#E8D8D2] text-center">
                  <Link
                    to="/login"
                    className="text-xs font-bold text-[#765E59] hover:text-[#EA717B] transition"
                  >
                    {t('auth.backToLogin', 'Back to Login')}
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

export default ResetPassword;
