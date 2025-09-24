import React, { useState } from 'react';
import { useTraffic } from '../../context/TrafficContext';
import { Activity, Server, Settings, RefreshCw } from 'lucide-react';

const SystemControl: React.FC = () => {
  const { state, dispatch } = useTraffic();
  const [reconnecting, setReconnecting] = useState<string | null>(null);
  const [serverCapacity, setServerCapacity] = useState(10);
  const [retryLimit, setRetryLimit] = useState(3);

  const handleReconnect = async (serverId: string) => {
    setReconnecting(serverId);
    dispatch({ type: 'ADD_LOG', log: { 
      timestamp: Date.now(), 
      type: 'info', 
      component: 'System', 
      message: `Attempting to reconnect to ${serverId}...` 
    }});

    // Simulate reconnection delay
    setTimeout(() => {
      dispatch({ type: 'UPDATE_SERVER_STATUS', serverId, connected: true });
      dispatch({ type: 'ADD_LOG', log: { 
        timestamp: Date.now(), 
        type: 'info', 
        component: 'System', 
        message: `Successfully reconnected to ${serverId}` 
      }});
      setReconnecting(null);
    }, 2000);
  };

  const getStatusColor = (connected: boolean) => connected ? 'text-green-400' : 'text-red-400';
  const getStatusIcon = (connected: boolean) => connected ? '●' : '●';

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center">
          <Server className="mr-2" size={20} />
          Server Connection Status
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {state.servers.map((server) => (
            <div key={server.id} className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold capitalize">{server.id.replace('-', ' ')}</h3>
                <span className={`text-2xl ${getStatusColor(server.connected)}`}>
                  {getStatusIcon(server.connected)}
                </span>
              </div>
              <p className="text-sm text-gray-300">Port: {server.port}</p>
              <p className={`text-sm ${getStatusColor(server.connected)}`}>
                {server.connected ? 'Connected' : 'Disconnected'}
              </p>
              {server.id !== 'load-balancer' && (
                <p className="text-sm text-gray-300 mt-1">
                  Load: {server.load}/{server.maxLoad}
                </p>
              )}
              {!server.connected && (
                <button
                  onClick={() => handleReconnect(server.id)}
                  disabled={reconnecting === server.id}
                  className="mt-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded text-sm transition-colors flex items-center"
                >
                  {reconnecting === server.id ? (
                    <RefreshCw className="animate-spin mr-1" size={12} />
                  ) : null}
                  {reconnecting === server.id ? 'Reconnecting...' : 'Reconnect'}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center">
            <Activity className="mr-2" size={20} />
            Real-time Server Loads
          </h2>
          
          {state.servers.filter(s => s.id !== 'load-balancer').map((server) => (
            <div key={server.id} className="mb-3">
              <div className="flex justify-between items-center mb-1">
                <span className="capitalize">{server.id}</span>
                <span>{server.load}/{server.maxLoad}</span>
              </div>
              <div className="w-full bg-gray-600 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    server.load / server.maxLoad > 0.8 ? 'bg-red-500' :
                    server.load / server.maxLoad > 0.6 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${(server.load / server.maxLoad) * 100}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Load Balancer Statistics</h2>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span>Total Requests:</span>
              <span className="font-semibold">{state.systemStats.totalRequests}</span>
            </div>
            <div className="flex justify-between">
              <span>Load-balanced Requests:</span>
              <span className="font-semibold">{Math.floor(state.systemStats.totalRequests * 0.6)}</span>
            </div>
            <div className="flex justify-between">
              <span>Failed Requests:</span>
              <span className="font-semibold text-red-400">{state.systemStats.failedRequests}</span>
            </div>
            <div className="flex justify-between">
              <span>Timeouts:</span>
              <span className="font-semibold text-yellow-400">{state.systemStats.timeouts}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center">
          <Settings className="mr-2" size={20} />
          Load Balancer Configuration
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Server Capacity</label>
            <input
              type="number"
              value={serverCapacity}
              onChange={(e) => setServerCapacity(parseInt(e.target.value) || 10)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              min="1"
              max="20"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Retry Limit</label>
            <input
              type="number"
              value={retryLimit}
              onChange={(e) => setRetryLimit(parseInt(e.target.value) || 3)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              min="1"
              max="10"
            />
          </div>
        </div>
        
        <button
          onClick={() => {
            dispatch({ type: 'ADD_LOG', log: { 
              timestamp: Date.now(), 
              type: 'info', 
              component: 'System', 
              message: `Configuration updated: Capacity=${serverCapacity}, Retry Limit=${retryLimit}` 
            }});
          }}
          className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
        >
          Update Configuration
        </button>
      </div>
    </div>
  );
};

export default SystemControl;