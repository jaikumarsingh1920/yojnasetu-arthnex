import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { applicationApi } from '../api/applicationApi';
import { ApplicationResponse } from '../types';
import { ApplicationStatusBadge } from '../components/Badge';
import { Alert } from '../components/Alert';
import {
  LayoutDashboard,
  FileText,
  Sparkles,
  Search,
  Calculator,
  PlusCircle,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchMyApplications();
  }, []);

  const fetchMyApplications = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await applicationApi.getMyApplications();
      setApplications(data.items);
    } catch (err: any) {
      setErrorMsg('Failed to load active applications. ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  // Status counters
  const draftCount = applications.filter(a => a.status === 'DRAFT' || a.status === 'DOCUMENTS_PENDING').length;
  const submittedCount = applications.filter(a => a.status === 'SUBMITTED' || a.status === 'UNDER_REVIEW').length;
  const approvedCount = applications.filter(a => a.status === 'APPROVED').length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-gov-blue to-gov-navy text-white p-6 sm:p-8 rounded-2xl shadow-md border-b-4 border-gov-saffron flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="inline-flex items-center gap-2 bg-sky-950 text-sky-300 text-xs font-bold px-3 py-1 rounded-full mb-2 border border-sky-800">
            <ShieldCheck className="w-4 h-4 text-sky-400" />
            Authenticated Beneficiary Workspace
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold">
            Welcome Back, {user?.email || user?.phone || 'Beneficiary'}
          </h1>
          <p className="text-slate-300 text-xs sm:text-sm mt-1">
            Manage your government welfare applications, track verification progress, and get tailored scheme recommendations.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Link
            to="/recommendations"
            className="bg-gov-saffron hover:bg-orange-600 text-white text-xs font-bold px-4 py-2.5 rounded-lg shadow transition flex items-center gap-1.5"
          >
            <Sparkles className="w-4 h-4" />
            Check Eligibility
          </Link>
          <Link
            to="/schemes"
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold px-4 py-2.5 rounded-lg border border-slate-600 transition flex items-center gap-1.5"
          >
            <Search className="w-4 h-4 text-sky-400" />
            Discover Schemes
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center font-bold">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="text-2xl font-extrabold text-slate-900">{draftCount}</span>
            <p className="text-xs text-slate-500 font-medium">Draft & Pending Docs</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-sky-100 text-sky-800 flex items-center justify-center font-bold">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <span className="text-2xl font-extrabold text-slate-900">{submittedCount}</span>
            <p className="text-xs text-slate-500 font-medium">Under Review / Submitted</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-2xl font-extrabold text-slate-900">{approvedCount}</span>
            <p className="text-xs text-slate-500 font-medium">Approved Applications</p>
          </div>
        </div>
      </div>

      {/* Applications Section */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex justify-between items-center pb-4 border-b border-slate-200">
          <div>
            <h2 className="text-lg font-bold text-slate-900">My Active Applications</h2>
            <p className="text-xs text-slate-500">Track application status and uploaded documents</p>
          </div>
          <Link
            to="/schemes"
            className="text-xs font-bold text-sky-700 hover:text-sky-900 flex items-center gap-1"
          >
            Start New Application <PlusCircle className="w-4 h-4" />
          </Link>
        </div>

        {errorMsg && <Alert type="error">{errorMsg}</Alert>}

        {isLoading ? (
          <div className="py-12 text-center">
            <div className="w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-slate-500 mt-2">Loading applications from server...</p>
          </div>
        ) : applications.length === 0 ? (
          <div className="py-12 text-center bg-slate-50 rounded-xl border border-dashed border-slate-300">
            <FileText className="w-10 h-10 text-slate-400 mx-auto mb-2" />
            <h3 className="text-sm font-bold text-slate-800">No Applications Found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
              You haven't applied for any government schemes yet. Explore recommendations or discover schemes to get started.
            </p>
            <Link
              to="/recommendations"
              className="bg-gov-saffron hover:bg-orange-600 text-white text-xs font-bold px-4 py-2 rounded-lg transition inline-flex items-center gap-1.5"
            >
              <Sparkles className="w-4 h-4" />
              Check Recommended Schemes
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-200">
            {applications.map((app) => {
              const uploadedCount = app.documents.filter(d => d.is_uploaded).length;
              const totalCount = app.documents.length;

              return (
                <div key={app.application_id} className="py-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-slate-900">{app.scheme_name || `Scheme ${app.scheme_id}`}</h4>
                      <ApplicationStatusBadge status={app.status} />
                    </div>
                    <p className="text-xs text-slate-500 font-mono">ID: {app.application_id}</p>
                    <div className="flex items-center gap-4 text-xs text-slate-600 pt-1">
                      <span>Created: {new Date(app.created_at).toLocaleDateString()}</span>
                      <span>Documents: {uploadedCount}/{totalCount} Uploaded</span>
                    </div>
                  </div>

                  <Link
                    to={`/applications/${app.application_id}`}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold px-4 py-2 rounded-lg border border-slate-300 transition flex items-center gap-1 shrink-0"
                  >
                    View Details & Documents
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
