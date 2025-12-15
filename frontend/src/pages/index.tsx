import { useEffect, useState, useCallback } from "react";
import { fetchOptimization, runApo, getRunStatus, type OptimizationData, type PromptMetric } from "../lib/api";
import Layout from "../components/Layout";
import { 
  AlertCircle, RefreshCw, Play, Sparkles, TrendingUp, 
  ChevronDown, ChevronUp, Trophy, Zap, ArrowRight,
  Copy, Check, Target, DollarSign, Percent, Clock,
  Lightbulb, GitBranch, ArrowUpRight, ArrowDownRight,
  CheckCircle2, XCircle, BarChart3
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, LineChart, Line, Legend,
  ScatterChart, Scatter, ZAxis
} from "recharts";

// ============ Copy Button ============
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button onClick={handleCopy} className="p-2 hover:bg-slate-100 rounded-lg transition-colors" title="Copy prompt">
      {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4 text-slate-400" />}
    </button>
  );
}

// ============ Key Results Summary ============
function KeyResultsHero({ data }: { data: OptimizationData }) {
  const story = data.optimization_story;
  if (!story) return null;

  const best = data.metrics.find(m => m.version === story.best_version);
  const seed = data.metrics.find(m => m.is_seed);
  const costSaved = seed && best ? seed.avg_cost - best.avg_cost : 0;
  const costSavedPct = seed && seed.avg_cost > 0 ? Math.abs(costSaved / seed.avg_cost * 100) : 0;

  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 p-8 text-white shadow-2xl">
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 right-0 w-96 h-96 bg-white rounded-full blur-3xl transform translate-x-1/2 -translate-y-1/2" />
      </div>
      
      <div className="relative z-10">
        <div className="flex items-center gap-3 mb-2">
          <Trophy className="w-8 h-8 text-yellow-300" />
          <h2 className="text-2xl font-bold">Optimization Results</h2>
        </div>
        <p className="text-white/70 mb-6">Agent Lightning tested {story.total_versions_tested} prompt variations to find the best one</p>

        {/* Key metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white/10 backdrop-blur rounded-xl p-4">
            <div className="flex items-center gap-2 text-white/60 text-sm mb-1">
              <TrendingUp className="w-4 h-4" />
              Accuracy Gain
            </div>
            <div className="text-3xl font-bold text-green-300">+{story.improvement_pct.toFixed(1)}%</div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-xl p-4">
            <div className="flex items-center gap-2 text-white/60 text-sm mb-1">
              <DollarSign className="w-4 h-4" />
              Token Cost
            </div>
            <div className="text-3xl font-bold text-green-300">{costSaved > 0 ? `-${costSavedPct.toFixed(0)}%` : `+${Math.abs(costSavedPct).toFixed(0)}%`}</div>
            <div className="text-xs text-white/50 mt-1">{story.best_cost} vs {story.seed_cost} tokens</div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-xl p-4">
            <div className="flex items-center gap-2 text-white/60 text-sm mb-1">
              <Target className="w-4 h-4" />
              Best Score
            </div>
            <div className="text-3xl font-bold">{(story.best_score * 100).toFixed(1)}%</div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-xl p-4">
            <div className="flex items-center gap-2 text-white/60 text-sm mb-1">
              <BarChart3 className="w-4 h-4" />
              Winner
            </div>
            <div className="text-3xl font-bold">v{story.best_version}</div>
          </div>
        </div>

        {/* Action item */}
        <div className="bg-white/20 backdrop-blur rounded-xl p-4 flex items-start gap-4">
          <div className="w-10 h-10 rounded-lg bg-yellow-400 flex items-center justify-center flex-shrink-0">
            <Lightbulb className="w-5 h-5 text-yellow-900" />
          </div>
          <div>
            <div className="font-semibold mb-1">Recommended Action</div>
            <p className="text-white/80 text-sm">
              Replace your current prompt with <strong>Version {story.best_version}</strong>. 
              The key improvement: <em>{best?.strategy || 'priority hierarchy and clear constraints'}</em>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============ Run APO Section ============
function RunAPOSection({ onComplete }: { onComplete: () => void }) {
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState<string>("");
  const [selectedExample, setSelectedExample] = useState<string>("room_selector");
  const [examples, setExamples] = useState<Record<string, {name: string, description: string}>>({
    room_selector: { name: "Room Selector", description: "Conference room booking assistant" },
    wealth_onboarding: { name: "Wealth Onboarding", description: "Bank KYC/AML compliance" }
  });

  useEffect(() => {
    // Fetch available examples from API
    fetch("http://localhost:8000/api/examples")
      .then(r => r.json())
      .then(data => setExamples(data))
      .catch(() => {}); // Use defaults on error
  }, []);

  const handleRun = async () => {
    setRunning(true);
    setStatus("Starting APO...");
    try {
      const result = await runApo(selectedExample);
      setStatus("Running optimization...");
      
      // Poll for completion
      const poll = setInterval(async () => {
        const st = await getRunStatus(result.pid);
        if (!st.alive) {
          clearInterval(poll);
          setRunning(false);
          setStatus("Complete!");
          onComplete();
        }
      }, 2000);
    } catch (e: any) {
      setStatus(`Error: ${e.message}`);
      setRunning(false);
    }
  };

  return (
    <div className="bg-gradient-to-r from-violet-600 to-indigo-600 rounded-2xl p-6 text-white">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center">
            <Zap className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold">Run Automatic Prompt Optimization</h3>
            <p className="text-white/70">{running ? status : "Let Agent Lightning find a better prompt for you"}</p>
          </div>
        </div>
        <button
          onClick={handleRun}
          disabled={running}
          className="flex items-center gap-2 px-6 py-3 bg-white text-indigo-600 rounded-xl font-semibold hover:bg-white/90 transition-colors disabled:opacity-50"
        >
          {running ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
          {running ? "Running..." : "Start APO"}
        </button>
      </div>
      
      {/* Example Selection */}
      <div className="mt-4 pt-4 border-t border-white/20">
        <p className="text-sm text-white/60 mb-2">Select Use Case:</p>
        <div className="flex gap-3">
          {Object.entries(examples).map(([key, ex]) => (
            <button
              key={key}
              onClick={() => !running && setSelectedExample(key)}
              disabled={running}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                selectedExample === key
                  ? "bg-white text-indigo-600"
                  : "bg-white/20 text-white hover:bg-white/30"
              } disabled:opacity-50`}
            >
              {ex.name}
            </button>
          ))}
        </div>
        {examples[selectedExample] && (
          <p className="mt-2 text-sm text-white/50">{examples[selectedExample].description}</p>
        )}
      </div>
    </div>
  );
}

// ============ Version Comparison Table ============
function VersionComparisonTable({ metrics, story }: { metrics: PromptMetric[], story: any }) {
  const [expandedVersion, setExpandedVersion] = useState<string | null>(null);
  const bestVersion = story?.best_version;
  
  // Sort by score descending
  const sorted = [...metrics].sort((a, b) => b.average - a.average);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200/50 overflow-hidden">
      <div className="p-6 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-800">All Versions Compared</h3>
            <p className="text-sm text-slate-500">Sorted by performance - click any row to see the prompt</p>
          </div>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-slate-50/80 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <th className="px-6 py-4 text-left">Rank</th>
              <th className="px-6 py-4 text-left">Version</th>
              <th className="px-6 py-4 text-left">Score</th>
              <th className="px-6 py-4 text-left">Success Rate</th>
              <th className="px-6 py-4 text-left">Token Cost</th>
              <th className="px-6 py-4 text-left">Efficiency</th>
              <th className="px-6 py-4 text-left">Strategy</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {sorted.map((m, idx) => {
              const isBest = m.version === bestVersion;
              const isSeed = m.is_seed;
              const isExpanded = expandedVersion === m.version;
              const successRate = m.tasks > 0 ? (m.successes / m.tasks * 100) : 0;
              
              return (
                <>
                  <tr 
                    key={m.version}
                    onClick={() => setExpandedVersion(isExpanded ? null : m.version)}
                    className={`cursor-pointer hover:bg-slate-50 transition-colors ${isBest ? 'bg-green-50/50' : ''}`}
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {idx === 0 ? (
                          <span className="w-8 h-8 rounded-full bg-gradient-to-br from-yellow-400 to-amber-500 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-amber-500/30">1</span>
                        ) : idx === 1 ? (
                          <span className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-300 to-slate-400 flex items-center justify-center text-white font-bold text-sm">2</span>
                        ) : idx === 2 ? (
                          <span className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-600 to-amber-700 flex items-center justify-center text-white font-bold text-sm">3</span>
                        ) : (
                          <span className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 font-medium text-sm">{idx + 1}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className={`inline-flex items-center px-3 py-1 rounded-lg text-sm font-mono font-medium ${
                          isBest ? 'bg-green-100 text-green-700' : isSeed ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-700'
                        }`}>
                          v{m.version}
                        </span>
                        {isBest && <Trophy className="w-4 h-4 text-amber-500" />}
                        {isSeed && <span className="text-xs text-indigo-600 font-medium">Seed</span>}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className={`font-mono text-sm font-semibold ${isBest ? 'text-green-700' : 'text-slate-700'}`}>
                          {(m.average * 100).toFixed(1)}%
                        </span>
                        {isSeed && idx > 0 && (
                          <span className="text-xs text-red-500 flex items-center gap-0.5">
                            <ArrowDownRight className="w-3 h-3" />
                            baseline
                          </span>
                        )}
                        {!isSeed && m.average > (metrics.find(x => x.is_seed)?.average || 0) && (
                          <span className="text-xs text-green-600 flex items-center gap-0.5">
                            <ArrowUpRight className="w-3 h-3" />
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-slate-200 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full ${successRate >= 80 ? 'bg-green-500' : successRate >= 60 ? 'bg-amber-500' : 'bg-red-500'}`}
                            style={{ width: `${successRate}%` }}
                          />
                        </div>
                        <span className="text-sm text-slate-600">{successRate.toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-slate-600">{m.avg_cost} tokens</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-sm font-medium ${m.cost_per_success && m.cost_per_success < 5 ? 'text-green-600' : 'text-slate-600'}`}>
                        {m.cost_per_success?.toFixed(1)} tokens/success
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-slate-500">{m.strategy || '-'}</span>
                    </td>
                  </tr>
                  {isExpanded && (
                    <tr key={`${m.version}-expanded`} className="bg-slate-50">
                      <td colSpan={7} className="px-6 py-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm font-semibold text-slate-700">Prompt Text:</span>
                              {m.changes && <span className="text-xs text-slate-500">({m.changes})</span>}
                            </div>
                            <pre className="text-sm bg-slate-900 text-slate-100 p-4 rounded-xl overflow-x-auto whitespace-pre-wrap font-mono">
                              {m.prompt}
                            </pre>
                          </div>
                          <CopyButton text={m.prompt || ''} />
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============ Performance Chart ============
function PerformanceChart({ metrics }: { metrics: PromptMetric[] }) {
  const chartData = metrics.map(m => ({
    version: `v${m.version}`,
    score: m.average * 100,
    cost: m.avg_cost,
    isBest: m.average === Math.max(...metrics.map(x => x.average)),
    isSeed: m.is_seed,
  }));

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200/50 p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
          <TrendingUp className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-800">Score by Version</h3>
          <p className="text-sm text-slate-500">Higher is better • Green = best, Blue = seed, Gray = others</p>
        </div>
      </div>
      
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} barCategoryGap="15%">
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="version" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
            <Tooltip 
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white shadow-lg rounded-xl border border-slate-200 p-3">
                      <p className="font-semibold">{data.version}</p>
                      <p className="text-sm">Score: <span className="font-mono">{data.score.toFixed(1)}%</span></p>
                      <p className="text-sm">Cost: <span className="font-mono">{data.cost} tokens</span></p>
                      {data.isBest && <p className="text-xs text-green-600 mt-1">🏆 Best</p>}
                      {data.isSeed && <p className="text-xs text-indigo-600 mt-1">📝 Seed</p>}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="score" radius={[6, 6, 0, 0]} maxBarSize={50}>
              {chartData.map((entry, index) => (
                <Cell key={index} fill={entry.isBest ? '#10b981' : entry.isSeed ? '#6366f1' : '#cbd5e1'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      <div className="flex items-center justify-center gap-6 mt-4 text-sm">
        <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-indigo-500" /> Seed (Original)</div>
        <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-slate-300" /> Generated</div>
        <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-emerald-500" /> Best</div>
      </div>
    </div>
  );
}

// ============ Cost vs Performance Scatter ============
function CostVsPerformanceChart({ metrics }: { metrics: PromptMetric[] }) {
  const chartData = metrics.map(m => ({
    version: `v${m.version}`,
    x: m.avg_cost,
    y: m.average * 100,
    isBest: m.average === Math.max(...metrics.map(x => x.average)),
    isSeed: m.is_seed,
  }));

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200/50 p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center shadow-lg shadow-orange-500/20">
          <DollarSign className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-800">Cost vs Performance</h3>
          <p className="text-sm text-slate-500">Find the sweet spot: high score, low cost (top-left is ideal)</p>
        </div>
      </div>
      
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis 
              type="number" 
              dataKey="x" 
              name="Cost" 
              unit=" tokens" 
              stroke="#94a3b8" 
              fontSize={12}
              domain={['dataMin - 10', 'dataMax + 10']}
              label={{ value: 'Token Cost', position: 'bottom', offset: -5 }}
            />
            <YAxis 
              type="number" 
              dataKey="y" 
              name="Score" 
              unit="%" 
              stroke="#94a3b8" 
              fontSize={12}
              domain={[50, 100]}
              label={{ value: 'Score (%)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white shadow-lg rounded-xl border border-slate-200 p-3">
                      <p className="font-semibold">{data.version}</p>
                      <p className="text-sm">Score: {data.y.toFixed(1)}%</p>
                      <p className="text-sm">Cost: {data.x} tokens</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Scatter data={chartData} fill="#6366f1">
              {chartData.map((entry, index) => (
                <Cell 
                  key={index} 
                  fill={entry.isBest ? '#10b981' : entry.isSeed ? '#6366f1' : '#94a3b8'} 
                  stroke={entry.isBest ? '#059669' : entry.isSeed ? '#4f46e5' : '#64748b'}
                  strokeWidth={2}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ============ Recommendations Section ============
function RecommendationsSection({ story }: { story: any }) {
  if (!story?.recommendations) return null;

  return (
    <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl border border-amber-200/50 p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/20">
          <Lightbulb className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-800">What We Learned</h3>
          <p className="text-sm text-slate-500">Actionable insights from the optimization</p>
        </div>
      </div>
      
      <div className="space-y-4">
        {story.recommendations.map((rec: any, idx: number) => (
          <div key={idx} className="bg-white rounded-xl p-4 flex items-start gap-4 shadow-sm">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
              rec.impact === 'high' ? 'bg-red-100' : rec.impact === 'medium' ? 'bg-amber-100' : 'bg-slate-100'
            }`}>
              {rec.impact === 'high' ? (
                <ArrowUpRight className="w-4 h-4 text-red-600" />
              ) : rec.impact === 'medium' ? (
                <ArrowRight className="w-4 h-4 text-amber-600" />
              ) : (
                <ArrowDownRight className="w-4 h-4 text-slate-600" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="font-semibold text-slate-800">{rec.action}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  rec.impact === 'high' ? 'bg-red-100 text-red-700' : 
                  rec.impact === 'medium' ? 'bg-amber-100 text-amber-700' : 
                  'bg-slate-100 text-slate-600'
                }`}>
                  {rec.impact} impact
                </span>
              </div>
              <p className="text-sm text-slate-600">{rec.description}</p>
            </div>
          </div>
        ))}
      </div>
      
      {story.key_insight && (
        <div className="mt-6 p-4 bg-white rounded-xl border-l-4 border-amber-500">
          <div className="text-sm font-semibold text-slate-700 mb-1">💡 Key Insight</div>
          <p className="text-sm text-slate-600">{story.key_insight}</p>
        </div>
      )}
    </div>
  );
}

// ============ Loading State ============
function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-4 border-slate-200"></div>
        <div className="absolute top-0 left-0 w-16 h-16 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
      </div>
      <p className="mt-4 text-slate-500 font-medium">Loading optimization results...</p>
    </div>
  );
}

// ============ Error State ============
function ErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
        <AlertCircle className="w-8 h-8 text-red-500" />
      </div>
      <p className="text-lg font-semibold text-slate-800 mb-2">Failed to load data</p>
      <p className="text-slate-500 mb-4">{error}</p>
      <button 
        onClick={onRetry}
        className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
      >
        <RefreshCw className="w-4 h-4" />
        Retry
      </button>
    </div>
  );
}

// ============ Main Dashboard ============
export default function Dashboard() {
  const [data, setData] = useState<OptimizationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchOptimization()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-800 mb-2">
              Sparky
            </h1>
            <p className="text-slate-500">
              See how Agent Lightning improved your prompt through automatic optimization
            </p>
          </div>
          {!loading && !error && (
            <button 
              onClick={loadData}
              className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg font-medium hover:bg-slate-50 hover:border-slate-300 transition-all shadow-sm"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          )}
        </div>
        
        {/* Content */}
        {loading && <LoadingState />}
        {error && <ErrorState error={error} onRetry={loadData} />}
        {!loading && !error && data && (
          <>
            {/* Run APO */}
            <RunAPOSection onComplete={loadData} />
            
            {/* Key Results */}
            <KeyResultsHero data={data} />
            
            {/* Charts Side by Side */}
            <div className="grid lg:grid-cols-2 gap-6">
              <PerformanceChart metrics={data.metrics} />
              <CostVsPerformanceChart metrics={data.metrics} />
            </div>
            
            {/* Recommendations */}
            {data.optimization_story && (
              <RecommendationsSection story={data.optimization_story} />
            )}
            
            {/* All Versions Table */}
            <VersionComparisonTable metrics={data.metrics} story={data.optimization_story} />
          </>
        )}
      </div>
    </Layout>
  );
}