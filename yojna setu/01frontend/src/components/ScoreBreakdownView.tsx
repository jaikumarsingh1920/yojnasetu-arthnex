import React from 'react';
import { CheckCircle2, AlertCircle, HelpCircle, XCircle } from 'lucide-react';
import { ScoreDimensionBreakdown } from '../types';

interface ScoreBreakdownViewProps {
  scoreBreakdown: ScoreDimensionBreakdown[];
  matchedFactors: string[];
  unmatchedFactors: string[];
  notEvaluatedFactors: string[];
}

export const ScoreBreakdownView: React.FC<ScoreBreakdownViewProps> = ({
  scoreBreakdown,
  matchedFactors,
  unmatchedFactors,
  notEvaluatedFactors,
}) => {
  const getResultBadge = (res: string) => {
    switch (res) {
      case 'MATCH':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            ✓ Strong Match
          </span>
        );
      case 'PARTIAL_MATCH':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
            <AlertCircle className="w-3 h-3 text-amber-600" />
            ◐ Related Match
          </span>
        );
      case 'NO_MATCH':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
            <XCircle className="w-3 h-3 text-rose-600" />
            ✕ Not a match
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            <HelpCircle className="w-3 h-3 text-slate-400" />
            — Not enough information
          </span>
        );
    }
  };

  const sanitizeReason = (reason: string) => {
    if (!reason) return 'Not enough information to compare';
    return reason
      .replace(/UNKNOWN/g, 'not specified / requires verification')
      .replace(/NOT_APPLICABLE/g, 'varies by candidate');
  };

  return (
    <div className="space-y-6">
      {/* Dimension Scores */}
      <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-4">
          Scheme Criteria Match Breakdown
        </h4>

        <div className="space-y-3">
          {scoreBreakdown.map((item, idx) => (
            <div key={idx} className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
              <div className="flex justify-between items-center mb-1.5">
                <span className="text-xs font-bold text-slate-800 capitalize">
                  {item.dimension.replace(/_/g, ' ')}
                </span>
                <div className="flex items-center gap-2">
                  {getResultBadge(item.result)}
                  <span className="text-xs font-mono font-extrabold text-slate-900">
                    {item.score} / {item.max_weight} pts
                  </span>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden mb-1">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    item.result === 'MATCH'
                      ? 'bg-emerald-500'
                      : item.result === 'PARTIAL_MATCH'
                      ? 'bg-amber-500'
                      : item.result === 'NO_MATCH'
                      ? 'bg-rose-500'
                      : 'bg-slate-300'
                  }`}
                  style={{ width: `${(item.score / item.max_weight) * 100}%` }}
                />
              </div>

              <p className="text-[11px] text-slate-500">{sanitizeReason(item.reason)}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Factor Lists */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        {/* Matched */}
        <div className="bg-emerald-50/60 p-3.5 rounded-lg border border-emerald-200">
          <h5 className="font-bold text-emerald-900 flex items-center gap-1.5 mb-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            Matched Dimensions ({matchedFactors.length})
          </h5>
          {matchedFactors.length === 0 ? (
            <p className="text-[11px] text-emerald-700/70 italic">None</p>
          ) : (
            <ul className="space-y-1 text-[11px] text-emerald-800 list-disc list-inside">
              {matchedFactors.map((f, i) => (
                <li key={i} className="capitalize">{f.replace(/_/g, ' ')}</li>
              ))}
            </ul>
          )}
        </div>

        {/* Unmatched */}
        <div className="bg-rose-50/60 p-3.5 rounded-lg border border-rose-200">
          <h5 className="font-bold text-rose-900 flex items-center gap-1.5 mb-2">
            <XCircle className="w-4 h-4 text-rose-600" />
            Unmatched Dimensions ({unmatchedFactors.length})
          </h5>
          {unmatchedFactors.length === 0 ? (
            <p className="text-[11px] text-rose-700/70 italic">None</p>
          ) : (
            <ul className="space-y-1 text-[11px] text-rose-800 list-disc list-inside">
              {unmatchedFactors.map((f, i) => (
                <li key={i} className="capitalize">{f.replace(/_/g, ' ')}</li>
              ))}
            </ul>
          )}
        </div>

        {/* Not Evaluated */}
        <div className="bg-slate-100/70 p-3.5 rounded-lg border border-slate-200">
          <h5 className="font-bold text-slate-800 flex items-center gap-1.5 mb-2">
            <HelpCircle className="w-4 h-4 text-slate-500" />
            Unspecified Dimensions ({notEvaluatedFactors.length})
          </h5>
          {notEvaluatedFactors.length === 0 ? (
            <p className="text-[11px] text-slate-600 italic">None</p>
          ) : (
            <ul className="space-y-1 text-[11px] text-slate-700 list-disc list-inside">
              {notEvaluatedFactors.map((f, i) => (
                <li key={i} className="capitalize">{f.replace(/_/g, ' ')}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};
