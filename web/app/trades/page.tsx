'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, OrdersResponse, JournalResponse } from '@/lib/api';

export default function TradesPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<OrdersResponse | null>(null);
  const [journal, setJournal] = useState<JournalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const key = localStorage.getItem('killjoy_api_key');
    if (!key) { router.push('/setup'); return; }
    api.orders().then(setOrders).catch(() => {});
    api.journal().then(setJournal).catch(e => setError(e.message));
  }, [router]);

  return (
    <>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="card mb-24">
        <div className="card-header">
          <span className="card-title">Alpaca Orders</span>
          <span className="badge badge-muted">{orders?.count ?? 0}</span>
        </div>
        <div className="card-body">
          {!orders ? (
            <div className="loading-state"><span className="spinner" /> Loading...</div>
          ) : orders.count === 0 ? (
            <div className="empty-state">
              <div className="icon">&#9654;</div>
              <p>No orders yet</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Type</th>
                    <th>Qty</th>
                    <th>Filled</th>
                    <th>Status</th>
                    <th>Submitted</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.orders.map((o, i) => (
                    <tr key={i}>
                      <td><strong>{o.symbol}</strong></td>
                      <td><span className={`badge ${o.side === 'buy' ? 'badge-green' : 'badge-red'}`}>{o.side}</span></td>
                      <td className="mono">{o.type}</td>
                      <td className="mono">{o.qty}</td>
                      <td className="mono">{o.filled_qty}</td>
                      <td>
                        <span className={`badge ${o.status === 'filled' ? 'badge-green' : o.status === 'canceled' ? 'badge-red' : 'badge-yellow'}`}>
                          {o.status}
                        </span>
                      </td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {o.submitted_at ? new Date(o.submitted_at).toLocaleString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Trade Journal</span>
          <span className="badge badge-muted">{journal?.count ?? 0}</span>
        </div>
        <div className="card-body">
          {!journal ? (
            <div className="loading-state"><span className="spinner" /> Loading...</div>
          ) : journal.count === 0 ? (
            <div className="empty-state">
              <div className="icon">&#9654;</div>
              <p>No journal entries</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Strategy</th>
                    <th>Confidence</th>
                    <th>Kill Score</th>
                    <th>Result</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {journal.entries.map((e, i) => (
                    <tr key={i}>
                      <td><strong>{e.underlying}</strong></td>
                      <td><span className="badge badge-blue">{e.strategy}</span></td>
                      <td className="mono">{(e.confidence * 100).toFixed(0)}%</td>
                      <td className="mono">
                        <span className={`badge ${e.kill_score >= 0.4 ? 'badge-green' : 'badge-red'}`}>
                          {e.kill_score.toFixed(2)}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${e.result === 'open' ? 'badge-yellow' : e.result === 'filled' ? 'badge-green' : 'badge-red'}`}>
                          {e.result}
                        </span>
                      </td>
                      <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {e.timestamp ? new Date(e.timestamp).toLocaleString() : '—'}
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
