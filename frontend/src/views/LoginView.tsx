import React, { useState } from 'react';
import { Shield, Mail, Lock, Loader, AlertCircle, ArrowRight } from 'lucide-react';
import { authApi } from '../lib/api';

interface LoginViewProps {
  onLoginSuccess: (token: string, user: any) => void;
  onSwitchToRegister: () => void;
}

const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess, onSwitchToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await authApi.login(email, password);
      onLoginSuccess(res.data.access_token, res.data.user);
    } catch (err: any) {
      if (!err.response) {
        setError('서버와 통신할 수 없습니다. 잠시 후 다시 시도해주세요.');
      } else {
        setError(err.response?.data?.detail || '로그인에 실패했습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0c0f] flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background Blobs */}
      <div className="absolute top-1/4 -right-20 w-96 h-96 bg-[#7896b2]/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-1/4 -left-20 w-96 h-96 bg-[#5b6b7a]/10 blur-[120px] rounded-full pointer-events-none" />

      <div className="w-full max-w-md animate-in fade-in zoom-in duration-500">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-gradient-to-b from-[#9fb2c2]/20 to-[#0a0c0f]/60 border border-[#9fb2c2]/30 mb-6 shadow-[inset_0_1px_0_rgba(200,212,222,0.18),0_0_30px_rgba(159,178,194,0.15)]">
            <Shield className="text-[#c8d4de]" size={32} style={{ filter: 'drop-shadow(0 0 6px rgba(159,178,194,0.4))' }} />
          </div>
          <h1 className="text-4xl font-black text-white tracking-tighter mb-2 flex items-center justify-center gap-1.5">
            Keepy<span className="inline-block w-2 h-2 rounded-full bg-[#c8d4de] shadow-[0_0_10px_rgba(159,178,194,0.8)]" />
          </h1>
          <p className="text-slate-500 font-bold uppercase tracking-[0.2em] text-[10px]">Premium Monitoring Solution</p>
        </div>

        <div className="glass rounded-2xl border border-[#9fb2c2]/10 p-8 shadow-2xl">
          <div className="mb-8">
            <h2 className="text-xl font-bold text-slate-200 mb-1">다시 오신 것을 환영합니다</h2>
            <p className="text-slate-500 text-sm font-medium">계정에 로그인하여 병원 상태를 확인하세요</p>
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
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-[#9fb2c2] transition-colors" size={18} />
                <input
                  required
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full glass border border-white/5 rounded-lg py-4 pl-12 pr-4 outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 focus:border-[#9fb2c2]/40 transition-all font-bold placeholder:text-slate-700"
                  placeholder="admin@hospital.com"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">비밀번호</label>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-[#9fb2c2] transition-colors" size={18} />
                <input
                  required
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full glass border border-white/5 rounded-lg py-4 pl-12 pr-4 outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 focus:border-[#9fb2c2]/40 transition-all font-bold placeholder:text-slate-700"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              disabled={loading}
              className="w-full bg-gradient-to-b from-[#e9eef2] via-[#b9c4cd] to-[#8b97a1] hover:brightness-110 disabled:opacity-50 text-[#0a0c0f] py-4 rounded-lg font-black flex items-center justify-center gap-3 transition-all border border-white/40 shadow-[inset_0_1px_0_rgba(255,255,255,0.5),0_10px_30px_rgba(0,0,0,0.5)] active:scale-95 mt-8"
            >
              {loading ? (
                <Loader size={20} className="animate-spin" />
              ) : (
                <>
                  로그인
                  <ArrowRight size={20} />
                </>
              )}
            </button>
          </form>
        </div>

        <div className="mt-8 text-center flex flex-col gap-3">
          <div className="text-slate-500 text-sm font-bold">
            가입 및 서비스 발급 문의: 010-6616-3032
          </div>
          <button
            onClick={onSwitchToRegister}
            className="text-slate-600 hover:text-[#9fb2c2] text-xs font-bold transition-colors"
          >
            발급 프로세스 안내 보기
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginView;
