import React from 'react';
import { Link } from 'react-router-dom';
import { Building2, IndianRupee, ShieldCheck, Tag, ArrowRight, Sparkles, CheckCircle2 } from 'lucide-react';
import { Scheme } from '../types';
import { VerificationBadge } from './Badge';

interface SchemeCardProps {
  scheme: Scheme;
}

export const SchemeCard: React.FC<SchemeCardProps> = ({ scheme }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition flex flex-col justify-between overflow-hidden group">
      <div className="p-5">
        {/* Header Badges */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <VerificationBadge status={scheme.verification_status} />
          {scheme.scheme_type && (
            <span className="text-[11px] bg-slate-100 text-slate-700 font-semibold px-2.5 py-0.5 rounded border border-slate-300">
              {scheme.scheme_type}
            </span>
          )}
        </div>

        {/* Scheme Title */}
        <h3 className="text-base font-extrabold text-slate-900 group-hover:text-sky-700 transition line-clamp-2 mb-2">
          {scheme.scheme_name}
        </h3>

        {/* Ministry & Agency */}
        <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-4">
          <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span className="truncate">{scheme.ministry || scheme.implementing_agency || "Government of India"}</span>
        </div>

        {/* Objective */}
        <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed mb-4">
          {scheme.short_description || scheme.objective || scheme.purpose || "Verified government welfare and enterprise support scheme."}
        </p>

        {/* Key Features Pill Grid */}
        <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-3 rounded-lg border border-slate-100 mb-4">
          <div>
            <span className="text-[10px] text-slate-400 font-medium block uppercase">Max Loan</span>
            <span className="font-bold text-slate-800 flex items-center">
              {scheme.max_loan_amount
                ? `₹${(scheme.max_loan_amount / 100000).toFixed(1)} Lakh`
                : scheme.max_loan_amount_raw === 'CONDITIONAL'
                ? 'Depends on slab/category'
                : 'Not specified in available data'}
            </span>
          </div>

          <div>
            <span className="text-[10px] text-slate-400 font-medium block uppercase">Interest Rate</span>
            <span className="font-bold text-slate-800">
              {scheme.interest_rate
                ? `${scheme.interest_rate}% p.a.`
                : scheme.interest_rate_type === 'CONDITIONAL' || scheme.interest_rate_min_raw === 'CONDITIONAL'
                ? 'Depends on slab/category'
                : 'Not specified in available data'}
            </span>
          </div>
        </div>

        {/* Target Group Tags */}
        <div className="flex flex-wrap gap-1.5">
          {(scheme.target_groups || scheme.marginalized_group || scheme.target_beneficiary) && (
            <span className="text-[10px] bg-amber-50 text-amber-800 font-medium px-2 py-0.5 rounded border border-amber-200 truncate max-w-[200px]">
              Target: {scheme.target_groups || scheme.marginalized_group || scheme.target_beneficiary}
            </span>
          )}
          {scheme.sector && (
            <span className="text-[10px] bg-sky-50 text-sky-800 font-medium px-2 py-0.5 rounded border border-sky-200">
              Sector: {scheme.sector}
            </span>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="bg-slate-50 px-5 py-3 border-t border-slate-100 flex items-center justify-between">
        <Link
          to={`/schemes/${scheme.scheme_id}`}
          className="text-xs font-bold text-sky-700 hover:text-sky-900 flex items-center gap-1 group-hover:translate-x-0.5 transition"
        >
          View Details
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>

        <Link
          to={`/calculator?scheme=${scheme.scheme_id}`}
          className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 bg-emerald-50 px-2.5 py-1 rounded border border-emerald-200 transition"
        >
          Calculate EMI
        </Link>
      </div>
    </div>
  );
};
