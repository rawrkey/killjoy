'use client';

import { useEffect, useState } from 'react';
import { api, JudgeModeData } from '@/lib/api';

export default function JudgePage() {
  const [data, setData] = useState<JudgeModeData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.judgeMode()
      .then(r => { setData(r); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) {
    return (
      <div className="loading-state" style={{ minHeight: '60vh' }}>
        <span className="spinner" /> Loading Judge Mode...
      </div>
    );
  }

  if (error) {
    return <div className="alert alert-error">{error}</div>;
  }

  if (!data) return null;

  const p = data.performance;
  const cf = data.counterfactual;
  const kp = data.kill_precision;
  const rx = data.receipts;

  return (
    <>
      {/* KILLJOY Header */}
      <div className="card mb-24" style={{ borderColor: 'var(--accent)', borderWidth: 2 }}>
        <div className="card-body" style={{ textAlign: 'center', padding: '32px 24px' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 28, fontWeight: 700, color: 'var(--accent)', letterSpacing: 6 }}>
            KILLJOY
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4, letterSpacing: 2 }}>
            THE AI THAT TRIES TO PROVE ITSELF WRONG
          </div>
        </div>
      </div>

      {/* Status Row */}
      <div className="stats-grid mb-24">
        <div className="stat-card">
          <div className="stat-label">AI Status</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className={`status-dot ${data.status.connected ? 'on' : 'off'}`} />
            <span className="stat-value" style={{ fontSize: 14 }}>
              {data.status.connected ? 'ACTIVE' : 'OFFLINE'}
            </span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Alpaca</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className={`status-dot ${data.status.connected ? 'on' : 'off'}`} />
            <span className="stat-value" style={{ fontSize: 14 }}>
              {data.status.connected ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">MCP</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="status-dot on" />
            <span className="stat-value" style={{ fontSize: 14, color: 'var(--green)' }}>CONNECTED</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Mode</div>
          <div className="stat-value accent" style={{ fontSize: 14 }}>PAPER</div>
        </div>
      </div>

      {/* Pipeline Overview */}
      <div className="stats-grid mb-24">
        <div className="stat-card">
          <div className="stat-label">Opportunities Analyzed</div>
          <div className="stat-value">{rx.total}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Killed</div>
          <div className="stat-value red">{rx.killed}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Survived</div>
          <div className="stat-value" style={{ color: 'var(--yellow)' }}>{rx.total - rx.killed}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Executed</div>
          <div className="stat-value green">{rx.executed}</div>
        </div>
      </div>

      {/* Kill Rate */}
      {rx.total > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title">Kill Rate</span>
            <span className="badge badge-red">{((rx.killed / rx.total) * 100).toFixed(1)}%</span>
          </div>
          <div className="card-body">
            <div style={{ height: 8, background: 'var(--bg-primary)', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{
                height: '100%',
                width: `${(rx.killed / rx.total) * 100}%`,
                background: 'linear-gradient(90deg, var(--red), var(--yellow))',
                borderRadius: 4,
              }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
              <span>{rx.killed} killed</span>
              <span>{rx.executed} executed</span>
            </div>
          </div>
        </div>
      )}

      {/* Performance */}
      {p.total_trades > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title">Performance</span>
            <span className="badge badge-green">{p.total_trades} trades</span>
          </div>
          <div className="card-body">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">P&L</div>
                <div className="stat-value" style={{ color: p.realized_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
                  {p.realized_pnl >= 0 ? '+' : ''}${p.realized_pnl.toFixed(2)}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Win Rate</div>
                <div className="stat-value" style={{ color: p.win_rate >= 0.5 ? 'var(--green)' : 'var(--red)' }}>
                  {(p.win_rate * 100).toFixed(1)}%
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Profit Factor</div>
                <div className="stat-value accent">{typeof p.profit_factor === 'string' ? '∞' : p.profit_factor.toFixed(2)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Max Drawdown</div>
                <div className="stat-value red">{p.max_drawdown.toFixed(2)}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Kill Precision — THE KEY METRIC */}
      <div className="card mb-24" style={{ borderColor: kp.kill_precision >= 0.6 ? 'var(--green-border)' : 'var(--red-border)' }}>
        <div className="card-header">
          <span className="card-title">Kill Precision</span>
          <span className={`badge ${kp.kill_precision >= 0.6 ? 'badge-green' : 'badge-red'}`}>
            {(kp.kill_precision * 100).toFixed(1)}%
          </span>
        </div>
        <div className="card-body">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Correct Kills</div>
              <div className="stat-value green">{kp.correct_kills}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">False Kills</div>
              <div className="stat-value red">{kp.false_kills}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Net Value Added</div>
              <div className="stat-value" style={{ color: kp.net_value_added >= 0 ? 'var(--green)' : 'var(--red)' }}>
                {kp.net_value_added >= 0 ? '+' : ''}${kp.net_value_added.toFixed(2)}
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Total Kills</div>
              <div className="stat-value">{kp.total_kills}</div>
            </div>
          </div>
          {kp.false_kill_analysis.length > 0 && (
            <div style={{ marginTop: 16, fontSize: 12, color: 'var(--text-secondary)' }}>
              <strong>Top False Kills (would have won):</strong>
              {kp.false_kill_analysis.slice(0, 3).map((fk, i) => (
                <span key={i} style={{ marginLeft: 8 }}>
                  <span className="badge badge-red">{fk.underlying}</span> +${fk.would_pnl.toFixed(0)}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Counterfactual Portfolio */}
      {cf.evaluated > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title">Counterfactual Portfolio</span>
            <span className="badge badge-purple">{cf.evaluated} evaluated</span>
          </div>
          <div className="card-body">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Simulated P&L</div>
                <div className="stat-value" style={{ color: cf.simulated_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
                  {cf.simulated_pnl >= 0 ? '+' : ''}${cf.simulated_pnl.toFixed(2)}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Would Win</div>
                <div className="stat-value" style={{ color: 'var(--yellow)' }}>{cf.would_win}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Would Loss</div>
                <div className="stat-value green">{cf.would_loss}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Win Rate</div>
                <div className="stat-value">{(cf.win_rate * 100).toFixed(1)}%</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MCP Tools Used */}
      <div className="card mb-24">
        <div className="card-header">
          <span className="card-title">MCP Tools Used</span>
          <span className="badge badge-blue">Alpaca MCP</span>
        </div>
        <div className="card-body">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {['get_account_info', 'get_stock_snapshot', 'get_option_chain', 'get_option_snapshot', 'get_all_positions', 'get_orders', 'place_option_order'].map(tool => (
              <span key={tool} className="badge badge-green" style={{ fontSize: 11 }}>
                ✓ {tool}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Strategy Attribution */}
      {Object.keys(p.by_strategy).length > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title">Strategy Attribution</span>
          </div>
          <div className="card-body">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Strategy</th><th>Trades</th><th>Win Rate</th><th>Total P&L</th><th>Avg P&L</th></tr>
                </thead>
                <tbody>
                  {Object.entries(p.by_strategy).map(([strat, stats]) => (
                    <tr key={strat}>
                      <td><span className="badge badge-blue">{strat}</span></td>
                      <td className="mono">{stats.count}</td>
                      <td className="mono" style={{ color: stats.win_rate >= 0.5 ? 'var(--green)' : 'var(--red)' }}>
                        {(stats.win_rate * 100).toFixed(1)}%
                      </td>
                      <td className="mono" style={{ color: stats.total_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {stats.total_pnl >= 0 ? '+' : ''}${stats.total_pnl.toFixed(2)}
                      </td>
                      <td className="mono" style={{ color: stats.avg_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {stats.avg_pnl >= 0 ? '+' : ''}${stats.avg_pnl.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Recent Receipts */}
      {rx.recent_receipts.length > 0 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Recent Decision Receipts</span>
            <span className="badge badge-muted">{rx.total} total</span>
          </div>
          <div className="card-body">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Receipt</th><th>Symbol</th><th>Strategy</th><th>Decision</th><th>Kill Score</th><th>Confidence</th><th>Time</th></tr>
                </thead>
                <tbody>
                  {rx.recent_receipts.map((r, i) => (
                    <tr key={i}>
                      <td className="mono" style={{ fontSize: 11 }}>{r.receipt_id}</td>
                      <td><strong>{r.underlying}</strong></td>
                      <td><span className="badge badge-blue">{r.strategy}</span></td>
                      <td>
                        <span className={`badge ${
                          r.final_decision === 'EXECUTE' ? 'badge-green' :
                          r.final_decision === 'KILLED' ? 'badge-red' :
                          'badge-yellow'
                        }`}>
                          {r.final_decision}
                        </span>
                      </td>
                      <td className="mono">
                        <span className={`badge ${r.kill_score >= 0.6 ? 'badge-green' : r.kill_score >= 0.4 ? 'badge-yellow' : 'badge-red'}`}>
                          {r.kill_score.toFixed(2)}
                        </span>
                      </td>
                      <td className="mono">{(r.confidence * 100).toFixed(0)}%</td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {new Date(r.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
