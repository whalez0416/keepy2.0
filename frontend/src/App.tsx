import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Shield, 
  AlertTriangle, 
  BarChart3, 
  Settings, 
  PlusCircle, 
  Download,
  Search,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Mock Data for Demo
const MOCK_SITES = [
  { id: 1, name: '민병원 Thyroid Center', status: 'success', uptime: '99.9%', url: 'https://minhospital.com', screenshot: 'https://via.placeholder.com/300x150/10b981/ffffff?text=Min+Hospital+Preview' },
  { id: 2, name: '강남 성모 안과', status: 'warning', uptime: '98.5%', url: 'https://gangnameye.co.kr', screenshot: 'https://via.placeholder.com/300x150/f59e0b/ffffff?text=Eye+Clinic+Preview' },
];

const MOCK_CHART = [
  { time: '09:00', ms: 120 }, { time: '10:00', ms: 240 }, { time: '11:00', ms: 110 },
  { time: '12:00', ms: 150 }, { time: '13:00', ms: 400 }, { time: '14:00', ms: 180 },
];

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen flex text-slate-200">
      {/* Sidebar */}
      <aside className="w-64 glass border-r border-slate-800 flex flex-col">
        <div className="p-6">
          <h1 className="text-2xl font-bold gradient-text flex items-center gap-2">
            <Shield className="text-emerald-500" /> Keepy <span className="text-xs font-normal text-slate-500 border border-slate-700 px-1 rounded">2.0</span>
          </h1>
        </div>
        
        <nav className="flex-1 px-4 space-y-2">
          {[
            { id: 'dashboard', icon: BarChart3, label: 'Dashboard' },
            { id: 'sites', icon: Activity, label: 'Managed Sites' },
            { id: 'alerts', icon: AlertTriangle, label: 'Alert History' },
            { id: 'settings', icon: Settings, label: 'Settings' },
          ].map((item) => (
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

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-[#0c0e14]">
        {/* Header */}
        <header className="h-20 border-b border-slate-800 flex items-center justify-between px-8 sticky top-0 bg-[#0c0e14]/80 backdrop-blur-md z-10">
          <div className="flex items-center gap-4 bg-white/5 px-4 py-2 rounded-full border border-white/5">
            <Search size={18} className="text-slate-500" />
            <input 
              type="text" 
              placeholder="Search hospitals..." 
              className="bg-transparent border-none outline-none text-sm w-64"
            />
          </div>
          <div className="flex items-center gap-4">
            <button className="bg-emerald-500 text-white px-5 py-2.5 rounded-xl font-bold flex items-center gap-2 hover:bg-emerald-600 transition-all">
              <PlusCircle size={18} /> Add New Hospital
            </button>
            <div className="w-10 h-10 rounded-full glass border-slate-700 flex items-center justify-center font-bold text-emerald-400 shadow-lg">
              W
            </div>
          </div>
        </header>

        <div className="p-8 space-y-8">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { label: 'Active Sites', value: '12', icon: Activity, color: 'text-blue-500' },
              { label: 'Avg. Success Rate', value: '99.98%', icon: CheckCircle2, color: 'text-emerald-500' },
              { label: 'Incidents (24h)', value: '1', icon: AlertTriangle, color: 'text-amber-500' },
            ].map((stat, idx) => (
              <div key={idx} className="glass p-6 rounded-2xl border border-white/5">
                <div className="flex justify-between items-start mb-4">
                  <span className="text-slate-400 font-medium">{stat.label}</span>
                  <stat.icon className={stat.color} size={24} />
                </div>
                <div className="text-3xl font-bold">{stat.value}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Sites List */}
            <div className="lg:col-span-2 space-y-4">
              <h3 className="text-xl font-bold flex items-center gap-2">
                <Shield size={20} className="text-emerald-500" /> Monitoring Status
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {MOCK_SITES.map(site => (
                  <div key={site.id} className="glass rounded-2xl overflow-hidden border border-white/5 group hover:border-emerald-500/30 transition-all">
                    <div className="relative h-32 overflow-hidden">
                      <img src={site.screenshot} alt={site.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                      <div className="absolute top-3 right-3">
                        <span className={`px-2 py-1 rounded-md text-[10px] uppercase font-bold tracking-wider ${
                          site.status === 'success' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50' : 'bg-amber-500/20 text-amber-400 border border-amber-500/50'
                        }`}>
                          {site.status}
                        </span>
                      </div>
                    </div>
                    <div className="p-5 space-y-3">
                      <h4 className="font-bold text-lg truncate">{site.name}</h4>
                      <div className="flex justify-between text-xs text-slate-400">
                        <span>Uptime: {site.uptime}</span>
                        <a href={site.url} className="text-blue-400 hover:underline">View Site</a>
                      </div>
                      <div className="flex gap-2">
                        <button className="flex-1 py-2 glass rounded-lg text-xs font-bold hover:bg-white/5">Details</button>
                        <button className="px-4 py-2 bg-emerald-500/10 text-emerald-400 rounded-lg text-xs font-bold hover:bg-emerald-500/20">Manual Check</button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Response Time Chart */}
            <div className="glass rounded-2xl p-6 border border-white/5 space-y-4">
              <h3 className="font-bold flex items-center gap-2">
                <BarChart3 size={18} className="text-blue-400" /> Response Time (ms)
              </h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={MOCK_CHART}>
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
              </div>
              <div className="bg-blue-500/10 border border-blue-500/20 p-4 rounded-xl text-xs text-blue-300 leading-relaxed">
                <Activity size={14} className="inline mr-1 mb-1" />
                성능 데이터 분석 결과, 오후 1시경 트래픽 집중으로 인해 응답 시간이 약 400ms까지 일시적으로 상승했습니다.
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
