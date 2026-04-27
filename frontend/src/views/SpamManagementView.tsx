import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Search, 
  Filter, 
  Brain, 
  Layout, 
  ChevronRight,
  Activity,
  History
} from 'lucide-react';
import { sitesApi, Site } from '../lib/api';
import SpamView from '../components/SpamView';

const SpamManagementView: React.FC = () => {
  const [sites, setSites] = useState<Site[]>([]);
  const [selectedSite, setSelectedSite] = useState<Site | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchSites = async () => {
    try {
      setLoading(true);
      const res = await sitesApi.list();
      setSites(res.data);
      if (res.data.length > 0 && !selectedSite) {
        setSelectedSite(res.data[0]);
      }
    } catch (error) {
      console.error('Failed to fetch sites:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSites();
  }, []);

  const filteredSites = sites.filter(site => 
    site.site_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    site.hospital_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-8 space-y-8 animate-in slide-up duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">AI 스팸 관리</h2>
          <p className="text-slate-400 mt-1 font-medium">Gemini AI 기반으로 병원 게시판의 스팸을 정밀하게 탐지하고 관리합니다.</p>
        </div>
        <div className="flex gap-3">
            <div className="bg-violet-500/10 border border-violet-500/20 px-4 py-2 rounded-2xl flex items-center gap-2">
                <Brain size={18} className="text-violet-400" />
                <span className="text-xs font-bold text-violet-300 uppercase tracking-wider">Gemini 1.5 Flash Active</span>
            </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Site Selector */}
        <div className="lg:col-span-4 space-y-4">
          <div className="relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-violet-400 transition-colors" size={18} />
            <input 
              type="text" 
              placeholder="병원 검색..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full glass border border-white/5 rounded-2xl py-3.5 pl-12 pr-4 focus:ring-2 focus:ring-violet-500/30 focus:border-violet-500/50 outline-none transition-all placeholder:text-slate-600 font-medium text-sm"
            />
          </div>

          <div className="glass rounded-3xl overflow-hidden border border-white/5 shadow-2xl flex flex-col h-[600px]">
            <div className="p-4 border-b border-white/5 bg-white/[0.02]">
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">병원 목록 ({filteredSites.length})</span>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-hide">
              {loading ? (
                Array(6).fill(0).map((_, i) => (
                  <div key={i} className="h-16 bg-white/[0.02] rounded-2xl animate-pulse m-2" />
                ))
              ) : filteredSites.length === 0 ? (
                <div className="py-20 text-center text-slate-600">
                    <p className="text-sm font-medium">검색 결과가 없습니다.</p>
                </div>
              ) : (
                filteredSites.map(site => (
                  <button
                    key={site.id}
                    onClick={() => setSelectedSite(site)}
                    className={`w-full text-left p-4 rounded-2xl transition-all group flex items-center justify-between ${
                      selectedSite?.id === site.id 
                        ? 'bg-violet-500/10 border border-violet-500/20' 
                        : 'hover:bg-white/[0.03] border border-transparent'
                    }`}
                  >
                    <div className="min-w-0">
                      <div className={`font-bold text-sm truncate ${selectedSite?.id === site.id ? 'text-violet-300' : 'text-slate-300'}`}>
                        {site.site_name}
                      </div>
                      <div className="text-[10px] text-slate-500 font-bold uppercase mt-0.5 truncate tracking-wider">
                        {site.hospital_name || '일반 그룹'}
                      </div>
                    </div>
                    <ChevronRight size={16} className={`transition-all ${selectedSite?.id === site.id ? 'text-violet-400 translate-x-0' : 'text-slate-700 -translate-x-2 opacity-0 group-hover:opacity-100 group-hover:translate-x-0'}`} />
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right: Spam Management Panel */}
        <div className="lg:col-span-8">
          <div className="glass rounded-3xl border border-white/5 shadow-2xl p-8 h-full">
            {selectedSite ? (
              <SpamView siteId={selectedSite.id} siteName={selectedSite.site_name} />
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-12 space-y-4">
                <div className="w-20 h-20 rounded-full bg-white/[0.02] border border-white/5 flex items-center justify-center text-slate-700">
                    <Shield size={40} />
                </div>
                <div>
                    <h3 className="text-xl font-bold text-slate-300">병원을 선택해주세요</h3>
                    <p className="text-slate-500 text-sm mt-2">왼쪽 목록에서 스팸 관리를 진행할 병원을 선택하세요.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpamManagementView;
