import React from 'react';
import { AlertCircle, CheckCircle2, AlertTriangle, Info } from 'lucide-react';

interface AlertProps {
  type?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  type = 'info',
  title,
  children,
  className = ''
}) => {
  const styles = {
    info: 'bg-blue-50 border-blue-200 text-blue-900 icon-blue-600',
    success: 'bg-emerald-50 border-emerald-200 text-emerald-900 icon-emerald-600',
    warning: 'bg-amber-50 border-amber-200 text-amber-900 icon-amber-600',
    error: 'bg-rose-50 border-rose-200 text-rose-900 icon-rose-600',
  };

  const icons = {
    info: <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />,
    success: <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />,
    warning: <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />,
    error: <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />,
  };

  return (
    <div className={`p-4 rounded-lg border flex gap-3 ${styles[type]} ${className}`}>
      {icons[type]}
      <div className="text-sm">
        {title && <h5 className="font-bold mb-1">{title}</h5>}
        <div className="leading-relaxed">{children}</div>
      </div>
    </div>
  );
};
