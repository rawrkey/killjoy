'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, CheckResponse, AccountResponse, PositionsResponse } from '@/lib/api';

export default function Dashboard() {
  const router = useRouter();
  const [connected, setConnected] = useState<boolean | null>(null);
  const [account, setAccount] = useState<AccountResponse | null>(null);
  const [positions, setPositions] = useState<PositionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const key = localStorage.getItem('killjoy_api_key');
    if (!key) { router.push('/setup'); return; }

    api.check()
      .then(r => setConnected(r.connected))
      .catch(e => setError(e.message));
    api.account().then(setAccount).catch(() => {});
    api.positions().then(setPositions).catch(() => {});
  }, [router]);

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
          <div className="stat-value" style={{ fontSize: 16, color: 'var(--purple)' }}>ACTIVE</div>
        </div>
      </div>

      {/* Account */}
      {account && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title">Account Overview</span>
            <span className="badge badge-green">{account.status}</span>
          </div>
          <div className="card-body">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Portfolio Value</div>
                <div className="stat-value">${Number(account.portfolio_value).toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Buying Power</div>
                <div className="stat-value accent">${Number(account.buying_power).toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Cash</div>
                <div className="stat-value">${Number(account.cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Day Trades</div>
                <div className="stat-value">{account.daytrade_count}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Positions */}
      <div className="card mb-24">
        <div className="card-header">
          <span className="card-title">Open Positions</span>
          <span className="badge badge-muted">{positions?.count ?? 0}</span>
        </div>
        <div className="card-body">
          {!positions ? (
            <div className="loading-state"><span className="spinner" /> Loading positions...</div>
          ) : positions.count === 0 ? (
            <div className="empty-state">
              <div className="icon">&#9650;</div>
              <p>No open positions</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Qty</th>
                    <th>Entry</th>
                    <th>Current</th>
                    <th>P&L</th>
                    <th>P&L %</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.positions.map((p, i) => (
                    <tr key={i}>
                      <td><strong>{p.symbol}</strong></td>
                      <td><span className={`badge ${p.side === 'long' ? 'badge-green' : 'badge-red'}`}>{p.side}</span></td>
                      <td className="mono">{p.qty}</td>
                      <td className="mono">${Number(p.avg_entry_price).toFixed(2)}</td>
                      <td className="mono">${Number(p.current_price).toFixed(2)}</td>
                      <td className={`mono ${Number(p.unrealized_pl) >= 0 ? 'green' : 'red'}`} style={{ color: Number(p.unrealized_pl) >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {Number(p.unrealized_pl) >= 0 ? '+' : ''}${Number(p.unrealized_pl).toFixed(2)}
                      </td>
                      <td className={`mono ${Number(p.unrealized_plpc) >= 0 ? 'green' : 'red'}`} style={{ color: Number(p.unrealized_plpc) >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {Number(p.unrealized_plpc) >= 0 ? '+' : ''}{(Number(p.unrealized_plpc) * 100).toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Pipeline */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Autonomous Pipeline</span>
          <span className="badge badge-blue">9 STAGES</span>
        </div>
        <div className="card-body">
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 2, color: 'var(--text-secondary)', overflowX: 'auto' }}>
            <div><span style={{ color: 'var(--cyan)' }}>Market Data</span> &rarr; <span style={{ color: 'var(--accent)' }}>Analyst</span> &rarr; <span style={{ color: 'var(--purple)' }}>Strategy</span> &rarr; <span style={{ color: 'var(--red)' }}>Kill Agent</span> &rarr; <span style={{ color: 'var(--yellow)' }}>Portfolio</span> &rarr; <span style={{ color: 'var(--green)' }}>Risk Engine</span> &rarr; <span style={{ color: 'var(--accent)' }}>Execution</span> &rarr; <span style={{ color: 'var(--cyan)' }}>Alpaca</span></div>
            <div style={{ color: 'var(--text-muted)', marginTop: 8 }}>
              &#8615; Position Monitor &larr; Trade Journal &larr; Postmortem
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
