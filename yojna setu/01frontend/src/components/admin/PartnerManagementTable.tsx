import React, { useState, useEffect } from 'react';
import { partnerApi } from '../../api/partnerApi';
import {
  Building2,
  Search,
  Filter,
  Plus,
  Edit3,
  Power,
  PowerOff,
  ShieldCheck,
  AlertCircle,
  ExternalLink,
  MapPin,
  Phone,
  Mail,
  Layers,
  CheckCircle2,
  X
} from 'lucide-react';
import { PartnerFormModal } from './PartnerFormModal';

export const PartnerManagementTable: React.FC = () => {
  const [partners, setPartners] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [totalActive, setTotalActive] = useState(0);
  const [totalInactive, setTotalInactive] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [districtFilter, setDistrictFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [partnerToEdit, setPartnerToEdit] = useState<any | null>(null);

  // Deactivate Modal
  const [targetPartner, setTargetPartner] = useState<any | null>(null);
  const [statusReason, setStatusReason] = useState('');
  const [isTogglingStatus, setIsTogglingStatus] = useState(false);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  // Scheme Linking Modal
  const [mappingTargetPartner, setMappingTargetPartner] = useState<any | null>(null);
  const [newSchemeId, setNewSchemeId] = useState('');
  const [newServiceType, setNewServiceType] = useState('FINANCING');
  const [newAuthLevel, setNewAuthLevel] = useState('SCHEME_ROUTE_VERIFIED');
  const [isLinkingScheme, setIsLinkingScheme] = useState(false);

  useEffect(() => {
    fetchPartners();
  }, [search, districtFilter, categoryFilter, statusFilter, page]);

  const fetchPartners = async () => {
    setIsLoading(true);
    try {
      const data = await partnerApi.getAdminPartners({
        search: search || undefined,
        district: districtFilter || undefined,
        partner_category: categoryFilter || undefined,
        status: statusFilter || undefined,
        page,
        page_size: 20,
      });
      setPartners(data.items || []);
      setTotal(data.total || 0);
      setTotalActive(data.total_active || 0);
      setTotalInactive(data.total_inactive || 0);
    } catch (err) {
      console.error('Failed to fetch admin partners:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleStatus = async () => {
    if (!targetPartner) return;
    setIsTogglingStatus(true);
    try {
      const newActive = !targetPartner.is_active;
      await partnerApi.updateAdminPartnerStatus(
        targetPartner.partner_id,
        newActive,
        statusReason || (newActive ? 'Reactivated by admin' : 'Deactivated by admin')
      );
      setSuccessBanner(`Partner '${targetPartner.name}' successfully ${newActive ? 'activated' : 'deactivated'}.`);
      setTargetPartner(null);
      setStatusReason('');
      fetchPartners();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to update partner status.');
    } finally {
      setIsTogglingStatus(false);
    }
  };

  const handleLinkScheme = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mappingTargetPartner || !newSchemeId.trim()) return;

    setIsLinkingScheme(true);
    try {
      await partnerApi.linkPartnerScheme(mappingTargetPartner.partner_id, {
        scheme_id: newSchemeId.trim(),
        service_type: newServiceType,
        authorization_level: newAuthLevel,
        reason: 'Official admin scheme mapping link',
      });
      setSuccessBanner(`Scheme '${newSchemeId}' successfully linked to '${mappingTargetPartner.name}'.`);
      setNewSchemeId('');
      setMappingTargetPartner(null);
      fetchPartners();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to link scheme.');
    } finally {
      setIsLinkingScheme(false);
    }
  };

  const handleUnlinkScheme = async (partnerId: string, schemeId: string) => {
    if (!confirm(`Are you sure you want to unlink scheme ${schemeId}?`)) return;
    try {
      await partnerApi.unlinkPartnerScheme(partnerId, schemeId, 'Unlinked by administrator');
      setSuccessBanner(`Scheme '${schemeId}' unlinked.`);
      fetchPartners();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to unlink scheme.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner Message */}
      {successBanner && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between text-xs text-emerald-900 shadow-sm animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="font-bold">{successBanner}</span>
          </div>
          <button onClick={() => setSuccessBanner(null)} className="text-slate-400 hover:text-slate-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-semibold">Total Partners</div>
          <div className="text-2xl font-black text-slate-900 mt-1">{total}</div>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="text-xs text-emerald-600 font-semibold">Active & Live</div>
          <div className="text-2xl font-black text-emerald-700 mt-1">{totalActive}</div>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-semibold">Deactivated</div>
          <div className="text-2xl font-black text-slate-600 mt-1">{totalInactive}</div>
        </div>
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <div className="text-xs text-indigo-600 font-semibold">Register Partner</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Add verified centre</div>
          </div>
          <button
            onClick={() => {
              setPartnerToEdit(null);
              setIsModalOpen(true);
            }}
            className="bg-indigo-600 hover:bg-indigo-700 text-white p-2.5 rounded-xl transition shadow-sm"
            title="Register new partner"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          {/* Search */}
          <div className="relative sm:col-span-2">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="Search by name, code, district, or partner ID..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3.5 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
            />
          </div>

          {/* Category Filter */}
          <div>
            <select
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-indigo-500 outline-none font-medium bg-white"
            >
              <option value="">All Categories</option>
              <option value="AUTHORIZED_SCHEME_PARTNER">Authorized Scheme Partner</option>
              <option value="IMPLEMENTING_ASSISTANCE_CENTRE">Assistance Centre</option>
              <option value="NEARBY_FINANCIAL_SERVICE_POINT">Financial Service Point</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-indigo-500 outline-none font-medium bg-white"
            >
              <option value="">All Statuses</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="INACTIVE">INACTIVE (Deactivated)</option>
            </select>
          </div>
        </div>

        {/* Quick District Focus */}
        <div className="flex items-center gap-2 text-[11px] pt-1">
          <span className="text-slate-400 font-bold text-[10px] uppercase tracking-wider">Quick Filter District:</span>
          {['Gorakhpur', 'Lucknow', 'Varanasi', 'Kanpur', 'Prayagraj', 'Deoria'].map(d => (
            <button
              key={d}
              onClick={() => {
                setDistrictFilter(districtFilter === d ? '' : d);
                setPage(1);
              }}
              className={`px-2.5 py-0.5 rounded-lg text-[10px] font-bold border transition ${
                districtFilter === d
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
              }`}
            >
              {d}
            </button>
          ))}
          {districtFilter && (
            <button
              onClick={() => {
                setDistrictFilter('');
                setPage(1);
              }}
              className="text-[10px] text-red-600 font-bold hover:underline ml-1"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Partners Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px] tracking-wider">
              <tr>
                <th className="p-3.5">Partner Details</th>
                <th className="p-3.5">Category & Type</th>
                <th className="p-3.5">Location</th>
                <th className="p-3.5">Contact</th>
                <th className="p-3.5">Schemes</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400">
                    Loading partner directory...
                  </td>
                </tr>
              ) : partners.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400">
                    No partner records found matching current filters.
                  </td>
                </tr>
              ) : (
                partners.map(p => (
                  <tr key={p.partner_id} className="hover:bg-slate-50/80 transition">
                    {/* Partner Details */}
                    <td className="p-3.5 max-w-xs">
                      <div className="font-bold text-slate-900 leading-snug">{p.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">{p.code}</div>
                    </td>

                    {/* Category & Type */}
                    <td className="p-3.5 whitespace-nowrap">
                      <div>
                        {p.partner_category === 'AUTHORIZED_SCHEME_PARTNER' && (
                          <span className="text-[10px] font-extrabold text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded-full">
                            AUTHORIZED
                          </span>
                        )}
                        {p.partner_category === 'IMPLEMENTING_ASSISTANCE_CENTRE' && (
                          <span className="text-[10px] font-extrabold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                            ASSISTANCE CENTRE
                          </span>
                        )}
                        {p.partner_category === 'NEARBY_FINANCIAL_SERVICE_POINT' && (
                          <span className="text-[10px] font-extrabold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                            FINANCIAL POINT
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1">
                        {p.institution_type || p.partner_type}
                      </div>
                    </td>

                    {/* Location */}
                    <td className="p-3.5">
                      <div className="font-bold text-slate-800">{p.district || '—'}</div>
                      <div className="text-[10px] text-slate-500">{p.state} {p.pincode ? `(${p.pincode})` : ''}</div>
                    </td>

                    {/* Contact */}
                    <td className="p-3.5">
                      {p.phone && <div className="text-[11px]">{p.phone}</div>}
                      {p.email && <div className="text-[10px] text-slate-400">{p.email}</div>}
                      {!p.phone && !p.email && <span className="text-slate-300">—</span>}
                    </td>

                    {/* Schemes */}
                    <td className="p-3.5 whitespace-nowrap">
                      <span className="bg-indigo-50 text-indigo-700 font-bold px-2 py-0.5 rounded-full text-[10px]">
                        {p.mapped_schemes_count} mapped
                      </span>
                    </td>

                    {/* Status */}
                    <td className="p-3.5 whitespace-nowrap">
                      {p.is_active ? (
                        <span className="bg-emerald-100 text-emerald-800 text-[10px] font-extrabold px-2 py-0.5 rounded-full">
                          ACTIVE
                        </span>
                      ) : (
                        <span className="bg-slate-200 text-slate-600 text-[10px] font-extrabold px-2 py-0.5 rounded-full">
                          DEACTIVATED
                        </span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="p-3.5 text-right whitespace-nowrap space-x-1">
                      <button
                        onClick={() => {
                          setPartnerToEdit(p);
                          setIsModalOpen(true);
                        }}
                        className="p-1.5 text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition"
                        title="Edit Partner"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => setMappingTargetPartner(p)}
                        className="p-1.5 text-slate-600 hover:text-sky-600 hover:bg-sky-50 rounded-lg transition"
                        title="Manage Scheme Links"
                      >
                        <Layers className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => setTargetPartner(p)}
                        className={`p-1.5 rounded-lg transition ${
                          p.is_active
                            ? 'text-slate-600 hover:text-red-600 hover:bg-red-50'
                            : 'text-emerald-600 hover:bg-emerald-50'
                        }`}
                        title={p.is_active ? 'Deactivate Partner' : 'Reactivate Partner'}
                      >
                        {p.is_active ? <PowerOff className="w-4 h-4" /> : <Power className="w-4 h-4" />}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Partner Form Modal (Add / Edit) */}
      <PartnerFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={(msg) => {
          setSuccessBanner(msg);
          fetchPartners();
        }}
        partnerToEdit={partnerToEdit}
      />

      {/* Status Toggle Modal */}
      {targetPartner && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-extrabold text-slate-900">
              {targetPartner.is_active ? 'Deactivate Partner' : 'Reactivate Partner'}
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Are you sure you want to {targetPartner.is_active ? 'deactivate' : 'reactivate'}{' '}
              <strong className="text-slate-800">{targetPartner.name}</strong> ({targetPartner.code})?
              {targetPartner.is_active
                ? ' This partner will no longer appear on public citizen maps or search results.'
                : ' This partner will become active and visible again in directory queries.'}
            </p>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Audit Reason for Status Change *
              </label>
              <textarea
                value={statusReason}
                onChange={(e) => setStatusReason(e.target.value)}
                placeholder="e.g. Branch merged / seasonal closure / administrative audit"
                rows={2}
                className="w-full text-xs p-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            <div className="flex justify-end items-center gap-2 pt-2">
              <button
                type="button"
                onClick={() => setTargetPartner(null)}
                className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleToggleStatus}
                disabled={isTogglingStatus}
                className={`px-4 py-2 text-xs font-bold text-white rounded-xl shadow-sm transition ${
                  targetPartner.is_active
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-emerald-600 hover:bg-emerald-700'
                }`}
              >
                {isTogglingStatus ? 'Processing...' : (targetPartner.is_active ? 'Confirm Deactivate' : 'Confirm Reactivate')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Scheme Mapping Modal */}
      {mappingTargetPartner && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-base font-extrabold text-slate-900">
                  Manage Scheme Authorizations
                </h3>
                <p className="text-xs text-slate-500">{mappingTargetPartner.name}</p>
              </div>
              <button onClick={() => setMappingTargetPartner(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Currently Mapped Schemes */}
            <div className="space-y-2">
              <div className="text-xs font-bold text-slate-700">Currently Linked Schemes:</div>
              {(!mappingTargetPartner.supported_schemes || mappingTargetPartner.supported_schemes.length === 0) ? (
                <div className="text-xs text-slate-400 italic bg-slate-50 p-3 rounded-xl">No schemes currently mapped.</div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {mappingTargetPartner.supported_schemes.map((sid: string) => (
                    <span
                      key={sid}
                      className="inline-flex items-center gap-1.5 bg-indigo-50 border border-indigo-200 text-indigo-800 text-xs font-bold px-2.5 py-1 rounded-lg"
                    >
                      {sid}
                      <button
                        type="button"
                        onClick={() => handleUnlinkScheme(mappingTargetPartner.partner_id, sid)}
                        className="text-indigo-400 hover:text-red-600 font-extrabold text-sm ml-1"
                        title="Unlink scheme"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Link New Scheme Form */}
            <form onSubmit={handleLinkScheme} className="pt-3 border-t border-slate-200 space-y-3">
              <div className="text-xs font-bold text-slate-800">Link an Authorized Scheme:</div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                  Scheme ID (e.g. SIH26092-001) *
                </label>
                <input
                  type="text"
                  value={newSchemeId}
                  onChange={(e) => setNewSchemeId(e.target.value)}
                  placeholder="SIH26092-001"
                  required
                  className="w-full text-xs px-3 py-2 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                    Service Type
                  </label>
                  <select
                    value={newServiceType}
                    onChange={(e) => setNewServiceType(e.target.value)}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                  >
                    <option value="FINANCING">FINANCING</option>
                    <option value="IMPLEMENTATION">IMPLEMENTATION</option>
                    <option value="TRAINING_EDP">TRAINING_EDP</option>
                    <option value="APPLICATION_ASSISTANCE">APPLICATION_ASSISTANCE</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                    Authorization Level
                  </label>
                  <select
                    value={newAuthLevel}
                    onChange={(e) => setNewAuthLevel(e.target.value)}
                    className="w-full text-xs px-3 py-2 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                  >
                    <option value="SCHEME_ROUTE_VERIFIED">SCHEME_ROUTE_VERIFIED</option>
                    <option value="AUTHORIZED_SCA">AUTHORIZED_SCA</option>
                    <option value="OFFICIAL_IMPLEMENTING_AGENCY">OFFICIAL_IMPLEMENTING_AGENCY</option>
                    <option value="TRAINING_PARTNER">TRAINING_PARTNER</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setMappingTargetPartner(null)}
                  className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Done
                </button>
                <button
                  type="submit"
                  disabled={isLinkingScheme}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl shadow-sm disabled:opacity-50"
                >
                  {isLinkingScheme ? 'Linking...' : 'Link Scheme'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
