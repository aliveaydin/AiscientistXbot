import React, { useState } from 'react';
import { 
  LayoutDashboard, Send, FileText, MessageCircle, Settings, 
  Bot, Menu, X, Zap, BookOpen
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import TweetsPage from './components/TweetsPage';
import ArticlesPage from './components/ArticlesPage';
import BlogPage from './components/BlogPage';
import RepliesPage from './components/RepliesPage';
import SettingsPage from './components/SettingsPage';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'tweets', label: 'Tweets', icon: Send },
  { id: 'blog', label: 'Blog Articles', icon: BookOpen },
  { id: 'articles', label: 'Source Papers', icon: FileText },
  { id: 'replies', label: 'Replies', icon: MessageCircle },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard': return <Dashboard />;
      case 'tweets': return <TweetsPage />;
      case 'blog': return <BlogPage />;
      case 'articles': return <ArticlesPage />;
      case 'replies': return <RepliesPage />;
      case 'settings': return <SettingsPage />;
      default: return <Dashboard />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-gray-900 border-r border-gray-800 flex flex-col transition-all duration-300 ease-in-out`}>
        {/* Logo */}
        <div className="flex items-center gap-3 p-5 border-b border-gray-800">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-xl flex items-center justify-center flex-shrink-0">
            <Bot className="w-6 h-6 text-white" />
          </div>
          {sidebarOpen && (
            <div className="overflow-hidden">
              <h1 className="font-bold text-lg text-white leading-tight">SciTweet</h1>
              <p className="text-xs text-gray-400">AI Agent Bot</p>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                activePage === item.id
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
            </button>
          ))}
        </nav>

        {/* Sidebar toggle */}
        <div className="p-3 border-t border-gray-800">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-all"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            {sidebarOpen && <span className="text-sm">Collapse</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-gray-950">
        <div className="p-6 max-w-7xl mx-auto">
          {renderPage()}
        </div>
      </main>
    </div>
  );
}
