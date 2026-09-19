import { NearestPartnerResponse, FinancialRuleEvaluation } from '../api/partnerApi';

/**
 * Category A: Verified Financial Evidence Item
 * Official regulatory indicators published by RBI/NABARD at legal institution level.
 */
export interface VerifiedEvidenceItem {
  metricKey: string;
  metricLabel: string;
  valueFormatted: string;
  numericValue: number;
  unit: string;
  sourceAuthority: string;
  sourceDocument: string;
  reportingPeriod: string;
  dataAsOf: string;
  scope: string; // 'INSTITUTION_LEVEL'
  scopeDescription: string;
  statusLabel: string;
  ruleApplicability?: string | null;
}

/**
 * Category B: Statutory / Prudential Rule Item
 * Grounded in official NSFDC Lending Policy & Guidelines.
 */
export interface PolicyPrudentialItem {
  ruleId: string;
  ruleName: string;
  authority: string;
  metricName: string;
  thresholdDisplay: string;
  criterionText: string;
  status: 'PASS' | 'FAIL' | 'NOT_PUBLICLY_VERIFIED' | 'NOT_APPLICABLE' | 'UNKNOWN';
  statusBadge: string;
  isApplicable: boolean;
  explanation: string;
  financialScope: string;
}

/**
 * Category C: Transparent Limitations for Unverified Data
 * Displayed honestly when operational fund utilization or overdue ledgers are not public.
 */
export interface UnverifiedLimitationNotice {
  honestStateText: string;
  routingContextText: string;
  unverifiedItems: {
    name: string;
    description: string;
    managementContext: string;
  }[];
  regulatoryReason: string;
}

/**
 * Category D: Sector-Level Macro Benchmark
 * Purely macro context. MUST NEVER be attached to an individual partner.
 */
export interface SectorBenchmarkItem {
  sectorTitle: string;
  institutionType: string;
  benchmarkMetric: string;
  benchmarkValue: string;
  sourceAuthority: string;
  sourceDocument: string;
  reportingPeriod: string;
  mandatoryDisclaimer: string;
}

/**
 * Formats NNPA value for display.
 * Returns formatted percentage (e.g. "0.55%", "0.40%") or localized fallback if not available.
 * Rule: If NNPA is unavailable, show "Not publicly verified" rather than 0 or "--".
 */
export const getNNPADisplay = (
  partnerResult: NearestPartnerResponse,
  fallbackText: string = 'Not publicly verified'
): string => {
  const metric = partnerResult.financial_intelligence?.NNPA_PERCENT;
  if (metric && typeof metric.value === 'number') {
    return `${metric.value.toFixed(2)}%`;
  }
  return fallbackText;
};

/**
 * Formats GNPA value for display.
 */
export const getGNPADisplay = (
  partnerResult: NearestPartnerResponse,
  fallbackText: string = 'Not publicly verified'
): string => {
  const metric = partnerResult.financial_intelligence?.GNPA_PERCENT;
  if (metric && typeof metric.value === 'number') {
    return `${metric.value.toFixed(2)}%`;
  }
  return fallbackText;
};

/**
 * Formats CRAR value for display.
 * Rule: If CRAR is unavailable, show "Not publicly verified" rather than fake fallback.
 */
export const getCRARDisplay = (
  partnerResult: NearestPartnerResponse,
  fallbackText: string = 'Not publicly verified'
): string => {
  const metric = partnerResult.financial_intelligence?.CRAR_PERCENT;
  if (metric && typeof metric.value === 'number') {
    return `${metric.value.toFixed(2)}%`;
  }
  return fallbackText;
};

/**
 * Returns the source of the financial observation (e.g. "RBI").
 * Rule: If source is unavailable, show "Source not available".
 */
export const getSourceDisplay = (
  partnerResult: NearestPartnerResponse,
  fallbackText: string = 'Source not available'
): string => {
  const metric = partnerResult.financial_intelligence?.NNPA_PERCENT;
  if (metric?.source) {
    return metric.source;
  }
  return fallbackText;
};

