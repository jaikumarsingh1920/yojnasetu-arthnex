import React from 'react';
import { SystemHealthResponse } from '../../api/adminApi';
import { Activity, Database, Cpu, Sparkles, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

interface Props {
  health: SystemHealthResponse | null;
}

export const SystemHealthCard: React.FC<Props> = ({ health }) => {
  if (!health) return null;

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
      <div className="flex justify-between items-center border-b border-slate-200 pb-3">
        <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
          <Activity className="w-5 h-5 text-emerald-600" />
          System & AI Observability Health
        </h3>
        <span className={`px-3 py-1 rounded-full font-extrabold text-xs flex items-center gap-1.5 border ${
          health.overall_status === 'ONLINE'
            ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
            : 'bg-amber-100 text-amber-800 border-amber-300'
        }`}>
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          SYSTEM STATUS: {health.overall_status}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {health.components.map((c, i) => (
          <div key={i} className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex flex-col justify-between space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-slate-900">{c.name}</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold border ${
                c.status === 'ONLINE'
                  ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                  : c.status === 'DEGRADED'
                  ? 'bg-amber-100 text-amber-800 border-amber-300'
                  : 'bg-rose-100 text-rose-800 border-rose-300'
              }`}>
                {c.status}
              </span>
            </div>
            <p className="text-[11px] text-slate-600 leading-snug">{c.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
