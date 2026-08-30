'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, AnalyzeResponse, PaperCycleResponse, CorrelationResponse } from '@/lib/api';

export default function MarketPage() {
  const router = useRouter();
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [cycleResult, setCycleResult] = useState<PaperCycleResponse | null>(null);
  const [correlation, setCorrelation] = useState<CorrelationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [liveLoading, setLiveLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const key = localStorage.getItem('killjoy_api_key');
    if (!key) { router.push('/setup'); return; }
    api.analyze().then(setData).catch(e => setError(e.message));
    api.correlation().then(setCorrelation).catch(() => {});
  }, [router]);

  const runCycle = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.paperCycle();
      setCycleResult(result);
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  };

  const runLiveCycle = async () => {
    if (!confirm('This will submit REAL paper orders to Alpaca. Continue?')) return;
    setLiveLoading(true);
    setError(null);
    try {
      const result = await api.liveCycle();
      setCycleResult(result);
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
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary" onClick={runCycle} disabled={loading}>
              {loading ? <><span className="spinner" /> Running...</> : 'Run Paper Cycle'}
            </button>
            <button className="btn btn-danger" onClick={runLiveCycle} disabled={liveLoading}>
              {liveLoading ? <><span className="spinner" /> Executing...</> : 'Run LIVE Cycle'}
            </button>
            <button className="btn btn-secondary" onClick={() => api.analyze().then(setData)}>
              Refresh Analysis
            </button>
          </div>
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

      {/* Correlation Matrix */}
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

      {cycleResult && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Paper Cycle Results</span>
            <span className="badge badge-green">Complete</span>
          </div>
          <div className="card-body">
            <div className="stats-grid">
              {Object.entries(cycleResult.results).map(([key, val]) => (
                <div className="stat-card" key={key}>
                  <div className="stat-label">{key.replace(/_/g, ' ')}</div>
                  <div className="stat-value" style={{ fontSize: 16 }}>{String(val)}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
