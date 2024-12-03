import React from 'react';
import { Cpu, Activity } from 'lucide-react';

function Metrics() {
  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <h2 className="text-lg font-semibold mb-4 flex items-center">
        <Activity className="h-5 w-5 mr-2 text-indigo-600" />
        System Metrics
      </h2>

      <div className="space-y-4">
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center text-sm font-medium text-gray-600">
              <Cpu className="h-4 w-4 mr-2" />
              CPU Usage
            </div>
            <span className="text-sm font-semibold text-gray-900">78%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-indigo-600 h-2 rounded-full"
              style={{ width: '78%' }}
            ></div>
          </div>
        </div>

        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center text-sm font-medium text-gray-600">
              <div className="h-4 w-4 mr-2" />
              Memory Usage
            </div>
            <span className="text-sm font-semibold text-gray-900">
              2.1GB / 4GB
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-indigo-600 h-2 rounded-full"
              style={{ width: '52%' }}
            ></div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-sm font-medium text-gray-600 mb-1">
              Active Tasks
            </div>
            <div className="text-2xl font-semibold text-gray-900">24</div>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-sm font-medium text-gray-600 mb-1">
              Queue Size
            </div>
            <div className="text-2xl font-semibold text-gray-900">12</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Metrics;
