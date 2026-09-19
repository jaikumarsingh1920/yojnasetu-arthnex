import React from 'react';
import { Info, ExternalLink, CheckCircle2, FileText, ShieldCheck } from 'lucide-react';

interface AboutInformationCardProps {
  sourceName?: string;
  sourceUrl?: string;
  latestUpdated?: string;
  dataLevel?: string;
  verificationStatus?: string;
  dataEngine?: string;
  sourceDocumentUrl?: string;
}

export const AboutInformationCard: React.FC<AboutInformationCardProps> = ({
  sourceName = 'Reserve Bank of India (RBI)',
  sourceUrl = 'https://rbi.org.in',
  latestUpdated = '31 March 2025',
  dataLevel = 'Institution-level',
  verificationStatus = 'Verified',
  dataEngine = 'YS-FIS-V1 (Deterministic)',
  sourceDocumentUrl,
}) => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs p-5 space-y-4">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
        <div className="w-7 h-7 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
          <Info className="w-4 h-4 text-sky-600" />
        </div>
        <h3 className="text-sm font-extrabold text-slate-900 tracking-tight">
          About This Information
        </h3>
      </div>

      <div className="space-y-3 text-xs">
        {/* Source */}
        <div className="flex items-center justify-between gap-2">
          <span className="text-slate-500 font-medium">Information Source</span>
          {sourceUrl ? (
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="font-bold text-sky-700 hover:text-sky-900 flex items-center gap-1 truncate max-w-[170px]"
            >
              <span className="truncate">{sourceName}</span>
              <ExternalLink className="w-3 h-3 shrink-0" />
            </a>
          ) : (
            <span className="font-bold text-slate-800">{sourceName}</span>
          )}
        </div>

        {/* Latest Updated */}
        <div className="flex items-center justify-between gap-2">
          <span className="text-slate-500 font-medium">Latest Updated</span>
          <span className="font-bold text-slate-800">{latestUpdated}</span>
        </div>

        {/* Data Level */}
        <div className="flex items-center justify-between gap-2">
          <span className="text-slate-500 font-medium">Financial Data Level</span>
          <span className="font-bold text-slate-800">{dataLevel}</span>
        </div>

        {/* Verification Status */}
        <div className="flex items-center justify-between gap-2">
          <span className="text-slate-500 font-medium">Verification Status</span>
          <span className="inline-flex items-center gap-1 font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full text-[11px]">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            {verificationStatus}
          </span>
        </div>

        {/* Data Engine */}
        <div className="flex items-center justify-between gap-2">
          <span className="text-slate-500 font-medium">Data Engine</span>
          <span className="font-mono text-[11px] font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
            {dataEngine}
          </span>
        </div>
      </div>

      {/* View Source Document Button */}
      {(sourceDocumentUrl || sourceUrl) && (
        <div className="pt-2 border-t border-slate-100">
          <a
            href={sourceDocumentUrl || sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full py-2.5 px-3 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 hover:text-slate-900 font-bold text-xs flex items-center justify-center gap-2 transition"
          >
            <FileText className="w-3.5 h-3.5 text-slate-500" />
            <span>View Source Document</span>
            <ExternalLink className="w-3 h-3 text-slate-400" />
          </a>
        </div>
      )}
    </div>
  );
};
