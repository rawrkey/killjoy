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
export interface JournalEntry { trade_id: string; underlying: string; strategy: string; confidence: number; kill_score: number; result: string; timestamp: string; }
export interface JournalResponse { entries: JournalEntry[]; count: number; }

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
};
