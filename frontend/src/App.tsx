import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { 
  Search, 
  PlusCircle,
  Bell,
  User as UserIcon,
  LogOut
} from 'lucide-react';
import Sidebar from './components/Sidebar';
import BottomNav from './components/BottomNav';
import DashboardView from './views/Dashboard';
import SiteListView from './views/SiteListView';
import AlertHistoryView from './views/AlertHistoryView';
import SettingsView from './views/SettingsView';
import SpamManagementView from './views/SpamManagementView';
import LoginView from './views/LoginView';
import RegisterView from './views/RegisterView';
import LeadsAdminView from './views/LeadsAdminView';
import SiteConfigModal from './components/SiteConfigModal';
import BuildingSelector from './components/HospitalSelector';
import { User, Site } from './lib/api';

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [selectedSite, setSelectedSite] = useState<Site | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedOrgId, setSelectedOrgId] = useState<number | 'all'>('all');

  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('keepy_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(localStorage.getItem('keepy_token'));

  const handleLoginSuccess = (newToken: string, newUser: User) => {
    localStorage.setItem('keepy_token', newToken);
    localStorage.setItem('keepy_user', JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
    navigate('/');
  };

  const handleLogout = () => {
    console.log("handleLogout executing...");
    localStorage.clear();
    setToken(null);
    setUser(null);
    navigate('/login');
  };

  const handleAddSite = () => {
    setSelectedSite(null);
    setIsConfigModalOpen(true);
  };

  const handleEditSite = (site: Site) => {
    setSelectedSite(site);
    setIsConfigModalOpen(true);
  };

  const handleSaveSite = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  // Sync activeTab with URL if possible, or just keep it for now
  useEffect(() => {
    const path = location.pathname.substring(1);
    if (path && ['dashboard', 'sites', 'alerts', 'spam', 'settings', 'leads'].includes(path)) {
      setActiveTab(path);
    }
  }, [location.pathname]);

  if (!token) {
    return (
      <Routes>
        <Route path="/login" element={
          <LoginView
            onLoginSuccess={handleLoginSuccess}
            onSwitchToRegister={() => navigate('/register')}
          />
        } />
        <Route path="/register" element={
          <RegisterView
            onSwitchToLogin={() => navigate('/login')}
            onRegisterSuccess={() => navigate('/login')}
          />
        } />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    );
  }

  return (
    <div className="min-h-screen flex text-slate-200 bg-[#080a0f] selection:bg-[#9fb2c2]/25">
      <Sidebar activeTab={activeTab} setActiveTab={(tab) => { setActiveTab(tab); navigate(`/${tab}`); }} onLogout={handleLogout} user={user} />

      <main className="flex-1 overflow-y-auto pb-20 md:pb-0 relative">
        <header className="h-16 md:h-24 flex items-center justify-between px-6 md:px-10 sticky top-0 bg-[#080a0f]/60 backdrop-blur-xl z-40 border-b border-white/[0.03]">
          <div className="flex items-center gap-4">
             <div className="md:hidden w-10 h-10 rounded-xl bg-[#9fb2c2]/20 flex items-center justify-center border border-[#9fb2c2]/30">
                <span className="text-[#c8d4de] font-black text-lg">K</span>
             </div>
             <h2 className="md:hidden font-bold text-xl tracking-tighter">Keepy</h2>
          </div>
          <div className="flex items-center gap-4">
            {user?.role === 'superadmin' && (
              <div className="hidden md:block mr-2">
                <BuildingSelector selectedOrgId={selectedOrgId} onSelect={(id) => setSelectedOrgId(id)} />
              </div>
            )}
            
            <button
              onClick={() => { setActiveTab('alerts'); navigate('/alerts'); }}
              title="알림 내역"
              className="p-3 glass rounded-xl text-slate-400 hover:text-[#c8d4de] hover:border-[#9fb2c2]/30 transition-all relative"
            >
              <Bell size={20} />
            </button>
            
            <button 
              onClick={handleAddSite}
              className="bg-gradient-to-b from-[#e9eef2] via-[#b9c4cd] to-[#8b97a1] text-[#0a0c0f] px-4 py-2.5 md:px-6 md:py-3.5 rounded-2xl font-bold flex items-center gap-2 hover:brightness-110 transition-all border border-white/40 shadow-[inset_0_1px_0_rgba(255,255,255,0.5),0_8px_24px_rgba(0,0,0,0.5)] active:scale-95"
            >
              <PlusCircle size={20} /> <span className="hidden md:inline">병원 추가</span>
            </button>
            
            <div className="h-10 w-[1px] bg-white/5 mx-2 hidden md:block" />
            
            {/* Header Profile - Removed container click logout */}
            <div className="flex items-center gap-3 pl-2 group relative">
              <div className="text-right hidden lg:block">
                <div className="text-sm font-bold text-slate-200">{user?.email || '관리자 계정'}</div>
                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">{user?.role === 'superadmin' ? 'Super Admin' : 'Hospital Admin'}</div>
              </div>
              <button 
                onClick={handleLogout}
                className="w-10 h-10 md:w-12 md:h-12 rounded-2xl glass-morphism border-white/10 flex items-center justify-center font-black text-[#c8d4de] shadow-2xl hover:border-red-500/50 transition-all overflow-hidden relative group"
                title="로그아웃"
              >
                <UserIcon size={24} className="opacity-80 group-hover:scale-0 transition-transform duration-200" />
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-red-500/10">
                   <LogOut size={20} className="text-red-400" />
                </div>
              </button>
            </div>
          </div>
        </header>

        <div className="relative z-10">
          <Routes>
            {/* key: 사이트 저장/조직 변경 시 뷰를 다시 마운트해 목록을 재조회한다 */}
            <Route path="/dashboard" element={<DashboardView key={`${refreshTrigger}-${selectedOrgId}`} onEditSite={handleEditSite} selectedOrgId={selectedOrgId} user={user} />} />
            <Route path="/sites" element={<SiteListView key={`${refreshTrigger}-${selectedOrgId}`} selectedOrgId={selectedOrgId} />} />
            <Route path="/alerts" element={<AlertHistoryView />} />
            <Route path="/spam" element={<SpamManagementView />} />
            <Route path="/leads" element={<LeadsAdminView />} />
            <Route path="/settings" element={<SettingsView onLogout={handleLogout} />} />
            <Route path="/" element={<Navigate to="/dashboard" />} />
          </Routes>
        </div>

        <div className="fixed top-1/4 -right-20 w-96 h-96 bg-blue-600/10 blur-[120px] rounded-full pointer-events-none -z-10" />
        <div className="fixed bottom-1/4 -left-20 w-96 h-96 bg-[#9fb2c2]/10 blur-[120px] rounded-full pointer-events-none -z-10" />
      </main>

      <BottomNav activeTab={activeTab} setActiveTab={(tab) => { setActiveTab(tab); navigate(`/${tab}`); }} user={user} />

      <SiteConfigModal 
        isOpen={isConfigModalOpen} 
        onClose={() => setIsConfigModalOpen(false)} 
        onSave={handleSaveSite}
        site={selectedSite}
      />
    </div>
  );
}

export default App;
