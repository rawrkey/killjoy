'use client';

import { useEffect, useState } from 'react';
import { api, OrdersResponse, JournalResponse } from '@/lib/api';

export default function TradesPage() {
  const [orders, setOrders] = useState<OrdersResponse | null>(null);
  const [journal, setJournal] = useState<JournalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.orders().then(setOrders).catch(() => {});
    api.journal().then(setJournal).catch(e => setError(e.message));
  }, []);

  return (
    <>
      <div className="page-header">
        <h2>Trade Log</h2>
        <div className="subtitle">Orders and journal entries</div>
      </div>

      {error && <div className="error">{error}</div>}

      {/* Orders */}
      {orders && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Alpaca Orders</span>
            <span className="badge badge-blue">{orders.count}</span>
          </div>
          {orders.count === 0 ? (
            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-dim)' }}>
              No orders yet
            </div>
          ) : (
            <div className="table-container">
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
                      <td>
                        <span className={`badge ${o.side === 'buy' ? 'badge-green' : 'badge-red'}`}>
                          {o.side}
                        </span>
                      </td>
                      <td>{o.type}</td>
                      <td>{o.qty}</td>
                      <td>{o.filled_qty}</td>
                      <td>
                        <span className={`badge ${
                          o.status === 'filled' ? 'badge-green' :
                          o.status === 'canceled' ? 'badge-red' :
                          'badge-yellow'
                        }`}>
                          {o.status}
                        </span>
                      </td>
                      <td style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                        {o.submitted_at ? new Date(o.submitted_at).toLocaleString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Journal */}
      {journal && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Trade Journal</span>
            <span className="badge badge-purple">{journal.count}</span>
          </div>
          {journal.count === 0 ? (
            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-dim)' }}>
              No journal entries
            </div>
          ) : (
            <div className="table-container">
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
                      <td>{(e.confidence * 100).toFixed(0)}%</td>
                      <td>
                        <span className={`badge ${e.kill_score >= 0.4 ? 'badge-green' : 'badge-red'}`}>
                          {e.kill_score.toFixed(2)}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${
                          e.result === 'open' ? 'badge-yellow' :
                          e.result === 'filled' ? 'badge-green' :
                          'badge-red'
                        }`}>
                          {e.result}
                        </span>
                      </td>
                      <td style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                        {e.timestamp ? new Date(e.timestamp).toLocaleString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </>
  );
}
