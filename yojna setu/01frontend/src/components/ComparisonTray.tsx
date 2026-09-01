import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useComparison } from '../context/ComparisonContext';
import { Scale, X, ArrowRight, Trash2, AlertCircle } from 'lucide-react';

export const ComparisonTray: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { selectedSchemeIds, removeSchemeFromCompare, clearComparison, warningMessage } = useComparison();

  if (selectedSchemeIds.length === 0) {
    return null;
  }

  const handleCompareNow = () => {
    if (selectedSchemeIds.length >= 2) {
      navigate(`/compare?schemes=${selectedSchemeIds.join(',')}`);
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-3 sm:p-4 bg-slate-900/95 backdrop-blur-md text-white border-t border-slate-700 shadow-2xl transition-all animate-in slide-in-from-bottom duration-300">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Left: Info & Chips */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2 bg-gov-blue/40 px-3 py-1.5 rounded-lg border border-gov-blue/50 text-xs font-bold">
            <Scale className="w-4 h-4 text-emerald-400" />
            <span>{t('compare.trayTitle', 'Compare Schemes')} ({selectedSchemeIds.length}/4)</span>
          </div>

          <div className="flex flex-wrap items-center gap-2 overflow-x-auto max-w-full">
            {selectedSchemeIds.map((id) => (
              <span
                key={id}
                className="inline-flex items-center gap-1.5 bg-slate-800 border border-slate-700 text-slate-200 text-[11px] font-mono font-medium px-2.5 py-1 rounded-md"
              >
                <span>{id}</span>
                <button
                  type="button"
                  onClick={() => removeSchemeFromCompare(id)}
                  className="hover:text-red-400 p-0.5 rounded transition"
                  title={t('compare.remove', 'Remove')}
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* Right: Messages & Actions */}
        <div className="flex flex-wrap items-center justify-end gap-3 w-full md:w-auto">
          {warningMessage && (
            <div className="flex items-center gap-1.5 text-amber-300 text-xs bg-amber-950/60 border border-amber-500/40 px-3 py-1.5 rounded-lg animate-pulse">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>{warningMessage}</span>
            </div>
          )}

          {selectedSchemeIds.length === 1 && !warningMessage && (
            <span className="text-slate-400 text-xs italic">
              {t('compare.selectOneMore', 'Select at least one more scheme to compare.')}
            </span>
          )}

          <button
            type="button"
            onClick={clearComparison}
            className="flex items-center gap-1.5 text-slate-400 hover:text-slate-200 text-xs font-semibold px-3 py-2.5 rounded-xl transition min-h-[44px]"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{t('compare.clearAll', 'Clear All')}</span>
          </button>

          <button
            type="button"
            disabled={selectedSchemeIds.length < 2}
            onClick={handleCompareNow}
            className="flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px]"
          >
            <span>{t('compare.compareNow', 'Compare Now')}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
