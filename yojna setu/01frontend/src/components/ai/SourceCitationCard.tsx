import React from 'react';
import { FileText, CheckCircle, ArrowRight } from 'lucide-react';
import { SourceCitation } from '../../types';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

interface Props {
  citation: SourceCitation;
}

const sanitizeClientSnippet = (text?: string): string => {
  if (!text) return '';
  let clean = text;
  clean = clean.replace(/Rule\s+Code:\s*\w+[-_]?\d*/gi, '');
  clean = clean.replace(/\bRULE[-_]?\d+\b/gi, '');
  clean = clean.replace(/Field:\s*[\w_]+(?:\s*(?:IN|==|!=|>|<|>=|<=)\s*[^;\.\n]+)*(?:;|\.|\n|$)/gi, '');
  clean = clean.replace(/Requirement\s+Field:\s*\w+/gi, '');
  clean = clean.replace(/Requirement\s+Value:\s*[^;\.\n]+/gi, '');
  clean = clean.replace(/\b(?:PM_SURAJ|AUTHORISED_SCA|AUTHORISED_CA)\b/gi, 'Authorized Partner Portal');
  clean = clean.replace(/\bTRADITIONAL_TRADE_\d+\b/gi, 'Traditional Artisanship & Trade');
  clean = clean.replace(/\bSMALL_MICRO_BUSINESS\b/gi, 'Small & Micro Enterprise');
  clean = clean.replace(/\bAPPLICATION_ROUTE\b/gi, 'Application Route');
  clean = clean.replace(/\bapplication_route\b/gi, 'application route');
  clean = clean.replace(/\bDescription:\s*/gi, '');
  clean = clean.replace(/\s{2,}/g, ' ').trim();
  return clean;
};

export const SourceCitationCard: React.FC<Props> = ({ citation }) => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const handleClick = () => {
    if (citation.scheme_id) {
      navigate(`/schemes/${citation.scheme_id}`);
    }
  };

  const safeSnippet = sanitizeClientSnippet(citation.snippet);

  return (
    <div
      onClick={handleClick}
      className="bg-slate-50 hover:bg-sky-50/70 p-2.5 rounded-xl border border-slate-200 hover:border-sky-300 transition cursor-pointer space-y-1 text-slate-800"
    >
      <div className="flex justify-between items-center text-[10px] font-bold text-sky-700">
        <span className="flex items-center gap-1">
          <FileText className="w-3 h-3 text-sky-500" />
          {t('copilot.verifiedInformation', 'Verified Information')}
        </span>
        <span className="flex items-center gap-0.5 text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
          <CheckCircle className="w-2.5 h-2.5" /> {t('copilot.officialSource', 'Official Source')}
        </span>
      </div>

      <p className="text-[11px] font-bold text-slate-900 line-clamp-1">
        {citation.scheme_name || citation.scheme_id}
      </p>

      {safeSnippet && (
        <p className="text-[10px] text-slate-600 line-clamp-2 leading-tight">
          "{safeSnippet}"
        </p>
      )}

      <div className="pt-0.5 text-[10px] font-bold text-sky-700 flex items-center gap-1">
        {t('copilot.viewDetails', 'View Scheme Details')} <ArrowRight className="w-2.5 h-2.5" />
      </div>
    </div>
  );
};
