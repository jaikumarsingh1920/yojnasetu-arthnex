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
      {/* Welcome Banner (Warm Theme) */}
      <div className="bg-gradient-to-r from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white p-6 sm:p-8 rounded-2xl shadow-warm-md border border-[#E8D8D2]/20 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="inline-flex items-center gap-2 bg-[#F7AE56]/20 text-[#F7AE56] text-xs font-bold px-3 py-1 rounded-full mb-2 border border-[#F7AE56]/40">
            <ShieldCheck className="w-4 h-4 text-[#F7AE56]" />
            {t('dashboard.workspaceBadge', 'Citizen Workspace')}
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold">
            {t('dashboard.welcome', { name: user?.email || user?.phone || 'Beneficiary' })}
          </h1>
          <p className="text-[#FFD0CA]/90 text-xs sm:text-sm mt-1">
            {t('dashboard.welcomeSub', 'Manage your scheme application guidance, eligibility readiness, and saved schemes.')}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Link
            to="/recommendations"
            className="bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-warm-xs transition flex items-center gap-1.5"
          >
            <Sparkles className="w-4 h-4 text-white" />
            {t('dashboard.checkEligibility', 'Find Schemes For Me')}
          </Link>
          <Link
            to="/profile"
            className="bg-[#FFD0CA] hover:bg-[#fca59d] text-[#4A2525] text-xs font-bold px-4 py-2.5 rounded-xl border border-transparent transition flex items-center gap-1.5"
          >
            <User className="w-4 h-4 text-[#4A2525]" />
            {t('dashboard.myProfile', 'My Citizen Profile')}
          </Link>
        </div>
      </div>

      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* ── Citizen Profile & Eligibility Readiness Card ── */}
      <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#E8D8D2]/60 pb-4">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 bg-[#FFD0CA] text-[#4A2525] rounded-xl flex items-center justify-center font-bold">
              <User className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-[#3B2522]">
                  {t('dashboard.profileCardTitle', 'Citizen Profile & Eligibility Readiness')}
                </h2>
                <span
                  className={`text-xs font-extrabold px-2.5 py-0.5 rounded-full border ${
                    completionPct >= 80
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : completionPct >= 50
                      ? 'bg-[#F7AE56]/20 text-[#3B2522] border-[#F7AE56]/40'
                      : 'bg-[#FFF4EC] text-[#765E59] border-[#E8D8D2]'
                  }`}
                >
                  {completionPct >= 100
                    ? t('dashboard.profile100Complete', '100% Profile Complete')
                    : `${completionPct}% ${t('dashboard.profileComplete', 'Profile Complete')}`}
                </span>
              </div>
              <p className="text-xs text-[#765E59] mt-0.5">
                {completionPct >= 80
                  ? t('dashboard.profileReadyDesc', 'Your profile is comprehensive. All 90 government schemes can be evaluated with 100% accuracy.')
                  : t('dashboard.profileIncompleteDesc', 'Complete your profile to get more accurate scheme recommendations and pre-fill applications.')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Link
              to="/profile"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#FFF4EC] hover:bg-[#FFD0CA]/40 text-[#4A2525] border border-[#E8D8D2] text-xs font-bold transition"
            >
              <Edit3 className="w-3.5 h-3.5 text-[#4A2525]" />
              {t('dashboard.editProfileBtn', 'Edit Profile')}
            </Link>
            <Link
              to="/recommendations"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold shadow-warm-xs transition"
            >
              <Sparkles className="w-3.5 h-3.5 text-white" />
              {t('dashboard.findSchemesBtn', 'Find Schemes For Me')}
            </Link>
          </div>
        </div>

        {/* Profile Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-bold text-[#3B2522]">
            <span>{t('dashboard.completionLabel', 'Profile Completeness')}</span>
            <span>{completionPct}%</span>
          </div>
          <div className="w-full h-2.5 bg-[#FFF4EC] border border-[#E8D8D2]/60 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                completionPct >= 80
                  ? 'bg-emerald-500'
                  : completionPct >= 50
                  ? 'bg-[#F7AE56]'
                  : 'bg-[#EA717B]'
              }`}
              style={{ width: `${completionPct}%` }}
            />
          </div>
        </div>

        {/* Profile Attributes Summary */}
        {prof && (prof.age || prof.social_category || prof.annual_income || prof.state) ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
            <div className="bg-[#FFFBF0] p-3 rounded-xl border border-[#E8D8D2]">
              <span className="text-[10px] font-bold text-[#765E59] uppercase block">{t('profile.age', 'Age')}</span>
              <span className="text-xs font-extrabold text-[#3B2522]">{prof.age ? `${prof.age} Yrs` : '—'}</span>
            </div>
            <div className="bg-[#FFFBF0] p-3 rounded-xl border border-[#E8D8D2]">
              <span className="text-[10px] font-bold text-[#765E59] uppercase block">{t('profile.gender', 'Gender')}</span>
              <span className="text-xs font-extrabold text-[#3B2522]">{prof.gender || '—'}</span>
            </div>
            <div className="bg-[#FFFBF0] p-3 rounded-xl border border-[#E8D8D2]">
              <span className="text-[10px] font-bold text-[#765E59] uppercase block">{t('profile.socialCategory', 'Category')}</span>
              <span className="text-xs font-extrabold text-[#3B2522]">{prof.social_category || '—'}</span>
            </div>
            <div className="bg-[#FFFBF0] p-3 rounded-xl border border-[#E8D8D2]">
              <span className="text-[10px] font-bold text-[#765E59] uppercase block">{t('profile.state', 'State')}</span>
              <span className="text-xs font-extrabold text-[#3B2522] truncate block" title={prof.state || ''}>
                {prof.state ? prof.state.replace(/_/g, ' ') : '—'}
              </span>
            </div>
            <div className="bg-[#FFFBF0] p-3 rounded-xl border border-[#E8D8D2]">
              <span className="text-[10px] font-bold text-[#765E59] uppercase block">{t('profile.annualIncome', 'Income')}</span>
              <span className="text-xs font-extrabold text-[#3B2522]">
                {prof.annual_income ? `₹${prof.annual_income.toLocaleString('en-IN')}` : '—'}
              </span>
            </div>
            <div className="bg-[#FFFBF0] p-3 rounded-xl border border-[#E8D8D2]">
              <span className="text-[10px] font-bold text-[#765E59] uppercase block">{t('profile.sector', 'Sector')}</span>
              <span className="text-xs font-extrabold text-[#3B2522] truncate block" title={prof.sector || ''}>
                {prof.sector || '—'}
              </span>
            </div>
          </div>
        ) : null}

        {/* Missing Fields Callout if incomplete */}
        {missingFields.length > 0 && (
          <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
            <div className="space-y-1">
              <div className="font-bold text-[#3B2522] flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-[#F7AE56] shrink-0" />
                <span>{t('dashboard.missingTitle', 'Missing Information for 100% Scheme Matching')}:</span>
              </div>
              <div className="flex flex-wrap gap-1.5 pt-0.5">
                {missingFields.map((mf) => (
                  <span
                    key={mf.field}
                    className="inline-block bg-white text-[#3B2522] text-[11px] font-bold px-2 py-0.5 rounded border border-[#E8D8D2]"
                    title={mf.impact_reason}
                  >
                    • {mf.label}
                  </span>
                ))}
              </div>
            </div>
            <Link
              to="/profile"
              className="shrink-0 bg-[#EA717B] hover:bg-[#d65f69] text-white font-bold text-xs px-3.5 py-2 rounded-xl transition shadow-warm-xs flex items-center gap-1"
            >
              {t('dashboard.completeNow', 'Complete Profile →')}
            </Link>
          </div>
        )}
      </div>

      {/* Readiness Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-[#E8D8D2] shadow-warm-xs flex items-center gap-4">
          <div className="w-12 h-12 bg-[#FFF4EC] rounded-xl flex items-center justify-center text-[#F7AE56]">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-[#765E59] uppercase tracking-wider block">{t('dashboard.checklistsInProgress', 'Checklists in Progress')}</span>
            <span className="text-2xl font-extrabold text-[#3B2522]">{draftCount}</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-[#E8D8D2] shadow-warm-xs flex items-center gap-4">
          <div className="w-12 h-12 bg-[#FFD0CA] rounded-xl flex items-center justify-center text-[#4A2525]">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-[#765E59] uppercase tracking-wider block">{t('dashboard.checklistsPrepared', 'Document Checklists Prepared')}</span>
            <span className="text-2xl font-extrabold text-[#3B2522]">{submittedCount + approvedCount}</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-[#E8D8D2] shadow-warm-xs flex items-center gap-4">
          <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center text-emerald-600">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-[#765E59] uppercase tracking-wider block">{t('dashboard.matchReadiness', 'Profile Match Readiness')}</span>
            <span className="text-2xl font-extrabold text-emerald-600">{completionPct}%</span>
          </div>
        </div>
      </div>

      {/* ── Quick Workspaces: Active Comparison & Saved Schemes ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Active Comparison Continuation Card */}
        {selectedSchemeIds.length > 0 ? (
          <div className="bg-gradient-to-r from-[#FFF4EC] to-[#FFFBF0] border border-[#FFD0CA] rounded-2xl p-6 shadow-warm-xs flex flex-col justify-between space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-[#4A2525] font-bold text-sm">
                <Scale className="w-5 h-5 text-[#EA717B] shrink-0" />
                <span>{t('dashboard.compareResumeTitle', 'Active Scheme Comparison')}</span>
              </div>
              <p className="text-xs text-[#765E59] leading-relaxed">
                {t('dashboard.compareResumeDesc', 'You have selected {{count}} scheme(s) for side-by-side comparison.', { count: selectedSchemeIds.length })}
              </p>
            </div>
            <div>
              <Link
                to={`/compare?schemes=${selectedSchemeIds.join(',')}`}
                className="inline-flex items-center gap-2 bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-warm-xs transition"
              >
                {t('dashboard.compareResumeBtn', 'Resume Comparison')} ({selectedSchemeIds.length}/4) →
              </Link>
            </div>
          </div>
        ) : (
          <div className="bg-white border border-[#E8D8D2] rounded-2xl p-6 shadow-warm-xs flex flex-col justify-between space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-[#3B2522] font-bold text-sm">
                <Scale className="w-5 h-5 text-[#765E59] shrink-0" />
                <span>{t('dashboard.compareResumeTitle', 'Scheme Comparison Tool')}</span>
              </div>
              <p className="text-xs text-[#765E59] leading-relaxed">
                {t('dashboard.compareDescEmpty', 'Compare up to 4 central & state schemes side-by-side on eligibility, interest rates, and subsidies.')}
              </p>
            </div>
            <div>
              <Link
                to="/schemes"
                className="inline-flex items-center gap-1.5 text-[#EA717B] hover:underline text-xs font-bold"
              >
                {t('dashboard.compareBrowseLink', 'Browse & Add Schemes to Compare →')}
              </Link>
            </div>
          </div>
        )}

        {/* Saved Schemes Workspace Card */}
        <div className="bg-white border border-[#E8D8D2] rounded-2xl p-6 shadow-warm-xs flex flex-col justify-between space-y-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-[#3B2522] font-bold text-sm">
              <Bookmark className="w-5 h-5 text-[#F7AE56] shrink-0" />
              <span>{t('dashboard.savedSchemesQuickTitle', 'Saved Schemes Workspace')}</span>
            </div>
            <p className="text-xs text-[#765E59] leading-relaxed">
              {t('dashboard.savedSchemesQuickDesc', 'View and manage your bookmarked official schemes for quick access and offline reference.')}
            </p>
          </div>
          <div>
            <Link
              to="/saved-schemes"
              className="inline-flex items-center gap-2 bg-[#F7AE56] hover:bg-[#e09a45] text-[#3B2522] text-xs font-bold px-4 py-2.5 rounded-xl shadow-warm-xs transition"
            >
              {t('dashboard.viewSavedBtn', 'View Saved Schemes')} →
            </Link>
          </div>
        </div>
      </div>

      {/* Active Applications Section */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-[#E8D8D2] shadow-warm-xs space-y-6">
        <div className="flex justify-between items-center border-b border-[#E8D8D2] pb-4">
          <div>
            <h2 className="text-lg font-bold text-[#3B2522] flex items-center gap-2">
              <FileText className="w-5 h-5 text-[#EA717B]" />
              {t('dashboard.activeApplications')}
            </h2>
            <p className="text-xs text-[#765E59] mt-0.5">
              {t('dashboard.activeApplicationsSub', 'Review current status, required document checklists, and assigned partner offices.')}
            </p>
          </div>

          <Link
            to="/recommendations"
            className="text-xs font-bold text-[#EA717B] hover:underline flex items-center gap-1"
          >
            <PlusCircle className="w-4 h-4" /> {t('dashboard.startNewCheck', 'Start New Check')}
          </Link>
        </div>

        {isLoading ? (
          <div className="py-12 text-center">
            <div className="w-8 h-8 border-3 border-[#EA717B] border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-[#765E59] mt-2">{t('errors.loading')}</p>
          </div>
        ) : applications.length === 0 ? (
          <div className="py-12 text-center bg-[#FFFBF0] rounded-xl border border-dashed border-[#E8D8D2] space-y-3">
            <FileText className="w-10 h-10 text-[#765E59]/40 mx-auto" />
            <p className="text-xs text-[#765E59] max-w-sm mx-auto">
              {t('dashboard.noApplications')}
            </p>
            <Link
              to="/recommendations"
              className="inline-flex items-center gap-1.5 bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold px-4 py-2 rounded-xl shadow-warm-xs transition"
            >
              <Sparkles className="w-4 h-4" /> {t('dashboard.checkEligibility')}
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FFFBF0] text-[#765E59] uppercase font-bold border-b border-[#E8D8D2] text-[11px]">
                <tr>
                  <th className="py-3 px-4">{t('applications.appId')}</th>
                  <th className="py-3 px-4">{t('applications.scheme')}</th>
                  <th className="py-3 px-4">{t('applications.status')}</th>
                  <th className="py-3 px-4">{t('applications.lastUpdated')}</th>
                  <th className="py-3 px-4 text-right">{t('common.action', 'Action')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E8D8D2]/50 font-medium">
                {applications.map((app) => (
                  <tr key={app.application_id} className="hover:bg-[#FFFBF0]/60 transition">
                    <td className="py-3 px-4 font-mono font-bold text-[#4A2525]">
                      {app.application_id}
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-bold text-[#3B2522] block">{app.scheme_name || app.scheme_id}</span>
                      <span className="font-mono text-[10px] text-[#765E59]">ID: {app.scheme_id}</span>
                    </td>
                    <td className="py-3 px-4">
                      <ApplicationStatusBadge status={app.status} />
                    </td>
                    <td className="py-3 px-4 text-[#765E59]">
                      {new Date(app.updated_at || app.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/applications/${app.application_id}`}
                        className="text-[#EA717B] hover:underline font-bold inline-flex items-center gap-1"
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
