import React, { useState } from 'react';
import { TrafficProvider } from './context/TrafficContext';
import TabNavigation from './components/TabNavigation';
import SystemControl from './components/tabs/SystemControl';
import TimeSync from './components/tabs/TimeSync';
import SignalRequests from './components/tabs/SignalRequests';
import PedestrianMonitoring from './components/tabs/PedestrianMonitoring';
import SignalStatus from './components/tabs/SignalStatus';
import SystemStats from './components/tabs/SystemStats';
import LoadTesting from './components/tabs/LoadTesting';
import LogsConsole from './components/tabs/LogsConsole';

const tabs = [
  { id: 'system-control', name: 'System Control', component: SystemControl },
  { id: 'time-sync', name: 'Time Sync', component: TimeSync },
  { id: 'signal-requests', name: 'Signal Requests', component: SignalRequests },
  { id: 'pedestrian', name: 'Pedestrian Monitoring', component: PedestrianMonitoring },
  { id: 'signal-status', name: 'Signal Status', component: SignalStatus },
  { id: 'system-stats', name: 'System Statistics', component: SystemStats },
  { id: 'load-testing', name: 'Load Testing', component: LoadTesting },
  { id: 'logs', name: 'Logs/Console', component: LogsConsole },
];

function App() {
  const [activeTab, setActiveTab] = useState('system-control');

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || SystemControl;

  return (
    <TrafficProvider>
      <div className="min-h-screen bg-gray-900 text-white">
        <div className="container mx-auto px-4 py-6">
          <header className="mb-6">
            <h1 className="text-3xl font-bold text-center mb-2">Traffic Management System</h1>
            <p className="text-gray-400 text-center">Real-time Traffic Control & Monitoring Dashboard</p>
          </header>

          <TabNavigation 
            tabs={tabs}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />

          <div className="mt-6">
            <ActiveComponent />
          </div>
        </div>
      </div>
    </TrafficProvider>
  );
}

export default App;