import React, { useState, useEffect, useMemo } from 'react';
import { adminApi, SchemeAuditItem } from '../../api/adminApi';
import {
  PendingSchemeUpdate,
  PendingUpdateReviewInput,
  DetectedFieldChange,
  SourceResponse,
} from '../../types';
import {
  GitCompare,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter,
  ArrowRight,
  ShieldCheck,
  FileText,
  Clock,
  Check,
  X,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Info,
  ShieldAlert,
  Sparkles,
  Layers,
  History,
  AlertCircle
} from 'lucide-react';

interface PendingUpdatesTableProps {
  schemes?: SchemeAuditItem[];
  sources?: SourceResponse[];
  onNavigateToChangelog?: () => void;
}

export const PendingUpdatesTable: React.FC<PendingUpdatesTableProps> = ({
  schemes = [],
  sources = [],
  onNavigateToChangelog,
}) => {
  const [updates, setUpdates] = useState<PendingSchemeUpdate[]>([]);
  const [localSchemes, setLocalSchemes] = useState<SchemeAuditItem[]>(schemes);
  const [localSources, setLocalSources] = useState<SourceResponse[]>(sources);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('PENDING');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Review Detail Modal State
  const [selectedUpdate, setSelectedUpdate] = useState<PendingSchemeUpdate | null>(null);
  const [isSourceProvenanceOpen, setIsSourceProvenanceOpen] = useState<boolean>(true);
  const [isRawJsonOpen, setIsRawJsonOpen] = useState<boolean>(false);

  // Approval / Rejection Dialog State
  const [actionConfirm, setActionConfirm] = useState<'APPROVE' | 'REJECT' | null>(null);
  const [rejectionReason, setRejectionReason] = useState<string>('');
  const [approvalNotes, setApprovalNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const fetchData = async () => {
    setIsLoading(true);
    setFeedback(null);
    try {
      const [updatesData, schemesData, sourcesData] = await Promise.all([
        adminApi.getPendingUpdates({
          status: statusFilter === 'ALL' ? undefined : statusFilter,
          page_size: 100,
        }).catch((err) => {
          console.error('Failed to load pending updates:', err);
          return [];
        }),
        localSchemes.length === 0
          ? adminApi.getSchemeAuditList({ page_size: 100 }).then((res) => res.items).catch(() => [])
          : Promise.resolve(localSchemes),
        localSources.length === 0
          ? adminApi.getSources().catch(() => [])
          : Promise.resolve(localSources),
      ]);

      setUpdates(updatesData || []);
      if (schemesData && schemesData.length > 0) setLocalSchemes(schemesData);
      if (sourcesData && sourcesData.length > 0) setLocalSources(sourcesData);
    } catch (err: any) {
      console.error('Failed to load updates view:', err);
      setFeedback({
        type: 'error',
        text: err?.response?.data?.detail || 'Failed to load scheme updates from backend.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Map for fast scheme and source resolution
  const schemesMap = useMemo(() => {
    const map = new Map<string, SchemeAuditItem>();
    localSchemes.forEach((s) => {
      map.set(s.scheme_id, s);
    });
    return map;
  }, [localSchemes]);

  const sourcesMap = useMemo(() => {
    const map = new Map<string, SourceResponse>();
    localSources.forEach((src) => {
      map.set(src.source_id, src);
    });
    return map;
  }, [localSources]);

  const getSchemeName = (update: PendingSchemeUpdate): string => {
    const fromMap = schemesMap.get(update.scheme_id);
    if (fromMap?.scheme_name) return fromMap.scheme_name;
    if (update.extracted_data?.scheme_name) return String(update.extracted_data.scheme_name);
    return update.scheme_id;
  };

  const getSourceInfo = (update: PendingSchemeUpdate) => {
    if (!update.source_id) return null;
    return sourcesMap.get(update.source_id) || null;
  };

  const handleOpenDetailModal = (update: PendingSchemeUpdate) => {
    setSelectedUpdate(update);
    setIsSourceProvenanceOpen(true);
    setIsRawJsonOpen(false);
    setActionConfirm(null);
  };

  const handleOpenActionConfirm = (action: 'APPROVE' | 'REJECT') => {
    setActionConfirm(action);
    setRejectionReason('');
    setApprovalNotes('');
  };

  const handleSubmitReviewDecision = async () => {
    if (!selectedUpdate || !actionConfirm) return;

    if (actionConfirm === 'REJECT' && !rejectionReason.trim()) {
      alert('A valid rejection reason is required to reject a proposed scheme update.');
      return;
    }

    setIsSubmitting(true);
    setFeedback(null);

    const isDemo =
      typeof window !== 'undefined' &&
      (sessionStorage.getItem('yojnasetu_demo_admin_authenticated') === 'true' ||
        window.location.pathname.includes('demo'));

    if (isDemo) {
      setTimeout(() => {
        const schemeName = getSchemeName(selectedUpdate);
        setUpdates((prev) => prev.filter((u) => u.update_id !== selectedUpdate.update_id));
        setFeedback({
          type: 'success',
          text: `✨ [DEMO SANDBOX] Update for '${schemeName}' (${selectedUpdate.scheme_id}) ${actionConfirm === 'APPROVE' ? 'approved' : 'rejected'} visually in preview. Database preserved.`,
        });
        setSelectedUpdate(null);
        setActionConfirm(null);
        setIsSubmitting(false);
        setTimeout(() => setFeedback(null), 7000);
      }, 400);
      return;
    }

    try {
      const payload: PendingUpdateReviewInput = {
        action: actionConfirm,
        reason: actionConfirm === 'REJECT' ? rejectionReason.trim() : approvalNotes.trim() || undefined,
      };

      const res = await adminApi.reviewPendingUpdate(selectedUpdate.update_id, payload);

      const schemeName = getSchemeName(selectedUpdate);
      setFeedback({
        type: 'success',
        text: actionConfirm === 'APPROVE'
          ? `Update for '${schemeName}' (${selectedUpdate.scheme_id}) approved! Canonical scheme updated, version bumped, and audit changelog recorded.`
          : `Update for '${schemeName}' (${selectedUpdate.scheme_id}) rejected. Reason logged in audit registry.`,
      });

      setSelectedUpdate(null);
      setActionConfirm(null);
      fetchData();
      setTimeout(() => setFeedback(null), 8000);
    } catch (err: any) {
      console.error('Review decision submission error:', err);
      setFeedback({
        type: 'error',
        text: err?.response?.data?.detail || 'Failed to submit review decision to backend.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Filter updates
  const filteredUpdates = updates.filter((u) => {
    // Type Filter
    if (typeFilter !== 'ALL') {
      const propType = u.proposal_type || 'MODIFICATION';
      if (propType !== typeFilter) return false;
    }

    // Search Query
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const schemeName = getSchemeName(u).toLowerCase();
    const schemeId = (u.scheme_id || '').toLowerCase();
    const sourceId = (u.source_id || '').toLowerCase();
    const updateId = (u.update_id || '').toLowerCase();
    return schemeName.includes(q) || schemeId.includes(q) || sourceId.includes(q) || updateId.includes(q);
  });

  // Helper for rendering field diff values cleanly
  const renderDiffValue = (val: any) => {
    if (val === null || val === undefined) {
      return <span className="text-slate-400 italic font-mono text-[11px]">None / Not Set</span>;
    }
    if (typeof val === 'boolean') {
      return (
        <span className={`font-mono text-xs font-bold ${val ? 'text-emerald-700' : 'text-slate-700'}`}>
          {val ? 'TRUE (Yes)' : 'FALSE (No)'}
        </span>
      );
    }
    if (typeof val === 'string' || typeof val === 'number') {
      return <span className="font-mono text-xs text-slate-900 break-words">{String(val)}</span>;
    }
    return <pre className="text-[10px] font-mono text-slate-800 whitespace-pre-wrap">{JSON.stringify(val, null, 2)}</pre>;
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-amber-100 text-amber-800 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
              Human-in-the-Loop Review
            </span>
            <span className="text-xs text-slate-500 font-semibold">
              SIH26092 Continuous Data Governance
            </span>
          </div>
          <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
            <GitCompare className="w-5 h-5 text-amber-600" />
            Pending Scheme Updates & Before / After Diffs
          </h2>
          <p className="text-xs text-slate-500 mt-0.5 max-w-3xl">
            Review field-level modifications detected across official government portals. Every approved change increments the scheme version, updates canonical rules, and appends an immutable entry to the audit changelog.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {onNavigateToChangelog && (
            <button
              type="button"
              onClick={onNavigateToChangelog}
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-bold rounded-xl transition"
            >
              <History className="w-3.5 h-3.5 text-slate-500" />
              <span>Audit Changelog</span>
            </button>
          )}

          <button
            type="button"
            onClick={fetchData}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-bold rounded-xl transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh Queue</span>
          </button>
        </div>
      </div>

      {/* Feedback Alert */}
      {feedback && (
        <div
          className={`p-4 rounded-xl text-xs font-semibold flex items-center justify-between gap-3 animate-fadeIn ${
            feedback.type === 'success'
              ? 'bg-emerald-50 text-emerald-900 border border-emerald-300'
              : feedback.type === 'info'
              ? 'bg-sky-50 text-sky-900 border border-sky-300'
              : 'bg-rose-50 text-rose-900 border border-rose-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {feedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : feedback.type === 'info' ? (
              <Info className="w-4 h-4 text-sky-600 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span>{feedback.text}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="text-slate-500 hover:text-slate-800 font-bold px-1">
            ✕
          </button>
        </div>
      )}

      {/* Search and Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by Scheme Name, ID, or Source..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 focus:border-gov-blue outline-none font-medium"
          />
        </div>

        {/* Status Filter */}
        <div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 font-bold focus:border-gov-blue outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">Awaiting Admin Review (PENDING)</option>
            <option value="APPROVED">Approved & Promoted (APPROVED)</option>
            <option value="REJECTED">Declined / Discarded (REJECTED)</option>
          </select>
        </div>

        {/* Update Type Filter */}
        <div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 font-bold focus:border-gov-blue outline-none"
          >
            <option value="ALL">All Proposal Types</option>
            <option value="MODIFICATION">Parameter Modification</option>
            <option value="NEW_SCHEME">New Scheme Discovered</option>
            <option value="DEACTIVATION">Closure / Deactivation Proposal</option>
          </select>
        </div>
      </div>

      {/* Pending Updates List */}
      {isLoading ? (
        <div className="py-16 text-center text-slate-500 text-xs flex flex-col items-center gap-2">
          <RefreshCw className="w-6 h-6 animate-spin text-amber-600" />
          <span>Loading detected scheme updates from official gazettes...</span>
        </div>
      ) : filteredUpdates.length === 0 ? (
        <div className="py-16 bg-slate-50 border border-dashed border-slate-200 rounded-2xl text-center space-y-2 p-6">
          <ShieldCheck className="w-10 h-10 text-emerald-600 mx-auto" />
          <h3 className="text-sm font-bold text-slate-800">No pending scheme updates</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            {statusFilter === 'PENDING'
              ? 'All canonical schemes are fully synchronized with their latest snapshots from authoritative government sources. No reviews are currently pending.'
              : 'No scheme updates matched the chosen status or type filter.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-[11px] font-bold text-slate-500 px-1">
            <span>Displaying {filteredUpdates.length} scheme update proposal{filteredUpdates.length > 1 ? 's' : ''}</span>
            <span>Human-in-the-Loop Gateway</span>
          </div>

          <div className="space-y-3.5">
            {filteredUpdates.map((update) => {
              const isPending = update.status === 'PENDING' || update.status === 'PENDING_REVIEW';
              const isApproved = update.status === 'APPROVED';
              const isRejected = update.status === 'REJECTED';

              const schemeName = getSchemeName(update);
              const sourceInfo = getSourceInfo(update);

              const propType = update.proposal_type || 'MODIFICATION';
              const isNewScheme = propType === 'NEW_SCHEME';
              const isDeactivation = propType === 'DEACTIVATION';

              const validationStatus = update.validation_status || 'VALID';
              const isValid = validationStatus === 'VALID';
              const isNeedsReview = validationStatus === 'NEEDS_REVIEW';
              const isInvalid = validationStatus === 'INVALID';

              const diffCount = update.detected_changes?.length ?? 0;

              return (
                <div
                  key={update.update_id}
                  className={`p-5 rounded-2xl border transition shadow-xs space-y-3.5 ${
                    isPending
                      ? 'bg-white border-slate-200 hover:border-amber-300'
                      : isApproved
                      ? 'bg-slate-50/60 border-slate-200'
                      : 'bg-rose-50/20 border-rose-100'
                  }`}
                >
                  {/* Card Header */}
                  <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        {/* Scheme ID Code */}
                        <span className="font-mono text-xs font-extrabold bg-slate-100 text-sky-800 px-2.5 py-0.5 rounded border border-slate-200">
                          {update.scheme_id}
                        </span>

                        {/* Proposal Type Badge */}
                        {isNewScheme ? (
                          <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                            <Sparkles className="w-3 h-3 text-emerald-600" />
                            New Scheme Detected
                          </span>
                        ) : isDeactivation ? (
                          <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-300 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3 text-rose-600" />
                            Closure / Deactivation Proposal
                          </span>
                        ) : (
                          <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 flex items-center gap-1">
                            <GitCompare className="w-3 h-3 text-amber-700" />
                            Parameter Modification ({diffCount} Field{diffCount !== 1 ? 's' : ''})
                          </span>
                        )}

                        {/* Validation Status Badge */}
                        <span
                          className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border flex items-center gap-1 ${
                            isValid
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : isNeedsReview
                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                              : 'bg-rose-50 text-rose-700 border-rose-200'
                          }`}
                        >
                          {isValid ? (
                            <Check className="w-3 h-3 text-emerald-600" />
                          ) : isNeedsReview ? (
                            <AlertCircle className="w-3 h-3 text-amber-600" />
                          ) : (
                            <X className="w-3 h-3 text-rose-600" />
                          )}
                          Validation: {validationStatus}
                        </span>

                        {/* Status Badge */}
                        <span
                          className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border ${
                            isApproved
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                              : isRejected
                              ? 'bg-rose-100 text-rose-800 border-rose-300'
                              : 'bg-amber-50 text-amber-800 border-amber-300'
                          }`}
                        >
                          Status: {update.status}
                        </span>
                      </div>

                      {/* Scheme Name Title */}
                      <h3 className="text-sm font-extrabold text-slate-900 truncate">
                        {schemeName}
                      </h3>

                      {/* Metadata Row: Source & Timestamp */}
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                        <span>
                          Source: <strong className="text-slate-700">{sourceInfo?.source_name || update.source_id || 'Official Portal'}</strong>
                          {sourceInfo?.authority && ` (${sourceInfo.authority})`}
                        </span>
                        <span>•</span>
                        <span>
                          Detected: <strong className="text-slate-700">{update.created_at ? new Date(update.created_at).toLocaleString('en-IN') : 'Recently'}</strong>
                        </span>
                        {update.old_version && (
                          <>
                            <span>•</span>
                            <span>
                              Version Baseline: <strong className="font-mono text-slate-700">v{update.old_version}</strong>
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => handleOpenDetailModal(update)}
                        className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl shadow-xs transition flex items-center gap-1.5"
                      >
                        <GitCompare className="w-3.5 h-3.5" />
                        <span>Review & Compare Diff</span>
                      </button>
                    </div>
                  </div>

                  {/* Summary of Detected Changes Preview */}
                  {update.detected_changes && update.detected_changes.length > 0 && (
                    <div className="bg-slate-50 rounded-xl p-3 border border-slate-200/80 space-y-2">
                      <div className="flex items-center justify-between text-[11px] font-bold text-slate-600">
                        <span className="uppercase tracking-wider">Field-Level Change Highlights:</span>
                        <span className="text-slate-400 font-mono text-[10px]">{diffCount} fields updated</span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                        {update.detected_changes.slice(0, 3).map((chg, idx) => (
                          <div key={idx} className="p-2 bg-white rounded-lg border border-slate-200 text-xs space-y-1">
                            <span className="font-bold font-mono text-[11px] text-slate-800 block truncate">
                              {chg.field}
                            </span>
                            <div className="flex items-center gap-1.5 text-[11px]">
                              <span className="line-through text-rose-600 font-mono truncate max-w-[45%]">
                                {String(chg.old_value ?? 'None')}
                              </span>
                              <ArrowRight className="w-3 h-3 text-slate-400 shrink-0" />
                              <span className="text-emerald-600 font-bold font-mono truncate max-w-[45%]">
                                {String(chg.new_value ?? 'None')}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>

                      {diffCount > 3 && (
                        <div className="text-[11px] text-indigo-600 font-semibold cursor-pointer hover:underline pt-0.5" onClick={() => handleOpenDetailModal(update)}>
                          + {diffCount - 3} more field changes (click to inspect all)
                        </div>
                      )}
                    </div>
                  )}

                  {/* Review History Notes (if already reviewed) */}
                  {!isPending && (
                    <div className={`p-3 rounded-xl text-xs space-y-1 ${isApproved ? 'bg-emerald-50 border border-emerald-200 text-emerald-900' : 'bg-rose-50 border border-rose-200 text-rose-900'}`}>
                      <div className="flex items-center justify-between">
                        <span className="font-bold uppercase tracking-wider text-[10px]">
                          {isApproved ? 'Approved by Admin' : 'Rejected by Admin'}:
                        </span>
                        <span className="font-mono text-[10px] text-slate-500">
                          {update.reviewed_at ? new Date(update.reviewed_at).toLocaleString('en-IN') : ''}
                        </span>
                      </div>
                      <p className="text-[11px]">
                        <strong>Reviewer:</strong> {update.reviewed_by || 'system_admin'}
                      </p>
                      {(update.rejection_reason || update.review_notes) && (
                        <p className="text-[11px]">
                          <strong>Audit Reason:</strong> {update.rejection_reason || update.review_notes}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────── */}
      {/* BEFORE / AFTER FIELD DIFF & PROVENANCE INSPECTION MODAL */}
      {/* ───────────────────────────────────────────────────────────── */}
      {selectedUpdate && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-5 overflow-y-auto animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden my-auto">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-200 bg-slate-900 text-white flex items-start justify-between gap-3 shrink-0">
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs font-bold bg-slate-800 text-sky-300 px-2.5 py-0.5 rounded border border-slate-700">
                    {selectedUpdate.scheme_id}
                  </span>
                  <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-amber-400 text-slate-950">
                    {selectedUpdate.proposal_type || 'MODIFICATION'}
                  </span>
                  <span className="text-[10px] font-mono text-slate-300 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                    Baseline: v{selectedUpdate.old_version || '1.0'} → Target: v{(parseFloat(selectedUpdate.old_version || '1.0') + 0.1).toFixed(1)}
                  </span>
                </div>
                <h3 className="text-base font-extrabold text-white">
                  {getSchemeName(selectedUpdate)}
                </h3>
              </div>

              <button
                type="button"
                onClick={() => setSelectedUpdate(null)}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition shrink-0"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body (Scrollable) */}
            <div className="p-6 space-y-6 overflow-y-auto flex-1 text-slate-800">
              {/* Validation Alert Gating Banner */}
              {selectedUpdate.validation_status === 'INVALID' ? (
                <div className="p-4 bg-rose-50 border border-rose-300 rounded-xl space-y-2 text-rose-900 text-xs">
                  <div className="flex items-center gap-2 font-bold text-rose-800">
                    <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0" />
                    <span>Deterministic Validation Failed: Approval Blocked</span>
                  </div>
                  <p className="text-[11px] leading-relaxed">
                    This proposed scheme update failed automatic schema validation rules. Admin approval is disabled until validation errors are addressed to protect citizen data integrity.
                  </p>
                  {selectedUpdate.validation_errors && selectedUpdate.validation_errors.length > 0 && (
                    <ul className="list-disc list-inside text-[11px] text-rose-800 space-y-0.5 pt-1">
                      {selectedUpdate.validation_errors.map((err, i) => (
                        <li key={i}>{err}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : selectedUpdate.validation_status === 'NEEDS_REVIEW' ? (
                <div className="p-3.5 bg-amber-50 border border-amber-300 rounded-xl flex items-start gap-2.5 text-xs text-amber-900">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Requires Administrative Review:</span>
                    <p className="text-[11px] text-amber-800 mt-0.5">
                      Statutory parameters differ significantly from baseline. Please verify the numbers against official gazette publications before approving.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="p-3.5 bg-emerald-50 border border-emerald-300 rounded-xl flex items-center gap-2.5 text-xs text-emerald-900">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>
                    <strong>Validation Passed:</strong> Proposed update matches strict statutory parameter typing and deterministic condition criteria.
                  </span>
                </div>
              )}

              {/* Collapsible Source & Provenance Section */}
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <button
                  type="button"
                  onClick={() => setIsSourceProvenanceOpen(!isSourceProvenanceOpen)}
                  className="w-full px-4 py-3 bg-slate-50 hover:bg-slate-100 flex items-center justify-between text-xs font-extrabold text-slate-800 border-b border-slate-200 transition"
                >
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-indigo-600" />
                    <span>Official Source & Verification Provenance</span>
                  </div>
                  {isSourceProvenanceOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {isSourceProvenanceOpen && (
                  <div className="p-4 bg-white grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Source Authority</span>
                      <span className="font-semibold text-slate-900">
                        {getSourceInfo(selectedUpdate)?.authority || 'Central Government Ministry'}
                      </span>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Official Source Name</span>
                      <span className="font-semibold text-slate-900">
                        {getSourceInfo(selectedUpdate)?.source_name || selectedUpdate.source_id || 'Official Government Portal'}
                      </span>
                    </div>

                    <div className="sm:col-span-2">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Authoritative URL</span>
                      {getSourceInfo(selectedUpdate)?.source_url ? (
                        <a
                          href={getSourceInfo(selectedUpdate)?.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-gov-blue hover:underline font-mono text-[11px] flex items-center gap-1.5 break-all mt-0.5"
                        >
                          <span>{getSourceInfo(selectedUpdate)?.source_url}</span>
                          <ExternalLink className="w-3 h-3 shrink-0" />
                        </a>
                      ) : (
                        <span className="text-slate-500 font-mono text-[11px]">Direct Gazette Feed</span>
                      )}
                    </div>

                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Snapshot SHA-256 Hash</span>
                      <span className="font-mono text-[11px] text-slate-700 break-all">
                        {selectedUpdate.snapshot_id || 'Immutable Crawler Snapshot'}
                      </span>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Detected Timestamp</span>
                      <span className="font-mono text-[11px] text-slate-700">
                        {selectedUpdate.created_at ? new Date(selectedUpdate.created_at).toLocaleString('en-IN') : 'Recently'}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Field-by-Field Before / After Comparison Table */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-black text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                    <GitCompare className="w-4 h-4 text-amber-600" />
                    Field-by-Field Comparison (Current vs Proposed)
                  </h4>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {selectedUpdate.detected_changes?.length ?? 0} field change{(selectedUpdate.detected_changes?.length ?? 0) !== 1 ? 's' : ''} detected
                  </span>
                </div>

                {(!selectedUpdate.detected_changes || selectedUpdate.detected_changes.length === 0) ? (
                  <div className="p-6 bg-slate-50 border border-dashed border-slate-200 rounded-xl text-center text-xs text-slate-500">
                    No discrete field diffs recorded. Review proposed JSON payload below.
                  </div>
                ) : (
                  <div className="overflow-x-auto border border-slate-200 rounded-xl">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="bg-slate-100 text-slate-700 font-extrabold border-b border-slate-200 text-[10px] uppercase tracking-wider">
                          <th className="p-3 w-1/4">Field Name</th>
                          <th className="p-3 w-3/8 bg-rose-50/50 text-rose-900 border-r border-slate-200">
                            Current Canonical Baseline
                          </th>
                          <th className="p-3 w-3/8 bg-emerald-50/50 text-emerald-900">
                            Proposed Value (Target Source)
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200">
                        {selectedUpdate.detected_changes.map((chg, idx) => {
                          const isNewField = chg.old_value === null || chg.old_value === undefined;
                          const isRemoved = chg.new_value === null || chg.new_value === undefined;

                          return (
                            <tr key={idx} className="hover:bg-slate-50/70">
                              <td className="p-3 font-mono font-bold text-slate-900 align-top">
                                <div className="space-y-0.5">
                                  <span>{chg.field}</span>
                                  <div>
                                    {isNewField ? (
                                      <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">
                                        Added
                                      </span>
                                    ) : isRemoved ? (
                                      <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-rose-100 text-rose-800">
                                        Removed
                                      </span>
                                    ) : (
                                      <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-amber-100 text-amber-800">
                                        Modified
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </td>

                              <td className="p-3 bg-rose-50/30 border-r border-slate-200 align-top">
                                {renderDiffValue(chg.old_value)}
                              </td>

                              <td className="p-3 bg-emerald-50/30 align-top">
                                {renderDiffValue(chg.new_value)}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Raw JSON Extracted Payload Viewer Toggle */}
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <button
                  type="button"
                  onClick={() => setIsRawJsonOpen(!isRawJsonOpen)}
                  className="w-full px-4 py-2.5 bg-slate-50 hover:bg-slate-100 flex items-center justify-between text-xs font-bold text-slate-700 transition"
                >
                  <span>View Full Extracted JSON Payload</span>
                  {isRawJsonOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
                {isRawJsonOpen && (
                  <div className="p-4 bg-slate-950 text-slate-200 text-[11px] font-mono overflow-x-auto max-h-64">
                    <pre>{JSON.stringify(selectedUpdate.extracted_data || {}, null, 2)}</pre>
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer Controls */}
            <div className="p-4 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 shrink-0">
              <div className="text-xs text-slate-500 font-medium">
                Human-in-the-Loop Gateway: Decisions directly update canonical DB & vector store.
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                <button
                  type="button"
                  onClick={() => setSelectedUpdate(null)}
                  className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-200 rounded-xl transition"
                >
                  Close
                </button>

                {/* Only display action buttons for actionable pending updates */}
                {(selectedUpdate.status === 'PENDING' || selectedUpdate.status === 'PENDING_REVIEW') && (
                  <>
                    <button
                      type="button"
                      onClick={() => handleOpenActionConfirm('REJECT')}
                      className="px-4 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-bold rounded-xl transition flex items-center gap-1.5"
                    >
                      <XCircle className="w-4 h-4 text-rose-600" />
                      <span>Reject Update</span>
                    </button>

                    <button
                      type="button"
                      disabled={selectedUpdate.validation_status === 'INVALID'}
                      onClick={() => handleOpenActionConfirm('APPROVE')}
                      className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-extrabold rounded-xl shadow-md transition flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
                      title={selectedUpdate.validation_status === 'INVALID' ? 'Approval disabled due to validation errors' : 'Approve Update'}
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Approve Update</span>
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────── */}
      {/* APPROVE / REJECT CONFIRMATION DIALOG */}
      {/* ───────────────────────────────────────────────────────────── */}
      {actionConfirm && selectedUpdate && (
        <div className="fixed inset-0 z-60 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center gap-3">
              <div
                className={`p-3 rounded-xl ${
                  actionConfirm === 'APPROVE' ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'
                }`}
              >
                {actionConfirm === 'APPROVE' ? (
                  <CheckCircle2 className="w-6 h-6" />
                ) : (
                  <AlertTriangle className="w-6 h-6" />
                )}
              </div>
              <div>
                <h3 className="text-base font-extrabold text-slate-900">
                  {actionConfirm === 'APPROVE' ? 'Approve Scheme Update?' : 'Reject Scheme Update?'}
                </h3>
                <p className="text-xs text-slate-500">
                  {actionConfirm === 'APPROVE' ? 'Canonical scheme catalog mutation' : 'Discard proposed changes'}
                </p>
              </div>
            </div>

            {actionConfirm === 'APPROVE' ? (
              <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl space-y-2 text-xs text-emerald-900">
                <p className="font-bold">
                  After approval, the following automated actions will execute:
                </p>
                <ul className="list-disc list-inside text-[11px] space-y-1 text-emerald-800">
                  <li>Canonical Scheme record in PostgreSQL will be updated</li>
                  <li>Scheme version will increment (e.g. v{selectedUpdate.old_version || '1.0'} → v{(parseFloat(selectedUpdate.old_version || '1.0') + 0.1).toFixed(1)})</li>
                  <li>Deterministic eligibility rules will be synchronized</li>
                  <li>RAG vector embeddings will update for live search</li>
                  <li>Immutable audit log entry recorded in <strong>SchemeChangelog</strong></li>
                </ul>
              </div>
            ) : (
              <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl space-y-2 text-xs text-rose-900">
                <p className="font-bold">
                  Canonical Scheme record will remain completely unchanged.
                </p>
                <p className="text-[11px] text-rose-800">
                  This proposal will be marked as <strong>REJECTED</strong> and recorded in the audit trail with your specified reason.
                </p>
              </div>
            )}

            {/* Input field */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                {actionConfirm === 'APPROVE' ? (
                  <>
                    Approval Notes <span className="text-slate-400 font-normal">(Optional audit notes)</span>
                  </>
                ) : (
                  <>
                    Rejection Reason <span className="text-rose-600 font-bold">* Required</span>
                  </>
                )}
              </label>
              <textarea
                rows={3}
                value={actionConfirm === 'APPROVE' ? approvalNotes : rejectionReason}
                onChange={(e) =>
                  actionConfirm === 'APPROVE' ? setApprovalNotes(e.target.value) : setRejectionReason(e.target.value)
                }
                placeholder={
                  actionConfirm === 'APPROVE'
                    ? 'e.g. Verified against official KVIC Gazette notification dated 2026-09-15...'
                    : 'e.g. Proposed interest rate contradicts recent Reserve Bank guideline...'
                }
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-3 text-xs text-slate-900 outline-none focus:border-gov-blue"
              />
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setActionConfirm(null)}
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl transition"
              >
                Cancel
              </button>

              <button
                type="button"
                disabled={isSubmitting || (actionConfirm === 'REJECT' && !rejectionReason.trim())}
                onClick={handleSubmitReviewDecision}
                className={`px-5 py-2 text-xs font-extrabold text-white rounded-xl shadow-md transition flex items-center gap-1.5 disabled:opacity-50 ${
                  actionConfirm === 'APPROVE' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-rose-600 hover:bg-rose-700'
                }`}
              >
                {isSubmitting ? (
                  'Submitting...'
                ) : actionConfirm === 'APPROVE' ? (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Confirm Approval</span>
                  </>
                ) : (
                  <>
                    <X className="w-4 h-4" />
                    <span>Confirm Rejection</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
