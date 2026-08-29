'use client';

import { usePathname } from 'next/navigation';
import './globals.css';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: '\u25A0' },
  { href: '/positions', label: 'Positions', icon: '\u25B2' },
  { href: '/market', label: 'Market', icon: '\u25C6' },
  { href: '/trades', label: 'Trades', icon: '\u25B6' },
  { href: '/settings', label: 'Settings', icon: '\u2699' },
];

const PAGE_TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/positions': 'Positions',
  '/market': 'Market Analysis',
  '/trades': 'Trade Log',
  '/settings': 'Settings',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <title>KILLJOY — AI Options Trading</title>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const title = PAGE_TITLES[pathname] || 'Dashboard';

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">KILLJOY</div>
          <div className="sub">AI Options Trading</div>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map(item => (
            <a
              key={item.href}
              href={item.href}
              className={`nav-link ${pathname === item.href ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </a>
          ))}
        </nav>
        <div className="sidebar-footer">v0.1.0 &middot; Paper Only</div>
      </aside>
      <main className="main">
        <div className="topbar">
          <div className="topbar-title">{title}</div>
          <div className="topbar-actions">
            <span className="badge badge-green">PAPER</span>
          </div>
        </div>
        <div className="content">{children}</div>
      </main>
    </div>
  );
}
