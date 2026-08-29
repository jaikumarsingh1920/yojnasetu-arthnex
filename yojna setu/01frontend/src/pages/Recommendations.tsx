import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { recommendationApi } from '../api/recommendationApi';
import { aiApi } from '../api/aiApi';
import {
  BeneficiaryProfileInput,
  RecommendationResponse,
  AIExplainableRecommendationResponse,
  NaturalLanguageExtractResponse,
} from '../types';
import { Alert } from '../components/Alert';
import { OfficialPortalModal } from '../components/OfficialPortalModal';
import { SaveSchemeButton } from '../components/SaveSchemeButton';
import {
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Award,
  Bot,
  Send,
  Mic,
  MicOff,
  PenTool,
  ListFilter,
  Check,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  FileText
} from 'lucide-react';

type InputMode = 'TYPE' | 'VOICE' | 'FORM';

export const Recommendations: React.FC = () => {
  // Mode Selection State
  const [inputMode, setInputMode] = useState<InputMode>('TYPE');

  // Text & Voice Input State
  const [userText, setUserText] = useState(
    'I am a 28 year old woman from Uttar Pradesh. I belong to SC category. My annual income is around 1.8 lakh. I want to start a small tailoring business with a project cost of 1 lakh.'
  );

  // Speech Recognition State
  const [isListening, setIsListening] = useState<boolean>(false);
  const [recognitionInstance, setRecognitionInstance] = useState<any>(null);

  // Quick Form State
  const [formAge, setFormAge] = useState<number>(28);
  const [formGender, setFormGender] = useState<string>('FEMALE');
  const [formState, setFormState] = useState<string>('UTTAR_PRADESH');
  const [formSocialCategory, setFormSocialCategory] = useState<string>('SC');
  const [formIncomeSlab, setFormIncomeSlab] = useState<number>(180000);
  const [formNeed, setFormNeed] = useState<string>('START_BUSINESS');
  const [formBusinessStage, setFormBusinessStage] = useState<string>('NEW');
  const [formProjectCostSlab, setFormProjectCostSlab] = useState<number>(100000);
  const [formLoanRequired, setFormLoanRequired] = useState<boolean>(true);

  // Recommendation Results State
  const [topK] = useState(5);
  const [aiResult, setAiResult] = useState<AIExplainableRecommendationResponse | null>(null);
  const [standardResult, setStandardResult] = useState<RecommendationResponse | null>(null);
  const [extractionResult, setExtractionResult] = useState<NaturalLanguageExtractResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Modal State for Official Portal Redirection
  const [selectedSchemeForModal, setSelectedSchemeForModal] = useState<{ name: string; url?: string | null } | null>(null);

  // Track expanded transparency details per scheme
  const [expandedDetails, setExpandedDetails] = useState<Record<string, boolean>>({});

  // Initialize Speech Recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'hi-IN';

      recognition.onresult = (event: any) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        if (transcript.trim()) {
          setUserText(prev => (prev ? `${prev} ${transcript}` : transcript));
        }
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      setRecognitionInstance(recognition);
    }
  }, []);

  const toggleSpeechListening = () => {
    if (!recognitionInstance) {
      alert('Speech recognition is not supported in your browser. Please type or select from the form.');
      return;
    }
    if (isListening) {
      recognitionInstance.stop();
      setIsListening(false);
    } else {
      try {
        recognitionInstance.start();
        setIsListening(true);
      } catch (err) {
        console.error('Error starting recognition:', err);
      }
    }
  };

  const toggleDetails = (schemeId: string) => {
    setExpandedDetails(prev => ({ ...prev, [schemeId]: !prev[schemeId] }));
  };

  const buildProfileFromForm = (): BeneficiaryProfileInput => {
    let sector = 'MICRO_FINANCE';
    let activity = 'SMALL_MICRO_BUSINESS';

    if (formNeed === 'START_BUSINESS') {
      sector = 'MICRO_FINANCE';
      activity = 'SMALL_MICRO_BUSINESS';
    } else if (formNeed === 'EXPAND_BUSINESS') {
      sector = 'MICRO_FINANCE';
      activity = 'BUSINESS_EXPANSION';
    } else if (formNeed === 'EDUCATION') {
      sector = 'EDUCATION';
      activity = 'HIGHER_EDUCATION';
    } else if (formNeed === 'SKILL_TRAINING') {
      sector = 'SKILL_DEVELOPMENT';
      activity = 'VOCATIONAL_TRAINING';
    } else if (formNeed === 'AGRICULTURE') {
      sector = 'AGRICULTURE';
      activity = 'FARMING_ALLIED';
    } else if (formNeed === 'HOUSING') {
      sector = 'HOUSING';
      activity = 'HOME_RENOVATION';
    }

    return {
      age: formAge,
      gender: formGender,
      state: formState,
      social_category: formSocialCategory === 'NOT_SPECIFIED' ? 'GENERAL' : formSocialCategory,
      is_sc: formSocialCategory === 'SC',
      annual_income: formIncomeSlab,
      sector: sector,
      activity_type: activity,
      business_stage: formBusinessStage,
      is_new_unit: formBusinessStage === 'NEW' || formBusinessStage === 'CONCEPT',
      project_cost: formProjectCostSlab,
      requested_loan_amount: formLoanRequired ? Math.round(formProjectCostSlab * 0.9) : 0,
      applicant_type: 'INDIVIDUAL',
    };
  };

  const handleFindSchemes = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);
    setAiResult(null);
    setStandardResult(null);

    try {
      if (inputMode === 'FORM') {
        const formProfile = buildProfileFromForm();
        const res = await recommendationApi.getRecommendations(formProfile, topK);
        setStandardResult(res);
      } else {
        const ext = await aiApi.extractProfile(userText);
        setExtractionResult(ext);

        const aiRes = await aiApi.getAIRecommendations({
          user_text: userText,
          profile: ext.extracted_profile,
          top_k: topK,
        });
        setAiResult(aiRes);
      }
    } catch (err: any) {
      setErrorMsg('Could not find recommendations: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const openPortalModal = (schemeName: string, officialUrl?: string | null) => {
    setSelectedSchemeForModal({ name: schemeName, url: officialUrl });
  };

  const getMatchLabel = (score: number) => {
    if (score >= 85) return 'Strong Match';
    if (score >= 70) return 'Good Match';
    return 'Moderate Match';
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div className="bg-gradient-to-r from-gov-blue via-gov-navy to-slate-900 text-white rounded-3xl p-8 shadow-xl border-b-4 border-gov-saffron relative overflow-hidden">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 bg-gov-saffron/20 border border-gov-saffron/40 text-gov-saffron px-3.5 py-1 rounded-full text-xs font-bold tracking-wide">
            <ShieldCheck className="w-4 h-4 text-emerald-400" /> ✓ Verified Government Scheme Discovery Platform
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Find Government Schemes & Official Application Portals
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Tell us about your needs to get personalized scheme recommendations, eligibility guidance, document checklists, and direct links to apply on official government portals.
          </p>
        </div>
      </div>

      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* 3-Way Choice Cards Header */}
      <div className="space-y-4">
        <h2 className="text-base font-extrabold text-slate-900 text-center sm:text-left">
          How would you like to tell us about yourself?
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <button
            type="button"
            onClick={() => setInputMode('TYPE')}
            className={`p-5 rounded-2xl border text-left transition flex flex-col justify-between space-y-3 ${
              inputMode === 'TYPE'
                ? 'bg-sky-50 border-sky-600 ring-2 ring-sky-500 shadow-md'
                : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-800 flex items-center justify-center font-bold">
                <PenTool className="w-5 h-5" />
              </div>
              {inputMode === 'TYPE' && <Check className="w-5 h-5 text-sky-600 font-extrabold" />}
            </div>
            <div>
              <h3 className="font-extrabold text-slate-900 text-sm">✍️ Type</h3>
              <p className="text-xs text-slate-500 mt-0.5">Tell us in your own words</p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => setInputMode('VOICE')}
            className={`p-5 rounded-2xl border text-left transition flex flex-col justify-between space-y-3 ${
              inputMode === 'VOICE'
                ? 'bg-amber-50 border-gov-saffron ring-2 ring-gov-saffron shadow-md'
                : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-amber-100 text-gov-saffron flex items-center justify-center font-bold">
                <Mic className="w-5 h-5" />
              </div>
              {inputMode === 'VOICE' && <Check className="w-5 h-5 text-gov-saffron font-extrabold" />}
            </div>
            <div>
              <h3 className="font-extrabold text-slate-900 text-sm">🎙️ Speak</h3>
              <p className="text-xs text-slate-500 mt-0.5">Speak instead of typing</p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => setInputMode('FORM')}
            className={`p-5 rounded-2xl border text-left transition flex flex-col justify-between space-y-3 ${
              inputMode === 'FORM'
                ? 'bg-emerald-50 border-emerald-600 ring-2 ring-emerald-500 shadow-md'
                : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
                <ListFilter className="w-5 h-5" />
              </div>
              {inputMode === 'FORM' && <Check className="w-5 h-5 text-emerald-600 font-extrabold" />}
            </div>
            <div>
              <h3 className="font-extrabold text-slate-900 text-sm">📋 Select Details</h3>
              <p className="text-xs text-slate-500 mt-0.5">Choose options from a simple form</p>
            </div>
          </button>
        </div>
      </div>

      {/* INPUT INTERFACE 1 & 2: TYPE & VOICE */}
      {(inputMode === 'TYPE' || inputMode === 'VOICE') && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-md p-6 space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-sky-700" />
              <h3 className="text-base font-bold text-slate-900">
                {inputMode === 'VOICE' ? 'Voice Input' : 'Type Your Profile'}
              </h3>
            </div>
            <span className="text-xs bg-slate-100 text-slate-600 px-3 py-1 rounded-full font-medium">
              English • Hindi • Hinglish
            </span>
          </div>

          {inputMode === 'VOICE' && (
            <div className="bg-amber-50/80 p-5 rounded-2xl border border-amber-200 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="space-y-1 text-center sm:text-left">
                <h4 className="font-extrabold text-slate-900 text-sm flex items-center gap-1.5 justify-center sm:justify-start">
                  <Mic className="w-4 h-4 text-gov-saffron" /> Speak Instead
                </h4>
                <p className="text-xs text-slate-600">
                  Tell us about yourself in your own words. We'll fill in the details for you.
                </p>
              </div>

              <button
                type="button"
                onClick={toggleSpeechListening}
                className={`px-6 py-3.5 rounded-xl font-bold text-xs shadow-lg transition flex items-center gap-2.5 shrink-0 ${
                  isListening
                    ? 'bg-rose-600 text-white animate-pulse ring-4 ring-rose-200'
                    : 'bg-gov-saffron hover:bg-orange-600 text-white'
                }`}
              >
                {isListening ? (
                  <>
                    <MicOff className="w-4 h-4" /> Stop Listening...
                  </>
                ) : (
                  <>
                    <Mic className="w-4 h-4" /> Start Speaking
                  </>
                )}
              </button>
            </div>
          )}

          <form onSubmit={handleFindSchemes} className="space-y-4">
            <textarea
              value={userText}
              onChange={(e) => setUserText(e.target.value)}
              rows={4}
              placeholder="e.g. I am a 30 year old woman from Uttar Pradesh wanting to start a tailoring work with 1 lakh budget..."
              className="w-full rounded-xl border-slate-300 shadow-sm focus:border-sky-500 focus:ring-sky-500 text-sm p-4 border outline-none leading-relaxed"
            />

            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Checked against verified government criteria</span>
              </div>

              <button
                type="submit"
                disabled={isLoading || !userText.trim()}
                className="bg-gov-saffron hover:bg-orange-600 text-white font-bold text-xs px-6 py-3.5 rounded-xl shadow transition flex items-center gap-2 disabled:opacity-50"
              >
                {isLoading ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Send className="w-4 h-4" /> Find Schemes For Me
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* INPUT INTERFACE 3: CITIZEN QUICK FORM */}
      {inputMode === 'FORM' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-md p-6 sm:p-8 space-y-6">
          <div className="border-b border-slate-200 pb-4">
            <h3 className="text-lg font-extrabold text-slate-900">Prefer to select your details?</h3>
            <p className="text-xs text-slate-500 mt-1">Choose a few details and we'll find schemes that may suit you.</p>
          </div>

          <form onSubmit={handleFindSchemes} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 text-xs">
            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">Age (Years)</label>
              <input
                type="number"
                min={18}
                max={100}
                value={formAge}
                onChange={(e) => setFormAge(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none font-medium bg-white"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">Gender</label>
              <select
                value={formGender}
                onChange={(e) => setFormGender(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none font-medium bg-white"
              >
                <option value="FEMALE">Female</option>
                <option value="MALE">Male</option>
                <option value="TRANSGENDER">Transgender</option>
                <option value="OTHER">Other / Prefer not to say</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">State</label>
              <select
                value={formState}
                onChange={(e) => setFormState(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none font-medium bg-white"
              >
                <option value="ALL_INDIA">All India / Central Scheme</option>
                <option value="UTTAR_PRADESH">Uttar Pradesh</option>
                <option value="MAHARASHTRA">Maharashtra</option>
                <option value="BIHAR">Bihar</option>
                <option value="WEST_BENGAL">West Bengal</option>
                <option value="MADHYA_PRADESH">Madhya Pradesh</option>
                <option value="TAMIL_NADU">Tamil Nadu</option>
                <option value="RAJASTHAN">Rajasthan</option>
                <option value="KARNATAKA">Karnataka</option>
                <option value="GUJARAT">Gujarat</option>
                <option value="DELHI">Delhi</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">Social Category</label>
              <select
                value={formSocialCategory}
                onChange={(e) => setFormSocialCategory(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none font-medium bg-white"
              >
                <option value="GENERAL">General</option>
                <option value="OBC">OBC</option>
                <option value="SC">SC</option>
                <option value="ST">ST</option>
                <option value="OTHER">Other</option>
                <option value="NOT_SPECIFIED">Prefer not to say</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">Annual Family Income</label>
              <select
                value={formIncomeSlab}
                onChange={(e) => setFormIncomeSlab(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none font-medium bg-white"
              >
                <option value={90000}>Below ₹1 Lakh</option>
                <option value={150000}>₹1 Lakh – ₹2 Lakh</option>
                <option value={300000}>₹2 Lakh – ₹5 Lakh</option>
                <option value={750000}>₹5 Lakh – ₹10 Lakh</option>
                <option value={1200000}>Above ₹10 Lakh</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">What do you need help with?</label>
              <select
                value={formNeed}
                onChange={(e) => setFormNeed(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none font-medium bg-white"
              >
                <option value="START_BUSINESS">Start a business</option>
                <option value="EXPAND_BUSINESS">Expand my business</option>
                <option value="EDUCATION">Education</option>
                <option value="SKILL_TRAINING">Skill training</option>
                <option value="LOAN_FINANCIAL">Loan / financial support</option>
                <option value="HOUSING">Housing</option>
                <option value="AGRICULTURE">Agriculture / Farming</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">Business Stage</label>
              <select
                value={formBusinessStage}
                onChange={(e) => setFormBusinessStage(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none font-medium bg-white"
              >
                <option value="CONCEPT">Planning to start</option>
                <option value="NEW">New business</option>
                <option value="EXISTING">Existing business</option>
                <option value="EXPANDING">Expanding business</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">Approximate Project Cost</label>
              <select
                value={formProjectCostSlab}
                onChange={(e) => setFormProjectCostSlab(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none font-medium bg-white"
              >
                <option value={40000}>Below ₹50,000</option>
                <option value={80000}>₹50,000 – ₹1 Lakh</option>
                <option value={250000}>₹1 Lakh – ₹5 Lakh</option>
                <option value={750000}>₹5 Lakh – ₹10 Lakh</option>
                <option value={1500000}>Above ₹10 Lakh</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">Loan Required?</label>
              <select
                value={formLoanRequired ? 'YES' : 'NO'}
                onChange={(e) => setFormLoanRequired(e.target.value === 'YES')}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none font-medium bg-white"
              >
                <option value="YES">Yes</option>
                <option value="NO">No</option>
              </select>
            </div>

            <div className="sm:col-span-2 lg:col-span-3 pt-2">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3.5 px-6 rounded-xl text-xs shadow-lg transition flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isLoading ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Send className="w-4 h-4" /> Find Schemes For Me
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* RESULTS LIST SECTION */}
      {(aiResult || standardResult) && (
        <div className="space-y-6 pt-4">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
            <div>
              <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
                <Award className="w-6 h-6 text-gov-saffron" />
                Here are the schemes that may suit you
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {aiResult
                  ? `Evaluated ${aiResult.evaluated_scheme_count} verified schemes`
                  : `Evaluated ${standardResult?.recommendations.length || 0} schemes against your profile`}
              </p>
            </div>
          </div>

          <div className="space-y-6">
            {(aiResult?.recommendations || standardResult?.recommendations || []).map((rec: any, idx: number) => {
              const matchPct = Math.round(rec.score || 85);
              const matchLabel = getMatchLabel(matchPct);
              const isExpanded = !!expandedDetails[rec.scheme_id];
              const officialUrl = rec.application_url || rec.official_portal || rec.official_source_url;

              return (
                <div
                  key={rec.scheme_id || idx}
                  className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition space-y-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-xl bg-gov-blue text-white font-extrabold text-lg flex items-center justify-center shrink-0 shadow">
                        #{rec.rank || idx + 1}
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-slate-900 hover:text-sky-700 transition">
                          <Link to={`/schemes/${rec.scheme_id}`}>{rec.scheme_name}</Link>
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span
                            className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                              rec.eligibility_status === 'ELIGIBLE'
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-rose-100 text-rose-800'
                            }`}
                          >
                            {rec.eligibility_status === 'ELIGIBLE' ? 'You appear to meet criteria' : 'Check Requirements'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="text-right bg-amber-50 px-4 py-2 rounded-xl border border-amber-200">
                      <div className="text-2xl font-extrabold text-gov-saffron">
                        Match: {matchPct}%
                      </div>
                      <span className="text-[11px] text-amber-700 font-bold">{matchLabel}</span>
                    </div>
                  </div>

                  {/* Why this matches */}
                  <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 text-xs leading-relaxed space-y-2 text-slate-700">
                    <div className="font-bold text-slate-900 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Why this matches:
                    </div>
                    <p>{rec.ai_explanation || rec.explanation || "Your selected profile matches key scheme requirements."}</p>
                    {rec.financial_fit_summary && (
                      <p className="font-semibold text-slate-800 pt-1 border-t border-slate-200/80">
                        {rec.financial_fit_summary}
                      </p>
                    )}
                  </div>

                  {/* Expandable Transparency Section */}
                  <div>
                    <button
                      onClick={() => toggleDetails(rec.scheme_id)}
                      className="text-xs font-bold text-slate-600 hover:text-slate-900 flex items-center gap-1 focus:outline-none"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      Why this matches
                    </button>

                    {isExpanded && (
                      <div className="mt-3 p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-2">
                        <p className="font-bold text-slate-900">Matching Criteria:</p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-700">
                          <div className="flex items-center gap-1.5">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Business Sector & Activity matched</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Location & State guidelines verified</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Financial limits and loan criteria checked</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Target category requirements reviewed</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Four Primary Recommendation CTAs */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100">
                    <div className="flex flex-wrap items-center gap-2 text-xs font-bold">
                      <SaveSchemeButton schemeId={rec.scheme_id} size="sm" />
                      <Link
                        to={`/schemes/${rec.scheme_id}`}
                        className="bg-slate-100 hover:bg-slate-200 text-slate-800 px-3 py-2 rounded-xl transition flex items-center gap-1"
                      >
                        <FileText className="w-3.5 h-3.5 text-sky-700" /> View Scheme
                      </Link>
                      <Link
                        to={`/schemes/${rec.scheme_id}`}
                        className="bg-sky-50 hover:bg-sky-100 text-sky-800 px-3 py-2 rounded-xl transition flex items-center gap-1 border border-sky-200"
                      >
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Check Eligibility
                      </Link>
                      <Link
                        to={`/schemes/${rec.scheme_id}`}
                        className="bg-slate-50 hover:bg-slate-100 text-slate-700 px-3 py-2 rounded-xl transition flex items-center gap-1 border border-slate-200"
                      >
                        <FileText className="w-3.5 h-3.5 text-amber-600" /> Required Documents
                      </Link>
                    </div>

                    <button
                      onClick={() => openPortalModal(rec.scheme_name, officialUrl)}
                      className="bg-gov-saffron hover:bg-orange-600 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow transition flex items-center gap-1.5"
                    >
                      Apply on Official Portal <ExternalLink className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* External Portal Safety Dialog */}
      <OfficialPortalModal
        isOpen={!!selectedSchemeForModal}
        onClose={() => setSelectedSchemeForModal(null)}
        officialUrl={selectedSchemeForModal?.url}
        schemeName={selectedSchemeForModal?.name}
      />
    </div>
  );
};
