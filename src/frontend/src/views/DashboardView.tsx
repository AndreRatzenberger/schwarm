/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState } from 'react';
import { Clock, Cpu, DollarSign, TrendingUp, TrendingDown } from 'lucide-react';
import { useLogStore } from '../store/logStore';
import { useRunStore } from '../store/runStore';
import CompactNetworkView from '../components/CompactNetworkView';
import CompactMessageFlow from '../components/CompactMessageFlow';
import DashboardMessageFlow from '../components/DashboardMessageFlow';
import { Card } from '../components/ui/card';

function DashboardView() {
  const getFilteredLogs = useLogStore(state => state.getFilteredLogs);
  const activeRunId = useRunStore(state => state.activeRunId);
  const logs = getFilteredLogs();
  const [tokenUsage, setTokenUsage] = useState(0);
  const [turns, setTurns] = useState(0);
  const [prevTokenUsage, setPrevTokenUsage] = useState(0);
  const [costSpent, setCostSpent] = useState(0);
  const [prevCostSpent, setPrevCostSpent] = useState(0);
  const [activeAgents, setActiveAgents] = useState(0);
  const [prevActiveAgents, setPrevActiveAgents] = useState(0);
  const [eventsToday, setEventsTotal] = useState(0);
  const [prevEventsToday, setPrevEventsTotal] = useState(0);

  useEffect(() => {
    // Store previous values before updating
    setPrevTokenUsage(tokenUsage);
    setPrevCostSpent(costSpent);
    setPrevActiveAgents(activeAgents);
    setPrevEventsTotal(eventsToday);

    // Calculate token usage and cost from START_TURN logs
    let maxTokens = 0;
    let maxCost = 0;
    let turns = 0;
    const seenAgents = new Set();
    let totalEvents = 0;

    logs.forEach(log => {
      if (log.run_id !== activeRunId) return;
      // Track unique agents
      seenAgents.add(log.agent);

      const attributes = log.attributes as { [key: string]: any };
      totalEvents++;

      // Process START_TURN logs for turn data
      if (log.level === 'START_TURN') {
        turns++;
      }

      // Process START_TURN logs for token and cost data
      if (log.level === 'POST_MESSAGE_COMPLETION' && log.attributes != null) {
        const rk: number = +attributes['message.info.token_counter'];
        const ck: number = +attributes['message.info.completion_cost'];

        maxTokens = maxTokens + rk;
        maxCost = maxCost + ck;
      }
    });

    setTokenUsage(maxTokens);
    setCostSpent(maxCost);
    setTurns(turns);
    setActiveAgents(seenAgents.size);
    setEventsTotal(totalEvents);
  }, [logs, activeRunId]);

  const TrendIndicator = ({ current, previous }: { current: number, previous: number }) => {
    if (current === previous) return null;
    const isUp = current > previous;
    const Icon = isUp ? TrendingUp : TrendingDown;
    const colorClass = isUp ? 'text-green-500' : 'text-red-500';

    return (
      <div className={`flex items-center ${colorClass} text-sm ml-2`}>
        <Icon className="h-4 w-4" />
      </div>
    );
  };



  return (
    <div className="space-y-6">

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center">
            <Cpu className="h-8 w-8 text-indigo-600" />
            <div className="ml-4 flex items-center">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Agents</p>
                <p className="text-2xl font-semibold text-gray-900">{activeAgents}</p>
              </div>
              <TrendIndicator current={activeAgents} previous={prevActiveAgents} />
            </div>
          </div>
        </Card>
        <Card className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-indigo-600" />
            <div className="ml-4 flex items-center">
              <div>
                <p className="text-sm font-medium text-gray-600">Events / Turns</p>
                <p className="text-2xl font-semibold text-gray-900">{eventsToday} / {turns}</p>
              </div>
              <TrendIndicator current={eventsToday} previous={prevEventsToday} />
            </div>
          </div>
        </Card>

        <Card className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center">
            <DollarSign className="h-8 w-8 text-indigo-600" />
            <div className="ml-4 flex items-center">
              <div>
                <p className="text-sm font-medium text-gray-600">Token Usage</p>
                <p className="text-2xl font-semibold text-gray-900">{tokenUsage}</p>
              </div>
              <TrendIndicator current={tokenUsage} previous={prevTokenUsage} />
            </div>
          </div>
        </Card>
        <Card className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center">
            <DollarSign className="h-8 w-8 text-indigo-600" />
            <div className="ml-4 flex items-center">
              <div>
                <p className="text-sm font-medium text-gray-600">Cost Spent</p>
                <p className="text-2xl font-semibold text-gray-900">${costSpent.toFixed(4)}</p>
              </div>
              <TrendIndicator current={costSpent} previous={prevCostSpent} />
            </div>
          </div>
        </Card>
      </div>
      {/* Message Flow */}


      {/* Message Flow */}
      {/* Network and Message Flow */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        <DashboardMessageFlow />

        <Card className="bg-white rounded-lg shadow-sm p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Events</h2>
          <CompactMessageFlow />
          <h2 className="text-lg font-semibold text-gray-900 mt-4">Network Overview</h2>
          <CompactNetworkView />

        </Card>
      </div>




    </div>
  );
}

export default DashboardView;