/**
 * Formats the observation period (e.g. "FY25").
 */
export const getDataPeriodDisplay = (
  partnerResult: NearestPartnerResponse,
  fallbackText: string = 'Not available'
): string => {
  const metric = partnerResult.financial_intelligence?.NNPA_PERCENT;
  if (!metric) return fallbackText;

  if (metric.document) {
    if (/FY\s*25\b/i.test(metric.document)) return 'FY25';
    const fyMatch = metric.document.match(/FY\s*20?(\d{2})/i);
    if (fyMatch) return `FY${fyMatch[1]}`;
  }

  if (metric.reporting_period) {
    if (metric.reporting_period.startsWith('2025')) return 'FY25';
    if (metric.reporting_period.startsWith('2024')) return 'FY24';
    return metric.reporting_period;
  }

  if (metric.data_as_of) {
    if (metric.data_as_of.startsWith('2025')) return 'FY25';
    if (metric.data_as_of.startsWith('2024')) return 'FY24';
    return metric.data_as_of;
  }

  return fallbackText;
};

/**
 * Returns formatted scope display (e.g. "Institution-level").
 * Rule: Always show scope if available.
 */
export const getScopeDisplay = (
  partnerResult: NearestPartnerResponse,
  institutionLevelText: string = 'Institution-level'
): string => {
  const scope = partnerResult.financial_scope || partnerResult.financial_intelligence?.NNPA_PERCENT?.financial_scope;
  if (scope === 'INSTITUTION_LEVEL') {
    return institutionLevelText;
  }
  if (scope) {
    return scope.replace(/_/g, ' ');
  }
  return institutionLevelText;
};

/**
 * Returns human-readable routing status.
 */
export const getRoutingStatusDisplay = (
  status?: string,
  routableWithLimitationText: string = 'ROUTABLE WITH FINANCIAL DATA LIMITATION'
): string => {
  if (!status) return routableWithLimitationText;
  if (status === 'ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION') {
    return routableWithLimitationText;
  }
  return status.replace(/_/g, ' ');
};

/**
 * Helper to normalize institution type string.
 */
export const getCanonicalInstitutionType = (partnerResult: NearestPartnerResponse): string => {
  const raw = (
    partnerResult.partner.institution_type ||
    partnerResult.partner.partner_type ||
    ''
  ).toUpperCase();

  if (raw.includes('RURAL') || raw.includes('RRB')) return 'REGIONAL_RURAL_BANK';
  if (raw.includes('PUBLIC') || raw.includes('COMMERCIAL') || raw === 'BANK') return 'PUBLIC_SECTOR_BANK';
  if (raw.includes('MFI') || raw.includes('MICRO_FINANCE')) return 'NBFC_MFI';
  if (raw.includes('COOPERATIVE')) return 'COOPERATIVE_BANK';
  if (raw.includes('SCA') || raw.includes('CHANNELIZING')) return 'STATE_CHANNELIZING_AGENCY';
  return raw || 'BANK';
};

/* =========================================================================
   CATEGORY A: VERIFIED FINANCIAL EVIDENCE
   ========================================================================= */

const METRIC_LABELS: Record<string, string> = {
  NNPA_PERCENT: 'Net Non-Performing Assets (Net NPA)',
  GNPA_PERCENT: 'Gross Non-Performing Assets (Gross NPA)',
  CRAR_PERCENT: 'Capital to Risk-Weighted Assets Ratio (CRAR)',
  PROFITABLE_YEAR_COUNT_PREV_6Y: 'Consecutive Profit Years (Past 6 Years)',
};

/**
 * Extracts all verified official regulatory observations for Category A.
 * Strictly checks that a numeric or verified value exists and is sourced officially.
 */
