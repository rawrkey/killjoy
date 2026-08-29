'use client';

import { useEffect, useState } from 'react';
import { api, PositionsResponse } from '@/lib/api';

export default function PositionsPage() {
  const [data, setData] = useState<PositionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.positions().then(setData).catch(e => setError(e.message));
  }, []);

  return (
    <>
      <div className="page-header">
        <h2>Positions</h2>
        <div className="subtitle">Open positions across all accounts</div>
      </div>

      {error && <div className="error">{error}</div>}

      {data && data.count === 0 && (
        <div className="card">
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-dim)' }}>
            No open positions
          </div>
        </div>
      )}

      {data && data.count > 0 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">All Positions</span>
            <span className="badge badge-blue">{data.count}</span>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Qty</th>
                  <th>Avg Entry</th>
                  <th>Current</th>
                  <th>Market Value</th>
                  <th>P&L</th>
                  <th>P&L %</th>
                </tr>
              </thead>
              <tbody>
                {data.positions.map((p, i) => (
                  <tr key={i}>
                    <td><strong>{p.symbol}</strong></td>
                    <td>
                      <span className={`badge ${p.side === 'long' ? 'badge-green' : 'badge-red'}`}>
                        {p.side}
                      </span>
                    </td>
                    <td>{p.qty}</td>
                    <td>${Number(p.avg_entry_price).toFixed(2)}</td>
                    <td>${Number(p.current_price).toFixed(2)}</td>
                    <td>${Number(p.market_value).toFixed(2)}</td>
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
    </>
  );
}
