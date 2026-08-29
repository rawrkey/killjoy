'use client';

import { useEffect, useState } from 'react';
import { api, CheckResponse, AccountResponse, PositionsResponse } from '@/lib/api';

export default function Dashboard() {
  const [connected, setConnected] = useState<boolean | null>(null);
  const [account, setAccount] = useState<AccountResponse | null>(null);
  const [positions, setPositions] = useState<PositionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.check().then(r => setConnected(r.connected)).catch(e => setError(e.message));
    api.account().then(setAccount).catch(() => {});
    api.positions().then(setPositions).catch(() => {});
  }, []);

  return (
    <>
      <div className="page-header">
        <h2>Dashboard</h2>
        <div className="subtitle">KILLJOY Autonomous Options Trading Agent</div>
      </div>

      {error && <div className="error">{error}</div>}

      {/* Connection Status */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">System Status</span>
          <span>
            <span className={`status-dot ${connected === true ? 'online' : connected === false ? 'offline' : 'loading'}`} />
            {connected === true ? 'Connected' : connected === false ? 'Disconnected' : 'Checking...'}
          </span>
        </div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Alpaca</div>
            <div className={`stat-value ${connected ? 'positive' : 'negative'}`}>
              {connected ? 'LIVE' : 'OFFLINE'}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Mode</div>
            <div className="stat-value accent">PAPER</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Trading</div>
            <div className="stat-value positive">OPTIONS</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Risk Engine</div>
            <div className="stat-value positive">ACTIVE</div>
          </div>
        </div>
      </div>

      {/* Account */}
      {account && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Account</span>
            <span className="badge badge-green">{account.status}</span>
          </div>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Portfolio Value</div>
              <div className="stat-value">${Number(account.portfolio_value).toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Buying Power</div>
              <div className="stat-value accent">${Number(account.buying_power).toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Cash</div>
              <div className="stat-value">${Number(account.cash).toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Day Trades</div>
              <div className="stat-value">{account.daytrade_count}</div>
            </div>
          </div>
        </div>
      )}

      {/* Positions */}
      {positions && positions.count > 0 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Open Positions</span>
            <span className="badge badge-blue">{positions.count}</span>
          </div>
          <div className="table-container">
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
                    <td>{p.qty}</td>
                    <td>${Number(p.avg_entry_price).toFixed(2)}</td>
                    <td>${Number(p.current_price).toFixed(2)}</td>
                    <td className={Number(p.unrealized_pl) >= 0 ? 'positive' : 'negative'}>
                      ${Number(p.unrealized_pl).toFixed(2)}
                    </td>
                    <td className={Number(p.unrealized_plpc) >= 0 ? 'positive' : 'negative'}>
                      {(Number(p.unrealized_plpc) * 100).toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {positions && positions.count === 0 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Open Positions</span>
            <span className="badge badge-yellow">0</span>
          </div>
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-dim)' }}>
            No open positions
          </div>
        </div>
      )}

      {/* Architecture */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Pipeline</span>
        </div>
        <div className="arch-diagram">
{`Market Data ──► Market Analyst ──► Strategy Agent ──► Kill Agent ──► Portfolio Check ──► Risk Engine ──► Execution ──► Alpaca Paper
      ↑                                                                                          │
      └──────────────────────── Position Monitor ◄── Trade Journal ◄── Postmortem ◄──────────────┘`}
        </div>
      </div>
    </>
  );
}
