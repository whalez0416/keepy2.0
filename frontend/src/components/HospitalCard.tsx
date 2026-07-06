import React from 'react';
import { Activity, ExternalLink, RefreshCw, Shield } from 'lucide-react';
import { Site, SiteCheckLog, sitesApi } from '../lib/api';

interface HospitalCardProps {
  site: Site;
  /** Dashboard가 가용성 로그(홈페이지/폼) 기준으로 계산해 내려주는 상태 */
  status?: 'ok' | 'warn' | 'error' | 'pending';
  latestLog?: SiteCheckLog | null;
  onRefresh?: () => void;
  onEdit?: (site: Site) => void;
  onViewLog?: () => void;
}

const HospitalCard: React.FC<HospitalCardProps> = ({ site, status = 'pending', latestLog, onRefresh, onEdit, onViewLog }) => {
  const [checking, setChecking] = React.useState(false);

  const handleManualCheck = async () => {
    try {
      setChecking(true);
      const res = await sitesApi.manualCheck(site.id);
      // 점검은 백그라운드로 실행됨 — 시작 안내만 표시
      if (res.data?.message) alert(res.data.message);
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Failed to run manual check:', error);
      alert('점검 요청에 실패했습니다. 잠시 후 다시 시도해 주세요.');
    } finally {
      setChecking(false);
    }
  };

  const S = {
    ok:      { label: '정상 작동중', text: 'text-emerald-400', bg: 'bg-emerald-500/20', border: 'border-emerald-500/50', dot: 'bg-emerald-500', header: 'from-emerald-500/15' },
    warn:    { label: '주의 필요',   text: 'text-amber-400',   bg: 'bg-amber-500/20',   border: 'border-amber-500/50',   dot: 'bg-amber-500',   header: 'from-amber-500/15' },
    error:   { label: '장애 발생',   text: 'text-red-400',     bg: 'bg-red-500/20',     border: 'border-red-500/50',     dot: 'bg-red-500',     header: 'from-red-500/15' },
    pending: { label: '첫 점검 대기', text: 'text-slate-400',   bg: 'bg-slate-500/20',   border: 'border-slate-500/50',   dot: 'bg-slate-500',   header: 'from-slate-500/10' },
  }[status];

  const lastCheckedText = latestLog
    ? new Date(latestLog.checked_at).toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    : '아직 없음 (곧 시작됩니다)';

  return (
    <div className={`glass rounded-2xl overflow-hidden border border-white/5 group hover:border-white/20 transition-all duration-300 ${status === 'error' ? 'glow-red' : ''}`}>
      <div className={`relative h-20 overflow-hidden bg-gradient-to-br ${S.header} to-transparent flex items-center px-5`}>
        <Shield size={40} className={`${S.text} opacity-30`} />
        <div className="absolute top-3 right-3 flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${S.dot} pulse-soft`} />
          <span className={`px-2 py-1 rounded-md text-[10px] uppercase font-bold tracking-wider ${S.bg} ${S.text} border ${S.border} backdrop-blur-md`}>
            {S.label}
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
           <span className="text-slate-400">마지막 점검: {lastCheckedText}</span>
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
            className={`flex-1 py-2.5 rounded-xl text-xs font-bold transition-all border ${status === 'error' ? 'bg-red-500/10 text-red-400 border-red-500/30 hover:bg-red-500/20' : 'bg-white/5 text-slate-300 border-white/10 hover:bg-white/10'}`}
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
