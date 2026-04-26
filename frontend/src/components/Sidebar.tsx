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
    { id: 'dashboard', icon: BarChart3, label: '대시보드' },
    { id: 'sites', icon: Activity, label: '병원 관리' },
    { id: 'alerts', icon: AlertTriangle, label: '알림 내역' },
    { id: 'settings', icon: Settings, label: '설정' },
  ];

  return (
    <aside className="hidden md:flex w-64 glass border-r border-white/5 flex-col z-50">
      <div className="p-8">
        <h1 className="text-2xl font-bold gradient-text flex items-center gap-2 tracking-tight">
          <Shield className="text-emerald-500 fill-emerald-500/20" size={28} /> Keepy <span className="text-[10px] font-bold text-slate-500 border border-slate-800 px-1.5 py-0.5 rounded-md bg-slate-900/50">V2</span>
        </h1>
      </div>
      
      <nav className="flex-1 px-4 space-y-1.5">
        {menuItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300 relative group ${
                isActive 
                  ? 'glass bg-emerald-500/10 text-emerald-400 glow-emerald' 
                  : 'hover:bg-white/5 text-slate-400 hover:text-slate-200'
              }`}
            >
              {isActive && (
                <div className="absolute left-0 w-1 h-6 bg-emerald-500 rounded-r-full shadow-[0_0_10px_rgba(16,185,129,0.8)]" />
              )}
              <item.icon size={20} className={`${isActive ? 'scale-110' : 'group-hover:scale-110'} transition-transform duration-300`} />
              <span className="font-bold text-sm">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-6 mt-auto">
        <button className="w-full flex flex-col items-center justify-center gap-2 py-4 px-4 glass border-emerald-500/20 text-emerald-400 rounded-2xl hover:bg-emerald-500/10 transition-all font-bold shadow-lg shadow-emerald-500/5 group">
          <div className="flex items-center gap-2">
            <Download size={16} className="group-hover:translate-y-0.5 transition-transform" />
            <span className="text-xs">데이터 마이그레이션</span>
          </div>
          <span className="text-[10px] opacity-60 font-medium italic">Keepy 1.0 (Render)</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
