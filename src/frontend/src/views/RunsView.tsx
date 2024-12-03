import React, { useMemo } from 'react';
import { useLogStore } from '../store/logStore';
import { useRunStore } from '../store/runStore';
import { Clock, MessageSquare, Zap } from 'lucide-react';

interface RunStats {
  id: string;
  timestamp: string;
  totalEvents: number;
  messageCompletions: number;
  toolExecutions: number;
  duration: number;
  agents: Set<string>;
}

function RunCard({ run, isActive }: { run: RunStats; isActive: boolean }) {
  return (
    <div className={`bg-white rounded-lg shadow-sm p-6 border-2 ${isActive ? 'border-indigo-500' : 'border-transparent'}`}>
      <div className="space-y-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-sm font-medium text-gray-900">Run ID</h3>
            <p className="text-sm text-gray-500 font-mono">{run.id}</p>
          </div>
          {isActive && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
              Active
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="flex items-center">
              <Clock className="h-4 w-4 text-gray-400 mr-2" />
              <span className="text-sm text-gray-500">Started</span>
            </div>
            <p className="mt-1 text-sm font-medium">
              {new Date(run.timestamp).toLocaleString()}
            </p>
          </div>
          <div>
            <div className="flex items-center">
              <MessageSquare className="h-4 w-4 text-gray-400 mr-2" />
              <span className="text-sm text-gray-500">Duration</span>
            </div>
            <p className="mt-1 text-sm font-medium">
              {(run.duration / 1000).toFixed(2)}s
            </p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 pt-4 border-t">
          <div>
            <p className="text-sm text-gray-500">Events</p>
            <p className="mt-1 text-lg font-semibold">{run.totalEvents}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Messages</p>
            <p className="mt-1 text-lg font-semibold">{run.messageCompletions}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Tools Used</p>
            <p className="mt-1 text-lg font-semibold">{run.toolExecutions}</p>
          </div>
        </div>

        <div>
          <p className="text-sm text-gray-500">Agents</p>
          <div className="mt-1 flex flex-wrap gap-2">
            {Array.from(run.agents).map(agent => (
              <span
                key={agent}
                className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800"
              >
                {agent}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function RunsView() {
  const logs = useLogStore(state => state.logs);
  const activeRunId = useRunStore(state => state.activeRunId);

  const runs = useMemo(() => {
    // Group logs by run_id
    const runGroups = new Map<string, typeof logs>();
    
    logs.forEach(log => {
      if (log.run_id) {
        if (!runGroups.has(log.run_id)) {
          runGroups.set(log.run_id, []);
        }
        runGroups.get(log.run_id)!.push(log);
      }
    });

    // Calculate statistics for each run
    return Array.from(runGroups.entries()).map(([runId, runLogs]) => {
      // Find the earliest log for this run to get the start time
      const startLog = runLogs.reduce((earliest, current) => 
        new Date(current.timestamp) < new Date(earliest.timestamp) ? current : earliest
      );

      // Find the latest log for this run to calculate duration
      const endLog = runLogs.reduce((latest, current) => 
        new Date(current.timestamp) > new Date(latest.timestamp) ? current : latest
      );

      const runStats: RunStats = {
        id: runId,
        timestamp: startLog.timestamp,
        totalEvents: runLogs.length,
        messageCompletions: runLogs.filter(log => log.level === 'MESSAGE_COMPLETION').length,
        toolExecutions: runLogs.filter(log => log.level === 'TOOL_EXECUTION').length,
        duration: new Date(endLog.timestamp).getTime() - new Date(startLog.timestamp).getTime(),
        agents: new Set(runLogs.map(log => log.agent))
      };

      return runStats;
    }).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [logs]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900">Runs</h2>
        <div className="flex items-center space-x-2">
          <Zap className="h-5 w-5 text-gray-400" />
          <span className="text-sm text-gray-500">
            {runs.length} total run{runs.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {runs.map(run => (
          <RunCard
            key={run.id}
            run={run}
            isActive={run.id === activeRunId}
          />
        ))}
      </div>
    </div>
  );
}

export default RunsView;
