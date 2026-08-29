import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import { SUPPORTED_LANGUAGES } from '../../i18n';

interface Props {
  onSpeechResult: (text: string) => void;
  lastAssistantResponse?: string;
}

export const VoiceButton: React.FC<Props> = ({ onSpeechResult, lastAssistantResponse }) => {
  const { i18n } = useTranslation();
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [isSupported, setIsSupported] = useState<boolean>(false);

  useEffect(() => {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      setIsSupported(true);
    }
  }, []);

  const handleToggleListen = () => {
    if (!isSupported) return;

    const currentLangObj = SUPPORTED_LANGUAGES.find((l) => l.code === i18n.language) || SUPPORTED_LANGUAGES[0];
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = currentLangObj.bcp47;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      if (transcript) {
        onSpeechResult(transcript);
      }
    };

    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  };

  const handleToggleSpeak = () => {
    if (!('speechSynthesis' in window) || !lastAssistantResponse) return;

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    } else {
      const utterance = new SpeechSynthesisUtterance(lastAssistantResponse);
      utterance.rate = 1.0;
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      setIsSpeaking(true);
      window.speechSynthesis.speak(utterance);
    }
  };

  if (!isSupported) {
    return (
      <button
        disabled
        className="p-2 text-slate-300 bg-slate-100 rounded-xl cursor-not-allowed"
        title="Voice STT unavailable in browser"
      >
        <MicOff className="w-4 h-4" />
      </button>
    );
  }

  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        onClick={handleToggleListen}
        className={`p-2 rounded-xl transition ${
          isListening
            ? 'bg-rose-500 text-white animate-pulse shadow-md'
            : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
        }`}
        title={isListening ? 'Stop Listening...' : 'Speak Question (Hindi/English)'}
      >
        <Mic className="w-4 h-4" />
      </button>

      {lastAssistantResponse && (
        <button
          type="button"
          onClick={handleToggleSpeak}
          className={`p-2 rounded-xl transition ${
            isSpeaking
              ? 'bg-sky-600 text-white animate-pulse shadow-md'
              : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
          }`}
          title={isSpeaking ? 'Stop Reading' : 'Listen Answer'}
        >
          {isSpeaking ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
        </button>
      )}
    </div>
  );
};
