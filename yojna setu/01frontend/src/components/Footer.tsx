import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Mail, MapPin, PhoneCall, ShieldCheck } from 'lucide-react';

const footerLinkClass =
  'w-fit text-left text-[14px] text-white/65 transition hover:text-[#B9E92F]';

export const Footer: React.FC = () => {
  const { t } = useTranslation();

  return (
    <footer className="mt-auto w-full bg-[#091928] text-white">
      <div className="mx-auto w-full max-w-[1380px] px-8 py-16 lg:px-12">
        <div className="grid grid-cols-1 gap-14 md:grid-cols-2 lg:grid-cols-4">
          <div>
            <Link to="/" className="flex w-fit items-center gap-4 text-left">
              <div className="flex h-[64px] w-[64px] shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-white/5">
                <img src="/logo.png" alt="YojnaSetu Logo" className="h-[58px] w-[58px] object-contain" />
              </div>
              <span className="text-[25px] font-bold tracking-tight">Yojna<span className="text-[#B9E92F]">Setu</span></span>
            </Link>

            <p className="mt-7 max-w-[310px] text-[14px] leading-7 text-white/65">{t('footer.aboutDesc')}</p>
            <div className="mt-5 flex items-center gap-2 text-[13px] text-white/45">
              <ShieldCheck className="h-4 w-4 shrink-0 text-[#B9E92F]" />
              <span>100% {t('home.gazetteVerified')}</span>
            </div>
          </div>

          <div>
            <h3 className="text-[17px] font-bold text-white">{t('footer.quickLinks')}</h3>
            <div className="mt-3 h-[2px] w-[55px] bg-[#B9E92F]" />
            <div className="mt-7 flex flex-col gap-4">
              <Link to="/schemes" className={footerLinkClass}>{t('footer.allSchemes')}</Link>
              <Link to="/recommendations" className={footerLinkClass}>{t('footer.smartMatch')}</Link>
              <Link to="/calculator" className={footerLinkClass}>{t('footer.calculator')}</Link>
              <Link to="/channel-partners" className={footerLinkClass}>{t('footer.partnerCenters')}</Link>
              <Link to="/login" className={footerLinkClass}>{t('footer.adminPortal')}</Link>
            </div>
          </div>

          <div>
            <h3 className="text-[17px] font-bold text-white">{t('footer.governanceTitle', 'Governance & Trust')}</h3>
            <div className="mt-3 h-[2px] w-[55px] bg-[#B9E92F]" />
            <p className="mt-7 max-w-[300px] text-[14px] leading-7 text-white/65">
              {t('footer.governanceDesc', 'Designed to eliminate financial misrepresentation and opaque approvals in welfare distribution.')}
            </p>
            <div className="mt-5 max-w-[310px] rounded-lg border border-white/10 bg-white/5 p-4 text-[12px] leading-5 text-white/45">
              <p className="font-semibold text-white/75">{t('footer.deterministicPolicy', 'Deterministic Engine Policy:')}</p>
              <p className="mt-1">{t('home.deterministicNote')}</p>
            </div>
          </div>

          <div>
            <h3 className="text-[17px] font-bold text-white">{t('footer.supportTitle', 'Support & Helpline')}</h3>
            <div className="mt-3 h-[2px] w-[55px] bg-[#B9E92F]" />
            <div className="mt-7 flex flex-col gap-5">
              <div className="flex items-start gap-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#B9E92F] text-[#091928]"><PhoneCall className="h-4 w-4" /></div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-white/40">Toll Free</p>
                  <a href="tel:1800112026" title="Call YojnaSetu Helpline" className="mt-1 block text-[14px] text-white/75 transition hover:text-[#B9E92F]">{t('footer.helplineText', '1800-11-2026 (Toll-Free, 9 AM - 6 PM IST)')}</a>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#B9E92F] text-[#091928]"><Mail className="h-4 w-4" /></div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-white/40">Email</p>
                  <a href="mailto:support@yojnasetu.gov.in" title="Email YojnaSetu Support" className="mt-1 block break-all text-[14px] text-white/75 transition hover:text-[#B9E92F]">{t('footer.supportEmail', 'support@yojnasetu.gov.in')}</a>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#B9E92F] text-[#091928]"><MapPin className="h-4 w-4" /></div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-white/40">Office</p>
                  <p className="mt-1 max-w-[230px] text-[14px] leading-6 text-white/75">{t('footer.ministryAddress', 'Ministry of Social Justice & Empowerment, New Delhi, India')}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-white/15">
        <div className="mx-auto flex min-h-[65px] max-w-[1380px] items-center px-8 text-center text-[12px] text-white/45 lg:px-12">
          <p className="m-0 w-full">{t('footer.rights')}</p>
        </div>
      </div>
    </footer>
  );
};
