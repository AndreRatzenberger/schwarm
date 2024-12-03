import React, { useState } from 'react';
import { useSettingsStore } from '../store/settingsStore';
import { useLogStore } from '../store/logStore';
import { useDataStore } from '../store/dataStore';
import { usePauseStore } from '../store/pauseStore';
import { useRunStore } from '../store/runStore';
import RawDataView from './RawDataView';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Label } from '../components/ui/label';

const REFRESH_INTERVALS = [
  { label: 'Off', value: 'off' },
  { label: '1 seconds', value: '1000' },
  { label: '5 seconds', value: '5000' },
  { label: '10 seconds', value: '10000' },
  { label: '30 seconds', value: '30000' },
  { label: '1 minute', value: '60000' },
  { label: '5 minute', value: '300000' },
  { label: '10 minute', value: '600000' }
];

export default function SettingsView() {
  const [showConfirmation, setShowConfirmation] = useState(false);
  
  const { 
    endpointUrl, 
    refreshInterval,
    showRefreshButton,
    groupLogsByParent,
    showLogIndentation,
    setEndpointUrl,
    setRefreshInterval,
    setShowRefreshButton,
    setGroupLogsByParent,
    setShowLogIndentation
  } = useSettingsStore();

  const clearAllStores = () => {
    useLogStore.getState().reset();
    useDataStore.getState().reset();
    usePauseStore.getState().reset();
    useRunStore.getState().setActiveRunId(null);
    setShowConfirmation(false);
  };

  const handleRefreshIntervalChange = (value: string) => {
    if (value === 'off') {
      setRefreshInterval(null);
    } else {
      setRefreshInterval(Number(value));
    }
  };

  const getCurrentRefreshValue = () => {
    if (refreshInterval === null) return 'off';
    return String(refreshInterval);
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-medium text-gray-900">Application Settings</h2>
      <Card>
        <CardContent className="space-y-6 pt-6">
          <div className="space-y-2">
            <Label htmlFor="endpoint">Endpoint URL</Label>
            <Input
              id="endpoint"
              value={endpointUrl}
              onChange={(e) => setEndpointUrl(e.target.value)}
              placeholder="http://127.0.0.1:8123"
            />
            <p className="text-sm text-muted-foreground">
              The base URL of your agent framework endpoint
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="refresh">Refresh Interval</Label>
            <Select
              value={getCurrentRefreshValue()}
              onValueChange={handleRefreshIntervalChange}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select refresh interval" />
              </SelectTrigger>
              <SelectContent>
                {REFRESH_INTERVALS.map(({ label, value }) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              How often the application should fetch new data
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="show-refresh-button"
              checked={showRefreshButton}
              onCheckedChange={(checked: boolean) => setShowRefreshButton(checked)}
            />
            <div className="space-y-1">
              <Label
                htmlFor="show-refresh-button"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Show Refresh Button
              </Label>
              <p className="text-sm text-muted-foreground">
                Toggle visibility of the manual refresh button in the navigation bar
              </p>
            </div>
          </div>

          <div className="border-t border-border pt-4">
            <h3 className="text-sm font-medium mb-4">Log View Settings</h3>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="group-logs"
                  checked={groupLogsByParent}
                  onCheckedChange={(checked: boolean) => setGroupLogsByParent(checked)}
                />
                <div className="space-y-1">
                  <Label
                    htmlFor="group-logs"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    Group Logs by Parent
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Group and allow collapsing of logs based on their parent-child relationships
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="show-indentation"
                  checked={showLogIndentation}
                  onCheckedChange={(checked: boolean) => setShowLogIndentation(checked)}
                />
                <div className="space-y-1">
                  <Label
                    htmlFor="show-indentation"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    Show Log Indentation
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Indent logs to visualize their hierarchy level
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-border">
            <h3 className="text-sm font-medium mb-4">Danger Zone</h3>
            <Button
              variant="destructive"
              onClick={() => setShowConfirmation(true)}
            >
              Delete Client Data
            </Button>
            <p className="mt-1 text-sm text-muted-foreground">
              Clear all locally stored data. This will not affect the server.
            </p>
          </div>
          
          <RawDataView />
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm">
          <div className="fixed inset-0 flex items-center justify-center">
            <Card className="max-w-sm w-full mx-4">
              <CardHeader>
                <CardTitle>Confirm Data Deletion</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Are you sure you want to delete all client data? This action cannot be undone.
                </p>
                <div className="flex justify-end space-x-4">
                  <Button
                    variant="outline"
                    onClick={() => setShowConfirmation(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={clearAllStores}
                  >
                    Delete Data
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
