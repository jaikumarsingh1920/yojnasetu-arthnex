import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, User, ArrowRight, ShieldCheck, Copy, Check } from 'lucide-react';
import { SourceCitation, AICopilotAction, RichCard } from '../../types';
import { SourceCitationCard } from './SourceCitationCard';
import { RichCardRenderer } from './RichCardRenderer';

export interface ChatMessageItem {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  intent?: string;
  responseMode?: string;
  citations?: SourceCitation[];
  actions?: AICopilotAction[];
  richCards?: RichCard[];
  suggestedQuestions?: string[];
  deterministicUsed?: boolean;
}

interface Props {
  message: ChatMessageItem;
  onSelectSuggestion?: (question: string) => void;
}

export const ChatMessage: React.FC<Props> = ({ message, onSelectSuggestion }) => {
  const navigate = useNavigate();
  const [copied, setCopied] = useState<boolean>(false);
  const isAssistant = message.sender === 'assistant';

  const handleActionClick = (action: AICopilotAction) => {
    if (action.target_url) {
      navigate(action.target_url);
    }
  };

  const handleCopyText = () => {
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex gap-3 text-xs ${isAssistant ? 'items-start' : 'items-end flex-row-reverse'}`}>
      {/* Avatar */}
      <div
        className={`w-7 h-7 rounded-xl flex items-center justify-center shrink-0 font-bold ${
          isAssistant
            ? 'bg-gradient-to-tr from-gov-navy to-sky-900 text-white shadow-xs border border-sky-500'
            : 'bg-slate-900 text-white'
        }`}
      >
        {isAssistant ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
      </div>

      {/* Message Bubble & Content */}
      <div className={`space-y-2 max-w-[85%] ${isAssistant ? '' : 'text-right'}`}>
        <div
          className={`p-3.5 rounded-2xl shadow-xs leading-relaxed space-y-2 relative group ${
            isAssistant
              ? 'bg-white border border-slate-200 text-slate-900 rounded-tl-xs'
              : 'bg-gradient-to-r from-gov-blue to-slate-900 text-white rounded-tr-xs'
          }`}
        >
          {/* Copy Button */}
          {isAssistant && (
            <button
              onClick={handleCopyText}
              className="absolute top-2 right-2 p-1 text-slate-400 hover:text-slate-700 bg-slate-100/80 hover:bg-slate-200 rounded transition opacity-0 group-hover:opacity-100"
              title="Copy Answer"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
            </button>
          )}

          {/* Humanized Verified Badge */}
          {isAssistant && message.deterministicUsed && (
            <div className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded border border-emerald-200">
              <ShieldCheck className="w-3 h-3 text-emerald-600" /> Verified Government Information
            </div>
          )}

          {/* Formatted Text */}
          <div className="whitespace-pre-wrap text-[11px] sm:text-xs font-sans">
            {message.text}
          </div>

          {/* Rich Response Cards */}
          {isAssistant && message.richCards && message.richCards.length > 0 && (
            <div className="space-y-2 pt-1">
              {message.richCards.map((rc, idx) => (
                <RichCardRenderer key={idx} card={rc} />
              ))}
            </div>
          )}

          {/* Action Buttons */}
          {isAssistant && message.actions && message.actions.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-1 border-t border-slate-100">
              {message.actions.map((act, idx) => (
                <button
                  key={idx}
                  onClick={() => handleActionClick(act)}
                  className="bg-gov-blue hover:bg-gov-navy text-white font-bold text-[10px] px-3 py-1.5 rounded-lg shadow-xs transition flex items-center gap-1"
                >
                  {act.label} <ArrowRight className="w-3 h-3" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Source Citations */}
        {isAssistant && message.citations && message.citations.length > 0 && (
          <div className="space-y-1.5 pt-1">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Verified Sources</p>
            <div className="grid grid-cols-1 gap-1.5">
              {message.citations.map((cite, idx) => (
                <SourceCitationCard key={idx} citation={cite} />
              ))}
            </div>
          </div>
        )}

        {/* Suggested Questions */}
        {isAssistant && message.suggestedQuestions && message.suggestedQuestions.length > 0 && onSelectSuggestion && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {message.suggestedQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => onSelectSuggestion(q)}
                className="bg-sky-50 hover:bg-sky-100 text-sky-800 text-[10px] font-bold px-2.5 py-1 rounded-full border border-sky-200 transition text-left"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        <span className="text-[9px] text-slate-400 block font-mono">
          {message.timestamp}
        </span>
      </div>
    </div>
  );
};
