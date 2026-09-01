import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { partnerApi } from '../api/partnerApi';
import { ApplicationResponse, ApprovalReadinessResponse, ApplicationDocument } from '../types';
import { ApplicationStatusBadge } from '../components/Badge';
import { StatusTimeline } from '../components/StatusTimeline';
import { Alert } from '../components/Alert';
import { useAuth } from '../context/AuthContext';
import {
  Building2,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  ArrowLeft,
  FileCheck2,
  MessageSquare,
  UserCheck,
  AlertTriangle
} from 'lucide-react';

export const PartnerDetail: React.FC = () => {
  const { t } = useTranslation();
  const { id: applicationId } = useParams<{ id: string }>();
  const { role } = useAuth();

  const [appData, setAppData] = useState<ApplicationResponse | null>(null);
  const [readiness, setReadiness] = useState<ApprovalReadinessResponse | null>(null);
  const [noteText, setNoteText] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Document Rejection Modal state
  const [rejectingDoc, setRejectingDoc] = useState<ApplicationDocument | null>(null);
  const [docRejectReason, setDocRejectReason] = useState('');

  // Final Decision Rejection Modal state
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
  const [finalRejectReason, setFinalRejectReason] = useState('');

  // Request Correction Modal state
  const [isCorrectionModalOpen, setIsCorrectionModalOpen] = useState(false);
  const [correctionReason, setCorrectionReason] = useState('');
  const [correctionFields, setCorrectionFields] = useState('');

  const handleRequestCorrectionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!applicationId || !correctionReason) return;
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const updated = await partnerApi.requestCorrection(applicationId, {
        reason: correctionReason,
        correction_fields: correctionFields ? correctionFields.split(',').map(s => s.trim()) : []
      });
      setAppData(updated);
      setIsCorrectionModalOpen(false);
      setCorrectionReason('');
      setCorrectionFields('');
      setSuccessMsg('Correction request sent to beneficiary.');
    } catch (err: any) {
      setErrorMsg('Request correction failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  useEffect(() => {
    if (applicationId) {
      fetchDetail(applicationId);
    }
  }, [applicationId]);

  const fetchDetail = async (id: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await partnerApi.getPartnerApplicationDetail(id);
      setAppData(data);
      checkReadiness(id);
    } catch (err: any) {
      setErrorMsg('Failed to load application detail. ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const checkReadiness = async (id: string) => {
    try {
      const r = await partnerApi.checkApprovalReadiness(id);
      setReadiness(r);
    } catch (err) {
      console.error('Readiness check error:', err);
    }
  };

  const handleVerifyDocument = async (docId: string) => {
    if (!applicationId) return;
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await partnerApi.reviewDocument(applicationId, docId, {
        verification_status: 'VERIFIED',
        reason: 'Document verified against authentic records.'
      });
      setSuccessMsg('Document verified successfully.');
      await fetchDetail(applicationId);
    } catch (err: any) {
      setErrorMsg('Document verification failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleRejectDocumentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!applicationId || !rejectingDoc || !docRejectReason) return;

    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await partnerApi.reviewDocument(applicationId, rejectingDoc.app_document_id, {
        verification_status: 'REJECTED',
        reason: docRejectReason
      });
      setSuccessMsg(`Document '${rejectingDoc.document_name}' rejected.`);
      setRejectingDoc(null);
      setDocRejectReason('');
      await fetchDetail(applicationId);
    } catch (err: any) {
      setErrorMsg('Document rejection failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!applicationId || !noteText) return;

    try {
      await partnerApi.addReviewNote(applicationId, noteText);
      setNoteText('');
      await fetchDetail(applicationId);
    } catch (err: any) {
      alert(`Add Note Error: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleApprove = async () => {
    if (!applicationId) return;
    if (!window.confirm('Confirm final approval decision for this application?')) return;

    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const updated = await partnerApi.processReviewDecision(applicationId, {
        decision: 'APPROVED',
        reason: 'All criteria and document verifications passed cleanly.'
      });
      setAppData(updated);
      setSuccessMsg('Application APPROVED successfully!');
    } catch (err: any) {
      setErrorMsg('Approval decision failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleRejectFinalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!applicationId || !finalRejectReason) return;

    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const updated = await partnerApi.processReviewDecision(applicationId, {
        decision: 'REJECTED',
        reason: finalRejectReason
      });
      setAppData(updated);
      setIsRejectModalOpen(false);
      setFinalRejectReason('');
      setSuccessMsg('Application REJECTED.');
    } catch (err: any) {
      setErrorMsg('Rejection decision failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (isLoading) {
    return (
      <div className="py-20 text-center">
        <div className="w-10 h-10 border-4 border-amber-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-xs text-slate-500 mt-3 font-medium">{t('partner.loadingWorkspace', 'Loading partner review workspace...')}</p>
      </div>
    );
  }

  if (!appData) {
    return (
      <div className="max-w-4xl mx-auto my-12 px-4">
        <Alert type="error" title={t('partner.accessRestriction', 'Access Restriction')}>{errorMsg || t('partner.appNotFound', 'Application not found or inaccessible.')}</Alert>
        <div className="mt-4">
          <Link to="/partner" className="text-xs font-bold text-sky-700 hover:underline flex items-center gap-1">
            <ArrowLeft className="w-4 h-4" /> {t('partner.backToQueue', 'Back to Queue')}
          </Link>
        </div>
      </div>
    );
  }

  const isDecisionMaker = role === 'PARTNER_ADMIN' || role === 'SYSTEM_ADMIN';
  const isFinalized = appData.status === 'APPROVED' || appData.status === 'REJECTED';

  const handleMarkCompleted = async () => {
    if (!applicationId) return;
    const notes = window.prompt(t('partner.promptDisbursementNotes', 'Enter optional completion / disbursement notes:'));
    if (notes === null) return;
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const updated = await partnerApi.completeApplication(applicationId, notes);
      setAppData(updated);
      setSuccessMsg('Application marked COMPLETED / Benefit Disbursed successfully!');
    } catch (err: any) {
      setErrorMsg('Mark completed failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <Link to="/partner" className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-slate-900 transition">
        <ArrowLeft className="w-4 h-4" /> {t('partner.backToQueueList', 'Back to Queue List')}
      </Link>

      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ApplicationStatusBadge status={appData.status} />
            <span className="text-xs font-mono text-slate-500 font-bold">{t('partner.appId', 'App ID: {{id}}', { id: appData.application_id })}</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900">{appData.scheme_name || `Scheme ${appData.scheme_id}`}</h1>
          <p className="text-xs text-slate-500 mt-1">{t('partner.beneficiaryUserId', 'Beneficiary User ID: {{id}}', { id: appData.user_id })}</p>
        </div>

        {/* Action Decision Buttons */}
        {appData.status === 'APPROVED' && isDecisionMaker && (
          <button
            onClick={handleMarkCompleted}
            className="bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-md transition flex items-center gap-1.5"
          >
            <ShieldCheck className="w-4 h-4" /> {t('partner.markCompletedBtn', 'Mark Completed / Benefit Disbursed')}
          </button>
        )}

        {!isFinalized && (
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setIsCorrectionModalOpen(true)}
              className="bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow transition flex items-center gap-1.5"
            >
              <AlertTriangle className="w-4 h-4" /> {t('partner.requestCorrectionBtn', 'Request Correction')}
            </button>

            {isDecisionMaker && (
              <>
                <button
                  onClick={() => setIsRejectModalOpen(true)}
                  className="bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow transition flex items-center gap-1.5"
                >
                  <XCircle className="w-4 h-4" /> {t('partner.rejectAppBtn', 'Reject Application')}
                </button>

                <button
                  onClick={handleApprove}
                  disabled={Boolean(readiness && !readiness.can_approve)}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow transition flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <CheckCircle2 className="w-4 h-4" /> {t('partner.issueApprovalBtn', 'Issue Approval Decision')}
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {successMsg && <Alert type="success">{successMsg}</Alert>}
      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* Approval Readiness Alert */}
      {readiness && !isFinalized && (
        <Alert type={readiness.can_approve ? "success" : "warning"} title={t('partner.approvalReadinessStatus', 'Approval Readiness Status')}>
          <p className="font-semibold">{readiness.message}</p>
          {readiness.blocking_documents.length > 0 && (
            <p className="mt-1 text-xs text-amber-900">
              {t('partner.unverifiedDocs', 'Unverified Documents:')} {readiness.blocking_documents.join(', ')}
            </p>
          )}
        </Alert>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-8 space-y-8">
          {/* Document Verification Queue */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-slate-200 pb-3">
              <FileCheck2 className="w-5 h-5 text-amber-600" />
              {t('partner.docQueueTitle', 'Document Verification Queue ({{count}})', { count: appData.documents.length })}
            </h3>

            <div className="space-y-4">
              {appData.documents.map((doc) => (
                <div key={doc.app_document_id} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-sm text-slate-900">{doc.document_name}</h4>
                      <p className="text-xs text-slate-500">{doc.requirement_type} {t('partner.document', 'document')}</p>
                    </div>

                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${
                      doc.verification_status === 'VERIFIED'
                        ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                        : doc.verification_status === 'REJECTED'
                        ? 'bg-rose-100 text-rose-800 border-rose-300'
                        : 'bg-amber-100 text-amber-800 border-amber-300'
                    }`}>
                      {doc.verification_status}
                    </span>
                  </div>

                  {doc.is_uploaded ? (
                    <div className="text-xs text-slate-700 bg-white p-2.5 rounded border border-slate-200 flex justify-between items-center">
                      <span>{t('applications.fileLabel', 'File:')} <strong>{doc.file_name}</strong></span>
                      <span className="text-[11px] text-slate-400">{t('partner.uploadedOn', 'Uploaded')} {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : ''}</span>
                    </div>
                  ) : (
                    <p className="text-xs text-rose-700 italic">{t('partner.notUploadedByBeneficiary', 'Not uploaded by beneficiary')}</p>
                  )}

                  {/* Verification Actions */}
                  {!isFinalized && doc.is_uploaded && (
                    <div className="pt-2 border-t border-slate-200 flex justify-end gap-2 text-xs">
                      <button
                        onClick={() => setRejectingDoc(doc)}
                        className="bg-rose-50 hover:bg-rose-100 text-rose-800 px-3 py-1.5 rounded border border-rose-300 font-bold transition"
                      >
                        {t('partner.rejectDocBtn', 'Reject Document')}
                      </button>

                      <button
                        onClick={() => handleVerifyDocument(doc.app_document_id)}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white px-3.5 py-1.5 rounded font-bold shadow transition flex items-center gap-1"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" /> {t('partner.verifyDocBtn', 'Verify Document')}
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Internal Review Notes */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-slate-200 pb-3">
              <MessageSquare className="w-5 h-5 text-sky-600" />
              {t('partner.reviewNotesTitle', 'Internal Agency Review Notes ({{count}})', { count: appData.review_notes?.length || 0 })}
            </h3>

            {appData.review_notes && appData.review_notes.length > 0 && (
              <div className="space-y-3">
                {appData.review_notes.map((note) => (
                  <div key={note.note_id} className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
                    <div className="flex justify-between items-center text-slate-500 mb-1">
                      <span className="font-bold text-slate-800">{note.author_role} ({note.author_id})</span>
                      <span>{new Date(note.created_at).toLocaleString()}</span>
                    </div>
                    <p className="text-slate-800">{note.content}</p>
                  </div>
                ))}
              </div>
            )}

            {!isFinalized && (
              <form onSubmit={handleAddNote} className="space-y-2 pt-2">
                <textarea
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  placeholder={t('partner.addNotesPlaceholder', 'Add internal partner review notes...')}
                  className="w-full p-3 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none"
                  rows={3}
                />
                <button
                  type="submit"
                  disabled={!noteText}
                  className="bg-gov-navy hover:bg-slate-900 text-white font-bold text-xs px-4 py-2 rounded-lg shadow transition disabled:opacity-50"
                >
                  {t('partner.addNoteBtn', 'Add Internal Note')}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Right 4 Cols: Status Timeline */}
        <div className="lg:col-span-4 space-y-6">
          <StatusTimeline
            currentStatus={appData.status}
            history={appData.status_history}
            submittedAt={appData.submitted_at}
          />
        </div>
      </div>

      {/* Document Rejection Modal */}
      {rejectingDoc && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-2xl max-w-md w-full space-y-4 shadow-xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900">{t('partner.rejectDocTitle', "Reject Document '{{name}}'", { name: rejectingDoc.document_name })}</h3>
            <form onSubmit={handleRejectDocumentSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  {t('partner.mandatoryRejectReason', 'Mandatory Rejection Reason')}
                </label>
                <textarea
                  required
                  value={docRejectReason}
                  onChange={(e) => setDocRejectReason(e.target.value)}
                  placeholder={t('partner.docRejectPlaceholder', 'e.g. Document image is blurry or income proof mismatch.')}
                  className="w-full p-3 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-rose-500 outline-none"
                  rows={3}
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setRejectingDoc(null)}
                  className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-100"
                >
                  {t('common.cancel', 'Cancel')}
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white shadow"
                >
                  {t('partner.confirmDocRejectBtn', 'Confirm Document Rejection')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Final Decision Rejection Modal */}
      {isRejectModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-2xl max-w-md w-full space-y-4 shadow-xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900">{t('partner.rejectAppTitle', 'Reject Application')}</h3>
            <form onSubmit={handleRejectFinalSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  {t('partner.mandatoryRejectReason', 'Mandatory Rejection Reason')}
                </label>
                <textarea
                  required
                  value={finalRejectReason}
                  onChange={(e) => setFinalRejectReason(e.target.value)}
                  placeholder={t('partner.finalRejectPlaceholder', 'e.g. Ineligible income slab or mandatory documents not provided.')}
                  className="w-full p-3 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-rose-500 outline-none"
                  rows={3}
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsRejectModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-100"
                >
                  {t('common.cancel', 'Cancel')}
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white shadow"
                >
                  {t('partner.confirmAppRejectBtn', 'Confirm Application Rejection')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Request Correction Modal */}
      {isCorrectionModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-2xl max-w-md w-full space-y-4 shadow-xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              {t('partner.requestCorrectionTitle', 'Request Application Correction')}
            </h3>
            <form onSubmit={handleRequestCorrectionSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  {t('partner.mandatoryCorrectionReason', 'Mandatory Correction Reason')}
                </label>
                <textarea
                  required
                  value={correctionReason}
                  onChange={(e) => setCorrectionReason(e.target.value)}
                  placeholder={t('partner.correctionReasonPlaceholder', 'e.g. Uploaded Aadhaar card scan is blurry. Please re-upload legible document.')}
                  className="w-full p-3 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-amber-500 outline-none"
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  {t('partner.targetFieldsLabel', 'Target Documents / Fields (Comma-separated)')}
                </label>
                <input
                  type="text"
                  value={correctionFields}
                  onChange={(e) => setCorrectionFields(e.target.value)}
                  placeholder={t('partner.targetFieldsPlaceholder', 'e.g. Identity Proof, Address Proof')}
                  className="w-full p-2.5 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-amber-500 outline-none"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCorrectionModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-100"
                >
                  {t('common.cancel', 'Cancel')}
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white shadow"
                >
                  {t('partner.sendCorrectionBtn', 'Send Correction Request')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
