import React from 'react';
import { 
  BarChart3, 
  Activity, 
  AlertTriangle, 
  Settings 
} from 'lucide-react';

interface BottomNavProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const BottomNav: React.FC<BottomNavProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'dashboard', icon: BarChart3, label: 'Dash' },
    { id: 'sites', icon: Activity, label: 'Sites' },
    { id: 'alerts', icon: AlertTriangle, label: 'Alerts' },
    { id: 'settings', icon: Settings, label: 'Set' },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-[#0c0e14]/90 backdrop-blur-xl border-t border-white/5 flex items-center justify-around px-4 pb-safe z-50">
      {navItems.map((item) => (
        <button
          key={item.id}
          onClick={() => setActiveTab(item.id)}
          className={`flex flex-col items-center gap-1 transition-all px-3 py-1 rounded-xl ${
            activeTab === item.id ? 'text-emerald-400 scale-110' : 'text-slate-500'
          }`}
        >
          <item.icon size={22} className={activeTab === item.id ? 'drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]' : ''} />
          <span className="text-[10px] font-bold tracking-tight">{item.label}</span>
        </button>
      ))}
    </nav>
  );
};

export default BottomNav;
