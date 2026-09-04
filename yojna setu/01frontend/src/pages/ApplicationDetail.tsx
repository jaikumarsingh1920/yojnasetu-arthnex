import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { applicationApi } from '../api/applicationApi';
import { schemeApi } from '../api/schemeApi';
import { ApplicationResponse, SubmissionValidationResponse, ApplicationDocument, Scheme } from '../types';
import { ApplicationStatusBadge } from '../components/Badge';
import { StatusTimeline } from '../components/StatusTimeline';
import { Alert } from '../components/Alert';
import { OfficialPortalModal } from '../components/OfficialPortalModal';
import { MapLocator } from '../components/MapLocator';
import {
  FileText,
  Upload,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  ShieldCheck,
  ArrowLeft,
  XCircle,
  FileCheck2,
  Clock
} from 'lucide-react';

export const ApplicationDetail: React.FC = () => {
  const { t } = useTranslation();
  const { id: applicationId } = useParams<{ id: string }>();

  const [appData, setAppData] = useState<ApplicationResponse | null>(null);
  const [scheme, setScheme] = useState<Scheme | null>(null);
  const [validation, setValidation] = useState<SubmissionValidationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedPartnerId, setSelectedPartnerId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmitApplication = async () => {
    if (!applicationId || !selectedPartnerId) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      await applicationApi.submitApplication(applicationId, selectedPartnerId);
      setSuccessMsg('Application successfully routed to the Channel Partner.');
      await fetchApplicationDetail(applicationId);
    } catch (err: any) {
      setErrorMsg('Failed to submit application. ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    if (applicationId) {
      fetchApplicationDetail(applicationId);
    }
  }, [applicationId]);

  const fetchApplicationDetail = async (id: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await applicationApi.getApplicationById(id);
      setAppData(data);

      if (data.scheme_id) {
        try {
          const sch = await schemeApi.getSchemeById(data.scheme_id);
          setScheme(sch);
        } catch (e) {
          console.warn('Scheme details load note:', e);
        }
      }

      if (['DRAFT', 'DOCUMENTS_PENDING', 'READY_FOR_SUBMISSION'].includes(data.status)) {
        checkValidation(id);
      }
    } catch (err: any) {
      setErrorMsg('Failed to load application details. ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const checkValidation = async (id: string) => {
    try {
      const val = await applicationApi.validateSubmission(id);
      setValidation(val);
    } catch (err) {
      console.error('Validation check error:', err);
    }
  };

  const handleFileUpload = async (doc: ApplicationDocument, file: File) => {
    if (!applicationId) return;

    const maxBytes = 5 * 1024 * 1024;
    if (file.size > maxBytes) {
      alert(`File size exceeds 5MB limit (${(file.size / 1024 / 1024).toFixed(2)} MB).`);
      return;
    }

    setIsUploading(doc.app_document_id);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      await applicationApi.uploadDocument(applicationId, doc.app_document_id, file);
      setSuccessMsg(`Document '${doc.document_name}' added to your personal checklist.`);
      await fetchApplicationDetail(applicationId);
    } catch (err: any) {
      setErrorMsg('Document upload failed. ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsUploading(null);
    }
  };

  if (isLoading) {
    return (
      <div className="py-20 text-center">
        <div className="w-10 h-10 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-xs text-slate-500 mt-3 font-medium">{t('applications.loadingDetail', 'Loading application guidance details...')}</p>
      </div>
    );
  }

  if (!appData) {
    return (
      <div className="max-w-4xl mx-auto my-12 px-4">
        <Alert type="error" title={t('applications.recordNotFound', 'Record Not Found')}>
          {errorMsg || `Application guidance record with ID '${applicationId}' was not found.`}
        </Alert>
        <div className="mt-4">
          <Link to="/applications" className="text-xs font-bold text-sky-700 hover:underline flex items-center gap-1">
            <ArrowLeft className="w-4 h-4" /> {t('applications.backToGuidance', 'Back to My Guidance Records')}
          </Link>
        </div>
      </div>
    );
  }

  const [isWithdrawModalOpen, setIsWithdrawModalOpen] = useState(false);
  const [withdrawReason, setWithdrawReason] = useState('');
  const [isWithdrawing, setIsWithdrawing] = useState(false);

  const handleWithdrawApplication = async () => {
    if (!applicationId) return;
    setIsWithdrawing(true);
    setErrorMsg(null);
    try {
      await applicationApi.withdrawApplication(applicationId, withdrawReason);
      setSuccessMsg('Application successfully withdrawn.');
      setIsWithdrawModalOpen(false);
      await fetchApplicationDetail(applicationId);
    } catch (err: any) {
      setErrorMsg('Failed to withdraw application. ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsWithdrawing(false);
    }
  };

  const officialUrl = scheme?.application_url || scheme?.official_portal || scheme?.official_source_url;
  const isActionRequired = appData && ['CORRECTION_REQUIRED', 'NEEDS_CORRECTION', 'MORE_INFORMATION_REQUIRED'].includes(appData.status);
  const canWithdraw = appData && !['APPROVED', 'REJECTED', 'WITHDRAWN', 'COMPLETED'].includes(appData.status);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back Button */}
      <div className="flex justify-between items-center">
        <Link to="/applications" className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-slate-900 transition">
          <ArrowLeft className="w-4 h-4" /> {t('applications.backToGuidance', 'Back to Guidance List')}
        </Link>
        {canWithdraw && (
          <button
            onClick={() => setIsWithdrawModalOpen(true)}
            className="text-xs font-bold text-rose-600 hover:text-rose-700 underline"
          >
            {t('applications.withdrawApp', 'Withdraw Application')}
          </button>
        )}
      </div>

      {/* Header Banner */}
      <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ApplicationStatusBadge status={appData.status} />
            <span className="text-xs font-mono text-slate-500 font-bold">{t('applications.guidanceId', 'Guidance ID: {{id}}', { id: appData.application_id, date: '' })}</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">{appData.scheme_name || `Scheme ${appData.scheme_id}`}</h1>
          <p className="text-xs text-slate-500 mt-1">
            {t('common.createdOn', 'Created On')}: {new Date(appData.created_at).toLocaleDateString()} | {t('common.lastUpdated', 'Last Updated')}: {new Date(appData.updated_at).toLocaleDateString()}
          </p>
        </div>

        {/* Primary CTA: Apply on Official Portal */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <button
            onClick={() => setIsModalOpen(true)}
            className="w-full md:w-auto bg-gov-saffron hover:bg-orange-600 text-white font-bold text-xs px-6 py-3 rounded-xl shadow-lg transition flex items-center justify-center gap-2 shrink-0 min-h-[44px]"
          >
            {t('channelPartners.applyOfficialPortal', 'Apply on Official Portal')} <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ── Action Required Highlight Box ── */}
      {isActionRequired && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-400 p-6 rounded-2xl shadow-sm space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-amber-700 animate-pulse" />
            <h3 className="text-base font-extrabold text-amber-950 uppercase tracking-wide">
              {t('applications.actionRequiredTitle', 'Action Required: Correction or Information Requested')}
            </h3>
          </div>
          <p className="text-xs text-amber-900 leading-relaxed">
            {t('applications.actionRequiredDesc', 'The reviewing channel partner authority has requested corrections or additional details for your application.')}
          </p>
          {appData.correction_reason && (
            <div className="bg-white p-4 rounded-xl border border-amber-200 text-xs">
              <span className="font-bold text-amber-900 block mb-0.5">{t('applications.reviewerRemarks', 'Reviewer Remarks:')}</span>
              <p className="text-slate-800 font-medium italic">"{appData.correction_reason}"</p>
            </div>
          )}
          {appData.correction_fields && (
            <div className="text-xs text-amber-900">
              <span className="font-bold block mb-1">{t('applications.fieldsToUpdate', 'Specific Fields / Items Requiring Update:')}</span>
              <div className="flex flex-wrap gap-1.5">
                {(() => {
                  try {
                    const fields = typeof appData.correction_fields === 'string' ? JSON.parse(appData.correction_fields) : appData.correction_fields;
                    return Array.isArray(fields) ? fields.map((f: string, i: number) => (
                      <span key={i} className="bg-amber-200 text-amber-900 font-bold px-2 py-0.5 rounded text-[11px]">
                        • {f}
                      </span>
                    )) : null;
                  } catch {
                    return <span className="bg-amber-200 text-amber-900 font-bold px-2 py-0.5 rounded text-[11px]">{String(appData.correction_fields)}</span>;
                  }
                })()}
              </div>
            </div>
          )}
          <div className="pt-2 flex items-center gap-3">
            <a
              href="#document-checklist"
              className="bg-amber-700 hover:bg-amber-800 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow transition inline-flex items-center gap-1.5"
            >
              <Upload className="w-4 h-4" /> {t('applications.updateDocs', 'Update Documents & Checklist')}
            </a>
          </div>
        </div>
      )}

      <div className="bg-sky-50 border border-sky-200 p-4 rounded-2xl flex items-start gap-3 text-xs text-sky-900">
        <ShieldCheck className="w-5 h-5 text-sky-700 shrink-0 mt-0.5" />
        <div>
          <p className="font-bold">{t('applications.officialNotice', 'Official Application Guidance Notice')}</p>
          <p className="text-[11px] text-sky-800 mt-0.5">
            {t('applications.officialNoticeDesc', 'YojnaSetu helps citizens organize documents and verify eligibility rules. Final application submission, document verification, and approval are performed on the official government website.')}
          </p>
        </div>
      </div>

      {successMsg && <Alert type="success">{successMsg}</Alert>}
      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left 8 Cols: Optional Document Checklist */}
        <div id="document-checklist" className="lg:col-span-8 space-y-8">

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
            <div className="flex justify-between items-center pb-4 border-b border-slate-200">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-amber-600" />
                  {t('applications.documentChecklistCount', 'Optional Document Checklist ({{count}})', { count: appData.documents.length })}
                </h3>
                <p className="text-xs text-slate-500">{t('applications.organizeDocsNotice', 'Organize your document files before applying on the official portal')}</p>
              </div>
            </div>

            <div className="space-y-4">
              {appData.documents.map((doc) => (
                <div key={doc.app_document_id} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-900">✓ {doc.document_name}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded uppercase bg-slate-200 text-slate-700">
                          {doc.requirement_type}
                        </span>
                      </div>
                      {doc.condition && <p className="text-xs text-slate-500 mt-0.5">{doc.condition}</p>}
                    </div>

                    <div className="shrink-0">
                      {doc.is_uploaded ? (
                        <span className="inline-flex items-center gap-1 bg-emerald-100 text-emerald-800 text-xs font-bold px-2.5 py-1 rounded border border-emerald-300">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> {t('applications.checklistAdded', 'CHECKLIST ADDED')}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 bg-amber-100 text-amber-800 text-xs font-medium px-2.5 py-1 rounded border border-amber-300">
                          <Clock className="w-3.5 h-3.5 text-amber-600" /> {t('applications.optionalFile', 'OPTIONAL FILE')}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 text-xs">
                    {doc.is_uploaded ? (
                      <div className="text-slate-600 flex items-center gap-2">
                        <FileCheck2 className="w-4 h-4 text-emerald-600" />
                        <span>{t('applications.fileLabel', 'File:')} <strong>{doc.file_name}</strong> ({((doc.file_size_bytes || 0) / 1024).toFixed(1)} KB)</span>
                      </div>
                    ) : (
                      <span className="text-slate-500 italic">{t('applications.noFileAdded', 'No document file added yet')}</span>
                    )}

                    <label className="cursor-pointer bg-white hover:bg-slate-100 text-slate-800 font-bold px-3 py-1.5 rounded-lg border border-slate-300 shadow-2xs transition flex items-center gap-1.5 shrink-0">
                      <Upload className="w-3.5 h-3.5 text-sky-600" />
                      {doc.is_uploaded ? t('applications.reuploadFile', 'Re-upload File') : t('applications.uploadFile', 'Upload File')}
                      <input
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg"
                        className="hidden"
                        onChange={(e) => {
                          if (e.target.files && e.target.files[0]) {
                            handleFileUpload(doc, e.target.files[0]);
                          }
                        }}
                      />
                    </label>
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500 italic">
              {t('applications.docDisclaimer', '* Final document requirements may vary. Please verify them on the official application portal.')}
            </div>
          </div>
        </div>

        {/* Right 4 Cols: Status Timeline & Official Link */}
        <div className="lg:col-span-4 space-y-6">
          {['DRAFT', 'DOCUMENTS_PENDING', 'READY_FOR_SUBMISSION', 'CORRECTION_REQUIRED'].includes(appData.status) && (
            <>
              <MapLocator 
                schemeId={appData.scheme_id}
                loanCategory={appData.profile_snapshot?.loan_category || appData.profile_snapshot?.sector}
                onSelectPartner={setSelectedPartnerId} 
                selectedPartnerId={selectedPartnerId} 
              />
              <button
                onClick={handleSubmitApplication}
                disabled={!selectedPartnerId || isSubmitting}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl text-sm transition shadow-lg"
              >
                {isSubmitting ? t('common.submitting', 'Submitting...') : t('applications.submitToPartner', 'Submit to Channel Partner')}
              </button>
            </>
          )}

          <div className="bg-slate-900 text-white p-6 rounded-2xl space-y-3 shadow-lg">
            <h4 className="text-sm font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
              <ExternalLink className="w-4 h-4" /> {t('applications.readyToApplyTitle', 'Ready to Apply?')}
            </h4>
            <p className="text-xs text-slate-300">
              {t('applications.readyToApplyDesc', 'When you are ready, click below to open the verified official portal and complete your application.')}
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="w-full mt-2 bg-gov-saffron hover:bg-orange-600 text-white font-bold py-3 rounded-xl text-xs transition shadow-lg flex items-center justify-center gap-1.5"
            >
              {t('channelPartners.applyOfficialPortal', 'Apply on Official Portal')} <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>

          <StatusTimeline
            currentStatus={appData.status}
            history={appData.status_history}
            submittedAt={appData.submitted_at}
          />
        </div>
      </div>

      {/* Official Portal Safety Dialog */}
      <OfficialPortalModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        officialUrl={officialUrl}
        schemeName={appData.scheme_name || `Scheme ${appData.scheme_id}`}
      />

      {/* Withdrawal Confirmation Dialog */}
      {isWithdrawModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 border border-slate-200">
            <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
              <div className="p-2 bg-rose-100 text-rose-600 rounded-xl">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-slate-900">{t('applications.withdrawApp', 'Withdraw Application')}</h3>
                <p className="text-xs text-slate-500">{t('applications.confirmWithdraw', 'Confirm withdrawing your active application')}</p>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              {t('applications.withdrawNotice', 'Are you sure you want to withdraw this application? This action will mark your application status as')} <strong>{t('applications.withdrawnStatus', 'WITHDRAWN')}</strong>.
            </p>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">{t('applications.withdrawReason', 'Reason for Withdrawal (Optional)')}</label>
              <textarea
                value={withdrawReason}
                onChange={(e) => setWithdrawReason(e.target.value)}
                placeholder={t('applications.withdrawPlaceholder', 'e.g. Applied via alternate scheme / No longer pursuing loan...')}
                className="w-full text-xs p-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-rose-500 focus:border-rose-500 outline-hidden min-h-[80px]"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-100">
              <button
                onClick={() => setIsWithdrawModalOpen(false)}
                disabled={isWithdrawing}
                className="px-4 py-2.5 rounded-xl border border-slate-300 text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
              >
                {t('common.cancel', 'Cancel')}
              </button>
              <button
                onClick={handleWithdrawApplication}
                disabled={isWithdrawing}
                className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold shadow-md transition disabled:opacity-50"
              >
                {isWithdrawing ? t('applications.withdrawing', 'Withdrawing...') : t('applications.confirmWithdrawBtn', 'Confirm Withdrawal')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

