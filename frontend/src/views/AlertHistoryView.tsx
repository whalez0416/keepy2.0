import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Bell, 
  CheckCircle2, 
  Filter, 
  Clock,
  Shield,
  Search,
  ExternalLink
} from 'lucide-react';
import { alertsApi, Alert, sitesApi, Site } from '../lib/api';

const AlertHistoryView: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [sites, setSites] = useState<Record<number, Site>>({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'warning' | 'danger'>('all');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [alertsRes, sitesRes] = await Promise.all([
        alertsApi.list(),
        sitesApi.list()
      ]);
      
      setAlerts(alertsRes.data);
      
      // 병원 정보를 ID 매핑으로 변환
      const siteMap: Record<number, Site> = {};
      sitesRes.data.forEach(site => {
        siteMap[site.id] = site;
      });
      setSites(siteMap);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'all') return true;
    return alert.alert_level === filter;
  });

  return (
    <div className="p-8 space-y-8 animate-in slide-up duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">알림 내역</h2>
          <p className="text-slate-400 mt-1 font-medium">발생한 모든 장애 및 복구 이력을 확인합니다.</p>
        </div>
        <div className="flex gap-2 glass p-1 rounded-xl">
          {(['all', 'warning', 'danger'] as const).map((level) => (
            <button
              key={level}
              onClick={() => setFilter(level)}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                filter === level 
                  ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20' 
                  : 'hover:bg-white/5 text-slate-400'
              }`}
            >
              {level === 'all' ? '전체' : level === 'warning' ? '주의' : '위험'}
            </button>
          ))}
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-emerald-400 transition-colors" size={20} />
          <input 
            type="text" 
            placeholder="병원명 또는 메시지로 검색..." 
            className="w-full glass border border-white/5 rounded-2xl py-4 pl-12 pr-4 focus:ring-2 focus:ring-emerald-500/30 outline-none transition-all placeholder:text-slate-600 font-medium"
          />
        </div>
      </div>

      {/* Alerts Timeline/List */}
      <div className="space-y-4">
        {loading ? (
          [1, 2, 3, 4].map(i => (
            <div key={i} className="glass h-24 rounded-2xl animate-pulse border-white/5" />
          ))
        ) : filteredAlerts.length === 0 ? (
          <div className="glass p-16 rounded-3xl flex flex-col items-center justify-center text-slate-500 border border-dashed border-slate-800">
            <Bell size={48} className="mb-4 opacity-10" />
            <p className="font-medium text-lg">알림 내역이 없습니다.</p>
          </div>
        ) : (
          filteredAlerts.map(alert => {
            const site = sites[alert.site_id];
            const isDanger = alert.alert_level === 'danger';
            const isResolved = !!alert.resolved_at;
            
            return (
              <div 
                key={alert.id} 
                className={`glass p-6 rounded-2xl border border-white/5 group hover:border-white/10 transition-all flex flex-col md:flex-row md:items-center gap-6 relative overflow-hidden ${isDanger && !isResolved ? 'glow-red' : ''}`}
              >
                {/* Status Indicator Bar */}
                <div className={`absolute left-0 top-0 bottom-0 w-1 ${isDanger ? 'bg-red-500' : 'bg-amber-500'} ${isResolved ? 'opacity-30' : 'shadow-[0_0_10px_rgba(239,68,68,0.5)]'}`} />
                
                {/* Icon & Time */}
                <div className="flex items-center gap-4 min-w-[180px]">
                  <div className={`p-3 rounded-xl ${isDanger ? 'bg-red-500/10 text-red-400' : 'bg-amber-500/10 text-amber-400'}`}>
                    <AlertTriangle size={24} />
                  </div>
                  <div className="flex flex-col">
                    <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1">
                      <Clock size={10} /> {new Date(alert.created_at).toLocaleDateString()}
                    </div>
                    <div className="text-sm font-bold text-slate-300">
                      {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </div>

                {/* Hospital Info & Message */}
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-black text-slate-200">{site?.site_name || '알 수 없는 병원'}</span>
                    <span className="text-[10px] font-bold bg-white/5 px-2 py-0.5 rounded text-slate-500 uppercase">{alert.check_type}</span>
                  </div>
                  <p className="text-sm text-slate-400 leading-relaxed">
                    {alert.message}
                  </p>
                </div>

                {/* Status Badge & Action */}
                <div className="flex items-center justify-between md:justify-end gap-4 min-w-[150px]">
                  {isResolved ? (
                    <div className="flex items-center gap-1.5 text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-lg border border-emerald-500/20 text-[10px] font-bold uppercase tracking-wider">
                      <CheckCircle2 size={14} /> 해결됨
                    </div>
                  ) : (
                    <div className={`flex items-center gap-1.5 ${isDanger ? 'text-red-400 bg-red-500/10 border-red-500/20' : 'text-amber-400 bg-amber-500/10 border-amber-500/20'} px-3 py-1.5 rounded-lg border text-[10px] font-bold uppercase tracking-wider pulse-soft`}>
                      <Shield size={14} /> 미해결
                    </div>
                  )}
                  <button className="p-2.5 glass rounded-xl text-slate-500 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all">
                    <ExternalLink size={18} />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default AlertHistoryView;
