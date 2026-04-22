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
  AlertTriangle
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
    if (!confirm('Are you sure you want to delete this hospital?')) return;
    try {
      await sitesApi.delete(id);
      fetchSites();
    } catch (error) {
      alert('Failed to delete site');
    }
  };

  return (
    <div className="p-8 space-y-6 animate-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold">Managed Hospitals</h2>
          <p className="text-slate-400 text-sm">Manage monitoring targets and configurations.</p>
        </div>
        <button 
          onClick={handleAdd}
          className="bg-emerald-500 hover:bg-emerald-600 px-6 py-3 rounded-xl font-bold flex items-center gap-2 transition-all shadow-lg shadow-emerald-500/20"
        >
          <Plus size={20} /> Add New Hospital
        </button>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
          <input 
            type="text" 
            placeholder="Filter by name, URL, or group..." 
            className="w-full bg-white/5 border border-white/5 rounded-xl py-3 pl-12 pr-4 focus:ring-2 focus:ring-emerald-500/50 outline-none transition-all"
          />
        </div>
        <button className="glass px-6 py-3 rounded-xl flex items-center gap-2 hover:bg-white/5 transition-all text-slate-300">
          <Filter size={18} /> Filters
        </button>
      </div>

      {/* Sites Table */}
      <div className="glass rounded-2xl overflow-hidden border border-white/5">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-white/5 text-slate-400 text-xs uppercase tracking-wider">
              <th className="px-6 py-4 font-semibold">Hospital Name</th>
              <th className="px-6 py-4 font-semibold">HP / Form URL</th>
              <th className="px-6 py-4 font-semibold">Methods</th>
              <th className="px-6 py-4 font-semibold">Status</th>
              <th className="px-6 py-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {loading ? (
              [1, 2, 3].map(i => (
                <tr key={i} className="animate-pulse">
                  <td colSpan={5} className="px-6 py-8 h-16 bg-white/5 opacity-50" />
                </tr>
              ))
            ) : sites.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                  <Activity size={32} className="mx-auto mb-2 opacity-20" />
                  No sites found.
                </td>
              </tr>
            ) : (
              sites.map(site => (
                <tr key={site.id} className="hover:bg-white/5 transition-all group">
                  <td className="px-6 py-5">
                    <div className="font-bold">{site.site_name}</div>
                    <div className="text-[10px] text-slate-500 uppercase">{site.hospital_name || 'General'}</div>
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex flex-col gap-1 text-sm">
                      <div className="text-blue-400 truncate max-w-[150px]">{site.homepage_url}</div>
                      {site.form_url && (
                        <div className="text-emerald-400/70 text-[10px] truncate max-w-[150px]">Form: {site.form_url}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex gap-1">
                      <span className="bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded text-[10px] border border-blue-500/20">HP</span>
                      {site.form_url && (
                        <span className="bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded text-[10px] border border-emerald-500/20">FORM</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${site.is_active ? 'bg-emerald-500' : 'bg-slate-600'} shadow-[0_0_8px_rgba(16,185,129,0.5)]`} />
                      <span className="text-sm">{site.is_active ? 'Active' : 'Paused'}</span>
                    </div>
                  </td>
                  <td className="px-6 py-5 text-right">
                    <div className="flex justify-end gap-2">
                       <button onClick={() => handleEdit(site)} className="text-slate-500 hover:text-emerald-400 p-2 rounded-lg hover:bg-emerald-500/10 transition-all">
                        <Edit2 size={16} />
                      </button>
                      <button onClick={() => handleDelete(site.id)} className="text-slate-500 hover:text-red-400 p-2 rounded-lg hover:bg-red-500/10 transition-all">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
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
