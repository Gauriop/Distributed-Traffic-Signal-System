import React from 'react';

interface Tab {
  id: string;
  name: string;
  component: React.ComponentType<any>;
}

interface TabNavigationProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

const TabNavigation: React.FC<TabNavigationProps> = ({ tabs, activeTab, onTabChange }) => {
  return (
    <div className="border-b border-gray-700">
      <nav className="flex space-x-0 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`
              px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors duration-200
              ${activeTab === tab.id
                ? 'bg-blue-600 text-white border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }
            `}
          >
            {tab.name}
          </button>
        ))}
      </nav>
    </div>
  );
};

export default TabNavigation;