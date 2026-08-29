import React, { useState, useEffect } from 'react';
import { schemeApi, SchemeQueryParams } from '../api/schemeApi';
import { Scheme } from '../types';
import { SchemeCard } from '../components/SchemeCard';
import { Alert } from '../components/Alert';
import { Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react';

export const Schemes: React.FC = () => {
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filters state
  const [searchTerm, setSearchTerm] = useState('');
  const [verificationStatus, setVerificationStatus] = useState<string>('');
  const [schemeType, setSchemeType] = useState<string>('');
  const [sector, setSector] = useState<string>('');

  useEffect(() => {
    fetchSchemes();
  }, [page, verificationStatus, schemeType, sector]);

  const fetchSchemes = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const queryParams: SchemeQueryParams = {
        page,
        page_size: 12,
        search: searchTerm || undefined,
        verification_status: verificationStatus || undefined,
        scheme_type: schemeType || undefined,
        sector: sector || undefined,
      };

      const data = await schemeApi.getSchemes(queryParams);
      setSchemes(data.items);
      setTotal(data.total);
      setTotalPages(data.pages);
    } catch (err: any) {
      setErrorMsg('Failed to load schemes. ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchSchemes();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 flex items-center gap-2">
              <Search className="w-6 h-6 text-sky-600" />
              Find Government Schemes
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Explore {total} government welfare and credit schemes based on your needs, location, work, and income.
            </p>
          </div>
        </div>

        {/* Search & Filter Form */}
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 pt-2">
          {/* Search Input */}
          <div className="lg:col-span-2 relative">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search scheme name, ministry, target work..."
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          </div>

          {/* Verification Status */}
          <select
            value={verificationStatus}
            onChange={(e) => { setVerificationStatus(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white"
          >
            <option value="">All Verification Statuses</option>
            <option value="VERIFIED">Verified Schemes Only</option>
            <option value="UNVERIFIED">Under Review</option>
          </select>

          {/* Scheme Type */}
          <select
            value={schemeType}
            onChange={(e) => { setSchemeType(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white"
          >
            <option value="">All Scheme Types</option>
            <option value="LOAN">Loan Schemes</option>
            <option value="SUBSIDY">Subsidy Schemes</option>
            <option value="MICRO_FINANCE">Micro-Finance Schemes</option>
            <option value="TERM_LOAN">Term Loan Schemes</option>
          </select>

          {/* Search Button */}
          <button
            type="submit"
            className="bg-gov-blue hover:bg-gov-navy text-white font-bold py-2 px-4 rounded-lg text-xs shadow transition flex items-center justify-center gap-1.5"
          >
            <Filter className="w-3.5 h-3.5" />
            Apply Filters
          </button>
        </form>
      </div>

      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* Grid */}
      {isLoading ? (
        <div className="py-16 text-center">
          <div className="w-10 h-10 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs text-slate-500 mt-3 font-medium">Loading government scheme details...</p>
        </div>
      ) : schemes.length === 0 ? (
        <div className="py-16 text-center bg-white rounded-xl border border-slate-200">
          <Search className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No Schemes Matched Your Search</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
            Try adjusting your search keywords or clearing selected filters to view available schemes.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {schemes.map((scheme) => (
            <SchemeCard key={scheme.scheme_id} scheme={scheme} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-xs font-semibold text-slate-700">
          <span>Showing Page {page} of {totalPages} ({total} Total Schemes)</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded border border-slate-300 hover:bg-slate-50 disabled:opacity-40 flex items-center gap-1"
            >
              <ChevronLeft className="w-4 h-4" /> Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 rounded border border-slate-300 hover:bg-slate-50 disabled:opacity-40 flex items-center gap-1"
            >
              Next <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
