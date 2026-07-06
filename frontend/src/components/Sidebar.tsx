import React from 'react';
import { 
  Shield, 
  BarChart3, 
  Activity, 
  AlertTriangle, 
  Settings,
  Brain,
  LogOut,
  Inbox
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onLogout: () => void;
  user: any;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, onLogout, user }) => {
  const menuItems = [
    { id: 'dashboard', icon: BarChart3, label: '대시보드' },
    { id: 'sites', icon: Activity, label: '병원 관리' },
    { id: 'alerts', icon: AlertTriangle, label: '알림 내역' },
    { id: 'spam', icon: Brain, label: 'AI 스팸 관리' },
    ...(user?.role === 'superadmin' ? [{ id: 'leads', icon: Inbox, label: '상담 관리' }] : []),
    { id: 'settings', icon: Settings, label: '설정' },
  ];

  return (
    <aside className="hidden md:flex w-64 h-screen sticky top-0 glass border-r border-white/5 flex-col z-50">
      <div className="p-8">
        <h1 className="text-2xl font-bold gradient-text flex items-center gap-2 tracking-tight">
          <Shield className="text-[#9fb2c2] fill-[#9fb2c2]/20" size={28} /> Keepy
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
                  ? 'glass bg-[#9fb2c2]/10 text-[#c8d4de]'
                  : 'hover:bg-white/5 text-slate-400 hover:text-slate-200'
              }`}
            >
              {isActive && (
                <div className="absolute left-0 w-1 h-6 bg-[#9fb2c2] rounded-r-full shadow-[0_0_10px_rgba(159,178,194,0.8)]" />
              )}
              <item.icon size={20} className={`${isActive ? 'scale-110' : 'group-hover:scale-110'} transition-transform duration-300`} />
              <span className="font-bold text-sm">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-4 mt-auto space-y-2">
        <button
          onClick={() => {
            console.log("Sidebar logout initiated");
            onLogout();
          }}
          className="w-full flex items-center justify-center gap-2 py-3.5 px-4 rounded-2xl hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-all font-bold group border border-transparent hover:border-red-500/20"
        >
          <LogOut size={18} className="group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm">로그아웃</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
