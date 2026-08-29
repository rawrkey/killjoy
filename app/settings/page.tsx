'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, CheckResponse, ParamsResponse } from '@/lib/api';

export default function SettingsPage() {
  const router = useRouter();
  const [health, setHealth] = useState<CheckResponse | null>(null);
  const [params, setParams] = useState<ParamsResponse | null>(null);
  const [apiUrl, setApiUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const key = localStorage.getItem('killjoy_api_key');
    if (!key) { router.push('/setup'); return; }
    setApiUrl(localStorage.getItem('killjoy_api_url') || 'http://localhost:8000');
    setApiKey(key);
    setSecretKey(localStorage.getItem('killjoy_secret_key') || '');
    api.check().then(setHealth).catch(() => {});
    api.params().then(setParams).catch(() => {});
  }, [router]);

  const handleSave = () => {
    localStorage.setItem('killjoy_api_url', apiUrl);
    localStorage.setItem('killjoy_api_key', apiKey);
    localStorage.setItem('killjoy_secret_key', secretKey);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleDisconnect = () => {
    localStorage.removeItem('killjoy_api_url');
    localStorage.removeItem('killjoy_api_key');
    localStorage.removeItem('killjoy_secret_key');
    router.push('/setup');
  };

  const paramLabels: Record<string, { label: string; desc: string; format: (v: number) => string }> = {
    min_dte: { label: 'Min DTE', desc: 'Minimum days to expiration', format: v => `${v} days` },
    max_dte: { label: 'Max DTE', desc: 'Maximum days to expiration', format: v => `${v} days` },
    min_reward_risk: { label: 'Min Reward/Risk', desc: 'Minimum reward-to-risk ratio', format: v => v.toFixed(1) },
    min_confidence: { label: 'Min Confidence', desc: 'Minimum strategy confidence', format: v => v.toFixed(2) },
    max_loss_per_trade: { label: 'Max Loss/Trade', desc: 'Maximum loss per single trade', format: v => `$${v.toFixed(0)}` },
    max_daily_loss: { label: 'Daily Loss Limit', desc: 'Maximum total daily loss', format: v => `$${v.toFixed(0)}` },
    max_positions: { label: 'Max Positions', desc: 'Maximum concurrent positions', format: v => `${v}` },
    max_options_exposure: { label: 'Options Exposure', desc: 'Maximum total options exposure', format: v => `$${v.toFixed(0)}` },
  };

  return (
    <>
      {/* Connection */}
      <div className="card mb-24">
        <div className="card-header">
          <span className="card-title">Alpaca Connection</span>
          <span className={`badge ${health?.connected ? 'badge-green' : 'badge-red'}`}>
            {health?.connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <div className="card-body">
          <div className="form-group">
            <label className="form-label">Backend API URL</label>
            <input className="form-input" value={apiUrl} onChange={e => setApiUrl(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Alpaca API Key</label>
            <input className="form-input" value={apiKey} onChange={e => setApiKey(e.target.value)} type="password" />
          </div>
          <div className="form-group">
            <label className="form-label">Alpaca Secret Key</label>
            <input className="form-input" value={secretKey} onChange={e => setSecretKey(e.target.value)} type="password" />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary" onClick={handleSave}>Save</button>
            <button className="btn btn-danger" onClick={handleDisconnect}>Disconnect</button>
          </div>
          {saved && <div className="alert alert-success" style={{ marginTop: 12 }}>Settings saved</div>}
        </div>
      </div>

      {/* Live Risk Engine Parameters */}
      <div className="card mb-24">
        <div className="card-header">
          <span className="card-title">Risk Engine Parameters</span>
          <span className="badge badge-green">Live</span>
        </div>
        <div className="card-body">
          {!params ? (
            <div className="loading-state"><span className="spinner" /> Loading params...</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Parameter</th><th>Value</th><th>Description</th></tr></thead>
                <tbody>
                  {Object.entries(params.params).map(([key, val]) => {
                    const meta = paramLabels[key];
                    return (
                      <tr key={key}>
                        <td><strong>{meta?.label ?? key}</strong></td>
                        <td className="mono" style={{ color: 'var(--accent)' }}>
                          {meta?.format(val) ?? String(val)}
                        </td>
                        <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                          {meta?.desc ?? '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          {params && params.history && params.history.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
                Recent Changes
              </div>
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Parameter</th><th>From</th><th>To</th><th>Confidence</th><th>Applied</th></tr></thead>
                  <tbody>
                    {params.history && params.history.slice(-5).reverse().map((h, i) => (
                      <tr key={i}>
                        <td className="mono">{h.parameter}</td>
                        <td className="mono">{h.old_value}</td>
                        <td className="mono" style={{ color: 'var(--accent)' }}>{h.recommended_value}</td>
                        <td className="mono">{(h.confidence * 100).toFixed(0)}%</td>
                        <td>
                          <span className={`badge ${h.applied ? 'badge-green' : 'badge-muted'}`}>
                            {h.applied ? 'Applied' : 'Pending'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Strategies */}
      <div className="card mb-24">
        <div className="card-header">
          <span className="card-title">Strategies</span>
          <span className="badge badge-blue">5</span>
        </div>
        <div className="card-body">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Strategy</th><th>Type</th><th>Regime</th><th>Status</th></tr></thead>
              <tbody>
                <tr><td>Long Call</td><td>Directional</td><td>Strong Uptrend</td><td><span className="badge badge-green">Active</span></td></tr>
                <tr><td>Long Put</td><td>Directional</td><td>Strong Downtrend</td><td><span className="badge badge-green">Active</span></td></tr>
                <tr><td>Bull Call Spread</td><td>Spread</td><td>Mild Uptrend</td><td><span className="badge badge-green">Active</span></td></tr>
                <tr><td>Bear Put Spread</td><td>Spread</td><td>Mild Downtrend</td><td><span className="badge badge-green">Active</span></td></tr>
                <tr><td>Iron Condor</td><td>Neutral</td><td>Sideways</td><td><span className="badge badge-green">Active</span></td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* MCP */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">MCP Server</span>
          <span className="badge badge-yellow">Prepared</span>
        </div>
        <div className="card-body">
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
            <p>Alpaca MCP server configured for AI-agent tool access.</p>
            <p style={{ marginTop: 8 }}><strong>Toolsets:</strong> account, trading, assets, stock-data, options-data, news</p>
            <p style={{ marginTop: 8 }}><strong>Command:</strong> <code style={{ color: 'var(--accent)' }}>uvx alpaca-mcp-server</code></p>
          </div>
        </div>
      </div>
    </>
  );
}
