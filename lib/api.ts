const getApiBase = (): string => {
  if (typeof window === 'undefined') return '';
  // In Vercel, the backend URL is set via env var
  // In local dev, fall back to localStorage or localhost
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  return localStorage.getItem('killjoy_api_url') || 'http://localhost:8000';
};

const getHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (typeof window !== 'undefined') {
    const apiKey = localStorage.getItem('killjoy_api_key');
    const secretKey = localStorage.getItem('killjoy_secret_key');
    if (apiKey) headers['X-Alpaca-Api-Key'] = apiKey;
    if (secretKey) headers['X-Alpaca-Secret-Key'] = secretKey;
  }
  return headers;
};

// ── Existing types ───────────────────────────────────────────────

export interface HealthResponse { status: string; alpaca_configured: boolean; paper_mode: boolean; }
export interface CheckResponse { connected: boolean; reason?: string; paper_mode?: boolean; account_status?: string; buying_power?: string; portfolio_value?: string; position_count?: number; }
export interface AccountResponse { status: string; buying_power: string; portfolio_value: string; equity: string; cash: string; initial_margin: string; maintenance_margin: string; daytrade_count: number; pattern_day_trader: boolean; trading_blocked: boolean; options_trading_level: number | null; }
export interface Position { symbol: string; qty: string; side: string; avg_entry_price: string; current_price: string; unrealized_pl: string; unrealized_plpc: string; market_value: string; }
export interface PositionsResponse { positions: Position[]; count: number; }
export interface Order { id: string; symbol: string; side: string; type: string; status: string; qty: string; filled_qty: string; submitted_at: string; filled_at: string; }
export interface OrdersResponse { orders: Order[]; count: number; }
export interface Analysis { symbol: string; regime?: string; confidence?: number; price?: string; thesis?: string; observations?: string[]; error?: string; }
export interface AnalyzeResponse { analyses: Analysis[]; }
export interface PaperCycleResponse { results: Record<string, unknown>; }
export interface JournalEntry { trade_id: string; underlying: string; strategy: string; confidence: number; kill_score: number; result: string; realized_pnl: number; thesis: string; timestamp: string; }
export interface JournalResponse { entries: JournalEntry[]; count: number; }

// ── Performance types ────────────────────────────────────────────

export interface PerformanceSummary {
  total_trades: number;
  open_trades: number;
  closed_trades: number;
  win_count: number;
  loss_count: number;
  breakeven_count: number;
  win_rate: number;
  realized_pnl: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number | string;
  max_drawdown: number;
  max_drawdown_pct: number;
  by_strategy: Record<string, { count: number; win_rate: number; total_pnl: number; avg_pnl: number }>;
  by_underlying: Record<string, { count: number; win_rate: number; total_pnl: number }>;
  kill_score_attribution: Record<string, { count: number; win_rate: number; avg_pnl: number }>;
  confidence_calibration: Record<string, { count: number; win_rate: number; avg_confidence: number }>;
  note?: string;
}

export interface RejectionAnalytics {
  total: number;
  top_rejection_reasons: Record<string, number>;
  avg_kill_score: number;
  by_strategy: Record<string, number>;
  recent: Array<{ id: string; timestamp: string; underlying: string; strategy: string; kill_score: number; reason: string }>;
}

export interface EventEntry {
  timestamp: string;
  run_id: string;
  event_type: string;
  symbol?: string;
  data?: Record<string, unknown>;
}

export interface EventsResponse {
  events: EventEntry[];
  count: number;
}

export interface EventsSummary {
  total_events: number;
  unique_runs: number;
  event_types: Record<string, number>;
  date: string;
}

export interface CorrelationMatrix {
  symbols: string[];
  matrix: number[][];
}

export interface CorrelationRisk {
  risk_level: string;
  max_correlation?: number;
  correlated_pairs?: Array<[string, string, number]>;
}

export interface CorrelationResponse {
  matrix: CorrelationMatrix;
  risk: CorrelationRisk;
}

export interface ParamHistoryEntry {
  parameter: string;
  old_value: number;
  recommended_value: number;
  reason: string;
  evidence: string;
  confidence: number;
  applied: boolean;
  applied_at?: string;
}

export interface ParamsResponse {
  params: Record<string, number>;
  history: ParamHistoryEntry[];
}

// ── New feature types ────────────────────────────────────────────

export interface CounterfactualSummary {
  total_trades: number;
  evaluated: number;
  simulated_pnl: number;
  win_rate: number;
  would_win: number;
  would_loss: number;
  would_breakeven: number;
  avg_kill_score: number;
  recent: Array<{
    id: string;
    underlying: string;
    strategy: string;
    kill_score: number;
    simulated_pnl: number;
    simulated_result: string;
    rejection_reason: string;
    timestamp: string;
  }>;
}

export interface KillPrecisionSummary {
  correct_kills: number;
  false_kills: number;
  total_kills: number;
  kill_precision: number;
  correct_executes: number;
  false_executes: number;
  total_executes: number;
  execute_quality: number;
  kill_score_distribution: Record<string, { count: number; precision: number; would_win: number; would_loss: number }>;
  false_kill_analysis: Array<{
    underlying: string;
    strategy: string;
    kill_score: number;
    would_pnl: number;
    rejection_reason: string;
  }>;
  net_value_added: number;
}

