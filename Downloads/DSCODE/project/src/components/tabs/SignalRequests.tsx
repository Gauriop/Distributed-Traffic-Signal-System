import React, { useState, useEffect, useCallback } from 'react';
import { useTraffic } from '../../context/TrafficContext';
import { Play, Pause, Settings, Zap, Car, AlertTriangle } from 'lucide-react';

const SignalRequests: React.FC = () => {
  const { state, dispatch } = useTraffic();
  const [requestCount, setRequestCount] = useState(0);
  const [successCount, setSuccessCount] = useState(0);
  const [vipCount, setVipCount] = useState(0);
  const [requestHistory, setRequestHistory] = useState<Array<{
    id: number;
    type: 'regular' | 'vip';
    signal: string;
    status: 'success' | 'failure';
    timestamp: number;
  }>>([]);

  const generateRandomSignal = () => `T${Math.floor(Math.random() * 4) + 1}`;
  
  const processSignalRequest = useCallback((signal: string, isVip: boolean = false) => {
    const success = Math.random() > 0.1; // 90% success rate
    const requestId = Date.now() + Math.random();
    
    setRequestCount(prev => prev + 1);
    if (success) setSuccessCount(prev => prev + 1);
    if (isVip) setVipCount(prev => prev + 1);

    setRequestHistory(prev => [{
      id: requestId,
      type: isVip ? 'vip' : 'regular',
      signal,
      status: success ? 'success' : 'failure',
      timestamp: Date.now()
    }, ...prev].slice(0, 50));

    dispatch({ type: 'ADD_LOG', log: {
      timestamp: Date.now(),
      type: 'info',
      component: 'Signal Control',
      message: `${isVip ? 'VIP' : 'Regular'} request initiated for ${signal}`
    }});

    if (success) {
      if (isVip) {
        dispatch({ type: 'SET_VIP_ACTIVE', active: true });
        dispatch({ type: 'ADD_LOG', log: {
          timestamp: Date.now(),
          type: 'warning',
          component: 'VIP System',
          message: `VIP request processed: ${signal} is now YELLOW (priority transition)`
        }});

        // VIP gets immediate priority
        dispatch({ type: 'UPDATE_SIGNAL', signalId: signal, status: 'yellow' });
        dispatch({ type: 'SET_ACTIVE_SIGNAL', signal });
        
        setTimeout(() => {
          dispatch({ type: 'UPDATE_SIGNAL', signalId: signal, status: 'green' });
          dispatch({ type: 'ADD_LOG', log: {
            timestamp: Date.now(),
            type: 'info',
            component: 'VIP System',
            message: `${signal} is now GREEN (VIP priority)`
          }});

          setTimeout(() => {
            dispatch({ type: 'UPDATE_SIGNAL', signalId: signal, status: 'yellow' });
            dispatch({ type: 'ADD_LOG', log: {
              timestamp: Date.now(),
              type: 'info',
              component: 'Signal Control',
              message: `${signal} is now YELLOW (end transition)`
            }});

            setTimeout(() => {
              dispatch({ type: 'UPDATE_SIGNAL', signalId: signal, status: 'red' });
              dispatch({ type: 'SET_VIP_ACTIVE', active: false });
              dispatch({ type: 'SET_ACTIVE_SIGNAL', signal: null });
              dispatch({ type: 'ADD_LOG', log: {
                timestamp: Date.now(),
                type: 'info',
                component: 'VIP System',
                message: `${signal} is now RED (VIP sequence complete)`
              }});
            }, 2000);
          }, 3000);
        }, 2000);
      } else {
        // Regular signal processing
        dispatch({ type: 'SET_ACTIVE_SIGNAL', signal });
        dispatch({ type: 'UPDATE_SIGNAL', signalId: signal, status: 'yellow' });
        dispatch({ type: 'ADD_LOG', log: {
          timestamp: Date.now(),
          type: 'info',
          component: 'Signal Control',
          message: `${signal} is now YELLOW (transition)`
        }});

        setTimeout(() => {
          dispatch({ type: 'UPDATE_SIGNAL', signalId: signal, status: 'green' });
          dispatch({ type: 'ADD_LOG', log: {
            timestamp: Date.now(),
            type: 'info',
            component: 'Signal Control',
            message: `${signal} is now GREEN`
          }});

          setTimeout(() => {
            dispatch({ type: 'UPDATE_SIGNAL', signalId: signal, status: 'yellow' });
            dispatch({ type: 'ADD_LOG', log: {
              timestamp: Date.now(),
              type: 'info',
              component: 'Signal Control',
              message: `${signal} is now YELLOW (end transition)`
            }});

            setTimeout(() => {
              dispatch({ type: 'UPDATE_SIGNAL', signalId: signal, status: 'red' });
              dispatch({ type: 'SET_ACTIVE_SIGNAL', signal: null });
              dispatch({ type: 'ADD_LOG', log: {
                timestamp: Date.now(),
                type: 'info',
                component: 'Signal Control',
                message: `${signal} is now RED`
              }});
            }, 2000);
          }, 5000);
        }, 2000);
      }

      dispatch({ type: 'UPDATE_STATS', stats: { 
        totalRequests: state.systemStats.totalRequests + 1,
        vipRequests: isVip ? state.systemStats.vipRequests + 1 : state.systemStats.vipRequests
      }});
    } else {
      dispatch({ type: 'ADD_LOG', log: {
        timestamp: Date.now(),
        type: 'error',
        component: isVip ? 'VIP System' : 'Signal Control',
        message: `Request failed for ${signal}`
      }});
      dispatch({ type: 'UPDATE_STATS', stats: { 
        failedRequests: state.systemStats.failedRequests + 1 
      }});
    }
  }, [state.systemStats, dispatch]);

  // Auto-generation effect
  useEffect(() => {
    if (!state.autoGenerateSignals) return;

    const interval = setInterval(() => {
      if (state.animationPaused) return;
      
      // Generate 1-2 random requests
      const numRequests = Math.random() > 0.7 ? 2 : 1;
      
      for (let i = 0; i < numRequests; i++) {
        setTimeout(() => {
          const signal = generateRandomSignal();
          processSignalRequest(signal);
        }, i * 500); // Stagger multiple requests
      }
    }, state.autoGenerateInterval * 1000);

    return () => clearInterval(interval);
  }, [state.autoGenerateSignals, state.autoGenerateInterval, processSignalRequest]);

  const handleManualRequest = () => {
    const signal = generateRandomSignal();
    processSignalRequest(signal);
    
    dispatch({ type: 'ADD_LOG', log: {
      timestamp: Date.now(),
      type: 'info',
      component: 'Signal Control',
      message: `Manual request generated for ${signal}`
    }});
  };

  const handleVipRequest = (route: number) => {
    const signal = `T${route}`;
    processSignalRequest(signal, true);
  };

  const successRate = requestCount > 0 ? ((successCount / requestCount) * 100).toFixed(1) : '0';

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Regular Requests Section */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center">
            <Car className="mr-2" size={20} />
            Regular Signal Requests
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-700 rounded">
              <div className="flex items-center">
                <span className="mr-3">Automatic Generation</span>
                {state.autoGenerateSignals && !state.animationPaused && (
                  <span className="text-green-400 animate-pulse">●</span>
                )}
              </div>
              <button
                onClick={() => dispatch({ type: 'TOGGLE_AUTO_GENERATE' })}
                className={`px-4 py-2 rounded transition-colors flex items-center ${
                  state.autoGenerateSignals
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                {state.autoGenerateSignals ? <Pause className="mr-1" size={16} /> : <Play className="mr-1" size={16} />}
                {state.autoGenerateSignals ? 'Stop' : 'Start'}
              </button>
            </div>
            
            {state.autoGenerateSignals && (
              <div className="p-3 bg-blue-900 border border-blue-600 rounded">
                <div className="flex items-center">
                  <span className="text-blue-400 animate-pulse mr-2">⚡</span>
                  <span className="text-sm">Auto-generating signals every {state.autoGenerateInterval}s</span>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <label className="block text-sm font-medium">Generation Interval (seconds)</label>
              <input
                type="range"
                min="1"
                max="10"
                value={state.autoGenerateInterval}
                onChange={(e) => dispatch({ type: 'SET_AUTO_INTERVAL', interval: parseInt(e.target.value) })}
                className="w-full"
              />
              <div className="text-center text-sm text-gray-400">
                {state.autoGenerateInterval}s
              </div>
            </div>

            <button
              onClick={handleManualRequest}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors flex items-center justify-center"
            >
              <Zap className="mr-2" size={16} />
              Generate Manual Request
            </button>

            <div className="grid grid-cols-3 gap-3 text-center text-sm">
              <div>
                <div className="font-bold text-lg">{requestCount}</div>
                <div className="text-gray-400">Total</div>
              </div>
              <div>
                <div className="font-bold text-lg text-green-400">{successCount}</div>
                <div className="text-gray-400">Success</div>
              </div>
              <div>
                <div className="font-bold text-lg">{successRate}%</div>
                <div className="text-gray-400">Rate</div>
              </div>
            </div>
          </div>
        </div>

        {/* VIP Requests Section */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center">
            <AlertTriangle className="mr-2 text-red-400" size={20} />
            VIP Signal Requests
          </h2>
          
          <div className="space-y-4">
            <p className="text-sm text-gray-400">
              VIP requests have priority and will interrupt regular signals
            </p>
            
            <div className="grid grid-cols-2 gap-2">
              {[1, 2, 3, 4].map((route) => (
                <button
                  key={route}
                  onClick={() => handleVipRequest(route)}
                  disabled={state.vipActive}
                  className="px-4 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 rounded transition-colors font-semibold"
                >
                  VIP Route {route}
                </button>
              ))}
            </div>

            {state.vipActive && (
              <div className="p-3 bg-red-900 border border-red-600 rounded">
                <div className="flex items-center">
                  <AlertTriangle className="mr-2 text-red-400" size={16} />
                  <span className="font-semibold">VIP Request Active</span>
                </div>
                <p className="text-sm mt-1">Priority signal processing in progress...</p>
              </div>
            )}

            <div className="text-center">
              <div className="font-bold text-lg text-red-400">{vipCount}</div>
              <div className="text-gray-400 text-sm">Total VIP Requests</div>
            </div>
          </div>
        </div>
      </div>

      {/* Request History */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Request History</h2>
        
        <div className="max-h-96 overflow-y-auto space-y-2">
          {requestHistory.length === 0 ? (
            <p className="text-gray-400 text-center py-8">No requests yet</p>
          ) : (
            requestHistory.map((request) => (
              <div
                key={request.id}
                className={`p-3 rounded border-l-4 ${
                  request.type === 'vip'
                    ? 'bg-red-900 border-red-500'
                    : request.status === 'success'
                    ? 'bg-green-900 border-green-500'
                    : 'bg-red-900 border-red-500'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <span className={`font-semibold ${request.type === 'vip' ? 'text-red-400' : 'text-blue-400'}`}>
                      {request.type.toUpperCase()}
                    </span>
                    <span className="ml-2">Signal {request.signal}</span>
                    <div className="text-sm text-gray-400 mt-1">
                      {new Date(request.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    request.status === 'success' ? 'bg-green-600' : 'bg-red-600'
                  }`}>
                    {request.status.toUpperCase()}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default SignalRequests;