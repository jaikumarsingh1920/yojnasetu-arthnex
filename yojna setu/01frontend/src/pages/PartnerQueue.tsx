import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { partnerApi } from '../api/partnerApi';
import { ApplicationResponse } from '../types';
import { ApplicationStatusBadge } from '../components/Badge';
import { Alert } from '../components/Alert';
import { useAuth } from '../context/AuthContext';
import { Building2, Search, Filter, ShieldCheck, ArrowRight, UserCheck, Play } from 'lucide-react';

export const PartnerQueue: React.FC = () => {
  const { t } = useTranslation();
  const { user, role } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const urlStatus = searchParams.get('status') || 'SUBMITTED';
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>(urlStatus);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    setStatusFilter(urlStatus);
  }, [urlStatus]);

  useEffect(() => {
    fetchQueue();
  }, [statusFilter]);

  const fetchQueue = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await partnerApi.getPartnerApplications(statusFilter || undefined);
      setApplications(data.items);
    } catch (err: any) {
      setErrorMsg('Failed to load partner review queue. ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartReview = async (appId: string) => {
    try {
      await partnerApi.startReview(appId);
      await fetchQueue();
    } catch (err: any) {
      alert(`Start Review Error: ${err.response?.data?.detail || err.message}`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-br from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white p-6 sm:p-8 rounded-3xl shadow-warm-md border border-[#E8D8D2]/20 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="inline-flex items-center gap-2 bg-white/10 text-[#F7AE56] text-xs font-bold px-3 py-1 rounded-full mb-2 border border-white/20">
            <Building2 className="w-4 h-4 text-[#F7AE56]" />
            {t('partner.portalBadge', 'Partner Channelizing Agency Review Portal')}
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white">{t('partner.queueTitle', 'Application Review Queue')}</h1>
          <p className="text-xs sm:text-sm text-[#FFFBF0]/85 mt-1">
            {t('partner.isolationNotice', 'Server-side data isolation active for partner ID:')} <strong className="font-mono text-[#F7AE56]">{user?.partner_id || 'GLOBAL ADMIN'}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => {
              const val = e.target.value;
              setStatusFilter(val);
              const updated = new URLSearchParams(searchParams);
              if (val) {
                updated.set('status', val);
              } else {
                updated.delete('status');
              }
              setSearchParams(updated, { replace: true });
            }}
            className="px-3.5 py-2 rounded-xl border border-white/20 text-xs font-bold bg-white/10 text-white outline-none focus:ring-2 focus:ring-[#EA717B] cursor-pointer"
          >
            <option value="" className="text-[#3B2522] bg-white">{t('partner.allStatuses', 'All Statuses')}</option>
            <option value="SUBMITTED" className="text-[#3B2522] bg-white">{t('partner.submittedPending', 'SUBMITTED (Pending Review)')}</option>
            <option value="UNDER_REVIEW" className="text-[#3B2522] bg-white">{t('partner.underReviewStatus', 'UNDER REVIEW')}</option>
            <option value="CORRECTION_REQUIRED" className="text-[#3B2522] bg-white">{t('partner.correctionReqStatus', 'CORRECTION REQUIRED')}</option>
            <option value="APPROVED" className="text-[#3B2522] bg-white">{t('partner.approvedStatus', 'APPROVED')}</option>
            <option value="REJECTED" className="text-[#3B2522] bg-white">{t('partner.rejectedStatus', 'REJECTED')}</option>
          </select>
        </div>
      </div>

      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* Queue Table */}
      {isLoading ? (
        <div className="py-16 text-center">
          <div className="w-8 h-8 border-4 border-[#EA717B] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs text-[#765E59] mt-2 font-medium">{t('partner.loadingQueue', 'Loading partner review applications...')}</p>
        </div>
      ) : applications.length === 0 ? (
        <div className="py-16 text-center bg-white rounded-3xl border border-[#E8D8D2] shadow-warm-xs">
          <Building2 className="w-12 h-12 text-[#765E59] mx-auto mb-3" />
          <h3 className="text-base font-bold text-[#3B2522]">{t('partner.noApplications', 'No Applications in Queue')}</h3>
          <p className="text-xs text-[#765E59] max-w-md mx-auto mt-1">
            {t('partner.noApplicationsMatching', "There are currently no submitted applications matching status filter '{{filter}}'.", { filter: statusFilter || 'ALL' })}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {applications.map((app) => (
            <div key={app.application_id} className="bg-white p-6 rounded-3xl border border-[#E8D8D2] shadow-warm-xs hover:shadow-warm-sm transition flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-[#3B2522]">{app.scheme_name || `Scheme ${app.scheme_id}`}</h3>
                  <ApplicationStatusBadge status={app.status} />
                </div>

                <p className="text-xs text-[#765E59] font-mono">
                  {t('partner.appId', 'App ID: {{id}}', { id: app.application_id })} | {t('partner.beneficiaryId', 'Beneficiary ID: {{id}}', { id: app.user_id })}
                </p>

                <div className="flex flex-wrap items-center gap-4 text-xs text-[#765E59] pt-1">
                  <span>{t('partner.submittedDate', 'Submitted: {{date}}', { date: app.submitted_at ? new Date(app.submitted_at).toLocaleString() : 'N/A' })}</span>
                  <span>{t('partner.assignedReviewer', 'Assigned Reviewer: {{reviewer}}', { reviewer: app.assigned_reviewer_id || t('partner.unassigned', 'Unassigned') })}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {app.status === 'SUBMITTED' && (
                  <button
                    onClick={() => handleStartReview(app.application_id)}
                    className="bg-[#F7AE56] hover:bg-[#e29d48] text-[#4A2525] text-xs font-bold px-3.5 py-2 rounded-xl transition shadow-warm-xs flex items-center gap-1"
                  >
                    <Play className="w-3.5 h-3.5" /> {t('partner.startReviewBtn', 'Start Review')}
                  </button>
                )}

                <Link
                  to={`/partner/applications/${app.application_id}`}
                  className="bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold px-4 py-2 rounded-xl transition shadow-warm-xs flex items-center gap-1"
                >
                  {t('partner.reviewDetailsBtn', 'Review Details & Documents')} <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
