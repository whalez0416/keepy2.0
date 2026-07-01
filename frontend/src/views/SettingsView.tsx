import React, { useState, useEffect } from 'react';
import {
  User,
  Shield,
  Key,
  LogOut,
  Loader,
  CheckCircle,
  AlertCircle,
  Bell,
} from 'lucide-react';
import { authApi, organizationsApi, type Organization } from '../lib/api';

interface SettingsViewProps {
  onLogout?: () => void;
}

const SettingsView: React.FC<SettingsViewProps> = ({ onLogout }) => {
  const [activeSection, setActiveSection] = useState<'profile' | 'notify' | 'security'>('profile');
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  // 알림 수신 설정 (조직 단위)
  const [org, setOrg] = useState<Organization | null>(null);
  const [notifyEmails, setNotifyEmails] = useState('');
  const [notifyPhones, setNotifyPhones] = useState('');
  const [orgLoading, setOrgLoading] = useState(false);
  const [notifyMsg, setNotifyMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    setOrgLoading(true);
    organizationsApi
      .list()
      .then((res) => {
        if (cancelled) return;
        const first = res.data?.[0] || null;
        setOrg(first);
        setNotifyEmails(first?.notify_emails || '');
        setNotifyPhones(first?.notify_phones || '');
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setOrgLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSaveNotify = async () => {
    if (!org) return;
    setNotifyMsg(null);
    setSaving(true);
    try {
      const res = await organizationsApi.update(org.id, {
        notify_emails: notifyEmails.trim(),
        notify_phones: notifyPhones.trim(),
      });
      setOrg(res.data);
      setNotifyMsg({ type: 'ok', text: '알림 수신 설정이 저장되었습니다.' });
    } catch (err: any) {
      setNotifyMsg({
        type: 'err',
        text: err?.response?.data?.detail || '저장에 실패했습니다.',
      });
    } finally {
      setSaving(false);
    }
  };

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
    { id: 'notify', label: '알림 수신', icon: Bell },
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
                    ? 'bg-gradient-to-b from-[#e9eef2] via-[#b9c4cd] to-[#8b97a1] text-[#0a0c0f] hover:brightness-110 border border-white/40 shadow-[inset_0_1px_0_rgba(255,255,255,0.5),0_8px_24px_rgba(0,0,0,0.5)]'
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
                <div className="w-24 h-24 rounded-3xl glass-morphism border-white/10 flex items-center justify-center font-black text-[#c8d4de] text-3xl shadow-2xl">
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

          {activeSection === 'notify' && (
            <div className="glass p-8 rounded-3xl border border-white/5 space-y-8">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-2xl bg-[#9fb2c2]/10 text-[#c8d4de]">
                  <Bell size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-bold">알림 수신 설정</h3>
                  <p className="text-slate-500 text-sm">
                    홈페이지 장애·연락처/화면 변조·SSL 만료·스팸 탐지 시 알림을 받을 곳을 지정합니다.
                  </p>
                </div>
              </div>

              {notifyMsg && (
                <div
                  className={`flex items-center gap-2 p-4 rounded-2xl text-sm font-bold border max-w-xl ${
                    notifyMsg.type === 'ok'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : 'bg-red-500/10 text-red-400 border-red-500/20'
                  }`}
                >
                  {notifyMsg.type === 'ok' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
                  {notifyMsg.text}
                </div>
              )}

              {orgLoading ? (
                <div className="flex items-center gap-2 text-slate-400">
                  <Loader size={18} className="animate-spin" /> 불러오는 중…
                </div>
              ) : !org ? (
                <p className="text-slate-500 text-sm">연결된 조직이 없습니다. 마스터 관리자에게 문의하세요.</p>
              ) : (
                <div className="space-y-6 max-w-xl">
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">
                      알림 이메일 (쉼표로 여러 명)
                    </label>
                    <input
                      type="text"
                      value={notifyEmails}
                      onChange={(e) => setNotifyEmails(e.target.value)}
                      placeholder="manager@hospital.com, director@hospital.com"
                      className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 transition-all font-medium text-white"
                    />
                    <p className="text-xs text-slate-600 ml-1">
                      비워두면 가입 시 등록한 대표 이메일로 발송됩니다. 받으실 담당자를 따로 지정하려면 입력하세요 (여러 명 가능).
                    </p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">
                      알림 휴대폰 (쉼표로 여러 명)
                    </label>
                    <input
                      type="text"
                      value={notifyPhones}
                      onChange={(e) => setNotifyPhones(e.target.value)}
                      placeholder="010-1234-5678, 010-9876-5432"
                      className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 transition-all font-medium text-white"
                    />
                    <p className="text-xs text-slate-600 ml-1">
                      문자(SMS)/카카오 알림톡 발송은 추후 연동 예정입니다. 지금은 번호만 등록됩니다.
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={saving}
                    onClick={handleSaveNotify}
                    className="bg-gradient-to-b from-[#e9eef2] via-[#b9c4cd] to-[#8b97a1] text-[#0a0c0f] py-4 px-8 rounded-2xl font-bold hover:brightness-110 border border-white/40 disabled:opacity-50 transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.5),0_8px_24px_rgba(0,0,0,0.5)] active:scale-95 flex items-center justify-center gap-2"
                  >
                    {saving ? <Loader size={20} className="animate-spin" /> : '저장'}
                  </button>
                </div>
              )}
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
                    className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 transition-all font-medium text-white"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">새 비밀번호 확인</label>
                  <input
                    type="password"
                    value={confirmPw}
                    onChange={(e) => setConfirmPw(e.target.value)}
                    placeholder="••••••••"
                    className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 transition-all font-medium text-white"
                  />
                </div>
                <button
                  type="button"
                  disabled={saving}
                  onClick={handleChangePassword}
                  className="w-full bg-gradient-to-b from-[#e9eef2] via-[#b9c4cd] to-[#8b97a1] text-[#0a0c0f] py-4 rounded-2xl font-bold hover:brightness-110 border border-white/40 disabled:opacity-50 transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.5),0_8px_24px_rgba(0,0,0,0.5)] active:scale-95 flex items-center justify-center gap-2"
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
