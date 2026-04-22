import React from 'react';
import { 
  Shield, 
  BarChart3, 
  Activity, 
  AlertTriangle, 
  Settings, 
  Download 
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const menuItems = [
    { id: 'dashboard', icon: BarChart3, label: 'Dashboard' },
    { id: 'sites', icon: Activity, label: 'Managed Sites' },
    { id: 'alerts', icon: AlertTriangle, label: 'Alert History' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <aside className="hidden md:flex w-64 glass border-r border-slate-800 flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold gradient-text flex items-center gap-2">
          <Shield className="text-emerald-500" /> Keepy <span className="text-xs font-normal text-slate-500 border border-slate-700 px-1 rounded">2.0</span>
        </h1>
      </div>
      
      <nav className="flex-1 px-4 space-y-2">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === item.id ? 'glass bg-emerald-500/10 text-emerald-400' : 'hover:bg-white/5'
            }`}
          >
            <item.icon size={20} />
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="p-4">
        <button className="w-full flex items-center justify-center gap-2 py-3 px-4 glass border-emerald-500/30 text-emerald-400 rounded-xl hover:bg-emerald-500/20 transition-all font-semibold shadow-lg shadow-emerald-500/10">
          <Download size={18} />
          Import from 1.0 (Render)
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
