import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ShieldCheck, PhoneCall, Mail, MapPin } from 'lucide-react';

export const Footer: React.FC = () => {
  const { t } = useTranslation();

  return (
    <footer className="bg-gov-blue text-slate-300 border-t-4 border-gov-saffron mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <Link to="/" className="flex items-center gap-2 mb-3">
            <img
              src="/logo.png"
              alt="YojnaSetu Logo"
              className="w-9 h-9 rounded-lg object-contain bg-slate-950 p-0.5 border border-slate-700 shadow"
            />
            <span className="font-extrabold text-xl text-white">{t('nav.title')}</span>
          </Link>
          <p className="text-xs text-slate-400 leading-relaxed mb-4">
            {t('footer.aboutDesc')}
          </p>
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-medium">
            <ShieldCheck className="w-4 h-4" />
            100% {t('home.gazetteVerified')}
          </div>
        </div>

        <div>
          <h4 className="text-white text-sm font-bold uppercase tracking-wider mb-3">{t('footer.quickLinks')}</h4>
          <ul className="space-y-2 text-xs">
            <li>
              <Link to="/schemes" className="hover:text-white transition">
                {t('footer.allSchemes')}
              </Link>
            </li>
            <li>
              <Link to="/recommendations" className="hover:text-white transition">
                {t('footer.smartMatch')}
              </Link>
            </li>
            <li>
              <Link to="/calculator" className="hover:text-white transition">
                {t('footer.calculator')}
              </Link>
            </li>
            <li>
              <Link to="/channel-partners" className="hover:text-white transition">
                {t('footer.partnerCenters')}
              </Link>
            </li>
            <li>
              <Link to="/login" className="hover:text-white transition">
                {t('footer.adminPortal')}
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <h4 className="text-white text-sm font-bold uppercase tracking-wider mb-3">{t('footer.supportTitle', 'Support & Helpline')}</h4>
          <ul className="space-y-2.5 text-xs text-slate-400">
            <li className="flex items-center gap-2">
              <PhoneCall className="w-4 h-4 text-gov-saffron" />
              {t('footer.helplineText', '1800-11-2026 (Toll-Free, 9 AM - 6 PM IST)')}
            </li>
            <li className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-sky-400" />
              {t('footer.supportEmail', 'support@yojnasetu.gov.in')}
            </li>
            <li className="flex items-start gap-2">
              <MapPin className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              {t('footer.ministryAddress', 'Ministry of Social Justice & Empowerment, New Delhi, India')}
            </li>
          </ul>
        </div>

        <div>
          <h4 className="text-white text-sm font-bold uppercase tracking-wider mb-3">{t('footer.governanceTitle', 'Governance & Trust')}</h4>
          <p className="text-xs text-slate-400 leading-relaxed mb-3">
            {t('footer.governanceDesc', 'Designed to eliminate financial misrepresentation and opaque approvals in welfare distribution.')}
          </p>
          <div className="bg-slate-900/80 p-3 rounded border border-slate-800 text-[11px] text-slate-400">
            <p className="font-semibold text-slate-200">{t('footer.deterministicPolicy', 'Deterministic Engine Policy:')}</p>
            {t('home.deterministicNote')}
          </div>
        </div>
      </div>

      <div className="bg-slate-950 px-4 py-4 text-center text-xs text-slate-500 border-t border-slate-800">
        <p>{t('footer.rights')}</p>
      </div>
    </footer>
  );
};
