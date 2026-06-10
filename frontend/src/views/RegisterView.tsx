import React from 'react';
import { Shield, Key, AlertCircle, ArrowLeft, Mail, Phone, Calendar } from 'lucide-react';

interface RegisterViewProps {
  onSwitchToLogin: () => void;
  onRegisterSuccess: (email: string) => void;
}

const RegisterView: React.FC<RegisterViewProps> = ({ onSwitchToLogin }) => {
  return (
    <div className="min-h-screen bg-[#080a0f] flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background Blobs */}
      <div className="absolute top-1/4 -right-20 w-96 h-96 bg-blue-600/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-1/4 -left-20 w-96 h-96 bg-emerald-600/10 blur-[120px] rounded-full pointer-events-none" />
      
      <div className="w-full max-w-lg animate-in fade-in zoom-in duration-500">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-3xl bg-amber-500/20 border border-amber-500/30 mb-6 shadow-2xl shadow-amber-500/20">
            <Shield className="text-amber-400" size={32} />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tighter mb-2">계정 발급 및 등록 안내</h1>
          <p className="text-slate-500 font-bold uppercase tracking-[0.2em] text-[10px]">B2B Premium Account Provisioning Only</p>
        </div>

        <div className="glass rounded-[40px] border border-amber-500/10 p-8 shadow-2xl space-y-6 bg-amber-500/[0.01]">
          <div className="flex items-start gap-4 p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl">
            <AlertCircle className="text-amber-400 mt-1 shrink-0" size={24} />
            <div>
              <h4 className="font-bold text-white text-base">직접 회원가입은 제공되지 않습니다</h4>
              <p className="text-amber-200/80 text-xs mt-1 leading-relaxed">
                Keepy V2는 프리미엄 병원 보안/모니터링 서비스로, 보안 신뢰성과 멀티 테넌트 무결성을 유지하기 위해 **담당자 직접 계약 및 마스터 계정의 수동 발급 정책**을 채택하고 있습니다.
              </p>
            </div>
          </div>

          <div className="space-y-4 pt-2">
            <h3 className="text-sm font-black text-slate-300 uppercase tracking-wider ml-1">도입 및 발급 프로세스</h3>
            <div className="grid grid-cols-1 gap-3 text-xs">
              <div className="flex items-center gap-3 glass p-3.5 rounded-xl border-white/5">
                <span className="w-6 h-6 rounded-full bg-emerald-500/10 text-emerald-400 font-bold flex items-center justify-center text-[10px]">1</span>
                <span className="text-slate-300 font-bold">B2B 요금제 상담 및 상담 양식 접수 (영업팀)</span>
              </div>
              <div className="flex items-center gap-3 glass p-3.5 rounded-xl border-white/5">
                <span className="w-6 h-6 rounded-full bg-emerald-500/10 text-emerald-400 font-bold flex items-center justify-center text-[10px]">2</span>
                <span className="text-slate-300 font-bold">담당자가 마스터 계정을 통해 병원 관리자 계정 생성</span>
              </div>
              <div className="flex items-center gap-3 glass p-3.5 rounded-xl border-white/5">
                <span className="w-6 h-6 rounded-full bg-emerald-500/10 text-emerald-400 font-bold flex items-center justify-center text-[10px]">3</span>
                <span className="text-slate-300 font-bold">발급 완료 메일 확인 후 초기 임시 번호로 즉각 로그인</span>
              </div>
            </div>
          </div>

          <div className="h-[1px] bg-white/5 my-6" />

          <div className="space-y-3.5">
            <h3 className="text-sm font-black text-slate-300 uppercase tracking-wider ml-1">가입 및 문의 채널</h3>
            <div className="grid grid-cols-2 gap-3 text-xs font-bold text-slate-300">
              <div className="flex items-center gap-2.5 glass p-3 rounded-xl border-white/5">
                <Mail size={16} className="text-blue-400" />
                <span>master@keepy.com</span>
              </div>
              <div className="flex items-center gap-2.5 glass p-3 rounded-xl border-white/5">
                <Phone size={16} className="text-emerald-400" />
                <span>02-1234-5678</span>
              </div>
            </div>
          </div>

          <div className="pt-4">
            <button
              onClick={onSwitchToLogin}
              className="w-full py-4 bg-white/5 hover:bg-white/10 text-white rounded-2xl font-black text-sm flex items-center justify-center gap-2 transition-all border border-white/10 shadow-lg active:scale-95"
            >
              <ArrowLeft size={16} /> 로그인 화면으로 돌아가기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterView;
