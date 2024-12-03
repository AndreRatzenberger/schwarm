import React from 'react';
import { Circle } from 'lucide-react';

interface AgentCardProps {
  agent: {
    id: string;
    name: string;
    status: string;
    type: string;
  };
  isActive: boolean;
  onClick: () => void;
}

const statusColors = {
  running: 'text-green-500',
  idle: 'text-yellow-500',
  error: 'text-red-500'
};

function AgentCard({ agent, isActive, onClick }: AgentCardProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-3 rounded-lg transition-colors ${
        isActive
          ? 'bg-indigo-50 border-2 border-indigo-200'
          : 'hover:bg-gray-50 border-2 border-transparent'
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium text-gray-900">{agent.name}</span>
        <Circle className={`h-3 w-3 ${statusColors[agent.status as keyof typeof statusColors]}`} />
      </div>
      <div className="mt-1 text-sm text-gray-500">Type: {agent.type}</div>
    </button>
  );
}

export default AgentCard;