import React, { useState, useEffect } from 'react';
import { adminApi } from '../../api/adminApi';
import { CandidateScheme, CandidateReviewInput } from '../../types';
import {
  Inbox,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Search,
  Filter,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  FileText,
  Building2,
  ArrowRight,
  Eye,
  Info
} from 'lucide-react';

export const CandidateStagingTable: React.FC = () => {
  const [candidates, setCandidates] = useState<CandidateScheme[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('STAGED');
  const [duplicateFilter, setDuplicateFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Review Action Modal State
  const [reviewTarget, setReviewTarget] = useState<CandidateScheme | null>(null);
  const [reviewAction, setReviewAction] = useState<'APPROVE' | 'REJECT'>('APPROVE');
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [feedbackMessage, setFeedbackMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchCandidates();
  }, [statusFilter, duplicateFilter]);

  const fetchCandidates = async () => {
    setIsLoading(true);
    try {
      const data = await adminApi.getCandidates({
        status_filter: statusFilter === 'ALL' ? undefined : statusFilter,
        duplicate_filter: duplicateFilter === 'ALL' ? undefined : duplicateFilter,
        limit: 100,
      });
      setCandidates(data || []);
    } catch (err: any) {
      console.error('Failed to fetch candidate schemes:', err);
      setFeedbackMessage({
        type: 'error',
        text: err?.response?.data?.detail || 'Failed to load candidate schemes from staging repository.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenReview = (candidate: CandidateScheme, action: 'APPROVE' | 'REJECT') => {
    setReviewTarget(candidate);
    setReviewAction(action);
    setReviewNotes('');
  };

  const handleSubmitReview = async () => {
    if (!reviewTarget) return;
    setIsSubmittingReview(true);
    setFeedbackMessage(null);

    try {
      const payload: CandidateReviewInput = {
        action: reviewAction,
        notes: reviewNotes.trim() || undefined,
        rejection_reason: reviewAction === 'REJECT' ? reviewNotes.trim() || 'Rejected by system administrator' : undefined,
      };

      const res = await adminApi.reviewCandidate(reviewTarget.candidate_id, payload);
      setFeedbackMessage({
        type: 'success',
        text: res.message || `Candidate successfully ${reviewAction.toLowerCase()}d.`,
      });
      setReviewTarget(null);
      fetchCandidates();
      setTimeout(() => setFeedbackMessage(null), 6000);
    } catch (err: any) {
      console.error('Review submission error:', err);
      setFeedbackMessage({
        type: 'error',
        text: err?.userFriendlyMessage || err?.response?.data?.detail || err?.message || `Failed to ${reviewAction.toLowerCase()} candidate scheme.`,
      });
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const filteredCandidates = candidates.filter((c) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      (c.scheme_name && c.scheme_name.toLowerCase().includes(q)) ||
      (c.candidate_id && c.candidate_id.toLowerCase().includes(q)) ||
      (c.ministry && c.ministry.toLowerCase().includes(q)) ||
      (c.target_source && c.target_source.toLowerCase().includes(q))
    );
  });

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-indigo-100 text-indigo-800 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
              Smart Scheme Automation
            </span>
            <span className="text-xs text-slate-500 font-semibold">
              Human-in-the-Loop Review Queue
            </span>
          </div>
          <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
            <Inbox className="w-5 h-5 text-indigo-600" />
            Candidate Scheme Staging Repository
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Automated discovery crawler identifies scheme opportunities from official sources. Staged candidates require review before canonical promotion.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={fetchCandidates}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh Staging</span>
          </button>
        </div>
      </div>

      {/* Feedback Banner */}
      {feedbackMessage && (
        <div
          className={`p-4 rounded-xl text-xs font-semibold flex items-center justify-between gap-3 ${
            feedbackMessage.type === 'success'
              ? 'bg-emerald-50 text-emerald-900 border border-emerald-300'
              : 'bg-rose-50 text-rose-900 border border-rose-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {feedbackMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span>{feedbackMessage.text}</span>
          </div>
          <button
            onClick={() => setFeedbackMessage(null)}
            className="text-slate-500 hover:text-slate-700 font-bold px-1"
          >
            ✕
          </button>
        </div>
      )}

      {/* Filters and Search Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search candidate name, ID, ministry..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 focus:border-gov-blue outline-none"
          />
        </div>

        <div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 font-medium focus:border-gov-blue outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="STAGED">Awaiting Review (STAGED)</option>
            <option value="APPROVED">Promoted to Canonical (APPROVED)</option>
            <option value="REJECTED">Declined (REJECTED)</option>
            <option value="DISCOVERED">Raw Ingested (DISCOVERED)</option>
          </select>
        </div>

        <div>
          <select
            value={duplicateFilter}
            onChange={(e) => setDuplicateFilter(e.target.value)}
            className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 font-medium focus:border-gov-blue outline-none"
          >
            <option value="ALL">All Duplicate States</option>
            <option value="UNIQUE">Unique Schemes Only</option>
            <option value="DUPLICATE_CANDIDATE">Flagged as Duplicate</option>
          </select>
        </div>
      </div>

      {/* Candidates List */}
      {isLoading ? (
        <div className="py-16 text-center text-slate-500 text-xs flex flex-col items-center gap-2">
          <RefreshCw className="w-6 h-6 animate-spin text-indigo-600" />
          <span>Querying candidate staging repository...</span>
        </div>
      ) : filteredCandidates.length === 0 ? (
        <div className="py-12 bg-slate-50 border border-dashed border-slate-200 rounded-xl text-center space-y-2">
          <Inbox className="w-8 h-8 text-slate-400 mx-auto" />
          <p className="text-xs font-bold text-slate-700">No candidate schemes match the current filters.</p>
          <p className="text-[11px] text-slate-500">Try changing the status or clearing the search query.</p>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="text-[11px] font-bold text-slate-500 px-1">
            Displaying {filteredCandidates.length} candidate schemes awaiting governance decision
          </div>

          <div className="border border-slate-200 rounded-xl overflow-hidden divide-y divide-slate-100">
            {filteredCandidates.map((candidate) => {
              const isExpanded = expandedId === candidate.candidate_id;
              const isStaged = candidate.candidate_status === 'STAGED';
              const isApproved = candidate.candidate_status === 'APPROVED';
              const isRejected = candidate.candidate_status === 'REJECTED';
              const isDup = candidate.duplicate_status === 'DUPLICATE_CANDIDATE';
              const isQualified = candidate.duplicate_status === 'UNIQUE' && (candidate.verification_status === 'OFFICIALLY_VERIFIED' || candidate.verification_status === 'VERIFIED') && candidate.validation_status === 'VALID';

              return (
                <div key={candidate.candidate_id} className="p-4 hover:bg-slate-50/70 transition">
                  <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
                    <div className="space-y-1 flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-bold border border-slate-200">
                          {candidate.candidate_id}
                        </span>

                        <span
                          className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${
                            isApproved
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                              : isRejected
                              ? 'bg-rose-100 text-rose-800 border-rose-300'
                              : 'bg-amber-100 text-amber-800 border-amber-300'
                          }`}
                        >
                          {candidate.candidate_status}
                        </span>

                        {isQualified ? (
                          <span className="text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-300 px-2 py-0.5 rounded-full flex items-center gap-1">
                            <ShieldCheck className="w-3 h-3 text-emerald-600" />
                            Ready to Promote
                          </span>
                        ) : isDup ? (
                          <span className="text-[10px] font-bold bg-purple-100 text-purple-800 border border-purple-200 px-2 py-0.5 rounded-full">
                            Duplicate Candidate
                          </span>
                        ) : (
                          <span className="text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-full">
                            Triage Required
                          </span>
                        )}

                        {candidate.confidence_score !== undefined && candidate.confidence_score !== null && (
                          <span className="text-[10px] font-bold bg-sky-100 text-sky-800 border border-sky-200 px-2 py-0.5 rounded-full">
                            Confidence: {Math.round(candidate.confidence_score * 100)}%
                          </span>
                        )}
                      </div>

                      <h3 className="text-sm font-bold text-slate-900 leading-snug">
                        {candidate.scheme_name}
                      </h3>

                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                        {candidate.ministry && <span>• {candidate.ministry}</span>}
                        {candidate.target_source && <span>• Source: {candidate.target_source}</span>}
                        {candidate.created_at && (
                          <span>• Discovered {new Date(candidate.created_at).toLocaleDateString('en-IN')}</span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                      <button
                        type="button"
                        onClick={() => setExpandedId(isExpanded ? null : candidate.candidate_id)}
                        className="inline-flex items-center gap-1 text-xs font-bold text-slate-600 hover:text-slate-900 px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>{isExpanded ? 'Hide Details' : 'Inspect'}</span>
                        {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      </button>

                      {isStaged && (
                        <>
                          {isDup ? (
                            <button
                              type="button"
                              disabled
                              title="Duplicate candidates cannot be promoted. Reject candidate to clear queue."
                              className="bg-slate-100 text-slate-400 cursor-not-allowed text-xs font-bold px-3 py-1.5 rounded-lg border border-slate-200 flex items-center gap-1"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5 text-slate-400" />
                              <span>Duplicate (Ineligible)</span>
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleOpenReview(candidate, 'APPROVE')}
                              className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg shadow-xs transition flex items-center gap-1"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Approve & Promote</span>
                            </button>
                          )}

                          <button
                            type="button"
                            onClick={() => handleOpenReview(candidate, 'REJECT')}
                            className="bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-bold px-3 py-1.5 rounded-lg transition flex items-center gap-1"
                          >
                            <XCircle className="w-3.5 h-3.5 text-rose-600" />
                            <span>Reject</span>
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Expandable Parameter Inspection Drawer */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-slate-200/80 bg-slate-50 p-4 rounded-xl text-xs space-y-3">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                          <span className="font-bold text-slate-700 block mb-1">Extracted Parameters:</span>
                          <div className="bg-white p-3 rounded-lg border border-slate-200 font-mono text-[11px] text-slate-800 space-y-1">
                            <div><strong>Category / Sector:</strong> {candidate.category || 'Not specified'}</div>
                            <div><strong>State / Coverage:</strong> {candidate.state || 'All India'}</div>
                            <div><strong>Source Authority:</strong> {candidate.target_source || 'Official Gazette'}</div>
                            {candidate.source_url && (
                              <div className="truncate">
                                <strong>Official URL: </strong>
                                <a
                                  href={candidate.source_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-gov-blue hover:underline inline-flex items-center gap-1"
                                >
                                  {candidate.source_url} <ExternalLink className="w-3 h-3 inline" />
                                </a>
                              </div>
                            )}
                          </div>
                        </div>

                        <div>
                          <span className="font-bold text-slate-700 block mb-1">Validation & Provenance Audit:</span>
                          <div className="bg-white p-3 rounded-lg border border-slate-200 text-[11px] space-y-1.5">
                            {candidate.validation_errors && candidate.validation_errors.length > 0 ? (
                              <div className="text-amber-800 bg-amber-50 p-2 rounded border border-amber-200">
                                <strong>Validation Flags:</strong>
                                <ul className="list-disc pl-4 mt-0.5 space-y-0.5">
                                  {candidate.validation_errors.map((err, i) => (
                                    <li key={i}>{err}</li>
                                  ))}
                                </ul>
                              </div>
                            ) : (
                              <div className="text-emerald-800 bg-emerald-50 p-2 rounded border border-emerald-200 flex items-center gap-1.5">
                                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                                <span>Passed statutory schema and duplicate validation checks.</span>
                              </div>
                            )}

                            {candidate.raw_parameters && (
                              <pre className="text-[10px] text-slate-600 bg-slate-50 p-2 rounded border border-slate-200 overflow-x-auto max-h-32">
                                {JSON.stringify(candidate.raw_parameters, null, 2)}
                              </pre>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Review Modal Dialog */}
      {reviewTarget && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-in fade-in">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                {reviewAction === 'APPROVE' ? (
                  <>
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    Approve & Promote Candidate Scheme
                  </>
                ) : (
                  <>
                    <XCircle className="w-5 h-5 text-rose-600" />
                    Reject Candidate Scheme
                  </>
                )}
              </h3>
              <button
                type="button"
                onClick={() => setReviewTarget(null)}
                className="text-slate-400 hover:text-slate-600 font-bold p-1"
              >
                ✕
              </button>
            </div>

            <div className="text-xs space-y-2 text-slate-700">
              <p>
                <strong>Scheme:</strong> {reviewTarget.scheme_name}
              </p>
              <p className="font-mono text-[11px] text-slate-500">
                ID: {reviewTarget.candidate_id}
              </p>

              {reviewAction === 'APPROVE' && reviewTarget.duplicate_status === 'DUPLICATE_CANDIDATE' ? (
                <div className="p-3 bg-purple-50 border border-purple-200 rounded-xl text-purple-900 space-y-1">
                  <p className="font-bold flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-purple-600" />
                    Duplicate Candidate — Ineligible for Promotion
                  </p>
                  <p className="text-[11px] leading-relaxed">
                    This scheme is flagged as a duplicate candidate. Statutory governance rules prohibit promoting duplicate records into the canonical scheme catalog. Please reject this candidate or review the existing canonical scheme.
                  </p>
                </div>
              ) : reviewAction === 'APPROVE' ? (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900 space-y-1">
                  <p className="font-bold">Automated Governance Pipeline:</p>
                  <p className="text-[11px] leading-relaxed">
                    Promoting this candidate will add it to the canonical Scheme database, generate statutory eligibility rules, create required document checklists, log an audit changelog entry, and sync the RAG vector index.
                  </p>
                </div>
              ) : (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 space-y-1">
                  <p className="font-bold">Rejection Notice:</p>
                  <p className="text-[11px] leading-relaxed">
                    Rejecting this candidate will mark it as REJECTED in the staging repository and prevent it from entering the public citizen catalogue.
                  </p>
                </div>
              )}

              <div>
                <label className="block font-bold text-slate-700 text-xs mb-1">
                  {reviewAction === 'APPROVE' ? 'Review Notes / Promotion Audit Record' : 'Reason for Rejection *'}
                </label>
                <textarea
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder={
                    reviewAction === 'APPROVE'
                      ? 'e.g. Verified against official ministry gazette notification...'
                      : 'e.g. Scheme discontinued / out of scope / duplicate...'
                  }
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-3 text-xs text-slate-900 outline-none focus:border-gov-blue"
                  required={reviewAction === 'REJECT'}
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setReviewTarget(null)}
                className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl transition"
              >
                Cancel
              </button>

              <button
                type="button"
                disabled={
                  isSubmittingReview ||
                  (reviewAction === 'REJECT' && !reviewNotes.trim()) ||
                  (reviewAction === 'APPROVE' && reviewTarget.duplicate_status === 'DUPLICATE_CANDIDATE')
                }
                onClick={handleSubmitReview}
                className={`px-5 py-2 text-xs font-bold text-white rounded-xl shadow-xs transition flex items-center gap-1.5 disabled:opacity-50 ${
                  reviewAction === 'APPROVE' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-rose-600 hover:bg-rose-700'
                }`}
              >
                {isSubmittingReview ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : reviewAction === 'APPROVE' ? (
                  <CheckCircle2 className="w-3.5 h-3.5" />
                ) : (
                  <XCircle className="w-3.5 h-3.5" />
                )}
                <span>{reviewAction === 'APPROVE' ? 'Confirm Promotion' : 'Confirm Rejection'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
