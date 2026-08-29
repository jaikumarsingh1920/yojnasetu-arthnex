import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { applicationApi } from '../api/applicationApi';
import { schemeApi } from '../api/schemeApi';
import { ApplicationResponse, SubmissionValidationResponse, ApplicationDocument, Scheme } from '../types';
import { ApplicationStatusBadge } from '../components/Badge';
import { StatusTimeline } from '../components/StatusTimeline';
import { Alert } from '../components/Alert';
import { OfficialPortalModal } from '../components/OfficialPortalModal';
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
  const { id: applicationId } = useParams<{ id: string }>();

  const [appData, setAppData] = useState<ApplicationResponse | null>(null);
  const [scheme, setScheme] = useState<Scheme | null>(null);
  const [validation, setValidation] = useState<SubmissionValidationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

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
        <p className="text-xs text-slate-500 mt-3 font-medium">Loading application guidance details...</p>
      </div>
    );
  }

  if (!appData) {
    return (
      <div className="max-w-4xl mx-auto my-12 px-4">
        <Alert type="error" title="Record Not Found">
          {errorMsg || `Application guidance record with ID '${applicationId}' was not found.`}
        </Alert>
        <div className="mt-4">
          <Link to="/applications" className="text-xs font-bold text-sky-700 hover:underline flex items-center gap-1">
            <ArrowLeft className="w-4 h-4" /> Back to My Guidance Records
          </Link>
        </div>
      </div>
    );
  }

  const officialUrl = scheme?.application_url || scheme?.official_portal || scheme?.official_source_url;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back Button */}
      <Link to="/applications" className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-slate-900 transition">
        <ArrowLeft className="w-4 h-4" /> Back to Guidance List
      </Link>

      {/* Header Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ApplicationStatusBadge status={appData.status} />
            <span className="text-xs font-mono text-slate-500 font-bold">Guidance ID: {appData.application_id}</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900">{appData.scheme_name || `Scheme ${appData.scheme_id}`}</h1>
          <p className="text-xs text-slate-500 mt-1">
            Created On: {new Date(appData.created_at).toLocaleDateString()}
          </p>
        </div>

        {/* Primary CTA: Apply on Official Portal */}
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-gov-saffron hover:bg-orange-600 text-white font-bold text-xs px-6 py-3 rounded-xl shadow-lg transition flex items-center gap-2 shrink-0"
        >
          Apply on Official Portal <ExternalLink className="w-4 h-4" />
        </button>
      </div>

      <div className="bg-sky-50 border border-sky-200 p-4 rounded-2xl flex items-start gap-3 text-xs text-sky-900">
        <ShieldCheck className="w-5 h-5 text-sky-700 shrink-0 mt-0.5" />
        <div>
          <p className="font-bold">Official Application Guidance Notice</p>
          <p className="text-[11px] text-sky-800 mt-0.5">
            YojnaSetu helps citizens organize documents and verify eligibility rules. Final application submission, document verification, and approval are performed on the official government website.
          </p>
        </div>
      </div>

      {successMsg && <Alert type="success">{successMsg}</Alert>}
      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left 8 Cols: Optional Document Checklist */}
        <div className="lg:col-span-8 space-y-8">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
            <div className="flex justify-between items-center pb-4 border-b border-slate-200">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-amber-600" />
                  Optional Document Checklist ({appData.documents.length})
                </h3>
                <p className="text-xs text-slate-500">Organize your document files before applying on the official portal</p>
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
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> CHECKLIST ADDED
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 bg-amber-100 text-amber-800 text-xs font-medium px-2.5 py-1 rounded border border-amber-300">
                          <Clock className="w-3.5 h-3.5 text-amber-600" /> OPTIONAL FILE
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 text-xs">
                    {doc.is_uploaded ? (
                      <div className="text-slate-600 flex items-center gap-2">
                        <FileCheck2 className="w-4 h-4 text-emerald-600" />
                        <span>File: <strong>{doc.file_name}</strong> ({((doc.file_size_bytes || 0) / 1024).toFixed(1)} KB)</span>
                      </div>
                    ) : (
                      <span className="text-slate-500 italic">No document file added yet</span>
                    )}

                    <label className="cursor-pointer bg-white hover:bg-slate-100 text-slate-800 font-bold px-3 py-1.5 rounded-lg border border-slate-300 shadow-2xs transition flex items-center gap-1.5 shrink-0">
                      <Upload className="w-3.5 h-3.5 text-sky-600" />
                      {doc.is_uploaded ? 'Re-upload File' : 'Upload File'}
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
              * Final document requirements may vary. Please verify them on the official application portal.
            </div>
          </div>
        </div>

        {/* Right 4 Cols: Status Timeline & Official Link */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-slate-900 text-white p-6 rounded-2xl space-y-3 shadow-lg">
            <h4 className="text-sm font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
              <ExternalLink className="w-4 h-4" /> Ready to Apply?
            </h4>
            <p className="text-xs text-slate-300">
              When you are ready, click below to open the verified official portal and complete your application.
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="w-full mt-2 bg-gov-saffron hover:bg-orange-600 text-white font-bold py-3 rounded-xl text-xs transition shadow-lg flex items-center justify-center gap-1.5"
            >
              Apply on Official Portal <ExternalLink className="w-3.5 h-3.5" />
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
    </div>
  );
};
