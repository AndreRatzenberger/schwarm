import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { useSettingsStore } from '../store/settingsStore';

const RefreshButton = ({ onRefresh }) => {
  const [countdown, setCountdown] = useState(null);
  const { refreshInterval } = useSettingsStore();
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (!refreshInterval) {
      setCountdown(null);
      return;
    }

    const updateCountdown = () => {
      const now = Date.now();
      const nextRefresh = Math.ceil((now % refreshInterval) / 1000);
      setCountdown(Math.floor(refreshInterval / 1000) - nextRefresh);
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await onRefresh();
    setIsRefreshing(false);
  };

  return (
    <div className="flex items-center gap-2">
      {countdown !== null && (
        <span className="text-sm text-gray-500">{countdown}s</span>
      )}
      <button
        onClick={handleRefresh}
        disabled={isRefreshing}
        className={`p-2 text-gray-600 hover:text-gray-900 focus:outline-none ${
          isRefreshing ? 'animate-spin' : ''
        }`}
        title="Manual refresh"
      >
        <RefreshCw className="w-5 h-5" />
      </button>
    </div>
  );
};

export default RefreshButton;