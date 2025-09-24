import React, { useState } from 'react';
import { useTraffic } from '../../context/TrafficContext';
import { Play, BarChart3, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface TestResult {
  id: number;
  status: 'success' | 'failure' | 'timeout';
  responseTime: number;
  server: string;
}

const LoadTesting: React.FC = () => {
  const { state, dispatch } = useTraffic();
  const [testConfig, setTestConfig] = useState({
    simultaneousQueries: 15,
    timeoutMs: 5000,
    testType: 'signal_status' as 'signal_status' | 'vip_request' | 'mixed'
  });
  const [isRunning, setIsRunning] = useState(false);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [testStats, setTestStats] = useState({
    totalRequests: 0,
    successCount: 0,
    failureCount: 0,
    timeoutCount: 0,
    averageResponseTime: 0,
    requestsPerSecond: 0,
    testDuration: 0,
    loadBalancingEffectiveness: 0
  });
  const [progress, setProgress] = useState(0);
  const [testLog, setTestLog] = useState<string[]>([]);

  const simulateRequest = async (requestId: number): Promise<TestResult> => {
    const startTime = Date.now();
    const servers = ['primary', 'clone', 'load-balancer'];
    const selectedServer = servers[Math.floor(Math.random() * servers.length)];
    
    // Simulate network delay
    const baseDelay = Math.random() * 100 + 50; // 50-150ms base delay
    const serverLoad = state.servers.find(s => s.id === selectedServer)?.load || 0;
    const loadDelay = serverLoad * 10; // Additional delay based on server load
    
    const totalDelay = baseDelay + loadDelay;
    
    return new Promise((resolve) => {
      setTimeout(() => {
        const responseTime = Date.now() - startTime;
        
        // Determine outcome based on server load and random factors
        let status: 'success' | 'failure' | 'timeout' = 'success';
        
        if (responseTime > testConfig.timeoutMs) {
          status = 'timeout';
        } else if (Math.random() < 0.1 + (serverLoad / 100)) { // Higher load = more failures
          status = 'failure';
        }
        
        resolve({
          id: requestId,
          status,
          responseTime,
          server: selectedServer
        });
      }, Math.min(totalDelay, testConfig.timeoutMs + 100));
    });
  };

  const runLoadTest = async () => {
    setIsRunning(true);
    setProgress(0);
    setTestResults([]);
    setTestLog(['Starting load test...']);
    
    const testStartTime = Date.now();
    const requests: Promise<TestResult>[] = [];
    
    // Create all requests
    for (let i = 1; i <= testConfig.simultaneousQueries; i++) {
      requests.push(simulateRequest(i));
      setTestLog(prev => [...prev, `Initiated request #${i} (${testConfig.testType})`]);
    }
    
    // Execute requests and update progress
    const results: TestResult[] = [];
    let completed = 0;
    
    const allResults = await Promise.allSettled(requests);
    
    allResults.forEach((result, index) => {
      completed++;
      setProgress((completed / testConfig.simultaneousQueries) * 100);
      
      if (result.status === 'fulfilled') {
        results.push(result.value);
        setTestLog(prev => [...prev, 
          `Request #${index + 1}: ${result.value.status.toUpperCase()} (${result.value.responseTime}ms) - ${result.value.server}`
        ]);
      } else {
        const failedResult: TestResult = {
          id: index + 1,
          status: 'failure',
          responseTime: testConfig.timeoutMs,
          server: 'unknown'
        };
        results.push(failedResult);
        setTestLog(prev => [...prev, `Request #${index + 1}: FAILED - ${result.reason}`]);
      }
    });
    
    const testEndTime = Date.now();
    const testDuration = (testEndTime - testStartTime) / 1000;
    
    // Calculate statistics
    const successCount = results.filter(r => r.status === 'success').length;
    const failureCount = results.filter(r => r.status === 'failure').length;
    const timeoutCount = results.filter(r => r.status === 'timeout').length;
    const averageResponseTime = results.reduce((sum, r) => sum + r.responseTime, 0) / results.length;
    const requestsPerSecond = results.length / testDuration;
    
    // Calculate load balancing effectiveness
    const serverDistribution = results.reduce((acc, r) => {
      acc[r.server] = (acc[r.server] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const loadBalancingEffectiveness = Object.keys(serverDistribution).length > 1 ? 
      (1 - Math.max(...Object.values(serverDistribution)) / results.length) * 100 : 0;
    
    setTestResults(results);
    setTestStats({
      totalRequests: results.length,
      successCount,
      failureCount,
      timeoutCount,
      averageResponseTime,
      requestsPerSecond,
      testDuration,
      loadBalancingEffectiveness
    });
    
    setTestLog(prev => [...prev, 
      `Test completed in ${testDuration.toFixed(2)}s`,
      `Success rate: ${((successCount / results.length) * 100).toFixed(1)}%`,
      `Average response time: ${averageResponseTime.toFixed(2)}ms`,
      `Requests per second: ${requestsPerSecond.toFixed(2)}`,
      `Load balancing effectiveness: ${loadBalancingEffectiveness.toFixed(1)}%`
    ]);
    
    // Update system stats
    dispatch({ type: 'UPDATE_STATS', stats: {
      totalRequests: state.systemStats.totalRequests + results.length,
      failedRequests: state.systemStats.failedRequests + failureCount,
      timeouts: state.systemStats.timeouts + timeoutCount
    }});
    
    dispatch({ type: 'ADD_LOG', log: {
      timestamp: Date.now(),
      type: 'info',
      component: 'Load Testing',
      message: `Load test completed: ${successCount}/${results.length} successful requests`
    }});
    
    setIsRunning(false);
  };

  const exportResults = () => {
    const data = {
      testConfig,
      testStats,
      results: testResults,
      timestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `load_test_results_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-400';
      case 'failure': return 'text-red-400';
      case 'timeout': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle size={16} className="text-green-400" />;
      case 'failure': return <AlertTriangle size={16} className="text-red-400" />;
      case 'timeout': return <Clock size={16} className="text-yellow-400" />;
      default: return null;
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center">
          <BarChart3 className="mr-2" size={20} />
          Load Testing Configuration
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium mb-2">Simultaneous Queries</label>
            <input
              type="number"
              min="1"
              max="100"
              value={testConfig.simultaneousQueries}
              onChange={(e) => setTestConfig(prev => ({ ...prev, simultaneousQueries: parseInt(e.target.value) || 15 }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isRunning}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Timeout (ms)</label>
            <input
              type="number"
              min="1000"
              max="30000"
              value={testConfig.timeoutMs}
              onChange={(e) => setTestConfig(prev => ({ ...prev, timeoutMs: parseInt(e.target.value) || 5000 }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isRunning}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Test Type</label>
            <select
              value={testConfig.testType}
              onChange={(e) => setTestConfig(prev => ({ ...prev, testType: e.target.value as any }))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isRunning}
            >
              <option value="signal_status">Signal Status Queries</option>
              <option value="vip_request">VIP Requests</option>
              <option value="mixed">Mixed Load</option>
            </select>
          </div>
        </div>
        
        <div className="flex space-x-4">
          <button
            onClick={runLoadTest}
            disabled={isRunning}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-md transition-colors flex items-center"
          >
            <Play className="mr-2" size={16} />
            {isRunning ? 'Running Test...' : 'Start Load Test'}
          </button>
          
          {testResults.length > 0 && (
            <button
              onClick={exportResults}
              className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-md transition-colors"
            >
              Export Results
            </button>
          )}
        </div>
        
        {isRunning && (
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-1">
              <span>Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-gray-600 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>

      {testStats.totalRequests > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-1">Success Rate</h3>
            <p className="text-2xl font-bold text-green-400">
              {((testStats.successCount / testStats.totalRequests) * 100).toFixed(1)}%
            </p>
            <p className="text-sm text-gray-500">{testStats.successCount}/{testStats.totalRequests}</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-1">Avg Response Time</h3>
            <p className="text-2xl font-bold text-blue-400">{testStats.averageResponseTime.toFixed(0)}ms</p>
            <p className="text-sm text-gray-500">Target: &lt;{testConfig.timeoutMs}ms</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-1">Requests/Second</h3>
            <p className="text-2xl font-bold text-yellow-400">{testStats.requestsPerSecond.toFixed(2)}</p>
            <p className="text-sm text-gray-500">Duration: {testStats.testDuration.toFixed(2)}s</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-1">Load Balancing</h3>
            <p className="text-2xl font-bold text-purple-400">{testStats.loadBalancingEffectiveness.toFixed(1)}%</p>
            <p className="text-sm text-gray-500">Distribution effectiveness</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Test Results Summary</h3>
          
          {testResults.length === 0 ? (
            <p className="text-gray-400 text-center py-8">No test results yet. Run a load test to see results.</p>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="bg-green-900 rounded p-3">
                  <div className="text-2xl font-bold text-green-400">{testStats.successCount}</div>
                  <div className="text-sm text-gray-300">Success</div>
                </div>
                <div className="bg-red-900 rounded p-3">
                  <div className="text-2xl font-bold text-red-400">{testStats.failureCount}</div>
                  <div className="text-sm text-gray-300">Failures</div>
                </div>
                <div className="bg-yellow-900 rounded p-3">
                  <div className="text-2xl font-bold text-yellow-400">{testStats.timeoutCount}</div>
                  <div className="text-sm text-gray-300">Timeouts</div>
                </div>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-semibold">Performance Analysis</h4>
                <div className="text-sm space-y-1">
                  <p>• Average response time: {testStats.averageResponseTime.toFixed(2)}ms</p>
                  <p>• Throughput: {testStats.requestsPerSecond.toFixed(2)} requests/second</p>
                  <p>• Load balancing effectiveness: {testStats.loadBalancingEffectiveness.toFixed(1)}%</p>
                  <p className={`${testStats.loadBalancingEffectiveness > 50 ? 'text-green-400' : 'text-yellow-400'}`}>
                    • {testStats.loadBalancingEffectiveness > 50 ? 'Good' : 'Fair'} request distribution across servers
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Test Log</h3>
          
          <div className="bg-gray-900 rounded p-3 max-h-96 overflow-y-auto">
            {testLog.length === 0 ? (
              <p className="text-gray-400 text-center">No test activity yet</p>
            ) : (
              <div className="space-y-1 text-sm font-mono">
                {testLog.map((log, index) => (
                  <div key={index} className="text-gray-300">
                    <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span> {log}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          {testLog.length > 0 && (
            <button
              onClick={() => setTestLog([])}
              className="mt-3 px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm transition-colors"
            >
              Clear Log
            </button>
          )}
        </div>
      </div>

      {testResults.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Individual Request Results</h3>
          
          <div className="max-h-96 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-700 sticky top-0">
                <tr>
                  <th className="text-left p-2">Request #</th>
                  <th className="text-left p-2">Status</th>
                  <th className="text-left p-2">Response Time</th>
                  <th className="text-left p-2">Server</th>
                </tr>
              </thead>
              <tbody>
                {testResults.map((result) => (
                  <tr key={result.id} className="border-t border-gray-600">
                    <td className="p-2">#{result.id}</td>
                    <td className="p-2">
                      <div className="flex items-center">
                        {getStatusIcon(result.status)}
                        <span className={`ml-2 capitalize ${getStatusColor(result.status)}`}>
                          {result.status}
                        </span>
                      </div>
                    </td>
                    <td className="p-2 font-mono">{result.responseTime}ms</td>
                    <td className="p-2 capitalize">{result.server}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default LoadTesting;