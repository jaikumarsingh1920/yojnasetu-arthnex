import React from 'react';
import { useTranslation } from 'react-i18next';
import { useComparison } from '../context/ComparisonContext';
import { Scale, Check } from 'lucide-react';

interface CompareButtonProps {
  schemeId: string;
  variant?: 'button' | 'compact' | 'icon' | 'badge';
  className?: string;
}

export const CompareButton: React.FC<CompareButtonProps> = ({
  schemeId,
  variant = 'button',
  className = '',
}) => {
  const { t } = useTranslation();
  const { isInComparison, toggleComparison } = useComparison();
  const selected = isInComparison(schemeId);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    toggleComparison(schemeId);
  };

  if (variant === 'compact') {
    return (
      <button
        type="button"
        onClick={handleClick}
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold transition ${
          selected
            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold'
            : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300'
        } ${className}`}
        title={selected ? t('compare.inComparison', 'In Comparison') : t('compare.addToCompare', 'Add to Compare')}
      >
        {selected ? (
          <>
            <Check className="w-3.5 h-3.5 text-emerald-600" />
            <span>{t('compare.comparing', 'Comparing')}</span>
          </>
        ) : (
          <>
            <Scale className="w-3.5 h-3.5 text-slate-500" />
            <span>{t('compare.compare', 'Compare')}</span>
          </>
        )}
      </button>
    );
  }

  if (variant === 'icon') {
    return (
      <button
        type="button"
        onClick={handleClick}
        className={`p-2 rounded-lg transition border ${
          selected
            ? 'bg-emerald-500 text-white border-emerald-600'
            : 'bg-white hover:bg-slate-100 text-slate-600 border-slate-300'
        } ${className}`}
        title={selected ? t('compare.inComparison', 'In Comparison') : t('compare.addToCompare', 'Add to Compare')}
      >
        <Scale className="w-4 h-4" />
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition shadow-sm ${
        selected
          ? 'bg-emerald-600 text-white hover:bg-emerald-700 border border-emerald-700'
          : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-300'
      } ${className}`}
    >
      {selected ? (
        <>
          <Check className="w-4 h-4 text-white" />
          <span>{t('compare.addedToCompare', 'Added to Compare')}</span>
        </>
      ) : (
        <>
          <Scale className="w-4 h-4 text-gov-blue" />
          <span>{t('compare.addToCompare', 'Add to Compare')}</span>
        </>
      )}
    </button>
  );
};
