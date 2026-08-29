import React, { useState, useEffect } from 'react';
import { adminApi, ChangelogItem } from '../../api/adminApi';
import { History, ShieldCheck } from 'lucide-react';

export const ChangelogTable: React.FC = () => {
  const [changelogs, setChangelogs] = useState<ChangelogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchChangelog();
  }, []);

  const fetchChangelog = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getChangelog({ page_size: 100 });
      setChangelogs(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error('Failed to fetch scheme changelog:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
      <div className="border-b border-slate-200 pb-4">
        <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
          <History className="w-5 h-5 text-rose-600" />
          Scheme Knowledge Base Audit Log ({total} Entries)
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">Historical record of scheme metadata updates, rule synchronization, and provenance audit log.</p>
      </div>

      {loading ? (
        <div className="py-8 text-center text-xs text-slate-500">Loading scheme audit changelog...</div>
      ) : changelogs.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500">No scheme audit history records present.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                <th className="p-2.5">ID</th>
                <th className="p-2.5">Scheme ID</th>
                <th className="p-2.5">Updated Field</th>
                <th className="p-2.5">Old Value</th>
                <th className="p-2.5">New Value</th>
                <th className="p-2.5">Reason / Source</th>
                <th className="p-2.5">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-800">
              {changelogs.map((cl) => (
                <tr key={cl.id} className="hover:bg-slate-50">
                  <td className="p-2.5 font-bold font-mono text-slate-500">#{cl.id}</td>
                  <td className="p-2.5 font-bold font-mono text-sky-800">{cl.scheme_id}</td>
                  <td className="p-2.5 font-mono font-bold text-slate-900">{cl.field || 'GENERAL'}</td>
                  <td className="p-2.5 font-mono text-rose-700 max-w-xs truncate">{cl.old_value || 'NULL'}</td>
                  <td className="p-2.5 font-mono text-emerald-700 max-w-xs truncate">{cl.new_value || 'UPDATED'}</td>
                  <td className="p-2.5 text-slate-600 max-w-xs truncate">{cl.reason || cl.source_document || 'Audit Verification'}</td>
                  <td className="p-2.5 text-slate-400 font-mono">{new Date(cl.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
