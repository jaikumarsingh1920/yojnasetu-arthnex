import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Home, Compass } from 'lucide-react';

export const NotFound: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full bg-white rounded-2xl border border-slate-200 shadow-md p-6 sm:p-8 text-center space-y-5">
        {/* YojnaSetu Branding */}
        <div className="flex items-center justify-center gap-2">
          <img
            src="/logo.png"
            alt="YojnaSetu"
            className="w-10 h-10 rounded-lg object-contain bg-slate-950 p-1 border border-slate-800 shadow-xs"
          />
          <span className="font-extrabold text-xl text-gov-navy tracking-tight">YojnaSetu</span>
        </div>

        {/* 404 Badge & Error Details */}
        <div className="space-y-2">
          <span className="inline-block px-3 py-1 bg-amber-50 text-amber-800 text-xs font-bold rounded-full border border-amber-200">
            404
          </span>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            {t('errors.pageNotFound', 'Page Not Found')}
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-sm mx-auto">
            {t('errors.pageNotFoundDesc', 'The page you are looking for does not exist or has been moved.')}
          </p>
        </div>

        {/* Navigation Action Buttons */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            to="/"
            className="w-full sm:w-auto bg-gov-navy hover:bg-slate-800 text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow-xs inline-flex items-center justify-center gap-2 transition cursor-pointer"
          >
            <Home className="w-4 h-4" /> {t('nav.home', 'Home')}
          </Link>
          <Link
            to="/schemes"
            className="w-full sm:w-auto bg-sky-50 hover:bg-sky-100 text-gov-blue text-xs font-bold px-5 py-2.5 rounded-xl border border-sky-200 inline-flex items-center justify-center gap-2 transition cursor-pointer"
          >
            <Compass className="w-4 h-4" /> {t('nav.schemes', 'Explore Schemes')}
          </Link>
        </div>
      </div>
    </div>
  );
};
