'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, AnalyzeResponse, PaperCycleResponse, CorrelationResponse } from '@/lib/api';

interface CycleReport {
  timestamp: string;
  mode: string;
  run_id: string;
  llm: string;
  summary_text: string;
  stats: {
    total_analyzed: number;
    killed: number;
    portfolio_rejected: number;
    risk_rejected: number;
    orders_submitted: number;
    positions_closed: number;
    closed_pnl: number;
  };
  symbols: {
    symbol: string;
    regime: string;
    confidence: number;
    price: number;
    thesis: string;
    proposals: {
      strategy: string;
      kill_score: number;
      survives: boolean;
      kill_reasons: string[];
      risk_approved: boolean;
      risk_reasons: string[];
      portfolio_approved: boolean;
      portfolio_reasons: string[];
      outcome: string;
      order_id: string;
    }[];
  }[];
  closes: {
    symbol: string;
    reason: string;
    pnl: number;
    strategy: string;
  }[];
}

export default function MarketPage() {
  const router = useRouter();
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [correlation, setCorrelation] = useState<CorrelationResponse | null>(null);
  const [report, setReport] = useState<CycleReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [liveLoading, setLiveLoading] = useState(false);
  const [marketOpen, setMarketOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const key = localStorage.getItem('killjoy_api_key');
    if (!key) { router.push('/setup'); return; }
    api.analyze().then(setData).catch(e => setError(e.message));
    api.correlation().then(setCorrelation).catch(() => {});
    api.lastReport().then(r => { if (r.report) setReport(r.report); }).catch(() => {});
  }, [router]);

  useEffect(() => {
    const checkMarket = () => {
      const now = new Date();
      const et = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }));
      const day = et.getDay();
      const h = et.getHours();
      const m = et.getMinutes();
      const mins = h * 60 + m;
      const isOpen = day >= 1 && day <= 5 && mins >= 570 && mins < 960;
      setMarketOpen(isOpen);
    };
    checkMarket();
    const id = setInterval(checkMarket, 30000);
    return () => clearInterval(id);
  }, []);

  const fetchReport = () => {
    api.lastReport().then(r => { if (r.report) setReport(r.report); }).catch(() => {});
  };

  const runCycle = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.paperCycle();
      fetchReport();
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  };

  const runLiveCycle = async () => {
    if (!confirm('This will submit REAL paper orders to Alpaca. Continue?')) return;
    setLiveLoading(true);
    setError(null);
    try {
      await api.liveCycle();
      fetchReport();
    } catch (e: any) {
      setError(e.message);
    }
    setLiveLoading(false);
  };

  return (
    <>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="card mb-24">
        <div className="card-header">
          <span className="card-title">Actions</span>
        </div>
        <div className="card-body">
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button className="btn btn-primary" onClick={runCycle} disabled={loading}>
              {loading ? <><span className="spinner" /> Running...</> : 'Run Paper Cycle'}
            </button>
            <button
              className="btn btn-danger"
              onClick={runLiveCycle}
              disabled={liveLoading || !marketOpen}
              title={!marketOpen ? 'Market is closed (Mon-Fri 9:30 AM - 4:00 PM ET)' : ''}
            >
              {liveLoading ? <><span className="spinner" /> Executing...</> : 'Run LIVE Cycle'}
            </button>
            <button className="btn btn-secondary" onClick={() => api.analyze().then(setData)}>
              Refresh Analysis
            </button>
            <span style={{ fontSize: 11, color: marketOpen ? 'var(--green)' : 'var(--text-muted)', marginLeft: 4 }}>
              {marketOpen ? 'Market OPEN' : 'Market CLOSED'}
            </span>
          </div>
        </div>
      </div>

      {/* ── Latest Cycle Report ── */}
      {report && (
        <div className="card mb-24" style={{ borderColor: 'var(--purple-border)' }}>
          <div className="card-header">
            <span className="card-title">Latest Cycle Report</span>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <span className="badge badge-purple">{report.mode}</span>
              <span className="badge">{report.llm}</span>
            </div>
          </div>
          <div className="card-body">
            {/* Plain-English Summary */}
            <div style={{ fontSize: 14, color: 'var(--text-primary)', marginBottom: 16, padding: '12px 16px', background: 'var(--bg-secondary)', borderRadius: 8, lineHeight: 1.6 }}>
              {report.summary_text}
            </div>

            {/* Stats Row */}
            <div className="stats-grid" style={{ marginBottom: 16 }}>
              <div className="stat-card">
                <div className="stat-label">Analyzed</div>
                <div className="stat-value">{report.stats.total_analyzed}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Killed</div>
                <div className="stat-value" style={{ color: 'var(--red)' }}>{report.stats.killed}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Orders</div>
                <div className="stat-value" style={{ color: 'var(--green)' }}>{report.stats.orders_submitted}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Closed</div>
                <div className="stat-value">{report.stats.positions_closed}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Closed P&L</div>
                <div className="stat-value" style={{ color: report.stats.closed_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
                  ${report.stats.closed_pnl >= 0 ? '+' : ''}{report.stats.closed_pnl.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Per-Symbol Breakdown */}
            {report.symbols.map((s, si) => (
              <div key={si} style={{ marginBottom: 12, padding: 12, border: '1px solid var(--border)', borderRadius: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <strong>{s.symbol}</strong>
                  <span className={`badge ${s.regime?.includes('up') || s.regime?.includes('bull') ? 'badge-green' : s.regime?.includes('down') || s.regime?.includes('bear') ? 'badge-red' : 'badge-yellow'}`}>
                    {s.regime}
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    ${(s.price || 0).toFixed(2)} · {(s.confidence * 100).toFixed(0)}% conf
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 6 }}>
                  {s.thesis || 'No thesis'}
                </div>
                {s.proposals.map((p, pi) => (
                  <div key={pi} style={{
                    marginLeft: 12, padding: '6px 10px', marginTop: 4, borderRadius: 6,
                    background: p.outcome === 'ORDER SUBMITTED' ? 'var(--green-bg)' :
                      p.outcome === 'KILLED BY AGENT' ? 'var(--red-bg)' : 'var(--bg-secondary)',
                    fontSize: 12, borderLeft: `3px solid ${
                      p.outcome === 'ORDER SUBMITTED' ? 'var(--green)' :
                      p.outcome === 'KILLED BY AGENT' ? 'var(--red)' : 'var(--yellow)'
                    }`
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <strong>{p.strategy.replace(/_/g, ' ')}</strong>
                      <span style={{
                        fontWeight: 600,
                        color: p.outcome === 'ORDER SUBMITTED' ? 'var(--green)' :
                          p.outcome === 'KILLED BY AGENT' ? 'var(--red)' : 'var(--yellow)'
                      }}>
                        {p.outcome}
                      </span>
                      {p.order_id && <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>#{p.order_id.slice(0, 8)}</span>}
                    </div>
                    {p.kill_reasons.length > 0 && (
                      <div style={{ color: 'var(--text-muted)', marginTop: 2 }}>
                        Kill Agent: {p.kill_reasons[0]}
                      </div>
                    )}
                    {p.risk_reasons.length > 0 && !p.risk_approved && (
                      <div style={{ color: 'var(--text-muted)', marginTop: 2 }}>
                        Risk: {p.risk_reasons[0]}
                      </div>
                    )}
                    {p.portfolio_reasons.length > 0 && !p.portfolio_approved && (
                      <div style={{ color: 'var(--text-muted)', marginTop: 2 }}>
                        Portfolio: {p.portfolio_reasons[0]}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ))}

            {/* Position Closes */}
            {report.closes.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6, color: 'var(--text-secondary)' }}>Position Closes</div>
                {report.closes.map((c, ci) => (
                  <div key={ci} style={{
                    padding: '6px 10px', marginBottom: 4, borderRadius: 6,
                    background: c.pnl >= 0 ? 'var(--green-bg)' : 'var(--red-bg)',
                    fontSize: 12, borderLeft: `3px solid ${c.pnl >= 0 ? 'var(--green)' : 'var(--red)'}`
                  }}>
                    <strong>{c.symbol}</strong> closed — {c.reason} — ${c.pnl >= 0 ? '+' : ''}{c.pnl.toFixed(2)}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="card mb-24">
        <div className="card-header">
          <span className="card-title">LLM Market Analysis</span>
          <span className="badge badge-purple">Top 5</span>
        </div>
        <div className="card-body">
          {!data ? (
            <div className="loading-state"><span className="spinner" /> Analyzing market...</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Regime</th>
                    <th>Confidence</th>
                    <th>Price</th>
                    <th>Thesis</th>
                    <th>Observations</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.analyses ?? []).map((a, i) => (
                    <tr key={i}>
                      <td><strong>{a.symbol}</strong></td>
                      <td>
                        <span className={`badge ${
                          a.regime?.includes('up') || a.regime?.includes('bull') ? 'badge-green' :
                          a.regime?.includes('down') || a.regime?.includes('bear') ? 'badge-red' :
                          'badge-yellow'
                        }`}>
                          {a.regime || '—'}
                        </span>
                      </td>
                      <td className="mono">{a.confidence != null ? `${(a.confidence * 100).toFixed(0)}%` : '—'}</td>
                      <td className="mono">{a.price ? `$${Number(a.price).toFixed(2)}` : '—'}</td>
                      <td style={{ maxWidth: 280, fontSize: 12, color: 'var(--text-secondary)' }}>
                        {a.thesis || a.error || '—'}
                      </td>
                      <td style={{ maxWidth: 200, fontSize: 11, color: 'var(--text-muted)' }}>
                        {a.observations?.slice(0, 2).join('; ') || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {correlation?.matrix?.symbols && correlation.matrix.symbols.length > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title">Portfolio Correlation</span>
            <span className={`badge ${correlation.risk.risk_level === 'low' ? 'badge-green' : correlation.risk.risk_level === 'high' ? 'badge-red' : 'badge-yellow'}`}>
              {correlation.risk.risk_level} risk
            </span>
          </div>
          <div className="card-body">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th></th>
                    {correlation.matrix.symbols.map(s => (
                      <th key={s} className="mono">{s}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(correlation.matrix.symbols ?? []).map((row, ri) => (
                    <tr key={ri}>
                      <td><strong className="mono">{row}</strong></td>
                      {(correlation.matrix.matrix[ri] ?? []).map((val, ci) => (
                        <td key={ci} className="mono" style={{
                          fontSize: 12,
                          color: ri === ci ? 'var(--text-muted)' :
                            val > 0.7 ? 'var(--red)' :
                            val > 0.4 ? 'var(--yellow)' :
                            'var(--green)',
                          background: ri === ci ? 'transparent' :
                            val > 0.7 ? 'var(--red-bg)' :
                            val > 0.4 ? 'var(--yellow-bg)' :
                            'var(--green-bg)',
                        }}>
                          {val.toFixed(2)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {correlation.risk.correlated_pairs && correlation.risk.correlated_pairs.length > 0 && (
              <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-secondary)' }}>
                <strong>High correlations:</strong>
                {correlation.risk.correlated_pairs.map(([a, b, c], i) => (
                  <span key={i} style={{ marginLeft: 8 }}>
                    <span className="badge badge-red">{a}/{b}</span> {c.toFixed(2)}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
