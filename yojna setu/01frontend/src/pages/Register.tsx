import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Alert } from '../components/Alert';
import { UserRole } from '../types';
import { UserPlus, Mail, Lock, Phone, Shield } from 'lucide-react';

export const Register: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('BENEFICIARY');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email && !phone) {
      setErrorMsg('Please provide either an email address or phone number.');
      return;
    }
    if (!password || password.length < 8) {
      setErrorMsg('Password must be at least 8 characters long.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      await register({
        email: email ? email.trim() : undefined,
        phone: phone ? phone.trim() : undefined,
        password
      });
      navigate('/dashboard');
    } catch (err: any) {
      let detail = 'Registration failed. User with this email/phone may already exist.';
      if (!err.response) {
        detail = 'Unable to connect to YojnaSetu server. Please try again.';
      } else if (typeof err.response?.data?.detail === 'string') {
        detail = err.response.data.detail;
      } else if (Array.isArray(err.response?.data?.detail)) {
        detail = err.response.data.detail.map((d: any) => d.msg).join(', ');
      }
      setErrorMsg(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto my-12 px-4">
      <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-lg space-y-6">
        <div className="text-center space-y-2">
          <img
            src="/logo.png"
            alt="YojnaSetu Logo"
            className="w-16 h-16 rounded-2xl mx-auto object-contain bg-slate-950 p-1.5 shadow-md border border-slate-700"
          />
          <h2 className="text-2xl font-extrabold text-slate-900">Create YojnaSetu Account</h2>
          <p className="text-xs text-slate-500">Register to apply for welfare schemes and track financing approvals</p>
        </div>

        {errorMsg && <Alert type="error">{errorMsg}</Alert>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Email Address
            </label>
            <div className="relative">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none"
              />
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Phone Number (Optional)
            </label>
            <div className="relative">
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="9876543210"
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none"
              />
              <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters"
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none"
              />
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Account Role Type
            </label>
            <div className="relative">
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as UserRole)}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none bg-white"
              >
                <option value="BENEFICIARY">BENEFICIARY (Individual / Business)</option>
                <option value="PARTNER_USER">PARTNER_USER (Agency Document Reviewer)</option>
                <option value="PARTNER_ADMIN">PARTNER_ADMIN (Agency Decision Admin)</option>
              </select>
              <Shield className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-gov-saffron hover:bg-orange-600 text-white font-bold py-3 rounded-lg text-sm shadow transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isSubmitting ? (
              <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <UserPlus className="w-4 h-4" />
                Complete Registration
              </>
            )}
          </button>
        </form>

        <div className="text-center pt-2 text-xs text-slate-600">
          Already registered?{' '}
          <Link to="/login" className="font-bold text-sky-700 hover:underline">
            Sign In Here
          </Link>
        </div>
      </div>
    </div>
  );
};
