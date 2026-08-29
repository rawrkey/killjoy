'use client';

import { usePathname } from 'next/navigation';
import './globals.css';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: '&#9632;' },
  { href: '/positions', label: 'Positions', icon: '&#9650;' },
  { href: '/market', label: 'Market', icon: '&#9670;' },
  { href: '/trades', label: 'Trades', icon: '&#9654;' },
  { href: '/settings', label: 'Settings', icon: '&#9881;' },
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
  const pathname = usePathname();

  return (
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
            <span className="nav-icon" dangerouslySetInnerHTML={{ __html: item.icon }} />
            <span>{item.label}</span>
          </a>
        ))}
      </nav>
      <div className="sidebar-footer">v0.1.0 &middot; Paper Only</div>
    </aside>
  );
}

function Topbar() {
  const pathname = usePathname();
  const title = PAGE_TITLES[pathname] || 'Dashboard';

  return (
    <div className="topbar">
      <div className="topbar-title">{title}</div>
      <div className="topbar-actions">
        <span className="badge badge-green">PAPER</span>
      </div>
    </div>
  );
}
