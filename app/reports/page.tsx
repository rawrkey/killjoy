'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

interface AgentReport {
  analyst: { score: number; stance: string; thesis: string };
  kill_agent: { score: number; survives: boolean; reasons: string[]; objections: string[]; critical_failures: string[]; debate_rounds: number };
  portfolio: { approved: boolean; reasons: string[] };
  risk_engine: { approved: boolean; reasons: string[]; checks: { name: string; passed: boolean; reason: string }[] };
}

interface ProposalReport {
  strategy: string;
  outcome: string;
  order_id: string;
  analyst: { score: number; stance: string; thesis: string };
  kill_agent: { score: number; survives: boolean; reasons: string[]; objections: string[]; critical_failures: string[]; debate_rounds: number };
  portfolio: { approved: boolean; reasons: string[] };
  risk_engine: { approved: boolean; reasons: string[]; checks: { name: string; passed: boolean; reason: string }[] };
}

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
    positions_checked: number;
    positions_closed: number;
    closed_pnl: number;
  };
  symbols: {
    symbol: string;
    regime: string;
    confidence: number;
    price: number;
    thesis: string;
    observations: string[];
    proposals: ProposalReport[];
  }[];
  closes: { symbol: string; reason: string; pnl: number; strategy: string }[];
}

function AgentPipeline({ p }: { p: ProposalReport }) {
  const color = p.outcome === 'ORDER SUBMITTED' ? 'var(--green)' : p.outcome === 'KILLED BY AGENT' ? 'var(--red)' : 'var(--yellow)';
  return (
    <div style={{ marginLeft: 12, marginTop: 6, padding: 8, borderRadius: 6, border: `1px solid ${color}22`, background: `${color}08` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <strong style={{ fontSize: 13 }}>{p.strategy.replace(/_/g, ' ')}</strong>
        <span style={{ fontWeight: 700, color, fontSize: 12 }}>{p.outcome}</span>
        {p.order_id && <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>#{p.order_id.slice(0, 8)}</span>}
      </div>

      {/* Pipeline flow */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 11 }}>
        {/* Analyst */}
        <div style={{ display: 'flex', gap: 6, alignItems: 'flex-start' }}>
          <span style={{ minWidth: 70, color: 'var(--text-muted)', fontWeight: 600 }}>Analyst</span>
          <span>{(p.analyst.score * 100).toFixed(0)}% conf · {p.analyst.stance}</span>
        </div>
        {p.analyst.thesis && (
          <div style={{ marginLeft: 76, color: 'var(--text-secondary)', fontStyle: 'italic' }}>&ldquo;{p.analyst.thesis}&rdquo;</div>
        )}

        {/* Kill Agent */}
        <div style={{ display: 'flex', gap: 6, alignItems: 'flex-start' }}>
          <span style={{ minWidth: 70, color: 'var(--red)', fontWeight: 600 }}>Kill Agent</span>
          <span>score: {(p.kill_agent.score * 100).toFixed(0)}% · {p.kill_agent.survives ? 'survived' : 'killed'} · {p.kill_agent.debate_rounds} debate rounds</span>
        </div>
        {p.kill_agent.reasons.length > 0 && (
          <div style={{ marginLeft: 76, color: 'var(--text-secondary)' }}>
            Reasons: {p.kill_agent.reasons.join('; ')}
          </div>
        )}
        {p.kill_agent.objections.length > 0 && (
          <div style={{ marginLeft: 76, color: 'var(--red)' }}>
            Objections: {p.kill_agent.objections.join('; ')}
          </div>
        )}
        {p.kill_agent.critical_failures.length > 0 && (
          <div style={{ marginLeft: 76, color: 'var(--red)', fontWeight: 600 }}>
            Critical: {p.kill_agent.critical_failures.join('; ')}
          </div>
        )}

        {/* Portfolio */}
        <div style={{ display: 'flex', gap: 6 }}>
          <span style={{ minWidth: 70, color: p.portfolio.approved ? 'var(--green)' : 'var(--red)', fontWeight: 600 }}>Portfolio</span>
          <span>{p.portfolio.approved ? 'approved' : 'rejected'}{p.portfolio.reasons.length > 0 ? ` — ${p.portfolio.reasons.join('; ')}` : ''}</span>
        </div>

        {/* Risk Engine */}
        <div style={{ display: 'flex', gap: 6 }}>
          <span style={{ minWidth: 70, color: p.risk_engine.approved ? 'var(--green)' : 'var(--red)', fontWeight: 600 }}>Risk</span>
          <span>{p.risk_engine.approved ? 'approved' : 'rejected'}{p.risk_engine.reasons.length > 0 ? ` — ${p.risk_engine.reasons.join('; ')}` : ''}</span>
        </div>
        {p.risk_engine.checks.length > 0 && (
          <div style={{ marginLeft: 76, display: 'flex', flexWrap: 'wrap', gap: 3 }}>
            {p.risk_engine.checks.map((c, i) => (
              <span key={i} style={{
                fontSize: 10, padding: '1px 5px', borderRadius: 3,
                background: c.passed ? 'var(--green-bg)' : 'var(--red-bg)',
                color: c.passed ? 'var(--green)' : 'var(--red)',
                border: `1px solid ${c.passed ? 'var(--green)' : 'var(--red)'}33`,
              }}>
                {c.name.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
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
      <div className="card-header" style={{ cursor: 'pointer' }} onClick={() => setExpanded(!expanded)}>
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
          {report.stats.positions_closed > 0 && <span>{report.stats.positions_closed} closed</span>}
          {report.stats.closed_pnl !== 0 && (
            <span style={{ color: report.stats.closed_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
              ${report.stats.closed_pnl >= 0 ? '+' : ''}{report.stats.closed_pnl.toFixed(2)}
            </span>
          )}
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
            <div key={si} style={{ marginBottom: 14, padding: 12, border: '1px solid var(--border)', borderRadius: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <strong style={{ fontSize: 14 }}>{s.symbol}</strong>
                <span className={`badge ${s.regime?.includes('up') || s.regime?.includes('bull') ? 'badge-green' : s.regime?.includes('down') || s.regime?.includes('bear') ? 'badge-red' : 'badge-yellow'}`}>
                  {s.regime}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  ${(s.price || 0).toFixed(2)} · {(s.confidence * 100).toFixed(0)}% conf
                </span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4, fontStyle: 'italic' }}>
                {s.thesis || 'No thesis'}
              </div>
              {s.observations && s.observations.length > 0 && (
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
                  Observations: {s.observations.join('; ')}
                </div>
              )}

              {s.proposals.map((p, pi) => (
                <AgentPipeline key={pi} p={p} />
              ))}
            </div>
          ))}

          {/* Closes */}
          {report.closes.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6, color: 'var(--text-secondary)' }}>Position Closes</div>
              {report.closes.map((c, ci) => (
                <div key={ci} style={{
                  padding: '6px 10px', marginBottom: 4, borderRadius: 6,
                  background: c.pnl >= 0 ? 'var(--green-bg)' : 'var(--red-bg)',
                  fontSize: 12, borderLeft: `3px solid ${c.pnl >= 0 ? 'var(--green)' : 'var(--red)'}`
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
