import React, { useState, useEffect, useRef } from 'react';
import { useTraffic } from '../../context/TrafficContext';
import { Play, Pause, RotateCcw, Activity } from 'lucide-react';

interface Vehicle {
  id: string;
  type: 'normal' | 'vip';
  signal: string;
  x: number;
  y: number;
  angle: number;
  progress: number;
}

interface Pedestrian {
  id: string;
  signal: string;
  x: number;
  y: number;
  progress: number;
}

const SignalStatus: React.FC = () => {
  const { state, dispatch } = useTraffic();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [pedestrians, setPedestrians] = useState<Pedestrian[]>([]);
  const animationRef = useRef<number>();

  // Animation loop
  useEffect(() => {
    if (state.animationPaused) return;

    const animate = () => {
      // Update vehicles
      setVehicles(prev => prev.map(vehicle => {
        const speed = vehicle.type === 'vip' ? 0.04 : 0.02;
        const newProgress = vehicle.progress + speed * state.animationSpeed;
        
        if (newProgress >= 1) {
          return null; // Remove completed vehicles
        }

        // Calculate position based on signal and progress
        const centerX = 200;
        const centerY = 200;
        let newX = vehicle.x;
        let newY = vehicle.y;

        switch (vehicle.signal) {
          case 'T1': // From bottom
            newX = centerX;
            newY = 400 - (newProgress * 200);
            break;
          case 'T2': // From right  
            newX = 400 - (newProgress * 200);
            newY = centerY;
            break;
          case 'T3': // From top
            newX = centerX;
            newY = newProgress * 200;
            break;
          case 'T4': // From left
            newX = newProgress * 200;
            newY = centerY;
            break;
        }

        return { ...vehicle, x: newX, y: newY, progress: newProgress };
      }).filter(Boolean) as Vehicle[]);

      // Update pedestrians
      setPedestrians(prev => prev.map(pedestrian => {
        const newProgress = pedestrian.progress + 0.025 * state.animationSpeed;
        
        if (newProgress >= 1) {
          return null; // Remove completed pedestrians
        }

        // Calculate pedestrian position
        let newX = pedestrian.x;
        let newY = pedestrian.y;

        switch (pedestrian.signal) {
          case 'P1': // Bottom crossing
            newX = 150 + (newProgress * 100);
            newY = 350;
            break;
          case 'P2': // Right crossing
            newX = 350;
            newY = 150 + (newProgress * 100);
            break;
          case 'P3': // Top crossing
            newX = 250 - (newProgress * 100);
            newY = 50;
            break;
          case 'P4': // Left crossing
            newX = 50;
            newY = 250 - (newProgress * 100);
            break;
        }

        return { ...pedestrian, x: newX, y: newY, progress: newProgress };
      }).filter(Boolean) as Pedestrian[]);

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [state.animationSpeed, state.animationPaused]);

  // Spawn vehicles when signals change
  useEffect(() => {
    if (state.activeSignal && !state.animationPaused) {
      const signalState = state.signals.find(s => s.id === state.activeSignal);
      
      if (signalState?.status === 'green') {
        const vehicleType = state.vipActive ? 'vip' : 'normal';
        
        // Starting positions for each signal
        let startX = 200, startY = 400;
        switch (state.activeSignal) {
          case 'T1': startX = 200; startY = 400; break;
          case 'T2': startX = 400; startY = 200; break;
          case 'T3': startX = 200; startY = 0; break;
          case 'T4': startX = 0; startY = 200; break;
        }

        const newVehicle: Vehicle = {
          id: `${Date.now()}-${Math.random()}`,
          type: vehicleType,
          signal: state.activeSignal,
          x: startX,
          y: startY,
          angle: 0,
          progress: 0
        };

        setVehicles(prev => [...prev, newVehicle]);
      }
    }
  }, [state.activeSignal, state.vipActive, state.signals, state.animationPaused]);

  // Spawn pedestrians when pedestrian signals are green
  useEffect(() => {
    state.pedestrianSignals.forEach(pedSignal => {
      const vehicleSignal = state.signals.find(s => s.id === `T${pedSignal.id.slice(1)}`);
      
      if (vehicleSignal?.status === 'red' && Math.random() > 0.95 && !state.animationPaused) {
        // Starting positions for each pedestrian signal
        let startX = 150, startY = 350;
        switch (pedSignal.id) {
          case 'P1': startX = 150; startY = 350; break;
          case 'P2': startX = 350; startY = 150; break;
          case 'P3': startX = 250; startY = 50; break;
          case 'P4': startX = 50; startY = 250; break;
        }

        const newPedestrian: Pedestrian = {
          id: `${Date.now()}-${Math.random()}`,
          signal: pedSignal.id,
          x: startX,
          y: startY,
          progress: 0
        };

        setPedestrians(prev => [...prev, newPedestrian]);
      }
    });
  }, [state.pedestrianSignals, state.signals, state.animationPaused]);

  // Canvas drawing
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = '#1f2937';
    ctx.fillRect(0, 0, 400, 400);

    // Draw roads
    ctx.fillStyle = '#374151';
    ctx.fillRect(0, 175, 400, 50); // Horizontal road
    ctx.fillRect(175, 0, 50, 400); // Vertical road

    // Draw intersection
    ctx.fillStyle = '#4b5563';
    ctx.fillRect(175, 175, 50, 50);

    // Draw lane markings
    ctx.strokeStyle = '#fbbf24';
    ctx.setLineDash([10, 10]);
    ctx.lineWidth = 2;
    
    // Horizontal lane divider
    ctx.beginPath();
    ctx.moveTo(0, 200);
    ctx.lineTo(175, 200);
    ctx.moveTo(225, 200);
    ctx.lineTo(400, 200);
    ctx.stroke();
    
    // Vertical lane divider
    ctx.beginPath();
    ctx.moveTo(200, 0);
    ctx.lineTo(200, 175);
    ctx.moveTo(200, 225);
    ctx.lineTo(200, 400);
    ctx.stroke();

    ctx.setLineDash([]);

    // Draw traffic signals
    state.signals.forEach((signal, index) => {
      const positions = [
        { x: 190, y: 160 }, // T1
        { x: 240, y: 190 }, // T2
        { x: 210, y: 240 }, // T3
        { x: 160, y: 210 }, // T4
      ];

      const pos = positions[index];
      const color = signal.status === 'green' ? '#10b981' : 
                   signal.status === 'yellow' ? '#f59e0b' : '#ef4444';

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 8, 0, 2 * Math.PI);
      ctx.fill();

      // Signal label
      ctx.fillStyle = '#ffffff';
      ctx.font = '10px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(signal.id, pos.x, pos.y + 20);
    });

    // Draw pedestrian crossings
    state.pedestrianSignals.forEach((pedSignal, index) => {
      const positions = [
        { x: 200, y: 350 }, // P1
        { x: 350, y: 200 }, // P2
        { x: 200, y: 50 },  // P3
        { x: 50, y: 200 },  // P4
      ];

      const pos = positions[index];
      const vehicleSignal = state.signals.find(s => s.id === `T${pedSignal.id.slice(1)}`);
      const color = vehicleSignal?.status === 'red' ? '#10b981' : '#ef4444';

      ctx.fillStyle = color;
      ctx.fillRect(pos.x - 10, pos.y - 5, 20, 10);

      // Pedestrian label
      ctx.fillStyle = '#ffffff';
      ctx.font = '8px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(pedSignal.id, pos.x, pos.y + 25);
    });

    // Draw vehicles
    vehicles.forEach(vehicle => {
      if (vehicle.type === 'vip') {
        ctx.fillStyle = '#ef4444';
        ctx.fillRect(vehicle.x - 8, vehicle.y - 15, 16, 30);
        // VIP siren effect
        if (Math.floor(Date.now() / 200) % 2) {
          ctx.fillStyle = '#fbbf24';
          ctx.fillRect(vehicle.x - 4, vehicle.y - 18, 8, 6);
        }
      } else {
        ctx.fillStyle = '#3b82f6';
        ctx.fillRect(vehicle.x - 6, vehicle.y - 12, 12, 24);
      }
    });

    // Draw pedestrians
    pedestrians.forEach(pedestrian => {
      ctx.fillStyle = '#000000';
      ctx.beginPath();
      ctx.arc(pedestrian.x, pedestrian.y, 4, 0, 2 * Math.PI);
      ctx.fill();
    });

  }, [vehicles, pedestrians, state.signals, state.pedestrianSignals]);

  const resetAnimation = () => {
    setVehicles([]);
    setPedestrians([]);
  };

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold flex items-center">
            <Activity className="mr-2" size={20} />
            Animated Intersection Visualization
          </h2>
          
          <div className="flex space-x-2">
            <button
              onClick={() => dispatch({ type: 'TOGGLE_ANIMATION' })}
              className={`px-4 py-2 rounded transition-colors flex items-center ${
                state.animationPaused
                  ? 'bg-green-600 hover:bg-green-700'
                  : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              {state.animationPaused ? <Play className="mr-1" size={16} /> : <Pause className="mr-1" size={16} />}
              {state.animationPaused ? 'Resume' : 'Pause'} Animation
            </button>
            
            <button
              onClick={resetAnimation}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors flex items-center"
            >
              <RotateCcw className="mr-1" size={16} />
              Reset
            </button>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex-1">
            <canvas
              ref={canvasRef}
              width={400}
              height={400}
              className="border border-gray-600 rounded bg-gray-900"
            />
          </div>

          <div className="lg:w-64 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Animation Speed</label>
              <input
                type="range"
                min="0.1"
                max="3"
                step="0.1"
                value={state.animationSpeed}
                onChange={(e) => dispatch({ type: 'SET_ANIMATION_SPEED', speed: parseFloat(e.target.value) })}
                className="w-full"
              />
              <div className="text-center text-sm text-gray-400 mt-1">
                {state.animationSpeed}x speed
              </div>
            </div>

            <div className="bg-gray-700 rounded p-3">
              <h4 className="font-semibold mb-2">Legend</h4>
              <div className="space-y-1 text-sm">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-blue-500 mr-2"></div>
                  Normal Vehicle
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-red-500 mr-2"></div>
                  VIP Vehicle
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-black rounded-full mr-2"></div>
                  Pedestrian
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                  Green Signal
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                  Yellow Signal
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                  Red Signal
                </div>
              </div>
            </div>

            {state.activeSignal && (
              <div className="bg-green-900 border border-green-600 rounded p-3">
                <h4 className="font-semibold text-green-400">Active Signal</h4>
                <p className="text-sm">{state.activeSignal}</p>
                <p className="text-xs text-gray-300 mt-1">
                  Status: {state.signals.find(s => s.id === state.activeSignal)?.status?.toUpperCase()}
                </p>
              </div>
            )}

            {state.vipActive && (
              <div className="bg-red-900 border border-red-500 rounded p-3 animate-pulse">
                <h4 className="font-semibold text-red-400">🚨 VIP Priority Active</h4>
                <p className="text-xs text-gray-300 mt-1">Emergency vehicle in transit</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Current Signal Status</h3>
        
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {state.signals.map((signal) => {
            const pedSignal = state.pedestrianSignals.find(p => p.id === `P${signal.id.slice(1)}`);
            return (
              <div key={signal.id} className="bg-gray-700 rounded p-3">
                <h4 className="font-semibold mb-2">{signal.id}</h4>
                <div className="space-y-1 text-sm">
                  <div className={`flex items-center ${
                    signal.status === 'green' ? 'text-green-400' :
                    signal.status === 'yellow' ? 'text-yellow-400' : 'text-red-400'
                  }`}>
                    <span className="w-2 h-2 rounded-full mr-2 bg-current"></span>
                    Vehicle: {signal.status.toUpperCase()}
                  </div>
                  <div className={`flex items-center ${
                    signal.status === 'red' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    <span className="w-2 h-2 rounded-full mr-2 bg-current"></span>
                    Pedestrian: {signal.status === 'red' ? 'WALK' : 'WAIT'}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default SignalStatus;