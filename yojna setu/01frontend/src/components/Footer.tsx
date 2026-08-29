import React from 'react';
import { ShieldCheck, PhoneCall, Mail, MapPin } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-gov-blue text-slate-300 border-t-4 border-gov-saffron mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <div className="flex items-center gap-2 mb-3">
            <img
              src="/logo.png"
              alt="YojnaSetu Logo"
              className="w-9 h-9 rounded-lg object-contain bg-slate-950 p-0.5 border border-slate-700 shadow"
            />
            <span className="font-extrabold text-xl text-white">YojnaSetu</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed mb-4">
            Authoritative National Scheme Discovery & Deterministic Financing Platform for Indian Beneficiaries, MSMEs, and Channelizing Agencies.
          </p>
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-medium">
            <ShieldCheck className="w-4 h-4" />
            100% Verified Scheme Database
          </div>
        </div>

        <div>
          <h4 className="text-white text-sm font-bold uppercase tracking-wider mb-3">Quick Services</h4>
          <ul className="space-y-2 text-xs">
            <li><a href="/schemes" className="hover:text-white transition">Discover Government Schemes</a></li>
            <li><a href="/recommendations" className="hover:text-white transition">AI Scheme Recommendation</a></li>
            <li><a href="/calculator" className="hover:text-white transition">Financial EMI & Subsidy Calculator</a></li>
            <li><a href="/dashboard" className="hover:text-white transition">Beneficiary Portal</a></li>
            <li><a href="/partner" className="hover:text-white transition">Partner Channelizing Portal</a></li>
          </ul>
        </div>

        <div>
          <h4 className="text-white text-sm font-bold uppercase tracking-wider mb-3">Support & Helpline</h4>
          <ul className="space-y-2.5 text-xs text-slate-400">
            <li className="flex items-center gap-2">
              <PhoneCall className="w-4 h-4 text-gov-saffron" />
              1800-11-2026 (Toll-Free, 9 AM - 6 PM IST)
            </li>
            <li className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-sky-400" />
              support@yojnasetu.gov.in
            </li>
            <li className="flex items-start gap-2">
              <MapPin className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              Ministry of Social Justice & Empowerment, New Delhi, India
            </li>
          </ul>
        </div>

        <div>
          <h4 className="text-white text-sm font-bold uppercase tracking-wider mb-3">Governance & Trust</h4>
          <p className="text-xs text-slate-400 leading-relaxed mb-3">
            Designed to eliminate financial misrepresentation and opaque approvals in welfare distribution.
          </p>
          <div className="bg-slate-900/80 p-3 rounded border border-slate-800 text-[11px] text-slate-400">
            <p className="font-semibold text-slate-200">Deterministic Engine Policy:</p>
            No LLMs or AI models are used for hard eligibility decisions. Rules are strictly code & database authoritative.
          </div>
        </div>
      </div>

      <div className="bg-slate-950 px-4 py-4 text-center text-xs text-slate-500 border-t border-slate-800">
        <p>© 2026 YojnaSetu Civic-Tech Portal. All rights reserved. Content authoritative from 56 verified schemes.</p>
      </div>
    </footer>
  );
};
