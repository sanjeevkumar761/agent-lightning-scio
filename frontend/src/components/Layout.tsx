import { ReactNode } from "react";
import { BarChart3, FileText, Zap, ExternalLink } from "lucide-react";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-lg bg-white/70 border-b border-slate-200/50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Agent Lightning
              </h1>
              <p className="text-xs text-slate-500">Automatic Prompt Optimization</p>
            </div>
          </div>
          <nav className="flex items-center gap-1">
            <a 
              href="/" 
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-slate-700 hover:bg-indigo-50 hover:text-indigo-600 transition-all duration-200"
            >
              <BarChart3 className="w-4 h-4" />
              Dashboard
            </a>
            <a 
              href="/log" 
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-slate-700 hover:bg-indigo-50 hover:text-indigo-600 transition-all duration-200"
            >
              <FileText className="w-4 h-4" />
              Raw Log
            </a>
            <a 
              href="https://microsoft.github.io/agent-lightning/stable/algorithm-zoo/apo/" 
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-all duration-200"
            >
              Docs
              <ExternalLink className="w-3 h-3" />
            </a>
          </nav>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto py-8 px-6">
        {children}
      </main>
      
      {/* Footer */}
      <footer className="border-t border-slate-200/50 bg-white/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between text-sm text-slate-500">
          <span>Agent Lightning • Automatic Prompt Optimization</span>
          <a 
            href="https://github.com/microsoft/agent-lightning" 
            target="_blank" 
            rel="noopener noreferrer"
            className="hover:text-indigo-600 transition-colors"
          >
            GitHub
          </a>
        </div>
      </footer>
    </div>
  );
}
