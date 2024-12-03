import React from 'react';
import { Clock, Zap, Timer, Server } from 'lucide-react';

function MetricsCard({
  title,
  value,
  icon: Icon,
  change,
}: {
  title: string;
  value: string;
  icon: React.ElementType;
  change?: { value: string; positive: boolean };
}) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center">
        <div className="p-2 bg-indigo-50 rounded-lg">
          <Icon className="h-6 w-6 text-indigo-600" />
        </div>
        <div className="ml-4 flex-1">
          <h3 className="text-sm font-medium text-gray-900">{title}</h3>
          <div className="mt-1 flex items-baseline">
            <p className="text-2xl font-semibold text-gray-900">{value}</p>
            {change && (
              <p
                className={`ml-2 text-sm ${
                  change.positive ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {change.positive ? '↑' : '↓'} {change.value}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricsView() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricsCard
          title="Average Response Time"
          value="245ms"
          icon={Clock}
          change={{ value: '12%', positive: true }}
        />
        <MetricsCard
          title="Total Requests"
          value="1.2M"
          icon={Zap}
          change={{ value: '8%', positive: true }}
        />
        <MetricsCard
          title="P95 Latency"
          value="850ms"
          icon={Timer}
          change={{ value: '3%', positive: false }}
        />
        <MetricsCard title="Server Uptime" value="99.9%" icon={Server} />
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Response Time Distribution */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Response Time Distribution
          </h3>
          <div className="space-y-4">
            {['< 100ms', '100-300ms', '300-500ms', '500ms-1s', '> 1s'].map(
              (range) => (
                <div key={range}>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>{range}</span>
                    <span>{Math.floor(Math.random() * 1000)}req</span>
                  </div>
                  <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-indigo-600 h-2 rounded-full"
                      style={{ width: `${Math.floor(Math.random() * 100)}%` }}
                    ></div>
                  </div>
                </div>
              )
            )}
          </div>
        </div>

        {/* Resource Usage */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Resource Usage
          </h3>
          <div className="space-y-4">
            {[
              { label: 'CPU Usage', value: '78%' },
              { label: 'Memory Usage', value: '2.1GB / 4GB' },
              { label: 'Network I/O', value: '1.2GB/s' },
              { label: 'Disk Usage', value: '45%' },
            ].map((resource) => (
              <div key={resource.label}>
                <div className="flex justify-between text-sm text-gray-600">
                  <span>{resource.label}</span>
                  <span>{resource.value}</span>
                </div>
                <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-indigo-600 h-2 rounded-full"
                    style={{
                      width: resource.value.includes('%')
                        ? resource.value
                        : '50%',
                    }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default MetricsView;