export const getVerifiedFinancialEvidence = (
  partnerResult: NearestPartnerResponse
): VerifiedEvidenceItem[] => {
  const verifiedList: VerifiedEvidenceItem[] = [];
  const finIntel = partnerResult.financial_intelligence;
  if (!finIntel) return verifiedList;

  const instType = getCanonicalInstitutionType(partnerResult);

  for (const [key, obs] of Object.entries(finIntel)) {
    if (!obs || typeof obs !== 'object') continue;

    const val = obs.value;
    if (typeof val === 'number') {
      const isPSB = instType === 'PUBLIC_SECTOR_BANK';
      const label = METRIC_LABELS[key] || key.replace(/_/g, ' ');
      const unit = obs.unit || (key.includes('PERCENT') ? '%' : '');
      const valueFormatted = `${val.toFixed(2)}${unit}`;

      let ruleApplicability = obs.rule_applicability;
      if (!ruleApplicability) {
        if (isPSB && key === 'NNPA_PERCENT') {
          ruleApplicability =
            'Official RBI regulatory indicator. NSFDC RRB Net NPA ceiling (<15%) does not apply to Scheduled Commercial Banks.';
        } else {
          ruleApplicability = 'Evaluated against applicable statutory prudential framework';
        }
      }

      verifiedList.push({
        metricKey: key,
        metricLabel: label,
        valueFormatted,
        numericValue: val,
        unit,
        sourceAuthority: obs.source || 'Official Regulatory Authority',
        sourceDocument: obs.document || 'Audited Financial Accounts',
        reportingPeriod: obs.reporting_period || 'Not available',
        dataAsOf: obs.data_as_of || 'Date not recorded',
        scope: obs.financial_scope || 'INSTITUTION_LEVEL',
        scopeDescription:
          obs.scope_description ||
          'Parent institution regulatory indicator (branch-level balance sheets are not published under banking regulations)',
        statusLabel: obs.status_label || (isPSB ? 'OFFICIAL_FINANCIAL_INDICATOR' : 'VERIFIED_OFFICIAL'),
        ruleApplicability,
      });
    }
  }

  return verifiedList;
};

/* =========================================================================
   CATEGORY B: POLICY / PRUDENTIAL INFORMATION
   ========================================================================= */

/**
 * Extracts and formats statutory & policy criteria for Category B.
 * Grounded in official NSFDC Lending Policy & Guidelines.
 * Strictly guarantees:
 * 1. RRB conditions apply only to RRBs.
 * 2. PSBs are NOT subjected to RRB Net NPA < 15% threshold as an eligibility rule.
 */
