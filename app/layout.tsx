import type { Metadata } from 'next';
import './globals.css';
import { Sidebar, Topbar } from './components';

export const metadata: Metadata = {
  title: 'KILLJOY — AI Options Trading',
  description: 'Autonomous AI options trading agent with adversarial kill testing',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
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
