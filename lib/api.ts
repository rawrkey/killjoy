const getApiBase = (): string => {
  if (typeof window === 'undefined') return '';
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

// ── New types ────────────────────────────────────────────────────

export interface PerformanceSummary {
  total_trades: number;
  win_count: number;
  loss_count: number;
  win_rate: number;
  realized_pnl: number;
  avg_pnl_per_trade: number;
  max_win: number;
  max_loss: number;
  max_drawdown: number;
  sharpe_ratio: number | null;
  by_strategy: Record<string, { count: number; win_rate: number; total_pnl: number }>;
  by_underlying: Record<string, { count: number; win_rate: number; total_pnl: number }>;
  kill_score_attribution: Record<string, { count: number; win_rate: number; avg_pnl: number }>;
  note?: string;
}

export interface RejectionAnalytics {
  total_rejected: number;
  by_stage: Record<string, number>;
  top_reasons: Array<{ reason: string; count: number }>;
  by_strategy: Record<string, number>;
  by_symbol: Record<string, number>;
  avg_kill_score: number;
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
  journal: () => apiFetch<JournalResponse>('/api/journal'),
  // New endpoints
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
};
