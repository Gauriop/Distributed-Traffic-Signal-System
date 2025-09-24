import React, { useState } from 'react';
import { useTraffic } from '../../context/TrafficContext';
import { Clock, Users, CheckCircle } from 'lucide-react';

const TimeSync: React.FC = () => {
  const { state, dispatch } = useTraffic();
  const [clientTimes, setClientTimes] = useState({
    'signal-manipulator': '',
    'vehicle-controller': '',
    'manual-vip': '',
    'pedestrian-controller': ''
  });
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const validateTime = (time: string): boolean => {
    const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$/;
    return timeRegex.test(time);
  };

  const handleTimeChange = (clientId: string, time: string) => {
    setClientTimes(prev => ({ ...prev, [clientId]: time }));
    
    if (time && !validateTime(time)) {
      setErrors(prev => ({ ...prev, [clientId]: 'Invalid time format. Use HH:MM:SS' }));
    } else {
      setErrors(prev => ({ ...prev, [clientId]: '' }));
    }
  };

  const handleRegisterTimes = () => {
    const validTimes = Object.entries(clientTimes).filter(([_, time]) => 
      time && validateTime(time)
    );

    if (validTimes.length === 0) {
      alert('Please enter at least one valid time in HH:MM:SS format');
      return;
    }

    validTimes.forEach(([clientId, time]) => {
      dispatch({ type: 'SET_CLIENT_TIME', clientId, time });
      dispatch({ type: 'ADD_LOG', log: {
        timestamp: Date.now(),
        type: 'info',
        component: 'Time Sync',
        message: `Registered time for ${clientId}: ${time}`
      }});
    });

    // Simulate Berkeley synchronization
    setTimeout(() => {
      const avgTime = new Date();
      const syncedTime = avgTime.toLocaleTimeString();
      dispatch({ type: 'SET_SYNCHRONIZED_TIME', time: syncedTime });
      dispatch({ type: 'ADD_LOG', log: {
        timestamp: Date.now(),
        type: 'info',
        component: 'Time Sync',
        message: `Berkeley synchronization completed. Synchronized time: ${syncedTime}`
      }});
    }, 1000);
  };

  const clients = [
    { id: 'signal-manipulator', name: 'Signal Manipulator (Server)' },
    { id: 'vehicle-controller', name: 'Vehicle Controller' },
    { id: 'manual-vip', name: 'Manual VIP Controller' },
    { id: 'pedestrian-controller', name: 'Pedestrian Controller' }
  ];

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center">
          <Clock className="mr-2" size={20} />
          Client Time Registration
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {clients.map((client) => (
            <div key={client.id} className="space-y-2">
              <label className="block text-sm font-medium">{client.name}</label>
              <input
                type="text"
                placeholder="HH:MM:SS"
                value={clientTimes[client.id]}
                onChange={(e) => handleTimeChange(client.id, e.target.value)}
                className={`w-full px-3 py-2 bg-gray-700 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors[client.id] ? 'border-red-500' : 'border-gray-600'
                }`}
              />
              {errors[client.id] && (
                <p className="text-red-400 text-xs">{errors[client.id]}</p>
              )}
            </div>
          ))}
        </div>

        <button
          onClick={handleRegisterTimes}
          className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-md transition-colors flex items-center"
        >
          <Users className="mr-2" size={16} />
          Register Times & Synchronize
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Registered Client Times</h2>
          
          {Object.keys(state.clientTimes).length === 0 ? (
            <p className="text-gray-400">No client times registered yet</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(state.clientTimes).map(([clientId, time]) => (
                <div key={clientId} className="flex justify-between items-center p-2 bg-gray-700 rounded">
                  <span className="capitalize">{clientId.replace('-', ' ')}</span>
                  <span className="font-mono text-green-400">{time}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center">
            <CheckCircle className="mr-2" size={20} />
            Synchronized Time
          </h2>
          
          <div className="text-center">
            <div className="text-3xl font-mono text-green-400 mb-2">
              {state.synchronizedTime}
            </div>
            <p className="text-sm text-gray-400">
              Updated every second
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TimeSync;