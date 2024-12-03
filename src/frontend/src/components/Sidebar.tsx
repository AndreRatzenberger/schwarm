import React from 'react';
import { Home, Users, Settings, HelpCircle, BarChart2 } from 'lucide-react';

function Sidebar() {
  return (
    <div className="w-16 bg-indigo-700 flex flex-col items-center py-6">
      <div className="flex-1 space-y-4">
        <button className="p-3 text-white hover:bg-indigo-600 rounded-lg">
          <Home className="h-6 w-6" />
        </button>
        <button className="p-3 text-white hover:bg-indigo-600 rounded-lg">
          <Users className="h-6 w-6" />
        </button>
        <button className="p-3 text-white hover:bg-indigo-600 rounded-lg">
          <BarChart2 className="h-6 w-6" />
        </button>
      </div>
      <div className="space-y-4">
        <button className="p-3 text-white hover:bg-indigo-600 rounded-lg">
          <Settings className="h-6 w-6" />
        </button>
        <button className="p-3 text-white hover:bg-indigo-600 rounded-lg">
          <HelpCircle className="h-6 w-6" />
        </button>
      </div>
    </div>
  );
}

export default Sidebar;