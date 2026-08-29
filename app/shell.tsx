'use client';

import { usePathname } from 'next/navigation';

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

export default function ClientShell({ children }: { children: React.ReactNode }) {
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
