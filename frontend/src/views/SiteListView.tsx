import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Search, 
  Filter, 
  ExternalLink, 
  MoreVertical,
  Activity,
  Edit2,
  Trash2,
  AlertTriangle,
  Globe,
  FileText
} from 'lucide-react';
import { sitesApi, Site } from '../lib/api';
import SiteConfigModal from '../components/SiteConfigModal';

const SiteListView: React.FC = () => {
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedSite, setSelectedSite] = useState<Site | null>(null);

  const fetchSites = async () => {
    try {
      setLoading(true);
      const res = await sitesApi.list();
      setSites(res.data);
    } catch (error) {
      console.error('Failed to fetch sites:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSites();
  }, []);

  const handleAdd = () => {
    setSelectedSite(null);
    setIsModalOpen(true);
  };

  const handleEdit = (site: Site) => {
    setSelectedSite(site);
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('정말로 이 병원을 삭제하시겠습니까?')) return;
    try {
      await sitesApi.delete(id);
      fetchSites();
    } catch (error) {
      alert('삭제에 실패했습니다.');
    }
  };

  return (
    <div className="p-8 space-y-8 animate-in slide-up duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">병원 관리</h2>
          <p className="text-slate-400 mt-1 font-medium">모니터링 대상 병원 및 설정을 관리합니다.</p>
        </div>
        <button 
          onClick={handleAdd}
          className="bg-emerald-500 hover:bg-emerald-600 px-8 py-4 rounded-2xl font-bold flex items-center gap-2 transition-all shadow-xl shadow-emerald-500/20 active:scale-95"
        >
          <Plus size={20} /> 신규 병원 등록
        </button>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-emerald-400 transition-colors" size={20} />
          <input 
            type="text" 
            placeholder="병원명, URL 또는 그룹으로 검색..." 
            className="w-full glass border border-white/5 rounded-2xl py-4 pl-12 pr-4 focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500/50 outline-none transition-all placeholder:text-slate-600 font-medium"
          />
        </div>
        <button className="glass px-6 py-4 rounded-2xl flex items-center gap-2 hover:bg-white/10 transition-all text-slate-300 font-bold border-white/10">
          <Filter size={18} /> 필터 상세
        </button>
      </div>

      {/* Sites Table */}
      <div className="glass rounded-3xl overflow-hidden border border-white/5 shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/[0.02] text-slate-500 text-[11px] font-bold uppercase tracking-[0.1em] border-b border-white/5">
                <th className="px-8 py-5">병원 정보</th>
                <th className="px-8 py-5">접속 경로 (HP/FORM)</th>
                <th className="px-8 py-5">모니터링 항목</th>
                <th className="px-8 py-5 text-center">상태</th>
                <th className="px-8 py-5 text-right">관리</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                [1, 2, 3, 4, 5].map(i => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan={5} className="px-8 py-6 h-20 bg-white/[0.01]" />
                  </tr>
                ))
              ) : sites.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-8 py-24 text-center text-slate-500">
                    <Activity size={48} className="mx-auto mb-4 opacity-10" />
                    <p className="font-medium text-lg">관리 중인 병원이 없습니다.</p>
                  </td>
                </tr>
              ) : (
                sites.map(site => (
                  <tr key={site.id} className="hover:bg-white/[0.03] transition-all group">
                    <td className="px-8 py-6">
                      <div className="font-bold text-slate-200 group-hover:text-white transition-colors">{site.site_name}</div>
                      <div className="text-[10px] text-slate-500 font-bold uppercase mt-1 tracking-wider">{site.hospital_name || '일반 그룹'}</div>
                    </td>
                    <td className="px-8 py-6">
                      <div className="flex flex-col gap-1.5">
                        <div className="flex items-center gap-2 text-xs text-blue-400 font-medium">
                          <Globe size={12} className="opacity-50" />
                          <span className="truncate max-w-[200px]">{site.homepage_url}</span>
                        </div>
                        {site.form_url && (
                          <div className="flex items-center gap-2 text-xs text-emerald-400/70 font-medium">
                            <FileText size={12} className="opacity-50" />
                            <span className="truncate max-w-[200px]">{site.form_url}</span>
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      <div className="flex gap-1.5">
                        <span className="bg-blue-500/10 text-blue-400 px-2.5 py-1 rounded-lg text-[10px] font-bold border border-blue-500/20">홈페이지</span>
                        {site.form_url && (
                          <span className="bg-emerald-500/10 text-emerald-400 px-2.5 py-1 rounded-lg text-[10px] font-bold border border-emerald-500/20">상담폼</span>
                        )}
                      </div>
                    </td>
                    <td className="px-8 py-6 text-center">
                      <div className="flex flex-col items-center gap-1">
                        <div className={`w-2.5 h-2.5 rounded-full ${site.is_active ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-slate-700'}`} />
                        <span className={`text-[10px] font-bold ${site.is_active ? 'text-emerald-400' : 'text-slate-500'}`}>
                          {site.is_active ? '감시중' : '중단됨'}
                        </span>
                      </div>
                    </td>
                    <td className="px-8 py-6 text-right">
                      <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                         <button 
                          onClick={() => handleEdit(site)} 
                          className="text-slate-400 hover:text-emerald-400 p-2.5 rounded-xl hover:bg-emerald-500/10 transition-all active:scale-90"
                          title="수정"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button 
                          onClick={() => handleDelete(site.id)} 
                          className="text-slate-400 hover:text-red-400 p-2.5 rounded-xl hover:bg-red-500/10 transition-all active:scale-90"
                          title="삭제"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <SiteConfigModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={fetchSites}
        site={selectedSite}
      />
    </div>
  );
};

export default SiteListView;
