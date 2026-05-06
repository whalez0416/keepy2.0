import React, { useState } from 'react';
import { Shield, Mail, Lock, Loader, AlertCircle, ArrowRight, UserPlus, CheckCircle2 } from 'lucide-react';
import { authApi } from '../lib/api';

interface RegisterViewProps {
  onSwitchToLogin: () => void;
  onRegisterSuccess: (email: string) => void;
  onShowPricing: () => void;
}

const RegisterView: React.FC<RegisterViewProps> = ({ onSwitchToLogin, onRegisterSuccess, onShowPricing }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await authApi.register({ email, password });
      setSuccess(true);
      setTimeout(() => {
        onRegisterSuccess(email);
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || '회원가입에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-[#080a0f] flex items-center justify-center p-6">
        <div className="w-full max-w-md text-center space-y-6 animate-in zoom-in duration-500">
          <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-emerald-500/20 border border-emerald-500/30 shadow-2xl shadow-emerald-500/20">
            <CheckCircle2 className="text-emerald-400" size={48} />
          </div>
          <div className="space-y-2">
            <h2 className="text-3xl font-black text-white tracking-tight">가입 완료!</h2>
            <p className="text-slate-400 font-medium">환영합니다. 잠시 후 로그인 화면으로 이동합니다.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#080a0f] flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background Blobs */}
      <div className="absolute top-1/4 -right-20 w-96 h-96 bg-blue-600/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-1/4 -left-20 w-96 h-96 bg-emerald-600/10 blur-[120px] rounded-full pointer-events-none" />
      
      <div className="w-full max-w-md animate-in fade-in slide-up duration-500">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-3xl bg-emerald-500/20 border border-emerald-500/30 mb-6 shadow-2xl shadow-emerald-500/20">
            <UserPlus className="text-emerald-400" size={32} />
          </div>
          <h1 className="text-4xl font-black text-white tracking-tighter mb-2">담당자 등록</h1>
          <p className="text-slate-500 font-bold uppercase tracking-[0.2em] text-[10px]">Hospital Administrator Sign Up</p>
        </div>

        <div className="glass rounded-[32px] border border-white/5 p-8 shadow-2xl">
          <div className="mb-8">
            <h2 className="text-xl font-bold text-slate-200 mb-1">새 계정 만들기</h2>
            <p className="text-slate-500 text-sm font-medium">Keepy를 통해 병원 시스템 모니터링을 시작하세요.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-2xl flex items-center gap-3 text-red-400 text-sm font-bold animate-in shake duration-300">
                <AlertCircle size={20} />
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">이메일 주소</label>
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-emerald-400 transition-colors" size={18} />
                <input
                  required
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full glass border border-white/5 rounded-2xl py-4 pl-12 pr-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-bold placeholder:text-slate-700"
                  placeholder="admin@hospital.com"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">비밀번호</label>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-emerald-400 transition-colors" size={18} />
                <input
                  required
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full glass border border-white/5 rounded-2xl py-4 pl-12 pr-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-bold placeholder:text-slate-700"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">비밀번호 확인</label>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-emerald-400 transition-colors" size={18} />
                <input
                  required
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full glass border border-white/5 rounded-2xl py-4 pl-12 pr-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-bold placeholder:text-slate-700"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              disabled={loading}
              className="w-full bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white py-4 rounded-2xl font-black flex items-center justify-center gap-3 transition-all shadow-2xl shadow-emerald-500/30 active:scale-95 mt-8"
            >
              {loading ? (
                <Loader size={20} className="animate-spin" />
              ) : (
                <>
                  가입하기
                  <ArrowRight size={20} />
                </>
              )}
            </button>
          </form>
        </div>

        <div className="mt-8 text-center flex flex-col gap-3">
          <button 
            onClick={onSwitchToLogin}
            className="text-slate-500 hover:text-emerald-400 text-sm font-bold transition-colors"
          >
            이미 계정이 있으신가요? 로그인하기
          </button>
          <button 
            onClick={onShowPricing}
            className="text-slate-400/50 hover:text-white text-xs font-bold transition-colors uppercase tracking-widest"
          >
            요금제 정책 확인하기
          </button>
        </div>
      </div>
    </div>
  );
};

export default RegisterView;
