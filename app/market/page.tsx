'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, AnalyzeResponse, CorrelationResponse } from '@/lib/api';

export default function MarketPage() {
  const router = useRouter();
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [correlation, setCorrelation] = useState<CorrelationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [liveLoading, setLiveLoading] = useState(false);
  const [marketOpen, setMarketOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cycleMessage, setCycleMessage] = useState<string | null>(null);

  useEffect(() => {
    const key = localStorage.getItem('killjoy_api_key');
    if (!key) { router.push('/setup'); return; }
    api.analyze().then(setData).catch(e => setError(e.message));
    api.correlation().then(setCorrelation).catch(() => {});
  }, [router]);

  useEffect(() => {
    const checkMarket = () => {
      const now = new Date();
      const et = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }));
      const day = et.getDay();
      const h = et.getHours();
      const m = et.getMinutes();
      const mins = h * 60 + m;
      const isOpen = day >= 1 && day <= 5 && mins >= 570 && mins < 960;
      setMarketOpen(isOpen);
    };
    checkMarket();
    const id = setInterval(checkMarket, 30000);
    return () => clearInterval(id);
  }, []);

  const runCycle = async () => {
    setLoading(true);
    setError(null);
    setCycleMessage(null);
    try {
      await api.paperCycle();
      setCycleMessage('Cycle complete. View report on Reports page.');
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  };

  const runLiveCycle = async () => {
    if (!confirm('This will submit REAL paper orders to Alpaca. Continue?')) return;
    setLiveLoading(true);
    setError(null);
    setCycleMessage(null);
    try {
      await api.liveCycle();
      setCycleMessage('Live cycle complete. View report on Reports page.');
    } catch (e: any) {
      setError(e.message);
    }
    setLiveLoading(false);
  };

  return (
    <>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="card mb-24">
        <div className="card-header">
          <span className="card-title">Actions</span>
        </div>
        <div className="card-body">
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button className="btn btn-primary" onClick={runCycle} disabled={loading}>
              {loading ? <><span className="spinner" /> Running...</> : 'Run Paper Cycle'}
            </button>
            <button
              className="btn btn-danger"
              onClick={runLiveCycle}
              disabled={liveLoading || !marketOpen}
              title={!marketOpen ? 'Market is closed (Mon-Fri 9:30 AM - 4:00 PM ET)' : ''}
            >
              {liveLoading ? <><span className="spinner" /> Executing...</> : 'Run LIVE Cycle'}
            </button>
            <button className="btn btn-secondary" onClick={() => api.analyze().then(setData)}>
              Refresh Analysis
            </button>
            <span style={{ fontSize: 11, color: marketOpen ? 'var(--green)' : 'var(--text-muted)', marginLeft: 4 }}>
              {marketOpen ? 'Market OPEN' : 'Market CLOSED'}
            </span>
          </div>
          {cycleMessage && (
            <div style={{ marginTop: 10, fontSize: 12, color: 'var(--green)' }}>{cycleMessage}</div>
          )}
        </div>
      </div>

      <div className="card mb-24">
        <div className="card-header">
          <span className="card-title">LLM Market Analysis</span>
          <span className="badge badge-purple">Top 5</span>
        </div>
        <div className="card-body">
          {!data ? (
            <div className="loading-state"><span className="spinner" /> Analyzing market...</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Regime</th>
                    <th>Confidence</th>
                    <th>Price</th>
                    <th>Thesis</th>
                    <th>Observations</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.analyses ?? []).map((a, i) => (
                    <tr key={i}>
                      <td><strong>{a.symbol}</strong></td>
                      <td>
                        <span className={`badge ${
                          a.regime?.includes('up') || a.regime?.includes('bull') ? 'badge-green' :
                          a.regime?.includes('down') || a.regime?.includes('bear') ? 'badge-red' :
                          'badge-yellow'
                        }`}>
                          {a.regime || '—'}
                        </span>
                      </td>
                      <td className="mono">{a.confidence != null ? `${(a.confidence * 100).toFixed(0)}%` : '—'}</td>
                      <td className="mono">{a.price ? `$${Number(a.price).toFixed(2)}` : '—'}</td>
                      <td style={{ maxWidth: 280, fontSize: 12, color: 'var(--text-secondary)' }}>
                        {a.thesis || a.error || '—'}
                      </td>
                      <td style={{ maxWidth: 200, fontSize: 11, color: 'var(--text-muted)' }}>
                        {a.observations?.slice(0, 2).join('; ') || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {correlation?.matrix?.symbols && correlation.matrix.symbols.length > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title">Portfolio Correlation</span>
            <span className={`badge ${correlation.risk.risk_level === 'low' ? 'badge-green' : correlation.risk.risk_level === 'high' ? 'badge-red' : 'badge-yellow'}`}>
              {correlation.risk.risk_level} risk
            </span>
          </div>
          <div className="card-body">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th></th>
                    {correlation.matrix.symbols.map(s => (
                      <th key={s} className="mono">{s}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(correlation.matrix.symbols ?? []).map((row, ri) => (
                    <tr key={ri}>
                      <td><strong className="mono">{row}</strong></td>
                      {(correlation.matrix.matrix[ri] ?? []).map((val, ci) => (
                        <td key={ci} className="mono" style={{
                          fontSize: 12,
                          color: ri === ci ? 'var(--text-muted)' :
                            val > 0.7 ? 'var(--red)' :
                            val > 0.4 ? 'var(--yellow)' :
                            'var(--green)',
                          background: ri === ci ? 'transparent' :
                            val > 0.7 ? 'var(--red-bg)' :
                            val > 0.4 ? 'var(--yellow-bg)' :
                            'var(--green-bg)',
                        }}>
                          {val.toFixed(2)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {correlation.risk.correlated_pairs && correlation.risk.correlated_pairs.length > 0 && (
              <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-secondary)' }}>
                <strong>High correlations:</strong>
                {correlation.risk.correlated_pairs.map(([a, b, c], i) => (
                  <span key={i} style={{ marginLeft: 8 }}>
                    <span className="badge badge-red">{a}/{b}</span> {c.toFixed(2)}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
