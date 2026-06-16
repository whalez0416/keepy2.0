import React from 'react';
import { Activity, ExternalLink, RefreshCw } from 'lucide-react';
import { Site, sitesApi } from '../lib/api';

interface HospitalCardProps {
  site: Site;
  onRefresh?: () => void;
  onEdit?: (site: Site) => void;
  onViewLog?: () => void;
}

const HospitalCard: React.FC<HospitalCardProps> = ({ site, onRefresh, onEdit, onViewLog }) => {
  const [checking, setChecking] = React.useState(false);

  const handleManualCheck = async () => {
    try {
      setChecking(true);
      await sitesApi.manualCheck(site.id);
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Failed to run manual check:', error);
    } finally {
      setChecking(false);
    }
  };

  const isError = site.last_check_status === 'error' || site.last_check_status === 'fail';
  const statusColor = isError ? 'text-red-400' : 'text-emerald-400';
  const statusBg = isError ? 'bg-red-500/20' : 'bg-emerald-500/20';
  const statusBorder = isError ? 'border-red-500/50' : 'border-emerald-500/50';
  const statusLabel = isError ? '장애 발생' : '정상 작동중';

  const screenshotUrl = site.id % 2 === 0 
    ? `https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&q=80&w=400&h=200`
    : `https://images.unsplash.com/photo-1538108149393-fbbd81895907?auto=format&fit=crop&q=80&w=400&h=200`;

  return (
    <div className={`glass rounded-2xl overflow-hidden border border-white/5 group hover:border-white/20 transition-all duration-300 ${isError ? 'glow-red' : ''}`}>
      <div className="relative h-32 overflow-hidden bg-slate-900">
        <img 
          src={screenshotUrl} 
          alt={site.site_name} 
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 opacity-60 group-hover:opacity-80" 
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#0c0e14] to-transparent opacity-60" />
        <div className="absolute top-3 right-3 flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isError ? 'bg-red-500' : 'bg-emerald-500'} pulse-soft`} />
          <span className={`px-2 py-1 rounded-md text-[10px] uppercase font-bold tracking-wider ${statusBg} ${statusColor} border ${statusBorder} backdrop-blur-md`}>
            {statusLabel}
          </span>
        </div>
      </div>
      <div className="p-5 space-y-4">
        <div>
          <h4 className="font-bold text-lg truncate group-hover:text-[#c8d4de] transition-colors">{site.site_name}</h4>
          <div className="flex items-center gap-1 text-[10px] text-slate-500 font-medium uppercase mt-1">
            <Activity size={10} />
            {site.hospital_name || '일반 병원'}
          </div>
        </div>

        <div className="flex justify-between items-center text-xs">
           <span className="text-slate-400">마지막 점검: {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
           <a 
            href={site.homepage_url} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="flex items-center gap-1 text-[#c8d4de] hover:text-[#dbe3ea] transition-colors font-semibold"
          >
            사이트 방문 <ExternalLink size={12} />
          </a>
        </div>

        <div className="flex gap-2">
          <button 
            onClick={() => onEdit?.(site)}
            className="flex-1 py-2.5 glass rounded-xl text-xs font-bold hover:bg-white/10 transition-all border-white/10"
          >
            상세 설정
          </button>
          <button 
            onClick={onViewLog}
            className={`flex-1 py-2.5 rounded-xl text-xs font-bold transition-all border ${isError ? 'bg-red-500/10 text-red-400 border-red-500/30 hover:bg-red-500/20' : 'bg-white/5 text-slate-300 border-white/10 hover:bg-white/10'}`}
          >
            로그 보기
          </button>
          <button 
            onClick={handleManualCheck}
            disabled={checking}
            className={`px-4 py-2.5 bg-gradient-to-b from-[#e9eef2] via-[#b9c4cd] to-[#8b97a1] text-[#0a0c0f] rounded-xl text-xs font-bold hover:brightness-110 border border-white/40 transition-all flex items-center gap-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.5),0_8px_24px_rgba(0,0,0,0.5)] ${checking ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <RefreshCw size={14} className={checking ? 'animate-spin' : ''} />
            {checking ? '' : '재점검'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default HospitalCard;
