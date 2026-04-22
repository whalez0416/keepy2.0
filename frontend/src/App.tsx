import React, { useState } from 'react';
import { 
  Search, 
  PlusCircle
} from 'lucide-react';
import Sidebar from './components/Sidebar';
import BottomNav from './components/BottomNav';
import DashboardView from './views/Dashboard';
import SiteListView from './views/SiteListView';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardView />;
      case 'sites':
        return <SiteListView />;
      default:
        return (
          <div className="p-8 text-slate-500 italic">
            {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} view is under development.
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen flex text-slate-200 bg-[#0c0e14]">
      {/* Sidebar Component (Desktop) */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto pb-20 md:pb-0">
        {/* Header - Hidden or simplified on mobile */}
        <header className="h-16 md:h-20 border-b border-white/5 flex items-center justify-between px-6 md:px-8 sticky top-0 bg-[#0c0e14]/80 backdrop-blur-md z-40">
          <div className="flex items-center gap-3">
             <div className="md:hidden w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                <span className="text-emerald-400 font-bold text-xs">K</span>
             </div>
             <h2 className="md:hidden font-bold text-lg tracking-tight">Keepy</h2>
             <div className="hidden md:flex items-center gap-4 bg-white/5 px-4 py-2 rounded-full border border-white/5">
                <Search size={18} className="text-slate-500" />
                <input 
                  type="text" 
                  placeholder="Search hospitals..." 
                  className="bg-transparent border-none outline-none text-sm w-64"
                />
              </div>
          </div>
          <div className="flex items-center gap-3">
            <button className="bg-emerald-500 text-white p-2 md:px-5 md:py-2.5 rounded-lg md:rounded-xl font-bold flex items-center gap-2 hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20">
              <PlusCircle size={18} /> <span className="hidden md:inline">Add Hospital</span>
            </button>
            <div className="w-8 h-8 md:w-10 md:h-10 rounded-full glass border-white/10 flex items-center justify-center font-bold text-emerald-400 shadow-lg text-xs md:text-base">
              K
            </div>
          </div>
        </header>

        {/* Dynamic Content Based on Tab */}
        {renderContent()}
      </main>

      {/* Bottom Navigation (Mobile) */}
      <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} />
    </div>
  );
}

export default App;
