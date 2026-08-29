import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'KILLJOY — AI Options Trading',
  description: 'Autonomous AI options trading agent with adversarial kill testing',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="app">
          <Sidebar />
          <main className="main">
            <Topbar />
            <div className="content">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo">KILLJOY</div>
        <div className="sub">AI Options Trading</div>
      </div>
      <nav className="sidebar-nav">
        <a href="/" className="nav-link active">
          <span className="nav-icon">&#9632;</span>
          <span>Dashboard</span>
        </a>
        <a href="/positions" className="nav-link">
          <span className="nav-icon">&#9650;</span>
          <span>Positions</span>
        </a>
        <a href="/market" className="nav-link">
          <span className="nav-icon">&#9670;</span>
          <span>Market</span>
        </a>
        <a href="/trades" className="nav-link">
          <span className="nav-icon">&#9654;</span>
          <span>Trades</span>
        </a>
        <a href="/settings" className="nav-link">
          <span className="nav-icon">&#9881;</span>
          <span>Settings</span>
        </a>
      </nav>
      <div className="sidebar-footer">v0.1.0 &middot; Paper Only</div>
    </aside>
  );
}

function Topbar() {
  return (
    <div className="topbar">
      <div className="topbar-title">Dashboard</div>
      <div className="topbar-actions">
        <span className="badge badge-green">PAPER</span>
      </div>
    </div>
  );
}
