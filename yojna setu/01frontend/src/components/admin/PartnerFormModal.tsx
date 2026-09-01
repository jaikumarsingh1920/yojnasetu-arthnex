import React, { useState, useEffect } from 'react';
import { partnerApi, PartnerData } from '../../api/partnerApi';
import { X, Building2, Save, AlertCircle, ShieldCheck, MapPin, Phone, Mail, Globe, ExternalLink } from 'lucide-react';

interface PartnerFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (msg: string) => void;
  partnerToEdit: any | null;
}

export const PartnerFormModal: React.FC<PartnerFormModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  partnerToEdit,
}) => {
  const isEditing = Boolean(partnerToEdit);

  const [formData, setFormData] = useState({
    name: '',
    code: '',
    partner_type: 'PUBLIC_SECTOR_BANK',
    institution_type: 'PUBLIC_SECTOR_BANK',
    partner_category: 'AUTHORIZED_SCHEME_PARTNER',
    district: '',
    state: 'Uttar Pradesh',
    pincode: '',
    phone: '',
    email: '',
    website: '',
    address: '',
    latitude: '',
    longitude: '',
    source_url: '',
    verification_status: 'VERIFIED_OFFICIAL',
    change_reason: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (partnerToEdit) {
      setFormData({
        name: partnerToEdit.name || '',
        code: partnerToEdit.code || '',
        partner_type: partnerToEdit.partner_type || 'PUBLIC_SECTOR_BANK',
        institution_type: partnerToEdit.institution_type || partnerToEdit.partner_type || 'PUBLIC_SECTOR_BANK',
        partner_category: partnerToEdit.partner_category || 'AUTHORIZED_SCHEME_PARTNER',
        district: partnerToEdit.district || '',
        state: partnerToEdit.state || 'Uttar Pradesh',
        pincode: partnerToEdit.pincode || '',
        phone: partnerToEdit.phone || '',
        email: partnerToEdit.email || '',
        website: partnerToEdit.website || '',
        address: partnerToEdit.address || '',
        latitude: partnerToEdit.latitude !== undefined && partnerToEdit.latitude !== null ? String(partnerToEdit.latitude) : '',
        longitude: partnerToEdit.longitude !== undefined && partnerToEdit.longitude !== null ? String(partnerToEdit.longitude) : '',
        source_url: partnerToEdit.source_url || '',
        verification_status: partnerToEdit.verification_status || 'VERIFIED_OFFICIAL',
        change_reason: '',
      });
    } else {
      setFormData({
        name: '',
        code: '',
        partner_type: 'PUBLIC_SECTOR_BANK',
        institution_type: 'PUBLIC_SECTOR_BANK',
        partner_category: 'AUTHORIZED_SCHEME_PARTNER',
        district: 'Gorakhpur',
        state: 'Uttar Pradesh',
        pincode: '',
        phone: '',
        email: '',
        website: '',
        address: '',
        latitude: '',
        longitude: '',
        source_url: '',
        verification_status: 'VERIFIED_OFFICIAL',
        change_reason: '',
      });
    }
    setErrorMsg(null);
  }, [partnerToEdit, isOpen]);

  if (!isOpen) return null;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!formData.name.trim() || !formData.code.trim()) {
      setErrorMsg('Partner name and code are required.');
      return;
    }

    const payload: any = {
      name: formData.name.trim(),
      code: formData.code.trim(),
      partner_type: formData.partner_type,
      institution_type: formData.institution_type || formData.partner_type,
      partner_category: formData.partner_category,
      district: formData.district.trim() || null,
      state: formData.state.trim() || null,
      pincode: formData.pincode.trim() || null,
      phone: formData.phone.trim() || null,
      email: formData.email.trim() || null,
      website: formData.website.trim() || null,
      address: formData.address.trim() || null,
      source_url: formData.source_url.trim() || null,
      verification_status: formData.verification_status,
      change_reason: formData.change_reason.trim() || (isEditing ? 'Administrative details update' : 'Official partner addition'),
    };

    if (formData.latitude.trim() && formData.longitude.trim()) {
      const lat = parseFloat(formData.latitude);
      const lng = parseFloat(formData.longitude);
      if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
        payload.latitude = lat;
        payload.longitude = lng;
      } else {
        setErrorMsg('Invalid latitude (-90 to 90) or longitude (-180 to 180).');
        return;
      }
    }

    setIsSubmitting(true);
    try {
      if (isEditing) {
        await partnerApi.updateAdminPartner(partnerToEdit.partner_id, payload);
        onSuccess(`Partner '${payload.name}' updated successfully.`);
      } else {
        await partnerApi.createAdminPartner(payload);
        onSuccess(`Partner '${payload.name}' created successfully.`);
      }
      onClose();
    } catch (err: any) {
      console.error('Failed to save partner:', err);
      setErrorMsg(err?.response?.data?.detail || 'Failed to save partner record.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-2xl w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 p-6 text-white flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-lg font-extrabold tracking-tight">
                {isEditing ? `Edit Partner: ${partnerToEdit.code}` : 'Register Verified Channel Partner'}
              </h2>
              <p className="text-xs text-slate-300">
                Official Directory Governance & Scheme Authorizations
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="m-6 mb-0 p-3.5 bg-red-50 border border-red-200 rounded-2xl flex items-start gap-2.5 text-xs text-red-800">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          {/* Row 1: Name and Code */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Partner / Branch Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="e.g. Bank of Baroda MSME Gorakhpur"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Branch / Entity Code *
              </label>
              <input
                type="text"
                name="code"
                value={formData.code}
                onChange={handleChange}
                required
                placeholder="e.g. BOB-MSME-GKP-01"
                disabled={isEditing}
                className={`w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium ${
                  isEditing ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : ''
                }`}
              />
            </div>
          </div>

          {/* Row 2: Category and Institution Type */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Partner Category *
              </label>
              <select
                name="partner_category"
                value={formData.partner_category}
                onChange={handleChange}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium bg-white"
              >
                <option value="AUTHORIZED_SCHEME_PARTNER">AUTHORIZED_SCHEME_PARTNER (Official Scheme Financing/Channel)</option>
                <option value="IMPLEMENTING_ASSISTANCE_CENTRE">IMPLEMENTING_ASSISTANCE_CENTRE (DIC, KVIC, RSETI, CSC)</option>
                <option value="NEARBY_FINANCIAL_SERVICE_POINT">NEARBY_FINANCIAL_SERVICE_POINT (General Branch Route)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Institution Type
              </label>
              <select
                name="institution_type"
                value={formData.institution_type}
                onChange={handleChange}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium bg-white"
              >
                <option value="PUBLIC_SECTOR_BANK">Public Sector Bank (PSB)</option>
                <option value="REGIONAL_RURAL_BANK">Regional Rural Bank (RRB)</option>
                <option value="STATE_CHANNELIZING_AGENCY">State Channelizing Agency (SCA)</option>
                <option value="DISTRICT_INDUSTRIES_CENTRE">District Industries Centre (DIC)</option>
                <option value="COMMISSION_OFFICE">Commission Office (KVIC / KVIB)</option>
                <option value="RSETI_TRAINING_INSTITUTE">RSETI Training Institute</option>
                <option value="COOPERATIVE_BANK">Cooperative Bank</option>
                <option value="MICRO_FINANCE_INSTITUTION">Micro Finance Institution (NBFC-MFI)</option>
              </select>
            </div>
          </div>

          {/* Row 3: Address */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Physical Address
            </label>
            <input
              type="text"
              name="address"
              value={formData.address}
              onChange={handleChange}
              placeholder="e.g. Bank Road, Bargadwa, Gorakhpur, UP 273007"
              className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
            />
          </div>

          {/* Row 4: District, State, Pincode */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                District
              </label>
              <input
                type="text"
                name="district"
                value={formData.district}
                onChange={handleChange}
                placeholder="e.g. Gorakhpur"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                State
              </label>
              <input
                type="text"
                name="state"
                value={formData.state}
                onChange={handleChange}
                placeholder="e.g. Uttar Pradesh"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Pincode
              </label>
              <input
                type="text"
                name="pincode"
                value={formData.pincode}
                onChange={handleChange}
                placeholder="e.g. 273001"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
              />
            </div>
          </div>

          {/* Row 5: Phone and Email */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Verified Phone Number
              </label>
              <input
                type="text"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="e.g. 0551-2282215"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Verified Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="e.g. branch@bankofbaroda.co.in"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
              />
            </div>
          </div>

          {/* Row 6: Website and Coordinates */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Official Website
              </label>
              <input
                type="url"
                name="website"
                value={formData.website}
                onChange={handleChange}
                placeholder="https://..."
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Latitude
              </label>
              <input
                type="number"
                step="any"
                name="latitude"
                value={formData.latitude}
                onChange={handleChange}
                placeholder="26.7865"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Longitude
              </label>
              <input
                type="number"
                step="any"
                name="longitude"
                value={formData.longitude}
                onChange={handleChange}
                placeholder="83.3512"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
              />
            </div>
          </div>

          {/* Row 7: Official Source URL and Verification Status */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Official Source URL
              </label>
              <input
                type="url"
                name="source_url"
                value={formData.source_url}
                onChange={handleChange}
                placeholder="https://msme.up.gov.in/..."
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Verification Status
              </label>
              <select
                name="verification_status"
                value={formData.verification_status}
                onChange={handleChange}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium bg-white"
              >
                <option value="VERIFIED_OFFICIAL">VERIFIED_OFFICIAL (Statutory / Bank Verified)</option>
                <option value="NEEDS_VERIFICATION">NEEDS_VERIFICATION</option>
              </select>
            </div>
          </div>

          {/* Changelog Reason */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Audit Changelog Reason
            </label>
            <input
              type="text"
              name="change_reason"
              value={formData.change_reason}
              onChange={handleChange}
              placeholder={isEditing ? 'e.g. Updated branch contact and verified coordinates' : 'e.g. Added verified Gorakhpur MSME branch'}
              className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none font-medium"
            />
          </div>

          {/* Form Actions */}
          <div className="pt-4 border-t border-slate-200 flex justify-end items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-extrabold rounded-xl shadow-md transition flex items-center gap-2 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {isSubmitting ? 'Saving...' : (isEditing ? 'Update Partner' : 'Save Partner')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
