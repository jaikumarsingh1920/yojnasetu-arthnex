import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export const Unauthorized: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4 py-12 bg-[#FFFBF0]">
      <div className="max-w-md w-full bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-md p-8 text-center space-y-4">
        <div className="w-16 h-16 bg-[#FFF4EC] text-[#EA717B] border border-[#FFD0CA] rounded-full mx-auto flex items-center justify-center">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-extrabold text-[#3B2522]">403 — {t('errors.unauthorized')}</h1>
        <p className="text-xs text-[#765E59] leading-relaxed">
          {t('errors.unauthorizedDesc')}
        </p>
        <div className="pt-2">
          <Link to="/login" className="bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold px-6 py-2.5 rounded-xl shadow-warm-xs inline-flex items-center gap-2 transition">
            <ArrowLeft className="w-4 h-4" /> {t('auth.signInBtn')}
          </Link>
        </div>
      </div>
    </div>
  );
};