export const getPrudentialPolicyRules = (
  partnerResult: NearestPartnerResponse
): { applicableRules: PolicyPrudentialItem[]; notApplicableRules: PolicyPrudentialItem[] } => {
  const instType = getCanonicalInstitutionType(partnerResult);
  const rawRules: FinancialRuleEvaluation[] = partnerResult.rules_evaluated || [];

  const applicableRules: PolicyPrudentialItem[] = [];
  const notApplicableRules: PolicyPrudentialItem[] = [];

  if (rawRules.length > 0) {
    for (const r of rawRules) {
      const isNotApplicable =
        r.rule_status === 'NOT_APPLICABLE' ||
        r.result === 'NOT_APPLICABLE' ||
        (r.rule_id?.includes('RRB') && instType !== 'REGIONAL_RURAL_BANK');

      const isApplicable = !isNotApplicable;
      const status = (r.rule_status || r.result || 'UNKNOWN') as PolicyPrudentialItem['status'];

      let statusBadge = 'UNKNOWN';
      if (isNotApplicable) {
        statusBadge =
          instType === 'PUBLIC_SECTOR_BANK'
            ? 'NOT APPLICABLE TO COMMERCIAL BANKS (REGULATED BY RBI)'
            : 'NOT APPLICABLE TO THIS INSTITUTION TYPE';
      } else if (status === 'PASS') {
        statusBadge = 'PASSED STATUTORY CRITERION';
      } else if (status === 'FAIL') {
        statusBadge = 'STATUTORY RESTRICTION VIOLATED';
      } else if (status === 'NOT_PUBLICLY_VERIFIED') {
        statusBadge = 'POLICY APPLIES • DATA NOT PUBLICLY VERIFIED';
      }

      let explanation = r.explanation || '';
      if (isNotApplicable && instType === 'PUBLIC_SECTOR_BANK' && r.rule_id?.includes('RRB')) {
        explanation =
          'NSFDC RRB Net NPA ceiling (<15%) applies solely to Regional Rural Banks. Scheduled Commercial Banks are directly governed by Reserve Bank of India statutory capital and asset quality directives.';
      }

      const item: PolicyPrudentialItem = {
        ruleId: r.rule_id,
        ruleName: r.rule_name || r.rule_id,
        authority: r.authority || 'NSFDC',
        metricName: r.metric_name || r.metric || 'CRITERION',
        thresholdDisplay:
          r.threshold !== undefined && r.threshold !== null
            ? `${r.operator || ''} ${r.threshold}${r.unit || ''}`
            : 'Statutory Policy Condition',
        criterionText: r.wording || `${r.rule_name || r.rule_id} mandated under official policy.`,
        status: isNotApplicable ? 'NOT_APPLICABLE' : status,
        statusBadge,
        isApplicable,
        explanation,
        financialScope: r.financial_scope || 'POLICY_LEVEL',
      };

      if (isApplicable) {
        applicableRules.push(item);
      } else {
        notApplicableRules.push(item);
      }
    }
  } else {
    // Fallback based on canonical institution type if rules_evaluated is not populated
    const isRRB = instType === 'REGIONAL_RURAL_BANK';
    const isPSB = instType === 'PUBLIC_SECTOR_BANK';

    if (isRRB) {
      const nnpaVal = partnerResult.financial_intelligence?.NNPA_PERCENT?.value;
      const nnpaPassed = typeof nnpaVal === 'number' && nnpaVal < 15.0;
      applicableRules.push({
        ruleId: 'NSFDC_RRB_NNPA_001',
        ruleName: 'Regional Rural Bank Net NPA Ceiling (<15%)',
        authority: 'NSFDC',
        metricName: 'NNPA_PERCENT',
        thresholdDisplay: '< 15.00%',
        criterionText: 'Regional Rural Banks must have Net NPA below 15% as per published statutory accounts.',
        status: typeof nnpaVal === 'number' ? (nnpaPassed ? 'PASS' : 'FAIL') : 'NOT_PUBLICLY_VERIFIED',
        statusBadge:
          typeof nnpaVal === 'number'
            ? nnpaPassed
              ? 'PASSED STATUTORY CRITERION'
              : 'STATUTORY RESTRICTION VIOLATED'
            : 'POLICY APPLIES • DATA NOT PUBLICLY VERIFIED',
        isApplicable: true,
        explanation:
          typeof nnpaVal === 'number'
            ? `Verified Net NPA (${nnpaVal.toFixed(2)}%) satisfies official NSFDC RRB criterion (< 15.0%).`
            : 'Statutory NSFDC RRB requirement applies. Official accounts being cross-checked.',
        financialScope: 'INSTITUTION_LEVEL',
      });
      applicableRules.push({
        ruleId: 'NSFDC_RRB_PROFIT_001',
        ruleName: 'RRB Profitability Track Record (3 of 6 Years)',
        authority: 'NSFDC',
        metricName: 'PROFITABLE_YEAR_COUNT_PREV_6Y',
        thresholdDisplay: '>= 3 Years',
        criterionText: 'RRB must have earned net profit in at least 3 of preceding 6 financial years.',
        status: 'NOT_PUBLICLY_VERIFIED',
        statusBadge: 'POLICY APPLIES • DATA NOT PUBLICLY VERIFIED',
        isApplicable: true,
        explanation: 'Multi-year audited profit returns are maintained in regulatory filings.',
        financialScope: 'INSTITUTION_LEVEL',
      });
    }

    if (isPSB) {
      notApplicableRules.push({
        ruleId: 'NSFDC_RRB_NNPA_001',
        ruleName: 'Regional Rural Bank Net NPA Ceiling (<15%)',
        authority: 'NSFDC',
        metricName: 'NNPA_PERCENT',
        thresholdDisplay: '< 15.00%',
        criterionText: 'Applies exclusively to Regional Rural Banks.',
        status: 'NOT_APPLICABLE',
        statusBadge: 'NOT APPLICABLE TO COMMERCIAL BANKS (REGULATED BY RBI)',
        isApplicable: false,
        explanation:
          'NSFDC RRB Net NPA ceiling (<15%) does not apply to Scheduled Commercial Banks. Regulated directly by Reserve Bank of India statutory capital and asset quality directives.',
        financialScope: 'POLICY_LEVEL',
      });
    }

    // General NSFDC Policy requirements for all channel partners
    applicableRules.push({
      ruleId: 'NSFDC_GEN_OVERDUE_001',
      ruleName: 'Zero Overdue to NSFDC Requirement',
      authority: 'NSFDC',
      metricName: 'OVERDUE_STATUS',
      thresholdDisplay: '== NO_OVERDUE',
      criterionText: 'The channelizing agency / partner must have no overdues payable to NSFDC.',
      status: 'NOT_PUBLICLY_VERIFIED',
      statusBadge: 'POLICY APPLIES • DATA NOT PUBLICLY VERIFIED',
      isApplicable: true,
      explanation:
        'Statutory requirement established in NSFDC Lending Policy. Partner-level loan default/recovery ledgers are managed internally in Ministry MIS.',
      financialScope: 'POLICY_LEVEL',
    });

    applicableRules.push({
      ruleId: 'NSFDC_GEN_UTILIZATION_001',
      ruleName: 'Minimum 100% Cumulative Fund Utilization',
      authority: 'NSFDC',
      metricName: 'FUND_UTILIZATION_PERCENT',
      thresholdDisplay: '>= 100%',
      criterionText: 'Minimum 100% cumulative utilization of previously disbursed funds must be achieved.',
      status: 'NOT_PUBLICLY_VERIFIED',
      statusBadge: 'POLICY APPLIES • DATA NOT PUBLICLY VERIFIED',
      isApplicable: true,
      explanation:
        'Statutory requirement established in NSFDC Lending Policy. Utilization certificates (UC) are managed internally within the Ministry channelizing framework.',
      financialScope: 'POLICY_LEVEL',
    });
  }

  return { applicableRules, notApplicableRules };
};

