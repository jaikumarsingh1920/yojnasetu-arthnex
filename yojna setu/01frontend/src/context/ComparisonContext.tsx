import React, { createContext, useContext, useState, useEffect } from 'react';

interface ComparisonContextType {
  selectedSchemeIds: string[];
  schemeNames: Record<string, string>;
  addSchemeToCompare: (schemeId: string, schemeName?: string) => boolean;
  removeSchemeFromCompare: (schemeId: string) => void;
  clearComparison: () => void;
  isInComparison: (schemeId: string) => boolean;
  toggleComparison: (schemeId: string, schemeName?: string) => void;
  warningMessage: string | null;
  setWarningMessage: (msg: string | null) => void;
}

const STORAGE_KEY = 'yojnasetu_compare_ids';
const NAMES_STORAGE_KEY = 'yojnasetu_compare_names';

const ComparisonContext = createContext<ComparisonContextType | undefined>(undefined);

export const ComparisonProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedSchemeIds, setSelectedSchemeIds] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          return parsed.slice(0, 4);
        }
      }
    } catch {
      // Fallback
    }
    return [];
  });

  const [schemeNames, setSchemeNames] = useState<Record<string, string>>(() => {
    try {
      const saved = localStorage.getItem(NAMES_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (typeof parsed === 'object' && parsed !== null) {
          return parsed;
        }
      }
    } catch {
      // Fallback
    }
    return {};
  });

  const [warningMessage, setWarningMessage] = useState<string | null>(null);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(selectedSchemeIds));
    } catch {
      // Storage quota / error ignore
    }
  }, [selectedSchemeIds]);

  useEffect(() => {
    try {
      localStorage.setItem(NAMES_STORAGE_KEY, JSON.stringify(schemeNames));
    } catch {
      // Storage quota / error ignore
    }
  }, [schemeNames]);

  const addSchemeToCompare = (schemeId: string, schemeName?: string): boolean => {
    if (!schemeId) return false;
    if (selectedSchemeIds.includes(schemeId)) {
      if (schemeName) {
        setSchemeNames((prev) => ({ ...prev, [schemeId]: schemeName }));
      }
      return true; // Already added
    }
    if (selectedSchemeIds.length >= 4) {
      setWarningMessage('You can compare a maximum of 4 schemes at a time.');
      setTimeout(() => setWarningMessage(null), 4000);
      return false;
    }
    setSelectedSchemeIds((prev) => [...prev, schemeId]);
    if (schemeName) {
      setSchemeNames((prev) => ({ ...prev, [schemeId]: schemeName }));
    }
    setWarningMessage(null);
    return true;
  };

  const removeSchemeFromCompare = (schemeId: string) => {
    setSelectedSchemeIds((prev) => prev.filter((id) => id !== schemeId));
    setSchemeNames((prev) => {
      const copy = { ...prev };
      delete copy[schemeId];
      return copy;
    });
    setWarningMessage(null);
  };

  const clearComparison = () => {
    setSelectedSchemeIds([]);
    setSchemeNames({});
    setWarningMessage(null);
  };

  const isInComparison = (schemeId: string): boolean => {
    return selectedSchemeIds.includes(schemeId);
  };

  const toggleComparison = (schemeId: string, schemeName?: string) => {
    if (isInComparison(schemeId)) {
      removeSchemeFromCompare(schemeId);
    } else {
      addSchemeToCompare(schemeId, schemeName);
    }
  };

  return (
    <ComparisonContext.Provider
      value={{
        selectedSchemeIds,
        schemeNames,
        addSchemeToCompare,
        removeSchemeFromCompare,
        clearComparison,
        isInComparison,
        toggleComparison,
        warningMessage,
        setWarningMessage,
      }}
    >
      {children}
    </ComparisonContext.Provider>
  );
};

export const useComparison = (): ComparisonContextType => {
  const context = useContext(ComparisonContext);
  if (!context) {
    throw new Error('useComparison must be used within a ComparisonProvider');
  }
  return context;
};
