import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { partnerApi } from '../api/partnerApi';
import { ApplicationResponse } from '../types';
import { ApplicationStatusBadge } from '../components/Badge';
import { Alert } from '../components/Alert';
import { useAuth } from '../context/AuthContext';
import { Building2, Search, Filter, ShieldCheck, ArrowRight, UserCheck, Play } from 'lucide-react';

export const PartnerQueue: React.FC = () => {
  const { user, role } = useAuth();
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('SUBMITTED');
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

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
      <div className="bg-gradient-to-r from-amber-900 via-amber-800 to-slate-900 text-white p-6 sm:p-8 rounded-2xl shadow-md border-b-4 border-amber-500 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="inline-flex items-center gap-2 bg-amber-950 text-amber-300 text-xs font-bold px-3 py-1 rounded-full mb-2 border border-amber-700">
            <Building2 className="w-4 h-4 text-amber-400" />
            Partner Channelizing Agency Review Portal
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold">Application Review Queue</h1>
          <p className="text-xs sm:text-sm text-amber-100 mt-1">
            Server-side data isolation active for partner ID: <strong className="font-mono text-white">{user?.partner_id || 'GLOBAL ADMIN'}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-700 text-xs font-bold bg-slate-800 text-white outline-none"
          >
            <option value="">All Statuses</option>
            <option value="SUBMITTED">SUBMITTED (Pending Review)</option>
            <option value="UNDER_REVIEW">UNDER REVIEW</option>
            <option value="CORRECTION_REQUIRED">CORRECTION REQUIRED</option>
            <option value="APPROVED">APPROVED</option>
            <option value="REJECTED">REJECTED</option>
          </select>
        </div>
      </div>

      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* Queue Table */}
      {isLoading ? (
        <div className="py-16 text-center">
          <div className="w-8 h-8 border-4 border-amber-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs text-slate-500 mt-2 font-medium">Loading partner review applications...</p>
        </div>
      ) : applications.length === 0 ? (
        <div className="py-16 text-center bg-white rounded-xl border border-slate-200">
          <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No Applications in Queue</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
            There are currently no submitted applications matching status filter '{statusFilter || 'ALL'}'.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {applications.map((app) => (
            <div key={app.application_id} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-slate-900">{app.scheme_name || `Scheme ${app.scheme_id}`}</h3>
                  <ApplicationStatusBadge status={app.status} />
                </div>

                <p className="text-xs text-slate-500 font-mono">
                  App ID: {app.application_id} | Beneficiary ID: {app.user_id}
                </p>

                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 pt-1">
                  <span>Submitted: {app.submitted_at ? new Date(app.submitted_at).toLocaleString() : 'N/A'}</span>
                  <span>Assigned Reviewer: {app.assigned_reviewer_id || 'Unassigned'}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {app.status === 'SUBMITTED' && (
                  <button
                    onClick={() => handleStartReview(app.application_id)}
                    className="bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold px-3.5 py-2 rounded-lg transition flex items-center gap-1"
                  >
                    <Play className="w-3.5 h-3.5" /> Start Review
                  </button>
                )}

                <Link
                  to={`/partner/applications/${app.application_id}`}
                  className="bg-gov-navy hover:bg-slate-900 text-white text-xs font-bold px-4 py-2 rounded-lg transition flex items-center gap-1"
                >
                  Review Details & Documents <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
