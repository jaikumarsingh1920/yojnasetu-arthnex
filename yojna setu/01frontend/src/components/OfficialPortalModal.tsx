import React from 'react';
import { useTranslation } from 'react-i18next';
import { ExternalLink, AlertTriangle, ShieldCheck, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  officialUrl?: string | null;
  schemeName?: string;
}

export const OfficialPortalModal: React.FC<Props> = ({
  isOpen,
  onClose,
  officialUrl,
  schemeName
}) => {
  const { t } = useTranslation();
  if (!isOpen) return null;

  const validUrl = officialUrl && officialUrl !== 'UNKNOWN' && officialUrl !== 'NOT_APPLICABLE' && officialUrl.startsWith('http')
    ? officialUrl
    : null;

  const handleContinue = () => {
    if (validUrl) {
      window.open(validUrl, '_blank', 'noopener,noreferrer');
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl max-w-[min(92vw,28rem)] max-h-[calc(100dvh-2rem)] overflow-y-auto w-full shadow-2xl border border-slate-200 text-slate-900">
        {/* Header */}
        <div className="bg-gradient-to-r from-gov-navy to-sky-900 text-white p-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-amber-500/20 rounded-lg flex items-center justify-center border border-amber-400/40">
              <ExternalLink className="w-4 h-4 text-amber-300" />
            </div>
            <h3 className="font-extrabold text-sm">{t('portalModal.title')}</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-300 hover:text-white p-1 rounded transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 flex gap-3 text-amber-900 text-xs">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-amber-950">{t('portalModal.warning')}</p>
              <p className="mt-1 text-amber-800 text-[11px] leading-relaxed">
                {t('portalModal.disclaimer')}
              </p>
            </div>
          </div>

          {schemeName && (
            <div className="text-xs bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-slate-500 font-bold block text-[10px] uppercase">{t('portalModal.selectedScheme')}</span>
              <span className="font-extrabold text-slate-900 block mt-0.5">{schemeName}</span>
            </div>
          )}

          {validUrl ? (
            <div className="text-xs bg-sky-50 p-3 rounded-xl border border-sky-200 text-sky-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-sky-600 shrink-0" />
              <div className="overflow-hidden">
                <span className="text-[10px] font-bold text-sky-700 block">{t('portalModal.verifiedUrl')}</span>
                <span className="font-mono text-[11px] truncate block text-sky-950">{validUrl}</span>
              </div>
            </div>
          ) : (
            <div className="text-xs bg-rose-50 p-3 rounded-xl border border-rose-200 text-rose-800">
              <p className="font-bold">{t('portalModal.pendingTitle', 'Official Application Link Pending Verification')}</p>
              <p className="mt-1 text-[11px]">
                {t('portalModal.pendingUrl')}
              </p>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-200 rounded-xl transition"
          >
            {t('portalModal.cancel')}
          </button>
          {validUrl && (
            <button
              onClick={handleContinue}
              className="px-4 py-2 text-xs font-bold bg-gov-blue hover:bg-gov-navy text-white rounded-xl shadow-xs transition flex items-center gap-1.5"
            >
              {t('portalModal.continue')} <ExternalLink className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
