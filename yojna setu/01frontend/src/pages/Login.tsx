import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Alert } from '../components/Alert';
import { LogIn, Lock, Mail, ShieldCheck } from 'lucide-react';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setErrorMsg('Please provide both email/phone and password.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const loginRes = await login({ username: username.trim(), password });
      const userRole = loginRes?.user?.role;
      const targetFrom = (location.state as any)?.from?.pathname;

      if (targetFrom && targetFrom !== '/' && targetFrom !== '/login') {
        navigate(targetFrom, { replace: true });
      } else if (userRole === 'SYSTEM_ADMIN') {
        navigate('/admin', { replace: true });
      } else if (userRole === 'PARTNER_USER' || userRole === 'PARTNER_ADMIN') {
        navigate('/partner', { replace: true });
      } else {
        navigate('/dashboard', { replace: true });
      }
    } catch (err: any) {
      let detail = 'Invalid email/phone or password.';
      if (!err.response) {
        detail = 'Unable to connect to YojnaSetu server. Please try again.';
      } else if (err.response.status === 401) {
        detail = 'Invalid email/phone or password.';
      } else if (err.response.status === 403) {
        detail = 'User account is deactivated.';
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
          <h2 className="text-2xl font-extrabold text-slate-900">Sign In to YojnaSetu</h2>
          <p className="text-xs text-slate-500">Access scheme discovery, application workflow, and partner reviews</p>
        </div>

        {errorMsg && <Alert type="error">{errorMsg}</Alert>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Email or Phone Number
            </label>
            <div className="relative">
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. ben10@example.com or admin@yojnasetu.gov.in"
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none"
              />
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
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
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none"
              />
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-gov-blue hover:bg-gov-navy text-white font-bold py-3 rounded-lg text-sm shadow transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isSubmitting ? (
              <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                Sign In
              </>
            )}
          </button>
        </form>

        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs text-slate-700 space-y-2">
          <p className="font-extrabold text-slate-900 flex items-center gap-1.5 border-b border-slate-200 pb-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            Development / Test Credentials:
          </p>
          <div className="space-y-1.5 text-[11px]">
            <p>• <span className="font-bold text-slate-800">Beneficiary:</span> <code className="bg-slate-200/80 text-slate-900 font-mono px-1.5 py-0.5 rounded border border-slate-300 font-bold">ben10@example.com / Secret123!</code></p>
            <p>• <span className="font-bold text-slate-800">Partner User:</span> <code className="bg-slate-200/80 text-slate-900 font-mono px-1.5 py-0.5 rounded border border-slate-300 font-bold">p1user@example.com / Secret123!</code></p>
            <p>• <span className="font-bold text-slate-800">Partner Admin:</span> <code className="bg-slate-200/80 text-slate-900 font-mono px-1.5 py-0.5 rounded border border-slate-300 font-bold">p1admin@example.com / Secret123!</code></p>
            <p>• <span className="font-bold text-slate-800">System Admin:</span> <code className="bg-slate-200/80 text-slate-900 font-mono px-1.5 py-0.5 rounded border border-slate-300 font-bold">admin@yojnasetu.gov.in / Secret123!</code></p>
          </div>
        </div>

        <div className="text-center pt-2 text-xs text-slate-600">
          Don't have an account yet?{' '}
          <Link to="/register" className="font-bold text-sky-700 hover:underline">
            Register Here
          </Link>
        </div>
      </div>
    </div>
  );
};
