import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Scheme, SchemeDocument } from '../types';
import {
  FileText,
  ShieldCheck,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CreditCard,
  Home,
  Wallet,
  Users,
  GraduationCap,
  Briefcase,
  FileCheck2,
  Info,
  Search,
  Code2
} from 'lucide-react';

interface SchemeDocumentsSectionProps {
  scheme: Scheme;
}

type DocumentGroupKey =
  | 'IDENTITY_KYC'
  | 'ADDRESS_RESIDENCE'
  | 'INCOME_FINANCIAL'
  | 'CATEGORY_COMMUNITY'
  | 'EDUCATION_QUALIFICATION'
  | 'BUSINESS_PROJECT'
  | 'SCHEME_AGENCY_SPECIFIC';

interface DocumentGroupMeta {
  key: DocumentGroupKey;
  title: string;
  description: string;
  icon: React.FC<{ className?: string }>;
  iconBg: string;
  iconColor: string;
}

const GROUPS_META: DocumentGroupMeta[] = [
  {
    key: 'IDENTITY_KYC',
    title: 'Identity & KYC Documents',
    description: 'Proof of identity and demographic verification via UIDAI / official IDs',
    icon: CreditCard,
    iconBg: 'bg-[#FFD0CA]/50',
    iconColor: 'text-[#EA717B]',
  },
  {
    key: 'ADDRESS_RESIDENCE',
    title: 'Address & Residence Documents',
    description: 'Proof of domicile, permanent residence, or local address',
    icon: Home,
    iconBg: 'bg-[#FFF4EC]',
    iconColor: 'text-[#765E59]',
  },
  {
    key: 'INCOME_FINANCIAL',
    title: 'Income & Financial Documents',
    description: 'Bank passbook, income certificates, tax returns, and bank statements',
    icon: Wallet,
    iconBg: 'bg-[#F7AE56]/20',
    iconColor: 'text-[#3B2522]',
  },
  {
    key: 'CATEGORY_COMMUNITY',
    title: 'Category & Community Documents',
    description: 'Scheduled Caste, Tribe, OBC, Minority, or Disability certificates',
    icon: Users,
    iconBg: 'bg-[#FFD0CA]/40',
    iconColor: 'text-[#4A2525]',
  },
  {
    key: 'EDUCATION_QUALIFICATION',
    title: 'Education & Qualification',
    description: 'Academic marksheets, degree certificates, and vocational diplomas',
    icon: GraduationCap,
    iconBg: 'bg-[#FFF4EC]',
    iconColor: 'text-[#EA717B]',
  },
  {
    key: 'BUSINESS_PROJECT',
    title: 'Business & Project Documents',
    description: 'Detailed Project Report (DPR), machinery quotations, and Udyam registration',
    icon: Briefcase,
    iconBg: 'bg-[#F7AE56]/20',
    iconColor: 'text-[#4A2525]',
  },
  {
    key: 'SCHEME_AGENCY_SPECIFIC',
    title: 'Scheme & Agency-Specific Documents',
    description: 'Departmental checklists, declarations, and authorized agency forms',
    icon: FileCheck2,
    iconBg: 'bg-[#FFF4EC]',
    iconColor: 'text-[#765E59]',
  },
];

