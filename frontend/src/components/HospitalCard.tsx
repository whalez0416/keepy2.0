import React from 'react';
import { Site, sitesApi } from '../lib/api';

interface HospitalCardProps {
  site: Site;
  onRefresh?: () => void;
}

const HospitalCard: React.FC<HospitalCardProps> = ({ site, onRefresh }) => {
  const handleManualCheck = async () => {
    try {
      await sitesApi.manualCheck(site.id);
      if (onRefresh) onRefresh();
      alert('Manual check triggered!');
    } catch (error) {
      console.error('Failed to run manual check:', error);
    }
  };

  // 백엔드에서 제공하는 스크린샷 경로가 있으면 사용, 없으면 플레이스홀더
  const screenshotUrl = site.id % 2 === 0 
    ? `https://via.placeholder.com/300x150/10b981/ffffff?text=${encodeURIComponent(site.site_name)}`
    : `https://via.placeholder.com/300x150/1e293b/ffffff?text=${encodeURIComponent(site.site_name)}`;

  return (
    <div className="glass rounded-2xl overflow-hidden border border-white/5 group hover:border-emerald-500/30 transition-all">
      <div className="relative h-32 overflow-hidden bg-slate-900">
        <img 
          src={screenshotUrl} 
          alt={site.site_name} 
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-80 group-hover:opacity-100" 
        />
        <div className="absolute top-3 right-3">
          <span className="px-2 py-1 rounded-md text-[10px] uppercase font-bold tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/50">
            Monitoring
          </span>
        </div>
      </div>
      <div className="p-5 space-y-3">
        <h4 className="font-bold text-lg truncate">{site.site_name}</h4>
        <div className="flex justify-between text-xs text-slate-400">
          <span>{site.hospital_name || 'Hospital'}</span>
          <a href={site.homepage_url} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:underline transition-all">Visit Site</a>
        </div>
        <div className="flex gap-2">
          <button className="flex-1 py-2 glass rounded-lg text-xs font-bold hover:bg-white/5 transition-all">Details</button>
          <button 
            onClick={handleManualCheck}
            className="px-4 py-2 bg-emerald-500/10 text-emerald-400 rounded-lg text-xs font-bold hover:bg-emerald-500/20 transition-all"
          >
            Manual Check
          </button>
        </div>
      </div>
    </div>
  );
};

export default HospitalCard;
