import React, { useState, useEffect, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGUAGES } from '../i18n';
import { useAuth } from '../context/AuthContext';
import { profileApi } from '../api/profileApi';
import { recommendationApi } from '../api/recommendationApi';
import { aiApi } from '../api/aiApi';
import {
  BeneficiaryProfileInput,
  CitizenProfileResponse,
  MissingFieldDetail,
  RecommendationResponse,
  RecommendationItem,
  AIExplainableRecommendationResponse,
  NaturalLanguageExtractResponse,
} from '../types';
import { Alert } from '../components/Alert';
import { OfficialPortalModal } from '../components/OfficialPortalModal';
import { SaveSchemeButton } from '../components/SaveSchemeButton';
import { CompareButton } from '../components/CompareButton';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Award,
  Send,
  PenTool,
  ClipboardList,
  Check,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  FileText,
  MapPin,
  HelpCircle,
  Calculator as CalcIcon,
  Sparkles,
  Info,
  User,
  Sliders,
  RefreshCw,
  ArrowRight,
  Mic,
  MicOff,
  Square
} from 'lucide-react';

type InputMode = 'PROFILE' | 'TYPE' | 'FORM';
type TabFilter = 'ELIGIBLE' | 'CONDITIONAL' | 'INSUFFICIENT' | 'INELIGIBLE' | 'ALL';

const formatFinancialCategory = (category?: string | null): string => {
  if (!category) return 'Financial Assistance';
  switch (category.toUpperCase()) {
    case 'LOAN_CREDIT':
      return 'Term Loan / Credit Facility';
    case 'GRANT_SUBSIDY':
      return 'Direct Subsidy / Grant';
    case 'SCHOLARSHIP':
      return 'Education Scholarship';
    case 'TRAINING_SKILL':
      return 'Skill Development & Stipend';
    case 'GUARANTEE_CREDIT_SUPPORT':
      return 'Credit Guarantee Coverage';
    case 'DIRECT_BENEFIT':
      return 'Direct Benefit Transfer';
    case 'NON_FINANCIAL':
      return 'Welfare & Advisory Support';
    default:
      return category.replace(/_/g, ' ');
  }
};

const cleanReasonText = (text?: string): string => {
  if (!text) return '';
  let clean = text;
  clean = clean.replace(/^(?:Rule\s+[A-Z0-9_-]+:?\s*)/i, '');
  clean = clean.replace(/^(?:Condition satisfied(?:\s+for)?:?\s*)/i, '');
  clean = clean.replace(/^(?:Condition failed(?:\s+for)?:?\s*)/i, '');
  clean = clean.replace(/^(?:Exact\s+(?:sector|category|income|state|age)\s+match(?:\s+for)?:?\s*)/i, '');
  clean = clean.replace(/^(?:Passed\s+(?:rule|criteria):?\s*)/i, '');
  clean = clean.replace(/^(?:Failed\s+(?:rule|criteria):?\s*)/i, '');
  clean = clean.replace(/^(?:Requirement\s+(?:Field|satisfied|failed):?\s*)/i, '');
  clean = clean.replace(/^(?:Missing\s+(?:parameter|requirement|field|information):?\s*)/i, '');
  clean = clean.replace(/Field:\s*[\w_]+\s*(?:==|!=|<=|>=|<|>|IN)\s*[^;]+;/gi, '');
  clean = clean.replace(/\b(?:PM_SURAJ|AUTHORISED_SCA|AUTHORISED_CA)\b/g, 'Authorized Partner Portal');
  clean = clean.replace(/\bTRADITIONAL_TRADE_\d+\b/g, 'Traditional Trade');
  clean = clean.replace(/\bSMALL_MICRO_BUSINESS\b/g, 'Small & Micro Business');
  clean = clean.replace(/\bAPPLICATION_ROUTE\b/g, 'Application Route');
  clean = clean.replace(/\s{2,}/g, ' ').trim();
  if (!clean) return '';
  return clean.charAt(0).toUpperCase() + clean.slice(1);
};

const calculateClientProfileCompletion = (profile: BeneficiaryProfileInput | null): number => {
  if (!profile) return 0;
  const coreFields = [
    'age',
    'gender',
    'state',
    'social_category',
    'annual_income',
    'applicant_type',
    'education_level',
    'sector',
    'business_stage',
    'project_cost',
  ];
  let count = 0;
  for (const f of coreFields) {
    const val = (profile as any)[f];
    if (val !== undefined && val !== null && val !== '' && val !== 'UNKNOWN' && val !== 'NOT_SPECIFIED') {
      count++;
    }
  }
  return Math.min(100, Math.round((count / coreFields.length) * 100));
};

