import React from 'react';
import { Clock, XCircle, ShieldCheck, Check } from 'lucide-react';
import { ApplicationStatus, StatusHistory } from '../types';

interface StatusTimelineProps {
  currentStatus: ApplicationStatus | string;
  history?: StatusHistory[];
  submittedAt?: string | null;
}

const LIFECYCLE_STEPS: { key: string; label: string; description: string }[] = [
  { key: 'DRAFT', label: 'Guidance Started', description: 'Selected scheme & initiated eligibility check' },
  { key: 'DOCUMENTS_PENDING', label: 'Checklist Prepared', description: 'Organized optional document checklist' },
  { key: 'READY_FOR_SUBMISSION', label: 'Ready for Official Portal', description: 'Reviewed requirements & ready to apply' },
  { key: 'SUBMITTED', label: 'Redirected to Portal', description: 'Visited official portal to complete application' },
  { key: 'UNDER_REVIEW', label: 'Assisted Review', description: 'Optional channelizing partner guidance' },
  { key: 'FINAL', label: 'Official Government Application', description: 'Final application submission, verification, and sanctioning are performed on the official government portal.' },
];

export const StatusTimeline: React.FC<StatusTimelineProps> = ({
  currentStatus,
  history = [],
}) => {
  const isRejected = currentStatus === 'REJECTED';
  const isApproved = currentStatus === 'APPROVED';

  const getStepState = (stepKey: string) => {
    if (stepKey === 'FINAL') {
      if (isApproved) return 'completed';
      if (isRejected) return 'rejected';
      return 'upcoming';
    }

    const order = ['DRAFT', 'DOCUMENTS_PENDING', 'READY_FOR_SUBMISSION', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED'];
    const currentIndex = order.indexOf(currentStatus);
    const stepIndex = order.indexOf(stepKey);

    if (isRejected && stepIndex < order.indexOf('UNDER_REVIEW')) return 'completed';
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'current';
    return 'upcoming';
  };

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
      <div className="border-b border-slate-200 pb-3">
        <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-sky-600" />
          What Happens Next?
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">Application progress timeline and review status</p>
      </div>

      <div className="relative border-l-2 border-slate-200 ml-4 space-y-8 pl-6">
        {LIFECYCLE_STEPS.map((step) => {
          const state = getStepState(step.key);

          // Find audit history log for this step
          const historyEntry = history.find(
            (h) => h.new_status === step.key || (step.key === 'FINAL' && (h.new_status === 'APPROVED' || h.new_status === 'REJECTED'))
          );

          return (
            <div key={step.key} className="relative group">
              {/* Bullet icon */}
              <div
                className={`absolute -left-[31px] top-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition ${
                  state === 'completed'
                    ? 'bg-emerald-600 text-white'
                    : state === 'current'
                    ? 'bg-sky-600 text-white ring-4 ring-sky-100 animate-pulse'
                    : state === 'rejected'
                    ? 'bg-rose-600 text-white ring-4 ring-rose-100'
                    : 'bg-slate-200 text-slate-500'
                }`}
              >
                {state === 'completed' ? (
                  <Check className="w-3.5 h-3.5" />
                ) : state === 'rejected' ? (
                  <XCircle className="w-3.5 h-3.5" />
                ) : (
                  <Clock className="w-3.5 h-3.5" />
                )}
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <h4 className={`text-sm font-bold ${
                    state === 'current' ? 'text-sky-700 font-extrabold' : state === 'rejected' ? 'text-rose-700' : 'text-slate-800'
                  }`}>
                    {step.key === 'FINAL' ? (isRejected ? 'Application Rejected' : isApproved ? 'Application Approved' : 'Final Decision Pending') : step.label}
                  </h4>

                  {state === 'current' && (
                    <span className="text-[10px] bg-sky-100 text-sky-800 px-2 py-0.5 rounded font-bold uppercase">Active Stage</span>
                  )}
                </div>

                <p className="text-xs text-slate-500 mt-0.5">{step.description}</p>

                {historyEntry && (
                  <div className="mt-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs text-slate-600">
                    <div className="flex justify-between items-center text-[11px] text-slate-500 mb-1">
                      <span>Updated: {new Date(historyEntry.created_at).toLocaleDateString()}</span>
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
