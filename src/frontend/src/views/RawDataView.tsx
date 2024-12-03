import React from 'react';
import { useDataStore } from '../store/dataStore';
import JsonView from '@uiw/react-json-view'
import { RefreshCw } from 'lucide-react';
import { useSettingsStore } from '../store/settingsStore';

export default function RawDataView() {
  const { data, error } = useDataStore();

  const { endpointUrl } = useSettingsStore();

  async function handleRefresh() {
    const url = new URL(`${endpointUrl}/spans`);
    const response = await fetch(url, {
      method: 'GET',
      mode: 'cors',
      headers: {
        'Accept': 'application/json',
      },
      credentials: 'omit'
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const jsonData = await response.json();
    useDataStore.getState().setData(jsonData);
  }

  return (
    <div className="space-y-4">
      {error ? (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error fetching data</h3>
              <pre className="mt-2 text-sm text-red-700 whitespace-pre-wrap">{error}</pre>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg p-4">
          <pre className="whitespace-pre-wrap overflow-auto max-h-[600px]">
           
          </pre>

          <div>
            <h4 className="text-sm font-medium text-gray-500 mb-2">Raw Data
              <button
                      onClick={handleRefresh}
                    
                      className={`p-2 text-gray-600 hover:text-gray-900 focus:outline-none`}
                      title="Manual refresh"
                    >
                      <RefreshCw className="w-3 h-3" />
                    </button>
            </h4>
            <div className="bg-gray-100 p-4 rounded-md overflow-auto max-h-96 border">
              <JsonView value={data || {}} />
            </div>
          </div>
          
        </div>
      )}
    </div>
  );
}
