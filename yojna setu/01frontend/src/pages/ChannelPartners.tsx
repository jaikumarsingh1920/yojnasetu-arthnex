import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { MapLocator } from '../components/MapLocator';
import { schemeApi } from '../api/schemeApi';
import { Scheme } from '../types';
import { Building2, ArrowLeft, Info, ExternalLink, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { OfficialPortalModal } from '../components/OfficialPortalModal';

export const ChannelPartners: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const schemeIdParam = searchParams.get('scheme_id') || '';
  const loanCategoryParam = searchParams.get('loan_category') || '';

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [selectedSchemeId, setSelectedSchemeId] = useState<string>(schemeIdParam);
  const [selectedScheme, setSelectedScheme] = useState<Scheme | null>(null);
  const [selectedPartnerId, setSelectedPartnerId] = useState<string | null>(null);
  const [isPortalModalOpen, setIsPortalModalOpen] = useState(false);

  useEffect(() => {
    fetchSchemes();
  }, []);

  useEffect(() => {
    if (schemeIdParam) {
      setSelectedSchemeId(schemeIdParam);
    }
  }, [schemeIdParam]);

  useEffect(() => {
    if (selectedSchemeId && schemes.length > 0) {
      const s = schemes.find(item => item.scheme_id === selectedSchemeId) || null;
      setSelectedScheme(s);
    } else {
      setSelectedScheme(null);
    }
  }, [selectedSchemeId, schemes]);

  const fetchSchemes = async () => {
    try {
      const res = await schemeApi.getSchemes();
      setSchemes(res.items || []);
    } catch (err) {
      console.error('Failed to fetch schemes list:', err);
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
      <div className="bg-gradient-to-r from-gov-navy via-slate-900 to-gov-blue text-white rounded-3xl p-8 shadow-xl border-b-4 border-gov-saffron space-y-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="bg-gov-saffron text-white px-2.5 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wider">
                {t('channelPartners.geoService', 'GEO-LOCATION SERVICE')}
              </span>
              <span className="text-xs text-sky-300 font-medium">{t('channelPartners.verifiedPartners', 'Verified Partners')}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
              <Building2 className="w-8 h-8 text-gov-saffron" />
              {t('channelPartners.title', 'Find a Nearby Channel Partner')}
            </h1>
            <p className="text-sm text-slate-300 max-w-2xl mt-1">
              {t('channelPartners.subtitle', 'Locate authorized Public Sector Banks, Regional Rural Banks, NBFC-MFIs, and State Channelizing Agencies supporting official welfare schemes in your area.')}
            </p>
          </div>

          <Link
            to="/schemes"
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold px-4 py-2.5 rounded-xl border border-slate-700 transition flex items-center gap-2 shrink-0"
          >
            <ArrowLeft className="w-4 h-4" /> {t('channelPartners.browseAllSchemes', 'Browse All Schemes')}
          </Link>
        </div>

        {/* Scheme Selector */}
        <div className="pt-4 border-t border-slate-700/80 flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <label className="text-xs font-bold text-slate-300 whitespace-nowrap">
            {t('channelPartners.selectedScheme', 'Selected Welfare Scheme:')}
          </label>
          <select
            value={selectedSchemeId}
            onChange={handleSchemeChange}
            className="bg-slate-800 border border-slate-600 text-white text-xs font-medium px-4 py-2.5 rounded-xl focus:ring-2 focus:ring-sky-400 outline-none w-full sm:w-auto sm:min-w-[280px]"
          >
            <option value="">{t('channelPartners.allEligibleSchemes', '-- All Eligible Schemes --')}</option>
            {schemes.map(s => (
              <option key={s.scheme_id} value={s.scheme_id}>
                {s.scheme_name} ({s.scheme_id})
              </option>
            ))}
          </select>

          {selectedScheme && (
            <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4" /> {t('channelPartners.filteringFor', 'Filtering partners for {{scheme}}', { scheme: selectedScheme.scheme_name })}
            </span>
          )}
        </div>
      </div>

      {/* Selected Partner Action Banner */}
      {selectedPartnerId && (
        <div className="bg-emerald-50 border-2 border-emerald-500 rounded-2xl p-6 shadow-md flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-xl shrink-0 mt-0.5">
              ✓
            </div>
            <div>
              <h3 className="font-extrabold text-slate-900 text-base">
                {t('channelPartners.partnerSelected', 'Channel Partner Selected for Application')}
              </h3>
              <p className="text-xs text-slate-600 mt-1 max-w-xl">
                {t('channelPartners.partnerSelectedDesc', 'You have identified an authorized local partner. YojnaSetu provides eligibility guidance and locates verified partners, but final application submission occurs directly on official government/bank portals.')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto">
            {selectedScheme && (
              <button
                onClick={() => setIsPortalModalOpen(true)}
                className="bg-gov-saffron hover:bg-orange-600 text-white font-extrabold text-xs px-6 py-3 rounded-xl shadow-lg transition flex items-center justify-center gap-2 w-full md:w-auto"
              >
                {t('channelPartners.applyOfficialPortal', 'Apply on Official Portal')} <ExternalLink className="w-4 h-4" />
              </button>
            )}
          </div>
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
