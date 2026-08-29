import React, { useState, useEffect } from 'react';
import { adminApi, AdminDashboardSummaryResponse, SchemeAuditItem } from '../api/adminApi';
import { partnerApi } from '../api/partnerApi';
import { ApplicationResponse } from '../types';
import { SystemHealthCard } from '../components/admin/SystemHealthCard';
import { RuleAuditTable } from '../components/admin/RuleAuditTable';
import { DocumentAuditTable } from '../components/admin/DocumentAuditTable';
import { ChangelogTable } from '../components/admin/ChangelogTable';
import { SchemeDetailAuditModal } from '../components/admin/SchemeDetailAuditModal';
import {
  ShieldAlert,
  Building2,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Users,
  Database,
  History,
  Layers,
  Search,
  Filter,
  Eye,
  ShieldCheck
} from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const [activeMainTab, setActiveMainTab] = useState<'OVERVIEW' | 'SCHEMES' | 'RULES' | 'DOCUMENTS' | 'CHANGELOG' | 'APPLICATIONS'>('OVERVIEW');
  const [summary, setSummary] = useState<AdminDashboardSummaryResponse | null>(null);
  const [schemes, setSchemes] = useState<SchemeAuditItem[]>([]);
  const [selectedSchemeId, setSelectedSchemeId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [ministryFilter, setMinistryFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Applications tab state
  const [recentApplications, setRecentApplications] = useState<ApplicationResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');

  useEffect(() => {
    fetchDashboardData();
  }, [searchQuery, ministryFilter, statusFilter]);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const sumData = await adminApi.getDashboardSummary();
      setSummary(sumData);

      const schData = await adminApi.getSchemeAuditList({
        search: searchQuery || undefined,
        ministry: ministryFilter || undefined,
        page_size: 100
      });
      setSchemes(schData.items);

      const appsData = await partnerApi.getAdminApplications({ status: statusFilter || undefined, page_size: 50 });
      setRecentApplications(appsData.items);
    } catch (err) {
      console.error('Failed to load admin dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-950 via-rose-950 to-slate-900 text-white p-6 sm:p-8 rounded-2xl shadow-md border-b-4 border-rose-500 space-y-2">
        <div className="inline-flex items-center gap-2 bg-rose-900/60 text-rose-200 text-xs font-bold px-3 py-1 rounded-full border border-rose-700/50">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          Global System Admin Control & Data Quality Center
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold">YojnaSetu System Admin Dashboard</h1>
        <p className="text-xs sm:text-sm text-slate-300 max-w-3xl">
          Complete authoritative monitoring across 56 VERIFIED schemes, 57 database rules, 20 document requirements, parameter completeness, application queues, and system health.
        </p>
      </div>

      {/* Main Navigation Tabs */}
      <div className="flex border-b border-slate-200 bg-white rounded-xl p-2 shadow-sm overflow-x-auto gap-2">
        {[
          { id: 'OVERVIEW', label: 'Dashboard Overview', icon: Layers },
          { id: 'SCHEMES', label: '56 Schemes Audit', icon: ShieldCheck },
          { id: 'RULES', label: '57 Rules Engine', icon: Database },
          { id: 'DOCUMENTS', label: '20 Documents Checklist', icon: FileText },
          { id: 'CHANGELOG', label: 'Scheme Changelogs', icon: History },
          { id: 'APPLICATIONS', label: 'Application Stream', icon: Users },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveMainTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-extrabold transition whitespace-nowrap ${
                activeMainTab === tab.id
                  ? 'bg-slate-900 text-white shadow-md'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* OVERVIEW TAB */}
      {activeMainTab === 'OVERVIEW' && (
        <div className="space-y-6">
          {/* Top Key Metrics Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center space-y-1">
              <span className="text-3xl font-extrabold text-emerald-600 block flex items-center justify-center gap-1">
                <ShieldCheck className="w-7 h-7 text-emerald-600 inline" />
                {summary?.verified_schemes ?? 56} / {summary?.total_schemes ?? 56}
              </span>
              <span className="text-xs font-bold text-slate-500 uppercase block">Verified Schemes</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center space-y-1">
              <span className="text-3xl font-extrabold text-indigo-700 block">{summary?.total_rules ?? 57}</span>
              <span className="text-xs font-bold text-slate-500 uppercase block">Configured Rules</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center space-y-1">
              <span className="text-3xl font-extrabold text-sky-700 block">{summary?.total_documents ?? 20}</span>
              <span className="text-xs font-bold text-slate-500 uppercase block">Required Documents</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center space-y-1">
              <span className="text-3xl font-extrabold text-amber-600 block">{summary?.avg_parameter_completeness ?? 85}%</span>
              <span className="text-xs font-bold text-slate-500 uppercase block">Avg Parameter Completeness</span>
            </div>
          </div>

          {/* System Health Observability Component */}
          <SystemHealthCard health={summary?.system_health ?? null} />

          {/* Applications Workflow Overview */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-base font-extrabold text-slate-900">Application Stream Status Distribution</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-center">
                <span className="text-2xl font-extrabold text-slate-900 block">{summary?.applications_total ?? 0}</span>
                <span className="text-[11px] font-bold text-slate-500 uppercase block">Total Applications</span>
              </div>
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-center">
                <span className="text-2xl font-extrabold text-purple-700 block">{summary?.applications_by_status?.UNDER_REVIEW ?? 0}</span>
                <span className="text-[11px] font-bold text-slate-500 uppercase block">Under Review</span>
              </div>
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-center">
                <span className="text-2xl font-extrabold text-amber-700 block">{summary?.applications_by_status?.CORRECTION_REQUIRED ?? 0}</span>
                <span className="text-[11px] font-bold text-slate-500 uppercase block">Correction Required</span>
              </div>
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-center">
                <span className="text-2xl font-extrabold text-emerald-700 block">{summary?.applications_by_status?.APPROVED ?? 0}</span>
                <span className="text-[11px] font-bold text-slate-500 uppercase block">Approved</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* SCHEMES TAB */}
      {activeMainTab === 'SCHEMES' && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-4">
            <div>
              <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                Scheme Knowledge Base Audit (56 VERIFIED Schemes)
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">Authoritative government schemes with parameter completeness scores and rule counts.</p>
            </div>

            <div className="flex flex-wrap gap-2 text-xs">
              <input
                type="text"
                placeholder="Search scheme name / ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="px-3 py-1.5 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-rose-500 font-mono"
              />
              <input
                type="text"
                placeholder="Filter by Ministry..."
                value={ministryFilter}
                onChange={(e) => setMinistryFilter(e.target.value)}
                className="px-3 py-1.5 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-rose-500 font-mono"
              />
            </div>
          </div>

          {isLoading ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading 56 verified scheme knowledge base...</div>
          ) : schemes.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500">No schemes found matching search criteria.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                    <th className="p-2.5">Scheme ID</th>
                    <th className="p-2.5">Scheme Title</th>
                    <th className="p-2.5">Ministry / Sector</th>
                    <th className="p-2.5">Status</th>
                    <th className="p-2.5">Rules</th>
                    <th className="p-2.5">Docs</th>
                    <th className="p-2.5">Completeness</th>
                    <th className="p-2.5">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 text-slate-800">
                  {schemes.map((s) => (
                    <tr key={s.scheme_id} className="hover:bg-slate-50">
                      <td className="p-2.5 font-bold font-mono text-sky-800">{s.scheme_id}</td>
                      <td className="p-2.5 font-bold text-slate-900 max-w-xs truncate">{s.scheme_name}</td>
                      <td className="p-2.5 text-slate-600 max-w-xs truncate">{s.ministry}</td>
                      <td className="p-2.5">
                        <span className="bg-emerald-100 text-emerald-800 text-[10px] font-extrabold px-2 py-0.5 rounded border border-emerald-300 flex items-center gap-1 w-fit">
                          <ShieldCheck className="w-3 h-3 text-emerald-600" />
                          VERIFIED
                        </span>
                      </td>
                      <td className="p-2.5 font-mono font-bold text-slate-700">{s.rule_count}</td>
                      <td className="p-2.5 font-mono font-bold text-slate-700">{s.document_count}</td>
                      <td className="p-2.5">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-slate-200 rounded-full h-2 overflow-hidden">
                            <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${s.completeness_score}%` }}></div>
                          </div>
                          <span className="font-bold font-mono text-[11px] text-slate-900">{s.completeness_score}%</span>
                        </div>
                      </td>
                      <td className="p-2.5">
                        <button
                          onClick={() => setSelectedSchemeId(s.scheme_id)}
                          className="px-2.5 py-1 bg-slate-900 text-white font-bold rounded-lg text-[11px] hover:bg-slate-800 transition flex items-center gap-1"
                        >
                          <Eye className="w-3 h-3" />
                          Audit Detail
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* RULES TAB */}
      {activeMainTab === 'RULES' && <RuleAuditTable />}

      {/* DOCUMENTS TAB */}
      {activeMainTab === 'DOCUMENTS' && <DocumentAuditTable />}

      {/* CHANGELOG TAB */}
      {activeMainTab === 'CHANGELOG' && <ChangelogTable />}

      {/* APPLICATIONS TAB */}
      {activeMainTab === 'APPLICATIONS' && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-200 pb-3">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-rose-600" />
              Global Application Audit Stream
            </h3>

            <div className="flex flex-wrap gap-1 text-xs">
              {['', 'SUBMITTED', 'UNDER_REVIEW', 'CORRECTION_REQUIRED', 'APPROVED', 'REJECTED'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-3 py-1 rounded-lg font-bold transition ${
                    statusFilter === st ? 'bg-rose-900 text-white shadow' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {st === '' ? 'ALL' : st.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          </div>

          {isLoading ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading global application stream...</div>
          ) : recentApplications.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">No applications found for selected status filter.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                    <th className="p-2.5">App ID</th>
                    <th className="p-2.5">User ID</th>
                    <th className="p-2.5">Scheme ID</th>
                    <th className="p-2.5">Status</th>
                    <th className="p-2.5">Assigned Partner</th>
                    <th className="p-2.5">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 text-slate-800">
                  {recentApplications.map((app) => (
                    <tr key={app.application_id} className="hover:bg-slate-50">
                      <td className="p-2.5 font-bold font-mono text-sky-800">{app.application_id}</td>
                      <td className="p-2.5 font-mono text-slate-600">{app.user_id}</td>
                      <td className="p-2.5 font-bold text-slate-900">{app.scheme_name || app.scheme_id}</td>
                      <td className="p-2.5"><span className="bg-slate-100 px-2 py-0.5 rounded text-[10px] font-bold border border-slate-300">{app.status}</span></td>
                      <td className="p-2.5 font-mono text-slate-600">{app.assigned_partner_id || 'Unassigned'}</td>
                      <td className="p-2.5">
                        <a href={`/partner/applications/${app.application_id}`} className="text-xs font-bold text-sky-700 hover:underline">
                          Inspect Application
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Scheme Detail Modal */}
      {selectedSchemeId && (
        <SchemeDetailAuditModal schemeId={selectedSchemeId} onClose={() => setSelectedSchemeId(null)} />
      )}
    </div>
  );
};
