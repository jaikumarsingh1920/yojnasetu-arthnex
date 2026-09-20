import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Scheme, SchemeRule } from '../types';
import {
  ShieldCheck,
  UserCheck,
  Wallet,
  Users,
  Briefcase,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Info,
  CheckCircle2,
  ExternalLink,
  Code2
} from 'lucide-react';

interface SchemeEligibilitySectionProps {
  scheme: Scheme;
}

type EligibilityCategory =
  | 'APPLICANT'
  | 'INCOME_FINANCIAL'
  | 'CATEGORY_COMMUNITY'
  | 'PROJECT_BUSINESS'
  | 'OTHER';

interface HumanizedRule {
  raw: SchemeRule;
  category: EligibilityCategory;
  humanTitle: string;
  humanValue: string;
  explanation?: string;
  isFinancialCondition: boolean;
  financialContextNote?: string;
}

export const SchemeEligibilitySection: React.FC<SchemeEligibilitySectionProps> = ({ scheme }) => {
  const { t } = useTranslation();
  const [activeCategory, setActiveCategory] = useState<EligibilityCategory | 'ALL'>('ALL');
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false);

  const rules: SchemeRule[] = (scheme.rules || []).filter((r) => r.field);

  const humanizeRule = (rule: SchemeRule): HumanizedRule => {
    const f = (rule.field || '').toLowerCase().trim();
    const val = String(rule.value || '').trim();
    const op = rule.operator || '=';
    const numVal = Number(val);
    const hasNum = !isNaN(numVal) && val !== '';

    // Check if error message had the legacy confusing message
    const isLegacyFinancialMsg =
      (rule.error_message && rule.error_message.includes('financial condition')) ||
      f.includes('project_cost') ||
      f.includes('loan_amount') ||
      f.includes('financing_percentage') ||
      f.includes('interest_rate') ||
      f.includes('repayment_period') ||
      f.includes('moratorium');

    // 1. CATEGORY: Category & Community
    if (
      f === 'sc_required' ||
      f === 'social_category' ||
      f === 'caste' ||
      f === 'marginalized_group' ||
      f === 'minority' ||
      f === 'disability' ||
      f === 'pwd' ||
      f === 'bpl'
    ) {
      if (f === 'sc_required') {
        return {
          raw: rule,
          category: 'CATEGORY_COMMUNITY',
          humanTitle: 'Scheduled Caste Applicant Requirement',
          humanValue:
            val.toUpperCase() === 'TRUE' || val === '1' || val === 'YES'
              ? 'Scheduled Caste requirement: Yes'
              : `Scheduled Caste requirement: ${val}`,
          explanation: 'Applicant must belong to the Scheduled Caste (SC) community as per official guidelines.',
          isFinancialCondition: false,
        };
      }
      return {
        raw: rule,
        category: 'CATEGORY_COMMUNITY',
        humanTitle: 'Community & Social Category Requirement',
        humanValue: `Target Category: ${val.replace(/_/g, ' ')}`,
        explanation: rule.error_message && !rule.error_message.includes('RULE-') ? rule.error_message : 'Beneficiary must satisfy the documented social category criteria.',
        isFinancialCondition: false,
      };
    }

    // 2. CATEGORY: Income & Financial Conditions
    if (
      f === 'income_limit' ||
      f === 'annual_income_max' ||
      f === 'family_income' ||
      f === 'max_loan_amount' ||
      f === 'financing_percentage' ||
      f === 'interest_rate_max' ||
      f === 'interest_rate' ||
      f === 'repayment_period_max_months' ||
      f === 'repayment_period_months' ||
      f === 'moratorium_min_months' ||
      f === 'moratorium_period_months' ||
      f === 'subsidy_percentage'
    ) {
      if (f === 'income_limit' || f === 'annual_income_max' || f === 'family_income') {
        const formattedAmt = hasNum ? `₹${numVal.toLocaleString('en-IN')}` : val;
        return {
          raw: rule,
          category: 'INCOME_FINANCIAL',
          humanTitle: 'Annual Family Income Limit',
          humanValue: `Annual family income limit: ${formattedAmt}`,
          explanation: `Total household income from all sources must not exceed ${formattedAmt} per annum.`,
          isFinancialCondition: false,
        };
      }

      if (f === 'max_loan_amount') {
        const formattedAmt = hasNum ? `₹${numVal.toLocaleString('en-IN')}` : val;
        return {
          raw: rule,
          category: 'INCOME_FINANCIAL',
          humanTitle: 'Program Financial Condition — Maximum Loan Quantum',
          humanValue: `Maximum Loan Amount: Up to ${formattedAmt}`,
          explanation: 'Maximum allowable loan assistance per beneficiary under this credit program.',
          isFinancialCondition: true,
          financialContextNote: 'YojnaSetu has compared this information with the documented programme condition.',
        };
      }

      if (f === 'financing_percentage') {
        return {
          raw: rule,
          category: 'INCOME_FINANCIAL',
          humanTitle: 'Program Financial Condition — Financing Ratio',
          humanValue: `Financing Ratio: Up to ${val}% of total project cost`,
          explanation: 'Proportion of total project expenditure funded under the government loan scheme.',
          isFinancialCondition: true,
          financialContextNote: 'YojnaSetu has compared this information with the documented programme condition.',
        };
      }

      if (f === 'interest_rate_max' || f === 'interest_rate') {
        return {
          raw: rule,
          category: 'INCOME_FINANCIAL',
          humanTitle: 'Program Financial Condition — Concessional Interest Rate',
          humanValue: `Concessional Interest Rate: ${val}% per annum`,
          explanation: 'Subsidized annual interest rate charged on the credit facility.',
          isFinancialCondition: true,
          financialContextNote: 'YojnaSetu has compared this information with the documented programme condition.',
        };
      }

      if (f === 'repayment_period_max_months' || f === 'repayment_period_months') {
        const yrs = hasNum ? Math.round(numVal / 12) : null;
        return {
          raw: rule,
          category: 'INCOME_FINANCIAL',
          humanTitle: 'Program Financial Condition — Repayment Tenure',
          humanValue: `Repayment Tenure: Up to ${val} months${yrs ? ` (${yrs} years)` : ''}`,
          explanation: 'Maximum scheduled tenure allowed for clearing loan principal and interest.',
          isFinancialCondition: true,
          financialContextNote: 'YojnaSetu has compared this information with the documented programme condition.',
        };
      }

      if (f === 'moratorium_min_months' || f === 'moratorium_period_months') {
        return {
          raw: rule,
          category: 'INCOME_FINANCIAL',
          humanTitle: 'Program Financial Condition — Moratorium Period',
          humanValue: `Moratorium Period: ${val} months`,
          explanation: 'Grace period before scheduled principal repayment installments commence.',
          isFinancialCondition: true,
          financialContextNote: 'YojnaSetu has compared this information with the documented programme condition.',
        };
      }
    }

    // 3. CATEGORY: Project & Business Conditions
    if (
      f === 'project_cost' ||
      f === 'max_project_cost' ||
      f === 'min_project_cost' ||
      f === 'business_stage' ||
      f === 'activity_type' ||
      f === 'trade' ||
      f === 'new_unit_required' ||
      f === 'existing_unit_allowed' ||
      f === 'enterprise_size' ||
      f === 'sector'
    ) {
      if (f === 'project_cost') {
        const formattedAmt = hasNum ? `₹${numVal.toLocaleString('en-IN')}` : val;
        return {
          raw: rule,
          category: 'PROJECT_BUSINESS',
          humanTitle: 'Program Financial Condition — Minimum Project Cost',
          humanValue: `Minimum Project Cost: ${op === '>' ? 'More than ' : ''}${formattedAmt}`,
          explanation: 'Minimum total project cost required for eligibility under this term loan program.',
          isFinancialCondition: true,
          financialContextNote: 'YojnaSetu has compared this information with the documented programme condition.',
        };
      }

      if (f === 'max_project_cost') {
        const formattedAmt = hasNum ? `₹${numVal.toLocaleString('en-IN')}` : val;
        return {
          raw: rule,
          category: 'PROJECT_BUSINESS',
          humanTitle: 'Program Financial Condition — Maximum Project Cost',
          humanValue: `Maximum Project Cost: Up to ${formattedAmt}`,
          explanation: 'Maximum permissible capital investment for eligible enterprise proposals.',
          isFinancialCondition: true,
          financialContextNote: 'YojnaSetu has compared this information with the documented programme condition.',
        };
      }

      if (f === 'new_unit_required') {
        return {
          raw: rule,
          category: 'PROJECT_BUSINESS',
          humanTitle: 'New Enterprise / Project Requirement',
          humanValue: val.toUpperCase() === 'TRUE' ? 'Eligible for New Business Units Only' : `New unit requirement: ${val}`,
          explanation: 'Assistance is meant for setting up fresh greenfield units or enterprises.',
          isFinancialCondition: false,
        };
      }

      if (f === 'activity_type' || f === 'trade') {
        return {
          raw: rule,
          category: 'PROJECT_BUSINESS',
          humanTitle: 'Eligible Economic Trade / Activity',
          humanValue: val === 'TRADITIONAL_TRADE_18' ? '18 Traditional Artisan & Craft Trades' : `Activity: ${val.replace(/_/g, ' ')}`,
          explanation: 'Project proposal must fall under the approved list of vocational or industrial trades.',
          isFinancialCondition: false,
        };
      }
    }

    // 4. CATEGORY: Applicant Eligibility
    if (
      f === 'age_min' ||
      f === 'age_max' ||
      f === 'gender_condition' ||
      f === 'gender' ||
      f === 'citizenship' ||
      f === 'domicile' ||
      f === 'education_applicable' ||
      f === 'applicant_types'
    ) {
      if (f === 'age_min') {
        return {
          raw: rule,
          category: 'APPLICANT',
          humanTitle: 'Minimum Age Requirement',
          humanValue: `Minimum Age: ${val} years`,
          explanation: 'Applicant must have reached the minimum legal age at the time of application.',
          isFinancialCondition: false,
        };
      }
      if (f === 'age_max') {
        return {
          raw: rule,
          category: 'APPLICANT',
          humanTitle: 'Maximum Age Ceiling',
          humanValue: `Maximum Age: ${val} years`,
          explanation: 'Applicant must not exceed this age ceiling at the time of submission.',
          isFinancialCondition: false,
        };
      }
      if (f === 'gender_condition' || f === 'gender') {
        const isFem = val.toUpperCase() === 'F' || val.toUpperCase() === 'FEMALE';
        return {
          raw: rule,
          category: 'APPLICANT',
          humanTitle: 'Target Gender Requirement',
          humanValue: isFem ? 'Targeted for Female Beneficiaries' : `Eligible Gender: ${val}`,
          explanation: isFem ? 'Exclusively reserved or prioritized for women entrepreneurs and artisans.' : 'Gender eligibility as defined in scheme rules.',
          isFinancialCondition: false,
        };
      }
    }

    // 5. CATEGORY: Other Conditions (e.g. application_route, state_coverage, etc.)
    if (f === 'application_route') {
      return {
        raw: rule,
        category: 'OTHER',
        humanTitle: 'Authorized Application Route',
        humanValue: 'Authorized Portal / Channel Partner Submission Only',
        explanation: 'Applications are accepted only through authorized partner channels (e.g. PM-SURAJ portal or designated SCAs). Direct application to headquarters is not accepted.',
        isFinancialCondition: false,
      };
    }

    // Fallback for any other rule:
    const fallbackTitle = isLegacyFinancialMsg
      ? `Program Financial Condition — ${f.replace(/_/g, ' ')}`
      : f.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

    return {
      raw: rule,
      category: isLegacyFinancialMsg ? 'INCOME_FINANCIAL' : 'OTHER',
      humanTitle: fallbackTitle,
      humanValue: `${f.replace(/_/g, ' ')}: ${val}`,
      explanation: rule.description || (rule.error_message && !rule.error_message.includes('RULE-') ? rule.error_message : 'Standard verified scheme criteria.'),
      isFinancialCondition: isLegacyFinancialMsg,
      financialContextNote: isLegacyFinancialMsg ? 'YojnaSetu has compared this information with the documented programme condition.' : undefined,
    };
  };

  const humanizedRules = rules.map(humanizeRule);

  const categoriesMeta: Record<
    EligibilityCategory,
    { title: string; icon: React.FC<{ className?: string }>; count: number; desc: string }
  > = {
    APPLICANT: {
      title: t('schemeDetail.eligibility.catApplicant', 'Applicant & Personal Requirements'),
      icon: UserCheck,
      count: humanizedRules.filter((r) => r.category === 'APPLICANT').length,
      desc: 'Age limits, gender, citizenship, and educational prerequisites',
    },
    INCOME_FINANCIAL: {
      title: t('schemeDetail.eligibility.catIncome', 'Income & Financial Criteria'),
      icon: Wallet,
      count: humanizedRules.filter((r) => r.category === 'INCOME_FINANCIAL').length,
      desc: 'Family income ceilings, loan quantums, interest rates, and tenures',
    },
    CATEGORY_COMMUNITY: {
      title: t('schemeDetail.eligibility.catCommunity', 'Category & Community Guidelines'),
      icon: Users,
      count: humanizedRules.filter((r) => r.category === 'CATEGORY_COMMUNITY').length,
      desc: 'Affirmative action, social category, and reserved community criteria',
    },
    PROJECT_BUSINESS: {
      title: t('schemeDetail.eligibility.catProject', 'Project & Business Rules'),
      icon: Briefcase,
      count: humanizedRules.filter((r) => r.category === 'PROJECT_BUSINESS').length,
      desc: 'Permissible project costs, business stage, and eligible trades',
    },
    OTHER: {
      title: t('schemeDetail.eligibility.catOther', 'Application Route & Other Conditions'),
      icon: HelpCircle,
      count: humanizedRules.filter((r) => r.category === 'OTHER').length,
      desc: 'Authorized application channels and territorial coverage',
    },
  };

  const activeCategories = (
    Object.keys(categoriesMeta) as EligibilityCategory[]
  ).filter((cat) => categoriesMeta[cat].count > 0);

  const filteredRules =
    activeCategory === 'ALL'
      ? humanizedRules
      : humanizedRules.filter((r) => r.category === activeCategory);

  return (
    <section id="eligibility" className="scroll-mt-24 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg sm:text-xl font-extrabold text-[#3B2522] tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-[#EA717B]" />
            {t('schemeDetail.eligibility.whoCanApply', 'Who Can Apply?')}
          </h2>
          <p className="text-xs text-[#765E59] mt-0.5">
            {t('schemeDetail.eligibility.whoCanApplyDesc', 'Verified official eligibility rules and program conditions extracted from scheme gazette.')}
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="text-[11px] font-bold bg-[#FFF4EC] text-[#4A2525] px-3 py-1 rounded-full border border-[#E8D8D2]">
            {rules.length} {rules.length === 1 ? t('schemeDetail.eligibility.officialRulesCount', 'Official Rule') : t('schemeDetail.eligibility.officialRulesCount_other', 'Official Rules')}
          </span>
          <button
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            className="text-[11px] font-semibold text-[#765E59] hover:text-[#3B2522] flex items-center gap-1 bg-white px-2.5 py-1 rounded-full border border-[#E8D8D2] shadow-warm-xs transition cursor-pointer"
          >
            <Code2 className="w-3.5 h-3.5 text-[#765E59]" />
            {showTechnicalDetails ? t('schemeDetail.eligibility.hideAuditFields', 'Hide Audit Fields') : t('schemeDetail.eligibility.showAuditFields', 'Show Audit Fields')}
          </button>
        </div>
      </div>

      {/* Citizen Guidance Advisory Card */}
      <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-2xl p-4 text-xs text-[#4A2525] flex items-start gap-3 shadow-warm-xs">
        <Info className="w-4 h-4 text-[#EA717B] shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-bold text-[#4A2525]">{t('schemeDetail.eligibility.citizenGuidanceGuarantee', 'Citizen Guidance Guarantee')}</p>
          <p className="text-[#765E59] leading-relaxed text-[11px]">
            {t('schemeDetail.eligibility.citizenGuidanceGuaranteeDesc', 'YojnaSetu presents documented criteria exactly as verified in official government notifications. YojnaSetu never approves, rejects, or decides applications. Final eligibility and approvals are made exclusively by the concerned department or designated lending partner.')}
          </p>
        </div>
      </div>

      {/* Category Pills Filter */}
      {activeCategories.length > 1 && (
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pb-1">
          <button
            onClick={() => setActiveCategory('ALL')}
            className={`text-xs font-bold px-3.5 py-1.5 rounded-xl border transition-all duration-150 cursor-pointer whitespace-nowrap shrink-0 ${
              activeCategory === 'ALL'
                ? 'bg-[#EA717B] text-white border-[#EA717B] shadow-warm-xs'
                : 'bg-white text-[#765E59] border-[#E8D8D2] hover:bg-[#FFF4EC]'
            }`}
          >
            {t('schemeDetail.eligibility.allConditions', { count: rules.length, defaultValue: `All Conditions (${rules.length})` })}
          </button>

          {activeCategories.map((catKey) => {
            const cat = categoriesMeta[catKey];
            const Icon = cat.icon;
            const isSelected = activeCategory === catKey;
            return (
              <button
                key={catKey}
                onClick={() => setActiveCategory(catKey)}
                className={`text-xs font-bold px-3.5 py-1.5 rounded-xl border transition-all duration-150 cursor-pointer whitespace-nowrap shrink-0 flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-[#EA717B] text-white border-[#EA717B] shadow-warm-xs'
                    : 'bg-white text-[#765E59] border-[#E8D8D2] hover:bg-[#FFF4EC]'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isSelected ? 'text-[#F7AE56]' : 'text-[#765E59]'}`} />
                <span>{cat.title}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full font-extrabold ${
                    isSelected ? 'bg-white/20 text-white' : 'bg-[#FFF4EC] text-[#4A2525]'
                  }`}
                >
                  {cat.count}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {/* Rules Grid */}
      {rules.length === 0 ? (
        <div className="bg-white p-6 rounded-2xl border border-[#E8D8D2] text-center space-y-2">
          <Info className="w-8 h-8 text-[#765E59] mx-auto" />
          <p className="text-sm font-bold text-[#3B2522]">{t('schemeDetail.eligibility.standardGuidelines', 'Standard Government Scheme Guidelines')}</p>
          <p className="text-xs text-[#765E59] max-w-md mx-auto">
            {t('schemeDetail.eligibility.standardGuidelinesDesc', 'Specific parametric rules are verified under general ministry directives. General Indian citizenship and sector-specific operational criteria apply.')}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredRules.map((r, idx) => {
            const cat = categoriesMeta[r.category];
            const CategoryIcon = cat.icon;
            return (
              <div
                key={r.raw.rule_id || idx}
                className="bg-white p-5 rounded-2xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-md hover:border-[#FFD0CA] transition-all duration-150 space-y-3 flex flex-col justify-between"
              >
                <div className="space-y-2">
                  {/* Category & Type Badges */}
                  <div className="flex items-center justify-between gap-2">
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#4A2525] bg-[#FFF4EC] px-2 py-0.5 rounded-md">
                      <CategoryIcon className="w-3 h-3 text-[#EA717B]" />
                      {cat.title}
                    </span>

                    <span
                      className={`text-[10px] font-extrabold px-2 py-0.5 rounded-md uppercase tracking-wider ${
                        r.raw.rule_type === 'ELIGIBILITY'
                          ? 'bg-[#FFF4EC] text-[#EA717B] border border-[#FFD0CA]'
                          : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      }`}
                    >
                      {r.raw.rule_type || 'ELIGIBILITY'}
                    </span>
                  </div>

                  {/* Human-Readable Title */}
                  <h3 className="text-sm font-bold text-[#3B2522] leading-snug">
                    {r.humanTitle}
                  </h3>

                  {/* Value / Main Criterion */}
                  <div className="bg-[#FFF4EC]/50 rounded-xl p-3 border border-[#E8D8D2]">
                    <p className="text-xs font-extrabold text-[#3B2522]">
                      {r.humanValue}
                    </p>
                    {r.explanation && (
                      <p className="text-[11px] text-[#765E59] mt-1 leading-relaxed">
                        {r.explanation}
                      </p>
                    )}
                  </div>

                  {/* Financial Condition Context Note */}
                  {r.isFinancialCondition && r.financialContextNote && (
                    <div className="flex items-start gap-1.5 text-[11px] text-emerald-800 bg-emerald-50/70 p-2 rounded-lg border border-emerald-100">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                      <span>{r.financialContextNote}</span>
                    </div>
                  )}
                </div>

                {/* Secondary Technical Disclosure */}
                {showTechnicalDetails && (
                  <div className="pt-2 border-t border-[#E8D8D2]/60 text-[10px] text-[#765E59] font-mono space-y-1">
                    <div className="flex items-center justify-between">
                      <span>Field: {r.raw.field} ({r.raw.operator})</span>
                      <span>ID: {r.raw.rule_id}</span>
                    </div>
                    {r.raw.source_document && (
                      <div className="truncate" title={r.raw.source_document}>
                        Source: {r.raw.source_document}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
};
