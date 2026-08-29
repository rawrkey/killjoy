'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, CheckResponse } from '@/lib/api';

export default function SettingsPage() {
  const router = useRouter();
  const [health, setHealth] = useState<CheckResponse | null>(null);
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

      {/* Risk Engine */}
      <div className="card mb-24">
        <div className="card-header">
          <span className="card-title">Risk Engine Parameters</span>
          <span className="badge badge-green">8 Gates</span>
        </div>
        <div className="card-body">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Gate</th><th>Limit</th><th>Description</th></tr></thead>
              <tbody>
                <tr><td>Max Risk/Trade</td><td className="mono">$500</td><td>Maximum loss per single trade</td></tr>
                <tr><td>Daily Loss Limit</td><td className="mono">$1,000</td><td>Maximum total daily loss</td></tr>
                <tr><td>Options Exposure</td><td className="mono">$10,000</td><td>Maximum total options exposure</td></tr>
                <tr><td>Underlying Exposure</td><td className="mono">$3,000</td><td>Maximum per-underlying exposure</td></tr>
                <tr><td>Min Reward/Risk</td><td className="mono">1.0</td><td>Minimum reward-to-risk ratio</td></tr>
                <tr><td>Min Buying Power</td><td className="mono">$500</td><td>Minimum required buying power</td></tr>
                <tr><td>Max Positions</td><td className="mono">10</td><td>Maximum concurrent positions</td></tr>
                <tr><td>Min Confidence</td><td className="mono">0.3</td><td>Minimum strategy confidence</td></tr>
              </tbody>
            </table>
          </div>
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
              <thead><tr><th>Strategy</th><th>Type</th><th>Status</th></tr></thead>
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
