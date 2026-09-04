import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { applicationApi } from '../api/applicationApi';
import { ApplicationResponse } from '../types';
import { ApplicationStatusBadge } from '../components/Badge';
import { Alert } from '../components/Alert';
import { FileText, PlusCircle, ArrowRight, ShieldCheck } from 'lucide-react';

export const Applications: React.FC = () => {
  const { t } = useTranslation();
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchApplications();
  }, [statusFilter]);

  const fetchApplications = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await applicationApi.getMyApplications(statusFilter || undefined);
      setApplications(data.items);
    } catch (err: any) {
      setErrorMsg('Failed to fetch applications. ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 flex items-center gap-2">
            <FileText className="w-6 h-6 text-sky-600" />
            {t('applications.guidanceTitle', 'Assisted Application Guidance & Document Checklists')}
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
            {t('applications.guidanceSubtitle', 'YojnaSetu helps you discover schemes, review eligibility, and prepare your document checklists. Final application submission and approval are handled directly on the concerned official government portal.')}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white font-medium"
          >
            <option value="">{t('applications.allRecords', 'All Applications & Guidance Records')}</option>
            <option value="DRAFT">{t('applications.guidanceStarted', 'Guidance Started')}</option>
            <option value="DOCUMENTS_PENDING">{t('applications.checklistPending', 'Checklist Pending')}</option>
            <option value="READY_FOR_SUBMISSION">{t('applications.readyToApply', 'Ready to Apply on Official Portal')}</option>
            <option value="SUBMITTED">{t('applications.submittedPartner', 'Submitted to Partner')}</option>
            <option value="UNDER_REVIEW">{t('applications.underReview', 'Under Official Review')}</option>
            <option value="CORRECTION_REQUIRED">{t('applications.correctionRequired', 'Action Required')}</option>
            <option value="APPROVED">{t('applications.approved', 'Approved')}</option>
            <option value="COMPLETED">{t('applications.completed', 'Completed / Benefit Disbursed')}</option>
            <option value="WITHDRAWN">{t('applications.withdrawn', 'Withdrawn')}</option>
            <option value="REJECTED">{t('applications.rejected', 'Rejected')}</option>
          </select>

          <Link
            to="/recommendations"
            className="bg-gov-saffron hover:bg-orange-600 text-white text-xs font-bold px-4 py-2.5 rounded-lg shadow transition flex items-center gap-1.5"
          >
            <PlusCircle className="w-4 h-4" />
            {t('applications.findNewScheme', 'Find New Scheme')}
          </Link>
        </div>
      </div>

      <div className="bg-sky-50 border border-sky-200 p-4 rounded-2xl flex items-start gap-3 text-xs text-sky-900">
        <ShieldCheck className="w-5 h-5 text-sky-700 shrink-0 mt-0.5" />
        <div>
          <p className="font-bold">{t('applications.portalReminderTitle', 'Official Application Portal Reminder')}</p>
          <p className="text-[11px] text-sky-800 mt-0.5">
            {t('applications.portalReminderDesc', 'Once you complete your document checklist on YojnaSetu, use the reference link to submit your official application on the concerned government portal. Keep your official reference/acknowledgement number for tracking.')}
          </p>
        </div>
      </div>

      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* Applications List */}
      {isLoading ? (
        <div className="py-16 text-center">
          <div className="w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs text-slate-500 mt-2 font-medium">{t('applications.loadingRecords', 'Loading application guidance records...')}</p>
        </div>
      ) : applications.length === 0 ? (
        <div className="py-16 text-center bg-white rounded-2xl border border-slate-200">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">{t('applications.noRecordsFound', 'No Guidance Records Found')}</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
            {t('applications.noRecordsMatching', "You don't have any application records matching the selected status filter.")}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {applications.map((app) => {
            const uploadedDocs = app.documents.filter(d => d.is_uploaded).length;
            const totalDocs = app.documents.length;

            return (
              <div key={app.application_id} className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-slate-900">{app.scheme_name || `Scheme ${app.scheme_id}`}</h3>
                    <ApplicationStatusBadge status={app.status} />
                  </div>

                  <p className="text-xs text-slate-500 font-mono">
                    {t('applications.guidanceId', 'Guidance ID: {{id}} | Created: {{date}}', { id: app.application_id, date: new Date(app.created_at).toLocaleDateString() })}
                  </p>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 pt-1">
                    <span>{t('applications.checklistStatus', 'Document Checklist: {{uploaded}} / {{total}} items checked', { uploaded: uploadedDocs, total: totalDocs })}</span>
                  </div>
                </div>

                <Link
                  to={`/applications/${app.application_id}`}
                  className="w-full sm:w-auto bg-gov-blue hover:bg-gov-navy text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow transition flex items-center justify-center gap-1.5 shrink-0 min-h-[44px]"
                >
                  {t('applications.viewChecklistBtn', 'View Checklist & Official Portal Link')}
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
