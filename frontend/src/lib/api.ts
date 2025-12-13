// Simple API client for FastAPI backend
const API_BASE = 'http://localhost:8000';

export interface PromptMetric {
  version: string;
  tasks: number;
  successes: number;
  failures: number;
  rewards: number[];
  average: number;
  prompt: string | null;
  parent: string | null;
  is_seed: boolean;
  avg_cost: number;
  round: number;
  changes: string;
  strategy: string;
  success_rate: number;
  cost_per_success: number;
  evaluations?: { round: number; tasks: number; average: number }[];
  gradient?: string | null;
}

export interface Recommendation {
  action: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
}

export interface OptimizationStory {
  seed_version: string;
  seed_score: number;
  seed_cost: number;
  best_version: string;
  best_score: number;
  best_cost: number;
  best_strategy: string;
  improvement: number;
  improvement_pct: number;
  cost_change: number;
  cost_change_pct: number;
  total_versions_tested: number;
  most_efficient_version: string;
  most_efficient_cost_per_success: number;
  worst_version: string;
  worst_score: number;
  key_insight: string;
  recommendations: Recommendation[];
  total_rounds?: number;
  best_updates?: { round: number; version: string; new_score: number; prev_score: number; improvement: number }[];
}

export interface RoundInfo {
  round: number;
  description: string;
  versions: string[];
  current?: number;
  total?: number;
  parents?: string;
  top_candidates?: string;
}

export interface OptimizationData {
  prompts: { version: string; prompt: string; parent: string | null; is_seed: boolean; round?: number; changes?: string; strategy?: string }[];
  metrics: PromptMetric[];
  rounds: RoundInfo[];
  gradients?: { round: number; version: string; gradient: string }[];
  optimization_story: OptimizationStory | null;
}

export async function fetchMetrics(): Promise<PromptMetric[]> {
  const res = await fetch(`${API_BASE}/api/metrics`);
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return res.json();
}

export async function fetchOptimization(): Promise<OptimizationData> {
  const res = await fetch(`${API_BASE}/api/optimization`);
  if (!res.ok) throw new Error('Failed to fetch optimization data');
  return res.json();
}

export async function fetchLog(): Promise<string> {
  const res = await fetch(`${API_BASE}/api/log`);
  if (!res.ok) throw new Error('Failed to fetch log');
  try {
    const data = await res.json();
    return data.log || '';
  } catch {
    return await res.text();
  }
}

export async function fetchPrompts() {
  const res = await fetch(`${API_BASE}/api/prompts`);
  if (!res.ok) throw new Error('Failed to fetch prompts');
  return res.json();
}

export async function runApo(example: string = "room_selector") {
  const res = await fetch(`${API_BASE}/api/run_apo?example=${encodeURIComponent(example)}`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to start APO');
  return res.json();
}

export async function getRunStatus(pid: number) {
  const res = await fetch(`${API_BASE}/api/run_status/${pid}`);
  if (!res.ok) throw new Error('Failed to get run status');
  return res.json();
}

export async function getRunLogs(pid: number): Promise<string> {
  const res = await fetch(`${API_BASE}/api/run_logs/${pid}`);
  if (!res.ok) throw new Error('Failed to get run logs');
  const data = await res.json();
  return data.log || '';
}
