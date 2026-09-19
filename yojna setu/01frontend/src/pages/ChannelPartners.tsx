import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { MapLocator } from '../components/MapLocator';
import { schemeApi, SchemeSelectorItem } from '../api/schemeApi';
import { Scheme } from '../types';
import { Building2, ArrowLeft, Info, ExternalLink, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { OfficialPortalModal } from '../components/OfficialPortalModal';

export const ChannelPartners: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const schemeIdParam = searchParams.get('scheme_id') || '';
  const loanCategoryParam = searchParams.get('loan_category') || '';

  const [selectorSchemes, setSelectorSchemes] = useState<SchemeSelectorItem[]>([]);
  const [selectedSchemeId, setSelectedSchemeId] = useState<string>(schemeIdParam);
  const [selectedScheme, setSelectedScheme] = useState<Scheme | null>(null);
  const [selectedPartnerId, setSelectedPartnerId] = useState<string | null>(null);
  const [isPortalModalOpen, setIsPortalModalOpen] = useState(false);
  const [hasProfile, setHasProfile] = useState<boolean>(false);
  const [schemeSearchText, setSchemeSearchText] = useState<string>('');

  const displayedSelectorSchemes = React.useMemo(() => {
    if (!schemeSearchText.trim()) return selectorSchemes;
    const q = schemeSearchText.toLowerCase();
    return selectorSchemes.filter(s =>
      s.scheme_name.toLowerCase().includes(q) ||
      (s.scheme_code && s.scheme_code.toLowerCase().includes(q)) ||
      s.scheme_id.toLowerCase().includes(q)
    );
  }, [selectorSchemes, schemeSearchText]);

  useEffect(() => {
    fetchSelectorSchemes();
    const savedProfile = localStorage.getItem('yojnasetu_beneficiary_profile');
    if (savedProfile) {
      try {
        const p = JSON.parse(savedProfile);
        if (p && Object.keys(p).length > 0) setHasProfile(true);
      } catch (e) {
        // ignore JSON parse error
      }
    }
  }, []);

  useEffect(() => {
    if (schemeIdParam) {
      setSelectedSchemeId(schemeIdParam);
    }
  }, [schemeIdParam]);

  useEffect(() => {
    if (selectedSchemeId) {
      schemeApi.getSchemeById(selectedSchemeId)
        .then(s => setSelectedScheme(s))
        .catch(() => setSelectedScheme(null));
    } else {
      setSelectedScheme(null);
    }
  }, [selectedSchemeId]);

  const fetchSelectorSchemes = async () => {
    try {
      const res = await schemeApi.getSchemeSelector();
      setSelectorSchemes(res || []);
    } catch (err) {
      console.error('Failed to fetch scheme selector items:', err);
    }
  };

  const handleSchemeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedSchemeId(val);
    setSelectedPartnerId(null);
    if (val) {
      setSearchParams({ scheme_id: val });
    } else {
      setSearchParams({});
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white rounded-3xl p-8 shadow-warm-md border border-[#E8D8D2]/20 space-y-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="bg-[#F7AE56] text-[#4A2525] px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider">
                {t('channelPartners.geoService', 'GEO-LOCATION SERVICE')}
              </span>
              <span className="text-xs text-[#FFD0CA] font-medium">{t('channelPartners.verifiedPartners', 'Verified Partners')}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
              <Building2 className="w-8 h-8 text-[#F7AE56]" />
              {t('channelPartners.title', 'Find a Nearby Channel Partner')}
            </h1>
            <p className="text-sm text-[#FFD0CA] max-w-2xl mt-1 leading-relaxed">
              {t('channelPartners.subtitle', 'Locate authorized Public Sector Banks, Regional Rural Banks, NBFC-MFIs, and State Channelizing Agencies supporting official welfare schemes in your area.')}
            </p>
            <p className="text-[11px] text-[#FFD0CA]/80 mt-1 italic">
              Partner coverage is based on currently ingested official and verified source records.
            </p>
          </div>

          <Link
            to="/schemes"
            className="bg-white/10 hover:bg-white/20 text-white text-xs font-bold px-4 py-2.5 rounded-xl border border-white/20 shadow-warm-xs transition flex items-center gap-2 shrink-0"
          >
            <ArrowLeft className="w-4 h-4" /> {t('channelPartners.browseAllSchemes', 'Browse All Schemes')}
          </Link>
        </div>

        {/* Scheme Selector */}
        <div className="pt-4 border-t border-white/15 flex flex-col md:flex-row items-start md:items-center gap-3">
          <label className="text-xs font-bold text-[#FFD0CA] whitespace-nowrap">
            {t('channelPartners.selectedScheme', 'Selected Welfare Scheme:')}
          </label>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full md:w-auto">
            <input
              type="text"
              value={schemeSearchText}
              onChange={(e) => setSchemeSearchText(e.target.value)}
              placeholder="Search 859 schemes by name/code..."
              className="bg-[#3B2522] border border-[#E8D8D2]/30 text-white text-xs px-3 py-2 rounded-xl focus:ring-2 focus:ring-[#EA717B] outline-none w-full sm:w-56 placeholder-[#FFD0CA]/50"
            />
            <select
              value={selectedSchemeId}
              onChange={handleSchemeChange}
              className="bg-[#3B2522] border border-[#E8D8D2]/30 text-white text-xs font-medium px-4 py-2.5 rounded-xl focus:ring-2 focus:ring-[#EA717B] outline-none w-full sm:w-auto sm:min-w-[320px] max-w-lg truncate"
            >
              <option value="">
                {hasProfile
                  ? t('channelPartners.eligibleForProfile', '-- Eligible for your profile --')
                  : t('channelPartners.availableSchemes', '-- All Available Canonical Schemes ({{count}}) --', { count: selectorSchemes.length || 859 })}
              </option>
              {displayedSelectorSchemes.map(s => (
                <option key={s.scheme_id} value={s.scheme_id}>
                  {s.scheme_name} ({s.scheme_code || s.scheme_id})
                </option>
              ))}
            </select>
          </div>

          {selectedScheme ? (
            <div className="flex flex-wrap items-center justify-between gap-2 w-full sm:w-auto">
              <span className="text-xs text-[#FFD0CA] font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-[#F7AE56]" /> {t('channelPartners.filteringFor', 'Filtering partners for {{scheme}}', { scheme: selectedScheme.scheme_name })}
              </span>
              {(selectedScheme.application_url || selectedScheme.official_portal || selectedScheme.official_source_url) && (
                <button
                  type="button"
                  onClick={() => setIsPortalModalOpen(true)}
                  className="bg-[#EA717B] hover:bg-[#d65f69] text-white text-[11px] font-bold px-3 py-1 rounded-xl transition flex items-center gap-1 shadow-warm-xs"
                >
                  <span>{t('channelPartners.applyOfficialPortal', 'Apply on Official Portal')}</span>
                  <ExternalLink className="w-3 h-3" />
                </button>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-[#FFD0CA] pt-1 sm:pt-0">
              <Info className="w-3.5 h-3.5 text-[#F7AE56] shrink-0" />
              <span>{t('partnerLocator.selectSchemeTip', 'Select a specific scheme above to filter channel partners authorized for that scheme.')}</span>
            </div>
          )}
        </div>
      </div>

      {/* Minimal Application Notice */}
{selectedPartnerId && (
  <div className="flex items-center gap-2 px-1 py-1 text-[11px] text-slate-500">
    <Info className="w-3.5 h-3.5 text-amber-500 shrink-0" />
    <span>
      {t('partnerLocator.disclaimerGuidance', 'YojnaSetu only provides eligibility guidance and partner discovery.')}{' '}
      {t('portalModal.disclaimer', 'Applications are submitted directly on official government/bank portals.')}
    </span>
  </div>
)}

      {/* Map Locator Component */}
      <MapLocator
        schemeId={selectedSchemeId || undefined}
        schemeName={selectedScheme?.scheme_name || undefined}
        loanCategory={loanCategoryParam || undefined}
        selectedPartnerId={selectedPartnerId}
        onSelectPartner={(partnerId) => setSelectedPartnerId(partnerId)}
      />

      {/* Official Portal Guidance Modal */}
      {selectedScheme && (
        <OfficialPortalModal
          isOpen={isPortalModalOpen}
          onClose={() => setIsPortalModalOpen(false)}
          schemeName={selectedScheme.scheme_name}
          officialUrl={selectedScheme.application_url || selectedScheme.official_portal || selectedScheme.official_source_url}
        />
      )}
    </div>
  );
};
