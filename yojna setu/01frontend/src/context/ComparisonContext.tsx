import React, { createContext, useContext, useState, useEffect } from 'react';

interface ComparisonContextType {
  selectedSchemeIds: string[];
  addSchemeToCompare: (schemeId: string) => boolean;
  removeSchemeFromCompare: (schemeId: string) => void;
  clearComparison: () => void;
  isInComparison: (schemeId: string) => boolean;
  toggleComparison: (schemeId: string) => void;
  warningMessage: string | null;
  setWarningMessage: (msg: string | null) => void;
}

const STORAGE_KEY = 'yojnasetu_compare_ids';

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

  const [warningMessage, setWarningMessage] = useState<string | null>(null);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(selectedSchemeIds));
    } catch {
      // Storage quota / error ignore
    }
  }, [selectedSchemeIds]);

  const addSchemeToCompare = (schemeId: string): boolean => {
    if (!schemeId) return false;
    if (selectedSchemeIds.includes(schemeId)) {
      return true; // Already added
    }
    if (selectedSchemeIds.length >= 4) {
      setWarningMessage('You can compare a maximum of 4 schemes at a time.');
      setTimeout(() => setWarningMessage(null), 4000);
      return false;
    }
    setSelectedSchemeIds((prev) => [...prev, schemeId]);
    setWarningMessage(null);
    return true;
  };

  const removeSchemeFromCompare = (schemeId: string) => {
    setSelectedSchemeIds((prev) => prev.filter((id) => id !== schemeId));
    setWarningMessage(null);
  };

  const clearComparison = () => {
    setSelectedSchemeIds([]);
    setWarningMessage(null);
  };

  const isInComparison = (schemeId: string): boolean => {
    return selectedSchemeIds.includes(schemeId);
  };

  const toggleComparison = (schemeId: string) => {
    if (isInComparison(schemeId)) {
      removeSchemeFromCompare(schemeId);
    } else {
      addSchemeToCompare(schemeId);
    }
  };

  return (
    <ComparisonContext.Provider
      value={{
        selectedSchemeIds,
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
