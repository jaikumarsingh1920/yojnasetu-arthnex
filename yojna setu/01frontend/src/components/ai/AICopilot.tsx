import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bot, Sparkles } from 'lucide-react';
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

  // Automatically minimize the expanded chatbot when route changes (e.g. navigating to scheme details)
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
      {/* Floating Action Button when closed or minimized */}
      {(!isOpen || isMinimized) && (
        <button
          onClick={handleToggle}
          className={`fixed ${
            hasComparisonDock ? 'bottom-28 sm:bottom-24' : 'bottom-3 sm:bottom-5'
          } right-3 sm:right-5 bg-gradient-to-r from-gov-navy via-sky-900 to-slate-900 text-white min-w-[48px] min-h-[48px] p-3 sm:p-3.5 rounded-full shadow-2xl hover:scale-105 border-2 border-sky-400/50 transition-all z-40 group flex items-center justify-center gap-2`}
          aria-label={t('copilot.openAssistantTitle', 'Open YojnaSetu AI Assistant')}
          title={t('copilot.openAssistantTitle', 'Open YojnaSetu AI Assistant')}
        >
          <div className="relative">
            <Bot className="w-5 h-5 sm:w-6 sm:h-6 text-sky-300 group-hover:rotate-6 transition" />
            <span className="absolute -top-1 -right-1 bg-emerald-400 w-2 h-2 sm:w-2.5 sm:h-2.5 rounded-full border-2 border-slate-900 animate-pulse" />
          </div>
          <span className="hidden sm:inline text-xs font-bold pr-1 tracking-tight">YojnaSetu AI</span>
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
