import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bot, User, ArrowRight, ShieldCheck, Copy, Check } from 'lucide-react';
import { SourceCitation, AICopilotAction, RichCard } from '../../types';
import { SourceCitationCard } from './SourceCitationCard';
import { RichCardRenderer } from './RichCardRenderer';
import { SafeChatMarkdown } from './SafeChatMarkdown';

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
  onNavigate?: () => void;
}

export const ChatMessage: React.FC<Props> = ({ message, onSelectSuggestion, onNavigate }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [copied, setCopied] = useState<boolean>(false);
  const isAssistant = message.sender === 'assistant';

  const handleActionClick = (action: AICopilotAction) => {
    onNavigate?.();
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
            ? 'bg-[#4A2525] text-[#F7AE56] shadow-warm-xs border border-[#FFD0CA]/40'
            : 'bg-[#EA717B] text-white shadow-warm-xs'
        }`}
      >
        {isAssistant ? <Bot className="w-4 h-4" aria-hidden="true" /> : <User className="w-4 h-4" aria-hidden="true" />}
      </div>

      {/* Message Bubble & Content */}
      <div className={`space-y-2 max-w-[88%] min-w-0 ${isAssistant ? '' : 'text-right'}`}>
        <div
          className={`p-3.5 rounded-2xl shadow-warm-sm leading-relaxed space-y-2 relative group ${
            isAssistant
              ? 'bg-white border border-[#E8D8D2] text-[#3B2522] rounded-tl-xs'
              : 'bg-[#4A2525] text-[#FFFBF0] rounded-tr-xs'
          }`}
        >
          {/* Copy Button */}
          {isAssistant && (
            <button
              onClick={handleCopyText}
              className="absolute top-2 right-2 p-1 text-[#765E59] hover:text-[#3B2522] bg-[#FFF4EC] hover:bg-[#FFD0CA] rounded transition opacity-0 group-hover:opacity-100"
              title={t('copilot.copyAnswer', 'Copy Answer')}
            >
              {copied ? <Check className="w-3 h-3 text-emerald-600" aria-hidden="true" /> : <Copy className="w-3 h-3" aria-hidden="true" />}
            </button>
          )}

          {/* Humanized Verified Badge */}
          {isAssistant && message.deterministicUsed && (
            <div className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded border border-emerald-200">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" /> {t('copilot.verifiedBadge', 'Verified Government Information')}
            </div>
          )}

          {/* Formatted Text */}
          {isAssistant ? (
            <SafeChatMarkdown content={message.text} />
          ) : (
            <div className="whitespace-pre-wrap text-[11px] sm:text-xs font-sans leading-relaxed break-words text-[#FFFBF0]">
              {message.text}
            </div>
          )}

          {/* Rich Response Cards */}
          {isAssistant && message.richCards && message.richCards.length > 0 && (
            <div className="space-y-2 pt-1">
              {message.richCards.map((rc, idx) => (
                <RichCardRenderer key={idx} card={rc} onNavigate={onNavigate} />
              ))}
            </div>
          )}

          {/* Action Buttons */}
          {isAssistant && message.actions && message.actions.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-1 border-t border-[#E8D8D2]">
              {message.actions.map((act, idx) => (
                <button
                  key={idx}
                  onClick={() => handleActionClick(act)}
                  className="bg-[#EA717B] hover:bg-[#D65D67] text-white font-bold text-[10px] px-3 py-1.5 rounded-lg shadow-warm-xs transition flex items-center gap-1"
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
            <p className="text-[10px] font-bold text-[#765E59] uppercase tracking-wider">{t('copilot.verifiedSources', 'Verified Sources')}</p>
            <div className="grid grid-cols-1 gap-1.5">
              {message.citations.map((cite, idx) => (
                <SourceCitationCard key={idx} citation={cite} onNavigate={onNavigate} />
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
                className="bg-[#FFF4EC] hover:bg-[#FFD0CA] text-[#4A2525] text-[10px] font-bold px-2.5 py-1 rounded-full border border-[#E8D8D2] transition text-left"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        <span className="text-[9px] text-[#765E59] block font-mono">
          {message.timestamp}
        </span>
      </div>
    </div>
  );
};
