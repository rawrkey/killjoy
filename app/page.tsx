'use client';

import { useEffect, useState } from 'react';
import { api, CheckResponse, AccountResponse, PositionsResponse, PerformanceSummary, EventsResponse, CounterfactualSummary, KillPrecisionSummary, DisagreementSummary } from '@/lib/api';

export default function Dashboard() {
  const [connected, setConnected] = useState<boolean | null>(null);
  const [account, setAccount] = useState<AccountResponse | null>(null);
  const [positions, setPositions] = useState<PositionsResponse | null>(null);
  const [performance, setPerformance] = useState<PerformanceSummary | null>(null);
  const [events, setEvents] = useState<EventsResponse | null>(null);
  const [counterfactual, setCounterfactual] = useState<CounterfactualSummary | null>(null);
  const [precision, setPrecision] = useState<KillPrecisionSummary | null>(null);
  const [disagreement, setDisagreement] = useState<DisagreementSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.check().then(r => setConnected(r.connected)).catch(() => {});
    api.account().then(setAccount).catch(() => {});
    api.positions().then(setPositions).catch(() => {});
    api.performance().then(setPerformance).catch(() => {});
    api.events({ event_type: 'analysis_completed' }).then(setEvents).catch(() => {});
    api.counterfactual().then(setCounterfactual).catch(() => {});
    api.precision().then(setPrecision).catch(() => {});
    api.disagreement().then(setDisagreement).catch(() => {});
  }, []);

  return (
    <>
      {error && <div className="alert alert-error">{error}</div>}

      {/* Status Row */}
      <div className="stats-grid mb-24">
        <div className="stat-card">
          <div className="stat-label">Connection</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className={`status-dot ${connected === true ? 'on' : connected === false ? 'off' : 'pending'}`} />
            <span className="stat-value" style={{ fontSize: 16 }}>
              {connected ? 'CONNECTED' : connected === false ? 'OFFLINE' : 'CHECKING'}
            </span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Mode</div>
          <div className="stat-value accent" style={{ fontSize: 16 }}>PAPER</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Risk Engine</div>
          <div className="stat-value green" style={{ fontSize: 16 }}>8 GATES</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Kill Agent</div>
          <div className="stat-value" style={{ fontSize: 16, color: 'var(--purple)' }}>ADVERSARIAL</div>
        </div>
      </div>

      {/* Kill Precision — KEY METRIC */}
      {precision && precision.total_kills > 0 && (
        <div className="card mb-24" style={{ borderColor: precision.kill_precision >= 0.6 ? 'var(--green-border)' : 'var(--red-border)' }}>
          <div className="card-header">
            <span className="card-title">Kill Precision</span>
            <span className={`badge ${precision.kill_precision >= 0.6 ? 'badge-green' : 'badge-red'}`}>
              {(precision.kill_precision * 100).toFixed(1)}% precision
            </span>
          </div>
          <div className="card-body">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Correct Kills</div>
                <div className="stat-value green">{precision.correct_kills}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">False Kills</div>
                <div className="stat-value red">{precision.false_kills}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Net Value Added</div>
                <div className="stat-value" style={{ color: precision.net_value_added >= 0 ? 'var(--green)' : 'var(--red)' }}>
                  {precision.net_value_added >= 0 ? '+' : ''}${precision.net_value_added.toFixed(2)}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Total Kills</div>
                <div className="stat-value">{precision.total_kills}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Performance Metrics */}
      {performance && performance.total_trades > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title">Performance</span>
            <span className="badge badge-green">{performance.total_trades} trades</span>
          </div>
          <div className="card-body">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Win Rate</div>
                <div className="stat-value" style={{ color: performance.win_rate >= 0.5 ? 'var(--green)' : 'var(--red)' }}>
                  {(performance.win_rate * 100).toFixed(1)}%
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Realized P&L</div>
                <div className="stat-value" style={{ color: performance.realized_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
                  {performance.realized_pnl >= 0 ? '+' : ''}${performance.realized_pnl.toFixed(2)}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Win / Loss</div>
                <div className="stat-value">
                  <span style={{ color: 'var(--green)' }}>{performance.win_count}</span>
                  <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>/</span>
                  <span style={{ color: 'var(--red)' }}>{performance.loss_count}</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Max Drawdown</div>
                <div className="stat-value red">{performance.max_drawdown.toFixed(2)}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Counterfactual Portfolio */}
      {counterfactual && counterfactual.evaluated > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title">Counterfactual Portfolio</span>
            <span className="badge badge-purple">{counterfactual.evaluated} evaluated</span>
          </div>
          <div className="card-body">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Simulated P&L</div>
                <div className="stat-value" style={{ color: counterfactual.simulated_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
                  {counterfactual.simulated_pnl >= 0 ? '+' : ''}${counterfactual.simulated_pnl.toFixed(2)}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Would Win</div>
                <div className="stat-value" style={{ color: 'var(--yellow)' }}>{counterfactual.would_win}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Would Loss</div>
                <div className="stat-value green">{counterfactual.would_loss}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Win Rate</div>
                <div className="stat-value">{(counterfactual.win_rate * 100).toFixed(1)}%</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Agent Disagreement */}
      {disagreement && disagreement.summary.total_evaluated > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title">Agent Disagreement</span>
            <span className={`badge ${disagreement.summary.avg_disagreement_index > 0.5 ? 'badge-yellow' : 'badge-green'}`}>
              {disagreement.summary.avg_disagreement_index > 0.5 ? 'HIGH' : 'LOW'} disagreement
            </span>
          </div>
          <div className="card-body">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Avg Disagreement</div>
                <div className="stat-value">{(disagreement.summary.avg_disagreement_index * 100).toFixed(1)}%</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Evaluated</div>
                <div className="stat-value">{disagreement.summary.total_evaluated}</div>
              </div>
              {Object.entries(disagreement.summary.consensus_distribution).map(([key, val]) => (
                <div className="stat-card" key={key}>
                  <div className="stat-label">{key}</div>
                  <div className="stat-value" style={{ fontSize: 16 }}>{val}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="grid-2 mb-24">
        {/* Account */}
        {account && (
          <div className="card">
            <div className="card-header">
              <span className="card-title">Account Overview</span>
              <span className="badge badge-green">{account.status}</span>
            </div>
            <div className="card-body">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="stat-card">
                  <div className="stat-label">Portfolio Value</div>
                  <div className="stat-value" style={{ fontSize: 16 }}>${Number(account.portfolio_value).toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Buying Power</div>
                  <div className="stat-value accent" style={{ fontSize: 16 }}>${Number(account.buying_power).toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Cash</div>
                  <div className="stat-value" style={{ fontSize: 16 }}>${Number(account.cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Day Trades</div>
                  <div className="stat-value" style={{ fontSize: 16 }}>{account.daytrade_count}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Positions */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Open Positions</span>
            <span className="badge badge-muted">{positions?.count ?? 0}</span>
          </div>
          <div className="card-body">
            {!positions ? (
              <div className="loading-state"><span className="spinner" /> Loading...</div>
            ) : positions.count === 0 ? (
              <div className="empty-state">
                <div className="icon">&#9650;</div>
                <p>No open positions</p>
              </div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>Symbol</th><th>Side</th><th>P&L</th></tr>
                  </thead>
                  <tbody>
                    {(positions?.positions ?? []).map((p, i) => (
                      <tr key={i}>
                        <td><strong>{p.symbol}</strong></td>
                        <td><span className={`badge ${p.side === 'long' ? 'badge-green' : 'badge-red'}`}>{p.side}</span></td>
                        <td className="mono" style={{ color: Number(p.unrealized_pl) >= 0 ? 'var(--green)' : 'var(--red)' }}>
                          {Number(p.unrealized_pl) >= 0 ? '+' : ''}${Number(p.unrealized_pl).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      {events && events.count > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title">Recent Activity</span>
            <span className="badge badge-blue">{events.count}</span>
          </div>
          <div className="card-body">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Event</th><th>Symbol</th><th>Time</th></tr>
                </thead>
                <tbody>
                  {(events?.events ?? []).slice(0, 8).map((e, i) => (
                    <tr key={i}>
                      <td>
                        <span className={`badge ${
                          e.event_type.includes('kill') ? 'badge-red' :
                          e.event_type.includes('order') ? 'badge-green' :
                          e.event_type.includes('risk') ? 'badge-yellow' :
                          'badge-blue'
                        }`}>
                          {e.event_type.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="mono">{e.symbol || '—'}</td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {new Date(e.timestamp).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Autonomous Pipeline</span>
          <span className="badge badge-purple">9 STAGES</span>
        </div>
        <div className="card-body">
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 2, color: 'var(--text-secondary)', overflowX: 'auto' }}>
            <div>
              <span style={{ color: 'var(--cyan)' }}>Market Data</span>
              {' '}&rarr;{' '}
              <span style={{ color: 'var(--accent)' }}>LLM Analyst</span>
              {' '}&rarr;{' '}
              <span style={{ color: 'var(--purple)' }}>LLM Strategy</span>
              {' '}&rarr;{' '}
              <span style={{ color: 'var(--red)' }}>Kill Agent</span>
              {' '}&rarr;{' '}
              <span style={{ color: 'var(--yellow)' }}>Portfolio</span>
              {' '}&rarr;{' '}
              <span style={{ color: 'var(--green)' }}>Risk Engine</span>
              {' '}&rarr;{' '}
              <span style={{ color: 'var(--accent)' }}>Execution</span>
              {' '}&rarr;{' '}
              <span style={{ color: 'var(--cyan)' }}>Alpaca</span>
            </div>
            <div style={{ color: 'var(--text-muted)', marginTop: 8 }}>
              &#8615; Position Monitor &larr; Trade Journal &larr; Postmortem
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
