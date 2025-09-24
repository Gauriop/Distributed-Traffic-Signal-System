import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';

export interface SignalState {
  id: string;
  status: 'green' | 'red' | 'yellow';
  lastChanged: number;
}

export interface ServerStatus {
  id: string;
  port: number;
  connected: boolean;
  load: number;
  maxLoad: number;
}

export interface SystemStats {
  totalRequests: number;
  vipRequests: number;
  failedRequests: number;
  timeouts: number;
  requestsPerMinute: number;
  uptime: number;
  logicalClock: number;
  criticalSectionActive: boolean;
}

export interface LogEntry {
  id: string;
  timestamp: number;
  type: 'info' | 'warning' | 'error';
  component: string;
  message: string;
}

export interface TrafficState {
  signals: SignalState[];
  pedestrianSignals: SignalState[];
  servers: ServerStatus[];
  systemStats: SystemStats;
  logs: LogEntry[];
  autoGenerateSignals: boolean;
  autoGenerateInterval: number;
  synchronizedTime: string;
  clientTimes: { [key: string]: string };
  activeSignal: string | null;
  vipActive: boolean;
  animationSpeed: number;
  animationPaused: boolean;
}

type TrafficAction = 
  | { type: 'UPDATE_SIGNAL'; signalId: string; status: 'green' | 'red' | 'yellow' }
  | { type: 'UPDATE_PEDESTRIAN_SIGNAL'; signalId: string; status: 'green' | 'red' }
  | { type: 'UPDATE_SERVER_STATUS'; serverId: string; connected: boolean; load?: number }
  | { type: 'ADD_LOG'; log: Omit<LogEntry, 'id'> }
  | { type: 'CLEAR_LOGS' }
  | { type: 'TOGGLE_AUTO_GENERATE' }
  | { type: 'SET_AUTO_INTERVAL'; interval: number }
  | { type: 'SET_CLIENT_TIME'; clientId: string; time: string }
  | { type: 'SET_SYNCHRONIZED_TIME'; time: string }
  | { type: 'SET_ACTIVE_SIGNAL'; signal: string | null }
  | { type: 'SET_VIP_ACTIVE'; active: boolean }
  | { type: 'UPDATE_STATS'; stats: Partial<SystemStats> }
  | { type: 'SET_ANIMATION_SPEED'; speed: number }
  | { type: 'TOGGLE_ANIMATION' };

const initialState: TrafficState = {
  signals: [
    { id: 'T1', status: 'red', lastChanged: Date.now() },
    { id: 'T2', status: 'red', lastChanged: Date.now() },
    { id: 'T3', status: 'red', lastChanged: Date.now() },
    { id: 'T4', status: 'red', lastChanged: Date.now() },
  ],
  pedestrianSignals: [
    { id: 'P1', status: 'green', lastChanged: Date.now() },
    { id: 'P2', status: 'green', lastChanged: Date.now() },
    { id: 'P3', status: 'green', lastChanged: Date.now() },
    { id: 'P4', status: 'green', lastChanged: Date.now() },
  ],
  servers: [
    { id: 'load-balancer', port: 9000, connected: true, load: 0, maxLoad: 100 },
    { id: 'primary', port: 8000, connected: true, load: 5, maxLoad: 10 },
    { id: 'clone', port: 8001, connected: true, load: 3, maxLoad: 10 },
  ],
  systemStats: {
    totalRequests: 0,
    vipRequests: 0,
    failedRequests: 0,
    timeouts: 0,
    requestsPerMinute: 0,
    uptime: 0,
    logicalClock: 0,
    criticalSectionActive: false,
  },
  logs: [],
  autoGenerateSignals: false,
  autoGenerateInterval: 4,
  synchronizedTime: new Date().toLocaleTimeString(),
  clientTimes: {},
  activeSignal: null,
  vipActive: false,
  animationSpeed: 1,
  animationPaused: false,
};

