import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Sparkles, MessageSquare, Bot } from 'lucide-react';
import { ChatWindow } from './ChatWindow';
import { useComparison } from '../../context/ComparisonContext';

export const AICopilot: React.FC = () => {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [isMinimized, setIsMinimized] = useState<boolean>(false);

  const location = useLocation();
  const { selectedSchemeIds } = useComparison();
  const hasComparisonDock = selectedSchemeIds && selectedSchemeIds.length > 0;

  // Extract scheme_id if on /schemes/:schemeId
  const schemeMatch = location.pathname.match(/\/schemes\/([^\/]+)/);
  const schemeIdContext = schemeMatch ? schemeMatch[1] : undefined;

  // Extract application_id if on /applications/:id
  const appMatch = location.pathname.match(/\/applications\/([^\/]+)/);
  const applicationIdContext = appMatch ? appMatch[1] : undefined;

  // Automatically minimize expanded chatbot when route changes
  const prevPathnameRef = useRef(location.pathname);
  useEffect(() => {
    if (prevPathnameRef.current !== location.pathname) {
      prevPathnameRef.current = location.pathname;
      if (isOpen && !isMinimized) {
        setIsMinimized(true);
        setIsOpen(false);
      }
    }
  }, [location.pathname, isOpen, isMinimized]);

  // Support opening assistant from external homepage prompt clicks
  useEffect(() => {
    const handleOpenExternal = (e: Event) => {
      setIsMinimized(false);
      setIsOpen(true);
    };
    window.addEventListener('open-yojnasetu-ai', handleOpenExternal);
    return () => window.removeEventListener('open-yojnasetu-ai', handleOpenExternal);
  }, []);

  const handleToggle = () => {
    if (isMinimized || !isOpen) {
      setIsMinimized(false);
      setIsOpen(true);
    } else {
      setIsMinimized(true);
      setIsOpen(false);
    }
  };

  return (
    <>
      {/* Floating Action Button: Sleek, compact, accessible, non-intrusive */}
      {(!isOpen || isMinimized) && (
        <button
          onClick={handleToggle}
          className={`fixed ${
            hasComparisonDock ? 'bottom-24 sm:bottom-20' : 'bottom-4 sm:bottom-6'
          } right-4 sm:right-6 bg-[#4A2525] hover:bg-[#3B2522] text-[#FFFBF0] p-2.5 sm:px-4 sm:py-2.5 rounded-full shadow-warm-lg hover:shadow-warm-xl border border-[#E8D8D2]/40 transition-all duration-200 z-40 group flex items-center justify-center gap-2 hover:-translate-y-0.5`}
          aria-label={t('copilot.openAssistantTitle', 'Open YojnaSetu AI Assistant')}
          title={t('copilot.openAssistantTitle', 'Open YojnaSetu AI Assistant')}
        >
          <div className="relative flex items-center justify-center">
            <Bot className="w-5 h-5 text-[#F7AE56] group-hover:scale-110 transition-transform" aria-hidden="true" />
            <span className="absolute -top-0.5 -right-0.5 bg-[#EA717B] w-2 h-2 rounded-full ring-2 ring-[#4A2525] animate-pulse" />
          </div>
          <span className="hidden sm:inline text-xs font-bold tracking-tight text-[#FFFBF0]">
            {t('copilot.askButton', 'Ask YojnaSetu')}
          </span>
        </button>
      )}

      {/* Expanded Chat Drawer Panel */}
      {isOpen && !isMinimized && (
        <ChatWindow
          onClose={() => setIsOpen(false)}
          onMinimize={() => setIsMinimized(true)}
          currentRoute={location.pathname}
          schemeIdContext={schemeIdContext}
          applicationIdContext={applicationIdContext}
        />
      )}
    </>
  );
};
