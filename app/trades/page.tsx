'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, OrdersResponse, JournalResponse, RejectionAnalytics } from '@/lib/api';

export default function TradesPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<OrdersResponse | null>(null);
  const [journal, setJournal] = useState<JournalResponse | null>(null);
  const [rejections, setRejections] = useState<RejectionAnalytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const key = localStorage.getItem('killjoy_api_key');
    if (!key) { router.push('/setup'); return; }
    api.orders().then(setOrders).catch(() => {});
    api.journal().then(setJournal).catch(e => setError(e.message));
    api.rejections().then(setRejections).catch(() => {});
  }, [router]);

  return (
    <>
      {error && <div className="alert alert-error">{error}</div>}

      {/* Rejection Analytics */}
      {rejections && rejections.total_rejected > 0 && (
        <div className="card mb-24">
          <div className="card-header">
            <span className="card-title">Why Not Trade?</span>
            <span className="badge badge-red">{rejections.total_rejected} rejected</span>
          </div>
          <div className="card-body">
            <div className="stats-grid mb-16">
              <div className="stat-card">
                <div className="stat-label">Kill Agent</div>
                <div className="stat-value red">{rejections.by_stage?.kill_agent ?? 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Portfolio</div>
                <div className="stat-value" style={{ color: 'var(--yellow)' }}>{rejections.by_stage?.portfolio ?? 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Risk Engine</div>
                <div className="stat-value" style={{ color: 'var(--purple)' }}>{rejections.by_stage?.risk_engine ?? 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Avg Kill Score</div>
                <div className="stat-value">{rejections.avg_kill_score.toFixed(2)}</div>
              </div>
            </div>
            {rejections.top_reasons && rejections.top_reasons.length > 0 && (
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                <strong>Top rejection reasons:</strong>
                {rejections.top_reasons.slice(0, 3).map((r, i) => (
                  <span key={i} style={{ marginLeft: 8 }}>
                    <span className="badge badge-muted">{r.reason}</span> ({r.count})
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

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
                    <th>P&L</th>
                    <th>Result</th>
                    <th>Thesis</th>
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
                        <span className={`badge ${e.kill_score >= 0.6 ? 'badge-green' : e.kill_score >= 0.4 ? 'badge-yellow' : 'badge-red'}`}>
                          {e.kill_score.toFixed(2)}
                        </span>
                      </td>
                      <td className="mono" style={{ color: e.realized_pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {e.realized_pnl >= 0 ? '+' : ''}${e.realized_pnl.toFixed(2)}
                      </td>
                      <td>
                        <span className={`badge ${e.result === 'open' ? 'badge-yellow' : e.result === 'filled' ? 'badge-green' : 'badge-red'}`}>
                          {e.result}
                        </span>
                      </td>
                      <td style={{ maxWidth: 200, fontSize: 11, color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {e.thesis || '—'}
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
