import React, { useState, useEffect } from 'react';
import { adminApi, RuleAuditItem } from '../../api/adminApi';
import { Filter, Search, Database } from 'lucide-react';

export const RuleAuditTable: React.FC = () => {
  const [rules, setRules] = useState<RuleAuditItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [schemeFilter, setSchemeFilter] = useState('');
  const [ruleTypeFilter, setRuleTypeFilter] = useState('');

  useEffect(() => {
    fetchRules();
  }, [schemeFilter, ruleTypeFilter]);

  const fetchRules = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getRuleAuditList({
        scheme_id: schemeFilter || undefined,
        rule_type: ruleTypeFilter || undefined,
        page_size: 100
      });
      setRules(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error('Failed to fetch rule audit list:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-4">
        <div>
          <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
            <Database className="w-5 h-5 text-indigo-600" />
            Database Rule Knowledge Audit ({total} Rules)
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">Authoritative condition rules used by Deterministic Eligibility & Financial engines.</p>
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
            value={ruleTypeFilter}
            onChange={(e) => setRuleTypeFilter(e.target.value)}
            className="px-3 py-1.5 border border-slate-300 rounded-lg text-slate-900 font-bold focus:outline-none focus:ring-2 focus:ring-rose-500"
          >
            <option value="">ALL RULE TYPES</option>
            <option value="HARD_GATE">HARD GATE</option>
            <option value="SOFT_FIT">SOFT FIT</option>
            <option value="FINANCIAL">FINANCIAL</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="py-8 text-center text-xs text-slate-500">Loading database rules...</div>
      ) : rules.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500">No database rules found matching selected filter.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                <th className="p-2.5">Rule ID</th>
                <th className="p-2.5">Scheme ID</th>
                <th className="p-2.5">Field</th>
                <th className="p-2.5">Operator</th>
                <th className="p-2.5">Value</th>
                <th className="p-2.5">Value Type</th>
                <th className="p-2.5">Rule Type</th>
                <th className="p-2.5">Priority</th>
                <th className="p-2.5">Group</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-800">
              {rules.map((r) => (
                <tr key={r.rule_id} className="hover:bg-slate-50">
                  <td className="p-2.5 font-bold font-mono text-sky-800">{r.rule_id}</td>
                  <td className="p-2.5 font-bold font-mono text-slate-900">{r.scheme_id}</td>
                  <td className="p-2.5 font-mono font-bold text-slate-800">{r.field}</td>
                  <td className="p-2.5 font-mono font-bold text-amber-700">{r.operator}</td>
                  <td className="p-2.5 font-mono text-slate-900 max-w-xs truncate">{r.value}</td>
                  <td className="p-2.5 font-mono text-slate-500">{r.value_type}</td>
                  <td className="p-2.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                      r.rule_type === 'HARD_GATE'
                        ? 'bg-rose-100 text-rose-800 border-rose-300'
                        : r.rule_type === 'FINANCIAL'
                        ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                        : 'bg-sky-100 text-sky-800 border-sky-300'
                    }`}>
                      {r.rule_type}
                    </span>
                  </td>
                  <td className="p-2.5"><span className="bg-slate-100 px-2 py-0.5 rounded font-bold text-[10px] border border-slate-300">{r.priority}</span></td>
                  <td className="p-2.5 font-mono text-slate-600">{r.condition_group}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