export interface ReceiptSummary {
  total: number;
  executed: number;
  killed: number;
  portfolio_rejected: number;
  risk_rejected: number;
  avg_kill_score: number;
  avg_debate_rounds: number;
  recent_receipts: Array<{
    receipt_id: string;
    underlying: string;
    strategy: string;
    final_decision: string;
    kill_score: number;
    confidence: number;
    timestamp: string;
  }>;
}

export interface DecisionReceipt {
  receipt_id: string;
  trade_id: string;
  timestamp: string;
  underlying: string;
  strategy: string;
  thesis: string;
  confidence: number;
  kill_score: number;
  survives_kill: boolean;
  portfolio_check: boolean;
  risk_check: boolean;
  final_decision: string;
  kill_reasons: string[];
  counterfactual: string;
  portfolio_reasons: string[];
  risk_reasons: string[];
  order_id: string;
  alpaca_status: string;
  agent_scores: Record<string, number>;
  debate_rounds: number;
  mcp_tools_used: string[];
  outcome_pnl: number | null;
  outcome_result: string;
}

export interface GraveyardSummary {
  total_variants: number;
  active: number;
  killed: number;
  resurrected: number;
  by_strategy: Record<string, Array<{
    version: number;
    status: string;
    total_trades: number;
    win_rate: number;
    total_pnl: number;
    kill_reason: string;
  }>>;
  resurrection_candidates: Array<{
    strategy_type: string;
    version: number;
    total_trades: number;
    win_rate: number;
    total_pnl: number;
    kill_reason: string;
    resurrection_readiness: string;
  }>;
  graves: Array<{
    id: string;
    strategy_type: string;
    version: number;
    status: string;
    total_trades: number;
    win_rate: number;
    total_pnl: number;
    kill_reason: string;
    created_at: string;
    killed_at: string | null;
    resurrected_at: string | null;
  }>;
}

export interface DisagreementSummary {
  disagreements: Array<{
    trade_id: string;
    underlying: string;
    disagreement_index: number;
    consensus: string;
    agent_scores: Array<{ agent_name: string; confidence: number; stance: string }>;
  }>;
  summary: {
    total_evaluated: number;
    avg_disagreement_index: number;
    consensus_distribution: Record<string, number>;
  };
}

export interface JudgeModeData {
  status: {
    connected: boolean;
    paper_mode: boolean;
    risk_engine: string;
    kill_agent: string;
    mcp: string;
  };
  account: Record<string, string | number>;
  performance: PerformanceSummary;
  counterfactual: CounterfactualSummary;
  kill_precision: KillPrecisionSummary;
  receipts: ReceiptSummary;
  graveyard: GraveyardSummary;
  rejections: {
    total: number;
    kill_agent: number;
    portfolio: number;
    risk_engine: number;
    avg_kill_score: number;
  };
}

// ── API client ───────────────────────────────────────────────────

async function apiFetch<T>(path: string): Promise<T> {
  const base = getApiBase();
  const res = await fetch(`${base}${path}`, { headers: getHeaders() });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => apiFetch<HealthResponse>('/api/health'),
  check: () => apiFetch<CheckResponse>('/api/check'),
  account: () => apiFetch<AccountResponse>('/api/account'),
  positions: () => apiFetch<PositionsResponse>('/api/positions'),
  orders: () => apiFetch<OrdersResponse>('/api/orders'),
  analyze: () => apiFetch<AnalyzeResponse>('/api/analyze'),
  paperCycle: () => apiFetch<PaperCycleResponse>('/api/paper-cycle'),
  liveCycle: () => apiFetch<PaperCycleResponse>('/api/live-cycle'),
  journal: () => apiFetch<JournalResponse>('/api/journal'),
  performance: () => apiFetch<PerformanceSummary>('/api/performance'),
  rejections: () => apiFetch<RejectionAnalytics>('/api/rejections'),
  events: (params?: { run_id?: string; event_type?: string; date?: string }) => {
    const qs = new URLSearchParams();
    if (params?.run_id) qs.set('run_id', params.run_id);
    if (params?.event_type) qs.set('event_type', params.event_type);
    if (params?.date) qs.set('date', params.date);
    const query = qs.toString();
    return apiFetch<EventsResponse>(`/api/events${query ? `?${query}` : ''}`);
  },
  eventsSummary: (date?: string) => {
    const qs = date ? `?date=${date}` : '';
    return apiFetch<EventsSummary>(`/api/events/summary${qs}`);
  },
  correlation: () => apiFetch<CorrelationResponse>('/api/correlation'),
  params: () => apiFetch<ParamsResponse>('/api/params'),
  // New endpoints
  counterfactual: () => apiFetch<CounterfactualSummary>('/api/counterfactual'),
  counterfactualEvaluate: () => apiFetch<{ evaluated: number; would_win: number; would_loss: number }>('/api/counterfactual/evaluate'),
  precision: () => apiFetch<KillPrecisionSummary>('/api/precision'),
  receipts: () => apiFetch<ReceiptSummary>('/api/receipts'),
  receipt: (id: string) => apiFetch<DecisionReceipt>(`/api/receipts/${id}`),
  graveyard: () => apiFetch<GraveyardSummary>('/api/graveyard'),
  disagreement: () => apiFetch<DisagreementSummary>('/api/disagreement'),
  judgeMode: () => apiFetch<JudgeModeData>('/api/judge-mode'),
};
