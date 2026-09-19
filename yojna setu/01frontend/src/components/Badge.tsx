import React from 'react';
import { useTranslation } from 'react-i18next';
import { ShieldCheck, Clock, CheckCircle2, XCircle, AlertCircle, FileCheck } from 'lucide-react';
import { ApplicationStatus } from '../types';

interface VerificationBadgeProps {
  status?: string | null;
}

export const VerificationBadge: React.FC<VerificationBadgeProps> = ({ status }) => {
  const { t } = useTranslation();
  const normStatus = (status || '').toUpperCase().trim();

  if (normStatus === 'VERIFIED' || normStatus === 'VERIFIED_OFFICIAL') {
    return (
      <span className="inline-flex items-center gap-1.5 bg-[#EAF4EE] text-[#1B5E20] text-xs font-semibold px-2.5 py-0.5 rounded-lg border border-[#A5D6A7]">
        <ShieldCheck className="w-3.5 h-3.5 text-[#2E7D32] shrink-0" aria-hidden="true" />
        {t('schemeCard.govtVerified')}
      </span>
    );
  }

  if (normStatus === 'SOURCE_VERIFIED') {
    return (
      <span className="inline-flex items-center gap-1.5 bg-[#FFF0EE] text-[#EA717B] text-xs font-semibold px-2.5 py-0.5 rounded-lg border border-[#FFD0CA]">
        <ShieldCheck className="w-3.5 h-3.5 text-[#EA717B] shrink-0" aria-hidden="true" />
        {t('schemeCard.sourceVerified')}
      </span>
    );
  }

  if (normStatus === 'UNDER_REVIEW' || normStatus === 'UNVERIFIED' || normStatus === 'NEEDS_SOURCE_VERIFICATION') {
    return (
      <span className="inline-flex items-center gap-1.5 bg-[#FFF4EC] text-[#B45309] text-xs font-medium px-2.5 py-0.5 rounded-lg border border-[#F7AE56]/40">
        <Clock className="w-3.5 h-3.5 text-[#F7AE56] shrink-0" aria-hidden="true" />
        {t('schemeCard.underVerification')}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 bg-[#FFF4EC] text-[#765E59] text-xs font-medium px-2.5 py-0.5 rounded-lg border border-[#E8D8D2]">
      <AlertCircle className="w-3.5 h-3.5 text-[#9B817A] shrink-0" aria-hidden="true" />
      {t('schemeCard.sourceUnavailable')}
    </span>
  );
};

interface ApplicationStatusBadgeProps {
  status: ApplicationStatus | string;
}

export const ApplicationStatusBadge: React.FC<ApplicationStatusBadgeProps> = ({ status }) => {
  const configs: Record<string, { label: string; bg: string; text: string; border: string; icon: React.ReactNode }> = {
    DRAFT: {
      label: 'Guidance Started',
      bg: 'bg-[#FFF4EC]',
      text: 'text-[#765E59]',
      border: 'border-[#E8D8D2]',
      icon: <Clock className="w-3.5 h-3.5 text-[#9B817A]" aria-hidden="true" />
    },
    DOCUMENTS_PENDING: {
      label: 'Checklist Pending',
      bg: 'bg-[#FFF4EC]',
      text: 'text-[#B45309]',
      border: 'border-[#F7AE56]/40',
      icon: <AlertCircle className="w-3.5 h-3.5 text-[#F7AE56]" aria-hidden="true" />
    },
    READY_FOR_SUBMISSION: {
      label: 'Ready for Official Portal',
      bg: 'bg-[#FFF0EE]',
      text: 'text-[#EA717B]',
      border: 'border-[#FFD0CA]',
      icon: <FileCheck className="w-3.5 h-3.5 text-[#EA717B]" aria-hidden="true" />
    },
    SUBMITTED: {
      label: 'Redirected to Portal',
      bg: 'bg-[#FFF0EE]',
      text: 'text-[#4A2525]',
      border: 'border-[#FFD0CA]',
      icon: <Clock className="w-3.5 h-3.5 text-[#EA717B]" aria-hidden="true" />
    },
    UNDER_REVIEW: {
      label: 'Assisted Review',
      bg: 'bg-[#FFF4EC]',
      text: 'text-[#B45309]',
      border: 'border-[#F7AE56]/40',
      icon: <Clock className="w-3.5 h-3.5 text-[#F7AE56]" aria-hidden="true" />
    },
    CORRECTION_REQUIRED: {
      label: 'Action Required',
      bg: 'bg-[#FDECEF]',
      text: 'text-[#B91C1C]',
      border: 'border-[#EA717B]/40',
      icon: <AlertCircle className="w-3.5 h-3.5 text-[#EA717B] font-extrabold animate-pulse" aria-hidden="true" />
    },
    NEEDS_CORRECTION: {
      label: 'Action Required',
      bg: 'bg-[#FDECEF]',
      text: 'text-[#B91C1C]',
      border: 'border-[#EA717B]/40',
      icon: <AlertCircle className="w-3.5 h-3.5 text-[#EA717B] font-extrabold animate-pulse" aria-hidden="true" />
    },
    MORE_INFORMATION_REQUIRED: {
      label: 'Information Required',
      bg: 'bg-[#FFF4EC]',
      text: 'text-[#B45309]',
      border: 'border-[#F7AE56]/40',
      icon: <AlertCircle className="w-3.5 h-3.5 text-[#F7AE56] font-extrabold animate-pulse" aria-hidden="true" />
    },
    APPROVED: {
      label: 'Approved',
      bg: 'bg-[#EAF4EE]',
      text: 'text-[#1B5E20]',
      border: 'border-[#A5D6A7]',
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-[#2E7D32]" aria-hidden="true" />
    },
    COMPLETED: {
      label: 'Completed / Benefit Disbursed',
      bg: 'bg-[#EAF4EE]',
      text: 'text-[#1B5E20]',
      border: 'border-[#81C784]',
      icon: <ShieldCheck className="w-3.5 h-3.5 text-[#2E7D32] font-extrabold" aria-hidden="true" />
    },
    REJECTED: {
      label: 'Rejected',
      bg: 'bg-[#FDECEF]',
      text: 'text-[#B91C1C]',
      border: 'border-[#EA717B]/40',
      icon: <XCircle className="w-3.5 h-3.5 text-[#EA717B]" aria-hidden="true" />
    },
    WITHDRAWN: {
      label: 'Withdrawn',
      bg: 'bg-[#FFF4EC]',
      text: 'text-[#765E59]',
      border: 'border-[#E8D8D2]',
      icon: <XCircle className="w-3.5 h-3.5 text-[#9B817A]" aria-hidden="true" />
    },
  };

  const cfg = configs[status] || {
    label: String(status).replace(/_/g, ' '),
    bg: 'bg-[#FFF4EC]',
    text: 'text-[#765E59]',
    border: 'border-[#E8D8D2]',
    icon: <Clock className="w-3.5 h-3.5 text-[#9B817A]" />
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold border ${cfg.bg} ${cfg.text} ${cfg.border}`}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
};