export const Recommendations: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { user, isAuthenticated } = useAuth();
  const [searchParams] = useSearchParams();
  const urlQuery = searchParams.get('q');

  // Read restored history state if available (from Back/Forward navigation)
  const historyState = (typeof window !== 'undefined' && window.history.state?.yojnasetu_rec_state) || null;

  // Canonical Citizen Profile State
  const [canonicalProfile, setCanonicalProfile] = useState<BeneficiaryProfileInput | null>(null);
  const [profileCompletion, setProfileCompletion] = useState<number>(0);
  const [missingProfileFields, setMissingProfileFields] = useState<MissingFieldDetail[]>([]);

  // Mode Selection State
  const [inputMode, setInputMode] = useState<InputMode>(
    historyState?.inputMode || (urlQuery ? 'TYPE' : (isAuthenticated ? 'PROFILE' : 'TYPE'))
  );
  // Text Input State
  const DEFAULT_USER_TEXT =
    'I am a 28 year old woman from Uttar Pradesh. I belong to SC category. My annual income is around 1.8 lakh. I want to start a small tailoring business with a project cost of 1 lakh.';
  const [userText, setUserText] = useState<string>(historyState?.userText ?? (urlQuery || ''));

  // Speech Recognition State for Natural Language / Voice Input
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isSpeechSupported, setIsSpeechSupported] = useState<boolean>(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);

  // References to guarantee no stale closures and prevent duplication across renders
  const recognitionRef = useRef<any>(null);
  const baseTextRef = useRef<string>('');
  const finalTranscriptRef = useRef<string>('');
  const interimTranscriptRef = useRef<string>('');
  const lastProcessedIndexRef = useRef<number>(-1);
  const isStartingRef = useRef<boolean>(false);

  useEffect(() => {
    if (typeof window !== 'undefined' && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
      setIsSpeechSupported(true);
    }
  }, []);

  const cleanupRecognition = () => {
    isStartingRef.current = false;
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onstart = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.abort();
      } catch {
        // ignore
      }
      recognitionRef.current = null;
    }
  };

  // Clean up speech recognition on unmount
  useEffect(() => {
    return () => {
      cleanupRecognition();
    };
  }, []);

  // Stop listening if user switches input mode away from 'TYPE'
  useEffect(() => {
    if (inputMode !== 'TYPE') {
      stopListening();
    }
  }, [inputMode]);

  useEffect(() => {
  if (!isAuthenticated && inputMode === 'PROFILE') {
    setInputMode('TYPE');
  }
}, [isAuthenticated, inputMode]);

  const startListening = () => {
    setVoiceError(null);

    // Guard against rapid duplicate clicks or concurrent start requests
    if (isStartingRef.current || isListening) return;

    // Check offline status before starting
    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      setVoiceError(
        t('voice.offlineError', 'You appear to be offline. Voice recognition requires an active internet connection.')
      );
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceError(t('voice.unavailable', 'Voice recognition is not supported in this browser.'));
      return;
    }

    // Clean up any existing recognition instance to avoid duplicate listeners
    cleanupRecognition();

    try {
      isStartingRef.current = true;
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      // Match speech recognition to the current site language, fallback to en-IN for Indian context
      const activeLangObj = SUPPORTED_LANGUAGES.find((l) => l.code === i18n.language);
      recognition.lang = activeLangObj?.bcp47 || 'en-IN';

      // Capture base text from textarea; if default sample text, start clean
      const current = userText.trim();
      const isDefault = current === DEFAULT_USER_TEXT.trim();
      baseTextRef.current = isDefault ? '' : userText;
      finalTranscriptRef.current = '';
      interimTranscriptRef.current = '';
      lastProcessedIndexRef.current = -1;

      recognition.onstart = () => {
        isStartingRef.current = false;
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        let latestInterim = '';

        for (let i = 0; i < event.results.length; i++) {
          const res = event.results[i];
          if (!res || !res[0]) continue;
          const transcript = (res[0].transcript || '').trim();
          if (!transcript) continue;

          if (res.isFinal) {
            // Process finalized result ONCE per result index to prevent re-processing on Android Chrome
            if (i > lastProcessedIndexRef.current) {
              lastProcessedIndexRef.current = i;

              const prevFinal = finalTranscriptRef.current.trim();

              // Handle cumulative final engines (where subsequent final events include previous text)
              if (prevFinal && transcript.toLowerCase().startsWith(prevFinal.toLowerCase())) {
                finalTranscriptRef.current = transcript;
              } else if (!prevFinal.toLowerCase().endsWith(transcript.toLowerCase())) {
                // Incremental chunk: append once with a space
                finalTranscriptRef.current = prevFinal ? `${prevFinal} ${transcript}` : transcript;
              }

              // Finalized chunk supersedes previous interim text
              latestInterim = '';
              interimTranscriptRef.current = '';
            }
          } else {
            // Interim result: replace previous interim (NEVER append)
            latestInterim = transcript;
          }
        }

        interimTranscriptRef.current = latestInterim;

        const cleanFinal = finalTranscriptRef.current.trim();
        let cleanInterim = interimTranscriptRef.current.trim();

        // If interim text starts with what is already finalized, strip the duplicated prefix
        if (cleanFinal && cleanInterim.toLowerCase().startsWith(cleanFinal.toLowerCase())) {
          cleanInterim = cleanInterim.slice(cleanFinal.length).trim();
        }

        // Always construct textarea from: baseText + finalTranscript + currentInterimTranscript
        const sessionSpoken = [cleanFinal, cleanInterim].filter(Boolean).join(' ').trim();
        const base = baseTextRef.current.trim();

        const fullText = base ? (sessionSpoken ? `${base} ${sessionSpoken}` : base) : sessionSpoken;
        setUserText(fullText);
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error);
        isStartingRef.current = false;

        if (event.error === 'not-allowed') {
          setVoiceError(
            t(
              'voice.permissionDenied',
              'Microphone access was denied. Please allow microphone permissions in your browser settings to use voice input.'
            )
          );
        } else if (event.error === 'network') {
          if (typeof navigator !== 'undefined' && !navigator.onLine) {
            setVoiceError(
              t('voice.offlineError', 'You appear to be offline. Voice recognition requires an active internet connection.')
            );
          } else {
            setVoiceError(
              t(
                'voice.networkServiceError',
                'Speech service connection failed. Please check your internet connection or browser privacy/ad-block settings, or type your query directly.'
              )
            );
          }
        } else if (event.error === 'audio-capture') {
          setVoiceError(
            t('voice.noMicrophone', 'No microphone detected on your device. Please ensure a microphone is connected and enabled.')
          );
        } else if (event.error === 'service-not-allowed' || event.error === 'language-not-supported') {
          setVoiceError(
            t('voice.serviceUnavailable', 'Voice recognition service is unavailable in this browser. Please type your requirements.')
          );
        } else if (event.error !== 'no-speech') {
          setVoiceError(t('voice.recognitionError', `Speech recognition notice: ${event.error}`));
        }

        setIsListening(false);
      };

      recognition.onend = () => {
        isStartingRef.current = false;
        setIsListening(false);

        // When recognition stops: clear temporary interim state and keep only the final clean transcript
        interimTranscriptRef.current = '';
        const base = baseTextRef.current.trim();
        const finalSpoken = finalTranscriptRef.current.trim();
        const fullFinal = base ? (finalSpoken ? `${base} ${finalSpoken}` : base) : finalSpoken;
        if (fullFinal) {
          setUserText(fullFinal);
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err: any) {
      console.error('Failed to start speech recognition:', err);
      isStartingRef.current = false;
      setVoiceError(
        t('voice.startFailed', 'Voice input could not be started. Please type your requirements directly.')
      );
      setIsListening(false);
    }
  };

  const stopListening = () => {
    isStartingRef.current = false;
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
    }
    setIsListening(false);
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  // Quick Form State (Restored from history navigation if available)
  const [formAge, setFormAge] = useState<number>(historyState?.formAge ?? 28);
  const [formGender, setFormGender] = useState<string>(historyState?.formGender ?? 'FEMALE');
  const [formState, setFormState] = useState<string>(historyState?.formState ?? 'UTTAR_PRADESH');
  const [formSocialCategory, setFormSocialCategory] = useState<string>(historyState?.formSocialCategory ?? 'SC');
  const [formIncomeSlab, setFormIncomeSlab] = useState<number>(historyState?.formIncomeSlab ?? 180000);
  const [formNeed, setFormNeed] = useState<string>(historyState?.formNeed ?? 'START_BUSINESS');
  const [formBusinessStage, setFormBusinessStage] = useState<string>(historyState?.formBusinessStage ?? 'NEW');
  const [formProjectCostSlab, setFormProjectCostSlab] = useState<number>(historyState?.formProjectCostSlab ?? 100000);
  const [formLoanRequired, setFormLoanRequired] = useState<boolean>(historyState?.formLoanRequired ?? true);

  // Recommendation Results State (Restored from history navigation if available)
  const [topK] = useState(10);
  const [activeTab, setActiveTab] = useState<TabFilter>(historyState?.activeTab ?? 'ELIGIBLE');
  const [aiResult, setAiResult] = useState<AIExplainableRecommendationResponse | null>(historyState?.aiResult ?? null);
  const [standardResult, setStandardResult] = useState<RecommendationResponse | null>(historyState?.standardResult ?? null);
  const [extractionResult, setExtractionResult] = useState<NaturalLanguageExtractResponse | null>(historyState?.extractionResult ?? null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Modal State for Official Portal Redirection
  const [selectedSchemeForModal, setSelectedSchemeForModal] = useState<{ name: string; url?: string | null } | null>(null);

  // Track expanded transparency details per scheme (Restored from history navigation if available)
  const [expandedDetails, setExpandedDetails] = useState<Record<string, boolean>>(historyState?.expandedDetails ?? {});

  // Track latest form/input state for saving on unmount
  const stateRef = useRef({
    inputMode,
    userText,
    formAge,
    formGender,
    formState,
    formSocialCategory,
    formIncomeSlab,
    formNeed,
    formBusinessStage,
    formProjectCostSlab,
    formLoanRequired,
    activeTab,
    standardResult,
    aiResult,
    extractionResult,
    expandedDetails,
  });

  useEffect(() => {
    stateRef.current = {
      inputMode,
      userText,
      formAge,
      formGender,
      formState,
      formSocialCategory,
      formIncomeSlab,
      formNeed,
      formBusinessStage,
      formProjectCostSlab,
      formLoanRequired,
      activeTab,
      standardResult,
      aiResult,
      extractionResult,
      expandedDetails,
    };
  }, [
    inputMode,
    userText,
    formAge,
    formGender,
    formState,
    formSocialCategory,
    formIncomeSlab,
    formNeed,
    formBusinessStage,
    formProjectCostSlab,
    formLoanRequired,
    activeTab,
    standardResult,
    aiResult,
    extractionResult,
    expandedDetails,
  ]);

  // Persist transient recommendation UI/results state into browser history state
  const persistRecommendationState = (overrides?: Record<string, any>) => {
    if (typeof window === 'undefined') return;
    const currentSaved = window.history.state?.yojnasetu_rec_state || {};
    const updated = {
      ...currentSaved,
      inputMode,
      userText,
      formAge,
      formGender,
      formState,
      formSocialCategory,
      formIncomeSlab,
      formNeed,
      formBusinessStage,
      formProjectCostSlab,
      formLoanRequired,
      activeTab,
      standardResult,
      aiResult,
      extractionResult,
      expandedDetails,
      ...overrides,
    };
    window.history.replaceState({ ...window.history.state, yojnasetu_rec_state: updated }, '');
  };

  // Save current input/form/result state to history state on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined') {
        const currentSaved = window.history.state?.yojnasetu_rec_state || {};
        window.history.replaceState(
          {
            ...window.history.state,
            yojnasetu_rec_state: {
              ...currentSaved,
              ...stateRef.current,
            },
          },
          ''
        );
      }
    };
  }, []);

  // Refs for dynamic auto-scrolling to results
  const resultsRef = useRef<HTMLDivElement>(null);
  const searchTriggeredRef = useRef<boolean>(false);

  // When search or evaluation results arrive after an explicit user action, scroll smoothly to the results section
  useEffect(() => {
    if (searchTriggeredRef.current && standardResult && resultsRef.current) {
      searchTriggeredRef.current = false;
      requestAnimationFrame(() => {
        if (!resultsRef.current) return;
        const navOffset = 85;
        const elementPosition = resultsRef.current.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - navOffset;

        window.scrollTo({
          top: Math.max(0, offsetPosition),
          behavior: 'smooth'
        });
      });
    }
  }, [standardResult]);

  // On mount: distinguish between History Restoration, Explicit URL Query, and Clean Fresh Navigation
  useEffect(() => {
    if (historyState?.standardResult) {
      // 1. History restoration: State already hydrated from window.history.state
      // Load user profile silently for metadata chips, NEVER re-trigger evaluation API
      loadProfileMetadata(false);
    } else if (urlQuery && urlQuery.trim()) {
      // 2. Explicit query parameter in URL (e.g. from search navigation)
      evaluateNaturalLanguage(urlQuery.trim());
      loadProfileMetadata(false);
    } else {
      // 3. Fresh navigation (e.g. from Home CTA or Navbar):
      // Load user profile for prefilling form fields if available, but NEVER auto-evaluate
      loadProfileMetadata(false);
    }
  }, [urlQuery, isAuthenticated]);

  const evaluateNaturalLanguage = async (text: string) => {
    searchTriggeredRef.current = true;
    setIsLoading(true);
    setErrorMsg(null);
    setAiResult(null);
    setStandardResult(null);

    try {
      const ext = await aiApi.extractProfile(text);
      setExtractionResult(ext);

      const formProfile = ext.extracted_profile;
      const res = await recommendationApi.getRecommendations(formProfile, topK);
      setStandardResult(res);

      let aiRes: AIExplainableRecommendationResponse | null = null;
      try {
        aiRes = await aiApi.getAIRecommendations({
          user_text: text,
          profile: ext.extracted_profile,
          top_k: topK,
        });
        setAiResult(aiRes);
      } catch (aiErr) {
        console.warn('AI explainability optional layer warning:', aiErr);
      }

      // Persist results to browser history state so Back navigation retains evaluation
      persistRecommendationState({
        userText: text,
        standardResult: res,
        aiResult: aiRes,
        extractionResult: ext,
      });
    } catch (err: any) {
      setErrorMsg(t('recommendations.evalError', 'Could not find recommendations: ') + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const loadProfileMetadata = async (autoEvaluate = false) => {
    try {
      let activeProf: BeneficiaryProfileInput | null = null;

      if (isAuthenticated) {
        const pRes = await profileApi.getProfile();
        setCanonicalProfile(pRes.profile);
        const compPct = pRes.completion_percentage !== undefined && pRes.completion_percentage !== null
          ? pRes.completion_percentage
          : calculateClientProfileCompletion(pRes.profile);
        setProfileCompletion(compPct);
        setMissingProfileFields(pRes.missing_fields || []);
        activeProf = pRes.profile;
      } else {
        const cached = localStorage.getItem('yojnasetu_citizen_profile');
        if (cached) {
          try {
            const parsed = JSON.parse(cached);
            setCanonicalProfile(parsed);
            setProfileCompletion(calculateClientProfileCompletion(parsed));
            activeProf = parsed;
          } catch (e) {
            console.warn('Failed parsing cached profile', e);
          }
        }
      }

      if (activeProf && (activeProf.age || activeProf.annual_income || activeProf.social_category)) {
        // Populate quick form state only if not already restored from history
        if (!historyState?.formAge && activeProf.age) setFormAge(activeProf.age);
        if (!historyState?.formGender && activeProf.gender) setFormGender(activeProf.gender);
        if (!historyState?.formState && activeProf.state) setFormState(activeProf.state);
        if (!historyState?.formSocialCategory && activeProf.social_category) setFormSocialCategory(activeProf.social_category);
        if (!historyState?.formIncomeSlab && activeProf.annual_income) setFormIncomeSlab(activeProf.annual_income);
        if (!historyState?.formProjectCostSlab && activeProf.project_cost) setFormProjectCostSlab(activeProf.project_cost);

        // Only evaluate if explicitly requested (e.g. by direct button click)
        if (autoEvaluate) {
          const res = await recommendationApi.getRecommendations(activeProf, topK);
          setStandardResult(res);
          persistRecommendationState({ standardResult: res });
        }
      }
    } catch (err: any) {
      console.warn('Profile metadata fetch notice:', err);
    }
  };

  const handleResetToStoredProfile = () => {
    if (!canonicalProfile) return;
    if (canonicalProfile.age) setFormAge(canonicalProfile.age);
    if (canonicalProfile.gender) setFormGender(canonicalProfile.gender);
    if (canonicalProfile.state) setFormState(canonicalProfile.state);
    if (canonicalProfile.social_category) setFormSocialCategory(canonicalProfile.social_category);
    if (canonicalProfile.annual_income) setFormIncomeSlab(canonicalProfile.annual_income);
    if (canonicalProfile.project_cost) setFormProjectCostSlab(canonicalProfile.project_cost);
    setSaveSuccessMsg(t('recommendations.resetSuccess', 'Form reset to your saved citizen profile values.'));
    setTimeout(() => setSaveSuccessMsg(null), 4000);
  };

  const handleSaveFormToProfile = async () => {
    setIsSavingProfile(true);
    setSaveSuccessMsg(null);
    setErrorMsg(null);
    try {
      const formProfile = buildProfileFromForm();
      if (isAuthenticated) {
        const res = await profileApi.updateProfile(formProfile);
        setCanonicalProfile(res.profile);
        const compPct = res.completion_percentage !== undefined && res.completion_percentage !== null
          ? res.completion_percentage
          : calculateClientProfileCompletion(res.profile);
        setProfileCompletion(compPct);
        setMissingProfileFields(res.missing_fields || []);
      } else {
        localStorage.setItem('yojnasetu_citizen_profile', JSON.stringify(formProfile));
        setCanonicalProfile(formProfile);
        setProfileCompletion(calculateClientProfileCompletion(formProfile));
      }
      setSaveSuccessMsg(t('recommendations.profileUpdatedSuccess', 'Your Citizen Profile has been updated with these parameters!'));
      setTimeout(() => setSaveSuccessMsg(null), 5000);
    } catch (err: any) {
      setErrorMsg(t('recommendations.saveProfileError', 'Failed to update profile: ') + (err.response?.data?.detail || err.message));
    } finally {
      setIsSavingProfile(false);
    }
  };

  const toggleDetails = (schemeId: string) => {
    setExpandedDetails(prev => {
      const updated = { ...prev, [schemeId]: !prev[schemeId] };
      persistRecommendationState({ expandedDetails: updated });
      return updated;
    });
  };

  const handleTabChange = (tab: TabFilter) => {
    setActiveTab(tab);
    persistRecommendationState({ activeTab: tab });
  };

  const handleInputModeChange = (mode: InputMode) => {
    setInputMode(mode);
    persistRecommendationState({ inputMode: mode });
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

  const handleFindSchemes = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    searchTriggeredRef.current = true;
    setIsLoading(true);
    setErrorMsg(null);
    setAiResult(null);
    setStandardResult(null);

    try {
      if (inputMode === 'PROFILE' && canonicalProfile) {
        setExtractionResult(null);
        const res = await recommendationApi.getRecommendations(canonicalProfile, topK);
        setStandardResult(res);
        let aiRes: AIExplainableRecommendationResponse | null = null;
        try {
          aiRes = await aiApi.getAIRecommendations({
            profile: canonicalProfile,
            top_k: topK,
          });
          setAiResult(aiRes);
        } catch (aiErr) {
          console.warn('AI explainability optional layer warning:', aiErr);
        }
        persistRecommendationState({
          inputMode: 'PROFILE',
          standardResult: res,
          aiResult: aiRes,
          extractionResult: null,
        });
      } else if (inputMode === 'FORM') {
        setExtractionResult(null);
        const formProfile = buildProfileFromForm();
        const res = await recommendationApi.getRecommendations(formProfile, topK);
        setStandardResult(res);
        let aiRes: AIExplainableRecommendationResponse | null = null;
        try {
          aiRes = await aiApi.getAIRecommendations({
            profile: formProfile,
            top_k: topK,
          });
          setAiResult(aiRes);
        } catch (aiErr) {
          console.warn('AI explainability optional layer warning:', aiErr);
        }
        persistRecommendationState({
          inputMode: 'FORM',
          standardResult: res,
          aiResult: aiRes,
          extractionResult: null,
        });
      } else {
        await evaluateNaturalLanguage(userText);
      }
    } catch (err: any) {
      setErrorMsg(t('recommendations.evalError', 'Could not find recommendations: ') + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const openPortalModal = (schemeName: string, officialUrl?: string | null) => {
    setSelectedSchemeForModal({ name: schemeName, url: officialUrl });
  };

  const getMatchLabel = (score: number) => {
    if (score >= 85) return t('recommendations.strongFit', 'Strong Fit');
    if (score >= 70) return t('recommendations.goodFit', 'Good Fit');
    if (score >= 50) return t('recommendations.moderateFit', 'Moderate Fit');
    return t('recommendations.basicFit', 'Basic Fit');
  };

  // Compile active list of items based on selected tab
  const getDisplayedItems = (): { items: RecommendationItem[]; emptyMessage: string } => {
    if (!standardResult) return { items: [], emptyMessage: t('recommendations.noEvalYet', 'No schemes evaluated yet.') };

    const eligible = standardResult.recommendations || [];
    const conditional = standardResult.conditional_schemes || [];
    const insufficient = standardResult.insufficient_info_schemes || [];
    const ineligible = standardResult.ineligible_schemes || [];

    if (activeTab === 'ELIGIBLE') {
      return {
        items: eligible,
        emptyMessage: t('recommendations.noEligible', 'No schemes passed all mandatory statutory criteria for the provided profile.')
      };
    } else if (activeTab === 'CONDITIONAL') {
      return {
        items: conditional,
        emptyMessage: t('recommendations.noConditional', 'No schemes with conditional statutory requirements found.')
      };
    } else if (activeTab === 'INSUFFICIENT') {
      return {
        items: insufficient,
        emptyMessage: t('recommendations.noInsufficient', 'No schemes are pending missing profile information.')
      };
    } else if (activeTab === 'INELIGIBLE') {
      return {
        items: ineligible,
        emptyMessage: t('recommendations.noIneligible', 'No schemes were excluded by hard eligibility gates.')
      };
    } else {
      return {
        items: [...eligible, ...conditional, ...insufficient, ...ineligible],
        emptyMessage: t('recommendations.noSchemesFound', 'No evaluated schemes found.')
      };
    }
  };

  const { items: displayedItems, emptyMessage } = getDisplayedItems();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-24 sm:pb-16 space-y-8">
      {/* ── Page Header (Matches Warm CIVIC-TECH Theme) ── */}
      <div className="bg-gradient-to-r from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white rounded-3xl p-6 sm:p-8 shadow-warm-md border border-[#E8D8D2]/20 relative overflow-hidden flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="relative z-10 max-w-3xl space-y-2.5">
          <div className="inline-flex items-center gap-2 bg-[#F7AE56]/20 border border-[#F7AE56]/40 text-[#F7AE56] px-3 py-1 rounded-full text-xs font-bold tracking-wide">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI-POWERED SCHEME DISCOVERY</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-black tracking-tight text-white">
            Find Schemes That Fit Your Situation
          </h1>
          <p className="text-xs sm:text-sm text-[#FFD0CA]/90 leading-relaxed max-w-xl">
            Tell us about yourself in simple language. We'll evaluate your profile against official published guidelines to find the most relevant schemes for you.
          </p>
        </div>
      </div>

      {errorMsg && <Alert type="error">{errorMsg}</Alert>}
      {saveSuccessMsg && <Alert type="success">{saveSuccessMsg}</Alert>}

      {/* ── Missing Profile Fields Guidance Banner (Warm Alert) ── */}
      {missingProfileFields.length > 0 && (
        <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-2xl p-5 shadow-warm-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-[#F7AE56] shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-[#3B2522]">
                {t('recommendations.incompleteBannerTitle', 'Complete your profile to get more accurate scheme recommendations.')}
              </h3>
              <p className="text-xs text-[#765E59] mt-0.5">
                {t('recommendations.incompleteBannerSub', 'The following parameters are currently missing from your Citizen Profile:')}
              </p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {missingProfileFields.map((mf) => (
                  <span
                    key={mf.field}
                    className="inline-flex items-center text-xs font-semibold bg-white text-[#3B2522] border border-[#E8D8D2] px-2.5 py-1 rounded-lg"
                  >
                    • {mf.label}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <Link
            to="/profile"
            className="btn-secondary btn-sm shrink-0 bg-[#EA717B] hover:bg-[#d65f69] text-white border-transparent shadow-warm-xs flex items-center gap-1.5"
          >
            <User className="w-4 h-4" />
            <span>{t('recommendations.completeProfileBtn', 'Complete Profile →')}</span>
          </Link>
        </div>
      )}

      {/* ── Unified Profile Management Zone (Warm Theme) ── */}
      {canonicalProfile && (
        <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-[#FFD0CA] text-[#4A2525] flex items-center justify-center font-bold shrink-0 mt-0.5">
              <User className="w-5 h-5" />
            </div>
            <div className="min-w-0 space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-bold text-[#3B2522]">
                  {t('recommendations.activeProfileTitle', 'Prefilled from your Citizen Profile')}:
                </span>
                <span
                  className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${
                    profileCompletion >= 100
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : profileCompletion >= 50
                      ? 'bg-[#F7AE56]/20 text-[#3B2522] border-[#F7AE56]/40'
                      : 'bg-[#FFF4EC] text-[#765E59] border-[#E8D8D2]'
                  }`}
                >
                  {profileCompletion >= 100
                    ? t('recommendations.profile100Complete', '100% Profile Complete')
                    : `${profileCompletion}% ${t('recommendations.profileComplete', 'Profile Complete')}`}
                </span>
              </div>

              {/* Readable Demographic Chips */}
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                {[
                  canonicalProfile.gender || 'Any Gender',
                  canonicalProfile.age ? `Age ${canonicalProfile.age}` : null,
                  canonicalProfile.social_category ? `Category ${canonicalProfile.social_category}` : null,
                  canonicalProfile.annual_income ? `Income ₹${canonicalProfile.annual_income.toLocaleString('en-IN')}` : null,
                  canonicalProfile.state ? canonicalProfile.state.replace(/_/g, ' ') : null,
                  canonicalProfile.sector ? `Sector ${canonicalProfile.sector}` : null,
                ].filter(Boolean).map((chip, cIdx) => (
                  <span
                    key={cIdx}
                    className="inline-flex items-center text-xs font-medium bg-[#FFFBF0] text-[#765E59] border border-[#E8D8D2] px-2.5 py-0.5 rounded-lg"
                  >
                    {chip}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Grouped Profile Actions */}
          <div className="flex flex-wrap sm:flex-nowrap items-center gap-2.5 w-full md:w-auto shrink-0 pt-2 md:pt-0">
            <button
              onClick={() => handleFindSchemes()}
              disabled={isLoading}
              className="btn-secondary btn-sm min-h-[40px] flex items-center justify-center gap-1.5 w-full sm:w-auto bg-[#FFD0CA] hover:bg-[#fca59d] text-[#4A2525] border-transparent"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>{t('recommendations.recalcBtn', 'Re-evaluate Schemes')}</span>
            </button>
            <Link
              to="/profile"
              className="btn-secondary btn-sm min-h-[40px] flex items-center justify-center gap-1.5 w-full sm:w-auto text-[#765E59] hover:text-[#EA717B] border-[#E8D8D2]"
            >
              <User className="w-3.5 h-3.5 text-[#765E59]" />
              <span>{t('recommendations.updateProfileLink', 'Update Profile')}</span>
            </Link>
          </div>
        </div>
      )}

      {/* ── 3-Way Input Choice Tab (Warm Theme) ── */}
      <div className="space-y-4">
        <h2 className="text-sm font-extrabold text-[#3B2522]">
          {t('recommendations.chooseInputMethod', 'Evaluation Mode / Profile Input Source')}
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <button
            type="button"
            disabled={!isAuthenticated}
            onClick={() => {
              if (isAuthenticated) {
                handleInputModeChange('PROFILE');
              }
            }}
            className={`p-4 rounded-2xl border text-left transition flex flex-col justify-between space-y-2 ${
              !isAuthenticated
                ? 'bg-[#FFFBF0]/60 border-[#E8D8D2] opacity-70 cursor-not-allowed'
                : inputMode === 'PROFILE'
                ? 'bg-[#FFF4EC] border-[#EA717B] ring-2 ring-[#EA717B]/20 shadow-warm-sm'
                : 'bg-white border-[#E8D8D2] hover:border-[#F7AE56]/60 shadow-warm-xs'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded-lg bg-[#FFD0CA] text-[#4A2525] flex items-center justify-center font-bold">
                <User className="w-4 h-4" />
              </div>

              {isAuthenticated && inputMode === 'PROFILE' && (
                <Check className="w-4 h-4 text-[#EA717B] font-extrabold" />
              )}
            </div>

            <div>
              <h3 className="font-extrabold text-[#3B2522] text-xs">
                {t('recommendations.modeProfile', '👤 Saved Citizen Profile')}
              </h3>

              {isAuthenticated ? (
                <p className="text-[11px] text-[#765E59] mt-0.5">
                  {t(
                    'recommendations.modeProfileDesc',
                    'Uses your authoritative saved profile parameters.'
                  )}
                </p>
              ) : (
                <p className="text-[11px] text-[#EA717B] font-bold mt-0.5">
                  🔒 {t(
                    'recommendations.signInFirst',
                    'Sign in first to use this feature'
                  )}
                </p>
              )}
            </div>
          </button>

          <button
            type="button"
            onClick={() => handleInputModeChange('TYPE')}
            className={`p-4 rounded-2xl border text-left transition flex flex-col justify-between space-y-2 ${
              inputMode === 'TYPE'
                ? 'bg-[#FFF4EC] border-[#EA717B] ring-2 ring-[#EA717B]/20 shadow-warm-sm'
                : 'bg-white border-[#E8D8D2] hover:border-[#F7AE56]/60 shadow-warm-xs'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded-lg bg-[#FFD0CA] text-[#4A2525] flex items-center justify-center font-bold">
                <PenTool className="w-4 h-4" />
              </div>
              {inputMode === 'TYPE' && <Check className="w-4 h-4 text-[#EA717B] font-extrabold" />}
            </div>
            <div>
              <h3 className="font-extrabold text-[#3B2522] text-xs">{t('recommendations.modeNatural', '✍️ Natural Language / Voice')}</h3>
              <p className="text-[11px] text-[#765E59] mt-0.5">{t('recommendations.modeNaturalDesc', 'Describe your situation in everyday sentences or Hindi.')}</p>
            </div>
          </button>

          <button
            type="button"
            onClick={() => handleInputModeChange('FORM')}
            className={`p-4 rounded-2xl border text-left transition flex flex-col justify-between space-y-2 ${
              inputMode === 'FORM'
                ? 'bg-[#FFF4EC] border-[#EA717B] ring-2 ring-[#EA717B]/20 shadow-warm-sm'
                : 'bg-white border-[#E8D8D2] hover:border-[#F7AE56]/60 shadow-warm-xs'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="w-8 h-8 rounded-lg bg-[#FFD0CA] text-[#4A2525] flex items-center justify-center font-bold">
                <ClipboardList className="w-4 h-4" />
              </div>
              {inputMode === 'FORM' && <Check className="w-4 h-4 text-[#EA717B] font-extrabold" />}
            </div>
            <div>
              <h3 className="font-extrabold text-[#3B2522] text-xs">{t('recommendations.modeQuickForm', '📋 Quick Override Form')}</h3>
              <p className="text-xs text-[#765E59] mt-0.5">{t('recommendations.modeQuickFormDesc', 'Temporarily simulate another age, category, or loan amount.')}</p>
            </div>
          </button>
        </div>
      </div>

      {/* INPUT INTERFACE 1: TEXT INPUT (Warm Theme) */}
      {inputMode === 'TYPE' && (
        <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs p-6 sm:p-8 space-y-6">
          <div className="flex items-center gap-2 pb-2 border-b border-[#E8D8D2]/60">
            <PenTool className="w-5 h-5 text-[#EA717B]" />
            <h2 className="text-base sm:text-lg font-bold text-[#3B2522]">
              {t('recommendations.nlSearchTitle', 'Natural Language Search')}
            </h2>
          </div>

          <form onSubmit={handleFindSchemes} className="space-y-4">
            <div>
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                <label htmlFor="user-text-input" className="block text-sm font-semibold text-[#3B2522]">
                  {t('recommendations.describeLabel', 'Describe yourself, your work, family income, caste category, and goals in plain language.')}
                </label>
                <button
                  type="button"
                  onClick={() => setUserText(DEFAULT_USER_TEXT)}
                  className="text-xs text-[#EA717B] hover:text-[#d65f69] font-semibold underline decoration-dotted transition flex items-center gap-1"
                  title="Insert sample profile text to test evaluation"
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#F7AE56]" />
                  <span>{t('recommendations.insertSample', 'Insert Sample Profile')}</span>
                </button>
              </div>

              <textarea
                id="user-text-input"
                value={userText}
                onChange={(e) => setUserText(e.target.value)}
                rows={4}
                placeholder={t('recommendations.typePlaceholder', 'e.g. I am a 28 year old woman from Uttar Pradesh belonging to SC category. My annual family income is ₹1.8 lakh. I want to start a small tailoring unit with a project cost of ₹1 lakh...')}
                className={`w-full rounded-xl border text-sm p-4 border-[#E8D8D2] bg-[#FFFBF0]/40 text-[#3B2522] placeholder:text-[#9B817A] shadow-warm-xs focus:border-[#EA717B] focus:ring-2 focus:ring-[#EA717B]/20 outline-none leading-relaxed transition ${
                  isListening ? 'border-[#EA717B] ring-2 ring-[#EA717B]/30 bg-[#FFF4EC]' : ''
                }`}
              />
            </div>

            {/* Clear Listening Status Banner */}
            {isListening && (
              <div className="bg-[#FFF4EC] border border-[#EA717B]/40 rounded-xl p-3 flex items-center justify-between gap-3 text-xs text-[#4A2525] animate-in fade-in duration-200">
                <div className="flex items-center gap-2.5">
                  <span className="relative flex h-3 w-3 shrink-0">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#EA717B] opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-[#EA717B]"></span>
                  </span>
                  <div>
                    <span className="font-bold">
                      {t('voice.listeningTitle', 'Listening... Speak now')}
                    </span>
                    <p className="text-xs text-[#765E59] mt-0.5">
                      {t('voice.listeningDesc', 'Speak naturally to describe your background, occupation, and financial requirements.')}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={stopListening}
                  className="px-3 py-1 bg-[#EA717B] hover:bg-[#d65f69] text-white rounded-lg text-xs font-bold transition flex items-center gap-1 shrink-0 shadow-warm-xs"
                >
                  <Square className="w-3 h-3 fill-current" />
                  <span>{t('common.stop', 'Stop')}</span>
                </button>
              </div>
            )}

            {/* Graceful Microphone Error Banner */}
            {voiceError && (
              <div className="text-xs text-[#EA717B] bg-[#FFF4EC] border border-[#EA717B]/30 rounded-xl p-3 flex items-center justify-between gap-2">
                <span>{voiceError}</span>
                <button
                  type="button"
                  onClick={() => setVoiceError(null)}
                  className="text-[#765E59] hover:text-[#3B2522] font-bold px-1"
                >
                  ✕
                </button>
              </div>
            )}

            {/* Dedicated Action Toolbar */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
              <div className="flex flex-wrap items-center gap-3">
                {isSpeechSupported ? (
                  <button
                    type="button"
                    onClick={toggleListening}
                    className={`btn-secondary btn-sm min-h-[40px] flex items-center gap-2 bg-[#FFF4EC] text-[#4A2525] border-[#E8D8D2] hover:border-[#EA717B] ${
                      isListening
                        ? '!bg-[#EA717B] !hover:bg-[#d65f69] !text-white animate-pulse !border-[#EA717B] ring-2 ring-[#EA717B]/30'
                        : ''
                    }`}
                    title={
                      isListening
                        ? t('voice.clickToStop', 'Listening... Click to stop')
                        : t('voice.clickToStart', 'Click to speak')
                    }
                    aria-label={isListening ? 'Stop voice recognition' : 'Start voice recognition'}
                  >
                    {isListening ? (
                      <>
                        <MicOff className="w-4 h-4 text-white" />
                        <span>{t('voice.listeningBtn', 'Listening...')}</span>
                      </>
                    ) : (
                      <>
                        <Mic className="w-4 h-4 text-[#EA717B]" />
                        <span>{t('voice.voiceBtn', 'Voice Input')}</span>
                      </>
                    )}
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled
                    className="btn-ghost btn-sm min-h-[40px] opacity-60 cursor-not-allowed flex items-center gap-2"
                    title={t('voice.unavailable', 'Voice input is not supported in this browser')}
                    aria-label="Voice input unsupported"
                  >
                    <MicOff className="w-4 h-4" />
                    <span>{t('voice.unavailableShort', 'Voice N/A')}</span>
                  </button>
                )}

                <div className="flex items-center gap-1.5 text-xs text-[#765E59]">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>{t('recommendations.noStorageGuarantee', 'Natural language is parsed on-the-fly and never retained.')}</span>
                </div>
              </div>

              {/* Primary Evaluate Matching Schemes CTA */}
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary min-h-[44px] px-6 text-sm font-bold flex items-center justify-center gap-2 shadow-warm-xs bg-[#EA717B] hover:bg-[#d65f69] text-white"
              >
                {isLoading ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>{t('recommendations.evaluateBtn', 'Evaluate Matching Schemes')}</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* INPUT INTERFACE 2: QUICK FORM (Warm Theme) */}
      {inputMode === 'FORM' && (
        <div className="bg-white rounded-2xl border border-[#E8D8D2] shadow-warm-xs p-6 sm:p-8 space-y-6">
          {/* Temporary Simulation Indicator & Profile Sync Options */}
          <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-[#4A2525]">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-[#F7AE56] shrink-0" />
              <span>
                {t('recommendations.simulatingNotice', 'Temporary simulation: Modifying these fields evaluates schemes without overwriting your saved profile.')}
              </span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={handleResetToStoredProfile}
                className="btn-secondary btn-sm min-h-[36px] bg-white text-[#765E59] border-[#E8D8D2] flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3 text-[#765E59]" />
                <span>{t('recommendations.resetToStored', 'Reset to Stored')}</span>
              </button>
              <button
                type="button"
                onClick={handleSaveFormToProfile}
                disabled={isSavingProfile}
                className="btn-secondary btn-sm min-h-[36px] bg-[#FFD0CA] hover:bg-[#fca59d] text-[#4A2525] border-transparent flex items-center gap-1 disabled:opacity-50"
              >
                {isSavingProfile ? (
                  <span className="w-3 h-3 border-2 border-[#4A2525] border-t-transparent rounded-full animate-spin" />
                ) : (
                  <User className="w-3 h-3 text-[#EA717B]" />
                )}
                <span>{t('recommendations.updateMyProfileBtn', 'Update My Profile')}</span>
              </button>
            </div>
          </div>

          <form onSubmit={handleFindSchemes} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 text-xs">
            <div>
              <label className="block font-semibold text-[#3B2522] mb-1.5">{t('profile.age', 'Applicant Age')}</label>
              <input
                type="number"
                min={14}
                max={120}
                value={formAge}
                onChange={(e) => setFormAge(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl border border-[#E8D8D2] text-xs focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] outline-none font-medium text-[#3B2522] bg-white"
                required
              />
            </div>

            <div>
              <label className="block font-semibold text-[#3B2522] mb-1.5">{t('profile.gender', 'Gender')}</label>
              <select
                value={formGender}
                onChange={(e) => setFormGender(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-[#E8D8D2] text-xs focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] outline-none font-medium text-[#3B2522] bg-white"
              >
                <option value="FEMALE">{t('gender.female', 'Female')}</option>
                <option value="MALE">{t('gender.male', 'Male')}</option>
                <option value="TRANSGENDER">{t('gender.transgender', 'Transgender')}</option>
                <option value="OTHER">{t('gender.other', 'Other')}</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-[#3B2522] mb-1.5">{t('profile.state', 'State')}</label>
              <select
                value={formState}
                onChange={(e) => setFormState(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-[#E8D8D2] text-xs focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] outline-none font-medium text-[#3B2522] bg-white"
              >
                <option value="ALL_INDIA">{t('states.allIndia', 'All India / Central Scheme')}</option>
                <option value="UTTAR_PRADESH">{t('states.uttarPradesh', 'Uttar Pradesh')}</option>
                <option value="MAHARASHTRA">{t('states.maharashtra', 'Maharashtra')}</option>
                <option value="BIHAR">{t('states.bihar', 'Bihar')}</option>
                <option value="WEST_BENGAL">{t('states.westBengal', 'West Bengal')}</option>
                <option value="MADHYA_PRADESH">{t('states.madhyaPradesh', 'Madhya Pradesh')}</option>
                <option value="TAMIL_NADU">{t('states.tamilNadu', 'Tamil Nadu')}</option>
                <option value="RAJASTHAN">{t('states.rajasthan', 'Rajasthan')}</option>
                <option value="KARNATAKA">{t('states.karnataka', 'Karnataka')}</option>
                <option value="GUJARAT">{t('states.gujarat', 'Gujarat')}</option>
                <option value="DELHI">{t('states.delhi', 'Delhi')}</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-[#3B2522] mb-1.5">{t('profile.socialCategory', 'Social Category')}</label>
              <select
                value={formSocialCategory}
                onChange={(e) => setFormSocialCategory(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-[#E8D8D2] text-xs focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] outline-none font-medium text-[#3B2522] bg-white"
              >
                <option value="SC">{t('category.sc', 'Scheduled Caste (SC - NSFDC Concessional Loans)')}</option>
                <option value="OBC">{t('category.obc', 'Other Backward Class (OBC - NBCFDC Loans)')}</option>
                <option value="ST">{t('category.st', 'Scheduled Tribe (ST - NSTFDC Concessional Loans)')}</option>
                <option value="MINORITY">{t('category.minority', 'Notified Minority Community (NMDFC Schemes)')}</option>
                <option value="GENERAL">{t('category.general', 'General / Unreserved')}</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-[#3B2522] mb-1.5">{t('profile.annualIncome', 'Annual Family Income (₹)')}</label>
              <select
                value={formIncomeSlab}
                onChange={(e) => setFormIncomeSlab(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl border border-[#E8D8D2] text-xs focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] outline-none font-medium text-[#3B2522] bg-white"
              >
                <option value={90000}>{t('recommendations.incomeSlabBelow1L', 'Below ₹1 Lakh (₹90,000)')}</option>
                <option value={180000}>{t('recommendations.incomeSlab1to2L', '₹1 Lakh – ₹2 Lakh (₹1,80,000)')}</option>
                <option value={300000}>{t('recommendations.incomeSlab2to3L', '₹2 Lakh – ₹3 Lakh (₹3,00,000)')}</option>
                <option value={500000}>{t('recommendations.incomeSlab3to5L', '₹3 Lakh – ₹5 Lakh (₹5,00,000)')}</option>
                <option value={1000000}>{t('recommendations.incomeSlabAbove5L', 'Above ₹5 Lakh (₹10,00,000)')}</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-[#3B2522] mb-1.5">{t('profile.projectCost', 'Project Cost')}</label>
              <select
                value={formProjectCostSlab}
                onChange={(e) => setFormProjectCostSlab(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl border border-[#E8D8D2] text-xs focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B] outline-none font-medium text-[#3B2522] bg-white"
              >
                <option value={50000}>{t('recommendations.projectCostUpTo50k', 'Up to ₹50,000')}</option>
                <option value={100000}>{t('recommendations.projectCost1L', '₹1,00,000 (Micro Loan)')}</option>
                <option value={500000}>{t('recommendations.projectCost5L', '₹5,00,000 (Term Loan / Vikas)')}</option>
                <option value={1500000}>{t('recommendations.projectCost15L', '₹15,00,000 (Major Unit)')}</option>
                <option value={5000000}>{t('recommendations.projectCostAbove50L', 'Above ₹50,00,000')}</option>
              </select>
            </div>

            <div className="sm:col-span-2 lg:col-span-3 pt-2">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full btn-primary min-h-[44px] justify-center text-sm font-bold shadow-warm-sm transition flex items-center gap-2 bg-[#EA717B] hover:bg-[#d65f69] text-white"
              >
                {isLoading ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>{t('recommendations.evaluateBtn', 'Evaluate Matching Schemes')}</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* RESULTS LIST SECTION (Warm Theme) */}
      {standardResult && (
        <div ref={resultsRef} id="scheme-results" className="space-y-6 pt-4 scroll-mt-24">
          {/* ── Extracted Natural Language Profile Grounding Banner ── */}
          {extractionResult && (
            <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-2xl p-4 sm:p-5 shadow-warm-xs space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#FFD0CA]/70 pb-2.5">
                <div className="flex items-center gap-2 text-[#3B2522] font-extrabold text-xs sm:text-sm">
                  <Sparkles className="w-4 h-4 text-[#F7AE56] shrink-0" />
                  <span>{t('recommendations.extractedProfileTitle', 'Extracted Profile Parameters (Grounded Input)')}</span>
                </div>
                <span className="text-[11px] font-bold text-[#4A2525] bg-[#FFD0CA] px-2.5 py-0.5 rounded-full border border-[#EA717B]/30">
                  Direct Statutory Grounding
                </span>
              </div>

              <p className="text-xs text-[#765E59] leading-relaxed">
                {t(
                  'recommendations.extractedProfileDesc',
                  'The following demographic and financial attributes were extracted directly from your input and evaluated deterministically against official scheme criteria:'
                )}
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 pt-1">
                <div className="bg-white p-2.5 rounded-xl border border-[#E8D8D2] text-xs shadow-warm-xs">
                  <span className="text-[10px] uppercase font-bold text-[#F7AE56] block">Age</span>
                  <span className="font-extrabold text-[#3B2522] text-xs sm:text-sm">
                    {extractionResult.extracted_profile.age ? `${extractionResult.extracted_profile.age} yrs` : 'Unspecified'}
                  </span>
                </div>

                <div className="bg-white p-2.5 rounded-xl border border-[#E8D8D2] text-xs shadow-warm-xs">
                  <span className="text-[10px] uppercase font-bold text-[#F7AE56] block">Gender</span>
                  <span className="font-extrabold text-[#3B2522] text-xs sm:text-sm capitalize">
                    {extractionResult.extracted_profile.gender ? extractionResult.extracted_profile.gender.toLowerCase() : 'Unspecified'}
                  </span>
                </div>

                <div className="bg-white p-2.5 rounded-xl border border-[#E8D8D2] text-xs shadow-warm-xs">
                  <span className="text-[10px] uppercase font-bold text-[#F7AE56] block">State</span>
                  <span className="font-extrabold text-[#3B2522] text-xs sm:text-sm truncate block" title={extractionResult.extracted_profile.state || 'All India'}>
                    {extractionResult.extracted_profile.state ? extractionResult.extracted_profile.state.replace(/_/g, ' ') : 'All India'}
                  </span>
                </div>

                <div className="bg-white p-2.5 rounded-xl border border-[#E8D8D2] text-xs shadow-warm-xs">
                  <span className="text-[10px] uppercase font-bold text-[#F7AE56] block">Category</span>
                  <span className="font-extrabold text-[#3B2522] text-xs sm:text-sm">
                    {extractionResult.extracted_profile.social_category || 'General'}
                  </span>
                </div>

                <div className="bg-white p-2.5 rounded-xl border border-[#E8D8D2] text-xs shadow-warm-xs">
                  <span className="text-[10px] uppercase font-bold text-[#F7AE56] block">Annual Income</span>
                  <span className="font-extrabold text-[#3B2522] text-xs sm:text-sm">
                    {extractionResult.extracted_profile.annual_income
                      ? `₹${extractionResult.extracted_profile.annual_income.toLocaleString('en-IN')}`
                      : 'Unspecified'}
                  </span>
                </div>

                <div className="bg-white p-2.5 rounded-xl border border-[#E8D8D2] text-xs shadow-warm-xs">
                  <span className="text-[10px] uppercase font-bold text-[#F7AE56] block">Project Cost / Loan</span>
                  <span className="font-extrabold text-[#3B2522] text-xs sm:text-sm">
                    {extractionResult.extracted_profile.project_cost
                      ? `₹${extractionResult.extracted_profile.project_cost.toLocaleString('en-IN')}`
                      : extractionResult.extracted_profile.requested_loan_amount
                      ? `₹${extractionResult.extracted_profile.requested_loan_amount.toLocaleString('en-IN')}`
                      : 'Standard Unit'}
                  </span>
                </div>
              </div>

              {extractionResult.missing_high_priority_fields && extractionResult.missing_high_priority_fields.length > 0 && (
                <div className="flex items-center gap-2 pt-1 text-[11px] text-[#765E59]">
                  <Info className="w-3.5 h-3.5 text-[#EA717B] shrink-0" />
                  <span>
                    Additional parameters not specified in text: <strong>{extractionResult.missing_high_priority_fields.join(', ')}</strong> (evaluated under standard baseline rules).
                  </span>
                </div>
              )}
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#E8D8D2] pb-4">
            <div>
              <h2 className="text-xl font-extrabold text-[#3B2522] flex items-center gap-2">
                <Award className="w-6 h-6 text-[#F7AE56]" />
                {t('recommendations.resultsTitle', 'Deterministic Scheme Eligibility & Rankings')}
              </h2>
              <p className="text-xs text-[#765E59] mt-0.5">
                {t('recommendations.evalCount', { count: standardResult.evaluated_scheme_count, defaultValue: `Evaluated ${standardResult.evaluated_scheme_count} official schemes against your profile rules.` })}
              </p>
            </div>

            {/* Scheme Evaluation Summary Counters */}
            <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 text-[11px] sm:text-xs font-bold">
              <span className="bg-emerald-50 text-emerald-800 px-3 py-1.5 rounded-xl border border-emerald-200 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                {standardResult.eligible_scheme_count} {t('recommendations.tabEligible', 'Eligible')}
              </span>
              {(standardResult.conditional_scheme_count || 0) > 0 && (
                <span className="bg-[#FFD0CA] text-[#4A2525] px-3 py-1.5 rounded-xl border border-[#EA717B]/30 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#EA717B]" />
                  {standardResult.conditional_scheme_count} {t('recommendations.conditional', 'Conditional')}
                </span>
              )}
              <span className="bg-[#F7AE56]/20 text-[#3B2522] px-3 py-1.5 rounded-xl border border-[#F7AE56]/40 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-[#F7AE56]" />
                {standardResult.insufficient_info_scheme_count} {t('recommendations.tabInfoNeeded', 'Info Needed')}
              </span>
              <span className="bg-[#EA717B]/15 text-[#4A2525] px-3 py-1.5 rounded-xl border border-[#EA717B]/30 flex items-center gap-1.5">
                <XCircle className="w-3.5 h-3.5 text-[#EA717B]" />
                {standardResult.excluded_scheme_count} {t('recommendations.tabIneligible', 'Ineligible')}
              </span>
            </div>
          </div>

          {/* Status Tabs Filter */}
          <div className="flex flex-wrap gap-2 border-b border-[#E8D8D2] pb-3">
            <button
              onClick={() => setActiveTab('ELIGIBLE')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                activeTab === 'ELIGIBLE'
                  ? 'bg-emerald-600 text-white shadow-warm-xs'
                  : 'bg-[#FFF4EC] hover:bg-[#FFD0CA]/40 text-[#765E59] border border-[#E8D8D2]'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              {t('recommendations.filterEligible', 'Eligible Schemes')} ({standardResult.eligible_scheme_count})
            </button>

            {(standardResult.conditional_scheme_count || 0) > 0 && (
              <button
                onClick={() => setActiveTab('CONDITIONAL')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                  activeTab === 'CONDITIONAL'
                    ? 'bg-[#4A2525] text-white shadow-warm-xs'
                    : 'bg-[#FFF4EC] hover:bg-[#FFD0CA]/40 text-[#765E59] border border-[#E8D8D2]'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                {t('recommendations.filterConditional', 'Conditional Schemes')} ({standardResult.conditional_scheme_count})
              </button>
            )}

            <button
              onClick={() => setActiveTab('INSUFFICIENT')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                activeTab === 'INSUFFICIENT'
                  ? 'bg-[#F7AE56] text-[#3B2522] shadow-warm-xs'
                  : 'bg-[#FFF4EC] hover:bg-[#FFD0CA]/40 text-[#765E59] border border-[#E8D8D2]'
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              {t('recommendations.filterMoreInfo', 'Needs More Information')} ({standardResult.insufficient_info_scheme_count})
            </button>

            <button
              onClick={() => setActiveTab('INELIGIBLE')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                activeTab === 'INELIGIBLE'
                  ? 'bg-[#EA717B] text-white shadow-warm-xs'
                  : 'bg-[#FFF4EC] hover:bg-[#FFD0CA]/40 text-[#765E59] border border-[#E8D8D2]'
              }`}
            >
              <XCircle className="w-3.5 h-3.5" />
              {t('recommendations.filterIneligible', 'Ineligible Schemes')} ({standardResult.excluded_scheme_count})
            </button>

            <button
              onClick={() => setActiveTab('ALL')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                activeTab === 'ALL'
                  ? 'bg-[#4A2525] text-white shadow-warm-xs'
                  : 'bg-[#FFF4EC] hover:bg-[#FFD0CA]/40 text-[#765E59] border border-[#E8D8D2]'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              {t('recommendations.filterAll', 'All Evaluated Schemes')} ({standardResult.evaluated_scheme_count})
            </button>
          </div>

          {/* Recommendation / Evaluation Cards */}
          {displayedItems.length === 0 ? (
            <div className="bg-[#FFF4EC] border border-dashed border-[#FFD0CA] rounded-2xl p-8 text-center text-[#765E59] text-sm">
              <Info className="w-8 h-8 text-[#F7AE56] mx-auto mb-2" />
              {emptyMessage}
            </div>
          ) : (
            <div className="space-y-6">
              {displayedItems.map((rec: RecommendationItem, idx: number) => {
                const isEligible = rec.eligibility_status === 'ELIGIBLE';
                const isConditional = rec.eligibility_status === 'CONDITIONAL';
                const isInsufficient = rec.eligibility_status === 'INSUFFICIENT_INFORMATION';
                const isIneligible = rec.eligibility_status === 'INELIGIBLE' || rec.eligibility_status === 'NOT_APPLICABLE';

                const matchPct = isIneligible ? 0 : Math.round(rec.score ?? 0);
                const matchLabel = isIneligible ? 'Ineligible' : getMatchLabel(matchPct);
                const isExpanded = !!expandedDetails[rec.scheme_id];
                const officialUrl = rec.application_url || rec.official_portal || rec.official_source_url;

                // Pre-fill amount for calculator
                const requestedAmount = canonicalProfile?.requested_loan_amount || canonicalProfile?.project_cost || formProjectCostSlab || '';

                // Prepared clean reason lists
                const allEligibleReasons = [
                  ...(rec.matched_rules && rec.matched_rules.length > 0 ? rec.matched_rules : rec.eligibility_reasons || []),
                  ...(rec.recommendation_reasons || [])
                ].map(cleanReasonText).filter(Boolean);
                const defaultEligible = allEligibleReasons.slice(0, 3);
                const remainingEligible = allEligibleReasons.slice(3);

                const allConditionalReasons = [
                  ...(rec.key_conditions && rec.key_conditions.length > 0 ? rec.key_conditions : []),
                  ...(rec.eligibility_reasons && rec.eligibility_reasons.length > 0 ? rec.eligibility_reasons : []),
                  ...(rec.matched_rules || [])
                ].map(cleanReasonText).filter(Boolean);
                const defaultConditional = allConditionalReasons.slice(0, 3);
                const remainingConditional = allConditionalReasons.slice(3);

                const allFailedReasons = (rec.failed_rules && rec.failed_rules.length > 0 ? rec.failed_rules : rec.eligibility_reasons || [])
                  .map(cleanReasonText).filter(Boolean);
                const defaultFailed = allFailedReasons.slice(0, 3);
                const remainingFailed = allFailedReasons.slice(3);

                const allMissingReasons = (rec.missing_information && rec.missing_information.length > 0
                  ? rec.missing_information
                  : ['Additional demographic or financial parameters required.']
                ).map(cleanReasonText).filter(Boolean);
                const defaultMissing = allMissingReasons.slice(0, 3);
                const remainingMissing = allMissingReasons.slice(3);

                return (
                  <div
                    key={rec.scheme_id || idx}
                    className={`bg-white rounded-2xl border shadow-warm-xs p-4 sm:p-5 hover:shadow-warm-md transition space-y-4 ${
                      isEligible
                        ? 'border-emerald-200 ring-1 ring-emerald-100'
                        : isConditional
                        ? 'border-[#FFD0CA] ring-1 ring-[#FFD0CA]/50'
                        : isInsufficient
                        ? 'border-[#F7AE56]/40 ring-1 ring-[#F7AE56]/20'
                        : 'border-[#E8D8D2] opacity-95'
                    }`}
                  >
                    {/* ── 1. SCHEME HEADER & COMPACT FIT SCORE ── */}
                    <div className="flex items-start gap-3">
                      {/* Rank Badge on Left */}
                      <div
                        className={`w-8 h-8 sm:w-9 sm:h-9 rounded-xl font-black text-xs sm:text-sm flex items-center justify-center shrink-0 shadow-warm-xs ${
                          isEligible
                            ? 'bg-emerald-600 text-white'
                            : isConditional
                            ? 'bg-[#4A2525] text-white'
                            : isInsufficient
                            ? 'bg-[#F7AE56] text-[#3B2522]'
                            : 'bg-[#765E59] text-white'
                        }`}
                      >
                        #{rec.rank || idx + 1}
                      </div>

                      {/* Main Header Info Area */}
                      <div className="flex-1 min-w-0 space-y-1.5">
                        <div className="flex flex-wrap items-baseline justify-between gap-x-2 gap-y-1">
                          <h3 className="text-sm sm:text-base font-extrabold text-[#3B2522] leading-snug hover:text-[#EA717B] transition">
                            <Link to={`/schemes/${rec.scheme_id}?amount=${requestedAmount}`}>
                              {rec.scheme_name}
                            </Link>
                          </h3>
                        </div>

                        {/* Short Purpose / Objective */}
                        {(rec.purpose || rec.short_description || rec.financial_assistance_summary) && (
                          <p className="text-xs sm:text-sm text-[#765E59] line-clamp-2 leading-relaxed">
                            {rec.purpose || rec.short_description || rec.financial_assistance_summary}
                          </p>
                        )}

                        {/* Secondary Details: Scheme ID & Ministry */}
                        <div className="flex flex-wrap items-center gap-2 text-xs text-[#765E59] pt-0.5">
                          <span className="font-mono text-xs bg-[#FFFBF0] px-2 py-0.5 rounded border border-[#E8D8D2] text-[#765E59] font-semibold">
                            {rec.scheme_id}
                          </span>
                          {rec.is_direct_portal_scheme && (
                            <span className="text-xs font-bold bg-[#FFD0CA] text-[#4A2525] px-2.5 py-0.5 rounded-full">
                              Direct Govt Portal
                            </span>
                          )}
                          {rec.ministry && (
                            <span className="hidden sm:inline text-xs text-[#765E59] font-medium truncate max-w-sm">
                              • {rec.ministry}
                            </span>
                          )}
                        </div>

                        {/* Eligibility + Compact Fit Badges directly alongside */}
                        <div className="flex flex-wrap items-center gap-2 pt-1">
                          {isEligible && (
                            <span className="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                              <span>✓ {t('recommendations.tabEligible', 'Eligible')}</span>
                            </span>
                          )}
                          {isConditional && (
                            <span className="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full font-bold bg-[#FFD0CA] text-[#4A2525] border border-[#EA717B]/40">
                              <ShieldCheck className="w-3.5 h-3.5 text-[#EA717B]" />
                              <span>⚡ {t('recommendations.conditional', 'Conditional')}</span>
                            </span>
                          )}
                          {isInsufficient && (
                            <span className="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full font-bold bg-[#F7AE56]/20 text-[#3B2522] border border-[#F7AE56]/40">
                              <AlertTriangle className="w-3.5 h-3.5 text-[#F7AE56]" />
                              <span>⚠ {t('recommendations.moreInfoRequired', 'More Info Needed')}</span>
                            </span>
                          )}
                          {isIneligible && (
                            <span className="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full font-bold bg-[#EA717B]/15 text-[#4A2525] border border-[#EA717B]/30">
                              <XCircle className="w-3.5 h-3.5 text-[#EA717B]" />
                              <span>✕ {t('recommendations.notEligible', 'Not Eligible')}</span>
                            </span>
                          )}

                          {/* Compact Fit Score Badge */}
                          <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded-full font-extrabold bg-[#FFF4EC] text-[#3B2522] border border-[#E8D8D2]">
                            <span className="font-mono text-[#EA717B] font-black">{matchPct}% Fit</span>
                            <span className="text-xs font-medium text-[#765E59]">• {matchLabel}</span>
                          </span>

                          {/* Scheme Financial Health / Fit Badge */}
                          {rec.is_credit_scheme === false || rec.financial_suitability === 'NOT_APPLICABLE' ? (
                            <span
                              className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full font-bold bg-[#FFFBF0] text-[#765E59] border border-[#E8D8D2]"
                              title="Non-credit scheme: Direct subsidy/welfare assistance with zero debt repayment obligations"
                            >
                              <span>{t('recommendations.fitNonCredit', 'Financial Fit: Non-Credit Scheme')}</span>
                            </span>
                          ) : rec.financial_suitability === 'STRONG_FIT' ? (
                            <span
                              className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-900 border border-emerald-300"
                              title={rec.financial_suitability_reason || 'Comfortable debt service capacity'}
                            >
                              <span>{t('recommendations.fitComfortable', '🟢 Financial Fit: Comfortable')}</span>
                            </span>
                          ) : rec.financial_suitability === 'POSSIBLE_FIT' ? (
                            <span
                              className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full font-bold bg-[#F7AE56]/20 text-[#3B2522] border border-[#F7AE56]/40"
                              title={rec.financial_suitability_reason || 'Manageable repayment burden'}
                            >
                              <span>{t('recommendations.fitManageable', '🟡 Financial Fit: Manageable')}</span>
                            </span>
                          ) : rec.financial_suitability === 'FINANCIALLY_UNSUITABLE' ? (
                            <span
                              className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full font-bold bg-[#EA717B]/15 text-[#4A2525] border border-[#EA717B]/30"
                              title={rec.financial_suitability_reason || 'High repayment burden detected'}
                            >
                              <span>{t('recommendations.fitHighBurden', '🔴 Financial Fit: High Repayment Burden')}</span>
                            </span>
                          ) : rec.financial_suitability_reason && rec.financial_suitability_reason.includes('specified') ? (
                            <span
                              className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full font-bold bg-[#FFFBF0] text-[#765E59] border border-[#E8D8D2]"
                              title={rec.financial_suitability_reason}
                            >
                              <span>{t('recommendations.fitUnspecified', '⚪ Financial Fit: Lender Rate Unspecified')}</span>
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </div>

                    {/* ── VERIFIED FINANCIAL CATEGORY & ASSISTANCE OVERVIEW ── */}
                    <div className="bg-[#FFFBF0] rounded-xl p-3 sm:p-3.5 border border-[#E8D8D2] grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
                      <div>
                        <span className="text-[10px] sm:text-[11px] uppercase tracking-wider font-semibold text-[#765E59] block">
                          {t('recommendations.financialCategoryLabel', 'Financial Category')}
                        </span>
                        <span className="font-bold text-[#3B2522] text-xs sm:text-[13px] truncate block mt-0.5" title={formatFinancialCategory(rec.financial_category)}>
                          {formatFinancialCategory(rec.financial_category)}
                        </span>
                      </div>

                      <div>
                        <span className="text-[10px] sm:text-[11px] uppercase tracking-wider font-semibold text-[#765E59] block">
                          {rec.max_loan_amount ? 'Max Assistance Limit' : rec.grant_amount ? 'Grant Amount' : 'Assistance Mode'}
                        </span>
                        <span className="font-bold text-[#3B2522] font-mono text-xs sm:text-[13px] block mt-0.5">
                          {rec.max_loan_amount
                            ? `₹${rec.max_loan_amount >= 100000 ? `${(rec.max_loan_amount / 100000).toFixed(1)} Lakh` : rec.max_loan_amount.toLocaleString('en-IN')}`
                            : rec.grant_amount
                            ? `₹${rec.grant_amount.toLocaleString('en-IN')}`
                            : rec.is_credit_scheme === false
                            ? 'Direct Benefit'
                            : 'Per Scheme Rules'}
                        </span>
                      </div>

                      <div>
                        <span className="text-[10px] sm:text-[11px] uppercase tracking-wider font-semibold text-[#765E59] block">
                          {rec.interest_rate !== undefined && rec.interest_rate !== null ? 'Interest Rate' : rec.subsidy_percentage ? 'Capital Subsidy' : 'Repayment Period'}
                        </span>
                        <span className="font-bold text-emerald-700 font-mono text-xs sm:text-[13px] block mt-0.5">
                          {rec.interest_rate !== undefined && rec.interest_rate !== null
                            ? `${rec.interest_rate > 0 ? `${rec.interest_rate}% p.a.` : 'Concessional / 0%'}`
                            : rec.subsidy_percentage
                            ? `${rec.subsidy_percentage}% of Project`
                            : rec.repayment_period_max_months
                            ? `${rec.repayment_period_max_months} Months`
                            : 'Concessional Terms'}
                        </span>
                      </div>

                      <div>
                        <span className="text-[10px] sm:text-[11px] uppercase tracking-wider font-semibold text-[#765E59] block">
                          {rec.estimated_monthly_installment ? 'Est. Repayment EMI' : rec.available_subsidy_amount ? 'Available Subsidy' : 'Verification'}
                        </span>
                        <span className="font-bold text-[#3B2522] font-mono text-xs sm:text-[13px] block mt-0.5">
                          {rec.estimated_monthly_installment
                            ? `₹${Math.round(rec.estimated_monthly_installment).toLocaleString('en-IN')}/mo`
                            : rec.available_subsidy_amount
                            ? `₹${Math.round(rec.available_subsidy_amount).toLocaleString('en-IN')}`
                            : 'Verified Authoritative'}
                        </span>
                      </div>
                    </div>

                    {/* ── 2. WHY YOU QUALIFY / CRITERIA SUMMARY ── */}
                    {isEligible && (
                      <div className="bg-emerald-50/70 rounded-xl p-3 sm:p-4 border border-emerald-200/80 text-xs space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="font-extrabold text-emerald-950 flex items-center gap-1.5 text-xs sm:text-sm">
                            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                            <span>{t('recommendations.whyQualifyTitle', 'Why You Qualify For This Scheme')}</span>
                          </div>
                          {allEligibleReasons.length > 0 && (
                            <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100/90 px-2 py-0.5 rounded-full border border-emerald-200">
                              {allEligibleReasons.length} Criteria Passed
                            </span>
                          )}
                        </div>

                        {/* Top 3 concise reasons */}
                        <ul className="space-y-1.5 pt-0.5">
                          {defaultEligible.map((reason, rIdx) => (
                            <li key={rIdx} className="flex items-start gap-2 text-[#3B2522] text-[11px] sm:text-xs leading-relaxed">
                              <span className="text-emerald-600 font-bold shrink-0 mt-0.5">✓</span>
                              <span>{reason}</span>
                            </li>
                          ))}
                        </ul>

                        {/* Expanded remaining reasons */}
                        {isExpanded && remainingEligible.length > 0 && (
                          <ul className="space-y-1.5 pt-1 border-t border-emerald-200/60">
                            {remainingEligible.map((reason, rIdx) => (
                              <li key={`rem-${rIdx}`} className="flex items-start gap-2 text-[#3B2522] text-[11px] sm:text-xs leading-relaxed">
                                <span className="text-emerald-600 font-bold shrink-0 mt-0.5">✓</span>
                                <span>{reason}</span>
                              </li>
                            ))}
                          </ul>
                        )}

                        {/* Non-guaranteed approval disclaimer */}
                        <p className="text-[11px] text-[#765E59] italic pt-1 border-t border-emerald-200/50">
                          Satisfies statutory eligibility criteria. Final loan sanction and disbursement depend on channel partner verification and underwriting. Approval is not guaranteed.
                        </p>

                        {/* Toggle button */}
                        {(remainingEligible.length > 0 || (rec.score_breakdown && rec.score_breakdown.length > 0)) && (
                          <div className="pt-2">
                            <button
                              type="button"
                              onClick={() => toggleDetails(rec.scheme_id)}
                              className="w-full flex items-center justify-between px-3.5 py-2 rounded-lg bg-white/90 hover:bg-white border border-emerald-200 text-xs font-semibold text-emerald-900 transition shadow-warm-xs focus:outline-hidden focus:ring-2 focus:ring-emerald-500/20"
                              aria-expanded={isExpanded}
                            >
                              <span className="flex items-center gap-1.5">
                                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                                <span>
                                  {isExpanded
                                    ? t('recommendations.hideBreakdown', 'Hide Criteria Breakdown')
                                    : t('recommendations.viewAllCriteria', 'View Criteria Breakdown')}
                                </span>
                                {!isExpanded && remainingEligible.length > 0 && (
                                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                                    +{remainingEligible.length} more
                                  </span>
                                )}
                              </span>
                              {isExpanded ? (
                                <ChevronUp className="w-4 h-4 text-emerald-700" />
                              ) : (
                                <ChevronDown className="w-4 h-4 text-emerald-700" />
                              )}
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                    {/* ── CONDITIONAL STATUTORY ELIGIBILITY ── */}
                    {isConditional && (
                      <div className="bg-[#FFF4EC] rounded-xl p-3 sm:p-4 border border-[#FFD0CA] text-xs space-y-2 text-[#3B2522]">
                        <div className="flex items-center justify-between">
                          <div className="font-extrabold text-[#4A2525] flex items-center gap-1.5 text-xs sm:text-sm">
                            <ShieldCheck className="w-4 h-4 text-[#EA717B] shrink-0" />
                            <span>{t('recommendations.statutoryConditionsRequired', 'Statutory Conditions Required')}</span>
                          </div>
                          {allConditionalReasons.length > 0 && (
                            <span className="text-[10px] font-bold text-[#4A2525] bg-[#FFD0CA] px-2 py-0.5 rounded-full border border-[#EA717B]/30">
                              {allConditionalReasons.length} Statutory Condition{allConditionalReasons.length > 1 ? 's' : ''}
                            </span>
                          )}
                        </div>

                        <p className="text-[11px] sm:text-xs text-[#765E59] leading-snug">
                          Applicant satisfies baseline profile parameters, subject to verifying the following statutory condition(s):
                        </p>

                        <ul className="space-y-1.5 pt-0.5">
                          {defaultConditional.map((reason, rIdx) => (
                            <li key={rIdx} className="flex items-start gap-2 text-[#3B2522] text-[11px] sm:text-xs leading-relaxed">
                              <span className="text-[#EA717B] font-bold shrink-0 mt-0.5">⚡</span>
                              <span>{reason}</span>
                            </li>
                          ))}
                        </ul>

                        {isExpanded && remainingConditional.length > 0 && (
                          <ul className="space-y-1.5 pt-1 border-t border-[#FFD0CA]/60">
                            {remainingConditional.map((reason, rIdx) => (
                              <li key={`rem-c-${rIdx}`} className="flex items-start gap-2 text-[#3B2522] text-[11px] sm:text-xs leading-relaxed">
                                <span className="text-[#EA717B] font-bold shrink-0 mt-0.5">⚡</span>
                                <span>{reason}</span>
                              </li>
                            ))}
                          </ul>
                        )}

                        {(remainingConditional.length > 0 || (rec.score_breakdown && rec.score_breakdown.length > 0)) && (
                          <div className="pt-2">
                            <button
                              type="button"
                              onClick={() => toggleDetails(rec.scheme_id)}
                              className="w-full flex items-center justify-between px-3.5 py-2 rounded-lg bg-white/90 hover:bg-white border border-[#FFD0CA] text-xs font-semibold text-[#4A2525] transition shadow-warm-xs focus:outline-hidden focus:ring-2 focus:ring-[#EA717B]/20"
                              aria-expanded={isExpanded}
                            >
                              <span className="flex items-center gap-1.5">
                                <ShieldCheck className="w-3.5 h-3.5 text-[#EA717B] shrink-0" />
                                <span>
                                  {isExpanded
                                    ? t('recommendations.hideBreakdown', 'Hide Criteria Breakdown')
                                    : t('recommendations.viewAllCriteria', 'View Criteria Breakdown')}
                                </span>
                                {!isExpanded && remainingConditional.length > 0 && (
                                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-[#FFD0CA] text-[#4A2525] border border-[#EA717B]/30">
                                    +{remainingConditional.length} more
                                  </span>
                                )}
                              </span>
                              {isExpanded ? (
                                <ChevronUp className="w-4 h-4 text-[#4A2525]" />
                              ) : (
                                <ChevronDown className="w-4 h-4 text-[#4A2525]" />
                              )}
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                    {isIneligible && (
                      <div className="bg-[#EA717B]/10 rounded-xl p-3 sm:p-4 border border-[#EA717B]/20 text-xs space-y-2 text-[#3B2522]">
                        <div className="flex items-center justify-between">
                          <div className="font-extrabold text-[#4A2525] flex items-center gap-1.5 text-xs sm:text-sm">
                            <XCircle className="w-4 h-4 text-[#EA717B] shrink-0" />
                            <span>{t('recommendations.statutoryCriteriaNotMet', 'Statutory Criteria Not Met')}</span>
                          </div>
                          {allFailedReasons.length > 0 && (
                            <span className="text-[10px] font-bold text-[#EA717B] bg-white px-2 py-0.5 rounded-full border border-[#EA717B]/30">
                              {allFailedReasons.length} Unmet Criteria
                            </span>
                          )}
                        </div>

                        <p className="text-[11px] sm:text-xs text-[#765E59] leading-snug">
                          Deterministic statutory check determined that the applicant does not satisfy the following mandatory requirement(s):
                        </p>

                        <ul className="space-y-1.5 pt-0.5">
                          {defaultFailed.map((reason, rIdx) => (
                            <li key={rIdx} className="flex items-start gap-2 text-[#3B2522] text-[11px] sm:text-xs leading-relaxed">
                              <span className="text-[#EA717B] font-bold shrink-0 mt-0.5">✕</span>
                              <span>{reason}</span>
                            </li>
                          ))}
                        </ul>

                        {isExpanded && remainingFailed.length > 0 && (
                          <ul className="space-y-1.5 pt-1 border-t border-[#EA717B]/20">
                            {remainingFailed.map((reason, rIdx) => (
                              <li key={`rem-f-${rIdx}`} className="flex items-start gap-2 text-[#3B2522] text-[11px] sm:text-xs leading-relaxed">
                                <span className="text-[#EA717B] font-bold shrink-0 mt-0.5">✕</span>
                                <span>{reason}</span>
                              </li>
                            ))}
                          </ul>
                        )}

                        {(remainingFailed.length > 0 || (rec.score_breakdown && rec.score_breakdown.length > 0)) && (
                          <div className="pt-2">
                            <button
                              type="button"
                              onClick={() => toggleDetails(rec.scheme_id)}
                              className="w-full flex items-center justify-between px-3.5 py-2 rounded-lg bg-white/90 hover:bg-white border border-[#EA717B]/30 text-xs font-semibold text-[#4A2525] transition shadow-warm-xs focus:outline-hidden focus:ring-2 focus:ring-[#EA717B]/20"
                              aria-expanded={isExpanded}
                            >
                              <span className="flex items-center gap-1.5">
                                <XCircle className="w-3.5 h-3.5 text-[#EA717B] shrink-0" />
                                <span>
                                  {isExpanded
                                    ? t('recommendations.hideBreakdown', 'Hide Criteria Breakdown')
                                    : t('recommendations.viewAllCriteria', 'View Criteria Breakdown')}
                                </span>
                                {!isExpanded && remainingFailed.length > 0 && (
                                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-[#EA717B]/20 text-[#4A2525] border border-[#EA717B]/30">
                                    +{remainingFailed.length} more
                                  </span>
                                )}
                              </span>
                              {isExpanded ? (
                                <ChevronUp className="w-4 h-4 text-[#4A2525]" />
                              ) : (
                                <ChevronDown className="w-4 h-4 text-[#4A2525]" />
                              )}
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                    {isInsufficient && (
                      <div className="bg-[#F7AE56]/15 rounded-xl p-3 sm:p-4 border border-[#F7AE56]/30 text-xs space-y-2 text-[#3B2522]">
                        <div className="flex items-center justify-between">
                          <div className="font-extrabold text-[#3B2522] flex items-center gap-1.5 text-xs sm:text-sm">
                            <AlertTriangle className="w-4 h-4 text-[#F7AE56] shrink-0" />
                            <span>{t('recommendations.missingInfoTitle', 'Missing Information Required')}</span>
                          </div>
                          <Link
                            to="/profile"
                            className="bg-[#EA717B] hover:bg-[#d65f69] text-white font-bold text-[10px] sm:text-[11px] px-2.5 py-1 rounded-lg shadow-warm-xs transition flex items-center gap-1"
                          >
                            <User className="w-3 h-3" />
                            <span>{t('recommendations.completeProfileBtn', 'Complete Profile →')}</span>
                          </Link>
                        </div>

                        <p className="text-[11px] sm:text-xs text-[#765E59] leading-snug">
                          To evaluate statutory eligibility, please provide the following missing profile information:
                        </p>

                        <ul className="space-y-1.5 pt-0.5">
                          {defaultMissing.map((msg, rIdx) => (
                            <li key={rIdx} className="flex items-start gap-2 text-[#3B2522] text-[11px] sm:text-xs leading-relaxed">
                              <span className="text-[#F7AE56] font-bold shrink-0 mt-0.5">⚠</span>
                              <span>{msg}</span>
                            </li>
                          ))}
                        </ul>

                        {isExpanded && remainingMissing.length > 0 && (
                          <ul className="space-y-1.5 pt-1 border-t border-[#F7AE56]/30">
                            {remainingMissing.map((msg, rIdx) => (
                              <li key={`rem-i-${rIdx}`} className="flex items-start gap-2 text-[#3B2522] text-[11px] sm:text-xs leading-relaxed">
                                <span className="text-[#F7AE56] font-bold shrink-0 mt-0.5">⚠</span>
                                <span>{msg}</span>
                              </li>
                            ))}
                          </ul>
                        )}

                        {(remainingMissing.length > 0 || (rec.score_breakdown && rec.score_breakdown.length > 0)) && (
                          <div className="pt-2">
                            <button
                              type="button"
                              onClick={() => toggleDetails(rec.scheme_id)}
                              className="w-full flex items-center justify-between px-3.5 py-2 rounded-lg bg-white/90 hover:bg-white border border-[#F7AE56]/30 text-xs font-semibold text-[#3B2522] transition shadow-warm-xs focus:outline-hidden focus:ring-2 focus:ring-[#F7AE56]/20"
                              aria-expanded={isExpanded}
                            >
                              <span className="flex items-center gap-1.5">
                                <AlertTriangle className="w-3.5 h-3.5 text-[#F7AE56] shrink-0" />
                                <span>
                                  {isExpanded
                                    ? t('recommendations.hideBreakdown', 'Hide Criteria Breakdown')
                                    : t('recommendations.viewAllCriteria', 'View Criteria Breakdown')}
                                </span>
                                {!isExpanded && remainingMissing.length > 0 && (
                                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-[#F7AE56]/20 text-[#3B2522] border border-[#F7AE56]/40">
                                    +{remainingMissing.length} more
                                  </span>
                                )}
                              </span>
                              {isExpanded ? (
                                <ChevronUp className="w-4 h-4 text-[#3B2522]" />
                              ) : (
                                <ChevronDown className="w-4 h-4 text-[#3B2522]" />
                              )}
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                    {/* ── 3. COLLAPSIBLE CRITERIA BREAKDOWN ── */}
                    {isExpanded && rec.score_breakdown && rec.score_breakdown.length > 0 && (
                      <div className="p-3 sm:p-4 bg-[#FFFBF0] rounded-xl border border-[#E8D8D2] text-xs space-y-3">
                        <div className="flex items-center justify-between border-b border-[#E8D8D2] pb-2">
                          <span className="font-extrabold text-[#3B2522] text-xs sm:text-sm flex items-center gap-1.5">
                            <ShieldCheck className="w-4 h-4 text-[#EA717B]" />
                            <span>{t('recommendations.fullBreakdown', 'Full Eligibility & Scoring Breakdown')}</span>
                          </span>
                          <span className="font-mono font-bold text-[#765E59] text-xs">
                            Total: {rec.score.toFixed(1)} / 100
                          </span>
                        </div>

                        <div className="grid grid-cols-1 gap-2">
                          {rec.score_breakdown.map((b, bIdx) => {
                            const isMatch = b.result === 'MATCH';
                            const isUnmet = b.result === 'NO_MATCH';
                            const isPending = b.result === 'PARTIAL_MATCH' || b.result === 'NOT_EVALUATED';
                            const cleanReason = cleanReasonText(b.reason);

                            return (
                              <div
                                key={bIdx}
                                className={`p-2.5 rounded-lg border flex items-start justify-between gap-2.5 text-xs transition ${
                                  isMatch
                                    ? 'bg-emerald-50/50 border-emerald-200 text-[#3B2522]'
                                    : isUnmet
                                    ? 'bg-[#EA717B]/10 border-[#EA717B]/30 text-[#3B2522]'
                                    : 'bg-[#F7AE56]/10 border-[#F7AE56]/30 text-[#3B2522]'
                                }`}
                              >
                                <div className="space-y-0.5 min-w-0">
                                  <div className="flex flex-wrap items-center gap-1.5">
                                    {isMatch && (
                                      <span className="inline-flex items-center text-xs font-bold text-emerald-800 bg-emerald-100 px-1.5 py-0.5 rounded">
                                        ✓ Matched
                                      </span>
                                    )}
                                    {isUnmet && (
                                      <span className="inline-flex items-center text-xs font-bold text-[#EA717B] bg-[#EA717B]/15 px-1.5 py-0.5 rounded">
                                        ! Unmet
                                      </span>
                                    )}
                                    {isPending && (
                                      <span className="inline-flex items-center text-xs font-bold text-[#3B2522] bg-[#F7AE56]/20 px-1.5 py-0.5 rounded">
                                        ○ Verification Needed
                                      </span>
                                    )}
                                    <span className="text-[#3B2522] text-xs font-bold capitalize">
                                      {b.dimension.replace(/_/g, ' ')}
                                    </span>
                                  </div>
                                  <p className="text-xs text-[#765E59] pl-0.5 leading-snug">{cleanReason}</p>
                                </div>

                                <div className="text-right shrink-0 font-mono text-xs pt-0.5">
                                  <span className={`font-bold ${isMatch ? 'text-emerald-700' : isUnmet ? 'text-[#EA717B]' : 'text-[#F7AE56]'}`}>
                                    +{b.score.toFixed(1)}
                                  </span>
                                  <span className="text-[#765E59]/60"> / {b.max_weight.toFixed(1)}</span>
                                </div>
                              </div>
                            );
                          })}
                        </div>

                        {rec.source_document && (
                          <div className="pt-2 border-t border-[#E8D8D2] text-xs text-[#765E59] flex items-center gap-1">
                            <FileText className="w-3.5 h-3.5 text-[#765E59] shrink-0" />
                            <span className="truncate">Official Rules Source: {rec.source_document}</span>
                          </div>
                        )}

                        {/* RAG Knowledge Citations & Grounded Explanation if loaded */}
                        {(() => {
                          const aiItem = aiResult?.recommendations?.find(
                            (a) => a.scheme_id === rec.scheme_id
                          );
                          if (!aiItem) return null;
                          return (
                            <div className="pt-2.5 border-t border-[#E8D8D2] space-y-2">
                              {aiItem.ai_explanation && (
                                <div className="bg-[#FFF4EC] border border-[#FFD0CA] rounded-lg p-2.5 text-xs text-[#4A2525] space-y-1">
                                  <span className="font-bold flex items-center gap-1 text-[11px] text-[#EA717B] uppercase tracking-wider">
                                    <Sparkles className="w-3 h-3 text-[#F7AE56]" /> Grounded Statutory Summary
                                  </span>
                                  <p className="text-[11px] leading-relaxed text-[#765E59]">{aiItem.ai_explanation}</p>
                                </div>
                              )}
                              {aiItem.citations && aiItem.citations.length > 0 && (
                                <div className="space-y-1.5 pt-0.5">
                                  <span className="font-bold text-[#3B2522] text-[11px] uppercase tracking-wider block">
                                    Verified Official Source Citations ({aiItem.citations.length})
                                  </span>
                                  <div className="space-y-1 pl-2 border-l-2 border-[#FFD0CA]">
                                    {aiItem.citations.map((cite, cIdx) => (
                                      <div key={cIdx} className="text-[11px] text-[#765E59] leading-snug">
                                        <span className="font-semibold text-[#3B2522]">
                                          {cite.source_document || cite.source_type}
                                          {cite.rule_id ? ` • Rule ${cite.rule_id}` : ''}:
                                        </span>{' '}
                                        <span className="italic">"{cite.snippet}"</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })()}
                      </div>
                    )}

                    {/* Advisory notice */}
                    <div className="bg-[#FFFBF0] rounded-xl p-2.5 text-xs text-[#765E59] border border-[#E8D8D2] flex items-start gap-2">
                      <Info className="w-3.5 h-3.5 text-[#F7AE56] shrink-0 mt-0.5" />
                      <span>{t('howToApply.disclaimer', 'Eligibility guidance only. Final eligibility and approval are determined by the concerned government authority.')}</span>
                    </div>

                    {/* ── 4. REDESIGNED COMPACT ACTION AREA (Warm Theme) ── */}
                    <div className="pt-3 border-t border-[#E8D8D2]/60 flex flex-col gap-2.5">
                      {/* Priority Tier 1: Primary Action & Direct View */}
                      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                        {officialUrl ? (
                          <button
                            type="button"
                            onClick={() => openPortalModal(rec.scheme_name, officialUrl)}
                            className="btn-primary btn-sm min-h-[40px] flex-1 flex items-center justify-center gap-2 font-bold shadow-warm-xs bg-[#EA717B] hover:bg-[#d65f69] text-white"
                          >
                            <span>{t('howToApply.ctaPortal', 'Apply on Official Portal')}</span>
                            <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                          </button>
                        ) : null}

                        <Link
                          to={`/schemes/${rec.scheme_id}?amount=${requestedAmount}`}
                          className={`btn-secondary btn-sm min-h-[40px] flex items-center justify-center gap-2 font-semibold bg-[#FFD0CA] hover:bg-[#fca59d] text-[#4A2525] border-transparent ${
                            officialUrl ? 'sm:flex-initial' : 'flex-1'
                          }`}
                        >
                          <FileText className="w-4 h-4 text-[#4A2525] shrink-0" />
                          <span>{t('schemeCard.viewDetails', 'View Details')}</span>
                        </Link>
                      </div>

                      {/* Priority Tier 2: Compact Cohesive Secondary Controls */}
                      <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                        {rec.is_credit_scheme !== false && (rec.max_loan_amount || rec.interest_rate !== undefined || rec.calculator_applicable !== false) ? (
                          <>
                            <Link
                              to={`/calculator?scheme=${rec.scheme_id}&loan=${rec.max_loan_amount || requestedAmount || 100000}`}
                              className="btn-secondary btn-sm h-8 px-2.5 text-xs text-[#765E59] hover:text-[#EA717B] flex items-center gap-1.5 rounded-lg border-[#E8D8D2] font-semibold bg-white"
                              title="Open Scheme Financial Calculator"
                            >
                              <CalcIcon className="w-3.5 h-3.5 text-[#765E59] shrink-0" />
                              <span>{t('recommendations.calculateEmi', 'Calculate')}</span>
                            </Link>

                            <Link
                              to={`/calculator?tab=health&scheme=${rec.scheme_id}&loan=${rec.max_loan_amount || requestedAmount || 100000}`}
                              className="btn-secondary btn-sm h-8 px-2.5 text-xs text-emerald-800 bg-emerald-50 hover:bg-emerald-100 flex items-center gap-1.5 rounded-lg border-emerald-200 font-bold"
                              title="Assess loan affordability and cashflow fit for this scheme"
                            >
                              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                              <span>{t('recommendations.checkFinancialHealth', 'Check Financial Health')}</span>
                            </Link>
                          </>
                        ) : (
                          <Link
                            to={`/calculator?scheme=${rec.scheme_id}`}
                            className="btn-secondary btn-sm h-8 px-2.5 text-xs text-[#765E59] hover:text-[#EA717B] flex items-center gap-1.5 rounded-lg border-[#E8D8D2] font-medium bg-white"
                            title="View Financial Assistance / Subsidy Guidelines"
                          >
                            <CalcIcon className="w-3.5 h-3.5 text-[#765E59] shrink-0" />
                            <span>{t('recommendations.calculateEmi', 'Calculate')}</span>
                          </Link>
                        )}

                        <Link
                          to={`/channel-partners?scheme_id=${rec.scheme_id}&state=${canonicalProfile?.state || formState || ''}`}
                          className="btn-secondary btn-sm h-8 px-2.5 text-xs text-[#765E59] hover:text-[#EA717B] flex items-center gap-1.5 rounded-lg border-[#E8D8D2] font-semibold bg-white"
                          title="Locate authorized banks and channel partners for this scheme"
                        >
                          <MapPin className="w-3.5 h-3.5 text-[#765E59] shrink-0" />
                          <span>{t('howToApply.ctaPartner', 'Find Nearby Partner')}</span>
                        </Link>

                        <CompareButton
                          schemeId={rec.scheme_id}
                          schemeName={rec.scheme_name}
                          variant="compact"
                          className="btn-secondary btn-sm h-8 px-2.5 text-xs text-[#765E59] hover:text-[#EA717B] rounded-lg border-[#E8D8D2] bg-white"
                        />

                        <SaveSchemeButton
                          schemeId={rec.scheme_id}
                          size="sm"
                          className="btn-secondary btn-sm h-8 px-2.5 text-xs text-[#765E59] hover:text-[#EA717B] rounded-lg border-[#E8D8D2] bg-white"
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* External Portal Safety Dialog */}
      <OfficialPortalModal
        isOpen={!!selectedSchemeForModal}
        onClose={() => setSelectedSchemeForModal(null)}
        schemeName={selectedSchemeForModal?.name || ''}
        officialUrl={selectedSchemeForModal?.url || ''}
      />
    </div>
  );
};
