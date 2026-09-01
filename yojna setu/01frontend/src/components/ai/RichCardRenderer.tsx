import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Award, CheckCircle, Calculator, FileCheck, ArrowRight, Info } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { RichCard } from '../../types';
import { formatCurrency } from '../../utils/formatters';

interface Props {
  card: RichCard;
}

export const RichCardRenderer: React.FC<Props> = ({ card }) => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  if (card.card_type === 'SCHEME_CARD') {
    const scheme = card.data;
    return (
      <div className="bg-gradient-to-r from-sky-50 to-indigo-50/50 border border-sky-200 rounded-xl p-3 space-y-2 shadow-xs text-slate-900">
        <div className="flex justify-between items-start">
          <div>
            <span className="text-[9px] font-extrabold text-sky-800 uppercase tracking-wide bg-sky-200/60 px-1.5 py-0.5 rounded">
              {t('recommendations.title', 'Recommended Scheme')}
            </span>
            <h4 className="font-extrabold text-sm text-slate-900 mt-1">{scheme.scheme_name}</h4>
          </div>
          {scheme.score && (
            <span className="text-xs font-black text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full border border-amber-300">
              {Math.round(scheme.score)}% Match
            </span>
          )}
        </div>

        <p className="text-xs text-slate-700 line-clamp-2">{scheme.objective}</p>

        <button
          onClick={() => navigate(`/schemes/${scheme.scheme_id}`)}
          className="w-full bg-sky-700 hover:bg-sky-800 text-white font-bold text-xs py-1.5 px-3 rounded-lg flex items-center justify-center gap-1 shadow-xs transition"
        >
          {t('copilot.viewDetails', 'View Details')} <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    );
  }

  if (card.card_type === 'FINANCIAL_CARD') {
    const fin = card.data;
    return (
      <div className="bg-slate-900 text-white border border-slate-700 rounded-xl p-3 space-y-2 shadow-xs">
        <div className="flex items-center gap-1.5 text-xs font-bold text-sky-400">
          <Calculator className="w-3.5 h-3.5 text-sky-400" />
          <span>{card.title}</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-[10px] pt-1">
          <div className="bg-slate-800/80 p-2 rounded-lg border border-slate-700">
            <span className="text-slate-400 block">{t('calculator.loanAmount', 'Eligible Loan')}</span>
            <span className="font-extrabold text-emerald-400 text-xs">
              {formatCurrency(fin.eligible_loan_amount, 'Rule dependent')}
            </span>
          </div>
          <div className="bg-slate-800/80 p-2 rounded-lg border border-slate-700">
            <span className="text-slate-400 block">{t('schemes.subsidy', 'Govt Subsidy')}</span>
            <span className="font-extrabold text-sky-300 text-xs">
              {formatCurrency(fin.subsidy_amount, 'Not applicable')}
            </span>
          </div>
          <div className="bg-slate-800/80 p-2 rounded-lg border border-slate-700">
            <span className="text-slate-400 block">{t('calculator.interestRate', 'Interest Rate')}</span>
            <span className="font-bold text-amber-300 text-xs">
              {fin.interest_rate !== null && fin.interest_rate !== undefined ? `${fin.interest_rate}% p.a.` : 'Based on category'}
            </span>
          </div>
          <div className="bg-slate-800/80 p-2 rounded-lg border border-slate-700">
            <span className="text-slate-400 block">{t('calculator.monthlyEmi', 'Monthly EMI')}</span>
            <span className="font-extrabold text-indigo-300 text-xs">
              {formatCurrency(fin.periodic_installment, 'Rule dependent')}
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (card.card_type === 'APPLICATION_STATUS_CARD') {
    const app = card.data;
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-3 space-y-2 shadow-xs text-slate-900">
        <div className="flex justify-between items-center">
          <span className="text-xs font-bold text-slate-500">App #{app.application_id}</span>
          <span className="text-[10px] font-extrabold bg-sky-100 text-sky-800 px-2 py-0.5 rounded-full uppercase">
            {app.status}
          </span>
        </div>
        <p className="text-xs font-bold text-slate-800">{app.scheme_name || 'Scheme Application'}</p>
        <button
          onClick={() => navigate(`/applications/${app.application_id}`)}
          className="text-xs font-bold text-sky-700 hover:underline flex items-center gap-1"
        >
          {t('nav.applications', 'Track Application')} <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    );
  }

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-700 space-y-1">
      <div className="font-bold text-slate-900 flex items-center gap-1">
        <Info className="w-3.5 h-3.5 text-sky-600" />
        <span>{card.title}</span>
      </div>
      <p>{card.subtitle}</p>
    </div>
  );
};
