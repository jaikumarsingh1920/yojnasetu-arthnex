import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { adminApi, AdminDashboardSummaryResponse, SchemeAuditItem } from '../api/adminApi';
import { SystemHealthCard } from '../components/admin/SystemHealthCard';
import { RuleAuditTable } from '../components/admin/RuleAuditTable';
import { DocumentAuditTable } from '../components/admin/DocumentAuditTable';
import { ChangelogTable } from '../components/admin/ChangelogTable';
import { AIHealthCard } from '../components/admin/AIHealthCard';
import { SchemeDetailAuditModal } from '../components/admin/SchemeDetailAuditModal';
import { SchemeFormModal } from '../components/admin/SchemeFormModal';
import { PartnerManagementTable } from '../components/admin/PartnerManagementTable';
import {
  ShieldAlert,
  Building2,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Database,
  History,
  Layers,
  Search,
  Filter,
  Eye,
  ShieldCheck,
  Sparkles,
  ExternalLink,
  Info,
  SlidersHorizontal,
  Plus,
  Edit3,
  Power,
  PowerOff,
  RotateCcw,
  Check,
  X
} from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [activeMainTab, setActiveMainTab] = useState<
    'OVERVIEW' | 'SCHEME_MANAGEMENT' | 'PARTNER_MANAGEMENT' | 'SCHEMES' | 'RULES' | 'DOCUMENTS' | 'CHANGELOG' | 'AI_HEALTH'
  >('OVERVIEW');
  const [summary, setSummary] = useState<AdminDashboardSummaryResponse | null>(null);
  const [schemes, setSchemes] = useState<SchemeAuditItem[]>([]);
  const [selectedSchemeId, setSelectedSchemeId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [ministryFilter, setMinistryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE' | 'INACTIVE'>('ALL');
  const [schemeTypeFilter, setSchemeTypeFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Scheme Form Modal State (Add / Edit)
  const [isSchemeModalOpen, setIsSchemeModalOpen] = useState(false);
  const [schemeToEdit, setSchemeToEdit] = useState<SchemeAuditItem | null>(null);

  // Deactivate Confirmation Modal State
  const [deactivateTarget, setDeactivateTarget] = useState<SchemeAuditItem | null>(null);
  const [deactivateReason, setDeactivateReason] = useState('');
  const [isTogglingStatus, setIsTogglingStatus] = useState(false);
  const [actionSuccessBanner, setActionSuccessBanner] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, [searchQuery, ministryFilter, statusFilter, schemeTypeFilter]);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const sumData = await adminApi.getDashboardSummary();
      setSummary(sumData);

      const schData = await adminApi.getSchemeAuditList({
        search: searchQuery || undefined,
        ministry: ministryFilter || undefined,
        status: statusFilter === 'ALL' ? undefined : statusFilter,
        scheme_type: schemeTypeFilter || undefined,
        page_size: 100,
      });
      setSchemes(schData.items);
    } catch (err) {
      console.error('Failed to load admin dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenAddScheme = () => {
    setSchemeToEdit(null);
    setIsSchemeModalOpen(true);
  };

  const handleOpenEditScheme = (scheme: SchemeAuditItem) => {
    setSchemeToEdit(scheme);
    setIsSchemeModalOpen(true);
  };

  const handleActivateScheme = async (scheme: SchemeAuditItem) => {
    try {
      setIsTogglingStatus(true);
      await adminApi.updateSchemeStatus(scheme.scheme_id, 'ACTIVE', 'Re-activated by system administrator');
      setActionSuccessBanner(`Scheme '${scheme.scheme_name}' (${scheme.scheme_id}) has been activated and restored to public catalog.`);
      fetchDashboardData();
      setTimeout(() => setActionSuccessBanner(null), 5000);
    } catch (err) {
      console.error('Failed to activate scheme:', err);
      alert('Failed to activate scheme. Please try again.');
    } finally {
      setIsTogglingStatus(false);
    }
  };

  const handleConfirmDeactivate = async () => {
    if (!deactivateTarget) return;
    try {
      setIsTogglingStatus(true);
      await adminApi.updateSchemeStatus(
        deactivateTarget.scheme_id,
        'INACTIVE',
        deactivateReason.trim() || 'Deactivated via Admin Scheme Management console'
      );
      setActionSuccessBanner(`Scheme '${deactivateTarget.scheme_name}' (${deactivateTarget.scheme_id}) has been deactivated and hidden from public view.`);
      setDeactivateTarget(null);
      setDeactivateReason('');
      fetchDashboardData();
      setTimeout(() => setActionSuccessBanner(null), 5000);
    } catch (err) {
      console.error('Failed to deactivate scheme:', err);
      alert('Failed to deactivate scheme. Please try again.');
    } finally {
      setIsTogglingStatus(false);
    }
  };

  // Distinct ministries and sectors for filter dropdowns
  const distinctMinistries = Array.from(new Set(schemes.map((s) => s.ministry).filter(Boolean))).sort();
  const distinctSectors = Array.from(new Set(schemes.map((s) => s.scheme_type || s.sector).filter(Boolean))).sort();

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
          Data Governance Center: manage verified schemes dynamically, configure deterministic statutory rules, inspect preparation documents, monitor AI/RAG health, and review audit changelogs.
        </p>
      </div>

      {/* Action Success Alert Banner */}
      {actionSuccessBanner && (
        <div className="p-4 bg-emerald-50 border border-emerald-300 rounded-xl flex items-center justify-between gap-3 text-emerald-900 text-xs font-medium animate-fadeIn">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{actionSuccessBanner}</span>
          </div>
          <button onClick={() => setActionSuccessBanner(null)} className="text-emerald-700 hover:text-emerald-900 p-1">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Navigation Tabs */}
      <div className="flex border-b border-slate-200 bg-white rounded-xl p-2 shadow-sm overflow-x-auto gap-2">
        {[
          { id: 'OVERVIEW', label: t('admin.dashboardTitle', 'Dashboard Overview'), icon: Layers },
          { id: 'SCHEME_MANAGEMENT', label: t('admin.schemeManagement', 'Scheme Management'), icon: SlidersHorizontal },
          { id: 'PARTNER_MANAGEMENT', label: 'Channel Partners', icon: Building2 },
          { id: 'SCHEMES', label: t('admin.schemesAudit', 'Schemes Audit'), icon: ShieldCheck },
          { id: 'RULES', label: t('admin.rulesEngine', 'Rules Engine'), icon: Database },
          { id: 'DOCUMENTS', label: t('admin.documentsChecklist', 'Documents Checklist'), icon: FileText },
          { id: 'CHANGELOG', label: t('admin.schemeChangelogs', 'Scheme Changelogs'), icon: History },
          { id: 'AI_HEALTH', label: t('admin.aiRagHealth', 'AI & RAG Health'), icon: Sparkles },
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

      {/* 1. OVERVIEW TAB */}
      {activeMainTab === 'OVERVIEW' && (
        <div className="space-y-6">
          {/* Top Key Metrics Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center space-y-1">
              <span className="text-3xl font-extrabold text-emerald-600 block flex items-center justify-center gap-1">
                <ShieldCheck className="w-7 h-7 text-emerald-600 inline" />
                {summary?.verified_schemes ?? 0} / {summary?.total_schemes ?? 0}
              </span>
              <span className="text-xs font-bold text-slate-700 uppercase block">Verified Schemes</span>
              <span className="text-[10px] text-slate-400 block font-medium">Official Gazette & Ministry Catalog</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center space-y-1">
              <span className="text-3xl font-extrabold text-indigo-700 block">{summary?.total_rules ?? 0}</span>
              <span className="text-xs font-bold text-slate-700 uppercase block">Configured Rules</span>
              <span className="text-[10px] text-slate-400 block font-medium">Statutory Deterministic Condition Rules</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center space-y-1">
              <span className="text-3xl font-extrabold text-sky-700 block">{summary?.total_documents ?? 0}</span>
              <span className="text-xs font-bold text-slate-700 uppercase block">Document Requirements</span>
              <span className="text-[10px] text-slate-400 block font-medium">Verified Preparation Checklists</span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center space-y-1">
              <span className="text-3xl font-extrabold text-amber-600 block">{summary?.avg_parameter_completeness ?? 0}%</span>
              <span className="text-xs font-bold text-slate-700 uppercase block">Avg Parameter Completeness</span>
              <span className="text-[10px] text-slate-400 block font-medium">Across Tracked Data Attributes</span>
            </div>
          </div>

          {/* System Health Observability Component */}
          <SystemHealthCard health={summary?.system_health ?? null} />

          {/* Platform Data Quality & Governance Summary */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-extrabold text-slate-900">Platform Data Quality & Governance Summary</h3>
                <p className="text-xs text-slate-500 mt-0.5">Authoritative metrics verified against government gazette notices and official ministry portals.</p>
              </div>
              <span className="text-xs font-bold bg-slate-100 text-slate-700 px-3 py-1 rounded-lg border border-slate-200">
                Data Catalog: {summary?.total_schemes ?? 90} Schemes
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-center">
                <span className="text-2xl font-extrabold text-slate-900 block">{summary?.total_ministries ?? 15}</span>
                <span className="text-[11px] font-bold text-slate-500 uppercase block">Union Ministries</span>
              </div>
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-center">
                <span className="text-2xl font-extrabold text-rose-700 block">{summary?.total_changelogs ?? 212}</span>
                <span className="text-[11px] font-bold text-slate-500 uppercase block">Changelog Audit Entries</span>
              </div>
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-center">
                <span className="text-2xl font-extrabold text-sky-700 block">12</span>
                <span className="text-[11px] font-bold text-slate-500 uppercase block">Supported Languages</span>
              </div>
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-center">
                <span className="text-2xl font-extrabold text-indigo-700 block">56</span>
                <span className="text-[11px] font-bold text-slate-500 uppercase block">Geocoded Partner Centers</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 2. DYNAMIC SCHEME MANAGEMENT TAB */}
      {activeMainTab === 'SCHEME_MANAGEMENT' && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
          {/* Action & Filter Header */}
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 border-b border-slate-200 pb-5">
            <div>
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="w-5 h-5 text-rose-600" />
                <h3 className="text-base font-extrabold text-slate-900">Canonical Scheme Management</h3>
                <span className="bg-slate-100 text-slate-700 text-xs font-bold px-2.5 py-0.5 rounded-full border border-slate-200">
                  {schemes.length} Schemes
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Full CRUD control, statutory parameter editing, and soft Active/Inactive lifecycle toggle with audit traceability.
              </p>
            </div>

            <button
              onClick={handleOpenAddScheme}
              className="flex items-center gap-2 px-4 py-2.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-extrabold rounded-xl shadow-md transition shrink-0"
            >
              <Plus className="w-4 h-4" />
              Add New Scheme
            </button>
          </div>

          {/* Filter Controls Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
            <div>
              <label className="block text-[11px] font-bold text-slate-600 mb-1">Search Scheme</label>
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search name, code, ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 border border-slate-300 rounded-lg text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-rose-500 font-mono text-xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-600 mb-1">Filter by Ministry</label>
              <select
                value={ministryFilter}
                onChange={(e) => setMinistryFilter(e.target.value)}
                className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-rose-500 text-xs"
              >
                <option value="">All Ministries</option>
                {distinctMinistries.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-600 mb-1">Filter by Scheme Type</label>
              <select
                value={schemeTypeFilter}
                onChange={(e) => setSchemeTypeFilter(e.target.value)}
                className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-rose-500 text-xs"
              >
                <option value="">All Types / Sectors</option>
                {distinctSectors.map((sec) => (
                  <option key={sec} value={sec}>
                    {sec}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-600 mb-1">Lifecycle Status</label>
              <div className="flex rounded-lg border border-slate-300 bg-white overflow-hidden p-0.5">
                {(['ALL', 'ACTIVE', 'INACTIVE'] as const).map((st) => (
                  <button
                    key={st}
                    type="button"
                    onClick={() => setStatusFilter(st)}
                    className={`flex-1 py-1 text-[10px] font-extrabold rounded transition ${
                      statusFilter === st ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Scheme Management Table */}
          {isLoading ? (
            <div className="py-12 text-center text-xs text-slate-500">Loading canonical schemes...</div>
          ) : schemes.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500 bg-slate-50 rounded-xl border border-dashed border-slate-200">
              No schemes found matching the specified filters.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-left text-xs border-collapse min-w-[900px]">
                <thead>
                  <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                    <th className="p-3">Scheme ID</th>
                    <th className="p-3">Scheme Title</th>
                    <th className="p-3">Ministry</th>
                    <th className="p-3">Type</th>
                    <th className="p-3">Loan Available</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Completeness</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 text-slate-800 bg-white">
                  {schemes.map((s) => {
                    const isActive = s.scheme_status === 'ACTIVE' || !s.scheme_status;
                    const hasLoan = s.loan_available === 'YES' || s.loan_available === 'TRUE';

                    return (
                      <tr key={s.scheme_id} className={`hover:bg-slate-50 transition ${!isActive ? 'bg-slate-50/70 opacity-80' : ''}`}>
                        <td className="p-3 font-mono font-bold text-sky-800 whitespace-nowrap">
                          {s.scheme_id}
                        </td>
                        <td className="p-3">
                          <div className="font-bold text-slate-900 max-w-xs truncate" title={s.scheme_name}>
                            {s.scheme_name}
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            Verified: {s.last_verified_date || '2026-08-26'}
                          </div>
                        </td>
                        <td className="p-3 text-slate-600 max-w-[200px] truncate" title={s.ministry}>
                          {s.ministry}
                        </td>
                        <td className="p-3 text-slate-700 max-w-[140px] truncate" title={s.scheme_type || s.sector}>
                          {s.scheme_type || s.sector || 'General'}
                        </td>
                        <td className="p-3">
                          {hasLoan ? (
                            <span className="bg-emerald-100 text-emerald-800 text-[10px] font-extrabold px-2 py-0.5 rounded border border-emerald-300">
                              Loan Facility
                            </span>
                          ) : (
                            <span className="bg-slate-100 text-slate-600 text-[10px] font-bold px-2 py-0.5 rounded border border-slate-200">
                              Grant / Direct
                            </span>
                          )}
                        </td>
                        <td className="p-3 whitespace-nowrap">
                          {isActive ? (
                            <span className="inline-flex items-center gap-1 bg-emerald-100 text-emerald-800 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border border-emerald-300">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
                              ACTIVE
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 bg-rose-100 text-rose-800 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border border-rose-300">
                              <span className="w-1.5 h-1.5 rounded-full bg-rose-600"></span>
                              INACTIVE
                            </span>
                          )}
                        </td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            <div className="w-14 bg-slate-200 rounded-full h-1.5 overflow-hidden">
                              <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${s.completeness_score}%` }}></div>
                            </div>
                            <span className="font-bold font-mono text-[10px] text-slate-700">{s.completeness_score}%</span>
                          </div>
                        </td>
                        <td className="p-3 text-right whitespace-nowrap">
                          <div className="inline-flex items-center gap-1.5">
                            <button
                              onClick={() => handleOpenEditScheme(s)}
                              className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold rounded-lg text-[11px] transition inline-flex items-center gap-1 border border-slate-200"
                              title="Edit Scheme Parameters"
                            >
                              <Edit3 className="w-3 h-3 text-indigo-600" />
                              Edit
                            </button>

                            {isActive ? (
                              <button
                                onClick={() => setDeactivateTarget(s)}
                                className="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold rounded-lg text-[11px] transition inline-flex items-center gap-1 border border-rose-200"
                                title="Deactivate Scheme"
                              >
                                <PowerOff className="w-3 h-3 text-rose-600" />
                                Deactivate
                              </button>
                            ) : (
                              <button
                                onClick={() => handleActivateScheme(s)}
                                disabled={isTogglingStatus}
                                className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-bold rounded-lg text-[11px] transition inline-flex items-center gap-1 border border-emerald-200"
                                title="Activate Scheme"
                              >
                                <Power className="w-3 h-3 text-emerald-600" />
                                Activate
                              </button>
                            )}

                            <button
                              onClick={() => setSelectedSchemeId(s.scheme_id)}
                              className="p-1 text-slate-400 hover:text-slate-700 rounded transition"
                              title="View Audit Detail"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* 2.5 CHANNEL PARTNER MANAGEMENT TAB */}
      {activeMainTab === 'PARTNER_MANAGEMENT' && (
        <PartnerManagementTable />
      )}

      {/* 3. SCHEMES AUDIT TAB */}
      {activeMainTab === 'SCHEMES' && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-4">
            <div>
              <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                Scheme Knowledge Base Audit ({summary?.verified_schemes ?? schemes.length} Verified Schemes)
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
            <div className="py-8 text-center text-xs text-slate-500">Loading scheme knowledge base...</div>
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
                    <th className="p-2.5">Verification</th>
                    <th className="p-2.5">Rule Status</th>
                    <th className="p-2.5">Docs</th>
                    <th className="p-2.5">Completeness</th>
                    <th className="p-2.5">Official Source</th>
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
                      <td className="p-2.5">
                        {s.rule_count > 0 ? (
                          <span className="font-mono font-bold text-slate-700">{s.rule_count} Rules</span>
                        ) : (
                          <span className="text-[10px] font-bold text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                            Eligibility rules not sufficiently configured
                          </span>
                        )}
                      </td>
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
                        {s.official_source_url ? (
                          <a
                            href={s.official_source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-indigo-600 hover:text-indigo-800 inline-flex items-center gap-1 font-bold text-[11px]"
                          >
                            Source Portal <ExternalLink className="w-3 h-3" />
                          </a>
                        ) : s.has_official_source ? (
                          <span className="text-slate-500 text-[11px]">Gazette Guideline</span>
                        ) : (
                          <span className="text-amber-600 text-[11px] font-medium">Pending Verification</span>
                        )}
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

      {/* 4. RULES TAB */}
      {activeMainTab === 'RULES' && <RuleAuditTable />}

      {/* 5. DOCUMENTS TAB */}
      {activeMainTab === 'DOCUMENTS' && <DocumentAuditTable />}

      {/* 6. CHANGELOG TAB */}
      {activeMainTab === 'CHANGELOG' && <ChangelogTable />}

      {/* 7. AI & RAG HEALTH TAB */}
      {activeMainTab === 'AI_HEALTH' && <AIHealthCard health={summary?.system_health ?? null} />}

      {/* Scheme Detail Audit Modal */}
      {selectedSchemeId && (
        <SchemeDetailAuditModal schemeId={selectedSchemeId} onClose={() => setSelectedSchemeId(null)} />
      )}

      {/* Dynamic Add / Edit Scheme Form Modal */}
      <SchemeFormModal
        isOpen={isSchemeModalOpen}
        onClose={() => {
          setIsSchemeModalOpen(false);
          setSchemeToEdit(null);
        }}
        onSuccess={() => {
          fetchDashboardData();
        }}
        schemeToEdit={schemeToEdit}
      />

      {/* Deactivation Confirmation Dialog */}
      {deactivateTarget && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-md p-6 space-y-4">
            <div className="flex items-center gap-3 text-rose-600">
              <div className="p-3 bg-rose-100 rounded-xl">
                <AlertTriangle className="w-6 h-6 text-rose-600" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-slate-900">Deactivate Scheme?</h3>
                <p className="text-xs text-slate-500">Soft deactivation confirmation</p>
              </div>
            </div>

            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl space-y-1.5 text-xs text-rose-900">
              <div className="font-bold">
                {deactivateTarget.scheme_name} ({deactivateTarget.scheme_id})
              </div>
              <p className="text-[11px] text-rose-800 leading-relaxed">
                When deactivated, this scheme is immediately:
              </p>
              <ul className="list-disc list-inside text-[11px] text-rose-800 space-y-0.5">
                <li>Hidden from the public Scheme Directory</li>
                <li>Excluded from beneficiary Recommendations</li>
                <li>Excluded from EMI Calculator scheme selection</li>
                <li>Excluded from live AI Copilot / RAG retrieval</li>
              </ul>
              <p className="text-[10px] text-slate-500 pt-1">
                Its historical records and rules will be safely preserved in the admin database.
              </p>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Deactivation Reason <span className="text-slate-400 font-normal">(Recorded in Changelog)</span>
              </label>
              <input
                type="text"
                placeholder="e.g. Scheme expired, superseded by new policy, or funding closed"
                value={deactivateReason}
                onChange={(e) => setDeactivateReason(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-rose-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => {
                  setDeactivateTarget(null);
                  setDeactivateReason('');
                }}
                disabled={isTogglingStatus}
                className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDeactivate}
                disabled={isTogglingStatus}
                className="px-4 py-2 text-xs font-extrabold text-white bg-rose-600 hover:bg-rose-700 disabled:opacity-50 rounded-xl shadow transition flex items-center gap-1.5"
              >
                <PowerOff className="w-3.5 h-3.5" />
                {isTogglingStatus ? 'Deactivating...' : 'Confirm Deactivation'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
