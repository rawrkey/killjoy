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
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>KILLJOY</h1>
        <div className="tagline">AI OPTIONS TRADING</div>
      </div>
      <nav>
        <a href="/" className="nav-item active">
          <span className="icon">&#9632;</span>
          <span>Dashboard</span>
        </a>
        <a href="/positions" className="nav-item">
          <span className="icon">&#9650;</span>
          <span>Positions</span>
        </a>
        <a href="/market" className="nav-item">
          <span className="icon">&#9670;</span>
          <span>Market</span>
        </a>
        <a href="/trades" className="nav-item">
          <span className="icon">&#9654;</span>
          <span>Trade Log</span>
        </a>
        <a href="/settings" className="nav-item">
          <span className="icon">&#9881;</span>
          <span>Settings</span>
        </a>
      </nav>
      <div className="sidebar-footer">
        v0.1.0 &middot; Paper Only
      </div>
    </aside>
  );
}
