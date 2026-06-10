import React, { useState } from 'react';
import {
  User,
  Shield,
  Key,
  LogOut,
  Loader,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { authApi } from '../lib/api';

interface SettingsViewProps {
  onLogout?: () => void;
}

const SettingsView: React.FC<SettingsViewProps> = ({ onLogout }) => {
  const [activeSection, setActiveSection] = useState<'profile' | 'security'>('profile');
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  // 로그인한 사용자 정보 (localStorage)
  const user = (() => {
    try {
      return JSON.parse(localStorage.getItem('keepy_user') || 'null');
    } catch {
      return null;
    }
  })();

  const sections = [
    { id: 'profile', label: '프로필 정보', icon: User },
    { id: 'security', label: '비밀번호 변경', icon: Shield },
    { id: 'logout', label: '로그아웃', icon: LogOut },
  ] as const;

  const handleChangePassword = async () => {
    setMsg(null);
    if (!currentPw || !newPw) {
      setMsg({ type: 'err', text: '현재 비밀번호와 새 비밀번호를 모두 입력해 주세요.' });
      return;
    }
    if (newPw.length < 8) {
      setMsg({ type: 'err', text: '새 비밀번호는 8자 이상이어야 합니다.' });
      return;
    }
    if (newPw !== confirmPw) {
      setMsg({ type: 'err', text: '새 비밀번호 확인이 일치하지 않습니다.' });
      return;
    }
    setSaving(true);
    try {
      await authApi.changePassword(currentPw, newPw);
      setMsg({ type: 'ok', text: '비밀번호가 성공적으로 변경되었습니다.' });
      setCurrentPw('');
      setNewPw('');
      setConfirmPw('');
    } catch (err: any) {
      setMsg({ type: 'err', text: err?.response?.data?.detail || '비밀번호 변경에 실패했습니다.' });
    } finally {
      setSaving(false);
    }
  };

  const isMaster = user?.role === 'superadmin';

  return (
    <div className="p-8 space-y-8 animate-in slide-up duration-500">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">설정</h2>
        <p className="text-slate-400 mt-1 font-medium">계정 정보와 비밀번호를 관리합니다.</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Navigation */}
        <div className="w-full lg:w-64 flex flex-row lg:flex-col gap-2 glass p-2 rounded-2xl h-fit">
          {sections.map((section) => {
            const Icon = section.icon;
            return (
              <button
                key={section.id}
                onClick={() => {
                  if (section.id === 'logout') {
                    onLogout?.();
                  } else {
                    setActiveSection(section.id as any);
                    setMsg(null);
                  }
                }}
                className={`flex-1 lg:flex-none flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${
                  activeSection === section.id
                    ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20'
                    : section.id === 'logout'
                    ? 'text-red-400 hover:bg-red-500/10'
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                }`}
              >
                <Icon size={18} />
                <span className="hidden md:inline">{section.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="flex-1 space-y-6">
          {activeSection === 'profile' && (
            <div className="glass p-8 rounded-3xl border border-white/5 space-y-8">
              <div className="flex items-center gap-6">
                <div className="w-24 h-24 rounded-3xl glass-morphism border-white/10 flex items-center justify-center font-black text-emerald-400 text-3xl shadow-2xl">
                  <User size={40} className="opacity-80" />
                </div>
                <div>
                  <h3 className="text-xl font-bold">{isMaster ? '마스터 관리자' : '병원 관리자'}</h3>
                  <p className="text-slate-500 text-sm font-medium">
                    {isMaster ? 'Super Admin' : 'Hospital Admin'}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">이메일 주소</label>
                  <input
                    type="email"
                    value={user?.email || ''}
                    className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none font-medium text-slate-400 cursor-not-allowed"
                    disabled
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">권한</label>
                  <input
                    type="text"
                    value={isMaster ? '마스터 관리자 (Super Admin)' : '병원 관리자 (Admin)'}
                    className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none font-medium text-slate-400 cursor-not-allowed"
                    disabled
                  />
                </div>
              </div>
              <p className="text-xs text-slate-600">
                이메일/권한은 보안을 위해 마스터 계정에서만 변경할 수 있습니다.
              </p>
            </div>
          )}

          {activeSection === 'security' && (
            <div className="glass p-8 rounded-3xl border border-white/5 space-y-8">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-2xl bg-amber-500/10 text-amber-400">
                  <Key size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-bold">비밀번호 변경</h3>
                  <p className="text-slate-500 text-sm">발급받은 임시 비밀번호를 본인만 아는 비밀번호로 바꾸세요.</p>
                </div>
              </div>

              {msg && (
                <div
                  className={`flex items-center gap-2 p-4 rounded-2xl text-sm font-bold border max-w-md ${
                    msg.type === 'ok'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : 'bg-red-500/10 text-red-400 border-red-500/20'
                  }`}
                >
                  {msg.type === 'ok' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
                  {msg.text}
                </div>
              )}

              <div className="space-y-6 max-w-md">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">현재 비밀번호</label>
                  <input
                    type="password"
                    value={currentPw}
                    onChange={(e) => setCurrentPw(e.target.value)}
                    placeholder="••••••••"
                    className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-amber-500/30 transition-all font-medium text-white"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">새 비밀번호 (8자 이상)</label>
                  <input
                    type="password"
                    value={newPw}
                    onChange={(e) => setNewPw(e.target.value)}
                    placeholder="••••••••"
                    className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-medium text-white"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">새 비밀번호 확인</label>
                  <input
                    type="password"
                    value={confirmPw}
                    onChange={(e) => setConfirmPw(e.target.value)}
                    placeholder="••••••••"
                    className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-medium text-white"
                  />
                </div>
                <button
                  type="button"
                  disabled={saving}
                  onClick={handleChangePassword}
                  className="w-full bg-emerald-500 text-white py-4 rounded-2xl font-bold hover:bg-emerald-600 disabled:opacity-50 transition-all shadow-xl shadow-emerald-500/20 active:scale-95 flex items-center justify-center gap-2"
                >
                  {saving ? <Loader size={20} className="animate-spin" /> : '비밀번호 변경'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsView;
