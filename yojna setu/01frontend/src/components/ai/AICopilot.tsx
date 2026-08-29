import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Bot, Sparkles } from 'lucide-react';
import { ChatWindow } from './ChatWindow';

export const AICopilot: React.FC = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [isMinimized, setIsMinimized] = useState<boolean>(false);

  const location = useLocation();

  // Extract scheme_id if on /schemes/:schemeId
  const schemeMatch = location.pathname.match(/\/schemes\/([^\/]+)/);
  const schemeIdContext = schemeMatch ? schemeMatch[1] : undefined;

  // Extract application_id if on /applications/:id
  const appMatch = location.pathname.match(/\/applications\/([^\/]+)/);
  const applicationIdContext = appMatch ? appMatch[1] : undefined;

  const handleToggle = () => {
    if (isMinimized) {
      setIsMinimized(false);
      setIsOpen(true);
    } else {
      setIsOpen(prev => !prev);
    }
  };

  return (
    <>
      {/* Floating Action Button when closed or minimized */}
      {(!isOpen || isMinimized) && (
        <button
          onClick={handleToggle}
          className="fixed bottom-5 right-5 bg-gradient-to-r from-gov-navy via-sky-900 to-slate-900 text-white p-3.5 rounded-full shadow-2xl hover:scale-105 border-2 border-sky-400/50 transition z-50 group flex items-center gap-2"
          title="Open YojnaSetu AI Assistant"
        >
          <div className="relative">
            <Bot className="w-6 h-6 text-sky-300 group-hover:rotate-6 transition" />
            <span className="absolute -top-1 -right-1 bg-emerald-400 w-2.5 h-2.5 rounded-full border-2 border-slate-900 animate-pulse" />
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
