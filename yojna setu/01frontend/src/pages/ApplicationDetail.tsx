import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
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
  const navigate = useNavigate();

  const handleBackNavigation = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate('/applications');
    }
  };

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
          <button
            onClick={handleBackNavigation}
            className="text-xs font-bold text-sky-700 hover:underline flex items-center gap-1 cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" /> {t('applications.backToGuidance', 'Back to My Guidance Records')}
          </button>
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
        <button
          onClick={handleBackNavigation}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-[#765E59] hover:text-[#3B2522] transition cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> {t('applications.backToGuidance', 'Back to Guidance List')}
        </button>
        {canWithdraw && (
          <button
            onClick={() => setIsWithdrawModalOpen(true)}
            className="text-xs font-bold text-[#EA717B] hover:underline"
          >
            {t('applications.withdrawApp', 'Withdraw Application')}
          </button>
        )}
      </div>

      {/* Header Banner */}
      <div className="bg-white p-4 sm:p-6 rounded-3xl border border-[#E8D8D2] shadow-warm-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ApplicationStatusBadge status={appData.status} />
            <span className="text-xs font-mono text-[#765E59] font-bold">{t('applications.guidanceId', 'Guidance ID: {{id}}', { id: appData.application_id, date: '' })}</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-[#3B2522]">{appData.scheme_name || `Scheme ${appData.scheme_id}`}</h1>
          <p className="text-xs text-[#765E59] mt-1">
            {t('common.createdOn', 'Created On')}: {new Date(appData.created_at).toLocaleDateString()} | {t('common.lastUpdated', 'Last Updated')}: {new Date(appData.updated_at).toLocaleDateString()}
          </p>
        </div>

        {/* Primary CTA: Apply on Official Portal */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <button
            onClick={() => setIsModalOpen(true)}
            className="w-full md:w-auto bg-[#EA717B] hover:bg-[#d65f69] text-white font-bold text-xs px-6 py-3 rounded-xl shadow-warm-xs transition flex items-center justify-center gap-2 shrink-0 min-h-[44px]"
          >
            {t('channelPartners.applyOfficialPortal', 'Apply on Official Portal')} <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ── Action Required Highlight Box ── */}
      {isActionRequired && (
        <div className="bg-[#FFF4EC] border-2 border-[#F7AE56] p-6 rounded-2xl shadow-warm-xs space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-[#EA717B] animate-pulse" />
            <h3 className="text-base font-extrabold text-[#4A2525] uppercase tracking-wide">
              {t('applications.actionRequiredTitle', 'Action Required: Correction or Information Requested')}
            </h3>
          </div>
          <p className="text-xs text-[#765E59] leading-relaxed">
            {t('applications.actionRequiredDesc', 'The reviewing channel partner authority has requested corrections or additional details for your application.')}
          </p>
          {appData.correction_reason && (
            <div className="bg-white p-4 rounded-xl border border-[#FFD0CA] text-xs">
              <span className="font-bold text-[#4A2525] block mb-0.5">{t('applications.reviewerRemarks', 'Reviewer Remarks:')}</span>
              <p className="text-[#3B2522] font-medium italic">"{appData.correction_reason}"</p>
            </div>
          )}
          {appData.correction_fields && (
            <div className="text-xs text-[#4A2525]">
              <span className="font-bold block mb-1">{t('applications.fieldsToUpdate', 'Specific Fields / Items Requiring Update:')}</span>
              <div className="flex flex-wrap gap-1.5">
                {(() => {
                  try {
                    const fields = typeof appData.correction_fields === 'string' ? JSON.parse(appData.correction_fields) : appData.correction_fields;
                    return Array.isArray(fields) ? fields.map((f: string, i: number) => (
                      <span key={i} className="bg-[#FFD0CA] text-[#4A2525] font-bold px-2 py-0.5 rounded text-[11px]">
                        • {f}
                      </span>
                    )) : null;
                  } catch {
                    return <span className="bg-[#FFD0CA] text-[#4A2525] font-bold px-2 py-0.5 rounded text-[11px]">{String(appData.correction_fields)}</span>;
                  }
                })()}
              </div>
            </div>
          )}
          <div className="pt-2 flex items-center gap-3">
            <a
              href="#document-checklist"
              className="bg-[#EA717B] hover:bg-[#d65f69] text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-warm-xs transition inline-flex items-center gap-1.5"
            >
              <Upload className="w-4 h-4" /> {t('applications.updateDocs', 'Update Documents & Checklist')}
            </a>
          </div>
        </div>
      )}

      <div className="bg-[#FFF4EC] border border-[#FFD0CA] p-4 rounded-2xl flex items-start gap-3 text-xs text-[#4A2525]">
        <ShieldCheck className="w-5 h-5 text-[#EA717B] shrink-0 mt-0.5" />
        <div>
          <p className="font-bold text-[#3B2522]">{t('applications.officialNotice', 'Official Application Guidance Notice')}</p>
          <p className="text-[11px] text-[#765E59] mt-0.5">
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

          <div className="bg-white p-6 rounded-3xl border border-[#E8D8D2] shadow-warm-xs space-y-6">
            <div className="flex justify-between items-center pb-4 border-b border-[#E8D8D2]">
              <div>
                <h3 className="text-base font-bold text-[#3B2522] flex items-center gap-2">
                  <FileText className="w-5 h-5 text-[#F7AE56]" />
                  {t('applications.documentChecklistCount', 'Optional Document Checklist ({{count}})', { count: appData.documents.length })}
                </h3>
                <p className="text-xs text-[#765E59]">{t('applications.organizeDocsNotice', 'Organize your document files before applying on the official portal')}</p>
              </div>
            </div>

            <div className="space-y-4">
              {appData.documents.map((doc) => (
                <div key={doc.app_document_id} className="bg-[#FFFBF0] p-4 rounded-2xl border border-[#E8D8D2] space-y-3">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-[#3B2522]">✓ {doc.document_name}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase bg-[#FFD0CA] text-[#4A2525]">
                          {doc.requirement_type}
                        </span>
                      </div>
                      {doc.condition && <p className="text-xs text-[#765E59] mt-0.5">{doc.condition}</p>}
                    </div>

                    <div className="shrink-0">
                      {doc.is_uploaded ? (
                        <span className="inline-flex items-center gap-1 bg-[#2D6A4F]/10 text-[#2D6A4F] text-xs font-bold px-2.5 py-1 rounded-lg border border-[#2D6A4F]/30">
                          <CheckCircle2 className="w-3.5 h-3.5 text-[#2D6A4F]" /> {t('applications.checklistAdded', 'CHECKLIST ADDED')}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 bg-[#F7AE56]/20 text-[#4A2525] text-xs font-medium px-2.5 py-1 rounded-lg border border-[#F7AE56]/40">
                          <Clock className="w-3.5 h-3.5 text-[#F7AE56]" /> {t('applications.optionalFile', 'OPTIONAL FILE')}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-[#E8D8D2] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 text-xs">
                    {doc.is_uploaded ? (
                      <div className="text-[#765E59] flex items-center gap-2">
                        <FileCheck2 className="w-4 h-4 text-[#2D6A4F]" />
                        <span>{t('applications.fileLabel', 'File:')} <strong className="text-[#3B2522]">{doc.file_name}</strong> ({((doc.file_size_bytes || 0) / 1024).toFixed(1)} KB)</span>
                      </div>
                    ) : (
                      <span className="text-[#765E59] italic">{t('applications.noFileAdded', 'No document file added yet')}</span>
                    )}

                    <label className="cursor-pointer bg-white hover:bg-[#FFF4EC] text-[#3B2522] font-bold px-3 py-1.5 rounded-xl border border-[#E8D8D2] shadow-warm-xs transition flex items-center gap-1.5 shrink-0">
                      <Upload className="w-3.5 h-3.5 text-[#EA717B]" />
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

            <div className="pt-2 border-t border-[#E8D8D2]/60 text-[11px] text-[#765E59] italic">
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
                className="w-full bg-[#EA717B] hover:bg-[#d65f69] disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl text-sm transition shadow-warm-xs"
              >
                {isSubmitting ? t('common.submitting', 'Submitting...') : t('applications.submitToPartner', 'Submit to Channel Partner')}
              </button>
            </>
          )}

          <div className="bg-gradient-to-br from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white p-6 rounded-3xl space-y-3 shadow-warm-md border border-[#E8D8D2]/20">
            <h4 className="text-sm font-bold text-[#F7AE56] uppercase tracking-wider flex items-center gap-2">
              <ExternalLink className="w-4 h-4" /> {t('applications.readyToApplyTitle', 'Ready to Apply?')}
            </h4>
            <p className="text-xs text-[#FFFBF0]/80">
              {t('applications.readyToApplyDesc', 'When you are ready, click below to open the verified official portal and complete your application.')}
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="w-full mt-2 bg-[#EA717B] hover:bg-[#d65f69] text-white font-bold py-3 rounded-xl text-xs transition shadow-warm-xs flex items-center justify-center gap-1.5"
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
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-warm-lg space-y-5 border border-[#E8D8D2]">
            <div className="flex items-center gap-3 border-b border-[#E8D8D2] pb-3">
              <div className="p-2 bg-[#FFF4EC] text-[#EA717B] border border-[#FFD0CA] rounded-xl">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-[#3B2522]">{t('applications.withdrawApp', 'Withdraw Application')}</h3>
                <p className="text-xs text-[#765E59]">{t('applications.confirmWithdraw', 'Confirm withdrawing your active application')}</p>
              </div>
            </div>

            <p className="text-xs text-[#765E59] leading-relaxed">
              {t('applications.withdrawNotice', 'Are you sure you want to withdraw this application? This action will mark your application status as')} <strong className="text-[#3B2522]">{t('applications.withdrawnStatus', 'WITHDRAWN')}</strong>.
            </p>

            <div>
              <label className="block text-xs font-bold text-[#3B2522] mb-1">{t('applications.withdrawReason', 'Reason for Withdrawal (Optional)')}</label>
              <textarea
                value={withdrawReason}
                onChange={(e) => setWithdrawReason(e.target.value)}
                placeholder={t('applications.withdrawPlaceholder', 'e.g. Applied via alternate scheme / No longer pursuing loan...')}
                className="w-full text-xs p-3 border border-[#E8D8D2] rounded-xl focus:ring-2 focus:ring-[#EA717B] focus:border-[#EA717B] outline-hidden min-h-[80px]"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-[#E8D8D2]">
              <button
                onClick={() => setIsWithdrawModalOpen(false)}
                disabled={isWithdrawing}
                className="px-4 py-2.5 rounded-xl border border-[#E8D8D2] text-xs font-bold text-[#765E59] hover:bg-[#FFF4EC] transition"
              >
                {t('common.cancel', 'Cancel')}
              </button>
              <button
                onClick={handleWithdrawApplication}
                disabled={isWithdrawing}
                className="px-5 py-2.5 rounded-xl bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold shadow-warm-xs transition disabled:opacity-50"
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

