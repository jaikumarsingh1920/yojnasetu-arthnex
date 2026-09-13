import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bookmark, LogIn, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { savedSchemesApi } from '../api/savedSchemesApi';

interface SaveSchemeButtonProps {
  schemeId: string;
  initialIsSaved?: boolean;
  onToggle?: (isSaved: boolean) => void;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const SaveSchemeButton: React.FC<SaveSchemeButtonProps> = ({
  schemeId,
  initialIsSaved,
  onToggle,
  size = 'md',
  showLabel = true,
}) => {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [isSaved, setIsSaved] = useState<boolean>(initialIsSaved || false);
  const [loading, setLoading] = useState<boolean>(false);
  const [showLoginModal, setShowLoginModal] = useState<boolean>(false);

  useEffect(() => {
    if (initialIsSaved !== undefined) {
      setIsSaved(initialIsSaved);
      return;
    }

    if (isAuthenticated && schemeId) {
      let isMounted = true;

      savedSchemesApi
        .checkSavedStatus(schemeId)
        .then((res) => {
          if (isMounted) setIsSaved(res.is_saved);
        })
        .catch(() => {});

      return () => {
        isMounted = false;
      };
    }
  }, [schemeId, isAuthenticated, initialIsSaved]);

  const handleToggle = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      setShowLoginModal(true);
      return;
    }

    if (loading) return;

    const previousState = isSaved;
    const nextState = !previousState;

    setIsSaved(nextState);
    setLoading(true);

    try {
      if (nextState) {
        await savedSchemesApi.saveScheme(schemeId);
      } else {
        await savedSchemesApi.removeSavedScheme(schemeId);
      }

      if (onToggle) onToggle(nextState);
    } catch (error) {
      setIsSaved(previousState);
    } finally {
      setLoading(false);
    }
  };

  const buttonSizeClasses = {
    sm: 'px-2.5 py-1 text-xs gap-1',
    md: 'px-3.5 py-1.5 text-sm gap-1.5',
    lg: 'px-5 py-2 text-base gap-2',
  }[size];

  const iconSizes = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  }[size];

  return (
    <>
      <button
        onClick={handleToggle}
        disabled={loading}
        title={
          isSaved
            ? t(
                'savedSchemes.removeSavedTooltip',
                'Remove from Saved Schemes'
              )
            : t(
                'savedSchemes.saveSchemeTooltip',
                'Save Scheme for Later'
              )
        }
        className={`inline-flex items-center font-semibold rounded-lg border transition shadow-sm ${buttonSizeClasses} ${
          isSaved
            ? 'bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100'
            : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50 hover:text-slate-900'
        }`}
      >
        <Bookmark
          className={`w-4 h-4 ${
            isSaved
              ? 'text-amber-500 fill-amber-500'
              : 'text-amber-500'
          }`}
        />

        {showLabel && (
          <span>
            {isSaved
              ? ` ${t('savedSchemes.saved', 'Saved')}`
              : ` ${t('savedSchemes.saveScheme', 'Save Scheme')}`}
          </span>
        )}
      </button>

      {/* Login Required Modal */}
      {showLoginModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-start">
              <div className="w-10 h-10 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center">
                <Bookmark className="w-5 h-5 text-amber-500 shrink-0" />
              </div>

              <button
                onClick={() => setShowLoginModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <h3 className="text-lg font-extrabold text-slate-900">
                {t(
                  'savedSchemes.saveToAccount',
                  'Save Scheme to Account'
                )}
              </h3>

              <p className="text-sm text-slate-600 mt-1">
                {t(
                  'savedSchemes.saveModalDesc',
                  'Please login to save schemes to your account. You can review saved schemes anytime from your dashboard.'
                )}
              </p>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => navigate('/login')}
                className="flex-1 px-4 py-2 bg-gov-blue text-white rounded-lg font-bold text-sm shadow hover:bg-sky-900 transition flex items-center justify-center gap-1.5"
              >
                <LogIn className="w-4 h-4" />
                {t('auth.loginNow', 'Login Now')}
              </button>

              <button
                onClick={() => setShowLoginModal(false)}
                className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg font-semibold text-sm hover:bg-slate-200 transition"
              >
                {t('common.cancel', 'Cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};