'use client';

import { useEffect, useState } from 'react';
import { api, GraveyardSummary } from '@/lib/api';

export default function GraveyardPage() {
  const [data, setData] = useState<GraveyardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.graveyard().then(setData).catch(e => setError(e.message));
  }, []);

  if (error) return <div className="alert alert-error">{error}</div>;
  if (!data) return <div className="loading-state"><span className="spinner" /> Loading graveyard...</div>;

  return (
    <>
      {/* Header */}
      <div className="card mb-24" style={{ borderColor: 'var(--red-border)' }}>
        <div className="card-body" style={{ textAlign: 'center', padding: '24px' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 700, color: 'var(--red)', letterSpacing: 3 }}>
            STRATEGY GRAVEYARD 💀
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
            Strategies that failed, got retired, and may return
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-grid mb-24">
        <div className="stat-card">
          <div className="stat-label">Total Variants</div>
          <div className="stat-value">{data.total_variants}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Active</div>
          <div className="stat-value green">{data.active}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Killed</div>
          <div className="stat-value red">{data.killed}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Resurrected</div>
          <div className="stat-value" style={{ color: 'var(--purple)' }}>{data.resurrected}</div>
        </div>
      </div>

      {/* Resurrection Candidates */}
      {data.resurrection_candidates.length > 0 && (
        <div className="card mb-24" style={{ borderColor: 'var(--yellow-border)' }}>
          <div className="card-header">
            <span className="card-title">Resurrection Candidates</span>
            <span className="badge badge-yellow">{data.resurrection_candidates.length} candidates</span>
          </div>
          <div className="card-body">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Strategy</th><th>Version</th><th>Trades</th><th>Win Rate</th><th>P&L</th><th>Kill Reason</th><th>Readiness</th></tr>
                </thead>
                <tbody>
                  {data.resurrection_candidates.map((c, i) => (
                    <tr key={i}>
                      <td><span className="badge badge-blue">{c.strategy_type}</span></td>
                      <td className="mono">v{c.version}</td>
                      <td className="mono">{c.total_trades}</td>
                      <td className="mono" style={{ color: c.win_rate >= 0.4 ? 'var(--yellow)' : 'var(--red)' }}>
                        {(c.win_rate * 100).toFixed(1)}%
                      </td>
                      <td className="mono" style={{ color: c.total_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {c.total_pnl >= 0 ? '+' : ''}${c.total_pnl.toFixed(2)}
                      </td>
                      <td style={{ fontSize: 12, color: 'var(--text-muted)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {c.kill_reason || '—'}
                      </td>
                      <td>
                        <span className={`badge ${c.resurrection_readiness === 'high' ? 'badge-green' : 'badge-yellow'}`}>
                          {c.resurrection_readiness}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* All Graves */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">All Strategy Variants</span>
          <span className="badge badge-muted">{data.graves.length}</span>
        </div>
        <div className="card-body">
          {data.graves.length === 0 ? (
            <div className="empty-state">
              <div className="icon">💀</div>
              <p>No strategies in the graveyard yet</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Strategy</th><th>Version</th><th>Status</th><th>Trades</th><th>Win Rate</th><th>P&L</th><th>Kill Reason</th><th>Created</th></tr>
                </thead>
                <tbody>
                  {data.graves.map((g, i) => (
                    <tr key={i}>
                      <td><span className="badge badge-blue">{g.strategy_type}</span></td>
                      <td className="mono">v{g.version}</td>
                      <td>
                        <span className={`badge ${
                          g.status === 'active' ? 'badge-green' :
                          g.status === 'killed' ? 'badge-red' :
                          'badge-purple'
                        }`}>
                          {g.status === 'killed' ? '💀 killed' : g.status === 'resurrected' ? '♻ resurrected' : '✓ active'}
                        </span>
                      </td>
                      <td className="mono">{g.total_trades}</td>
                      <td className="mono" style={{ color: g.win_rate >= 0.5 ? 'var(--green)' : 'var(--red)' }}>
                        {(g.win_rate * 100).toFixed(1)}%
                      </td>
                      <td className="mono" style={{ color: g.total_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {g.total_pnl >= 0 ? '+' : ''}${g.total_pnl.toFixed(2)}
                      </td>
                      <td style={{ fontSize: 12, color: 'var(--text-muted)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {g.kill_reason || '—'}
                      </td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {new Date(g.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
