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
                <th className="p-2.5">Action</th>
                <th className="p-2.5">Scheme</th>
                <th className="p-2.5">Field</th>
                <th className="p-2.5">Old Value</th>
                <th className="p-2.5">New Value</th>
                <th className="p-2.5">Admin User</th>
                <th className="p-2.5">Reason / Source</th>
                <th className="p-2.5">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-800">
              {changelogs.map((cl) => {
                const action = (cl.action || 'UPDATE').toUpperCase();
                const badgeColor =
                  action === 'CREATE'
                    ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                    : action === 'DEACTIVATE'
                    ? 'bg-rose-100 text-rose-800 border-rose-300'
                    : action === 'ACTIVATE'
                    ? 'bg-teal-100 text-teal-800 border-teal-300'
                    : 'bg-indigo-100 text-indigo-800 border-indigo-300';

                return (
                  <tr key={cl.id} className="hover:bg-slate-50">
                    <td className="p-2.5 font-bold font-mono text-slate-400">#{cl.id}</td>
                    <td className="p-2.5">
                      <span className={`inline-block px-2 py-0.5 text-[10px] font-extrabold rounded-md border ${badgeColor}`}>
                        {action}
                      </span>
                    </td>
                    <td className="p-2.5">
                      <div className="font-mono font-bold text-sky-800">{cl.scheme_id}</div>
                      {cl.scheme_name && cl.scheme_name !== cl.scheme_id && (
                        <div className="text-[11px] text-slate-500 truncate max-w-[200px]">{cl.scheme_name}</div>
                      )}
                    </td>
                    <td className="p-2.5 font-mono font-bold text-slate-900">{cl.field || 'GENERAL'}</td>
                    <td className="p-2.5 font-mono text-rose-700 max-w-xs truncate" title={cl.old_value || '—'}>
                      {cl.old_value || '—'}
                    </td>
                    <td className="p-2.5 font-mono text-emerald-700 max-w-xs truncate" title={cl.new_value || 'UPDATED'}>
                      {cl.new_value || 'UPDATED'}
                    </td>
                    <td className="p-2.5 text-slate-600 font-mono text-[11px] truncate max-w-[140px]" title={cl.admin_identifier || 'sysadmin'}>
                      {cl.admin_identifier || 'sysadmin'}
                    </td>
                    <td className="p-2.5 text-slate-600 max-w-xs truncate" title={cl.reason || cl.source_document || 'Administrative Update'}>
                      {cl.reason || cl.source_document || 'Administrative Update'}
                    </td>
                    <td className="p-2.5 text-slate-500 font-mono text-[11px] whitespace-nowrap">
                      {new Date(cl.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
