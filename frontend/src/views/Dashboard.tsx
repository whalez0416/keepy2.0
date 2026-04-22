import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  BarChart3, 
  Shield 
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import StatCard from '../components/StatCard';
import HospitalCard from '../components/HospitalCard';
import { sitesApi, Site, logsApi, SiteCheckLog } from '../lib/api';

const DashboardView: React.FC = () => {
  const [sites, setSites] = useState<Site[]>([]);
  const [logs, setLogs] = useState<SiteCheckLog[]>([]);
  const [loading, setLoading] = useState(true);

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
  }, []);

  // 통계 계산
  const activeCount = sites.filter(s => s.is_active).length;
  const errorCount = sites.filter(s => s.last_check_status === 'error' || s.last_check_status === 'fail').length;
  const successRate = sites.length > 0 ? ((sites.filter(s => s.last_check_status === 'success').length / sites.length) * 100).toFixed(1) : '0';

  // 차트 데이터 (최근 로그 기준)
  const chartData = logs.slice(0, 10).map(log => ({
    time: new Date(log.checked_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    ms: log.response_time
  })).reverse();

  return (
    <div className="p-8 space-y-8 animate-in fade-in duration-500">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard label="Active Sites" value={activeCount} icon={Activity} color="text-blue-500" />
        <StatCard label="Success Rate" value={`${successRate}%`} icon={CheckCircle2} color="text-emerald-500" />
        <StatCard label="Critical Issues" value={errorCount} icon={AlertTriangle} color="text-red-500" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Sites List */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-xl font-bold flex items-center gap-2">
            <Shield size={20} className="text-emerald-500" /> Monitoring Status
          </h3>
          
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="glass h-48 rounded-2xl animate-pulse" />
              ))}
            </div>
          ) : sites.length === 0 ? (
            <div className="glass p-12 rounded-2xl flex flex-col items-center justify-center text-slate-500 border border-dashed border-slate-700">
              <Activity size={48} className="mb-4 opacity-20" />
              <p>No sites registered yet. Go to 'Managed Sites' to add one.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {sites.map(site => (
                <HospitalCard key={site.id} site={site} onRefresh={fetchData} />
              ))}
            </div>
          )}
        </div>

        {/* Response Time Chart */}
        <div className="glass rounded-2xl p-6 border border-white/5 space-y-4 h-fit">
          <h3 className="font-bold flex items-center gap-2">
            <BarChart3 size={18} className="text-blue-400" /> Response Time (ms)
          </h3>
          <div className="h-64">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" vertical={false} />
                  <XAxis dataKey="time" stroke="#4a5568" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#4a5568" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1a202c', border: '1px solid #2d3748', borderRadius: '8px' }}
                    itemStyle={{ color: '#10b981' }}
                  />
                  <Line type="monotone" dataKey="ms" stroke="#3b82f6" strokeWidth={3} dot={{ fill: '#3b82f6' }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm italic">
                Waiting for check logs...
              </div>
            )}
          </div>
          <div className="bg-blue-500/10 border border-blue-500/20 p-4 rounded-xl text-xs text-blue-300 leading-relaxed">
            <Activity size={14} className="inline mr-1 mb-1" />
            최근 10건의 모니터링 로그를 기반으로 한 응답 지표입니다. 400ms 이상의 수치가 지속될 경우 서버 지연이 의심됩니다.
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardView;
