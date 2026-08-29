import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export const Unauthorized: React.FC = () => {
  return (
    <div className="max-w-md mx-auto my-20 px-4 text-center space-y-4">
      <div className="w-16 h-16 bg-rose-100 text-rose-700 rounded-full mx-auto flex items-center justify-center">
        <ShieldAlert className="w-8 h-8" />
      </div>
      <h1 className="text-2xl font-extrabold text-slate-900">403 — Unauthorized Access</h1>
      <p className="text-xs text-slate-600 leading-relaxed">
        Your current user role does not have authorization to access this partner or administrator workspace route.
      </p>
      <div className="pt-2">
        <Link to="/login" className="bg-gov-navy text-white text-xs font-bold px-5 py-2.5 rounded-lg shadow inline-flex items-center gap-1.5">
          <ArrowLeft className="w-4 h-4" /> Sign In with Authorized Account
        </Link>
      </div>
    </div>
  );
};
