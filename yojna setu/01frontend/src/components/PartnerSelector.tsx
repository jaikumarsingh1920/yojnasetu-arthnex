import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { partnerApi, NearestPartnerResponse } from '../api/partnerApi';
import { MapPin, Navigation, Loader2, Building, AlertCircle, ShieldCheck } from 'lucide-react';

interface PartnerSelectorProps {
  onSelectPartner: (partnerId: string) => void;
  selectedPartnerId?: string | null;
}

export const PartnerSelector: React.FC<PartnerSelectorProps> = ({ onSelectPartner, selectedPartnerId }) => {
  const { t } = useTranslation();
  const [partners, setPartners] = useState<NearestPartnerResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchPartners = async (lat: number, lng: number) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await partnerApi.getNearestPartners(lat, lng, 100);
      setPartners(data);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || t('partnerLocator.fetchError', 'Failed to fetch nearby partners.'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleLocateMe = () => {
    if (!navigator.geolocation) {
      setErrorMsg(t('partnerLocator.geoNotSupported', 'Geolocation is not supported by your browser.'));
      return;
    }
    setIsLoading(true);
    setErrorMsg(null);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        fetchPartners(position.coords.latitude, position.coords.longitude);
      },
      (error) => {
        setIsLoading(false);
        setErrorMsg(t('partnerLocator.geoPermissionDenied', 'Location permission denied or unavailable. Please enable location to find nearby partners.'));
      }
    );
  };

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
      <div className="flex items-center gap-2 text-slate-800 font-bold text-lg border-b border-slate-100 pb-2">
        <MapPin className="w-5 h-5 text-indigo-600" />
        {t('channelPartners.selectPartner', 'Select a Channel Partner')}
      </div>
      
      <p className="text-sm text-slate-600">
        {t('partnerLocator.directLoansNotice', 'Direct loans are not processed on this platform. Please select a verified Channel Partner nearby to route your application.')}
      </p>

      {/* Official Data Notice */}
      <div className="bg-sky-50 border border-sky-200 rounded-lg p-3 text-xs text-sky-900 shadow-sm">
        <div className="flex items-center gap-1.5 font-bold mb-1 text-sky-800">
          <ShieldCheck className="w-4 h-4 text-sky-600" />
          {t('partnerLocator.officialDataBadge', 'OFFICIAL NSFDC CHANNEL PARTNER DATA')}
        </div>
        <p className="opacity-90">
          {t('partnerLocator.officialDataDesc', 'Partner organizations are sourced from official NSFDC directories. Geocoded locations represent verified branch locations. Please confirm branch operating status before visiting.')}
        </p>
      </div>

      {partners.length === 0 && !isLoading && (
        <button
          onClick={handleLocateMe}
          className="bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-medium px-4 py-2 rounded-lg border border-indigo-200 transition flex items-center justify-center gap-2 w-full md:w-auto"
        >
          <Navigation className="w-4 h-4" />
          {t('partnerLocator.findNearest', 'Find Nearest Partners')}
        </button>
      )}

      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-indigo-600 font-medium">
          <Loader2 className="w-4 h-4 animate-spin" />
          {t('partnerLocator.locating', 'Locating partners...')}
        </div>
      )}

      {errorMsg && (
        <div className="bg-red-50 text-red-700 p-3 rounded-lg flex items-start gap-2 text-sm border border-red-200">
          <AlertCircle className="w-5 h-5 shrink-0" />
          {errorMsg}
        </div>
      )}

      {partners.length > 0 && (
        <div className="space-y-3 mt-4">
          <h4 className="text-xs font-bold text-slate-500 uppercase">{t('partnerLocator.availablePartners', 'Available Partners')}</h4>
          <div className="grid gap-3">
            {partners.map((p) => {
              const partner = p.partner;
              const isSelected = selectedPartnerId === partner.partner_id;
              
              return (
                <label 
                  key={partner.partner_id} 
                  className={`flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition ${isSelected ? 'border-indigo-600 bg-indigo-50' : 'border-slate-200 bg-white hover:border-indigo-300'}`}
                >
                  <input
                    type="radio"
                    name="partner"
                    value={partner.partner_id}
                    checked={isSelected}
                    onChange={() => onSelectPartner(partner.partner_id)}
                    className="mt-1 w-4 h-4 text-indigo-600 border-slate-300 focus:ring-indigo-600"
                  />
                  <div className="flex-1">
                    <div className="flex justify-between items-start">
                      <div className="font-bold text-slate-900">{partner.name}</div>
                      <div className="text-xs font-bold text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded-full whitespace-nowrap">
                        {p.distance_km} {t('common.km', 'km')}
                      </div>
                    </div>
                    <div className="text-xs text-slate-500 flex items-center gap-1 mt-1">
                      <Building className="w-3.5 h-3.5" />
                      {partner.partner_type} {partner.partner_sub_type ? `(${partner.partner_sub_type})` : ''}
                    </div>
                    {p.is_scheme_matched && (
                      <div className="text-[10px] text-emerald-700 font-semibold bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded mt-1.5 inline-flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3 text-emerald-600" /> {t('partnerLocator.schemeAuthConfirmed', 'Scheme Authorization Confirmed')}
                      </div>
                    )}
                    <div className="text-[10px] text-slate-500 mt-2 flex flex-wrap gap-3">
                      {partner.npa_percentage !== undefined && partner.npa_percentage !== null ? (
                        <span><span className="font-medium">NPA:</span> {partner.npa_percentage}%</span>
                      ) : null}
                      {partner.overdue_percentage !== undefined && partner.overdue_percentage !== null ? (
                        <span><span className="font-medium">Overdue:</span> {partner.overdue_percentage}%</span>
                      ) : null}
                      {(partner.npa_percentage === undefined || partner.npa_percentage === null) &&
                       (partner.overdue_percentage === undefined || partner.overdue_percentage === null) && (
                        <span className="italic text-slate-400">{t('partnerLocator.capacityNotAvailable', 'Current lending capacity/status not available from verified source')}</span>
                      )}
                    </div>
                  </div>
                </label>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
