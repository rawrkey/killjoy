'use client';

import { useEffect, useState } from 'react';
import { api, CheckResponse } from '@/lib/api';

export default function SettingsPage() {
  const [health, setHealth] = useState<CheckResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.check().then(setHealth).catch(e => setError(e.message));
  }, []);

  return (
    <>
      <div className="page-header">
        <h2>Settings</h2>
        <div className="subtitle">Configuration and risk parameters</div>
      </div>

      {error && <div className="error">{error}</div>}

      {/* Connection */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Alpaca Connection</span>
          <span className={`badge ${health?.connected ? 'badge-green' : 'badge-red'}`}>
            {health?.connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">API</div>
            <div className="stat-value" style={{ fontSize: '14px' }}>
              {health?.connected ? 'paper-api.alpaca.markets' : 'Not configured'}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Mode</div>
            <div className="stat-value accent">Paper Only</div>
          </div>
        </div>
      </div>

      {/* Risk Engine */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Risk Engine Parameters</span>
          <span className="badge badge-green">8 Gates</span>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Gate</th>
                <th>Limit</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>Max Risk/Trade</td><td>$500</td><td>Maximum loss per single trade</td></tr>
              <tr><td>Daily Loss Limit</td><td>$1,000</td><td>Maximum total daily loss</td></tr>
              <tr><td>Options Exposure</td><td>$10,000</td><td>Maximum total options exposure</td></tr>
              <tr><td>Underlying Exposure</td><td>$3,000</td><td>Maximum per-underlying exposure</td></tr>
              <tr><td>Min Reward/Risk</td><td>1.0</td><td>Minimum reward-to-risk ratio</td></tr>
              <tr><td>Min Buying Power</td><td>$500</td><td>Minimum required buying power</td></tr>
              <tr><td>Max Positions</td><td>10</td><td>Maximum concurrent positions</td></tr>
              <tr><td>Min Confidence</td><td>0.3</td><td>Minimum strategy confidence</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Strategies */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Strategies</span>
          <span className="badge badge-blue">5</span>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr><th>Strategy</th><th>Type</th><th>Status</th></tr>
            </thead>
            <tbody>
              <tr><td>Long Call</td><td>Directional</td><td><span className="badge badge-green">Active</span></td></tr>
              <tr><td>Long Put</td><td>Directional</td><td><span className="badge badge-green">Active</span></td></tr>
              <tr><td>Bull Call Spread</td><td>Spread</td><td><span className="badge badge-green">Active</span></td></tr>
              <tr><td>Bear Put Spread</td><td>Spread</td><td><span className="badge badge-green">Active</span></td></tr>
              <tr><td>Iron Condor</td><td>Neutral</td><td><span className="badge badge-green">Active</span></td></tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Universe */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Market Universe</span>
          <span className="badge badge-purple">10</span>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {['SPY','QQQ','IWM','AAPL','MSFT','NVDA','AMZN','META','GOOGL','TSLA'].map(s => (
            <span key={s} className="badge badge-blue" style={{ fontSize: '12px', padding: '5px 10px' }}>{s}</span>
          ))}
        </div>
      </div>

      {/* MCP Server */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">MCP Server</span>
          <span className="badge badge-yellow">Prepared</span>
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-dim)', lineHeight: 1.8 }}>
          <p>Alpaca MCP server is configured for AI-agent tool access.</p>
          <p style={{ marginTop: '8px' }}>
            <strong>Toolsets:</strong> account, trading, assets, stock-data, options-data, news
          </p>
          <p style={{ marginTop: '8px' }}>
            <strong>Command:</strong> <code style={{ color: 'var(--accent)' }}>uvx alpaca-mcp-server</code>
          </p>
        </div>
      </div>
    </>
  );
}
