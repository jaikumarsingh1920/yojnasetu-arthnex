import React from 'react';
import { FinancialIndicatorStatus } from '../api/partnerApi';
import { CheckCircle2, AlertTriangle, AlertCircle, HelpCircle } from 'lucide-react';

export interface FinancialStatusBadgeProps {
  status?: FinancialIndicatorStatus | null;
  size?: 'sm' | 'md' | 'lg';
  showDescription?: boolean;
  className?: string;
}

export const FinancialStatusBadge: React.FC<FinancialStatusBadgeProps> = ({
  status,
  size = 'md',
  showDescription = false,
  className = '',
}) => {
  const code = status?.code || 'LIMITED_DATA';

  const defaultLabels: Record<string, string> = {
    STRONGER: 'Financial position looks stronger',
    MIXED: 'Financial position is mixed',
    HIGHER_STRESS: 'Financial position needs attention',
    LIMITED_DATA: 'Not enough information',
  };

  const defaultDescriptions: Record<string, string> = {
    STRONGER: 'Reported loan problems are lower and capital is in a stronger range.',
    MIXED: 'Some reported financial numbers need attention.',
    HIGHER_STRESS: 'One or more reported financial numbers need attention.',
    LIMITED_DATA: 'Not enough verified financial information is available.',
  };

  const label = status?.label || defaultLabels[code] || defaultLabels.LIMITED_DATA;
  const description = status?.short_description || defaultDescriptions[code] || defaultDescriptions.LIMITED_DATA;

  const config = {
    STRONGER: {
      dotColor: 'bg-emerald-500',
      badgeBg: 'bg-emerald-50 border-emerald-300 text-emerald-900',
      icon: CheckCircle2,
      iconColor: 'text-emerald-600',
      accessibleAria: 'Financial position looks stronger: Reported loan problems are lower and capital is in a stronger range',
    },
    MIXED: {
      dotColor: 'bg-amber-500',
      badgeBg: 'bg-amber-50 border-amber-300 text-amber-900',
      icon: AlertTriangle,
      iconColor: 'text-amber-600',
      accessibleAria: 'Financial position is mixed: Some reported financial numbers need attention',
    },
    HIGHER_STRESS: {
      dotColor: 'bg-rose-500',
      badgeBg: 'bg-rose-50 border-rose-300 text-rose-900',
      icon: AlertCircle,
      iconColor: 'text-rose-600',
      accessibleAria: 'Financial position needs attention: One or more reported financial numbers need attention',
    },
    LIMITED_DATA: {
      dotColor: 'bg-slate-400',
      badgeBg: 'bg-slate-100 border-slate-300 text-slate-800',
      icon: HelpCircle,
      iconColor: 'text-slate-500',
      accessibleAria: 'Not enough information: Not enough verified financial information is available',
    },
  }[code] || {
    dotColor: 'bg-slate-400',
    badgeBg: 'bg-slate-100 border-slate-300 text-slate-800',
    icon: HelpCircle,
    iconColor: 'text-slate-500',
    accessibleAria: 'Not enough information',
  };

  const Icon = config.icon;

  const sizeClasses = {
    sm: {
      badge: 'px-2.5 py-1 text-xs gap-1.5',
      icon: 'w-3.5 h-3.5',
      dot: 'w-2 h-2',
      text: 'text-xs font-bold',
    },
    md: {
      badge: 'px-3.5 py-1.5 text-sm gap-2',
      icon: 'w-4 h-4',
      dot: 'w-2.5 h-2.5',
      text: 'text-sm font-extrabold',
    },
    lg: {
      badge: 'px-4 py-2 text-base gap-2.5',
      icon: 'w-5 h-5',
      dot: 'w-3 h-3',
      text: 'text-base font-black',
    },
  }[size];

  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <div
        role="status"
        aria-label={config.accessibleAria}
        className={`inline-flex items-center rounded-full border shadow-xs transition-colors ${config.badgeBg} ${sizeClasses.badge} w-fit`}
      >
        <span className={`rounded-full shrink-0 ${config.dotColor} ${sizeClasses.dot}`} aria-hidden="true" />
        <Icon className={`shrink-0 ${config.iconColor} ${sizeClasses.icon}`} aria-hidden="true" />
        <span className={`${sizeClasses.text} tracking-tight`}>{label}</span>
      </div>

      {showDescription && (
        <p className="text-xs text-slate-600 leading-relaxed font-medium pl-1">
          {description}
        </p>
      )}
    </div>
  );
};
