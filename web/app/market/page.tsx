'use client';

import { useEffect, useState } from 'react';
import { api, AnalyzeResponse, PaperCycleResponse } from '@/lib/api';

export default function MarketPage() {
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [cycleResult, setCycleResult] = useState<PaperCycleResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.analyze().then(setData).catch(e => setError(e.message));
  }, []);

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

  return (
    <>
      <div className="page-header">
        <h2>Market Analysis</h2>
        <div className="subtitle">Real-time market thesis and paper cycle</div>
      </div>

      {error && <div className="error">{error}</div>}

      {/* Actions */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Actions</span>
        </div>
        <div className="btn-group">
          <button className="btn btn-primary" onClick={runCycle} disabled={loading}>
            {loading ? 'Running...' : 'Run Paper Cycle'}
          </button>
          <button className="btn btn-secondary" onClick={() => api.analyze().then(setData)}>
            Refresh Analysis
          </button>
        </div>
      </div>

      {/* Analysis */}
      {data && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Market Regime</span>
            <span className="badge badge-purple">Top 5</span>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Regime</th>
                  <th>Confidence</th>
                  <th>Price</th>
                  <th>Thesis</th>
                </tr>
              </thead>
              <tbody>
                {data.analyses.map((a, i) => (
                  <tr key={i}>
                    <td><strong>{a.symbol}</strong></td>
                    <td>
                      <span className={`badge ${
                        a.regime === 'bullish' ? 'badge-green' :
                        a.regime === 'bearish' ? 'badge-red' :
                        'badge-yellow'
                      }`}>
                        {a.regime || '—'}
                      </span>
                    </td>
                    <td>{a.confidence != null ? `${(a.confidence * 100).toFixed(0)}%` : '—'}</td>
                    <td>{a.price ? `$${Number(a.price).toFixed(2)}` : '—'}</td>
                    <td style={{ maxWidth: '300px', fontSize: '12px', color: 'var(--text-dim)' }}>
                      {a.thesis || a.error || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Cycle Results */}
      {cycleResult && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Paper Cycle Results</span>
            <span className="badge badge-green">Complete</span>
          </div>
          <div className="stats-grid">
            {Object.entries(cycleResult.results).map(([key, val]) => (
              <div className="stat-card" key={key}>
                <div className="stat-label">{key.replace(/_/g, ' ')}</div>
                <div className="stat-value">{String(val)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
