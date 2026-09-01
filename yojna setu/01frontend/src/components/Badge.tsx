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
      <span className="inline-flex items-center gap-1 bg-emerald-100 text-emerald-800 text-[11px] font-bold px-2 py-0.5 rounded border border-emerald-300">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
        {t('schemeCard.govtVerified')}
      </span>
    );
  }

  if (normStatus === 'SOURCE_VERIFIED') {
    return (
      <span className="inline-flex items-center gap-1 bg-blue-100 text-blue-800 text-[11px] font-bold px-2 py-0.5 rounded border border-blue-300">
        <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
        {t('schemeCard.sourceVerified')}
      </span>
    );
  }

  if (normStatus === 'UNDER_REVIEW' || normStatus === 'UNVERIFIED' || normStatus === 'NEEDS_SOURCE_VERIFICATION') {
    return (
      <span className="inline-flex items-center gap-1 bg-amber-100 text-amber-800 text-[11px] font-medium px-2 py-0.5 rounded border border-amber-300">
        <Clock className="w-3.5 h-3.5 text-amber-600" />
        {t('schemeCard.underVerification')}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 bg-slate-100 text-slate-700 text-[11px] font-medium px-2 py-0.5 rounded border border-slate-300">
      <AlertCircle className="w-3.5 h-3.5 text-slate-500" />
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
      bg: 'bg-slate-100',
      text: 'text-slate-700',
      border: 'border-slate-300',
      icon: <Clock className="w-3.5 h-3.5 text-slate-500" />
    },
    DOCUMENTS_PENDING: {
      label: 'Checklist Pending',
      bg: 'bg-amber-50',
      text: 'text-amber-800',
      border: 'border-amber-300',
      icon: <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
    },
    READY_FOR_SUBMISSION: {
      label: 'Ready for Official Portal',
      bg: 'bg-blue-50',
      text: 'text-blue-800',
      border: 'border-blue-300',
      icon: <FileCheck className="w-3.5 h-3.5 text-blue-600" />
    },
    SUBMITTED: {
      label: 'Redirected to Portal',
      bg: 'bg-indigo-50',
      text: 'text-indigo-800',
      border: 'border-indigo-300',
      icon: <Clock className="w-3.5 h-3.5 text-indigo-600" />
    },
    UNDER_REVIEW: {
      label: 'Assisted Review',
      bg: 'bg-purple-50',
      text: 'text-purple-800',
      border: 'border-purple-300',
      icon: <Clock className="w-3.5 h-3.5 text-purple-600" />
    },
    CORRECTION_REQUIRED: {
      label: 'Action Required',
      bg: 'bg-amber-100',
      text: 'text-amber-900',
      border: 'border-amber-400',
      icon: <AlertCircle className="w-3.5 h-3.5 text-amber-700 font-extrabold animate-pulse" />
    },
    NEEDS_CORRECTION: {
      label: 'Action Required',
      bg: 'bg-amber-100',
      text: 'text-amber-900',
      border: 'border-amber-400',
      icon: <AlertCircle className="w-3.5 h-3.5 text-amber-700 font-extrabold animate-pulse" />
    },
    MORE_INFORMATION_REQUIRED: {
      label: 'Information Required',
      bg: 'bg-amber-100',
      text: 'text-amber-900',
      border: 'border-amber-400',
      icon: <AlertCircle className="w-3.5 h-3.5 text-amber-700 font-extrabold animate-pulse" />
    },
    APPROVED: {
      label: 'Approved',
      bg: 'bg-emerald-50',
      text: 'text-emerald-800',
      border: 'border-emerald-300',
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
    },
    COMPLETED: {
      label: 'Completed / Benefit Disbursed',
      bg: 'bg-emerald-100',
      text: 'text-emerald-900',
      border: 'border-emerald-400',
      icon: <ShieldCheck className="w-3.5 h-3.5 text-emerald-700 font-extrabold" />
    },
    REJECTED: {
      label: 'Rejected',
      bg: 'bg-rose-50',
      text: 'text-rose-800',
      border: 'border-rose-300',
      icon: <XCircle className="w-3.5 h-3.5 text-rose-600" />
    },
    WITHDRAWN: {
      label: 'Withdrawn',
      bg: 'bg-slate-200',
      text: 'text-slate-700',
      border: 'border-slate-400',
      icon: <XCircle className="w-3.5 h-3.5 text-slate-500" />
    },
  };


  const cfg = configs[status] || {
    label: String(status).replace(/_/g, ' '),
    bg: 'bg-slate-100',
    text: 'text-slate-700',
    border: 'border-slate-300',
    icon: <Clock className="w-3.5 h-3.5 text-slate-500" />
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold border ${cfg.bg} ${cfg.text} ${cfg.border}`}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
};
