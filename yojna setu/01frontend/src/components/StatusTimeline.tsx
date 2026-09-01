import React from 'react';
import { useTranslation } from 'react-i18next';
import { Clock, XCircle, ShieldCheck, Check, AlertCircle, Sparkles, FileText } from 'lucide-react';
import { ApplicationStatus, StatusHistory } from '../types';

interface StatusTimelineProps {
  currentStatus: ApplicationStatus | string;
  history?: StatusHistory[];
  submittedAt?: string | null;
}

const STAGE_ORDER = [
  'DRAFT',
  'DOCUMENTS_PENDING',
  'READY_FOR_SUBMISSION',
  'SUBMITTED',
  'UNDER_REVIEW',
  'CORRECTION_REQUIRED',
  'DECISION',
  'COMPLETED'
];

export const StatusTimeline: React.FC<StatusTimelineProps> = ({
  currentStatus,
  history = [],
}) => {
  const { t } = useTranslation();
  const normStatus = (currentStatus || '').toUpperCase();
  const isWithdrawn = normStatus === 'WITHDRAWN';
  const isRejected = normStatus === 'REJECTED';
  const isApproved = normStatus === 'APPROVED' || normStatus === 'COMPLETED';
  const isCompleted = normStatus === 'COMPLETED';
  const isActionRequired = normStatus === 'CORRECTION_REQUIRED' || normStatus === 'NEEDS_CORRECTION' || normStatus === 'MORE_INFORMATION_REQUIRED';

  const LIFECYCLE_STEPS = [
    {
      key: 'PREPARATION',
      label: t('timeline.preparationLabel', 'Application Initiated'),
      description: t('timeline.preparationDesc', 'Scheme selected & profile snapshot saved'),
      matchedStatuses: ['DRAFT', 'DOCUMENTS_PENDING'],
    },
    {
      key: 'CHECKLIST_READY',
      label: t('timeline.checklistReadyLabel', 'Checklist & Readiness Confirmed'),
      description: t('timeline.checklistReadyDesc', 'Document requirements reviewed & ready for submission'),
      matchedStatuses: ['READY_FOR_SUBMISSION'],
    },
    {
      key: 'SUBMITTED',
      label: t('timeline.submittedLabel', 'Submitted to Channel Partner'),
      description: t('timeline.submittedDesc', 'Application routed to official processing partner'),
      matchedStatuses: ['SUBMITTED'],
    },
    {
      key: 'UNDER_REVIEW',
      label: t('timeline.underReviewLabel', 'Under Official Review'),
      description: t('timeline.underReviewDesc', 'Processing officer reviewing eligibility & credentials'),
      matchedStatuses: ['UNDER_REVIEW'],
    },
    ...(isActionRequired ? [{
      key: 'ACTION_REQUIRED',
      label: t('timeline.actionRequiredLabel', 'Action / Information Required'),
      description: t('timeline.actionRequiredDesc', 'Reviewer requested correction or additional document checklist update'),
      matchedStatuses: ['CORRECTION_REQUIRED', 'NEEDS_CORRECTION', 'MORE_INFORMATION_REQUIRED'],
    }] : []),
    {
      key: 'DECISION',
      label: isRejected ? t('timeline.decisionRejected', 'Application Rejected') : isApproved ? t('timeline.decisionApproved', 'Application Approved') : t('timeline.decisionPending', 'Final Processing Decision'),
      description: isRejected
        ? t('timeline.decisionRejectedDesc', 'Application did not meet specified official criteria')
        : isApproved
        ? t('timeline.decisionApprovedDesc', 'Application officially approved by processing authority')
        : t('timeline.decisionPendingDesc', 'Awaiting final decision from channel partner'),
      matchedStatuses: ['APPROVED', 'REJECTED', 'COMPLETED'],
    },
    {
      key: 'COMPLETED',
      label: t('timeline.completedLabel', 'Completed / Benefit Disbursed'),
      description: t('timeline.completedDesc', 'Scheme benefit disbursed or official process finished'),
      matchedStatuses: ['COMPLETED'],
    },
  ];

  const getStepState = (stepKey: string, stepStatuses: string[]) => {
    if (isWithdrawn) return 'withdrawn';

    if (stepStatuses.includes(normStatus)) return 'current';

    if (stepKey === 'PREPARATION') {
      return 'completed';
    }
    if (stepKey === 'CHECKLIST_READY') {
      return ['SUBMITTED', 'UNDER_REVIEW', 'CORRECTION_REQUIRED', 'APPROVED', 'REJECTED', 'COMPLETED'].includes(normStatus) ? 'completed' : 'upcoming';
    }
    if (stepKey === 'SUBMITTED') {
      return ['UNDER_REVIEW', 'CORRECTION_REQUIRED', 'APPROVED', 'REJECTED', 'COMPLETED'].includes(normStatus) ? 'completed' : 'upcoming';
    }
    if (stepKey === 'UNDER_REVIEW') {
      return ['APPROVED', 'REJECTED', 'COMPLETED'].includes(normStatus) ? 'completed' : 'upcoming';
    }
    if (stepKey === 'ACTION_REQUIRED') {
      return isActionRequired ? 'current' : 'upcoming';
    }
    if (stepKey === 'DECISION') {
      if (isRejected) return 'rejected';
      if (isApproved) return 'completed';
      return 'upcoming';
    }
    if (stepKey === 'COMPLETED') {
      return isCompleted ? 'completed' : 'upcoming';
    }

    return 'upcoming';
  };

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
      <div className="border-b border-slate-200 pb-3 flex justify-between items-center">
        <div>
          <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-sky-600" />
            {t('timeline.title', 'Application Lifecycle & History')}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">{t('timeline.subtitle', 'Real-time status progression and traceable audit history')}</p>
        </div>
      </div>

      {isWithdrawn && (
        <div className="bg-slate-100 border border-slate-300 p-3 rounded-xl text-xs text-slate-700 font-medium flex items-center gap-2">
          <XCircle className="w-4 h-4 text-slate-500" />
          <span>{t('timeline.withdrawnNotice', 'This application was withdrawn by the beneficiary.')}</span>
        </div>
      )}

      <div className="relative border-l-2 border-slate-200 ml-4 space-y-8 pl-6">
        {LIFECYCLE_STEPS.map((step) => {
          const state = getStepState(step.key, step.matchedStatuses);

          // Find audit history entry for this step
          const historyEntry = history.find((h) =>
            step.matchedStatuses.includes((h.new_status || '').toUpperCase())
          );

          return (
            <div key={step.key} className="relative group">
              {/* Timeline Bullet Icon */}
              <div
                className={`absolute -left-[31px] top-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition ${
                  state === 'completed'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : state === 'current'
                    ? step.key === 'ACTION_REQUIRED'
                      ? 'bg-amber-500 text-white ring-4 ring-amber-100 animate-pulse'
                      : 'bg-sky-600 text-white ring-4 ring-sky-100 animate-pulse'
                    : state === 'rejected'
                    ? 'bg-rose-600 text-white ring-4 ring-rose-100'
                    : state === 'withdrawn'
                    ? 'bg-slate-400 text-white'
                    : 'bg-slate-200 text-slate-500'
                }`}
              >
                {state === 'completed' ? (
                  <Check className="w-3.5 h-3.5" />
                ) : state === 'rejected' ? (
                  <XCircle className="w-3.5 h-3.5" />
                ) : step.key === 'ACTION_REQUIRED' ? (
                  <AlertCircle className="w-3.5 h-3.5" />
                ) : (
                  <Clock className="w-3.5 h-3.5" />
                )}
              </div>

              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h4 className={`text-sm font-bold ${
                    state === 'current'
                      ? step.key === 'ACTION_REQUIRED' ? 'text-amber-800 font-extrabold' : 'text-sky-700 font-extrabold'
                      : state === 'rejected'
                      ? 'text-rose-700'
                      : state === 'completed'
                      ? 'text-slate-900'
                      : 'text-slate-500'
                  }`}>
                    {step.label}
                  </h4>

                  {state === 'current' && (
                    <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                      step.key === 'ACTION_REQUIRED'
                        ? 'bg-amber-100 text-amber-900 border border-amber-300'
                        : 'bg-sky-100 text-sky-800'
                    }`}>
                      {t('timeline.currentStage', 'Current Stage')}
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-500 mt-0.5">{step.description}</p>

                {historyEntry && (
                  <div className="mt-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs text-slate-600">
                    <div className="flex justify-between items-center text-[11px] text-slate-500 mb-1">
                      <span className="font-semibold text-slate-700">{t('timeline.updated', 'Updated')}: {new Date(historyEntry.created_at).toLocaleString()}</span>
                    </div>
                    {historyEntry.reason && <p className="italic text-slate-700">"{historyEntry.reason}"</p>}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

