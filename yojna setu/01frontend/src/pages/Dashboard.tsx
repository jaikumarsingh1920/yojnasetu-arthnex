import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { applicationApi } from '../api/applicationApi';
import { profileApi } from '../api/profileApi';
import { ApplicationResponse, CitizenProfileResponse } from '../types';
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
  ShieldCheck,
  User,
  Edit3,
  ChevronRight,
  Bookmark,
  Scale
} from 'lucide-react';
import { useComparison } from '../context/ComparisonContext';


export const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { selectedSchemeIds } = useComparison();
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [profileData, setProfileData] = useState<CitizenProfileResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const [appData, profData] = await Promise.all([
        applicationApi.getMyApplications().catch(() => ({ items: [] })),
        profileApi.getProfile().catch(() => null),
      ]);
      setApplications(appData.items);
      setProfileData(profData);
    } catch (err: any) {
      setErrorMsg(t('errors.networkError') + ' ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  // Status counters
  const draftCount = applications.filter(a => a.status === 'DRAFT' || a.status === 'DOCUMENTS_PENDING').length;
  const submittedCount = applications.filter(a => a.status === 'SUBMITTED' || a.status === 'UNDER_REVIEW').length;
  const approvedCount = applications.filter(a => a.status === 'APPROVED').length;

  const completionPct = profileData?.completion_percentage || 0;
  const missingFields = profileData?.missing_fields || [];
  const prof = profileData?.profile;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-gov-blue to-gov-navy text-white p-6 sm:p-8 rounded-2xl shadow-md border-b-4 border-gov-saffron flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="inline-flex items-center gap-2 bg-sky-950 text-sky-300 text-xs font-bold px-3 py-1 rounded-full mb-2 border border-sky-800">
            <ShieldCheck className="w-4 h-4 text-sky-400" />
            {t('dashboard.workspaceBadge', 'Citizen Workspace')}
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold">
            {t('dashboard.welcome', { name: user?.email || user?.phone || 'Beneficiary' })}
          </h1>
          <p className="text-slate-300 text-xs sm:text-sm mt-1">
            {t('dashboard.welcomeSub', 'Manage your scheme application guidance, eligibility readiness, and saved schemes.')}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Link
            to="/recommendations"
            className="bg-gov-saffron hover:bg-orange-600 text-white text-xs font-bold px-4 py-2.5 rounded-lg shadow transition flex items-center gap-1.5"
          >
            <Sparkles className="w-4 h-4" />
            {t('dashboard.checkEligibility', 'Find Schemes For Me')}
          </Link>
          <Link
            to="/profile"
            className="bg-sky-800 hover:bg-sky-700 text-white text-xs font-bold px-4 py-2.5 rounded-lg border border-sky-600 transition flex items-center gap-1.5"
          >
            <User className="w-4 h-4 text-sky-300" />
            {t('dashboard.myProfile', 'My Citizen Profile')}
          </Link>
        </div>
      </div>

      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* ── Citizen Profile & Eligibility Readiness Card ── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 bg-sky-50 text-sky-700 rounded-xl flex items-center justify-center font-bold">
              <User className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900">
                  {t('dashboard.profileCardTitle', 'Citizen Profile & Eligibility Readiness')}
                </h2>
                <span
                  className={`text-xs font-extrabold px-2.5 py-0.5 rounded-full border ${
                    completionPct >= 80
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : completionPct >= 50
                      ? 'bg-amber-50 text-amber-700 border-amber-200'
                      : 'bg-slate-100 text-slate-700 border-slate-200'
                  }`}
                >
                  {completionPct >= 100
                    ? t('dashboard.profile100Complete', '100% Profile Complete')
                    : `${completionPct}% ${t('dashboard.profileComplete', 'Profile Complete')}`}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {completionPct >= 80
                  ? t('dashboard.profileReadyDesc', 'Your profile is comprehensive. All 90 government schemes can be evaluated with 100% accuracy.')
                  : t('dashboard.profileIncompleteDesc', 'Complete your profile to get more accurate scheme recommendations and pre-fill applications.')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Link
              to="/profile"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold transition"
            >
              <Edit3 className="w-3.5 h-3.5 text-slate-600" />
              {t('dashboard.editProfileBtn', 'Edit Profile')}
            </Link>
            <Link
              to="/recommendations"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gov-saffron hover:bg-orange-600 text-white text-xs font-bold shadow-xs transition"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-200" />
              {t('dashboard.findSchemesBtn', 'Find Schemes For Me')}
            </Link>
          </div>
        </div>

        {/* Profile Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-bold text-slate-700">
            <span>{t('dashboard.completionLabel', 'Profile Completeness')}</span>
            <span>{completionPct}%</span>
          </div>
          <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                completionPct >= 80
                  ? 'bg-emerald-500'
                  : completionPct >= 50
                  ? 'bg-amber-500'
                  : 'bg-gov-blue'
              }`}
              style={{ width: `${completionPct}%` }}
            />
          </div>
        </div>

        {/* Profile Attributes Summary or Missing Fields Indicator */}
        {prof && (prof.age || prof.social_category || prof.annual_income || prof.state) ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">{t('profile.age', 'Age')}</span>
              <span className="text-xs font-extrabold text-slate-900">{prof.age ? `${prof.age} Yrs` : '—'}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">{t('profile.gender', 'Gender')}</span>
              <span className="text-xs font-extrabold text-slate-900">{prof.gender || '—'}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">{t('profile.socialCategory', 'Category')}</span>
              <span className="text-xs font-extrabold text-slate-900">{prof.social_category || '—'}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">{t('profile.state', 'State')}</span>
              <span className="text-xs font-extrabold text-slate-900 truncate block" title={prof.state || ''}>
                {prof.state ? prof.state.replace(/_/g, ' ') : '—'}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">{t('profile.annualIncome', 'Income')}</span>
              <span className="text-xs font-extrabold text-slate-900">
                {prof.annual_income ? `₹${prof.annual_income.toLocaleString('en-IN')}` : '—'}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">{t('profile.sector', 'Sector')}</span>
              <span className="text-xs font-extrabold text-slate-900 truncate block" title={prof.sector || ''}>
                {prof.sector || '—'}
              </span>
            </div>
          </div>
        ) : null}

        {/* Missing Fields Callout if incomplete */}
        {missingFields.length > 0 && (
          <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
            <div className="space-y-1">
              <div className="font-bold text-amber-900 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>{t('dashboard.missingTitle', 'Missing Information for 100% Scheme Matching')}:</span>
              </div>
              <div className="flex flex-wrap gap-1.5 pt-0.5">
                {missingFields.map((mf) => (
                  <span
                    key={mf.field}
                    className="inline-block bg-white text-amber-800 text-[11px] font-bold px-2 py-0.5 rounded border border-amber-200"
                    title={mf.impact_reason}
                  >
                    • {mf.label}
                  </span>
                ))}
              </div>
            </div>
            <Link
              to="/profile"
              className="shrink-0 bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs px-3.5 py-2 rounded-lg transition shadow-xs flex items-center gap-1"
            >
              {t('dashboard.completeNow', 'Complete Profile →')}
            </Link>
          </div>
        )}
      </div>

      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* Readiness Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 bg-amber-50 rounded-xl flex items-center justify-center text-amber-600">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">{t('dashboard.checklistsInProgress', 'Checklists in Progress')}</span>
            <span className="text-2xl font-extrabold text-slate-900">{draftCount}</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 bg-sky-50 rounded-xl flex items-center justify-center text-sky-600">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">{t('dashboard.checklistsPrepared', 'Document Checklists Prepared')}</span>
            <span className="text-2xl font-extrabold text-slate-900">{submittedCount + approvedCount}</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center text-emerald-600">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">{t('dashboard.matchReadiness', 'Profile Match Readiness')}</span>
            <span className="text-2xl font-extrabold text-emerald-600">{completionPct}%</span>
          </div>
        </div>
      </div>

      {/* ── Quick Workspaces: Active Comparison & Saved Schemes ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Active Comparison Continuation Card */}
        {selectedSchemeIds.length > 0 ? (
          <div className="bg-gradient-to-r from-sky-50 to-indigo-50 border border-sky-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-sky-800 font-bold text-sm">
                <Scale className="w-5 h-5 text-sky-600 shrink-0" />
                <span>{t('dashboard.compareResumeTitle', 'Active Scheme Comparison')}</span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                {t('dashboard.compareResumeDesc', 'You have selected {{count}} scheme(s) for side-by-side comparison.', { count: selectedSchemeIds.length })}
              </p>
            </div>
            <div>
              <Link
                to={`/compare?schemes=${selectedSchemeIds.join(',')}`}
                className="inline-flex items-center gap-2 bg-sky-700 hover:bg-sky-800 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-xs transition"
              >
                {t('dashboard.compareResumeBtn', 'Resume Comparison')} ({selectedSchemeIds.length}/4) →
              </Link>
            </div>
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-slate-800 font-bold text-sm">
                <Scale className="w-5 h-5 text-slate-400 shrink-0" />
                <span>{t('dashboard.compareResumeTitle', 'Scheme Comparison Tool')}</span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                {t('dashboard.compareDescEmpty', 'Compare up to 4 central & state schemes side-by-side on eligibility, interest rates, and subsidies.')}
              </p>
            </div>
            <div>
              <Link
                to="/schemes"
                className="inline-flex items-center gap-1.5 text-sky-700 hover:text-sky-800 text-xs font-bold"
              >
                {t('dashboard.compareBrowseLink', 'Browse & Add Schemes to Compare →')}
              </Link>
            </div>
          </div>
        )}

        {/* Saved Schemes Workspace Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between space-y-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-slate-800 font-bold text-sm">
              <Bookmark className="w-5 h-5 text-amber-500 shrink-0" />
              <span>{t('dashboard.savedSchemesQuickTitle', 'Saved Schemes Workspace')}</span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              {t('dashboard.savedSchemesQuickDesc', 'View and manage your bookmarked official schemes for quick access and offline reference.')}
            </p>
          </div>
          <div>
            <Link
              to="/saved-schemes"
              className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-xs transition"
            >
              {t('dashboard.viewSavedBtn', 'View Saved Schemes')} →
            </Link>
          </div>
        </div>
      </div>

      {/* Official Government Guidance Notice */}
      <div className="bg-sky-50/80 border border-sky-200 rounded-2xl p-4 sm:p-5 flex items-start gap-3.5 text-xs text-sky-950">
        <ShieldCheck className="w-5 h-5 text-sky-700 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h4 className="font-bold text-sky-900">{t('dashboard.governanceNoticeTitle', 'Official Government Guidance & Prefill Bridge')}</h4>
          <p className="text-sky-800 leading-relaxed text-[11px]">
            {t('dashboard.governanceNoticeDesc', 'YojnaSetu provides citizen guidance, document checklists, partner locators, and profile prefill. Final application submission, document verification, and benefit disbursement are managed directly by the respective Ministry or Nodal Agency.')}
          </p>
        </div>
      </div>


      {/* Active Applications Section */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex justify-between items-center border-b border-slate-200 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-sky-600" />
              {t('dashboard.activeApplications')}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {t('dashboard.activeApplicationsSub', 'Review current status, required document checklists, and assigned partner offices.')}
            </p>
          </div>

          <Link
            to="/recommendations"
            className="text-xs font-bold text-sky-600 hover:text-sky-700 flex items-center gap-1"
          >
            <PlusCircle className="w-4 h-4" /> {t('dashboard.startNewCheck', 'Start New Check')}
          </Link>
        </div>

        {isLoading ? (
          <div className="py-12 text-center">
            <div className="w-8 h-8 border-3 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-slate-500 mt-2">{t('errors.loading')}</p>
          </div>
        ) : applications.length === 0 ? (
          <div className="py-12 text-center bg-slate-50 rounded-xl border border-dashed border-slate-300 space-y-3">
            <FileText className="w-10 h-10 text-slate-300 mx-auto" />
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {t('dashboard.noApplications')}
            </p>
            <Link
              to="/recommendations"
              className="inline-flex items-center gap-1.5 bg-gov-blue hover:bg-gov-navy text-white text-xs font-bold px-4 py-2 rounded-lg shadow transition"
            >
              <Sparkles className="w-4 h-4" /> {t('dashboard.checkEligibility')}
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 uppercase font-bold border-b border-slate-200 text-[11px]">
                <tr>
                  <th className="py-3 px-4">{t('applications.appId')}</th>
                  <th className="py-3 px-4">{t('applications.scheme')}</th>
                  <th className="py-3 px-4">{t('applications.status')}</th>
                  <th className="py-3 px-4">{t('applications.lastUpdated')}</th>
                  <th className="py-3 px-4 text-right">{t('common.action', 'Action')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {applications.map((app) => (
                  <tr key={app.application_id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3 px-4 font-mono font-bold text-gov-navy">
                      {app.application_id}
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-bold text-slate-900 block">{app.scheme_name || app.scheme_id}</span>
                      <span className="font-mono text-[10px] text-slate-400">ID: {app.scheme_id}</span>
                    </td>
                    <td className="py-3 px-4">
                      <ApplicationStatusBadge status={app.status} />
                    </td>
                    <td className="py-3 px-4 text-slate-500">
                      {new Date(app.updated_at || app.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/applications/${app.application_id}`}
                        className="text-sky-600 hover:text-sky-700 font-bold inline-flex items-center gap-1"
                      >
                        {t('applications.viewDetails', 'View Details')} <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
