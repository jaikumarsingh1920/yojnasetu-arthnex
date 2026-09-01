import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ShieldAlert, RefreshCw } from 'lucide-react';
import i18n from '../i18n';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Unhandled React Error Boundary Exception:', error, errorInfo);
  }

  public handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
          <div className="bg-slate-800 text-white rounded-2xl max-w-lg w-full p-8 border border-slate-700 shadow-2xl space-y-6 text-center">
            <div className="w-16 h-16 bg-rose-500/20 text-rose-400 rounded-full flex items-center justify-center mx-auto border border-rose-500/30">
              <ShieldAlert className="w-8 h-8" />
            </div>

            <div className="space-y-2">
              <h2 className="text-2xl font-black tracking-tight text-white">{i18n.t('errors.somethingWentWrong', 'Something Went Wrong')}</h2>
              <p className="text-xs text-slate-300 leading-relaxed">
                {i18n.t('errors.unexpectedRenderError', 'An unexpected application error occurred while rendering this interface.')}
              </p>
            </div>

            {this.state.error && (
              <div className="bg-slate-950 p-4 rounded-xl text-left border border-slate-800 font-mono text-[11px] text-rose-300 overflow-x-auto max-h-32">
                {this.state.error.toString()}
              </div>
            )}

            <button
              onClick={this.handleReload}
              className="w-full bg-sky-600 hover:bg-sky-500 text-white font-extrabold text-sm py-3 px-6 rounded-xl shadow-lg transition flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-4 h-4" /> {i18n.t('errors.reloadApp', 'Reload Application')}
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
