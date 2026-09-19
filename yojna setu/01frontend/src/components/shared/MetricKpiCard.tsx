import React from 'react';
import { ChevronRight, Info } from 'lucide-react';

export interface MetricKpiCardProps {
  id: string;
  label: string;
  value: string;
  statusBadgeText: string;
  statusBadgeType?: 'positive' | 'moderate' | 'neutral' | 'caution';
  interpretation: string;
  whyItMattersUrl?: string;
  onWhyItMattersClick?: () => void;
  icon: React.FC<{ className?: string }>;
  iconBg: string;
  iconColor: string;
}

export const MetricKpiCard: React.FC<MetricKpiCardProps> = ({
  label,
  value,
  statusBadgeText,
  statusBadgeType = 'positive',
  interpretation,
  onWhyItMattersClick,
  icon: Icon,
  iconBg,
  iconColor,
}) => {
  const badgeClasses = {
    positive: 'bg-emerald-100/80 text-emerald-800 border-emerald-200/80',
    moderate: 'bg-emerald-50 text-emerald-700 border-emerald-200/60',
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
    caution: 'bg-amber-100/80 text-amber-800 border-amber-200/80',
  }[statusBadgeType];

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs hover:shadow-md transition-all duration-150 p-5 flex flex-col justify-between space-y-4">
      <div className="space-y-3">
        {/* Top: Icon + Label */}
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl ${iconBg} ${iconColor} flex items-center justify-center shrink-0`}>
            <Icon className="w-5 h-5" />
          </div>
          <span className="text-xs font-bold text-slate-600 uppercase tracking-wider block">
            {label}
          </span>
        </div>

        {/* Number Value */}
        <div className="text-3xl font-black text-slate-900 tracking-tight font-sans">
          {value}
        </div>

        {/* Status Pill Badge */}
        <div>
          <span
            className={`inline-flex items-center text-[11px] font-extrabold px-3 py-0.5 rounded-full border ${badgeClasses}`}
          >
            {statusBadgeText}
          </span>
        </div>

        {/* What it means / Citizen interpretation */}
        <p className="text-xs text-slate-600 leading-relaxed pt-1">
          {interpretation}
        </p>
      </div>

      {/* Why This Matters Link */}
      <div className="pt-2 border-t border-slate-100">
        <button
          type="button"
          onClick={onWhyItMattersClick}
          className="text-xs font-bold text-sky-700 hover:text-sky-900 flex items-center gap-1.5 transition cursor-pointer"
        >
          <Info className="w-3.5 h-3.5 text-sky-600" />
          <span>Why this matters?</span>
        </button>
      </div>
    </div>
  );
};
