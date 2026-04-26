import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  CheckCircle2, 
  AlertCircle, 
  TrendingUp, 
  Clock,
  RefreshCw,
  Calendar,
  Shield
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer
} from 'recharts';
import StatCard from '../components/StatCard';
import HospitalCard from '../components/HospitalCard';
import { sitesApi, logsApi, Site, SiteCheckLog } from '../lib/api';

const DashboardView: React.FC = () => {
  const [sites, setSites] = useState<Site[]>([]);
  const [logs, setLogs] = useState<SiteCheckLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());

  const fetchData = async () => {
    try {
      setLoading(true);
      const [sitesRes, logsRes] = await Promise.all([
        sitesApi.list(),
        logsApi.list()
      ]);
      setSites(sitesRes.data);
      setLogs(logsRes.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // 통계 계산
  const activeSitesCount = sites.filter(s => s.is_active).length;
  const healthySitesCount = sites.filter(s => {
    const siteLogs = logs.filter(l => l.site_id === s.id);
    return siteLogs.length > 0 && siteLogs[0].status === 'success';
  }).length;
  
  const uptimePercent = sites.length > 0 ? Math.round((healthySitesCount / sites.length) * 100) : 0;
  const issueCount = sites.length - healthySitesCount;

  // 차트 데이터 변환
  const chartData = logs
    .slice(0, 15)
    .reverse()
    .map(log => ({
      time: new Date(log.checked_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      ms: log.response_time
    }));

  return (
    <div className="p-8 space-y-10 animate-in fade-in slide-up duration-700">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 bg-gradient-to-r from-emerald-500/10 to-blue-500/10 p-8 rounded-[32px] border border-white/[0.03] relative overflow-hidden group">
        <div className="relative z-10">
          <h1 className="text-4xl font-black tracking-tight text-white flex items-center gap-3">
            안녕하세요, 관리자님 👋
          </h1>
          <p className="text-slate-400 mt-2 font-medium">오늘도 병원 시스템이 안전하게 모니터링되고 있습니다.</p>
        </div>
        <div className="relative z-10 text-right">
          <div className="flex items-center gap-2 text-emerald-400 font-black text-xl justify-end">
            <Clock size={20} />
            {currentTime.toLocaleTimeString('ko-KR', { hour12: true })}
          </div>
          <div className="text-slate-500 text-xs font-bold mt-1 uppercase tracking-widest flex items-center gap-1 justify-end">
             <Calendar size={12} /> {currentTime.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })}
          </div>
        </div>
        <div className="absolute -right-20 -top-20 w-64 h-64 bg-emerald-500/10 blur-[80px] rounded-full group-hover:bg-emerald-500/20 transition-all duration-1000" />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <StatCard 
          label="활성 모니터링" 
          value={activeSitesCount.toString()} 
          icon={Activity} 
          color="text-emerald-400" 
          glowColor="emerald"
        />
        <StatCard 
          label="정상 가동률" 
          value={`${uptimePercent}%`} 
          icon={CheckCircle2} 
          color="text-blue-400" 
          glowColor="blue"
        />
        <StatCard 
          label="주의 및 장애" 
          value={issueCount.toString()} 
          icon={AlertCircle} 
          color="text-red-400" 
          glowColor={issueCount > 0 ? 'red' : undefined}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Sites List */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold flex items-center gap-2 text-white">
              <Shield size={24} className="text-emerald-500" /> 실시간 감시 현황
            </h3>
            <button 
              onClick={fetchData} 
              className="p-2 glass rounded-xl text-slate-500 hover:text-emerald-400 hover:rotate-180 transition-all duration-500"
            >
              <RefreshCw size={18} />
            </button>
          </div>
          
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="glass h-64 rounded-3xl animate-pulse" />
              ))}
            </div>
          ) : sites.length === 0 ? (
            <div className="glass p-16 rounded-3xl flex flex-col items-center justify-center text-slate-500 border border-dashed border-white/5">
              <Activity size={48} className="mb-4 opacity-10" />
              <p className="font-bold text-lg">등록된 병원이 없습니다.</p>
              <p className="text-sm opacity-60 mt-1">'병원 관리' 탭에서 첫 번째 모니터링을 시작하세요.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {sites.map(site => (
                <HospitalCard key={site.id} site={site} onRefresh={fetchData} />
              ))}
            </div>
          )}
        </div>

        {/* Info & Chart Card */}
        <div className="space-y-8">
          <div className="glass p-8 rounded-[32px] border border-white/5 relative overflow-hidden group h-fit">
            <div className="relative z-10">
              <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-400 w-fit mb-6">
                <TrendingUp size={24} />
              </div>
              <h3 className="text-xl font-bold tracking-tight text-white mb-2">응답 속도 (ms)</h3>
              <p className="text-slate-500 text-[11px] font-bold uppercase tracking-widest leading-relaxed">
                최근 15건의 데이터를 기반으로 한 응답 지표입니다. 400ms 이상의 수치가 지속될 경우 서버 부하 가능성을 점검해 주세요.
              </p>
            </div>
            
            <div className="h-48 mt-8 relative z-10">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorMs" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                    <XAxis dataKey="time" hide />
                    <YAxis hide />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0c0e14', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', fontSize: '10px' }}
                      itemStyle={{ color: '#3b82f6' }}
                    />
                    <Area type="monotone" dataKey="ms" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorMs)" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-700 italic text-sm">
                  데이터 대기 중...
                </div>
              )}
            </div>
            <TrendingUp size={200} className="absolute -right-10 -top-10 text-blue-500/[0.02] -rotate-12 pointer-events-none" />
          </div>

          <div className="glass p-8 rounded-[32px] border border-white/5 relative overflow-hidden group">
             <div className="flex items-center gap-3 mb-4">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">실시간 모니터링 활성</span>
             </div>
             <p className="text-sm text-slate-500 font-medium leading-relaxed">
               시스템은 현재 모든 등록된 병원의 홈페이지와 상담폼을 정기적으로 점검하고 있습니다. 장애 감지 시 등록된 채널로 즉시 알림이 발송됩니다.
             </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardView;
