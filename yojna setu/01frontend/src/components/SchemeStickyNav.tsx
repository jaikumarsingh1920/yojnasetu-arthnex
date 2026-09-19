import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Sparkles,
  ShieldCheck,
  Building2,
  FileText,
  Calculator as CalcIcon,
  Bot,
  Info,
  Layers
} from 'lucide-react';

interface SchemeStickyNavProps {
  hasCalculator?: boolean;
  hasRules?: boolean;
  hasDocs?: boolean;
}

export const SchemeStickyNav: React.FC<SchemeStickyNavProps> = ({
  hasCalculator = true,
  hasRules = true,
  hasDocs = true,
}) => {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] = useState<string>('glance');

  const navItems = [
    { id: 'glance', label: 'At a Glance', icon: Sparkles },
    ...(hasRules ? [{ id: 'eligibility', label: 'Who Can Apply', icon: ShieldCheck }] : []),
    { id: 'how-to-apply', label: 'How to Apply', icon: Building2 },
    ...(hasDocs ? [{ id: 'documents', label: 'Documents Needed', icon: FileText }] : []),
    ...(hasCalculator ? [{ id: 'calculator', label: 'Calculator', icon: CalcIcon }] : []),
    { id: 'ai-guidance', label: 'AI Guidance', icon: Bot },
    { id: 'official-source', label: 'Official Source', icon: Info },
  ];

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 140;
      for (let i = navItems.length - 1; i >= 0; i--) {
        const item = navItems[i];
        const el = document.getElementById(item.id);
        if (el && el.offsetTop <= scrollPosition) {
          setActiveSection(item.id);
          break;
        }
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [navItems]);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      const offset = 90;
      const bodyRect = document.body.getBoundingClientRect().top;
      const elementRect = el.getBoundingClientRect().top;
      const elementPosition = elementRect - bodyRect;
      const offsetPosition = elementPosition - offset;

      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth',
      });
      setActiveSection(id);
    }
  };

  return (
    <nav
      aria-label="Scheme Section Navigation"
      className="sticky top-16 z-20 bg-[#FFFBF0]/95 backdrop-blur-md border border-[#E8D8D2] rounded-2xl shadow-warm-xs px-2 sm:px-4 py-2 transition-all duration-200"
    >
      <div className="flex items-center gap-1 sm:gap-2 overflow-x-auto no-scrollbar scroll-smooth">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;
          return (
            <button
              key={item.id}
              onClick={() => scrollToSection(item.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all duration-150 cursor-pointer shrink-0 ${
                isActive
                  ? 'bg-[#EA717B] text-white shadow-warm-xs'
                  : 'text-[#765E59] hover:text-[#3B2522] hover:bg-[#FFD0CA]/40'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-[#F7AE56]' : 'text-[#765E59]'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
