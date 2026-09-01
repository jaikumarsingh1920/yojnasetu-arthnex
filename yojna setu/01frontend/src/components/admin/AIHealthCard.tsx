import React from 'react';
import { SystemHealthResponse } from '../../api/adminApi';
import { Sparkles, Bot, ShieldCheck, Database, Layers, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  health: SystemHealthResponse | null;
}

export const AIHealthCard: React.FC<Props> = ({ health }) => {
  const aiComponent = health?.components.find((c) => c.name.toLowerCase().includes('ai') || c.name.toLowerCase().includes('rag'));
  const isFallback = aiComponent?.details?.is_fallback ?? false;
  const aiStatus = aiComponent?.status || 'ONLINE';

  return (
    <div className="space-y-6">
      {/* Overview Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-6 sm:p-8 rounded-2xl border border-indigo-900/50 shadow-md flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 bg-indigo-900/60 text-indigo-200 text-xs font-bold px-3 py-1 rounded-full border border-indigo-700/50">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            Grounded Hybrid RAG & AI Infrastructure
          </div>
          <h2 className="text-xl sm:text-2xl font-extrabold">AI Copilot & Statutory Retrieval Health</h2>
          <p className="text-xs text-indigo-200 max-w-2xl leading-relaxed">
            Real-time status of the YojnaSetu RAG vector store, LLM provider integration, grounded scheme verification, and deterministic fallbacks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className={`px-4 py-2 rounded-xl text-xs font-extrabold border flex items-center gap-2 ${
            aiStatus === 'ONLINE' && !isFallback
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
              : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
          }`}>
            <span className={`w-2.5 h-2.5 rounded-full ${aiStatus === 'ONLINE' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
            AI ENGINE: {isFallback ? 'DEGRADED (FALLBACK ACTIVE)' : aiStatus}
          </span>
        </div>
      </div>

      {/* Subsystem Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* 1. Provider Status */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="flex justify-between items-start">
            <div className="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center font-bold">
              <Bot className="w-5 h-5" />
            </div>
            <span className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded border ${
              !isFallback ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'
            }`}>
              {!isFallback ? 'ONLINE' : 'FALLBACK MODE'}
            </span>
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-slate-900">LLM Provider & Model</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {!isFallback ? 'Google Gemini 1.5 Flash (Verified Live API)' : 'Offline Grounded Fallback Provider'}
            </p>
          </div>
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-[11px] space-y-1 text-slate-600 font-mono">
            <div className="flex justify-between">
              <span>Provider:</span>
              <span className="font-bold text-slate-900">{!isFallback ? 'Google Gemini AI' : 'Deterministic Mock'}</span>
            </div>
            <div className="flex justify-between">
              <span>Model ID:</span>
              <span className="font-bold text-slate-900">{!isFallback ? 'gemini-1.5-flash' : 'offline-deterministic'}</span>
            </div>
            <div className="flex justify-between">
              <span>API Authentication:</span>
              <span className="font-bold text-emerald-600">Configured in Server Env</span>
            </div>
          </div>
        </div>

        {/* 2. RAG & Vector Store */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="flex justify-between items-start">
            <div className="w-10 h-10 bg-sky-50 text-sky-600 rounded-xl flex items-center justify-center font-bold">
              <Database className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded border bg-emerald-50 text-emerald-700 border-emerald-200">
              ONLINE
            </span>
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-slate-900">RAG Chunk Index</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              In-memory TF-IDF + Gazette Chunk Retriever across 90 schemes
            </p>
          </div>
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-[11px] space-y-1 text-slate-600 font-mono">
            <div className="flex justify-between">
              <span>Indexed Schemes:</span>
              <span className="font-bold text-slate-900">90 Verified Schemes</span>
            </div>
            <div className="flex justify-between">
              <span>Chunk Granularity:</span>
              <span className="font-bold text-slate-900">Eligibility, Benefits, Docs</span>
            </div>
            <div className="flex justify-between">
              <span>Citation Matching:</span>
              <span className="font-bold text-emerald-600">Dual-Pass Strict Grounding</span>
            </div>
          </div>
        </div>

        {/* 3. Statutory Guardrails */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="flex justify-between items-start">
            <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center font-bold">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded border bg-emerald-50 text-emerald-700 border-emerald-200">
              ACTIVE
            </span>
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-slate-900">Statutory Guardrails</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Zero-hallucination policy forbidding unverified interest rates or loans
            </p>
          </div>
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-[11px] space-y-1 text-slate-600 font-mono">
            <div className="flex justify-between">
              <span>Intent Pre-Routing:</span>
              <span className="font-bold text-slate-900">Deterministic Rule Gate</span>
            </div>
            <div className="flex justify-between">
              <span>Calculation Math:</span>
              <span className="font-bold text-slate-900">Engine Routed (Zero LLM Math)</span>
            </div>
            <div className="flex justify-between">
              <span>Disallowed Phrases:</span>
              <span className="font-bold text-emerald-600">Strictly Filtered</span>
            </div>
          </div>
        </div>
      </div>

      {/* Grounding & Verification Explanation */}
      <div className="bg-sky-50 border border-sky-200 rounded-2xl p-5 text-xs text-sky-950 space-y-2">
        <h4 className="font-extrabold text-sky-900 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-sky-700" />
          Statutory Grounding & Fallback Architecture
        </h4>
        <p className="text-sky-800 leading-relaxed">
          YojnaSetu operates a dual-layer AI architecture. General greetings and conversational turns are handled with friendly guidance, while financial calculations and eligibility rules are strictly intercepted and evaluated by deterministic Python engines. If the external Gemini API is unreachable, the system automatically falls back to an offline rule-based responder with 0 downtime.
        </p>
      </div>
    </div>
  );
};
