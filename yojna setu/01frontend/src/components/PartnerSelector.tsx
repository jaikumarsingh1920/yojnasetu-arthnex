import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { partnerApi, NearestPartnerResponse } from '../api/partnerApi';
import {
  getNNPADisplay,
  getSourceDisplay,
  getDataPeriodDisplay,
  getScopeDisplay,
  getRoutingStatusDisplay,
} from '../utils/financialEvidence';
import { localizeRoutingReason } from '../utils/civicLocalization';
import { FinancialIntelligencePanel } from './FinancialIntelligencePanel';
import {
  MapPin,
  Navigation,
  Loader2,
  Building,
  AlertCircle,
  ShieldCheck,
  Compass,
  CheckCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface PartnerSelectorProps {
  onSelectPartner: (partnerId: string) => void;
  selectedPartnerId?: string | null;
}

export const PartnerSelector: React.FC<PartnerSelectorProps> = ({ onSelectPartner, selectedPartnerId }) => {
  const { t, i18n } = useTranslation();
  const [partners, setPartners] = useState<NearestPartnerResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [expandedEvidence, setExpandedEvidence] = useState<Record<string, boolean>>({});

  const toggleEvidence = (partnerId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setExpandedEvidence((prev) => ({ ...prev, [partnerId]: !prev[partnerId] }));
  };

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
        setErrorMsg(
          t('partnerLocator.geoPermissionDenied', 'Location permission denied or unavailable. Please enable location to find nearby partners.')
        );
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
        {t(
          'partnerLocator.directLoansNotice',
          'Direct loans are not processed on this platform. Please select a verified Channel Partner nearby to route your application.'
        )}
      </p>

      {/* Smart Routing Guidance Banner */}
      <div className="bg-gradient-to-r from-indigo-50 via-sky-50 to-blue-50 border border-indigo-100 rounded-xl p-3.5 shadow-2xs space-y-1">
        <div className="flex items-center gap-1.5 text-indigo-950 font-bold text-xs">
          <Compass className="w-4 h-4 text-indigo-600 shrink-0" />
          <span>{t('partnerLocator.smartRoutingTitle', 'Smart Channel Partner Routing')}</span>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed font-medium">
          {t(
            'partnerLocator.smartRoutingDesc',
            'These are nearby channel partners relevant to your scheme, after applying statutory eligibility and financial routing constraints.'
          )}
        </p>
      </div>

      {/* Official Data Notice */}
      <div className="bg-sky-50 border border-sky-200 rounded-lg p-3 text-xs text-sky-900 shadow-sm">
        <div className="flex items-center gap-1.5 font-bold mb-1 text-sky-800">
          <ShieldCheck className="w-4 h-4 text-sky-600" />
          {t('partnerLocator.officialDataBadge', 'OFFICIAL NSFDC CHANNEL PARTNER DATA')}
        </div>
        <p className="opacity-90">
          {t(
            'partnerLocator.officialDataDesc',
            'Partner organizations are sourced from official NSFDC directories. Geocoded locations represent verified branch locations. Please confirm branch operating status before visiting.'
          )}
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
                  className={`block p-4 rounded-xl border-2 cursor-pointer transition ${
                    isSelected ? 'border-indigo-600 bg-white ring-4 ring-indigo-50' : 'border-slate-200 bg-white hover:border-indigo-300'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <input
                      type="radio"
                      name="partner"
                      value={partner.partner_id}
                      checked={isSelected}
                      onChange={() => onSelectPartner(partner.partner_id)}
                      className="mt-1 w-4 h-4 text-indigo-600 border-slate-300 focus:ring-indigo-600 cursor-pointer shrink-0"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start">
                        <div className="font-bold text-slate-900 text-sm leading-snug">{partner.name}</div>
                        <div className="text-xs font-bold text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded-full whitespace-nowrap shrink-0 ml-2">
                          {p.distance_km} {t('common.km', 'km')}
                        </div>
                      </div>
                      <div className="text-xs text-slate-500 flex items-center gap-1 mt-1">
                        <Building className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span>{partner.partner_type} {partner.partner_sub_type ? `(${partner.partner_sub_type})` : ''}</span>
                      </div>
                      {p.is_scheme_matched && (
                        <div className="text-[10px] text-emerald-700 font-semibold bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded mt-1.5 inline-flex items-center gap-1">
                          <ShieldCheck className="w-3 h-3 text-emerald-600" /> {t('partnerLocator.schemeAuthConfirmed', 'Scheme Authorization Confirmed')}
                        </div>
                      )}

                      {/* Routing & Financial Evidence Status Badges */}
                      <div className="mt-2 flex flex-wrap gap-1.5 items-center">
                        {p.routing_status && (
                          <span
                            className={`inline-flex items-center gap-1 text-[9px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider ${
                              p.routing_status === 'VERIFIED_ELIGIBLE_FOR_ROUTING'
                                ? 'bg-emerald-50 text-emerald-800 border border-emerald-300'
                                : 'bg-slate-100 text-slate-800 border border-slate-300'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                p.routing_status === 'VERIFIED_ELIGIBLE_FOR_ROUTING' ? 'bg-emerald-600' : 'bg-slate-500'
                              }`}
                            ></span>
                            {getRoutingStatusDisplay(
                              p.routing_status,
                              t('partnerLocator.routableWithLimitation', 'ROUTABLE WITH FINANCIAL DATA LIMITATION')
                            )}
                          </span>
                        )}

                        {/* Financial Evidence Status Indicator */}
                        {p.financial_intelligence?.NNPA_PERCENT?.value != null ? (
                          <span className="inline-flex items-center gap-1 text-[10px] font-extrabold text-emerald-800 bg-emerald-50 border border-emerald-300 px-2.5 py-0.5 rounded-full">
                            <ShieldCheck className="w-3 h-3 text-emerald-600 shrink-0" />
                            INSTITUTION-LEVEL EVIDENCE VERIFIED
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-900 bg-amber-50 border border-amber-300 px-2 py-0.5 rounded-full">
                            <AlertCircle className="w-3 h-3 text-amber-600 shrink-0" />
                            FINANCIAL DATA LIMITATION (MINISTRY MIS)
                          </span>
                        )}
                      </div>

                      {/* Quick Financial Summary Strip */}
                      <div className="mt-2 text-[10px] bg-slate-50 border border-slate-200 rounded-xl p-2.5 space-y-0.5">
                        {p.financial_intelligence?.NNPA_PERCENT?.value != null ? (
                          <div className="flex flex-wrap items-center justify-between gap-1">
                            <div>
                              <span className="font-bold text-slate-700">{t('partnerLocator.verifiedNetNpa', 'Verified Net NPA:')} </span>
                              <span className="font-extrabold text-slate-900 text-[11px]">
                                {p.financial_intelligence.NNPA_PERCENT.value.toFixed(2)}%
                              </span>
                              {p.financial_intelligence.NNPA_PERCENT.source && (
                                <span className="text-slate-500 ml-1">
                                  ({p.financial_intelligence.NNPA_PERCENT.source})
                                </span>
                              )}
                            </div>
                            <div className="text-slate-500 text-[9px]">
                              {p.financial_intelligence.NNPA_PERCENT.reporting_period ? (
                                <span>{t('partnerLocator.period', 'Period')}: {p.financial_intelligence.NNPA_PERCENT.reporting_period}</span>
                              ) : (
                                <span>{t('partnerLocator.period', 'Period')}: Published</span>
                              )}
                              <span className="mx-1">•</span>
                              <span className="font-semibold text-slate-700">{p.financial_scope || t('partnerLocator.institutionLevel', 'Institution-level')}</span>
                            </div>
                          </div>
                        ) : (
                          <div className="text-amber-950 space-y-0.5">
                            <div className="font-bold text-[10px]">
                              {t('partnerLocator.disclaimerNotVerified')}
                            </div>
                            <div className="text-[9px] text-slate-600">
                              {t('partnerLocator.disclaimerRouting')}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* "Why this partner?" Smart Routing Rationale */}
                      {((p.routing_reasons && p.routing_reasons.length > 0) || p.suitability_reason) && (
                        <div className="mt-2 bg-indigo-50/70 border border-indigo-100 rounded-xl p-2.5 space-y-1 text-xs shadow-2xs">
                          <div className="flex items-center gap-1 font-bold text-indigo-950 text-[11px]">
                            <Compass className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                            <span>{t('partnerLocator.whyThisPartner', 'Why this partner?')}</span>
                          </div>
                          {p.suitability_reason && (
                            <p className="text-[10px] text-slate-700 font-medium leading-relaxed">
                              {localizeRoutingReason(p.suitability_reason, t, i18n.language)}
                            </p>
                          )}
                          {p.routing_reasons && p.routing_reasons.length > 0 && (
                            <div className="flex flex-wrap gap-1 pt-0.5">
                              {p.routing_reasons.map((reason, rIdx) => (
                                <span
                                  key={rIdx}
                                  className="inline-flex items-center gap-1 text-[9px] font-semibold text-indigo-900 bg-white border border-indigo-200 px-2 py-0.5 rounded-md shadow-2xs"
                                >
                                  <CheckCircle className="w-3 h-3 text-emerald-600 shrink-0" />
                                  {localizeRoutingReason(reason, t, i18n.language)}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Expandable Financial & Regulatory Evidence (Categories A, B, C, D) */}
                      <div className="mt-2.5">
                        <button
                          type="button"
                          onClick={(e) => toggleEvidence(partner.partner_id, e)}
                          className="w-full flex items-center justify-between px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-[11px] font-bold transition border border-slate-200 shadow-2xs"
                        >
                          <span className="flex items-center gap-1.5">
                            <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
                            <span>
                              {expandedEvidence[partner.partner_id]
                                ? t('partnerLocator.hideFinancialEvidence', 'Hide Financial & Regulatory Evidence')
                                : t('partnerLocator.viewFinancialEvidence', 'View Financial & Regulatory Evidence')}
                            </span>
                            {p.prudential_status === 'ELIGIBLE' && (
                              <span className="text-[9px] bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded font-extrabold ml-1">
                                PRUDENTIAL CLEARANCE MET
                              </span>
                            )}
                          </span>
                          {expandedEvidence[partner.partner_id] ? (
                            <ChevronUp className="w-3.5 h-3.5 text-slate-500" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                          )}
                        </button>

                        {expandedEvidence[partner.partner_id] && (
                          <div className="mt-2">
                            <FinancialIntelligencePanel partnerResult={p} compact />
                          </div>
                        )}
                      </div>
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
