import { useEffect, useState, useRef } from "react";
import Layout from "../components/Layout";
import { FileText, Terminal, RefreshCw, Download, Search, Filter } from "lucide-react";
import { fetchLog } from "../lib/api";

interface ParsedLogEntry {
  timestamp?: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  message: string;
  raw: string;
}

function parseLogLine(line: string): ParsedLogEntry {
  // Try to parse structured log format: [timestamp] LEVEL message
  const match = line.match(/^\[?(\d{2}\/\d{2}\/\d{2}\s+\d{2}:\d{2}:\d{2})?\]?\s*(INFO|WARNING|ERROR|DEBUG)?\s*(.*)$/i);
  
  let level: ParsedLogEntry['level'] = 'INFO';
  if (line.includes('ERROR') || line.includes('error')) level = 'ERROR';
  else if (line.includes('WARNING') || line.includes('warn')) level = 'WARNING';
  else if (line.includes('DEBUG')) level = 'DEBUG';
  
  return {
    timestamp: match?.[1],
    level,
    message: match?.[3] || line,
    raw: line
  };
}

function LogEntry({ entry, highlight }: { entry: ParsedLogEntry; highlight?: string }) {
  const levelColors = {
    INFO: 'text-blue-400',
    WARNING: 'text-amber-400',
    ERROR: 'text-red-400',
    DEBUG: 'text-slate-500'
  };
  
  const levelBg = {
    INFO: 'bg-blue-500/20',
    WARNING: 'bg-amber-500/20',
    ERROR: 'bg-red-500/20',
    DEBUG: 'bg-slate-500/20'
  };
  
  // Highlight important keywords
  let message = entry.message;
  const importantPatterns = [
    { pattern: /\[Round \d+.*?\]/g, class: 'text-purple-400 font-semibold' },
    { pattern: /Prompt v\d+/g, class: 'text-emerald-400 font-semibold' },
    { pattern: /average is [\d.]+/g, class: 'text-cyan-400 font-semibold' },
    { pattern: /Best prompt updated/g, class: 'text-amber-300 font-bold' },
    { pattern: /New prompt template created/g, class: 'text-green-400' },
    { pattern: /Evaluated \d+ rollouts/g, class: 'text-blue-300' },
    { pattern: /score: [\d.]+/g, class: 'text-cyan-300' },
  ];
  
  // Build highlighted message
  let highlightedMessage = message;
  if (highlight) {
    const regex = new RegExp(`(${highlight})`, 'gi');
    highlightedMessage = message.replace(regex, '<mark class="bg-yellow-500/50 text-yellow-200 px-0.5 rounded">$1</mark>');
  }
  
  return (
    <div className={`flex gap-3 py-1.5 px-3 hover:bg-white/5 rounded ${entry.level === 'ERROR' ? 'bg-red-500/10' : ''}`}>
      {entry.timestamp && (
        <span className="text-slate-500 text-xs font-mono shrink-0 w-20">
          {entry.timestamp.split(' ')[1]}
        </span>
      )}
      <span className={`text-xs font-mono shrink-0 w-16 ${levelColors[entry.level]}`}>
        <span className={`px-1.5 py-0.5 rounded ${levelBg[entry.level]}`}>
          {entry.level}
        </span>
      </span>
      <span 
        className="text-slate-300 text-sm font-mono break-all"
        dangerouslySetInnerHTML={{ __html: highlightedMessage }}
      />
    </div>
  );
}

export default function LogPage() {
  const [log, setLog] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'INFO' | 'WARNING' | 'ERROR'>('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const logContainerRef = useRef<HTMLDivElement>(null);

  const loadLog = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLog();
      setLog(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLog();
    // Auto-refresh every 5 seconds
    const interval = setInterval(loadLog, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [log, autoScroll]);

  const lines = log.split('\n').filter(l => l.trim());
  const entries = lines.map(parseLogLine);
  
  const filteredEntries = entries.filter(entry => {
    if (filter !== 'all' && entry.level !== filter) return false;
    if (search && !entry.raw.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const downloadLog = () => {
    const blob = new Blob([log], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `apo-log-${new Date().toISOString().split('T')[0]}.log`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Extract key events for summary
  const keyEvents = entries.filter(e => 
    e.message.includes('Round') && e.message.includes('Prompt v') ||
    e.message.includes('Best prompt updated') ||
    e.message.includes('average is')
  ).slice(-10);

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-800 mb-2">APO Run Log</h1>
            <p className="text-slate-500">View detailed optimization logs and debug output</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={loadLog}
              className="inline-flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={downloadLog}
              className="inline-flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all"
            >
              <Download className="w-4 h-4" />
              Download
            </button>
          </div>
        </div>

        {/* Key Events Summary */}
        {keyEvents.length > 0 && (
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-4 border border-indigo-200">
            <h3 className="text-sm font-semibold text-indigo-800 mb-3 flex items-center gap-2">
              <Terminal className="w-4 h-4" />
              Recent Key Events
            </h3>
            <div className="space-y-1">
              {keyEvents.map((event, idx) => (
                <div key={idx} className="text-sm text-indigo-700 font-mono">
                  {event.message.substring(0, 100)}{event.message.length > 100 ? '...' : ''}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Log Container */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200/50 overflow-hidden">
          {/* Toolbar */}
          <div className="p-4 border-b border-slate-100 flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-600 to-slate-800 flex items-center justify-center shadow-lg shadow-slate-500/20">
                <Terminal className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-800">Console Output</h3>
                <p className="text-xs text-slate-500">{filteredEntries.length} entries</p>
              </div>
            </div>
            
            <div className="flex-1" />
            
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search logs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent w-64"
              />
            </div>
            
            {/* Filter */}
            <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
              {(['all', 'INFO', 'WARNING', 'ERROR'] as const).map((level) => (
                <button
                  key={level}
                  onClick={() => setFilter(level)}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                    filter === level 
                      ? 'bg-white text-slate-800 shadow-sm' 
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {level === 'all' ? 'All' : level}
                </button>
              ))}
            </div>
            
            {/* Auto-scroll toggle */}
            <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              Auto-scroll
            </label>
          </div>
          
          {/* Log Content */}
          <div 
            ref={logContainerRef}
            className="bg-slate-900 p-4 min-h-[500px] max-h-[700px] overflow-auto font-mono text-sm"
          >
            {loading && !log && (
              <div className="flex items-center gap-2 text-slate-400">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Loading logs...</span>
              </div>
            )}
            {error && (
              <div className="text-red-400">Error loading logs: {error}</div>
            )}
            {!loading && !error && filteredEntries.length === 0 && (
              <div className="flex items-center gap-2 text-slate-500">
                <FileText className="w-4 h-4" />
                <span>No log entries {search || filter !== 'all' ? 'match your filters' : 'yet'}.</span>
              </div>
            )}
            {filteredEntries.map((entry, idx) => (
              <LogEntry key={idx} entry={entry} highlight={search} />
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}
