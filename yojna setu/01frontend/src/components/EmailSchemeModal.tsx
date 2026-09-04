import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, CheckCircle2, AlertCircle, Loader2, X, Send, ShieldCheck } from 'lucide-react';
import { schemeApi } from '../api/schemeApi';

interface EmailSchemeModalProps {
  isOpen: boolean;
  onClose: () => void;
  schemeId: string;
  schemeName: string;
  defaultEmail?: string;
}

export const EmailSchemeModal: React.FC<EmailSchemeModalProps> = ({
  isOpen,
  onClose,
  schemeId,
  schemeName,
  defaultEmail = '',
}) => {
  const { t, i18n } = useTranslation();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setEmail(defaultEmail || '');
      setError(null);
      setSuccess(false);
      setSuccessMessage(null);
      setLoading(false);
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape' && !loading) {
          onClose();
        }
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, defaultEmail, loading, onClose]);

  if (!isOpen) return null;

  const validateEmail = (val: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val.trim());
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading || success) return;

    const trimmed = email.trim();
    if (!trimmed) {
      setError(t('emailModal.errors.required', 'Please enter your email address.'));
      return;
    }

    if (!validateEmail(trimmed)) {
      setError(t('emailModal.errors.invalid', 'Please enter a valid email address.'));
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await schemeApi.emailScheme(
        schemeId,
        trimmed,
        i18n.language || 'en'
      );

      if (res.sent) {
        setSuccess(true);
        setSuccessMessage(
          res.message ||
          t('emailModal.success', 'Scheme details sent to your email.')
        );
      } else {
        setError(
          res.message ||
          t('emailModal.errors.failed', 'Failed to send scheme details. Please try again.')
        );
      }
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        t('emailModal.errors.failed', 'Failed to send scheme details. Please try again later.');
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !loading) {
      onClose();
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="email-modal-title"
      className="fixed inset-0 z-[110] bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-2xl max-w-[min(94vw,28rem)] max-h-[calc(100dvh-2rem)] overflow-y-auto w-full shadow-2xl border border-slate-200 text-slate-900 flex flex-col">
        {/* Modal Header */}
        <div className="bg-gradient-to-r from-gov-navy to-sky-900 text-white p-4 flex justify-between items-center rounded-t-2xl">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 bg-sky-500/20 rounded-lg flex items-center justify-center border border-sky-400/40 shrink-0">
              <Mail className="w-4 h-4 text-sky-300" />
            </div>
            <div className="min-w-0">
              <h3 id="email-modal-title" className="font-extrabold text-sm truncate">
                {t('emailModal.title', 'Email Scheme Details')}
              </h3>
              <p className="text-[11px] text-sky-200 truncate">
                {t('emailModal.subtitle', 'Receive official scheme overview in your inbox')}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            aria-label="Close dialog"
            className="text-slate-300 hover:text-white p-1 rounded-lg hover:bg-white/10 transition disabled:opacity-50 shrink-0 ml-2 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-4 sm:p-5 space-y-4">
          {/* Scheme Summary Card */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-0.5">
              {t('emailModal.selectedScheme', 'Selected Scheme')}
            </p>
            <p className="font-bold text-slate-900 text-xs sm:text-sm line-clamp-2">
              {schemeName}
            </p>
            <p className="text-[11px] text-slate-500 mt-1 font-mono">
              ID: {schemeId}
            </p>
          </div>

          {success ? (
            /* Success State */
            <div className="space-y-4 py-2 animate-in fade-in zoom-in-95 duration-200 text-center">
              <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center mx-auto text-emerald-600">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <div>
                <h4 className="font-bold text-slate-900 text-sm sm:text-base">
                  {t('emailModal.sentSuccessTitle', 'Scheme Details Sent!')}
                </h4>
                <p className="text-xs text-slate-600 mt-1 px-2">
                  {successMessage || t('emailModal.success', 'Scheme details sent to your email.')}
                </p>
                <p className="text-[11px] text-slate-400 mt-2">
                  {t('emailModal.checkInboxNote', 'Please check your inbox or spam folder in a few moments.')}
                </p>
              </div>
              <div className="pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="w-full py-2.5 px-4 bg-gov-navy hover:bg-slate-800 text-white rounded-xl text-xs sm:text-sm font-semibold transition cursor-pointer"
                >
                  {t('emailModal.closeBtn', 'Done')}
                </button>
              </div>
            </div>
          ) : (
            /* Form State */
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              <div>
                <label
                  htmlFor="scheme-recipient-email"
                  className="block text-xs font-semibold text-slate-700 mb-1.5"
                >
                  {t('emailModal.emailLabel', 'Recipient Email Address')}
                </label>
                <div className="relative">
                  <input
                    ref={inputRef}
                    id="scheme-recipient-email"
                    type="email"
                    name="recipient_email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (error) setError(null);
                    }}
                    disabled={loading}
                    placeholder="name@example.com"
                    autoComplete="email"
                    required
                    className={`w-full px-3.5 py-2.5 text-xs sm:text-sm bg-white border rounded-xl outline-hidden transition ${
                      error
                        ? 'border-rose-400 focus:border-rose-500 focus:ring-2 focus:ring-rose-100'
                        : 'border-slate-300 focus:border-sky-600 focus:ring-2 focus:ring-sky-100'
                    } disabled:bg-slate-100 disabled:text-slate-400`}
                  />
                  <Mail className="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
                {error && (
                  <div className="flex items-center gap-1.5 mt-1.5 text-rose-600 text-[11px] animate-in fade-in">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    <span>{error}</span>
                  </div>
                )}
              </div>

              {/* Privacy Notice */}
              <div className="flex items-start gap-2 bg-sky-50/60 border border-sky-100 rounded-lg p-2.5 text-[11px] text-sky-950">
                <ShieldCheck className="w-4 h-4 text-sky-700 shrink-0 mt-0.5" />
                <p className="leading-relaxed">
                  {t(
                    'emailModal.privacyNote',
                    'Your email is only used to send this official scheme brief. We never share your data or request passwords/Aadhaar.'
                  )}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pt-1">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={loading}
                  className="w-1/2 py-2.5 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs sm:text-sm font-semibold transition disabled:opacity-50 cursor-pointer"
                >
                  {t('emailModal.cancelBtn', 'Cancel')}
                </button>
                <button
                  type="submit"
                  disabled={loading || !email.trim()}
                  className="w-1/2 py-2.5 px-3 bg-gov-navy hover:bg-sky-900 text-white rounded-xl text-xs sm:text-sm font-semibold transition flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm cursor-pointer"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>{t('emailModal.sending', 'Sending...')}</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>{t('emailModal.sendBtn', 'Send Scheme')}</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
