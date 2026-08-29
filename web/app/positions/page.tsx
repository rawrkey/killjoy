'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, PositionsResponse } from '@/lib/api';

export default function PositionsPage() {
  const router = useRouter();
  const [data, setData] = useState<PositionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const key = localStorage.getItem('killjoy_api_key');
    if (!key) { router.push('/setup'); return; }
    api.positions().then(setData).catch(e => setError(e.message));
  }, [router]);

  return (
    <>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <div className="card-header">
          <span className="card-title">All Positions</span>
          <span className="badge badge-muted">{data?.count ?? 0}</span>
        </div>
        <div className="card-body">
          {!data ? (
            <div className="loading-state"><span className="spinner" /> Loading...</div>
          ) : data.count === 0 ? (
            <div className="empty-state">
              <div className="icon">&#9650;</div>
              <p>No open positions</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Qty</th>
                    <th>Avg Entry</th>
                    <th>Current</th>
                    <th>Market Value</th>
                    <th>Unrealized P&L</th>
                    <th>P&L %</th>
                  </tr>
                </thead>
                <tbody>
                  {data.positions.map((p, i) => (
                    <tr key={i}>
                      <td><strong>{p.symbol}</strong></td>
                      <td><span className={`badge ${p.side === 'long' ? 'badge-green' : 'badge-red'}`}>{p.side}</span></td>
                      <td className="mono">{p.qty}</td>
                      <td className="mono">${Number(p.avg_entry_price).toFixed(2)}</td>
                      <td className="mono">${Number(p.current_price).toFixed(2)}</td>
                      <td className="mono">${Number(p.market_value).toFixed(2)}</td>
                      <td className="mono" style={{ color: Number(p.unrealized_pl) >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {Number(p.unrealized_pl) >= 0 ? '+' : ''}${Number(p.unrealized_pl).toFixed(2)}
                      </td>
                      <td className="mono" style={{ color: Number(p.unrealized_plpc) >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {Number(p.unrealized_plpc) >= 0 ? '+' : ''}{(Number(p.unrealized_plpc) * 100).toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
