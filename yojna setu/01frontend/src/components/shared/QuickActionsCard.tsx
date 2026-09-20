import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Zap,
  CheckCircle2,
  Calculator,
  MapPin,
  Share2,
  ChevronRight,
} from 'lucide-react';

export interface QuickActionItem {
  id: string;
  label: string;
  link?: string;
  onClick?: () => void;
  variant: 'green' | 'orange' | 'blue' | 'slate';
  icon: React.FC<{ className?: string }>;
}

interface QuickActionsCardProps {
  schemeId?: string;
  partnerId?: string;
  customActions?: QuickActionItem[];
}

export const QuickActionsCard: React.FC<QuickActionsCardProps> = ({
  schemeId,
  partnerId,
  customActions,
}) => {
  const { t } = useTranslation();

  const defaultActions: QuickActionItem[] = [
    {
      id: 'eligibility',
      label: t('shared.checkEligibility'),
      link: schemeId ? `/recommendations?scheme_id=${schemeId}` : '/recommendations',
      variant: 'green',
      icon: CheckCircle2,
    },
    {
      id: 'calculator',
      label: t('shared.calculateLoanSubsidy'),
      link: schemeId ? `/calculator?scheme=${schemeId}` : '/calculator',
      variant: 'orange',
      icon: Calculator,
    },
    {
      id: 'partner',
      label: t('shared.findNearbyPartner'),
      link: schemeId ? `/channel-partners?scheme_id=${schemeId}` : '/channel-partners',
      variant: 'blue',
      icon: MapPin,
    },
    {
      id: 'share',
      label: t('shared.shareInformation'),
      onClick: () => {
        if (navigator.share) {
          navigator.share({
            title: 'YojnaSetu Verified Scheme & Partner Information',
            url: window.location.href,
          }).catch(() => {});
        } else {
          navigator.clipboard.writeText(window.location.href);
          alert(t('shared.linkCopiedToast'));
        }
      },
      variant: 'slate',
      icon: Share2,
    },
  ];

  const actions = customActions || defaultActions;

  const variantStyles = {
    green: 'bg-emerald-50/80 hover:bg-emerald-100/80 text-emerald-800 border-emerald-200/80',
    orange: 'bg-orange-50/80 hover:bg-orange-100/80 text-orange-800 border-orange-200/80',
    blue: 'bg-sky-50/80 hover:bg-sky-100/80 text-sky-800 border-sky-200/80',
    slate: 'bg-slate-50 hover:bg-slate-100 text-slate-800 border-slate-200',
  };

  const iconColors = {
    green: 'text-emerald-600',
    orange: 'text-orange-600',
    blue: 'text-sky-600',
    slate: 'text-slate-500',
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs p-5 space-y-4">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
        <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
          <Zap className="w-4 h-4 fill-amber-500 text-amber-500" />
        </div>
        <h3 className="text-sm font-extrabold text-slate-900 tracking-tight">
          {t('shared.quickActions')}
        </h3>
      </div>

      <div className="space-y-2.5">
        {actions.map((act) => {
          const Icon = act.icon;
          const content = (
            <div
              className={`w-full p-3 rounded-xl border font-bold text-xs flex items-center justify-between transition-all duration-150 group cursor-pointer ${variantStyles[act.variant]}`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <Icon className={`w-4 h-4 shrink-0 ${iconColors[act.variant]}`} />
                <span className="truncate">{act.label}</span>
              </div>
              <ChevronRight className="w-4 h-4 shrink-0 opacity-70 group-hover:translate-x-0.5 group-hover:opacity-100 transition-all" />
            </div>
          );

          if (act.link) {
            return (
              <Link key={act.id} to={act.link} className="block">
                {content}
              </Link>
            );
          }

          return (
            <button
              key={act.id}
              type="button"
              onClick={act.onClick}
              className="w-full text-left"
            >
              {content}
            </button>
          );
        })}
      </div>
    </div>
  );
};
