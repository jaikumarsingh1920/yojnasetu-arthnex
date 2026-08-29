import React, { useState, useEffect } from 'react';
import { adminApi, SchemeAuditDetailResponse } from '../../api/adminApi';
import { X, ShieldCheck, AlertTriangle, FileText, CheckCircle, Database, HelpCircle } from 'lucide-react';

interface Props {
  schemeId: string;
  onClose: () => void;
}

export const SchemeDetailAuditModal: React.FC<Props> = ({ schemeId, onClose }) => {
  const [detail, setDetail] = useState<SchemeAuditDetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'PARAMETERS' | 'RULES' | 'DOCUMENTS' | 'CHANGELOG'>('PARAMETERS');

  useEffect(() => {
    fetchDetail();
  }, [schemeId]);

  const fetchDetail = async () => {
    setLoading(true);
    try {
      const data = await adminApi.getSchemeAuditDetail(schemeId);
      setDetail(data);
    } catch (err) {
      console.error('Failed to fetch scheme audit detail:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl text-center space-y-4">
          <div className="w-12 h-12 border-4 border-rose-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm font-bold text-slate-700">Loading Scheme Audit Data ({schemeId})...</p>
        </div>
      </div>
    );
  }

  if (!detail) return null;

  return (
    <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl max-w-4xl w-full shadow-2xl overflow-hidden border border-slate-200 my-8">
        {/* Header */}
        <div className="bg-slate-900 text-white p-6 flex justify-between items-start border-b border-slate-800">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="bg-emerald-500/20 text-emerald-300 text-xs font-extrabold px-2.5 py-0.5 rounded-full border border-emerald-500/30 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                ✓ VERIFIED SCHEME
              </span>
              <span className="text-xs font-mono text-slate-400">{detail.scheme_id}</span>
            </div>
            <h2 className="text-xl font-extrabold text-white">{detail.scheme_name}</h2>
            <p className="text-xs text-slate-400">{detail.ministry} • {detail.sector}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Completeness Score Bar */}
        <div className="bg-slate-100 p-4 border-b border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-slate-900 text-rose-400 flex items-center justify-center font-extrabold text-lg shadow">
              {detail.completeness_score}%
            </div>
            <div>
              <span className="text-xs font-bold text-slate-700 block">Parameter Completeness</span>
              <span className="text-[11px] text-slate-500">
                {Object.keys(detail.known_fields).length} Known • {detail.unknown_fields.length} Unknown • {detail.conditional_fields.length} Conditional
              </span>
            </div>
          </div>

          <div className="w-full sm:w-64 bg-slate-200 rounded-full h-3 overflow-hidden shadow-inner">
            <div
              className="bg-gradient-to-r from-amber-500 to-emerald-500 h-full rounded-full transition-all duration-500"
              style={{ width: `${detail.completeness_score}%` }}
            ></div>
          </div>
        </div>

        {/* Data Quality Warnings */}
        {detail.data_quality_warnings.length > 0 && (
          <div className="bg-amber-50 border-b border-amber-200 p-4">
            <div className="flex items-center gap-2 text-xs font-bold text-amber-900 mb-1">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              Data Quality Audit Warnings (Verification Intact)
            </div>
            <div className="flex flex-wrap gap-2">
              {detail.data_quality_warnings.map((warn, i) => (
                <span key={i} className="text-[11px] bg-amber-100 text-amber-800 px-2.5 py-0.5 rounded border border-amber-300">
                  ⚠️ {warn}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Audit Tabs */}
        <div className="flex border-b border-slate-200 bg-slate-50 px-6 pt-3 gap-2 text-xs font-bold text-slate-600">
          {[
            { id: 'PARAMETERS', label: 'Parameter Audit' },
            { id: 'RULES', label: `Database Rules (${detail.rules.length})` },
            { id: 'DOCUMENTS', label: `Required Documents (${detail.documents.length})` },
            { id: 'CHANGELOG', label: `Enrichment History (${detail.changelogs.length})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`pb-3 px-3 transition border-b-2 ${
                activeTab === tab.id
                  ? 'border-rose-600 text-rose-700 font-extrabold'
                  : 'border-transparent hover:text-slate-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="p-6 max-h-[60vh] overflow-y-auto space-y-6">
          {activeTab === 'PARAMETERS' && (
            <div className="space-y-6">
              {/* Purpose & Target */}
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                  <span className="text-xs font-bold text-slate-500 uppercase block mb-1">Scheme Purpose</span>
                  <p className="text-xs text-slate-800 leading-relaxed">{detail.purpose || 'N/A'}</p>
                </div>
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                  <span className="text-xs font-bold text-slate-500 uppercase block mb-1">Target Group</span>
                  <p className="text-xs text-slate-800 leading-relaxed">{detail.target_groups || 'N/A'}</p>
                </div>
              </div>

              {/* Known Parameters Table */}
              <div>
                <h4 className="text-xs font-bold text-slate-700 uppercase mb-2">Populated Parameters ({Object.keys(detail.known_fields).length})</h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {Object.entries(detail.known_fields).map(([k, v]) => (
                    <div key={k} className="bg-emerald-50/50 p-2.5 rounded-lg border border-emerald-200/60 text-xs">
                      <span className="text-emerald-900 font-bold block text-[11px]">{k}</span>
                      <span className="text-slate-800 font-mono font-medium block truncate">{String(v)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Unknown Fields */}
              {detail.unknown_fields.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-amber-800 uppercase mb-2">Unknown Parameters Requiring Completion ({detail.unknown_fields.length})</h4>
                  <div className="flex flex-wrap gap-2">
                    {detail.unknown_fields.map((f) => (
                      <span key={f} className="text-xs bg-amber-50 text-amber-900 border border-amber-200 px-2.5 py-1 rounded-md font-mono">
                        {f}: UNKNOWN
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'RULES' && (
            <div className="space-y-4">
              {detail.rules.length === 0 ? (
                <p className="text-xs text-slate-500 py-4 text-center">No explicit condition rules configured for this scheme.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                        <th className="p-2">Rule ID</th>
                        <th className="p-2">Field</th>
                        <th className="p-2">Operator</th>
                        <th className="p-2">Value</th>
                        <th className="p-2">Type</th>
                        <th className="p-2">Priority</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {detail.rules.map((r) => (
                        <tr key={r.rule_id} className="hover:bg-slate-50">
                          <td className="p-2 font-mono font-bold text-sky-800">{r.rule_id}</td>
                          <td className="p-2 font-mono font-bold">{r.field}</td>
                          <td className="p-2 font-mono text-amber-700 font-bold">{r.operator}</td>
                          <td className="p-2 font-mono text-slate-900">{r.value}</td>
                          <td className="p-2">{r.rule_type}</td>
                          <td className="p-2"><span className="bg-rose-100 text-rose-800 text-[10px] font-bold px-2 py-0.5 rounded">{r.priority}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'DOCUMENTS' && (
            <div className="space-y-4">
              {detail.documents.length === 0 ? (
                <p className="text-xs text-slate-500 py-4 text-center">No documents registered for this scheme.</p>
              ) : (
                <div className="space-y-2">
                  {detail.documents.map((d) => (
                    <div key={d.document_id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex justify-between items-center text-xs">
                      <div>
                        <span className="font-bold text-slate-900 block">{d.document_name}</span>
                        <span className="text-slate-500 text-[11px]">{d.applicant_type || 'ALL'} • Source: {d.source_document || 'Official Guidelines'}</span>
                      </div>
                      <span className="bg-sky-100 text-sky-800 px-2.5 py-1 rounded font-bold text-[10px] border border-sky-300">
                        {d.requirement_type}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'CHANGELOG' && (
            <div className="space-y-4">
              {detail.changelogs.length === 0 ? (
                <p className="text-xs text-slate-500 py-4 text-center">No historical changelog records logged for this scheme.</p>
              ) : (
                <div className="space-y-2">
                  {detail.changelogs.map((cl) => (
                    <div key={cl.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-slate-900 font-mono">{cl.field || 'General Update'}</span>
                        <span className="text-slate-400 text-[10px]">{cl.created_at}</span>
                      </div>
                      <p className="text-slate-600 text-[11px]">Reason: {cl.reason || 'Data Quality Enrichment'}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-slate-100 p-4 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-900 text-white font-bold text-xs rounded-xl hover:bg-slate-800 transition shadow"
          >
            Close Audit View
          </button>
        </div>
      </div>
    </div>
  );
};
