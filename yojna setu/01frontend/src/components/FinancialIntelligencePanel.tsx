import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ShieldCheck,
  ShieldAlert,
  AlertCircle,
  Info,
  Building,
  Scale,
  TrendingUp,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  Database,
  Layers,
  HelpCircle,
} from 'lucide-react';
import { NearestPartnerResponse } from '../api/partnerApi';
import {
  getVerifiedFinancialEvidence,
  getPrudentialPolicyRules,
  getUnverifiedDataLimitations,
  getSectorLevelContext,
  getScopeDisplay,
  getSourceDisplay,
  getDataPeriodDisplay,
  getNNPADisplay,
} from '../utils/financialEvidence';

interface FinancialIntelligencePanelProps {
  partnerResult: NearestPartnerResponse;
  compact?: boolean;
}

export const FinancialIntelligencePanel: React.FC<FinancialIntelligencePanelProps> = ({
  partnerResult,
  compact = false,
}) => {
  const { t } = useTranslation();
  const [activeCategory, setActiveCategory] = useState<'A' | 'B' | 'C' | 'D'>('A');

  const verifiedEvidence = getVerifiedFinancialEvidence(partnerResult);
  const { applicableRules, notApplicableRules } = getPrudentialPolicyRules(partnerResult);
  const limitations = getUnverifiedDataLimitations(partnerResult);
  const sectorContext = getSectorLevelContext(partnerResult);

  const instName =
    partnerResult.institution_name ||
    partnerResult.partner.name ||
    t('partnerLocator.institutionLevel', 'Institution-level');

  const hasVerifiedData = verifiedEvidence.length > 0;

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs text-left">
      {/* Category Tabs Header */}
      <div className="bg-slate-50 border-b border-slate-200 p-2">
        <div className="flex items-center justify-between gap-1 overflow-x-auto scrollbar-none text-[11px]">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setActiveCategory('A');
            }}
            className={`px-2.5 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 shrink-0 ${
              activeCategory === 'A'
                ? 'bg-emerald-700 text-white shadow-xs'
                : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>{t('partnerLocator.catA', 'A. Verified Evidence')}</span>
            <span
              className={`text-[9px] px-1.5 py-0.2 rounded-full font-extrabold ${
                activeCategory === 'A' ? 'bg-emerald-800 text-white' : 'bg-slate-100 text-slate-600'
              }`}
            >
              {verifiedEvidence.length}
            </span>
          </button>

          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setActiveCategory('B');
            }}
            className={`px-2.5 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 shrink-0 ${
              activeCategory === 'B'
                ? 'bg-indigo-700 text-white shadow-xs'
                : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            <Scale className="w-3.5 h-3.5" />
            <span>{t('partnerLocator.catB', 'B. Policy & Rules')}</span>
            <span
              className={`text-[9px] px-1.5 py-0.2 rounded-full font-extrabold ${
                activeCategory === 'B' ? 'bg-indigo-800 text-white' : 'bg-slate-100 text-slate-600'
              }`}
            >
              {applicableRules.length}
            </span>
          </button>

          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setActiveCategory('C');
            }}
            className={`px-2.5 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 shrink-0 ${
              activeCategory === 'C'
                ? 'bg-amber-700 text-white shadow-xs'
                : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            <AlertCircle className="w-3.5 h-3.5" />
            <span>{t('partnerLocator.catC', 'C. Unverified Limits')}</span>
          </button>

          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setActiveCategory('D');
            }}
            className={`px-2.5 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 shrink-0 ${
              activeCategory === 'D'
                ? 'bg-sky-800 text-white shadow-xs'
                : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            <span>{t('partnerLocator.catD', 'D. Sector Benchmark')}</span>
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="p-3 text-xs space-y-2.5">
        {/* =========================================================================
            CATEGORY A: VERIFIED FINANCIAL EVIDENCE
           ========================================================================= */}
        {activeCategory === 'A' && (
          <div className="space-y-2.5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
              <div className="flex items-center gap-1.5 font-bold text-slate-900 text-xs">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{t('partnerLocator.catATitle', 'Category A: Verified Financial Evidence')}</span>
              </div>
              <span className="text-[10px] font-extrabold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                INSTITUTION-LEVEL METRICS
              </span>
            </div>

            {/* Institution Scope Banner */}
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-2 text-[11px] space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-700">{t('partnerLocator.institutionName', 'Legal Institution')}:</span>
                <span className="font-extrabold text-slate-900">{instName}</span>
              </div>
              <p className="text-[10px] text-slate-500 italic">
                {t(
                  'partnerLocator.scopeNotice',
                  'Branch-level balance sheets are not published under Indian banking regulations. Metrics reflect audited parent institution performance.'
                )}
              </p>
            </div>

            {/* Verified Metrics Cards */}
            {hasVerifiedData ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {verifiedEvidence.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-emerald-50/50 border border-emerald-200 rounded-xl space-y-1.5 shadow-2xs"
                  >
                    <div className="flex justify-between items-start">
                      <div className="font-bold text-slate-800 text-[11px] leading-tight">
                        {item.metricLabel}
                      </div>
                      <span className="text-[9px] font-extrabold text-emerald-800 bg-emerald-100 px-1.5 py-0.5 rounded">
                        {item.statusLabel}
                      </span>
                    </div>

                    <div className="text-xl font-extrabold text-slate-900 tracking-tight">
                      {item.valueFormatted}
                    </div>

                    {/* Full Regulatory Provenance */}
                    <div className="pt-1 border-t border-emerald-100 text-[10px] space-y-0.5 text-slate-600">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500 font-semibold">{t('partnerLocator.source', 'Source')}:</span>
                        <span className="font-bold text-slate-800 truncate max-w-[170px]" title={item.sourceAuthority}>
                          {item.sourceAuthority}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500 font-semibold">{t('partnerLocator.dataPeriod', 'Data Period')}:</span>
                        <span className="font-bold text-slate-800">{item.reportingPeriod}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500 font-semibold">{t('partnerLocator.dataAsOf', 'Data as of')}:</span>
                        <span className="font-bold text-slate-800">{item.dataAsOf}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500 font-semibold">{t('partnerLocator.scope', 'Scope')}:</span>
                        <span className="font-bold text-slate-800">{item.scope.replace(/_/g, ' ')}</span>
                      </div>
                    </div>

                    {item.ruleApplicability && (
                      <div className="text-[9px] text-emerald-900 bg-emerald-100/70 p-1.5 rounded font-medium mt-1">
                        {item.ruleApplicability}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-center space-y-1">
                <div className="text-[11px] font-bold text-slate-700">
                  {t('partnerLocator.noVerifiedMetrics', 'No institution-level financial indicators published for this partner.')}
                </div>
                <p className="text-[10px] text-slate-500">
                  {t(
                    'partnerLocator.noVerifiedMetricsDesc',
                    'Channel partner routing for this entity relies on verified government scheme authorization and statutory location coordinates.'
                  )}
                </p>
              </div>
            )}
          </div>
        )}

        {/* =========================================================================
            CATEGORY B: POLICY / PRUDENTIAL INFORMATION
           ========================================================================= */}
        {activeCategory === 'B' && (
          <div className="space-y-2.5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
              <div className="flex items-center gap-1.5 font-bold text-slate-900 text-xs">
                <Scale className="w-4 h-4 text-indigo-600 shrink-0" />
                <span>{t('partnerLocator.catBTitle', 'Category B: Statutory Policy & Prudential Rules')}</span>
              </div>
              <span className="text-[10px] font-extrabold text-indigo-800 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-full">
                NSFDC LENDING POLICY
              </span>
            </div>

            <p className="text-[10px] text-slate-600 font-medium">
              {t(
                'partnerLocator.catBDesc',
                'Statutory criteria evaluated under official NSFDC Lending Policy & Guidelines. Rules are strictly applied according to institutional charter.'
              )}
            </p>

            {/* Applicable Rules */}
            <div className="space-y-2">
              <h5 className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider">
                {t('partnerLocator.applicableRules', 'Applicable Statutory Criteria')}
              </h5>

              {applicableRules.map((rule, idx) => (
                <div
                  key={idx}
                  className={`p-2.5 rounded-xl border text-[11px] space-y-1 ${
                    rule.status === 'PASS'
                      ? 'bg-emerald-50/70 border-emerald-200'
                      : rule.status === 'FAIL'
                      ? 'bg-red-50/70 border-red-200'
                      : 'bg-slate-50 border-slate-200'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="font-bold text-slate-900 flex items-center gap-1.5">
                      {rule.status === 'PASS' ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      ) : rule.status === 'FAIL' ? (
                        <XCircle className="w-3.5 h-3.5 text-red-600 shrink-0" />
                      ) : (
                        <Clock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      )}
                      <span>{rule.ruleName}</span>
                    </div>
                    <span
                      className={`text-[9px] font-extrabold px-2 py-0.5 rounded-full ${
                        rule.status === 'PASS'
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                          : rule.status === 'FAIL'
                          ? 'bg-red-100 text-red-800 border border-red-300'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {rule.statusBadge}
                    </span>
                  </div>

                  <p className="text-[10px] text-slate-600 italic pl-5">
                    {rule.criterionText}
                  </p>

                  <div className="pl-5 text-[10px] font-medium text-slate-700 pt-0.5">
                    <span className="font-bold">{t('partnerLocator.finding', 'Finding')}: </span>
                    <span>{rule.explanation}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Explicitly Not Applicable Rules (e.g. PSB evaluated vs RRB rule) */}
            {notApplicableRules.length > 0 && (
              <div className="pt-2 space-y-1.5 border-t border-slate-200">
                <h5 className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                  <Info className="w-3 h-3 text-slate-400" />
                  <span>{t('partnerLocator.notApplicableTitle', 'Statutory Rules Not Applicable to this Institution')}</span>
                </h5>

                {notApplicableRules.map((rule, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-slate-100/80 border border-slate-200 rounded-xl text-[10px] space-y-1"
                  >
                    <div className="flex justify-between items-start">
                      <span className="font-bold text-slate-800 line-through decoration-slate-400">
                        {rule.ruleName} ({rule.thresholdDisplay})
                      </span>
                      <span className="text-[9px] font-bold text-slate-600 bg-white border border-slate-300 px-2 py-0.5 rounded-full">
                        {rule.statusBadge}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-600 leading-relaxed">
                      {rule.explanation}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* =========================================================================
            CATEGORY C: NOT PUBLICLY VERIFIED INFORMATION
           ========================================================================= */}
        {activeCategory === 'C' && (
          <div className="space-y-2.5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
              <div className="flex items-center gap-1.5 font-bold text-slate-900 text-xs">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>{t('partnerLocator.catCTitle', 'Category C: Transparent Data Limitations')}</span>
              </div>
              <span className="text-[10px] font-extrabold text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                ANTI-FABRICATION COMPLIANCE
              </span>
            </div>

            {/* Mandatory Honest State Banner */}
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl space-y-1.5 text-amber-950">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <div className="font-extrabold text-xs">
                    "{limitations.honestStateText}"
                  </div>
                  <div className="text-[11px] font-semibold text-amber-800 mt-0.5">
                    "{limitations.routingContextText}"
                  </div>
                </div>
              </div>
              <p className="text-[10px] text-amber-900 leading-relaxed pt-1">
                {t(
                  'partnerLocator.antiFabricationRule',
                  'In strict compliance with public financial disclosure standards, YojnaSetu does not display synthetic health labels (such as "Low NPA", "Healthy", "Safe", "Best partner", or "Funds available") when operational branch ledgers are not open public data.'
                )}
              </p>
            </div>

            {/* Specific Unverified Dimensions */}
            <div className="space-y-1.5">
              <h5 className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider">
                {t('partnerLocator.unverifiedDimensions', 'Operational Dimensions Managed Internally in Government MIS')}
              </h5>

              {limitations.unverifiedItems.map((item, idx) => (
                <div
                  key={idx}
                  className="p-2.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1 text-[11px]"
                >
                  <div className="font-bold text-slate-900 flex items-center gap-1.5">
                    <Database className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{item.name}</span>
                  </div>
                  <p className="text-[10px] text-slate-600 pl-5 leading-snug">
                    {item.description}
                  </p>
                  <div className="pl-5 text-[10px] text-slate-500 italic">
                    <span className="font-semibold text-slate-700">{t('partnerLocator.governance', 'Governance:')} </span>
                    {item.managementContext}
                  </div>
                </div>
              ))}
            </div>

            <div className="text-[10px] text-slate-500 bg-white border border-slate-200 p-2 rounded-lg">
              {limitations.regulatoryReason}
            </div>
          </div>
        )}

        {/* =========================================================================
            CATEGORY D: SECTOR-LEVEL INFORMATION
           ========================================================================= */}
        {activeCategory === 'D' && (
          <div className="space-y-2.5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
              <div className="flex items-center gap-1.5 font-bold text-slate-900 text-xs">
                <TrendingUp className="w-4 h-4 text-sky-700 shrink-0" />
                <span>{t('partnerLocator.catDTitle', 'Category D: Sector-Level Context')}</span>
              </div>
              <span className="text-[10px] font-extrabold text-sky-800 bg-sky-50 border border-sky-200 px-2 py-0.5 rounded-full">
                SECTOR-LEVEL CONTEXT ONLY
              </span>
            </div>

            {/* Mandatory Strict Disclaimer Banner */}
            <div className="p-3 bg-red-50/90 border-2 border-red-200 rounded-xl space-y-1 text-red-950">
              <div className="flex items-center gap-1.5 font-extrabold text-xs text-red-800">
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                <span>{t('partnerLocator.regulatoryNotice', 'IMPORTANT REGULATORY NOTICE:')}</span>
              </div>
              <p className="text-[11px] font-bold text-red-900 leading-snug">
                "{sectorContext.mandatoryDisclaimer}"
              </p>
            </div>

            {/* Sector Benchmark Card */}
            <div className="p-3 bg-sky-50/60 border border-sky-200 rounded-xl space-y-2">
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-extrabold text-slate-900 text-xs">
                    {sectorContext.sectorTitle}
                  </div>
                  <div className="text-[10px] text-slate-600 font-medium">
                    Sector Scope: {sectorContext.institutionType}
                  </div>
                </div>
                <span className="text-[9px] font-extrabold text-sky-800 bg-sky-100 px-2 py-0.5 rounded">
                  INDUSTRY BENCHMARK
                </span>
              </div>

              <div className="bg-white p-2.5 rounded-lg border border-sky-200 flex items-center justify-between">
                <div>
                  <div className="text-[10px] text-slate-500 font-bold uppercase">
                    {sectorContext.benchmarkMetric}
                  </div>
                  <div className="text-xl font-extrabold text-sky-900 mt-0.5">
                    {sectorContext.benchmarkValue}
                  </div>
                </div>
                <div className="text-right text-[10px] text-slate-600 space-y-0.5">
                  <div>
                    <span className="text-slate-500 font-semibold">{t('partnerLocator.authority', 'Authority:')} </span>
                    <span className="font-bold text-slate-800">{sectorContext.sourceAuthority}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 font-semibold">{t('partnerLocator.period', 'Period')}: </span>
                    <span className="font-bold text-slate-800">{sectorContext.reportingPeriod}</span>
                  </div>
                </div>
              </div>

              <div className="text-[10px] text-slate-600 space-y-1">
                <div>
                  <span className="font-bold text-slate-700">{t('partnerLocator.publicationRef', 'Publication Reference:')} </span>
                  <span>{sectorContext.sourceDocument}</span>
                </div>
                <p className="text-slate-500 italic">
                  This macro average provides national industry context for citizen awareness. It is strictly never attached to this partner or branch as an individual financial score.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
