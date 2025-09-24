import React, { useState, useEffect } from 'react';
import { useTraffic } from '../../context/TrafficContext';
import { Users, Play, Pause, RefreshCw } from 'lucide-react';

const PedestrianMonitoring: React.FC = () => {
  const { state, dispatch } = useTraffic();
  const [monitoring, setMonitoring] = useState(true);
  const [messages, setMessages] = useState<Array<{
    id: string;
    timestamp: number;
    message: string;
    type: 'normal' | 'vip' | 'warning';
  }>>([]);

  useEffect(() => {
    if (!monitoring) return;

    const interval = setInterval(() => {
      // Generate pedestrian messages based on current signal states
      state.pedestrianSignals.forEach((pedestrianSignal) => {
        const vehicleSignal = state.signals.find(s => s.id === `T${pedestrianSignal.id.slice(1)}`);
        
        if (vehicleSignal) {
          const messageType = state.vipActive ? 'vip' : 
                            vehicleSignal.status === 'yellow' ? 'warning' : 'normal';
          
          let message = '';
          
          if (vehicleSignal.status === 'green') {
            message = `Pedestrian ${pedestrianSignal.id}: RED due to ${vehicleSignal.id} GREEN`;
          } else if (vehicleSignal.status === 'yellow') {
            message = `Pedestrian ${pedestrianSignal.id}: RED due to ${vehicleSignal.id} YELLOW`;
          } else if (vehicleSignal.status === 'red') {
            message = `Pedestrian ${pedestrianSignal.id}: GREEN - Safe to cross`;
          }

          if (message && Math.random() > 0.7) { // Don't spam messages
            setMessages(prev => [{
              id: `${Date.now()}-${pedestrianSignal.id}`,
              timestamp: Date.now(),
              message: message.replace('CLONE - ', ''), // Strip server identifiers
              type: messageType
            }, ...prev].slice(0, 100));
          }
        }
      });

      // Add VIP priority messages
      if (state.vipActive && Math.random() > 0.8) {
        setMessages(prev => [{
          id: `vip-${Date.now()}`,
          timestamp: Date.now(),
          message: 'VIP PRIORITY ACTIVE - All pedestrian crossings RED for emergency vehicle',
          type: 'vip'
        }, ...prev].slice(0, 100));
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [monitoring, state.pedestrianSignals, state.signals, state.vipActive]);

  const handleRefresh = () => {
    // Manually refresh pedestrian status
    dispatch({ type: 'ADD_LOG', log: {
      timestamp: Date.now(),
      type: 'info',
      component: 'Pedestrian Monitor',
      message: 'Manual refresh of pedestrian status'
    }});

    // Generate immediate status update
    state.pedestrianSignals.forEach((pedestrianSignal) => {
      const vehicleSignal = state.signals.find(s => s.id === `T${pedestrianSignal.id.slice(1)}`);
      if (vehicleSignal) {
        const status = vehicleSignal.status === 'red' ? 'Safe to cross' : 'Wait - do not cross';
        setMessages(prev => [{
          id: `refresh-${Date.now()}-${pedestrianSignal.id}`,
          timestamp: Date.now(),
          message: `Pedestrian ${pedestrianSignal.id}: ${status}`,
          type: 'normal'
        }, ...prev].slice(0, 100));
      }
    });
  };

  const getMessageStyle = (type: 'normal' | 'vip' | 'warning') => {
    switch (type) {
      case 'vip':
        return 'bg-red-900 border-red-500 text-red-200';
      case 'warning':
        return 'bg-yellow-900 border-yellow-500 text-yellow-200';
      default:
        return 'bg-gray-700 border-gray-500';
    }
  };

  const getMessageIcon = (type: 'normal' | 'vip' | 'warning') => {
    switch (type) {
      case 'vip':
        return '🚨';
      case 'warning':
        return '⚠️';
      default:
        return '🚶';
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold flex items-center">
            <Users className="mr-2" size={20} />
            Pedestrian Crossing Monitor
          </h2>
          
          <div className="flex space-x-2">
            <button
              onClick={() => setMonitoring(!monitoring)}
              className={`px-4 py-2 rounded transition-colors flex items-center ${
                monitoring
                  ? 'bg-red-600 hover:bg-red-700'
                  : 'bg-green-600 hover:bg-green-700'
              }`}
            >
              {monitoring ? <Pause className="mr-1" size={16} /> : <Play className="mr-1" size={16} />}
              {monitoring ? 'Stop' : 'Start'} Monitor
            </button>
            
            <button
              onClick={handleRefresh}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors flex items-center"
            >
              <RefreshCw className="mr-1" size={16} />
              Manual Refresh
            </button>
          </div>
        </div>

        {monitoring && (
          <div className="mb-4 p-3 bg-green-900 border border-green-600 rounded flex items-center">
            <span className="animate-pulse text-green-400 mr-2">●</span>
            <span>Real-time monitoring active - Updates every 2 seconds</span>
          </div>
        )}

        {state.vipActive && (
          <div className="mb-4 p-3 bg-red-900 border border-red-500 rounded animate-pulse">
            <div className="flex items-center">
              <span className="text-red-400 mr-2 text-xl">🚨</span>
              <span className="font-bold">VIP EMERGENCY - All pedestrian crossings on hold</span>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
        {state.pedestrianSignals.map((pedestrianSignal) => {
          const vehicleSignal = state.signals.find(s => s.id === `T${pedestrianSignal.id.slice(1)}`);
          return (
            <div key={pedestrianSignal.id} className="bg-gray-800 rounded-lg p-4">
              <h3 className="font-semibold mb-2">Crossing {pedestrianSignal.id}</h3>
              <div className="text-center">
                <div className={`w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center text-2xl ${
                  pedestrianSignal.status === 'green' && vehicleSignal?.status === 'red'
                    ? 'bg-green-500 text-white' 
                    : 'bg-red-500 text-white'
                }`}>
                  🚶
                </div>
                <p className={`text-sm font-semibold ${
                  pedestrianSignal.status === 'green' && vehicleSignal?.status === 'red'
                    ? 'text-green-400' 
                    : 'text-red-400'
                }`}>
                  {pedestrianSignal.status === 'green' && vehicleSignal?.status === 'red' 
                    ? 'WALK' 
                    : 'WAIT'
                  }
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Vehicle {vehicleSignal?.id}: {vehicleSignal?.status?.toUpperCase()}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Real-time Pedestrian Messages</h3>
        
        <div className="max-h-96 overflow-y-auto space-y-2">
          {messages.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              {monitoring ? 'Monitoring for pedestrian updates...' : 'Start monitoring to see messages'}
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`p-3 rounded border-l-4 ${getMessageStyle(msg.type)} ${
                  msg.type === 'vip' ? 'animate-pulse' : ''
                }`}
              >
                <div className="flex items-start">
                  <span className="mr-2 text-lg">{getMessageIcon(msg.type)}</span>
                  <div className="flex-1">
                    <p className="text-sm">{msg.message}</p>
                    <p className="text-xs opacity-75 mt-1">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {messages.length > 0 && (
          <button
            onClick={() => setMessages([])}
            className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 rounded transition-colors text-sm"
          >
            Clear Messages
          </button>
        )}
      </div>
    </div>
  );
};

export default PedestrianMonitoring;