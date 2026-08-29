import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { schemeApi } from '../api/schemeApi';
import { aiApi } from '../api/aiApi';
import { Scheme, AIChatResponse } from '../types';
import { VerificationBadge } from '../components/Badge';
import { Alert } from '../components/Alert';
import { OfficialPortalModal } from '../components/OfficialPortalModal';
import { savedSchemesApi } from '../api/savedSchemesApi';
import { SaveSchemeButton } from '../components/SaveSchemeButton';
import {
  Building2,
  FileText,
  ShieldCheck,
  ArrowLeft,
  Info,
  Bot,
  Send,
  BookmarkCheck,
  ExternalLink,
  CheckCircle2,
  Mail,
} from 'lucide-react';

export const SchemeDetail: React.FC = () => {
  const { schemeId } = useParams<{ schemeId: string }>();

  const [scheme, setScheme] = useState<Scheme | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailFeedback, setEmailFeedback] = useState<{ message: string; success: boolean } | null>(null);

  // Scheme-specific AI Chat State
  const [chatMessage, setChatMessage] = useState('');
  const [chatResult, setChatResult] = useState<AIChatResponse | null>(null);
  const [isChatLoading, setIsChatLoading] = useState(false);

  useEffect(() => {
    if (schemeId) {
      fetchSchemeDetail(schemeId);
    }
  }, [schemeId]);

  const fetchSchemeDetail = async (id: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await schemeApi.getSchemeById(id);
      setScheme(data);
    } catch (err: any) {
      setErrorMsg('Failed to load scheme detail. ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmailScheme = async () => {
    if (!schemeId) return;
    setEmailLoading(true);
    setEmailFeedback(null);
    try {
      const res = await savedSchemesApi.emailScheme(schemeId);
      setEmailFeedback({ message: res.message, success: res.sent });
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Email delivery service is not configured yet.';
      setEmailFeedback({ message: msg, success: false });
    } finally {
      setEmailLoading(false);
    }
  };

  const handleAskSchemeAI = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!schemeId || !chatMessage.trim()) return;

    setIsChatLoading(true);
    try {
      const res = await aiApi.askAboutScheme(schemeId, { message: chatMessage });
      setChatResult(res);
    } catch (err: any) {
      setErrorMsg('AI guidance failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsChatLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-gov-saffron border-t-transparent" />
      </div>
    );
  }

  if (errorMsg || !scheme) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 space-y-4">
        <Alert type="error">{errorMsg || 'Scheme not found.'}</Alert>
        <Link to="/schemes" className="text-sky-700 font-bold text-xs hover:underline flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Back to Scheme Search
        </Link>
      </div>
    );
  }

  const officialUrl = scheme.application_url || scheme.official_portal || scheme.official_source_url;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back Button */}
      <Link to="/schemes" className="text-xs font-bold text-slate-600 hover:text-sky-700 flex items-center gap-1 transition">
        <ArrowLeft className="w-4 h-4" /> Back to All Schemes
      </Link>

      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-gov-blue via-gov-navy to-slate-900 text-white rounded-3xl p-8 shadow-xl border-b-4 border-gov-saffron relative overflow-hidden space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="bg-gov-saffron text-white px-2.5 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wider">
                {scheme.scheme_type || "CENTRAL SCHEME"}
              </span>
              <span className="font-mono text-xs text-slate-300 bg-slate-800 px-2 py-0.5 rounded">
                ID: {scheme.scheme_id}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {scheme.scheme_name}
            </h1>
            <p className="text-xs text-slate-300 flex items-center gap-2">
              <Building2 className="w-4 h-4 text-gov-saffron" />
              {scheme.ministry || scheme.implementing_agency || "Government of India"}
            </p>
          </div>

          <div className="flex flex-col items-end gap-3">
            {scheme.verifications && scheme.verifications.length > 0 && (
              <VerificationBadge status={scheme.verifications[0].status} />
            )}
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <SaveSchemeButton schemeId={scheme.scheme_id} size="md" />
            
            <button
              onClick={handleEmailScheme}
              disabled={emailLoading}
              className="bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs px-4 py-2.5 rounded-xl border border-slate-700 transition flex items-center gap-1.5 shadow-sm"
              title="Send scheme details to registered email"
            >
              <Mail className="w-4 h-4 text-sky-400" />
              {emailLoading ? 'Sending...' : 'Email Me This Scheme'}
            </button>

            <button
              onClick={() => setIsModalOpen(true)}
              className="bg-gov-saffron hover:bg-orange-600 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-lg transition flex items-center gap-2"
            >
              Apply on Official Portal <ExternalLink className="w-4 h-4" />
            </button>
          </div>
          </div>
        </div>
      </div>

      {emailFeedback && (
        <Alert type={emailFeedback.success ? 'success' : 'info'}>
          {emailFeedback.message}
        </Alert>
      )}

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Columns: Scheme Details */}
        <div className="lg:col-span-2 space-y-8">
          {/* Overview */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-slate-900 border-b border-slate-200 pb-3 flex items-center gap-2">
              <Info className="w-5 h-5 text-sky-600" /> Scheme Purpose & Objective
            </h2>
            <p className="text-xs text-slate-600 leading-relaxed">
              {scheme.objective || "Verified scheme under Government of India welfare guidelines."}
            </p>
          </div>

          {/* Rules List */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex justify-between items-center border-b border-slate-200 pb-3">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" /> Eligibility Criteria & Guidelines ({scheme.rules?.length || 0})
              </h2>
            </div>

            <div className="bg-sky-50 border border-sky-200 p-3.5 rounded-xl text-xs text-sky-900 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-sky-700 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Eligibility Guidance Note</p>
                <p className="text-[11px] text-sky-800 mt-0.5">
                  Based on the information provided, you appear to meet the listed eligibility criteria. Final eligibility, document verification, and sanctioning are determined exclusively by the concerned official authority.
                </p>
              </div>
            </div>

            {!scheme.rules || scheme.rules.length === 0 ? (
              <p className="text-xs text-slate-500 italic">Standard government scheme conditions apply.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {scheme.rules.map((rule) => (
                  <div key={rule.rule_id} className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-xs space-y-1">
                    <div className="flex items-center justify-between font-bold text-slate-800">
                      <span className="font-mono text-gov-navy text-[11px]">{rule.rule_id}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                        rule.rule_type === 'ELIGIBILITY' ? 'bg-sky-100 text-sky-800' : 'bg-emerald-100 text-emerald-800'
                      }`}>
                        {rule.rule_type}
                      </span>
                    </div>
                    <p className="text-slate-700 font-medium capitalize">
                      {rule.field.replace(/_/g, ' ')} {rule.operator} {rule.value}
                    </p>
                    {rule.error_message && <p className="text-[11px] text-slate-500">{rule.error_message}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Interactive AI Q&A Widget */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-md p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Bot className="w-5 h-5 text-sky-600" /> Ask AI Guidance About This Scheme
              </h2>
              <span className="text-[11px] bg-emerald-50 text-emerald-800 font-bold px-2.5 py-0.5 rounded-full border border-emerald-200">
                Government Verified Information
              </span>
            </div>

            <form onSubmit={handleAskSchemeAI} className="flex gap-2">
              <input
                type="text"
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder="Ask about EMI, interest rate, documents, or how to apply..."
                className="flex-1 rounded-xl border-slate-300 text-xs p-3 shadow-sm focus:border-sky-500 focus:ring-sky-500 border outline-none"
              />
              <button
                type="submit"
                disabled={isChatLoading || !chatMessage.trim()}
                className="bg-gov-blue hover:bg-gov-navy text-white font-bold text-xs px-5 py-3 rounded-xl shadow transition flex items-center gap-1.5 disabled:opacity-50"
              >
                {isChatLoading ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Send className="w-4 h-4" /> Ask
                  </>
                )}
              </button>
            </form>

            {chatResult && (
              <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 text-xs text-slate-700">
                <div className="font-bold text-slate-900 flex items-center gap-1.5">
                  <Bot className="w-4 h-4 text-sky-600" /> Answer:
                </div>
                <div className="whitespace-pre-wrap font-sans leading-relaxed text-slate-800">{chatResult.answer}</div>

                {chatResult.citations && chatResult.citations.length > 0 && (
                  <div className="pt-2 border-t border-slate-200 space-y-1.5">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                      <BookmarkCheck className="w-3.5 h-3.5 text-emerald-600" /> Sources:
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {chatResult.citations.map((cite, i) => (
                        <div key={i} className="bg-white p-2.5 rounded-lg border border-slate-200 text-[11px] text-slate-600 space-y-1">
                          <span className="font-bold text-slate-800 block">Verified Information</span>
                          <p className="line-clamp-2 italic text-slate-500">"{cite.snippet}"</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Required Documents Checklist & Official Link */}
        <div className="space-y-8">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-slate-200 pb-3">
              <FileText className="w-5 h-5 text-amber-600" /> Optional Document Checklist ({scheme.documents?.length || 0})
            </h3>

            {!scheme.documents || scheme.documents.length === 0 ? (
              <p className="text-xs text-slate-500 italic">Standard identity proof & project details required.</p>
            ) : (
              <ul className="space-y-2.5 text-xs">
                {scheme.documents.map((doc) => (
                  <li key={doc.document_id} className="bg-slate-50 p-3 rounded-lg border border-slate-200 flex items-start justify-between gap-2">
                    <div>
                      <span className="font-bold text-slate-800 block">✓ {doc.document_name}</span>
                      {doc.condition && <span className="text-[11px] text-slate-500">{doc.condition}</span>}
                    </div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded border uppercase bg-sky-50 text-sky-800 border-sky-200 shrink-0">
                      {doc.requirement_type}
                    </span>
                  </li>
                ))}
              </ul>
            )}

            <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500 italic">
              * Final document requirements may vary. Please verify them on the official application portal.
            </div>
          </div>

          <div className="bg-slate-900 text-white p-6 rounded-2xl space-y-3 shadow-lg">
            <h4 className="text-sm font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
              <ExternalLink className="w-4 h-4" /> Official Application Portal
            </h4>
            <p className="text-xs text-slate-300">
              YojnaSetu helps you discover schemes and understand requirements. Final application submission and approval are performed on the official government website.
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="w-full mt-2 bg-gov-saffron hover:bg-orange-600 text-white font-bold py-3 rounded-xl text-xs transition shadow-lg flex items-center justify-center gap-1.5"
            >
              Apply on Official Portal <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Official Portal Safety Dialog */}
      <OfficialPortalModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        officialUrl={officialUrl}
        schemeName={scheme.scheme_name}
      />
    </div>
  );
};
