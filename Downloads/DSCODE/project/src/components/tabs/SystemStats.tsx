import React, { useState, useEffect } from 'react';
import { useTraffic } from '../../context/TrafficContext';
import { BarChart3, PieChart, RefreshCw, TrendingUp, Clock, Cpu } from 'lucide-react';

const SystemStats: React.FC = () => {
  const { state, dispatch } = useTraffic();
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [chartData, setChartData] = useState({
    serverLoads: [0, 0],
    requestOutcomes: [0, 0, 0], // success, failed, timeout
  });

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Update chart data based on current stats
      const primaryServer = state.servers.find(s => s.id === 'primary');
      const cloneServer = state.servers.find(s => s.id === 'clone');
      
      setChartData({
        serverLoads: [
          primaryServer?.load || 0,
          cloneServer?.load || 0
        ],
        requestOutcomes: [
          state.systemStats.totalRequests - state.systemStats.failedRequests - state.systemStats.timeouts,
          state.systemStats.failedRequests,
          state.systemStats.timeouts
        ]
      });

      // Simulate some stat fluctuations
      dispatch({ type: 'UPDATE_STATS', stats: {
        requestsPerMinute: Math.max(0, state.systemStats.requestsPerMinute + Math.floor((Math.random() - 0.5) * 10))
      }});
    }, 2000);

    return () => clearInterval(interval);
  }, [autoRefresh, state.servers, state.systemStats, dispatch]);

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const successRate = state.systemStats.totalRequests > 0 ? 
    ((state.systemStats.totalRequests - state.systemStats.failedRequests - state.systemStats.timeouts) / state.systemStats.totalRequests * 100).toFixed(1) :
    '100';

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">System Statistics</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded transition-colors flex items-center ${
              autoRefresh ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-600 hover:bg-gray-700'
            }`}
          >
            <RefreshCw className={`mr-1 ${autoRefresh ? 'animate-spin' : ''}`} size={16} />
            Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Requests</p>
              <p className="text-2xl font-bold text-blue-400">{state.systemStats.totalRequests}</p>
            </div>
            <TrendingUp className="text-blue-400" size={24} />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">VIP Requests</p>
              <p className="text-2xl font-bold text-red-400">{state.systemStats.vipRequests}</p>
            </div>
            <div className="text-red-400 text-2xl">🚨</div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Success Rate</p>
              <p className="text-2xl font-bold text-green-400">{successRate}%</p>
            </div>
            <div className="text-green-400 text-2xl">✓</div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Requests/Min</p>
              <p className="text-2xl font-bold text-yellow-400">{state.systemStats.requestsPerMinute}</p>
            </div>
            <Clock className="text-yellow-400" size={24} />
          </div>
        </div>
      </div>

      {/* Detailed Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <BarChart3 className="mr-2" size={20} />
            Request Statistics
          </h3>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span>Total Processed:</span>
              <span className="font-semibold">{state.systemStats.totalRequests}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>VIP Requests:</span>
              <span className="font-semibold text-red-400">{state.systemStats.vipRequests}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Regular Requests:</span>
              <span className="font-semibold">{state.systemStats.totalRequests - state.systemStats.vipRequests}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Failed Requests:</span>
              <span className="font-semibold text-red-400">{state.systemStats.failedRequests}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Timeouts:</span>
              <span className="font-semibold text-yellow-400">{state.systemStats.timeouts}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Pending Requests:</span>
              <span className="font-semibold text-blue-400">
                {Math.max(0, Math.floor(Math.random() * 5))}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Cpu className="mr-2" size={20} />
            Server Performance
          </h3>
          
          <div className="space-y-4">
            {state.servers.filter(s => s.id !== 'load-balancer').map(server => (
              <div key={server.id} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="capitalize">{server.id} Server:</span>
                  <span className="font-semibold">
                    {server.load}/{server.maxLoad} ({((server.load / server.maxLoad) * 100).toFixed(0)}%)
                  </span>
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
            
            <div className="pt-4 border-t border-gray-600">
              <div className="flex justify-between items-center">
                <span>Load Balanced Requests:</span>
                <span className="font-semibold">{Math.floor(state.systemStats.totalRequests * 0.6)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Direct Requests:</span>
                <span className="font-semibold">{Math.floor(state.systemStats.totalRequests * 0.4)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* System Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">System Information</h3>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span>System Uptime:</span>
              <span className="font-mono text-green-400">{formatUptime(state.systemStats.uptime)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Logical Clock:</span>
              <span className="font-mono text-blue-400">{state.systemStats.logicalClock}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Critical Section:</span>
              <span className={`font-semibold ${
                state.systemStats.criticalSectionActive ? 'text-red-400' : 'text-green-400'
              }`}>
                {state.systemStats.criticalSectionActive ? 'ACTIVE' : 'INACTIVE'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span>Active Connections:</span>
              <span className="font-semibold text-blue-400">
                {state.servers.filter(s => s.connected).length}/{state.servers.length}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <PieChart className="mr-2" size={20} />
            Request Distribution
          </h3>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-4 h-4 bg-green-500 rounded mr-2"></div>
                <span>Successful</span>
              </div>
              <span className="font-semibold">
                {state.systemStats.totalRequests - state.systemStats.failedRequests - state.systemStats.timeouts}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-4 h-4 bg-red-500 rounded mr-2"></div>
                <span>Failed</span>
              </div>
              <span className="font-semibold">{state.systemStats.failedRequests}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-4 h-4 bg-yellow-500 rounded mr-2"></div>
                <span>Timeouts</span>
              </div>
              <span className="font-semibold">{state.systemStats.timeouts}</span>
            </div>
          </div>

          {/* Simple visual representation */}
          <div className="mt-4">
            <div className="w-full bg-gray-600 rounded-full h-4 overflow-hidden">
              <div className="h-full flex">
                <div 
                  className="bg-green-500" 
                  style={{ width: `${((state.systemStats.totalRequests - state.systemStats.failedRequests - state.systemStats.timeouts) / Math.max(1, state.systemStats.totalRequests)) * 100}%` }}
                ></div>
                <div 
                  className="bg-red-500" 
                  style={{ width: `${(state.systemStats.failedRequests / Math.max(1, state.systemStats.totalRequests)) * 100}%` }}
                ></div>
                <div 
                  className="bg-yellow-500" 
                  style={{ width: `${(state.systemStats.timeouts / Math.max(1, state.systemStats.totalRequests)) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Ricart-Agrawala Details */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Distributed System Details (Ricart-Agrawala)</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-700 rounded p-4">
            <h4 className="font-semibold text-blue-400 mb-2">Mutual Exclusion</h4>
            <p className="text-sm text-gray-300 mb-2">
              Current algorithm ensures only one traffic signal is green at a time
            </p>
            <div className="text-xs">
              <p>Active Signal: <span className="font-mono text-green-400">{state.activeSignal || 'None'}</span></p>
              <p>Critical Section: <span className={`font-mono ${state.systemStats.criticalSectionActive ? 'text-red-400' : 'text-green-400'}`}>
                {state.systemStats.criticalSectionActive ? 'OCCUPIED' : 'FREE'}
              </span></p>
            </div>
          </div>

          <div className="bg-gray-700 rounded p-4">
            <h4 className="font-semibold text-blue-400 mb-2">Logical Clock</h4>
            <p className="text-sm text-gray-300 mb-2">
              Lamport timestamp for event ordering
            </p>
            <div className="text-2xl font-mono text-blue-400 text-center">
              {state.systemStats.logicalClock}
            </div>
          </div>

          <div className="bg-gray-700 rounded p-4">
            <h4 className="font-semibold text-blue-400 mb-2">Message Queue</h4>
            <p className="text-sm text-gray-300 mb-2">
              Pending requests in the system
            </p>
            <div className="text-2xl font-mono text-yellow-400 text-center">
              {Math.max(0, Math.floor(Math.random() * 3))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemStats;