'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function SetupPage() {
  const router = useRouter();
  const [apiUrl, setApiUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [controlSecret, setControlSecret] = useState('');
  const [saved, setSaved] = useState(false);
  const [hasEnvUrl, setHasEnvUrl] = useState(false);

  useEffect(() => {
    // Check if env var is set (Vercel deployment)
    const envUrl = process.env.NEXT_PUBLIC_API_URL;
    if (envUrl) {
      setHasEnvUrl(true);
      setApiUrl(envUrl);
    } else {
      const url = localStorage.getItem('killjoy_api_url');
      if (url) setApiUrl(url);
    }
    const key = localStorage.getItem('killjoy_api_key');
    const secret = localStorage.getItem('killjoy_secret_key');
    if (key) setApiKey(key);
    if (secret) setSecretKey(secret);
    const control = localStorage.getItem('killjoy_control_secret');
    if (control) setControlSecret(control);
    // Auto-redirect if we have everything
    if ((envUrl || localStorage.getItem('killjoy_api_url')) && key && secret) {
      router.push('/');
    }
  }, [router]);

  const handleSave = () => {
    localStorage.setItem('killjoy_api_url', apiUrl);
    localStorage.setItem('killjoy_api_key', apiKey);
    localStorage.setItem('killjoy_secret_key', secretKey);
    if (controlSecret) localStorage.setItem('killjoy_control_secret', controlSecret);
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

          {hasEnvUrl && (
            <div className="alert alert-info" style={{ marginBottom: 16 }}>
              Backend URL configured via environment variable. You can override it below.
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Backend API URL</label>
            <input
              className="form-input"
              value={apiUrl}
              onChange={e => setApiUrl(e.target.value)}
              placeholder="https://your-backend.railway.app"
              readOnly={hasEnvUrl}
              style={hasEnvUrl ? { opacity: 0.6 } : {}}
            />
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              {hasEnvUrl ? 'Set via NEXT_PUBLIC_API_URL env var' : 'Where your Python backend is running'}
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

          <div className="form-group">
            <label className="form-label">Control Secret <span style={{ color: 'var(--text-muted)' }}>(optional)</span></label>
            <input
              className="form-input"
              value={controlSecret}
              onChange={e => setControlSecret(e.target.value)}
              placeholder="Set KILLJOY_CONTROL_SECRET on backend"
              type="password"
            />
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              Required only if KILLJOY_CONTROL_SECRET env var is set on the backend
            </div>
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
