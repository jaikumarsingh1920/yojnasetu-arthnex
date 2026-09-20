import React, { useState, useEffect } from 'react';
import { adminApi } from '../../api/adminApi';
import {
  SourceResponse,
  IngestionQualityMetricsResponse,
  DiscoveryBatchRunResponse,
  SchedulerStatusResponse,
} from '../../types';
import {
  Activity,
  Cpu,
  RefreshCw,
  Play,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Database,
  ShieldCheck,
  Building2,
  ExternalLink,
  Zap,
  Clock,
  Sparkles,
  ArrowRight,
  GitBranch,
  Search,
  Filter,
  Radio,
  Power,
  Info,
  Check,
  X,
  FileText,
  AlertCircle
} from 'lucide-react';

interface IngestionGovernanceViewProps {
  onNavigateToPending?: () => void;
}

export const IngestionGovernanceView: React.FC<IngestionGovernanceViewProps> = ({ onNavigateToPending }) => {
  const [scheduler, setScheduler] = useState<SchedulerStatusResponse | null>(null);
  const [metrics, setMetrics] = useState<IngestionQualityMetricsResponse | null>(null);
  const [sources, setSources] = useState<SourceResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRunningDiscovery, setIsRunningDiscovery] = useState<boolean>(false);
  const [runningSourceId, setRunningSourceId] = useState<string | null>(null);
  const [actionAlert, setActionAlert] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  // Manual Ingestion Run Modal State
  const [isTriggerModalOpen, setIsTriggerModalOpen] = useState<boolean>(false);
  const [forceUpdate, setForceUpdate] = useState<boolean>(false);
  const [isTriggering, setIsTriggering] = useState<boolean>(false);

  // Source filters
  const [sourceFilter, setSourceFilter] = useState<'ALL' | 'HEALTHY' | 'DEGRADED' | 'FAILED'>('ALL');
  const [sourceSearch, setSourceSearch] = useState<string>('');

  useEffect(() => {
    loadGovernanceData();
  }, []);

  const loadGovernanceData = async () => {
    setIsLoading(true);
    try {
      const [schedulerData, metricsData, sourcesData] = await Promise.all([
        adminApi.getSchedulerStatus().catch((err) => {
          console.warn('Failed to load scheduler status:', err);
          return null;
        }),
        adminApi.getQualityMetrics().catch(() => null),
        adminApi.getSources().catch(() => []),
      ]);
      if (schedulerData) setScheduler(schedulerData);
      if (metricsData) setMetrics(metricsData);
      setSources(sourcesData || []);
    } catch (err: any) {
      console.error('Failed to load governance data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTriggerSchedulerRun = async () => {
    setIsTriggering(true);
    setActionAlert(null);

    const isDemo =
      typeof window !== 'undefined' &&
      (sessionStorage.getItem('yojnasetu_demo_admin_authenticated') === 'true' ||
        window.location.pathname.includes('demo'));

    if (isDemo) {
      setTimeout(() => {
        setIsTriggerModalOpen(false);
        setActionAlert({
          type: 'success',
          text: `✨ [DEMO SANDBOX] Automated Gazette monitoring run simulated! Discovered: 3 staged updates, 2 source revisions. Production database preserved.`,
        });
        setIsTriggering(false);
        setTimeout(() => setActionAlert(null), 8000);
      }, 700);
      return;
    }

    try {
      const res = await adminApi.triggerSchedulerRun(forceUpdate);
      setIsTriggerModalOpen(false);
      setActionAlert({
        type: 'success',
        text: `Automated monitoring run initiated: status is '${res?.status || 'STARTED'}'. Discovered: ${res?.records_staged ?? 0} staged updates, ${res?.records_changed ?? 0} changed sources.`,
      });
      loadGovernanceData();
      setTimeout(() => setActionAlert(null), 9000);
    } catch (err: any) {
      console.error('Manual scheduler trigger error:', err);
      setActionAlert({
        type: 'error',
        text: err?.response?.data?.detail || 'Failed to trigger on-demand monitoring cycle.',
      });
    } finally {
      setIsTriggering(false);
    }
  };

  const handleRunDiscoveryBatch = async () => {
    setIsRunningDiscovery(true);
    setActionAlert(null);

    const isDemo =
      typeof window !== 'undefined' &&
      (sessionStorage.getItem('yojnasetu_demo_admin_authenticated') === 'true' ||
        window.location.pathname.includes('demo'));

    if (isDemo) {
      setTimeout(() => {
        setActionAlert({
          type: 'success',
          text: `✨ [DEMO SANDBOX] Scheme discovery batch simulated in preview! Discovered: 12 schemes, Staged: 4, Filtered: 8.`,
        });
        setIsRunningDiscovery(false);
        setTimeout(() => setActionAlert(null), 8000);
      }, 700);
      return;
    }

    try {
      const res = await adminApi.runDiscoveryBatch({ max_candidates: 25 });
      setActionAlert({
        type: 'success',
        text: `Discovery batch completed! Discovered: ${res.discovered}, Staged: ${res.staged_for_review}, Duplicates: ${res.duplicates_filtered}.`,
      });
      loadGovernanceData();
      setTimeout(() => setActionAlert(null), 8000);
    } catch (err: any) {
      console.error('Discovery batch error:', err);
      setActionAlert({
        type: 'error',
        text: err?.response?.data?.detail || 'Failed to trigger discovery batch run.',
      });
    } finally {
      setIsRunningDiscovery(false);
    }
  };

  const handleRunSource = async (sourceId: string) => {
    setRunningSourceId(sourceId);
    setActionAlert(null);

    const isDemo =
      typeof window !== 'undefined' &&
      (sessionStorage.getItem('yojnasetu_demo_admin_authenticated') === 'true' ||
        window.location.pathname.includes('demo'));

    if (isDemo) {
      setTimeout(() => {
        setActionAlert({
          type: 'success',
          text: `✨ [DEMO SANDBOX] Ingestion pipeline for source '${sourceId}' simulated successfully (100% verified).`,
        });
        setRunningSourceId(null);
        setTimeout(() => setActionAlert(null), 8000);
      }, 700);
      return;
    }

    try {
      const res = await adminApi.runIngestion(sourceId);
      setActionAlert({
        type: 'success',
        text: `Pipeline run on source '${sourceId}' completed with status: ${res.status || res.change_status}. Discovered changes: ${res.detected_change_count ?? 0}.`,
      });
      loadGovernanceData();
      setTimeout(() => setActionAlert(null), 8000);
    } catch (err: any) {
      console.error('Source run error:', err);
      setActionAlert({
        type: 'error',
        text: err?.response?.data?.detail || `Failed to run pipeline for source '${sourceId}'.`,
      });
    } finally {
      setRunningSourceId(null);
    }
  };

  // Filter sources
  const filteredSources = sources.filter((src) => {
    const matchesFilter =
      sourceFilter === 'ALL'
        ? true
        : sourceFilter === 'HEALTHY'
        ? (src.health_status === 'HEALTHY' || (!src.health_status && src.last_status === 'SUCCESS'))
        : sourceFilter === 'DEGRADED'
        ? src.health_status === 'DEGRADED'
        : (src.health_status === 'FAILED' || src.last_status === 'FAILED' || (src.consecutive_failures ?? 0) > 0);

    if (!matchesFilter) return false;

    if (!sourceSearch.trim()) return true;
    const q = sourceSearch.toLowerCase();
    return (
      (src.source_name && src.source_name.toLowerCase().includes(q)) ||
      (src.source_id && src.source_id.toLowerCase().includes(q)) ||
      (src.authority && src.authority.toLowerCase().includes(q)) ||
      (src.source_url && src.source_url.toLowerCase().includes(q))
    );
  });

  const isSchedulerExecuting = scheduler?.is_executing_cycle;
  const isSchedulerActive = scheduler?.is_running || scheduler?.scheduler_enabled;
  const cadenceDisplay = scheduler?.interval_hours ? `Every ${scheduler.interval_hours} hours` : 'Every 24 hours';
  const pendingCount = scheduler?.pending_updates_count ?? 0;

  return (
    <div className="space-y-6">
      {/* Action Alert Banner */}
      {actionAlert && (
        <div
          className={`p-4 rounded-2xl border text-xs font-semibold flex items-center justify-between gap-3 animate-fadeIn ${
            actionAlert.type === 'success'
              ? 'bg-emerald-50 text-emerald-900 border-emerald-300'
              : actionAlert.type === 'info'
              ? 'bg-sky-50 text-sky-900 border-sky-300'
              : 'bg-rose-50 text-rose-900 border-rose-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {actionAlert.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : actionAlert.type === 'info' ? (
              <Info className="w-4 h-4 text-sky-600 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span>{actionAlert.text}</span>
          </div>
          <button onClick={() => setActionAlert(null)} className="text-slate-500 hover:text-slate-800 font-bold px-1">
            ✕
          </button>
        </div>
      )}

      {/* 1. AUTOMATED MONITORING & 24-HOUR SCHEDULER TELEMETRY */}
      <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-6 shadow-md border border-indigo-900/50 space-y-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-indigo-800/40 pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="bg-indigo-500/20 text-indigo-300 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider border border-indigo-400/30 flex items-center gap-1.5">
                <Radio className={`w-3 h-3 ${isSchedulerExecuting ? 'text-amber-400 animate-pulse' : 'text-emerald-400'}`} />
                Automated Scheme Monitoring
              </span>
              <span className="text-xs text-indigo-200 font-semibold">
                Cadence: {cadenceDisplay}
              </span>
            </div>
            <h2 className="text-xl font-black text-white flex items-center gap-2">
              <Cpu className="w-6 h-6 text-indigo-400" />
              Dynamic Ingestion Scheduler & Provenance Engine
            </h2>
            <p className="text-xs text-slate-300 max-w-2xl">
              Monitors official gazettes, ministry portals, and scheme rule documents continuously on a 24-hour cycle. Detects field-level diffs and stages verified updates for administrative review.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <button
              type="button"
              onClick={loadGovernanceData}
              disabled={isLoading}
              className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl border border-slate-700 transition flex items-center gap-1.5 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Refresh Telemetry</span>
            </button>

            <button
              type="button"
              onClick={() => setIsTriggerModalOpen(true)}
              disabled={isSchedulerExecuting}
              className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-extrabold rounded-xl shadow-md transition flex items-center gap-1.5 disabled:opacity-50"
            >
              <Zap className={`w-3.5 h-3.5 ${isSchedulerExecuting ? 'animate-spin' : ''}`} />
              <span>{isSchedulerExecuting ? 'Executing Cycle...' : 'Run Monitoring Now'}</span>
            </button>
          </div>
        </div>

        {/* Live Scheduler Key Telemetry Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {/* Status */}
          <div className="p-3.5 rounded-xl bg-slate-800/80 border border-indigo-800/40 text-center space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Scheduler State</span>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-black">
              <span className={`w-2 h-2 rounded-full ${isSchedulerExecuting ? 'bg-amber-400 animate-ping' : isSchedulerActive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`}></span>
              <span className={isSchedulerExecuting ? 'text-amber-300' : isSchedulerActive ? 'text-emerald-300' : 'text-slate-400'}>
                {isSchedulerExecuting ? 'CYCLE RUNNING' : isSchedulerActive ? 'ACTIVE' : 'IDLE'}
              </span>
            </div>
          </div>

          {/* Cadence */}
          <div className="p-3.5 rounded-xl bg-slate-800/80 border border-indigo-800/40 text-center space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Cadence</span>
            <span className="text-sm font-black text-indigo-300 block">{cadenceDisplay}</span>
            <span className="text-[10px] text-slate-400 block">Periodic automated scan</span>
          </div>

          {/* Last Run */}
          <div className="p-3.5 rounded-xl bg-slate-800/80 border border-indigo-800/40 text-center space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Last Check</span>
            <span className="text-xs font-bold text-white block truncate">
              {scheduler?.last_run_time ? new Date(scheduler.last_run_time).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' }) : 'Recently completed'}
            </span>
            <span className="text-[10px] font-mono text-emerald-400 block">Status: {scheduler?.last_run_status || 'SUCCESS'}</span>
          </div>

          {/* Next Scheduled Run */}
          <div className="p-3.5 rounded-xl bg-slate-800/80 border border-indigo-800/40 text-center space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Next Check</span>
            <span className="text-xs font-bold text-sky-300 block truncate">
              {scheduler?.next_scheduled_run ? new Date(scheduler.next_scheduled_run).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' }) : 'Within 24 hours'}
            </span>
            <span className="text-[10px] text-slate-400 block">Automatic Trigger</span>
          </div>

          {/* Configured Sources */}
          <div className="p-3.5 rounded-xl bg-slate-800/80 border border-indigo-800/40 text-center space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Sources Tracked</span>
            <span className="text-xl font-black text-indigo-200 block font-mono">
              {scheduler?.sources_summary?.total_sources ?? sources.length}
            </span>
            <span className="text-[10px] text-emerald-400 block font-medium">
              {scheduler?.sources_summary?.healthy_sources ?? sources.filter(s => s.health_status === 'HEALTHY').length} Healthy
            </span>
          </div>

          {/* Pending Reviews */}
          <div className="p-3.5 rounded-xl bg-indigo-900/60 border border-indigo-500/40 text-center space-y-1">
            <span className="text-[10px] font-bold text-indigo-200 uppercase tracking-wider block">Pending Reviews</span>
            <span className="text-xl font-black text-amber-300 block font-mono">
              {pendingCount}
            </span>
            <span className="text-[10px] text-indigo-300 block">
              {pendingCount > 0 ? 'Awaiting Human-in-the-Loop' : 'Fully Synchronized'}
            </span>
          </div>
        </div>

        {/* Pending Reviews Action Callout (if updates pending) */}
        {pendingCount > 0 && onNavigateToPending && (
          <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 text-xs text-amber-200">
              <AlertCircle className="w-5 h-5 text-amber-400 shrink-0" />
              <span>
                <strong>{pendingCount} scheme update proposal{pendingCount > 1 ? 's' : ''}</strong> detected by the monitoring engine require administrative review before canonical catalog promotion.
              </span>
            </div>
            <button
              type="button"
              onClick={onNavigateToPending}
              className="px-3.5 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-extrabold text-xs rounded-lg transition flex items-center gap-1 shrink-0"
            >
              <span>Review Pending Diffs</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* 2. VISUAL SMART AUTOMATION ARCHITECTURE FLOW */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-indigo-100 text-indigo-800 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                Smart Scheme Automation
              </span>
              <span className="text-xs text-slate-500 font-semibold">Continuous Ingestion & Governance Architecture</span>
            </div>
            <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-indigo-600" />
              End-to-End Scheme Lifecycle & Provenance Pipeline
            </h2>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={handleRunDiscoveryBatch}
              disabled={isRunningDiscovery}
              className="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 font-bold text-xs px-3.5 py-2 rounded-xl transition flex items-center gap-1.5 disabled:opacity-50"
            >
              <Sparkles className={`w-3.5 h-3.5 ${isRunningDiscovery ? 'animate-spin text-indigo-600' : ''}`} />
              <span>{isRunningDiscovery ? 'Discovering...' : 'Run Candidate Discovery'}</span>
            </button>
          </div>
        </div>

        {/* Visual Pipeline Flow Steps */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 pt-1">
          {[
            { step: '1. MONITOR', desc: 'Govt Gazette & Portals (24h)', color: 'bg-sky-50 text-sky-900 border-sky-200' },
            { step: '2. SNAPSHOT', desc: 'Immutable SHA-256 Hashing', color: 'bg-indigo-50 text-indigo-900 border-indigo-200' },
            { step: '3. DIFF ENGINE', desc: 'Field-Level Change Detection', color: 'bg-purple-50 text-purple-900 border-purple-200' },
            { step: '4. EXTRACT', desc: 'Normalized Schema Parameters', color: 'bg-teal-50 text-teal-900 border-teal-200' },
            { step: '5. VALIDATE', desc: 'Deterministic Rules Check', color: 'bg-amber-50 text-amber-900 border-amber-200' },
            { step: '6. STAGE', desc: 'Pending Updates Table', color: 'bg-orange-50 text-orange-900 border-orange-200' },
            { step: '7. ADMIN REVIEW', desc: 'Human-in-the-Loop Verdict', color: 'bg-emerald-50 text-emerald-900 border-emerald-200' },
            { step: '8. PROMOTION', desc: 'Canonical DB & Vector RAG', color: 'bg-blue-50 text-blue-900 border-blue-200' },
          ].map((s, idx) => (
            <div key={idx} className={`p-3 rounded-xl border text-center space-y-1 ${s.color}`}>
              <span className="text-[10px] font-black uppercase block tracking-wider">{s.step}</span>
              <p className="text-[10px] leading-tight text-slate-600 font-medium">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 3. SOURCE MONITORING TABLE */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-slate-100 text-slate-700 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                Source Health Monitor
              </span>
              <span className="text-xs text-slate-500 font-semibold">
                {sources.length} Configured Government Endpoints
              </span>
            </div>
            <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
              <Database className="w-5 h-5 text-indigo-600" />
              Official Government Scheme Sources & Ingestion Health
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Live tracking of authoritative ministry portals, official Gazette notifications, and statutory scheme guideline pages.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
            {/* Search Input */}
            <div className="relative flex-1 sm:w-64">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search source or ministry..."
                value={sourceSearch}
                onChange={(e) => setSourceSearch(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-900 outline-none focus:border-gov-blue"
              />
            </div>

            {/* Health Filter */}
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value as any)}
              className="bg-slate-50 border border-slate-300 rounded-xl px-3 py-1.5 text-xs text-slate-900 font-bold outline-none focus:border-gov-blue"
            >
              <option value="ALL">All Sources ({sources.length})</option>
              <option value="HEALTHY">Healthy ({sources.filter(s => s.health_status === 'HEALTHY' || (!s.health_status && s.last_status === 'SUCCESS')).length})</option>
              <option value="DEGRADED">Degraded ({sources.filter(s => s.health_status === 'DEGRADED').length})</option>
              <option value="FAILED">Failed / Outage ({sources.filter(s => s.health_status === 'FAILED' || s.last_status === 'FAILED' || (s.consecutive_failures ?? 0) > 0).length})</option>
            </select>
          </div>
        </div>

        {/* Source Isolation Callout Banner */}
        <div className="p-3 bg-sky-50 border border-sky-200 rounded-xl flex items-start gap-2.5 text-xs text-sky-900">
          <Info className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
          <p className="text-[11px] leading-relaxed">
            <strong>Source Outage Isolation Guarantee:</strong> Network timeouts or fetch errors on an external source do <strong>NOT</strong> mark canonical schemes as inactive or withdrawn. Outages are isolated to protect citizen accessibility. Only explicit official closure notices produce deactivation proposals.
          </p>
        </div>

        {/* Sources Table */}
        {isLoading ? (
          <div className="py-12 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
            <RefreshCw className="w-5 h-5 animate-spin text-indigo-600" />
            <span>Loading registered official sources...</span>
          </div>
        ) : filteredSources.length === 0 ? (
          <div className="py-12 bg-slate-50 border border-dashed border-slate-200 rounded-xl text-center text-xs text-slate-500">
            No registered scheme sources match the selected criteria.
          </div>
        ) : (
          <div className="overflow-x-auto border border-slate-200 rounded-xl">
            <table className="w-full text-left text-xs border-collapse divide-y divide-slate-200">
              <thead className="bg-slate-50 text-[10px] font-extrabold uppercase text-slate-600 tracking-wider">
                <tr>
                  <th className="py-3 px-3.5">Source & ID</th>
                  <th className="py-3 px-3.5">Authority / Ministry</th>
                  <th className="py-3 px-3.5">Endpoint URL</th>
                  <th className="py-3 px-3.5">Format</th>
                  <th className="py-3 px-3.5">Cadence</th>
                  <th className="py-3 px-3.5">Last Checked</th>
                  <th className="py-3 px-3.5">Health State</th>
                  <th className="py-3 px-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {filteredSources.map((source) => {
                  const isRunning = runningSourceId === source.source_id;
                  const isHealthy = source.health_status === 'HEALTHY' || (!source.health_status && source.last_status === 'SUCCESS');
                  const isDegraded = source.health_status === 'DEGRADED';
                  const isFailed = source.health_status === 'FAILED' || source.last_status === 'FAILED' || (source.consecutive_failures ?? 0) > 0;

                  return (
                    <tr key={source.source_id} className="hover:bg-slate-50/80 transition">
                      <td className="py-3 px-3.5">
                        <div className="font-bold text-slate-900">{source.source_name}</div>
                        <div className="font-mono text-[10px] text-slate-400">{source.source_id}</div>
                      </td>

                      <td className="py-3 px-3.5">
                        <span className="text-[11px] font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 inline-block max-w-xs truncate">
                          {source.authority || 'Central Government Ministry'}
                        </span>
                      </td>

                      <td className="py-3 px-3.5 max-w-xs truncate">
                        {source.source_url ? (
                          <a
                            href={source.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-gov-blue hover:underline font-mono text-[11px] flex items-center gap-1"
                            title={source.source_url}
                          >
                            <span className="truncate">{source.source_url}</span>
                            <ExternalLink className="w-3 h-3 shrink-0" />
                          </a>
                        ) : (
                          <span className="text-slate-400">N/A</span>
                        )}
                      </td>

                      <td className="py-3 px-3.5">
                        <span className="font-mono text-[10px] font-extrabold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                          {source.source_type || 'HTML'}
                        </span>
                      </td>

                      <td className="py-3 px-3.5 text-slate-600 font-medium">
                        {source.fetch_frequency_hours ? `${source.fetch_frequency_hours}h` : '24h'}
                      </td>

                      <td className="py-3 px-3.5 text-slate-600 font-mono text-[11px]">
                        {source.last_fetched_at
                          ? new Date(source.last_fetched_at).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' })
                          : 'Pending first run'}
                      </td>

                      <td className="py-3 px-3.5">
                        <div className="space-y-1">
                          <span
                            className={`inline-flex items-center gap-1 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border ${
                              isHealthy
                                ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                                : isDegraded
                                ? 'bg-amber-100 text-amber-800 border-amber-300'
                                : 'bg-rose-100 text-rose-800 border-rose-300'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                isHealthy ? 'bg-emerald-500' : isDegraded ? 'bg-amber-500' : 'bg-rose-500'
                              }`}
                            ></span>
                            {source.health_status || (source.last_status === 'SUCCESS' ? 'HEALTHY' : 'UNFETCHED')}
                          </span>

                          {(source.consecutive_failures ?? 0) > 0 && (
                            <div className="text-[10px] font-bold text-rose-600">
                              {source.consecutive_failures} consecutive failure{source.consecutive_failures! > 1 ? 's' : ''}
                            </div>
                          )}
                        </div>
                      </td>

                      <td className="py-3 px-3.5 text-right">
                        <button
                          type="button"
                          disabled={isRunning}
                          onClick={() => handleRunSource(source.source_id)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-[11px] font-bold rounded-lg transition disabled:opacity-50"
                        >
                          <Play className={`w-3 h-3 ${isRunning ? 'animate-spin' : ''}`} />
                          <span>{isRunning ? 'Running...' : 'Run Pipeline'}</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Manual Monitoring Run Confirmation Dialog */}
      {isTriggerModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center gap-3 text-indigo-600">
              <div className="p-3 bg-indigo-100 rounded-xl">
                <Zap className="w-6 h-6 text-indigo-600" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-slate-900">Run Monitoring Cycle Now?</h3>
                <p className="text-xs text-slate-500">On-demand government source inspection</p>
              </div>
            </div>

            <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-xl space-y-2 text-xs text-indigo-900">
              <p className="font-semibold">
                This will trigger an on-demand scheme data ingestion run across all {sources.length} active government sources.
              </p>
              <ul className="list-disc list-inside text-[11px] space-y-1 text-slate-700">
                <li>Fetches latest snapshots from official ministry websites</li>
                <li>Calculates SHA-256 hashes and evaluates field diffs</li>
                <li>Performs deterministic validation on changes</li>
                <li>Stages detected updates into the Pending Reviews queue</li>
                <li><strong>Never</strong> mutates canonical schemes without admin review</li>
              </ul>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="forceUpdateToggle"
                checked={forceUpdate}
                onChange={(e) => setForceUpdate(e.target.checked)}
                className="w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
              />
              <label htmlFor="forceUpdateToggle" className="text-xs text-slate-700 font-medium cursor-pointer">
                Force re-fetch and evaluation (bypass cached hash check)
              </label>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsTriggerModalOpen(false)}
                disabled={isTriggering}
                className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isTriggering}
                onClick={handleTriggerSchedulerRun}
                className="px-4 py-2 text-xs font-extrabold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl shadow-md transition flex items-center gap-1.5"
              >
                <Zap className="w-3.5 h-3.5" />
                {isTriggering ? 'Triggering...' : 'Confirm & Run Monitoring'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
