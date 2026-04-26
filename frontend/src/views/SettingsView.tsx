import React, { useState } from 'react';
import { 
  User, 
  Bell, 
  Shield, 
  Database, 
  Mail, 
  MessageSquare, 
  Save,
  Key,
  Smartphone,
  Globe
} from 'lucide-react';

const SettingsView: React.FC = () => {
  const [activeSection, setActiveSection] = useState<'profile' | 'notifications' | 'security' | 'system'>('profile');

  const sections = [
    { id: 'profile', label: '프로필 설정', icon: User },
    { id: 'notifications', label: '알림 채널', icon: Bell },
    { id: 'security', label: '보안 및 인증', icon: Shield },
    { id: 'system', label: '시스템 환경', icon: Database },
  ] as const;

  return (
    <div className="p-8 space-y-8 animate-in slide-up duration-500">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">시스템 설정</h2>
        <p className="text-slate-400 mt-1 font-medium">마스터 계정 정보 및 전역 시스템 환경을 관리합니다.</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Navigation Sidebar */}
        <div className="w-full lg:w-64 flex flex-row lg:flex-col gap-2 glass p-2 rounded-2xl h-fit">
          {sections.map((section) => {
            const Icon = section.icon;
            return (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`flex-1 lg:flex-none flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${
                  activeSection === section.id 
                    ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20' 
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                }`}
              >
                <Icon size={18} />
                <span className="hidden md:inline">{section.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content Area */}
        <div className="flex-1 space-y-6">
          {activeSection === 'profile' && (
            <div className="glass p-8 rounded-3xl border border-white/5 space-y-8">
              <div className="flex items-center gap-6">
                <div className="w-24 h-24 rounded-3xl glass-morphism border-white/10 flex items-center justify-center font-black text-emerald-400 text-3xl shadow-2xl relative overflow-hidden group">
                   <User size={40} className="opacity-80" />
                   <div className="absolute inset-0 bg-emerald-500/10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer backdrop-blur-sm">
                      <Save size={24} />
                   </div>
                </div>
                <div>
                  <h3 className="text-xl font-bold">마스터 관리자</h3>
                  <p className="text-slate-500 text-sm font-medium">관리자 계정 / Premium Plan</p>
                  <button className="mt-3 text-xs font-bold text-emerald-400 hover:text-emerald-300 transition-colors">프로필 사진 변경</button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">사용자 이름</label>
                  <input type="text" defaultValue="관리자" className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-medium" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">이메일 주소</label>
                  <input type="email" defaultValue="admin@keepy.com" className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-medium text-slate-500 cursor-not-allowed" disabled />
                </div>
              </div>
            </div>
          )}

          {activeSection === 'notifications' && (
            <div className="space-y-6">
              <div className="glass p-8 rounded-3xl border border-white/5">
                <div className="flex items-center gap-3 mb-8">
                  <div className="p-3 rounded-2xl bg-emerald-500/10 text-emerald-400">
                    <Mail size={24} />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold">이메일 알림 설정 (SMTP)</h3>
                    <p className="text-slate-500 text-sm">장애 발생 시 알림을 보낼 메일 서버를 설정합니다.</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">SMTP 서버</label>
                    <input type="text" placeholder="smtp.gmail.com" className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-medium" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">포트</label>
                    <input type="text" placeholder="587" className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-medium" />
                  </div>
                </div>
              </div>

              <div className="glass p-8 rounded-3xl border border-white/5">
                <div className="flex items-center gap-3 mb-8">
                  <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-400">
                    <MessageSquare size={24} />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold">비즈니스 알림톡 (Kakao)</h3>
                    <p className="text-slate-500 text-sm">카카오톡 알림 전송을 위한 API 키를 설정합니다.</p>
                  </div>
                </div>
                
                <div className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">API KEY</label>
                    <div className="flex gap-2">
                      <input type="password" value="************************" className="flex-1 glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-blue-500/30 transition-all font-medium" />
                      <button className="px-6 glass border border-white/10 rounded-2xl font-bold text-sm hover:bg-white/5 transition-all text-slate-300">연결 테스트</button>
                    </div>
                  </div>
                </div>
              </div>
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
                  <p className="text-slate-500 text-sm">주기적인 비밀번호 변경으로 계정을 안전하게 보호하세요.</p>
                </div>
              </div>
              
              <div className="space-y-6 max-w-md">
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">현재 비밀번호</label>
                  <input type="password" placeholder="••••••••" className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-amber-500/30 transition-all font-medium" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest ml-1">새 비밀번호</label>
                  <input type="password" placeholder="••••••••" className="w-full glass border border-white/5 rounded-2xl py-3.5 px-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-medium" />
                </div>
                <button className="w-full bg-emerald-500 text-white py-4 rounded-2xl font-bold hover:bg-emerald-600 transition-all shadow-xl shadow-emerald-500/20 active:scale-95">
                  비밀번호 저장
                </button>
              </div>
            </div>
          )}

          {activeSection === 'system' && (
            <div className="glass p-8 rounded-3xl border border-white/5 space-y-8">
               <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-2xl bg-purple-500/10 text-purple-400">
                      <Globe size={24} />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold">글로벌 시스템 설정</h3>
                      <p className="text-slate-500 text-sm">전체 서비스 운영에 필요한 환경 변수를 설정합니다.</p>
                    </div>
                  </div>
                  <button className="bg-emerald-500/10 text-emerald-400 px-4 py-2 rounded-xl text-xs font-bold hover:bg-emerald-500/20 transition-all">설정 초기화</button>
               </div>

               <div className="space-y-6 pt-4">
                  <div className="flex items-center justify-between p-4 glass rounded-2xl border border-white/5">
                    <div className="flex items-center gap-3">
                      <Smartphone className="text-slate-400" size={20} />
                      <div>
                        <div className="text-sm font-bold">모바일 푸시 알림</div>
                        <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Mobile Push Notification</div>
                      </div>
                    </div>
                    <div className="w-12 h-6 bg-emerald-500 rounded-full relative cursor-pointer">
                      <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-4 glass rounded-2xl border border-white/5">
                    <div className="flex items-center gap-3">
                      <Database className="text-slate-400" size={20} />
                      <div>
                        <div className="text-sm font-bold">자동 백업 주기</div>
                        <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Database Auto Backup</div>
                      </div>
                    </div>
                    <select className="bg-transparent border-none outline-none text-sm font-bold text-emerald-400 cursor-pointer">
                      <option>매일 (00:00)</option>
                      <option>주간 (일요일)</option>
                      <option>매월 (1일)</option>
                    </select>
                  </div>
               </div>
            </div>
          )}

          {/* Global Save Button */}
          <div className="flex justify-end pt-4">
            <button className="flex items-center gap-2 bg-emerald-500 text-white px-10 py-4 rounded-2xl font-black text-lg hover:bg-emerald-600 transition-all shadow-2xl shadow-emerald-500/30 active:scale-95">
              <Save size={20} /> 전체 설정 저장
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsView;
