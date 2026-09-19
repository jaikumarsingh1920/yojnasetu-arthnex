import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bookmark, Building2, Calendar, Mail, ExternalLink, Trash2, ArrowRight, ShieldCheck } from 'lucide-react';
import { savedSchemesApi, SavedSchemeItem } from '../api/savedSchemesApi';
import { OfficialPortalModal } from '../components/OfficialPortalModal';
import { CompareButton } from '../components/CompareButton';

export const SavedSchemes: React.FC = () => {
  const { t } = useTranslation();
  const [savedItems, setSavedItems] = useState<SavedSchemeItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [emailStatus, setEmailStatus] = useState<{ [key: string]: { loading: boolean; message: string; success?: boolean } }>({});
  
  // Official Portal Modal State
  const [portalModalOpen, setPortalModalOpen] = useState<boolean>(false);
  const [selectedSchemeName, setSelectedSchemeName] = useState<string>('');
  const [selectedOfficialUrl, setSelectedOfficialUrl] = useState<string | null>(null);

  const fetchSavedSchemes = async () => {
    setLoading(true);
    try {
      const res = await savedSchemesApi.listSavedSchemes();
      setSavedItems(res.items || []);
    } catch (err) {
      console.error('Failed to load saved schemes:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSavedSchemes();
  }, []);

  const handleRemove = async (schemeId: string) => {
    setSavedItems((prev) => prev.filter((item) => item.scheme_id !== schemeId));
    try {
      await savedSchemesApi.removeSavedScheme(schemeId);
    } catch (err) {
      fetchSavedSchemes();
    }
  };

  const handleEmailScheme = async (schemeId: string) => {
    setEmailStatus((prev) => ({ ...prev, [schemeId]: { loading: true, message: 'Sending email...' } }));
    try {
      const res = await savedSchemesApi.emailScheme(schemeId);
      setEmailStatus((prev) => ({
        ...prev,
        [schemeId]: { loading: false, message: res.message, success: res.sent }
      }));
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || 'Email delivery service is currently unavailable.';
      setEmailStatus((prev) => ({
        ...prev,
        [schemeId]: { loading: false, message: errorMsg, success: false }
      }));
    }
  };

  const handleOpenPortal = (schemeName: string, url?: string | null) => {
    setSelectedSchemeName(schemeName);
    setSelectedOfficialUrl(url || null);
    setPortalModalOpen(true);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner (Warm Theme) */}
      <div className="bg-gradient-to-r from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white p-8 rounded-3xl shadow-warm-md border border-[#E8D8D2]/20 relative overflow-hidden">
        <div className="relative z-10 max-w-3xl space-y-2">
          <div className="inline-flex items-center gap-2 bg-[#F7AE56]/20 text-[#F7AE56] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border border-[#F7AE56]/40">
            <Bookmark className="w-3.5 h-3.5" />
            {t('savedSchemes.title')}
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">{t('savedSchemes.title')}</h1>
          <p className="text-[#FFD0CA]/90 text-sm sm:text-base leading-relaxed">
            {t('savedSchemes.subtitle')}
          </p>
        </div>
      </div>

      {/* Main Content */}
      {loading ? (
        <div className="text-center py-16 space-y-3">
          <div className="w-10 h-10 border-4 border-[#EA717B] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm font-semibold text-[#765E59]">{t('errors.loading')}</p>
        </div>
      ) : savedItems.length === 0 ? (
        /* Empty State */
        <div className="bg-white rounded-3xl border border-[#E8D8D2] p-12 text-center max-w-2xl mx-auto shadow-warm-xs space-y-6">
          <div className="w-16 h-16 bg-[#FFF4EC] text-[#EA717B] rounded-full flex items-center justify-center mx-auto ring-8 ring-[#FFF4EC]">
            <Bookmark className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h3 className="text-xl font-extrabold text-[#3B2522]">{t('savedSchemes.emptyState')}</h3>
          </div>
          <div>
            <Link
              to="/schemes"
              className="inline-flex items-center gap-2 bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold px-6 py-3 rounded-xl shadow-warm-xs transition"
            >
              {t('home.exploreAllSchemes', 'Explore All Schemes')} <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {savedItems.map((item) => (
            <div
              key={item.scheme_id}
              className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md transition flex flex-col justify-between overflow-hidden"
            >
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-[#765E59] bg-[#FFFBF0] px-2 py-0.5 rounded border border-[#E8D8D2]">
                    {item.scheme_id}
                  </span>
                  <button
                    onClick={() => handleRemove(item.scheme_id)}
                    className="text-[#765E59]/50 hover:text-[#EA717B] transition p-1"
                    title={t('savedSchemes.remove')}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div>
                  <h3 className="font-bold text-[#3B2522] text-base leading-snug">
                    {item.scheme?.scheme_name || item.scheme_id}
                  </h3>
                  <p className="text-xs text-[#765E59] mt-1 flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5 text-[#F7AE56]" />
                    {item.scheme?.ministry || 'Government of India'}
                  </p>
                </div>

                {item.scheme?.objective && (
                  <p className="text-xs text-[#765E59] line-clamp-3 leading-relaxed">
                    {item.scheme.objective}
                  </p>
                )}
              </div>

              <div className="p-3.5 sm:p-4 bg-[#FFFBF0] border-t border-[#E8D8D2] flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-1.5 sm:gap-2">
                  <Link
                    to={`/schemes/${item.scheme_id}`}
                    className="text-xs font-bold text-[#EA717B] hover:underline flex items-center gap-1"
                  >
                    {t('schemeCard.viewDetails', 'View Details')} <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                  <CompareButton schemeId={item.scheme_id} schemeName={item.scheme?.scheme_name} variant="compact" />
                </div>

                <button
                  onClick={() => handleEmailScheme(item.scheme_id)}
                  disabled={emailStatus[item.scheme_id]?.loading}
                  className="text-xs font-bold text-[#3B2522] hover:text-[#EA717B] bg-white border border-[#E8D8D2] px-3 py-1.5 rounded-xl shadow-warm-xs flex items-center gap-1.5"
                >
                  <Mail className="w-3.5 h-3.5 text-[#EA717B]" />
                  {emailStatus[item.scheme_id]?.loading ? 'Sending...' : t('savedSchemes.emailMe')}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Official Portal Redirection Dialog */}
      <OfficialPortalModal
        isOpen={portalModalOpen}
        onClose={() => setPortalModalOpen(false)}
        schemeName={selectedSchemeName}
        officialUrl={selectedOfficialUrl}
      />
    </div>
  );
};