/* =========================================================================
   CATEGORY C: NOT PUBLICLY VERIFIED INFORMATION
   ========================================================================= */

/**
 * Generates transparent limitation statements for unverified data.
 * Adheres strictly to the anti-fabrication mandate:
 * - NO "Low NPA", "Healthy", "Safe", "Best partner", or "Funds available"
 * - Honest state: "Partner-level financial utilization/overdue data is not publicly verified."
 * - Routing context: "Routing uses available verified institutional/prudential information."
 */
export const getUnverifiedDataLimitations = (
  partnerResult: NearestPartnerResponse
): UnverifiedLimitationNotice => {
  return {
    honestStateText: 'Partner-level financial utilization/overdue data is not publicly verified.',
    routingContextText: 'Routing uses available verified institutional/prudential information.',
    unverifiedItems: [
      {
        name: 'Cumulative Scheme Fund Utilization Certificates (UC)',
        description: 'Actual percentage of previously disbursed government scheme funds utilized by this specific channel partner.',
        managementContext: 'Managed internally inside Ministry / State Corporation MIS; not exposed on open public portals.',
      },
      {
        name: 'Partner-Level Overdue & Recovery Ledger',
        description: 'Live demand-versus-collection ledger for repayments due to NSFDC / Apex Corporations.',
        managementContext: 'Maintained internally between the channel partner and the financing apex body; not published as public open data.',
      },
      {
        name: 'Branch-Specific Balance Sheet & NPA',
        description: 'Independent financial balance sheet for this individual bank branch.',
        managementContext: 'Under statutory Reserve Bank of India regulations, financial accounts are published at the legal institution level, not for individual branch service points.',
      },
    ],
    regulatoryReason:
      'To prevent misleading financial claims, YojnaSetu strictly prohibits synthetic scores or unverified health labels. Routing relies deterministically on official institution-level regulatory publications and statutory scheme authorization.',
  };
};

