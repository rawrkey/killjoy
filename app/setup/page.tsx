'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function SetupPage() {
  const router = useRouter();
  const [apiUrl, setApiUrl] = useState('http://localhost:8000');
  const [apiKey, setApiKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const url = localStorage.getItem('killjoy_api_url');
    const key = localStorage.getItem('killjoy_api_key');
    const secret = localStorage.getItem('killjoy_secret_key');
    if (url) setApiUrl(url);
    if (key) setApiKey(key);
    if (secret) setSecretKey(secret);
    if (url && key && secret) router.push('/');
  }, [router]);

  const handleSave = () => {
    localStorage.setItem('killjoy_api_url', apiUrl);
    localStorage.setItem('killjoy_api_key', apiKey);
    localStorage.setItem('killjoy_secret_key', secretKey);
    setSaved(true);
    setTimeout(() => router.push('/'), 800);
  };

  return (
    <div style={{ maxWidth: 480, margin: '60px auto' }}>
      <div className="card">
        <div className="card-header">
          <span className="card-title">KILLJOY Setup</span>
        </div>
        <div className="card-body">
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 20 }}>
            Enter your Alpaca paper-trading credentials and the backend API URL.
            Keys are stored in your browser only — never sent anywhere except your backend.
          </p>

          <div className="form-group">
            <label className="form-label">Backend API URL</label>
            <input
              className="form-input"
              value={apiUrl}
              onChange={e => setApiUrl(e.target.value)}
              placeholder="http://localhost:8000"
            />
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              Where your Python backend is running
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Alpaca API Key</label>
            <input
              className="form-input"
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              placeholder="PK..."
              type="password"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Alpaca Secret Key</label>
            <input
              className="form-input"
              value={secretKey}
              onChange={e => setSecretKey(e.target.value)}
              placeholder="..."
              type="password"
            />
          </div>

          {saved && (
            <div className="alert alert-success" style={{ marginBottom: 16 }}>
              Saved! Redirecting...
            </div>
          )}

          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={!apiUrl || !apiKey || !secretKey}
            style={{ width: '100%', justifyContent: 'center' }}
          >
            Save &amp; Continue
          </button>

          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 12, textAlign: 'center' }}>
            You can change these later in Settings
          </div>
        </div>
      </div>
    </div>
  );
}
