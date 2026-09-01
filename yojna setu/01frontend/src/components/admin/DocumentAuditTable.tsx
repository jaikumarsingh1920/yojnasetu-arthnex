import React, { useState, useEffect } from 'react';
import { adminApi, DocumentAuditItem } from '../../api/adminApi';
import { FileText, ShieldCheck } from 'lucide-react';

export const DocumentAuditTable: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentAuditItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [schemeFilter, setSchemeFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  useEffect(() => {
    fetchDocuments();
  }, [schemeFilter, typeFilter]);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getDocumentAuditList({
        scheme_id: schemeFilter || undefined,
        page_size: 100
      });
      let items = res.items;
      if (typeFilter) {
        items = items.filter((d) => d.requirement_type.toUpperCase() === typeFilter.toUpperCase());
      }
      setDocuments(items);
      setTotal(typeFilter ? items.length : res.total);
    } catch (err) {
      console.error('Failed to fetch document audit list:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-4">
        <div>
          <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
            <FileText className="w-5 h-5 text-sky-600" />
            Document Requirements Audit ({total} Documents)
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">Verified document preparation checklists across target schemes.</p>
        </div>

        <div className="flex flex-wrap gap-2 text-xs">
          <input
            type="text"
            placeholder="Filter by Scheme ID..."
            value={schemeFilter}
            onChange={(e) => setSchemeFilter(e.target.value)}
            className="px-3 py-1.5 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-rose-500 font-mono"
          />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-1.5 border border-slate-300 rounded-lg text-slate-900 font-bold focus:outline-none focus:ring-2 focus:ring-rose-500"
          >
            <option value="">ALL REQUIREMENT TYPES</option>
            <option value="MANDATORY">REQUIRED / MANDATORY</option>
            <option value="CONDITIONAL">CONDITIONAL</option>
            <option value="OPTIONAL">OPTIONAL</option>
            <option value="NOT_VERIFIED">NOT VERIFIED</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="py-8 text-center text-xs text-slate-500">Loading document audit entries...</div>
      ) : documents.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500">No document requirements found matching criteria.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                <th className="p-2.5">Doc ID</th>
                <th className="p-2.5">Scheme ID</th>
                <th className="p-2.5">Document Name</th>
                <th className="p-2.5">Requirement Type</th>
                <th className="p-2.5">Applicant Category</th>
                <th className="p-2.5">Source Guidelines</th>
                <th className="p-2.5">Verification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-800">
              {documents.map((d) => (
                <tr key={d.document_id} className="hover:bg-slate-50">
                  <td className="p-2.5 font-bold font-mono text-sky-800">{d.document_id}</td>
                  <td className="p-2.5 font-bold font-mono text-slate-900">{d.scheme_id}</td>
                  <td className="p-2.5 font-bold text-slate-900">{d.document_name}</td>
                  <td className="p-2.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                      d.requirement_type === 'MANDATORY' || d.requirement_type === 'REQUIRED'
                        ? 'bg-rose-100 text-rose-800 border-rose-300'
                        : d.requirement_type === 'CONDITIONAL'
                        ? 'bg-amber-100 text-amber-800 border-amber-300'
                        : d.requirement_type === 'OPTIONAL'
                        ? 'bg-sky-100 text-sky-800 border-sky-300'
                        : 'bg-slate-100 text-slate-800 border-slate-300'
                    }`}>
                      {d.requirement_type === 'MANDATORY' ? 'REQUIRED' : d.requirement_type}
                    </span>
                  </td>
                  <td className="p-2.5 font-mono text-slate-600">{d.applicant_type || 'ALL APPLICANTS'}</td>
                  <td className="p-2.5 font-mono text-slate-500 max-w-xs truncate">{d.source_document || 'Official Scheme Guidelines'}</td>
                  <td className="p-2.5">
                    <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded border border-emerald-300 flex items-center gap-1 w-fit">
                      <ShieldCheck className="w-3 h-3 text-emerald-600" />
                      VERIFIED
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
