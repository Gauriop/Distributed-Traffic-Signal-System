import React, { useState, useEffect, useRef } from 'react';
import { useTraffic } from '../../context/TrafficContext';
import { Terminal, Filter, Download, Trash2, Search } from 'lucide-react';

type LogLevel = 'info' | 'warning' | 'error';
type LogComponent = 'System' | 'Signal Control' | 'VIP System' | 'Time Sync' | 'Pedestrian Monitor' | 'Load Testing';

const LogsConsole: React.FC = () => {
  const { state, dispatch } = useTraffic();
  const [filterComponent, setFilterComponent] = useState<LogComponent | 'All'>('All');
  const [filterLevel, setFilterLevel] = useState<LogLevel | 'All'>('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const logContainerRef = useRef<HTMLDivElement>(null);

  const filteredLogs = state.logs.filter(log => {
    const componentMatch = filterComponent === 'All' || log.component === filterComponent;
    const levelMatch = filterLevel === 'All' || log.type === filterLevel;
    const searchMatch = searchTerm === '' || 
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.component.toLowerCase().includes(searchTerm.toLowerCase());
    
    return componentMatch && levelMatch && searchMatch;
  });

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [state.logs, autoScroll]);

  // Generate sample logs periodically for demonstration
  useEffect(() => {
    const interval = setInterval(() => {
      // Generate random system activity logs
      const activities = [
        { component: 'System', type: 'info' as LogLevel, message: 'System health check completed successfully' },
        { component: 'Signal Control', type: 'info' as LogLevel, message: `Signal ${['T1', 'T2', 'T3', 'T4'][Math.floor(Math.random() * 4)]} cycle completed` },
        { component: 'Load Testing', type: 'info' as LogLevel, message: 'Background load monitoring active' },
        { component: 'Time Sync', type: 'info' as LogLevel, message: 'Clock synchronization drift check: ±2ms' }
      ];

      if (Math.random() > 0.7) {
        const activity = activities[Math.floor(Math.random() * activities.length)];
        dispatch({ type: 'ADD_LOG', log: {
          timestamp: Date.now(),
          type: activity.type,
          component: activity.component,
          message: activity.message
        }});
      }

      // Generate warning logs occasionally
      if (Math.random() > 0.9) {
        const serverLoad = state.servers.find(s => s.id === 'primary')?.load || 0;
        if (serverLoad > 7) {
          dispatch({ type: 'ADD_LOG', log: {
            timestamp: Date.now(),
            type: 'warning',
            component: 'System',
            message: `High server load detected: Primary server at ${serverLoad}/10`
          }});
        }
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [dispatch, state.servers]);

  const exportLogs = () => {
    const logsText = filteredLogs.map(log => 
      `[${new Date(log.timestamp).toISOString()}] [${log.type.toUpperCase()}] [${log.component}] ${log.message}`
    ).join('\n');
    
    const blob = new Blob([logsText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `traffic_system_logs_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const clearLogs = () => {
    if (confirm('Are you sure you want to clear all logs?')) {
      dispatch({ type: 'CLEAR_LOGS' });
    }
  };

  const getLogIcon = (type: LogLevel) => {
    switch (type) {
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      default: return '📝';
    }
  };

  const getLogColor = (type: LogLevel) => {
    switch (type) {
      case 'error': return 'text-red-400 bg-red-900/20 border-red-500/30';
      case 'warning': return 'text-yellow-400 bg-yellow-900/20 border-yellow-500/30';
      case 'info': return 'text-blue-400 bg-blue-900/20 border-blue-500/30';
      default: return 'text-gray-400 bg-gray-700 border-gray-600';
    }
  };

  const getComponentColor = (component: string) => {
    const colors = {
      'System': 'bg-gray-600',
      'Signal Control': 'bg-green-600',
      'VIP System': 'bg-red-600',
      'Time Sync': 'bg-blue-600',
      'Pedestrian Monitor': 'bg-purple-600',
      'Load Testing': 'bg-yellow-600'
    };
    return colors[component as keyof typeof colors] || 'bg-gray-600';
  };

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
          <h2 className="text-xl font-bold flex items-center">
            <Terminal className="mr-2" size={20} />
            System Logs & Console
          </h2>
          
          <div className="flex flex-wrap gap-2">
            <button
              onClick={exportLogs}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded transition-colors flex items-center"
            >
              <Download className="mr-1" size={16} />
              Export
            </button>
            
            <button
              onClick={clearLogs}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded transition-colors flex items-center"
            >
              <Trash2 className="mr-1" size={16} />
              Clear
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium mb-2">Component Filter</label>
            <select
              value={filterComponent}
              onChange={(e) => setFilterComponent(e.target.value as LogComponent | 'All')}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="All">All Components</option>
              <option value="System">System</option>
              <option value="Signal Control">Signal Control</option>
              <option value="VIP System">VIP System</option>
              <option value="Time Sync">Time Sync</option>
              <option value="Pedestrian Monitor">Pedestrian Monitor</option>
              <option value="Load Testing">Load Testing</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Level Filter</label>
            <select
              value={filterLevel}
              onChange={(e) => setFilterLevel(e.target.value as LogLevel | 'All')}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="All">All Levels</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-gray-400" size={16} />
              <input
                type="text"
                placeholder="Search logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex items-end">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="mr-2"
              />
              Auto-scroll
            </label>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-700 rounded p-3 text-center">
            <div className="text-2xl font-bold text-blue-400">{state.logs.length}</div>
            <div className="text-sm text-gray-400">Total Logs</div>
          </div>
          <div className="bg-gray-700 rounded p-3 text-center">
            <div className="text-2xl font-bold text-green-400">
              {state.logs.filter(log => log.type === 'info').length}
            </div>
            <div className="text-sm text-gray-400">Info</div>
          </div>
          <div className="bg-gray-700 rounded p-3 text-center">
            <div className="text-2xl font-bold text-yellow-400">
              {state.logs.filter(log => log.type === 'warning').length}
            </div>
            <div className="text-sm text-gray-400">Warnings</div>
          </div>
          <div className="bg-gray-700 rounded p-3 text-center">
            <div className="text-2xl font-bold text-red-400">
              {state.logs.filter(log => log.type === 'error').length}
            </div>
            <div className="text-sm text-gray-400">Errors</div>
          </div>
        </div>
      </div>

      {/* Log Console */}
      <div className="bg-gray-900 rounded-lg border border-gray-700">
        <div className="bg-gray-800 px-4 py-2 rounded-t-lg border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center">
            <Filter className="mr-2" size={16} />
            <span className="text-sm">
              Showing {filteredLogs.length} of {state.logs.length} logs
              {filterComponent !== 'All' && ` • ${filterComponent}`}
              {filterLevel !== 'All' && ` • ${filterLevel.toUpperCase()}`}
              {searchTerm && ` • "${searchTerm}"`}
            </span>
          </div>
          <div className="text-xs text-gray-400">
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </div>

        <div
          ref={logContainerRef}
          className="max-h-96 overflow-y-auto p-4 bg-gray-900 font-mono text-sm"
        >
          {filteredLogs.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              {searchTerm || filterComponent !== 'All' || filterLevel !== 'All' 
                ? 'No logs match the current filters' 
                : 'No logs available'
              }
            </div>
          ) : (
            <div className="space-y-2">
              {filteredLogs.map((log) => (
                <div
                  key={log.id}
                  className={`p-3 rounded border-l-4 ${getLogColor(log.type)}`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-start gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-lg">{getLogIcon(log.type)}</span>
                      <span className="text-xs text-gray-500 whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs font-semibold text-white ${getComponentColor(log.component)}`}>
                        {log.component}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="break-words">{log.message}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LogsConsole;