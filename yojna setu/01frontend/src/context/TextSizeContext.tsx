import React, { createContext, useContext, useEffect, useState } from 'react';

export type TextSize = 'small' | 'default' | 'large';

interface TextSizeContextType {
  textSize: TextSize;
  setTextSize: (size: TextSize) => void;
  decreaseText: () => void;
  resetText: () => void;
  increaseText: () => void;
}

const TextSizeContext = createContext<TextSizeContextType | undefined>(undefined);

const STORAGE_KEY = 'yojnasetu_text_size';

export const TextSizeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [textSize, setTextSizeState] = useState<TextSize>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'small' || saved === 'large') {
      return saved;
    }
    return 'default';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-text-size', textSize);
    try {
      localStorage.setItem(STORAGE_KEY, textSize);
    } catch {
      // ignore storage access restrictions
    }
  }, [textSize]);

  const setTextSize = (size: TextSize) => {
    setTextSizeState(size);
  };

  const decreaseText = () => {
    setTextSizeState((curr) => (curr === 'large' ? 'default' : 'small'));
  };

  const resetText = () => {
    setTextSizeState('default');
  };

  const increaseText = () => {
    setTextSizeState((curr) => (curr === 'small' ? 'default' : 'large'));
  };

  return (
    <TextSizeContext.Provider
      value={{
        textSize,
        setTextSize,
        decreaseText,
        resetText,
        increaseText,
      }}
    >
      {children}
    </TextSizeContext.Provider>
  );
};

export const useTextSize = (): TextSizeContextType => {
  const context = useContext(TextSizeContext);
  if (!context) {
    throw new Error('useTextSize must be used within a TextSizeProvider');
  }
  return context;
};
