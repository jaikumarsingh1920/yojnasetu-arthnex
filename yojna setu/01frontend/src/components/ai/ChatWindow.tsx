import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Bot, Send, Trash2, Minus, X, Sparkles, Square } from 'lucide-react';
import { aiApi } from '../../api/aiApi';
import { ChatMessage, ChatMessageItem } from './ChatMessage';
import { VoiceButton } from './VoiceButton';

interface Props {
  onClose: () => void;
  onMinimize: () => void;
  currentRoute: string;
  schemeIdContext?: string;
  applicationIdContext?: string;
}

export const ChatWindow: React.FC<Props> = ({
  onClose,
  onMinimize,
  currentRoute,
  schemeIdContext,
  applicationIdContext,
}) => {
  const { t, i18n } = useTranslation();
  const [messages, setMessages] = useState<ChatMessageItem[]>(() => [
    {
      id: 'welcome-msg',
      sender: 'assistant',
      text: schemeIdContext
        ? t('copilot.schemeWelcome', 'Namaste! 👋\nI am with you on this scheme page. Ask me about interest rates, loan limits, eligibility requirements, or documents for this scheme.')
        : t('copilot.defaultWelcome', 'Namaste! 👋\nI can help you discover government schemes, check eligibility guidelines, understand required documents, calculate loan EMIs, and route to official portals.\n\nAsk any question — type or speak.'),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      suggestedQuestions: schemeIdContext
        ? [
            t('copilot.amIEligible', '💡 Am I eligible for this scheme?'),
            t('copilot.whatDocsNeed', '📄 What documents do I need?'),
            t('copilot.whatInterestBenefit', '💰 What is the interest rate / benefit?'),
            t('copilot.howToApplyPortal', '🌐 How do I apply on the official portal?')
          ]
        : [
            t('copilot.startBusiness', '💡 I want to start a small business'),
            t('copilot.whichSchemesQualify', '🔎 Which schemes might I qualify for?'),
            t('copilot.whatDocsNeed', '📄 What documents do I need?'),
            t('copilot.need2LakhLoan', '💰 I need a ₹2 lakh loan'),
            t('copilot.speakHindi', '🗣️ Speak to me in Hindi')
          ]
    }
  ]);

  const [inputQuery, setInputQuery] = useState<string>('');
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-collapse on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        onMinimize();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [onMinimize]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || isTyping) return;

    const userMsg: ChatMessageItem = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMsg]);
    setInputQuery('');
    setIsTyping(true);

    try {
      const res = await aiApi.chatWithAI({
        message: query,
        session_id: sessionId || undefined,
        scheme_id: schemeIdContext,
        application_id: applicationIdContext,
        page_context: { current_route: currentRoute },
        preferred_language: i18n.language
      });

      if (res.session_id) setSessionId(res.session_id);

      const assistantMsg: ChatMessageItem = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: res.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        intent: res.intent,
        responseMode: res.response_mode,
        citations: res.citations,
        actions: res.actions,
        richCards: res.rich_cards,
        suggestedQuestions: res.suggested_questions,
        deterministicUsed: res.deterministic_used,
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error('YojnaSetu AI chat error:', err);
      const errorMsg: ChatMessageItem = {
        id: `error-${Date.now()}`,
        sender: 'assistant',
        text: t('copilot.chatError', 'I encountered an issue processing your request. Please check your internet connection or try again.'),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleStopGeneration = () => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
    }
    setIsTyping(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        sender: 'assistant',
        text: t('copilot.conversationCleared', 'Conversation cleared. How can I assist you with government schemes today?'),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        suggestedQuestions: [
          t('copilot.startBusiness', '💡 I want to start a small business'),
          t('copilot.whichSchemesQualify', '🔎 Which schemes might I qualify for?'),
          t('copilot.whatDocsNeed', '📄 What documents do I need?'),
          t('copilot.need2LakhLoan', '💰 I need a ₹2 lakh loan')
        ]
      }
    ]);
  };

  const lastAssistantMsgText = messages
    .filter(m => m.sender === 'assistant')
    .slice(-1)[0]?.text;

  return (
    <div ref={containerRef} className="fixed bottom-3 right-3 sm:bottom-4 sm:right-4 w-[min(420px,calc(100vw-1.5rem))] h-[min(600px,calc(100dvh-1.5rem))] bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-slate-300 flex flex-col z-50 overflow-hidden text-slate-900 animate-in fade-in slide-in-from-bottom-4 duration-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-gov-navy via-sky-900 to-slate-900 text-white p-3.5 flex justify-between items-center border-b border-sky-800 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-sky-500/20 rounded-lg flex items-center justify-center border border-sky-400/40">
            <Bot className="w-4 h-4 text-sky-300" />
          </div>
          <div>
            <h3 className="font-extrabold text-xs leading-tight">YojnaSetu AI</h3>
            <span className="text-[10px] text-sky-200 block">
              {t('copilot.assistantSubtitle', 'Your guide to government schemes')}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleClearChat}
            className="p-1 text-slate-300 hover:text-white hover:bg-sky-800 rounded transition"
            title={t('copilot.clearChat', 'Clear Conversation')}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onMinimize}
            className="p-1 text-slate-300 hover:text-white hover:bg-sky-800 rounded transition"
            title={t('copilot.minimize', 'Minimize')}
          >
            <Minus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onClose}
            className="p-1 text-slate-300 hover:text-white hover:bg-rose-900 rounded transition"
            title={t('common.close', 'Close')}
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 p-3.5 overflow-y-auto space-y-4 bg-slate-50/50">
        {messages.map(msg => (
          <ChatMessage
            key={msg.id}
            message={msg}
            onSelectSuggestion={(q) => handleSendMessage(q)}
          />
        ))}

        {isTyping && (
          <div className="flex items-center justify-between gap-2 text-xs text-sky-800 font-bold bg-sky-50 p-2.5 rounded-xl border border-sky-200 w-full">
            <div className="flex items-center gap-2">
              <div className="w-3.5 h-3.5 border-2 border-sky-600 border-t-transparent rounded-full animate-spin" />
              <span>{t('copilot.searching', 'Checking verified government scheme information...')}</span>
            </div>
            <button
              onClick={handleStopGeneration}
              className="p-1 text-slate-600 hover:text-rose-700 bg-white rounded border border-slate-300 text-[10px] flex items-center gap-1"
            >
              <Square className="w-2.5 h-2.5 fill-current" /> {t('copilot.stop', 'Stop')}
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-3 bg-white border-t border-slate-200 shrink-0 space-y-2">
        <div className="flex items-center gap-2">
          <VoiceButton
            onSpeechResult={(transcript) => {
              setInputQuery(transcript);
              handleSendMessage(transcript);
            }}
            lastAssistantResponse={lastAssistantMsgText}
          />

          <input
            ref={inputRef}
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('copilot.placeholder', 'Ask about schemes, eligibility, loan EMIs, or documents...')}
            className="flex-1 px-3 py-2 text-xs border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-sky-500 bg-white"
          />

          <button
            onClick={() => handleSendMessage()}
            disabled={!inputQuery.trim() || isTyping}
            className="p-2.5 bg-gov-blue hover:bg-gov-navy disabled:bg-slate-300 text-white rounded-xl shadow-xs transition"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