function trafficReducer(state: TrafficState, action: TrafficAction): TrafficState {
  switch (action.type) {
    case 'UPDATE_SIGNAL':
      return {
        ...state,
        signals: state.signals.map(signal =>
          signal.id === action.signalId
            ? { ...signal, status: action.status, lastChanged: Date.now() }
            : signal
        ),
        pedestrianSignals: state.pedestrianSignals.map(signal =>
          signal.id === `P${action.signalId.slice(1)}`
            ? { ...signal, status: action.status === 'green' ? 'red' : 'green', lastChanged: Date.now() }
            : signal
        ),
      };
    
    case 'UPDATE_PEDESTRIAN_SIGNAL':
      return {
        ...state,
        pedestrianSignals: state.pedestrianSignals.map(signal =>
          signal.id === action.signalId
            ? { ...signal, status: action.status, lastChanged: Date.now() }
            : signal
        ),
      };

    case 'UPDATE_SERVER_STATUS':
      return {
        ...state,
        servers: state.servers.map(server =>
          server.id === action.serverId
            ? { ...server, connected: action.connected, load: action.load ?? server.load }
            : server
        ),
      };

    case 'ADD_LOG':
      const newLog: LogEntry = {
        ...action.log,
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      };
      return {
        ...state,
        logs: [newLog, ...state.logs].slice(0, 1000), // Keep only last 1000 logs
      };

    case 'CLEAR_LOGS':
      return { ...state, logs: [] };

    case 'TOGGLE_AUTO_GENERATE':
      return { ...state, autoGenerateSignals: !state.autoGenerateSignals };

    case 'SET_AUTO_INTERVAL':
      return { ...state, autoGenerateInterval: action.interval };

    case 'SET_CLIENT_TIME':
      return {
        ...state,
        clientTimes: { ...state.clientTimes, [action.clientId]: action.time },
      };

    case 'SET_SYNCHRONIZED_TIME':
      return { ...state, synchronizedTime: action.time };

    case 'SET_ACTIVE_SIGNAL':
      return { ...state, activeSignal: action.signal };

    case 'SET_VIP_ACTIVE':
      return { ...state, vipActive: action.active };

    case 'UPDATE_STATS':
      return {
        ...state,
        systemStats: { ...state.systemStats, ...action.stats },
      };

    case 'SET_ANIMATION_SPEED':
      return { ...state, animationSpeed: action.speed };

    case 'TOGGLE_ANIMATION':
      return { ...state, animationPaused: !state.animationPaused };

    default:
      return state;
  }
}

const TrafficContext = createContext<{
  state: TrafficState;
  dispatch: React.Dispatch<TrafficAction>;
} | null>(null);

export const TrafficProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(trafficReducer, initialState);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Update synchronized time
      dispatch({ type: 'SET_SYNCHRONIZED_TIME', time: new Date().toLocaleTimeString() });
      
      // Update system stats
      dispatch({
        type: 'UPDATE_STATS',
        stats: {
          uptime: state.systemStats.uptime + 1,
          logicalClock: state.systemStats.logicalClock + 1,
          requestsPerMinute: Math.max(0, state.systemStats.requestsPerMinute + Math.floor((Math.random() - 0.5) * 3))
        },
      });

      // Randomly update server loads
      if (Math.random() < 0.3) {
        state.servers.forEach(server => {
          if (server.id !== 'load-balancer') {
            const newLoad = Math.max(0, Math.min(server.maxLoad, server.load + (Math.random() - 0.5) * 2));
            dispatch({
              type: 'UPDATE_SERVER_STATUS',
              serverId: server.id,
              connected: true,
              load: Math.round(newLoad),
            });
          }
        });
      }
      
      // Generate some background activity logs
      if (Math.random() < 0.1) {
        const activities = [
          'System heartbeat check completed',
          'Load balancer health check passed',
          'Signal timing synchronization verified',
          'Pedestrian crossing sensors active'
        ];
        
        dispatch({ type: 'ADD_LOG', log: {
          timestamp: Date.now(),
          type: 'info',
          component: 'System',
          message: activities[Math.floor(Math.random() * activities.length)]
        }});
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [state.systemStats.uptime, state.systemStats.logicalClock]);

  return (
    <TrafficContext.Provider value={{ state, dispatch }}>
      {children}
    </TrafficContext.Provider>
  );
};

export const useTraffic = () => {
  const context = useContext(TrafficContext);
  if (!context) {
    throw new Error('useTraffic must be used within a TrafficProvider');
  }
  return context;
};