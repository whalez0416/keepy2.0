import React, { useState } from 'react';
import { 
  Search, 
  PlusCircle,
  Bell,
  User
} from 'lucide-react';
import Sidebar from './components/Sidebar';
import BottomNav from './components/BottomNav';
import DashboardView from './views/Dashboard';
import SiteListView from './views/SiteListView';
import AlertHistoryView from './views/AlertHistoryView';
import SettingsView from './views/SettingsView';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardView />;
      case 'sites':
        return <SiteListView />;
      case 'alerts':
        return <AlertHistoryView />;
      case 'settings':
        return <SettingsView />;
      default:
        return (
          <div className="p-8 text-slate-500 italic font-medium">
            {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} 화면은 현재 개발 중입니다.
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen flex text-slate-200 bg-[#080a0f] selection:bg-emerald-500/30">
      {/* Sidebar Component (Desktop) */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto pb-20 md:pb-0 relative">
        {/* Header - Premium Navigation Bar */}
        <header className="h-16 md:h-24 flex items-center justify-between px-6 md:px-10 sticky top-0 bg-[#080a0f]/60 backdrop-blur-xl z-40 border-b border-white/[0.03]">
          <div className="flex items-center gap-4">
             <div className="md:hidden w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center border border-emerald-500/30">
                <span className="text-emerald-400 font-black text-lg">K</span>
             </div>
             <h2 className="md:hidden font-bold text-xl tracking-tighter">Keepy</h2>
             
             <div className="hidden md:flex items-center gap-4 bg-white/[0.03] px-6 py-3 rounded-2xl border border-white/5 focus-within:border-emerald-500/30 focus-within:bg-white/[0.05] transition-all group">
                <Search size={18} className="text-slate-500 group-focus-within:text-emerald-400 transition-colors" />
                <input 
                  type="text" 
                  placeholder="병원 또는 시스템 상태 검색..." 
                  className="bg-transparent border-none outline-none text-sm w-72 placeholder:text-slate-600 font-medium"
                />
              </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="p-3 glass rounded-xl text-slate-400 hover:text-emerald-400 hover:border-emerald-500/30 transition-all relative">
              <Bell size={20} />
              <div className="absolute top-2.5 right-2.5 w-2 h-2 bg-emerald-500 rounded-full border-2 border-[#080a0f]" />
            </button>
            
            <button className="bg-emerald-500 text-white px-4 py-2.5 md:px-6 md:py-3.5 rounded-2xl font-bold flex items-center gap-2 hover:bg-emerald-600 transition-all shadow-2xl shadow-emerald-500/30 active:scale-95">
              <PlusCircle size={20} /> <span className="hidden md:inline">병원 추가</span>
            </button>
            
            <div className="h-10 w-[1px] bg-white/5 mx-2 hidden md:block" />
            
            <div className="flex items-center gap-3 pl-2 group cursor-pointer">
              <div className="text-right hidden lg:block">
                <div className="text-sm font-bold text-slate-200 group-hover:text-emerald-400 transition-colors">관리자 계정</div>
                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Premium Plan</div>
              </div>
              <div className="w-10 h-10 md:w-12 md:h-12 rounded-2xl glass-morphism border-white/10 flex items-center justify-center font-black text-emerald-400 shadow-2xl group-hover:border-emerald-500/50 transition-all overflow-hidden relative">
                <User size={24} className="opacity-80" />
                <div className="absolute inset-0 bg-emerald-500/5 group-hover:bg-emerald-500/10 transition-colors" />
              </div>
            </div>
          </div>
        </header>

        {/* Dynamic Content Based on Tab */}
        <div className="relative z-10">
          {renderContent()}
        </div>

        {/* Background Decorative Blobs for Depth */}
        <div className="fixed top-1/4 -right-20 w-96 h-96 bg-blue-600/10 blur-[120px] rounded-full pointer-events-none -z-10" />
        <div className="fixed bottom-1/4 -left-20 w-96 h-96 bg-emerald-600/10 blur-[120px] rounded-full pointer-events-none -z-10" />
      </main>

      {/* Bottom Navigation (Mobile) */}
      <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} />
    </div>
  );
}

export default App;
