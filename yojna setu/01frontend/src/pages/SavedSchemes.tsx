import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Bookmark, Building2, Calendar, Mail, ExternalLink, Trash2, ArrowRight, ShieldCheck } from 'lucide-react';
import { savedSchemesApi, SavedSchemeItem } from '../api/savedSchemesApi';
import { OfficialPortalModal } from '../components/OfficialPortalModal';

export const SavedSchemes: React.FC = () => {
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
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-gov-navy via-slate-900 to-sky-900 text-white p-8 rounded-3xl shadow-xl border border-slate-700 relative overflow-hidden">
        <div className="relative z-10 max-w-3xl space-y-2">
          <div className="inline-flex items-center gap-2 bg-rose-500/20 text-rose-300 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border border-rose-500/30">
            <Bookmark className="w-3.5 h-3.5" />
            BOOKMARKED WELFARE SCHEMES
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Saved Schemes</h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Government schemes you've saved for later. Review eligibility guidelines, estimate loan EMIs, or email details to your inbox anytime.
          </p>
        </div>
      </div>

      {/* Main Content */}
      {loading ? (
        <div className="text-center py-16 space-y-3">
          <div className="w-10 h-10 border-4 border-gov-saffron border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm font-semibold text-slate-600">Loading your saved schemes...</p>
        </div>
      ) : savedItems.length === 0 ? (
        /* Empty State */
        <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center max-w-2xl mx-auto shadow-sm space-y-6">
          <div className="w-16 h-16 bg-rose-50 text-rose-500 rounded-full flex items-center justify-center mx-auto ring-8 ring-rose-50">
            <Bookmark className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h3 className="text-xl font-extrabold text-slate-900">No saved schemes yet</h3>
            <p className="text-sm text-slate-600">
              Found something useful? Save a scheme and come back to it anytime to compare benefits or email details.
            </p>
          </div>
          <div>
            <Link
              to="/schemes"
              className="inline-flex items-center gap-2 bg-gov-saffron hover:bg-orange-600 text-white font-bold px-6 py-3 rounded-xl shadow transition"
            >
              Explore Schemes
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      ) : (
        /* Grid of Saved Schemes */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {savedItems.map((item) => {
            const scheme = item.scheme;
            const status = emailStatus[item.scheme_id];

            return (
              <div
                key={item.id}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition flex flex-col justify-between overflow-hidden group"
              >
                <div className="p-6 space-y-4">
                  {/* Top Row: Tag & Remove */}
                  <div className="flex justify-between items-start gap-2">
                    <span className="text-[11px] font-bold bg-sky-50 text-sky-700 px-2.5 py-1 rounded-md border border-sky-100 uppercase">
                      {scheme.sector || 'Welfare Scheme'}
                    </span>
                    <button
                      onClick={() => handleRemove(item.scheme_id)}
                      title="Remove from saved schemes"
                      className="text-slate-400 hover:text-rose-600 p-1 rounded-lg hover:bg-rose-50 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Title & Ministry */}
                  <div className="space-y-1">
                    <h3 className="font-extrabold text-slate-900 text-lg group-hover:text-sky-700 transition line-clamp-2">
                      {scheme.scheme_name}
                    </h3>
                    <p className="text-xs text-slate-500 flex items-center gap-1.5 font-medium">
                      <Building2 className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                      <span className="truncate">{scheme.ministry || 'Government of India'}</span>
                    </p>
                  </div>

                  {/* Objective Short */}
                  <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                    {scheme.objective || scheme.short_description || 'National government welfare & credit scheme.'}
                  </p>

                  {/* Metrics */}
                  <div className="grid grid-cols-2 gap-2 bg-slate-50 p-3 rounded-xl border border-slate-100 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-500 font-semibold uppercase">Max Benefit</span>
                      <p className="font-extrabold text-slate-900">
                        {scheme.max_loan_amount ? `₹${scheme.max_loan_amount.toLocaleString()}` : 'Varies'}
                      </p>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 font-semibold uppercase">Subsidy</span>
                      <p className="font-extrabold text-emerald-600">
                        {scheme.subsidy_percentage ? `${scheme.subsidy_percentage}%` : 'Standard'}
                      </p>
                    </div>
                  </div>

                  {/* Saved Date */}
                  <div className="flex items-center gap-1 text-[11px] text-slate-400 font-medium pt-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>Saved on {new Date(item.created_at).toLocaleDateString()}</span>
                  </div>

                  {/* Email Feedback status message */}
                  {status && (
                    <div
                      className={`text-xs p-2.5 rounded-lg border font-medium ${
                        status.loading
                          ? 'bg-sky-50 text-sky-800 border-sky-200'
                          : status.success
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                          : 'bg-amber-50 text-amber-800 border-amber-200'
                      }`}
                    >
                      {status.message}
                    </div>
                  )}
                </div>

                {/* Card Actions */}
                <div className="p-4 bg-slate-50 border-t border-slate-100 space-y-2">
                  <div className="grid grid-cols-2 gap-2">
                    <Link
                      to={`/schemes/${item.scheme_id}`}
                      className="px-3 py-2 bg-white text-slate-800 border border-slate-300 hover:bg-slate-100 font-bold text-xs rounded-lg text-center transition flex items-center justify-center gap-1"
                    >
                      View Scheme
                    </Link>
                    <button
                      onClick={() => handleEmailScheme(item.scheme_id)}
                      disabled={status?.loading}
                      className="px-3 py-2 bg-sky-50 text-sky-700 hover:bg-sky-100 border border-sky-200 font-bold text-xs rounded-lg transition flex items-center justify-center gap-1"
                    >
                      <Mail className="w-3.5 h-3.5" />
                      Email Me
                    </button>
                  </div>

                  <button
                    onClick={() => handleOpenPortal(scheme.scheme_name, scheme.application_url)}
                    className="w-full px-3 py-2 bg-gov-saffron hover:bg-orange-600 text-white font-bold text-xs rounded-lg text-center transition flex items-center justify-center gap-1 shadow-sm"
                  >
                    <span>Apply on Official Portal</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Official Portal Redirection Warning Dialog */}
      <OfficialPortalModal
        isOpen={portalModalOpen}
        onClose={() => setPortalModalOpen(false)}
        schemeName={selectedSchemeName}
        officialUrl={selectedOfficialUrl}
      />
    </div>
  );
};