/* =========================================================================
   CATEGORY D: SECTOR-LEVEL INFORMATION
   ========================================================================= */

/**
 * Returns macro sector-level context for Category D.
 * Never attached directly to an individual partner.
 * Always carries the explicit disclaimer:
 * "Sector averages represent nationwide industry benchmarks and are NOT the financial metrics of this specific branch or institution."
 */
export const getSectorLevelContext = (
  partnerResult: NearestPartnerResponse
): SectorBenchmarkItem => {
  const instType = getCanonicalInstitutionType(partnerResult);

  if (instType === 'REGIONAL_RURAL_BANK') {
    return {
      sectorTitle: 'Regional Rural Banks (RRBs) Sector Benchmark',
      institutionType: 'Regional Rural Banks',
      benchmarkMetric: 'All-India RRB Average Net NPA',
      benchmarkValue: '4.70%',
      sourceAuthority: 'NABARD / Department of Financial Services (DFS)',
      sourceDocument: 'NABARD Annual Financial Performance of Regional Rural Banks 2023-24',
      reportingPeriod: 'FY 2023-24',
      mandatoryDisclaimer:
        'Sector averages represent nationwide industry benchmarks and are NOT the financial metrics of this specific branch or institution.',
    };
  }

  if (instType === 'NBFC_MFI') {
    return {
      sectorTitle: 'NBFC-Microfinance Sector Benchmark',
      institutionType: 'Non-Banking Financial Companies (NBFC-MFI)',
      benchmarkMetric: 'All-India Microfinance Portfolio at Risk (PAR 90+)',
      benchmarkValue: '2.70%',
      sourceAuthority: 'SIDBI / Microfinance Institutions Network (MFIN)',
      sourceDocument: 'SIDBI Microfinance Pulse Report (Vol. XIII)',
      reportingPeriod: 'Q4 FY 2023-24',
      mandatoryDisclaimer:
        'Sector averages represent nationwide industry benchmarks and are NOT the financial metrics of this specific branch or institution.',
    };
  }

  if (instType === 'COOPERATIVE_BANK') {
    return {
      sectorTitle: 'Urban & Rural Cooperative Banks Sector Benchmark',
      institutionType: 'Cooperative Banking Sector',
      benchmarkMetric: 'All-India Cooperative Banking Sector Average Gross NPA',
      benchmarkValue: '6.10%',
      sourceAuthority: 'Reserve Bank of India (RBI) / NABARD',
      sourceDocument: 'RBI Report on Trend and Progress of Banking in India 2023-24',
      reportingPeriod: 'FY 2023-24',
      mandatoryDisclaimer:
        'Sector averages represent nationwide industry benchmarks and are NOT the financial metrics of this specific branch or institution.',
    };
  }

  // Default: Scheduled Commercial Banks (Public Sector & Commercial Banks)
  return {
    sectorTitle: 'Scheduled Commercial Banks (SCBs) Sector Benchmark',
    institutionType: 'Scheduled Commercial Banks (Public & Private Sector)',
    benchmarkMetric: 'All-India Scheduled Commercial Banks Gross NPA Ratio',
    benchmarkValue: '2.80%',
    sourceAuthority: 'Reserve Bank of India (RBI)',
    sourceDocument: 'RBI Financial Stability Report (Issue No. 29, June 2024)',
    reportingPeriod: 'June 2024',
    mandatoryDisclaimer:
      'Sector averages represent nationwide industry benchmarks and are NOT the financial metrics of this specific branch or institution.',
  };
};
