import React, { useState } from 'react';
import { 
  LayoutDashboard, Send, FileText, MessageCircle, Settings, 
  Bot, Menu, X, Zap, BookOpen, FlaskConical, Joystick,
  Users, Box, ScrollText, Megaphone, Heart, Calendar, Brain, Image,
  MessageSquareText, Mail,
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import TweetsPage from './components/TweetsPage';
import ArticlesPage from './components/ArticlesPage';
import BlogPage from './components/BlogPage';
import LabPage from './components/LabPage';
import RLEnvsPage from './components/RLEnvsPage';
import RepliesPage from './components/RepliesPage';
import SettingsPage from './components/SettingsPage';
import UsersPage from './components/UsersPage';
import PlatformEnvsPage from './components/PlatformEnvsPage';
import PapersPage from './components/PapersPage';
import GTMTweetsPage from './components/GTMTweetsPage';
import EngagementPage from './components/EngagementPage';
import ContentCalendarPage from './components/ContentCalendarPage';
import StrategyPage from './components/StrategyPage';
import VisualsPage from './components/VisualsPage';
import AgentsPage from './components/AgentsPage';
import FeedbackPage from './components/FeedbackPage';
import EmailPage from './components/EmailPage';

const platformNav = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'agents', label: 'Agents', icon: Bot },
  { id: 'users', label: 'Users', icon: Users },
  { id: 'platform-envs', label: 'Environments', icon: Box },
  { id: 'papers', label: 'Papers', icon: ScrollText },
  { id: 'feedback', label: 'Feedback', icon: MessageSquareText },
  { id: 'email', label: 'Email', icon: Mail },
];

const marketingNav = [
  { id: 'strategy', label: 'Strategy', icon: Brain },
  { id: 'gtm-tweets', label: 'GTM Tweets', icon: Megaphone },
  { id: 'blog', label: 'Blog Articles', icon: BookOpen },
  { id: 'engagement', label: 'Engagement', icon: Heart },
  { id: 'content-calendar', label: 'Content Calendar', icon: Calendar },
  { id: 'visuals', label: 'Visuals', icon: Image },
];

const researchBotNav = [
  { id: 'tweets', label: 'Tweets', icon: Send },
  { id: 'replies', label: 'Replies', icon: MessageCircle },
  { id: 'articles', label: 'Source Papers', icon: FileText },
];

const toolsNav = [
  { id: 'lab', label: 'Research Lab', icon: FlaskConical },
  { id: 'rl-envs', label: 'RL Envs (Admin)', icon: Joystick },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard': return <Dashboard />;
      case 'users': return <UsersPage />;
      case 'platform-envs': return <PlatformEnvsPage />;
      case 'papers': return <PapersPage />;
      case 'strategy': return <StrategyPage />;
      case 'gtm-tweets': return <GTMTweetsPage />;
      case 'blog': return <BlogPage />;
      case 'engagement': return <EngagementPage />;
      case 'content-calendar': return <ContentCalendarPage />;
      case 'visuals': return <VisualsPage />;
      case 'agents': return <AgentsPage />;
      case 'feedback': return <FeedbackPage />;
      case 'email': return <EmailPage />;
      case 'tweets': return <TweetsPage />;
      case 'replies': return <RepliesPage />;
      case 'articles': return <ArticlesPage />;
      case 'lab': return <LabPage />;
      case 'rl-envs': return <RLEnvsPage />;
      case 'settings': return <SettingsPage />;
      default: return <Dashboard />;
    }
  };

  const NavGroup = ({ label, items }) => (
    <div>
      {sidebarOpen && <p className="px-3 pt-4 pb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-600">{label}</p>}
      {!sidebarOpen && <div className="border-t border-gray-800 my-2" />}
      {items.map((item) => (
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
    </div>
  );

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-gray-900 border-r border-gray-800 flex flex-col transition-all duration-300 ease-in-out`}>
        <div className="flex items-center gap-3 p-5 border-b border-gray-800">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-xl flex items-center justify-center flex-shrink-0">
            <Bot className="w-6 h-6 text-white" />
          </div>
          {sidebarOpen && (
            <div className="overflow-hidden">
              <h1 className="font-bold text-lg text-white leading-tight">kualia.ai</h1>
              <p className="text-xs text-gray-400">Admin Panel</p>
            </div>
          )}
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          <NavGroup label="Platform" items={platformNav} />
          <NavGroup label="Marketing" items={marketingNav} />
          <NavGroup label="Research Bot" items={researchBotNav} />
          <NavGroup label="Tools" items={toolsNav} />
        </nav>

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

      <main className="flex-1 overflow-y-auto bg-gray-950">
        <div className="p-6 max-w-7xl mx-auto">
          {renderPage()}
        </div>
      </main>
    </div>
  );
}
