'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

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

function ReportCard({ report }: { report: CycleReport }) {
  const [expanded, setExpanded] = useState(false);
  const ts = new Date(report.timestamp);
  const timeStr = ts.toLocaleString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });

  return (
    <div className="card mb-16" style={{ borderColor: report.mode === 'live' ? 'var(--green-border)' : 'var(--border)' }}>
      <div
        className="card-header"
        style={{ cursor: 'pointer' }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', minWidth: 160 }}>{timeStr}</span>
          <span className={`badge ${report.mode === 'live' ? 'badge-green' : 'badge-yellow'}`}>
            {report.mode === 'live' ? 'LIVE' : 'DRY RUN'}
          </span>
          <span className="badge">{report.llm}</span>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{report.run_id}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 12 }}>
          <span>{report.stats.total_analyzed} analyzed</span>
          <span style={{ color: 'var(--red)' }}>{report.stats.killed} killed</span>
          <span style={{ color: 'var(--green)' }}>{report.stats.orders_submitted} orders</span>
          <span style={{ color: report.stats.closed_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
            ${report.stats.closed_pnl >= 0 ? '+' : ''}{report.stats.closed_pnl.toFixed(2)}
          </span>
          <span style={{ color: 'var(--text-muted)' }}>{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {expanded && (
        <div className="card-body">
          {/* Summary */}
          <div style={{ fontSize: 13, color: 'var(--text-primary)', marginBottom: 16, padding: '10px 14px', background: 'var(--bg-secondary)', borderRadius: 8, lineHeight: 1.6 }}>
            {report.summary_text}
          </div>

          {/* Per-Symbol */}
          {report.symbols.map((s, si) => (
            <div key={si} style={{ marginBottom: 10, padding: 10, border: '1px solid var(--border)', borderRadius: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <strong>{s.symbol}</strong>
                <span className={`badge ${s.regime?.includes('up') || s.regime?.includes('bull') ? 'badge-green' : s.regime?.includes('down') || s.regime?.includes('bear') ? 'badge-red' : 'badge-yellow'}`}>
                  {s.regime}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  ${(s.price || 0).toFixed(2)} · {(s.confidence * 100).toFixed(0)}% conf
                </span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 4 }}>
                {s.thesis || 'No thesis'}
              </div>
              {s.proposals.map((p, pi) => (
                <div key={pi} style={{
                  marginLeft: 12, padding: '4px 8px', marginTop: 3, borderRadius: 4,
                  background: p.outcome === 'ORDER SUBMITTED' ? 'var(--green-bg)' :
                    p.outcome === 'KILLED BY AGENT' ? 'var(--red-bg)' : 'var(--bg-secondary)',
                  fontSize: 11, borderLeft: `3px solid ${
                    p.outcome === 'ORDER SUBMITTED' ? 'var(--green)' :
                    p.outcome === 'KILLED BY AGENT' ? 'var(--red)' : 'var(--yellow)'
                  }`
                }}>
                  <strong>{p.strategy.replace(/_/g, ' ')}</strong>{' '}
                  <span style={{
                    color: p.outcome === 'ORDER SUBMITTED' ? 'var(--green)' :
                      p.outcome === 'KILLED BY AGENT' ? 'var(--red)' : 'var(--yellow)'
                  }}>
                    {p.outcome}
                  </span>
                  {p.order_id && <span style={{ fontSize: 10, color: 'var(--text-muted)', marginLeft: 6 }}>#{p.order_id.slice(0, 8)}</span>}
                  {p.kill_reasons.length > 0 && (
                    <div style={{ color: 'var(--text-muted)', marginTop: 1 }}>Kill: {p.kill_reasons[0]}</div>
                  )}
                  {p.risk_reasons.length > 0 && !p.risk_approved && (
                    <div style={{ color: 'var(--text-muted)', marginTop: 1 }}>Risk: {p.risk_reasons[0]}</div>
                  )}
                </div>
              ))}
            </div>
          ))}

          {/* Closes */}
          {report.closes.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <div style={{ fontSize: 11, fontWeight: 600, marginBottom: 4, color: 'var(--text-secondary)' }}>Position Closes</div>
              {report.closes.map((c, ci) => (
                <div key={ci} style={{
                  padding: '4px 8px', marginBottom: 3, borderRadius: 4,
                  background: c.pnl >= 0 ? 'var(--green-bg)' : 'var(--red-bg)',
                  fontSize: 11, borderLeft: `3px solid ${c.pnl >= 0 ? 'var(--green)' : 'var(--red)'}`
                }}>
                  <strong>{c.symbol}</strong> — {c.reason} — ${c.pnl >= 0 ? '+' : ''}{c.pnl.toFixed(2)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<CycleReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'dry' | 'live'>('all');

  useEffect(() => {
    const key = localStorage.getItem('killjoy_api_key');
    if (!key) { router.push('/setup'); return; }
    api.allReports().then(r => {
      setReports(r.reports || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [router]);

  const filtered = reports.filter(r => {
    if (filter === 'dry') return r.mode !== 'live';
    if (filter === 'live') return r.mode === 'live';
    return true;
  });

  const dryCount = reports.filter(r => r.mode !== 'live').length;
  const liveCount = reports.filter(r => r.mode === 'live').length;

  return (
    <>
      <div className="card mb-24">
        <div className="card-header">
          <span className="card-title">Cycle Reports</span>
          <div style={{ display: 'flex', gap: 6 }}>
            <button className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter('all')} style={{ fontSize: 12, padding: '4px 10px' }}>
              All ({reports.length})
            </button>
            <button className={`btn ${filter === 'dry' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter('dry')} style={{ fontSize: 12, padding: '4px 10px' }}>
              Dry Runs ({dryCount})
            </button>
            <button className={`btn ${filter === 'live' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter('live')} style={{ fontSize: 12, padding: '4px 10px' }}>
              Live ({liveCount})
            </button>
          </div>
        </div>
        <div className="card-body">
          {loading ? (
            <div className="loading-state"><span className="spinner" /> Loading reports...</div>
          ) : filtered.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
              {reports.length === 0 ? 'No reports yet. Run a cycle on the Market page.' : `No ${filter} reports found.`}
            </div>
          ) : (
            filtered.map((r, i) => <ReportCard key={i} report={r} />)
          )}
        </div>
      </div>
    </>
  );
}