export const SchemeDocumentsSection: React.FC<SchemeDocumentsSectionProps> = ({ scheme }) => {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  // Active documents from scheme
  const allDocs: SchemeDocument[] = useMemo(() => {
    return (scheme.documents || []).filter((d) => d.active !== false);
  }, [scheme.documents]);

  // Categorize document
  const categorizeDocument = (doc: SchemeDocument): DocumentGroupKey => {
    const name = (doc.document_name || '').toLowerCase();
    const cond = (doc.condition || '').toLowerCase();
    const type = (doc.applicant_type || '').toLowerCase();
    const text = `${name} ${cond} ${type}`;

    // 1. Identity & KYC
    if (
      text.includes('aadhaar') ||
      text.includes('pan card') ||
      (text.includes('pan') && !text.includes('company') && !text.includes('partner')) ||
      text.includes('voter') ||
      text.includes('passport') ||
      text.includes('photograph') ||
      text.includes('photo') ||
      text.includes('kyc') ||
      text.includes('driving license') ||
      text.includes('driving licence')
    ) {
      if (text.includes('bank account') || text.includes('passbook') || text.includes('statement')) {
        return 'INCOME_FINANCIAL';
      }
      return 'IDENTITY_KYC';
    }

    // 2. Address & Residence
    if (
      text.includes('domicile') ||
      text.includes('residence') ||
      text.includes('address proof') ||
      text.includes('electricity bill') ||
      text.includes('ration card') ||
      text.includes('water bill') ||
      text.includes('utility bill')
    ) {
      return 'ADDRESS_RESIDENCE';
    }

    // 3. Category & Community
    if (
      text.includes('caste') ||
      text.includes('scheduled caste') ||
      text.includes('scheduled tribe') ||
      text.includes('sc certificate') ||
      text.includes('st certificate') ||
      text.includes('obc') ||
      text.includes('minority') ||
      text.includes('disability') ||
      text.includes('pwd') ||
      text.includes('divyangjan') ||
      text.includes('community certificate') ||
      text.includes('tribe')
    ) {
      return 'CATEGORY_COMMUNITY';
    }

    // 4. Income & Financial
    if (
      text.includes('income') ||
      text.includes('bpl') ||
      text.includes('salary') ||
      text.includes('bank account') ||
      text.includes('passbook') ||
      text.includes('bank statement') ||
      text.includes('itr') ||
      text.includes('tax return') ||
      text.includes('balance sheet') ||
      text.includes('financial') ||
      text.includes('audited') ||
      text.includes('net worth')
    ) {
      return 'INCOME_FINANCIAL';
    }

    // 5. Education & Qualification
    if (
      text.includes('education') ||
      text.includes('qualification') ||
      text.includes('marksheet') ||
      text.includes('degree') ||
      text.includes('diploma') ||
      text.includes('matriculation') ||
      text.includes('school') ||
      text.includes('college') ||
      text.includes('admission') ||
      text.includes('certificate / marksheet') ||
      text.includes('skill')
    ) {
      return 'EDUCATION_QUALIFICATION';
    }

    // 6. Business & Project
    if (
      text.includes('project report') ||
      text.includes('dpr') ||
      text.includes('quotation') ||
      text.includes('machinery') ||
      text.includes('project profile') ||
      text.includes('business') ||
      text.includes('udyam') ||
      text.includes('registration') ||
      text.includes('gst') ||
      text.includes('trade license') ||
      text.includes('partnership') ||
      text.includes('incorporation') ||
      text.includes('msme') ||
      text.includes('estimate') ||
      text.includes('work order') ||
      text.includes('lease')
    ) {
      return 'BUSINESS_PROJECT';
    }

    // 7. Scheme / Agency-Specific
    return 'SCHEME_AGENCY_SPECIFIC';
  };

  // Grouped documents map
  const groupedDocs = useMemo(() => {
    const map = new Map<DocumentGroupKey, SchemeDocument[]>();
    GROUPS_META.forEach((g) => map.set(g.key, []));

    allDocs.forEach((doc) => {
      const groupKey = categorizeDocument(doc);
      map.get(groupKey)?.push(doc);
    });

    return map;
  }, [allDocs]);

  // Track expanded groups - by default all collapsed as requested in section 9
  const [expandedGroups, setExpandedGroups] = useState<Record<DocumentGroupKey, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    GROUPS_META.forEach((g) => {
      // By default collapsed as specified in section 9 ("DOCUMENT DISPLAY — COLLAPSED BY DEFAULT")
      initial[g.key] = false;
    });
    return initial as Record<DocumentGroupKey, boolean>;
  });

  const toggleGroup = (key: DocumentGroupKey) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const expandAll = () => {
    const next: Record<string, boolean> = {};
    GROUPS_META.forEach((g) => {
      next[g.key] = true;
    });
    setExpandedGroups(next as Record<DocumentGroupKey, boolean>);
  };

  const collapseAll = () => {
    const next: Record<string, boolean> = {};
    GROUPS_META.forEach((g) => {
      next[g.key] = false;
    });
    setExpandedGroups(next as Record<DocumentGroupKey, boolean>);
  };

  const areAllExpanded = GROUPS_META.every((g) => expandedGroups[g.key]);

  // Only render categories with documents matching the search
  const populatedGroups = GROUPS_META.filter((meta) => {
    const docsInGroup = groupedDocs.get(meta.key) || [];
    if (!searchTerm.trim()) return docsInGroup.length > 0;

    return docsInGroup.some(
      (d) =>
        d.document_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (d.condition && d.condition.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  });

  const formatRequirementType = (type: string) => {
    const upper = (type || '').toUpperCase();
    if (upper === 'MANDATORY' || upper === 'REQUIRED') {
      return {
        label: 'Required',
        className: 'bg-[#EA717B]/15 text-[#4A2525] border-[#EA717B]/30',
      };
    }
    if (upper === 'CONDITIONAL' || upper === 'PARTNER_VERIFICATION') {
      return {
        label: 'Conditional',
        className: 'bg-[#F7AE56]/20 text-[#3B2522] border-[#F7AE56]/40',
      };
    }
    return {
      label: 'Optional',
      className: 'bg-[#FFF4EC] text-[#765E59] border-[#E8D8D2]',
    };
  };

  return (
    <section id="documents" className="scroll-mt-24 space-y-6">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg sm:text-xl font-extrabold text-[#3B2522] tracking-tight flex items-center gap-2">
            <FileText className="w-5 h-5 text-[#EA717B]" />
            Documents You May Need
          </h2>
          <p className="text-xs text-[#765E59] mt-0.5">
            Organized checklist of verified government documents required before application submission.
          </p>
        </div>

        {/* Dynamic Count Header */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="text-[11px] font-extrabold bg-[#FFF4EC] text-[#3B2522] px-3 py-1 rounded-full border border-[#E8D8D2]">
            {allDocs.length} official {allDocs.length === 1 ? 'requirement' : 'requirements'}
          </span>
          <button
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            className="text-[11px] font-semibold text-[#765E59] hover:text-[#3B2522] flex items-center gap-1 bg-white px-2.5 py-1 rounded-full border border-[#E8D8D2] shadow-warm-xs transition cursor-pointer"
          >
            <Code2 className="w-3.5 h-3.5 text-[#765E59]/60" />
            {showTechnicalDetails ? 'Hide IDs' : 'Show IDs'}
          </button>
        </div>
      </div>

      {/* Action Row: Search & Expand All */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-[#E8D8D2] shadow-warm-xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-[#765E59]/60 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search required documents (e.g. Aadhaar, ITR, DPR)..."
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl border border-[#E8D8D2] bg-[#FFFBF0] text-[#3B2522] placeholder-[#765E59]/60 focus:bg-white focus:border-[#EA717B] focus:ring-1 focus:ring-[#EA717B] focus:outline-none transition"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
          <button
            onClick={areAllExpanded ? collapseAll : expandAll}
            className="text-xs font-bold text-[#4A2525] bg-[#FFD0CA]/60 hover:bg-[#FFD0CA] px-3.5 py-1.5 rounded-xl border border-[#E8D8D2] transition cursor-pointer flex items-center gap-1"
          >
            {areAllExpanded ? (
              <>
                <ChevronUp className="w-4 h-4" /> {t('schemeDetail.documents.collapseAllGroups', 'Collapse All Groups')}
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" /> {t('schemeDetail.documents.expandAllGroups', 'Expand All Groups')}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Document Groups Stack */}
      {allDocs.length === 0 ? (
        <div className="bg-[#FFF4EC] border border-[#F7AE56]/30 p-6 rounded-2xl text-center space-y-2">
          <Info className="w-8 h-8 text-[#F7AE56] mx-auto" />
          <p className="text-sm font-bold text-[#3B2522]">{t('schemeDetail.documents.underReview', 'Document Guidelines Under Gazette Review')}</p>
          <p className="text-xs text-[#765E59] max-w-lg mx-auto">
            Official document requirements are being synchronized with the latest ministry gazette. Please keep standard identity (Aadhaar), residence, and bank records ready.
          </p>
        </div>
      ) : populatedGroups.length === 0 ? (
        <div className="bg-white p-6 rounded-2xl border border-[#E8D8D2] text-center space-y-2">
          <p className="text-xs text-[#765E59]">{t('schemeDetail.documents.noDocsMatch', { term: searchTerm, defaultValue: `No documents found matching "${searchTerm}".` })}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {populatedGroups.map((meta) => {
            const rawDocs = groupedDocs.get(meta.key) || [];
            const docsToDisplay = searchTerm.trim()
              ? rawDocs.filter(
                  (d) =>
                    d.document_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    (d.condition && d.condition.toLowerCase().includes(searchTerm.toLowerCase()))
                )
              : rawDocs;

            const isExpanded = expandedGroups[meta.key] || Boolean(searchTerm.trim());
            const Icon = meta.icon;

            return (
              <div
                key={meta.key}
                className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs overflow-hidden transition-all duration-150"
              >
                {/* Accordion Group Header */}
                <button
                  onClick={() => toggleGroup(meta.key)}
                  className="w-full flex items-center justify-between p-4 sm:p-4.5 hover:bg-[#FFF4EC]/60 transition-colors cursor-pointer text-left gap-3"
                  aria-expanded={isExpanded}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`w-9 h-9 rounded-xl ${meta.iconBg} ${meta.iconColor} flex items-center justify-center shrink-0`}>
                      <Icon className="w-4.5 h-4.5" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-[#3B2522] truncate">
                          {t(`schemeDetail.documents.cat${meta.key}Title`, meta.title)}
                        </h3>
                        <span className="text-[11px] font-extrabold bg-[#FFF4EC] text-[#765E59] px-2 py-0.5 rounded-full shrink-0 border border-[#E8D8D2]">
                          {docsToDisplay.length}
                        </span>
                      </div>
                      <p className="text-[11px] text-[#765E59] truncate hidden sm:block">
                        {meta.description}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs font-semibold text-[#765E59] hidden sm:inline">
                      {isExpanded ? t('common.hide', 'Hide') : t('common.show', 'Show')}
                    </span>
                    <div className="w-7 h-7 rounded-lg bg-[#FFF4EC] text-[#4A2525] flex items-center justify-center">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </div>
                  </div>
                </button>

                {/* Expanded Document Rows */}
                {isExpanded && (
                  <div className="border-t border-[#E8D8D2]/60 divide-y divide-[#E8D8D2]/40 bg-[#FFFBF0]/60">
                    {docsToDisplay.map((doc) => {
                      const reqBadge = formatRequirementType(doc.requirement_type);
                      return (
                        <div
                          key={doc.document_id}
                          className="p-4 sm:px-5 sm:py-3.5 hover:bg-white transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-2.5"
                        >
                          <div className="space-y-1 min-w-0 flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                              <span className="text-xs font-extrabold text-[#3B2522]">
                                {doc.document_name}
                              </span>
                              <span
                                className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border uppercase shrink-0 ${reqBadge.className}`}
                              >
                                {reqBadge.label}
                              </span>
                            </div>

                            {doc.condition && (
                              <p className="text-[11px] text-[#765E59] pl-6 leading-relaxed">
                                {doc.condition}
                              </p>
                            )}

                            {/* Secondary Technical ID & Source (hidden from primary UI) */}
                            {showTechnicalDetails && (
                              <div className="pl-6 pt-1 text-[10px] text-[#765E59]/70 font-mono flex items-center gap-3">
                                <span>ID: {doc.document_id}</span>
                                {doc.source_section && <span>Source: {doc.source_section}</span>}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Advisory Notice */}
      <div className="bg-[#FFF4EC] rounded-2xl p-4 border border-[#E8D8D2] text-xs text-[#765E59] flex items-start gap-3">
        <ShieldCheck className="w-4 h-4 text-[#EA717B] shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-bold text-[#3B2522] text-[11px]">{t('schemeDetail.documents.zeroStorage', 'Zero Document Storage Security')}</p>
          <p className="text-[11px] text-[#765E59] leading-relaxed">
            YojnaSetu never asks you to upload, transmit, or store sensitive documents. Please carry your original papers or present them via authorized DigiLocker channels during in-person verification with authorized channel partners or bank officers.
          </p>
        </div>
      </div>
    </section>
  );
};
