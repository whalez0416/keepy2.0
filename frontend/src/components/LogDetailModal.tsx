import React from 'react';
import { X, AlertCircle, Clock, Globe, Camera, RefreshCw, ChevronRight } from 'lucide-react';
import { Site, SiteCheckLog } from '../lib/api';

interface LogDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  site: Site | null;
  latestLog: SiteCheckLog | null;
}

const LogDetailModal: React.FC<LogDetailModalProps> = ({ isOpen, onClose, site, latestLog }) => {
  if (!isOpen || !site) return null;

  const isError = latestLog?.status !== 'success';

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-6">
      <div className="fixed inset-0 bg-[#080a0f]/80 backdrop-blur-xl" onClick={onClose} />
      
      <div className="relative w-full max-w-2xl glass rounded-[40px] border border-white/10 shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-300">
        {/* Header */}
        <div className={`p-8 flex items-center justify-between ${isError ? 'bg-red-500/10' : 'bg-emerald-500/10'}`}>
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${isError ? 'bg-red-500 text-white' : 'bg-emerald-500 text-white'} shadow-2xl`}>
              {isError ? <AlertCircle size={24} /> : <Globe size={24} />}
            </div>
            <div>
              <h3 className="text-2xl font-black text-white leading-none">{site.site_name}</h3>
              <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mt-2">{site.hospital_name || 'System Monitoring'}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-3 hover:bg-white/5 rounded-2xl text-slate-500 transition-colors">
            <X size={24} />
          </button>
        </div>

        <div className="p-8 space-y-8">
          {/* Status Banner */}
          <div className={`p-6 rounded-[32px] border ${isError ? 'bg-red-500/5 border-red-500/20' : 'bg-emerald-500/5 border-emerald-500/20'} flex items-start gap-4`}>
             <div className={`mt-1 ${isError ? 'text-red-500' : 'text-emerald-500'}`}>
                <AlertCircle size={20} />
             </div>
             <div>
                <h4 className={`font-black text-lg ${isError ? 'text-red-400' : 'text-emerald-400'}`}>
                  {isError ? '장애가 감지되었습니다' : '시스템이 정상입니다'}
                </h4>
                <p className="text-slate-400 text-sm font-medium mt-1 leading-relaxed">
                  {latestLog?.fail_reason || '현재 사이트가 정상적으로 응답하고 있으며, 모든 기능이 최상의 상태를 유지하고 있습니다.'}
                </p>
             </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="glass p-5 rounded-[24px] border-white/5">
              <div className="flex items-center gap-2 text-slate-500 mb-2">
                <Clock size={14} />
                <span className="text-[10px] font-black uppercase tracking-widest">마지막 확인 시각</span>
              </div>
              <div className="text-lg font-black text-white">
                {latestLog ? new Date(latestLog.checked_at).toLocaleTimeString('ko-KR', { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '-'}
              </div>
            </div>
            <div className="glass p-5 rounded-[24px] border-white/5">
              <div className="flex items-center gap-2 text-slate-500 mb-2">
                <RefreshCw size={14} />
                <span className="text-[10px] font-black uppercase tracking-widest">응답 속도</span>
              </div>
              <div className="text-lg font-black text-white">
                {latestLog?.response_time || 0} <span className="text-xs text-slate-500">ms</span>
              </div>
            </div>
          </div>

          {/* Visual Proof */}
          <div className="space-y-3">
             <div className="flex items-center gap-2 text-slate-500 ml-1">
                <Camera size={14} />
                <span className="text-[10px] font-black uppercase tracking-widest">장애 시점 스크린샷 (Visual Proof)</span>
             </div>
             <div className="aspect-video rounded-[32px] bg-slate-900 overflow-hidden border border-white/10 relative group">
                {latestLog?.screenshot_path ? (
                  <img src={`/api/logs/screenshot/${latestLog.id}`} alt="Failure Screenshot" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-slate-700 bg-slate-900/50">
                    <Camera size={48} strokeWidth={1} className="mb-2 opacity-20" />
                    <p className="text-sm italic font-medium opacity-40">캡쳐된 데이터가 없습니다.</p>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-6">
                   <p className="text-xs text-white/60 font-medium">점검 시스템: Playwright Agent (Chrome)</p>
                </div>
             </div>
          </div>

          <div className="flex gap-4">
             <button className="flex-1 bg-white/[0.03] hover:bg-white/[0.08] text-white py-4 rounded-2xl font-black transition-all border border-white/5" onClick={onClose}>
                닫기
             </button>
             <a 
              href={site.homepage_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex-1 bg-gradient-to-b from-[#e9eef2] via-[#b9c4cd] to-[#8b97a1] text-[#0a0c0f] py-4 rounded-2xl font-black text-center flex items-center justify-center gap-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.5),0_8px_24px_rgba(0,0,0,0.5)] hover:brightness-110 border border-white/40 transition-all"
            >
              실제 사이트 방문 <ChevronRight size={18} />
             </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LogDetailModal;
