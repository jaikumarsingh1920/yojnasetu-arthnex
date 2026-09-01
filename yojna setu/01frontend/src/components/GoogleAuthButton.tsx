import React, { useEffect, useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: any) => void;
          renderButton: (parent: HTMLElement, options: any) => void;
          prompt: (momentListener?: (notification: any) => void) => void;
          disableAutoSelect: () => void;
        };
      };
    };
  }
}

interface GoogleAuthButtonProps {
  mode?: 'login' | 'register';
  onSuccess?: () => void;
  onError?: (errorMsg: string) => void;
  className?: string;
}

export const GoogleAuthButton: React.FC<GoogleAuthButtonProps> = ({
  mode = 'login',
  onSuccess,
  onError,
  className = '',
}) => {
  const { t, i18n } = useTranslation();
  const { loginWithGoogle } = useAuth();
  const [isProcessing, setIsProcessing] = useState(false);
  const [gisLoaded, setGisLoaded] = useState(false);
  const googleBtnContainerRef = useRef<HTMLDivElement>(null);

  // Read client ID from environment and clean quotes/whitespace
  const rawClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  const googleClientId =
    typeof rawClientId === 'string' && rawClientId.trim() !== ''
      ? rawClientId.trim().replace(/^["']|["']$/g, '')
      : '';

  const handleCredentialResponse = async (response: any) => {
    const idToken = response?.credential;
    if (!idToken) {
      if (onError) onError(t('auth.googleAuthFailed', 'Google authentication failed to return a credential.'));
      return;
    }

    setIsProcessing(true);
    try {
      await loginWithGoogle(idToken, i18n.language || 'en');
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      let detail = t('auth.googleAuthError', 'Google authentication failed. Please try again.');
      if (err.response?.data?.detail) {
        detail = typeof err.response.data.detail === 'string'
          ? err.response.data.detail
          : JSON.stringify(err.response.data.detail);
      }
      if (onError) {
        onError(detail);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  useEffect(() => {
    // Check if GIS script already exists
    const scriptId = 'google-gsi-client-script';
    let script = document.getElementById(scriptId) as HTMLScriptElement | null;

    const initGis = () => {
      if (!googleClientId) {
        console.warn('VITE_GOOGLE_CLIENT_ID is not configured in 01frontend/.env');
        return;
      }
      if (window.google?.accounts?.id) {
        try {
          window.google.accounts.id.initialize({
            client_id: googleClientId,
            callback: handleCredentialResponse,
            auto_select: false,
            cancel_on_tap_outside: true,
          });
          setGisLoaded(true);

          if (googleBtnContainerRef.current) {
            window.google.accounts.id.renderButton(googleBtnContainerRef.current, {
              type: 'standard',
              theme: 'outline',
              size: 'large',
              text: mode === 'register' ? 'signup_with' : 'signin_with',
              shape: 'rectangular',
              logo_alignment: 'left',
              width: 380,
            });
          }
        } catch (e) {
          console.warn('Google Identity Services initialization notice:', e);
        }
      }
    };

    if (!script) {
      script = document.createElement('script');
      script.id = scriptId;
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = initGis;
      document.body.appendChild(script);
    } else if (window.google?.accounts?.id) {
      initGis();
    }
  }, [mode, googleClientId, i18n.language]);

  // Fallback direct click handler if standard button isn't rendered
  const handleCustomButtonClick = () => {
    if (window.google?.accounts?.id) {
      window.google.accounts.id.prompt();
    } else {
      if (onError) onError(t('auth.googleSdkLoading', 'Google Services are loading. Please try again in a moment.'));
    }
  };

  return (
    <div className={`w-full flex flex-col items-center justify-center ${className}`}>
      {isProcessing && (
        <div className="w-full py-3 px-4 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-center gap-3 text-slate-700 text-xs font-semibold shadow-sm animate-pulse">
          <span className="w-4 h-4 border-2 border-sky-600 border-t-transparent rounded-full animate-spin" />
          <span>{t('auth.verifyingGoogle', 'Verifying with Google Identity...')}</span>
        </div>
      )}

      {!isProcessing && (
        <>
          {/* Official GIS Render Target */}
          <div
            ref={googleBtnContainerRef}
            className={`w-full flex justify-center ${!gisLoaded ? 'hidden' : ''}`}
          />

          {/* Custom Styled Fallback Button if GIS standard iframe is loading or on custom themes */}
          {!gisLoaded && (
            <button
              type="button"
              onClick={handleCustomButtonClick}
              className="w-full py-2.5 px-4 bg-white hover:bg-slate-50 text-slate-700 font-semibold border border-slate-300 rounded-xl text-sm shadow-sm transition flex items-center justify-center gap-3 hover:border-slate-400 active:scale-[0.99]"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>
                {mode === 'register'
                  ? t('auth.continueWithGoogle', 'Continue with Google')
                  : t('auth.signInWithGoogle', 'Sign in with Google')}
              </span>
            </button>
          )}
        </>
      )}
    </div>
  );
};
