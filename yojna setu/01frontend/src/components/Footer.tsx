import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Mail, MapPin, PhoneCall, ShieldCheck, ExternalLink } from 'lucide-react';

const footerLinkClass =
  'w-fit text-left text-sm text-[#FFFBF0]/80 transition hover:text-[#F7AE56] flex items-center gap-1.5';

export const Footer: React.FC = () => {
  const { t } = useTranslation();

  return (
    <footer className="mt-auto w-full bg-[#4A2525] text-[#FFFBF0] border-t border-[#3B2522]">
      <div className="mx-auto w-full max-w-[1440px] px-6 py-14 lg:px-12 lg:py-16">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-2 lg:grid-cols-4">
          {/* Column 1: Brand & Mission */}
          <div className="space-y-4">
            <Link to="/" className="flex items-center gap-3 text-left">
              <img
                src="/logo.png"
                alt="YojnaSetu Logo"
                className="h-10 w-10 object-contain"
              />
              <span className="text-xl font-bold tracking-tight text-[#FFFBF0]">
                Yojna<span className="text-[#F7AE56]">Setu</span>
              </span>
            </Link>

            <p className="text-sm leading-6 text-[#FFFBF0]/80 max-w-[300px]">
              {t(
                'footer.aboutDesc',
                'National civic-tech platform connecting Indian citizens, entrepreneurs, and students to verified government schemes.'
              )}
            </p>

            <div className="inline-flex items-center gap-2 bg-[#3B2522] border border-[#E8D8D2]/20 text-[#FFFBF0] px-3 py-1.5 rounded-xl text-xs font-semibold">
              <ShieldCheck className="h-4 w-4 text-[#A5D6A7] shrink-0" />
              <span>{t('footer.gazetteVerified', '100% Gazette-Verified Portfolios')}</span>
            </div>
          </div>

          {/* Column 2: Quick Links */}
          <div className="space-y-4">
            <h3 className="text-sm sm:text-base font-bold text-[#FFFBF0]">
              {t('footer.quickLinks', 'Quick Links')}
            </h3>
            <div className="h-0.5 w-8 bg-[#F7AE56] rounded-full" />

            <div className="flex flex-col gap-3 pt-1">
              <Link to="/schemes" className={footerLinkClass}>
                <span>{t('footer.allSchemes', 'Explore Schemes Directory')}</span>
              </Link>
              <Link to="/recommendations" className={footerLinkClass}>
                <span>{t('footer.smartMatch', 'Smart Scheme Matching')}</span>
              </Link>
              <Link to="/calculator" className={footerLinkClass}>
                <span>{t('footer.calculator', 'Financial Calculator')}</span>
              </Link>
              <Link to="/channel-partners" className={footerLinkClass}>
                <span>{t('footer.partnerCenters', 'Nearby Partner Centers')}</span>
              </Link>
              <Link to="/compare" className={footerLinkClass}>
                <span>{t('footer.compare', 'Compare Schemes')}</span>
              </Link>
              <Link to="/login" className={footerLinkClass}>
                <span>{t('footer.adminPortal', 'Citizen & Partner Login')}</span>
              </Link>
            </div>
          </div>

          {/* Column 3: Governance & Policy */}
          <div className="space-y-4">
            <h3 className="text-sm sm:text-base font-bold text-[#FFFBF0]">
              {t('footer.governanceTitle', 'Governance & Trust')}
            </h3>
            <div className="h-0.5 w-8 bg-[#F7AE56] rounded-full" />

            <p className="text-sm leading-6 text-[#FFFBF0]/80">
              {t(
                'footer.governanceDesc',
                'Built to eliminate financial misrepresentation, opaque approvals, and unverified intermediary fees in welfare distribution.'
              )}
            </p>

            <div className="rounded-2xl border border-[#E8D8D2]/20 bg-[#3B2522]/90 p-4 text-xs text-[#FFFBF0]/80 space-y-1.5">
              <p className="font-bold text-[#FFFBF0]">
                {t('footer.enginePolicyTitle', 'Deterministic Engine Policy:')}
              </p>
              <p className="text-xs leading-relaxed text-[#FFFBF0]/75">
                {t('footer.enginePolicyDesc', 'Eligibility determinations are grounded in published Ministry criteria without speculative estimation.')}
              </p>
            </div>
          </div>

          {/* Column 4: Helpline & Support */}
          <div className="space-y-4">
            <h3 className="text-sm sm:text-base font-bold text-[#FFFBF0]">
              {t('footer.supportTitle', 'Support & Helpline')}
            </h3>
            <div className="h-0.5 w-8 bg-[#F7AE56] rounded-full" />

            <div className="flex flex-col gap-3 pt-1">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#3B2522] border border-[#E8D8D2]/20 text-[#F7AE56]">
                  <PhoneCall className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-xs font-medium text-[#FFFBF0]/70">
                    {t('footer.helplineLabel', 'Toll-free helpline')}
                  </p>
                  <a
                    href="tel:1800112026"
                    className="text-sm font-semibold text-[#FFFBF0] hover:text-[#F7AE56] transition"
                  >
                    1800-11-2026 (9 AM – 6 PM IST)
                  </a>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#3B2522] border border-[#E8D8D2]/20 text-[#FFD0CA]">
                  <Mail className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-xs font-medium text-[#FFFBF0]/70">
                    {t('footer.supportEmailLabel', 'Citizen support email')}
                  </p>
                  <a
                    href="mailto:support@yojnasetu.gov.in"
                    className="text-sm text-[#FFFBF0] hover:text-[#F7AE56] transition"
                  >
                    support@yojnasetu.gov.in
                  </a>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#3B2522] border border-[#E8D8D2]/20 text-[#A5D6A7]">
                  <MapPin className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-xs font-medium text-[#FFFBF0]/70">
                    {t('footer.nationalOfficeLabel', 'National head office')}
                  </p>
                  <span className="text-sm text-[#FFFBF0]/85">
                    Ministry of Social Justice & Empowerment, New Delhi
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-6 border-t border-[#E8D8D2]/15 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#FFFBF0]/70">
          <p>{t('footer.rights', '© 2026 YojnaSetu Civic-Tech Portal. Content authoritative from published Gazette notifications.')}</p>
          <div className="flex items-center gap-5 text-[#FFFBF0]/75">
            <Link to="/about" className="hover:text-[#F7AE56] transition">{t('footer.about', 'About')}</Link>
            <Link to="/resources" className="hover:text-[#F7AE56] transition">{t('footer.guidelines', 'Guidelines')}</Link>
            <Link to="/faq" className="hover:text-[#F7AE56] transition">{t('footer.faq', 'FAQ')}</Link>
          </div>
        </div>
      </div>
    </footer>
  );
};