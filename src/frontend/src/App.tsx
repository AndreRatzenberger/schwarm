import React from 'react';
import { LayoutDashboard, ScrollText, Network, History, Settings } from 'lucide-react';
import DashboardView from './views/DashboardView';
import LogsView from './views/LogsView';
import NetworkView from './views/NetworkView';
import RunsView from './views/RunsView';
import SettingsView from './views/SettingsView';
import MessageFlow from './components/message-flow';
import { ActiveRunBanner } from './components/ActiveRunBanner';
import { cn } from './lib/utils';

type View = 'dashboard' | 'messageflow' | 'logs' | 'network' | 'runs' | 'settings';

function App() {
  const [currentView, setCurrentView] = React.useState<View>('dashboard');

  const views = {
    dashboard: <DashboardView />,
    logs: <LogsView />,
    network: <NetworkView />,
    runs: <RunsView />,
    messageflow: <MessageFlow />,
    settings: <SettingsView />
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'logs', label: 'Logs', icon: ScrollText },
    { id: 'network', label: 'Network', icon: Network },
    { id: 'runs', label: 'Runs', icon: History },
    { id: 'messageflow', label: 'Message Flow', icon: ScrollText},
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <Network className="h-8 w-8 text-indigo-600" />
                <span className="ml-2 text-xl font-bold text-gray-900">Schwarm</span>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {navItems.map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    onClick={() => setCurrentView(id as View)}
                    className={cn(
                      "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors duration-200",
                      currentView === id
                        ? "border-indigo-500 text-gray-900 bg-indigo-50"
                        : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 hover:bg-gray-50"
                    )}
                  >
                    <Icon className={cn(
                      "h-4 w-4 mr-2 transition-colors duration-200",
                      currentView === id
                        ? "text-indigo-600"
                        : "text-gray-400 group-hover:text-gray-500"
                    )} />
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </nav>
      </header>

      <ActiveRunBanner />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {views[currentView]}
      </main>
    </div>
  );
}

export default App;
