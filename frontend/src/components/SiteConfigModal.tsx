import React, { useState, useEffect } from 'react';
import { 
  X, 
  Save, 
  AlertCircle, 
  Info, 
  ChevronDown, 
  ChevronUp, 
  Plus, 
  Trash2, 
  MousePointer2, 
  Keyboard, 
  Timer,
  Layout,
  FileText,
  Activity,
  Shield,
  Globe,
  Brain
} from 'lucide-react';
import { Site, FormConfig, SpamConfig, sitesApi, Organization, organizationsApi } from '../lib/api';
import AutoDiscoveryModal from './AutoDiscoveryModal';

interface SiteConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  site?: Site | null;
}

interface ActionStep {
  type: 'click' | 'type' | 'wait';
  selector: string;
  value?: string;
  seconds?: number;
}

const SiteConfigModal: React.FC<SiteConfigModalProps> = ({ isOpen, onClose, onSave, site }) => {
  const [formData, setFormData] = useState({
    site_name: '',
    hospital_name: '',
    homepage_url: '',
    check_interval_minutes: 5,
    extra_steps_json: '',
    org_id: 0 as number | undefined,
    expected_phone: '',
    expected_kakao_url: '',
    admin_path: '/admin',
    emergency_mode_active: false,
    emergency_message: ''
  });

  const [forms, setForms] = useState<Partial<FormConfig>[]>([]);
  const [spams, setSpams] = useState<Partial<SpamConfig>[]>([]);
  const [activeFormIndex, setActiveFormIndex] = useState<number | null>(null);
  const [activeSpamIndex, setActiveSpamIndex] = useState<number | null>(null);
  const [extraSteps, setExtraSteps] = useState<ActionStep[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [isDiscoveryOpen, setIsDiscoveryOpen] = useState(false);

  const user = JSON.parse(localStorage.getItem('keepy_user') || '{}');
  const isSuperAdmin = user.role === 'superadmin';

  useEffect(() => {
    if (isSuperAdmin) {
      organizationsApi.list().then(res => setOrganizations(res.data));
    }
  }, [isSuperAdmin]);

  useEffect(() => {
    if (site) {
      setFormData({
        site_name: site.site_name,
        hospital_name: site.hospital_name || '',
        homepage_url: site.homepage_url,
        check_interval_minutes: site.check_interval_minutes,
        extra_steps_json: site.extra_steps_json || '',
        org_id: site.org_id,
        expected_phone: site.expected_phone || '',
        expected_kakao_url: site.expected_kakao_url || '',
        admin_path: site.admin_path || '/admin',
        emergency_mode_active: site.emergency_mode_active || false,
        emergency_message: site.emergency_message || ''
      });
      setForms(site.form_configs || []);
      setSpams(site.spam_configs || []);
      if (site.extra_steps_json) {
        try {
          setExtraSteps(JSON.stringify(site.extra_steps_json).startsWith('[') ? JSON.parse(site.extra_steps_json) : []);
        } catch (e) {
          setExtraSteps([]);
        }
      }
    } else {
      setFormData({
        site_name: '',
        hospital_name: '',
        homepage_url: '',
        check_interval_minutes: 5,
        extra_steps_json: '',
        org_id: undefined,
        expected_phone: '',
        expected_kakao_url: '',
        admin_path: '/admin',
        emergency_mode_active: false,
        emergency_message: ''
      });
      setForms([]);
      setSpams([]);
      setExtraSteps([]);
      setActiveFormIndex(null);
      setActiveSpamIndex(null);
    }
  }, [site, isOpen]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    let finalValue: any = value;
    
    if (type === 'number' || name === 'org_id') {
      finalValue = parseInt(value);
    } else if (type === 'checkbox') {
      finalValue = (e.target as HTMLInputElement).checked;
    }
    
    setFormData(prev => ({
      ...prev,
      [name]: finalValue
    }));
  };

  const handleFormChange = (index: number, field: string, value: any) => {
    const updatedForms = [...forms];
    updatedForms[index] = { ...updatedForms[index], [field]: value };
    setForms(updatedForms);
  };

  const handleSpamChange = (index: number, field: string, value: any) => {
    const updatedSpams = [...spams];
    updatedSpams[index] = { ...updatedSpams[index], [field]: value };
    setSpams(updatedSpams);
  };

  const addForm = () => {
    setForms([...forms, { 
      name: `상담폼 ${forms.length + 1}`, 
      form_url: '', 
      check_interval_minutes: 60,
      is_active: true 
    }]);
    setActiveFormIndex(forms.length);
  };

  const addSpam = () => {
    setSpams([...spams, { 
      board_url: '', 
      is_active: true 
    }]);
    setActiveSpamIndex(spams.length);
  };

  const removeForm = (index: number) => {
    setForms(forms.filter((_, i) => i !== index));
    if (activeFormIndex === index) setActiveFormIndex(null);
  };

  const handleApplyDiscovery = (discoveredForm: any, homepageUrl: string) => {
    setForms(prev => [
      ...prev,
      {
        name: discoveredForm.link_text || '자동 탐지 상담폼',
        form_url: discoveredForm.url,
        name_selector: discoveredForm.selectors.name_selector || '',
        phone_selector: discoveredForm.selectors.phone_selector || '',
        subject_selector: discoveredForm.selectors.subject_selector || '',
        message_selector: discoveredForm.selectors.message_selector || '',
        agreement_selector: discoveredForm.selectors.agreement_selector || '',
        submit_selector: discoveredForm.selectors.submit_selector || '',
        check_interval_minutes: 60,
        is_active: true
      }
    ]);
    if (!formData.homepage_url) {
      setFormData(prev => ({
        ...prev,
        homepage_url: homepageUrl
      }));
    }
    setActiveFormIndex(forms.length);
  };

  const removeSpam = (index: number) => {
    setSpams(spams.filter((_, i) => i !== index));
    if (activeSpamIndex === index) setActiveSpamIndex(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        ...formData,
        extra_steps_json: extraSteps.length > 0 ? JSON.stringify(extraSteps) : null,
        form_configs: forms,
        spam_configs: spams
      };

      if (site) {
        await sitesApi.update(site.id, payload);
      } else {
        await sitesApi.create(payload);
      }
      onSave();
      onClose();
    } catch (err: any) {
      console.error('Save error:', err);
      const detail = err.response?.data?.detail;
      const errorMessage = typeof detail === 'string' 
        ? detail 
        : Array.isArray(detail) 
          ? detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', ')
          : '저장에 실패했습니다. 데이터 형식을 확인해주세요.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 md:p-10 animate-in fade-in duration-300">
      <div className="absolute inset-0 bg-[#080a0f]/80 backdrop-blur-md" onClick={onClose} />
      
      <div className="glass w-full max-w-6xl max-h-[90vh] overflow-hidden rounded-[40px] border border-white/5 shadow-2xl flex flex-col relative z-10 animate-in zoom-in duration-300">
        {/* Header */}
        <div className="px-8 py-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-[#9fb2c2]/10 border border-[#9fb2c2]/20 flex items-center justify-center">
              <Plus className="text-[#c8d4de]" size={24} />
            </div>
            <div>
              <h2 className="text-2xl font-black tracking-tight text-white">{site ? '병원 설정 수정' : '새 병원 등록'}</h2>
              <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mt-0.5">Full Site & Spam Monitoring</p>
            </div>
          </div>
          <button onClick={onClose} className="p-3 hover:bg-white/5 rounded-2xl text-slate-500 transition-all">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
            
            {/* Left: Basic Info & Forms */}
            <div className="space-y-10">
              <section className="space-y-6">
                <div className="flex items-center gap-3">
                   <div className="w-1.5 h-4 bg-[#9fb2c2] rounded-full" />
                   <h3 className="text-sm font-black text-slate-300 uppercase tracking-wider">기본 정보</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">병원 이름 *</label>
                    <input 
                      required
                      name="site_name"
                      value={formData.site_name}
                      onChange={handleChange}
                      className="w-full glass border border-white/5 rounded-2xl px-5 py-4 outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 transition-all font-bold placeholder:text-slate-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">
                      {isSuperAdmin ? '소속 조직 (관리자 권한)' : '병원 그룹'}
                    </label>
                    {isSuperAdmin ? (
                      <select 
                        name="org_id"
                        value={formData.org_id || ''}
                        onChange={handleChange}
                        className="w-full glass border border-white/5 rounded-2xl px-5 py-4 outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 transition-all font-bold"
                      >
                        <option value="" disabled>조직 선택</option>
                        {organizations.map(org => (
                          <option key={org.id} value={org.id}>{org.name}</option>
                        ))}
                      </select>
                    ) : (
                      <input 
                        name="hospital_name"
                        value={formData.hospital_name}
                        onChange={handleChange}
                        className="w-full glass border border-white/5 rounded-2xl px-5 py-4 outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 transition-all font-bold placeholder:text-slate-700"
                        disabled
                      />
                    )}
                  </div>
                  <div className="md:col-span-2 space-y-2">
                    <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">홈페이지 URL *</label>
                    <input 
                      required
                      name="homepage_url"
                      value={formData.homepage_url}
                      onChange={handleChange}
                      className="w-full glass border border-white/5 rounded-2xl px-5 py-4 outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 transition-all font-bold text-[#c8d4de]"
                    />
                  </div>
                </div>
              </section>

              <section className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-1.5 h-4 bg-[#9fb2c2] rounded-full" />
                    <h3 className="text-sm font-black text-slate-300 uppercase tracking-wider">상담폼 모니터링 ({forms.length})</h3>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      type="button" 
                      onClick={() => setIsDiscoveryOpen(true)}
                      className="px-3 py-1.5 bg-violet-500/10 text-violet-400 rounded-xl border border-violet-500/20 text-xs font-black hover:bg-violet-500/20 transition-all flex items-center gap-1"
                    >
                      <Brain size={14} /> AI 자동 탐색 🌟
                    </button>
                    <button type="button" onClick={addForm} className="px-3 py-1.5 bg-[#9fb2c2]/10 text-[#c8d4de] rounded-xl border border-[#9fb2c2]/20 text-xs font-black hover:bg-[#9fb2c2]/20 transition-all flex items-center gap-1">
                      <Plus size={14} /> 추가
                    </button>
                  </div>
                </div>

                <div className="space-y-3">
                  {forms.map((form, idx) => (
                    <div key={idx} className={`border rounded-3xl transition-all ${activeFormIndex === idx ? 'bg-[#9fb2c2]/5 border-[#9fb2c2]/20 p-6' : 'hover:bg-white/[0.02] border-white/5 p-4'}`}>
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4 flex-1 min-w-0 cursor-pointer" onClick={() => setActiveFormIndex(activeFormIndex === idx ? null : idx)}>
                          <FileText size={20} className={activeFormIndex === idx ? 'text-[#c8d4de]' : 'text-slate-500'} />
                          <div className="truncate">
                            <div className="text-sm font-bold text-slate-200">{form.name || `상담폼 ${idx + 1}`}</div>
                            <div className="text-[10px] text-slate-500 truncate">{form.form_url || 'URL 미입력'}</div>
                          </div>
                        </div>
                        <button type="button" onClick={() => removeForm(idx)} className="p-2 text-slate-600 hover:text-red-400 transition-colors"><Trash2 size={16} /></button>
                      </div>
                      {activeFormIndex === idx && (
                        <div className="mt-6 pt-6 border-t border-white/5 space-y-4 animate-in slide-in-from-top-2">
                          <input placeholder="폼 이름" value={form.name} onChange={e => handleFormChange(idx, 'name', e.target.value)} className="w-full glass-compact border border-white/5 rounded-xl px-4 py-2.5 text-sm font-bold" />
                          <input placeholder="폼 URL" value={form.form_url} onChange={e => handleFormChange(idx, 'form_url', e.target.value)} className="w-full glass-compact border border-white/5 rounded-xl px-4 py-2.5 text-sm text-[#c8d4de] font-bold" />
                          <div className="grid grid-cols-2 gap-3">
                            <input placeholder="이름 셀렉터" value={form.name_selector} onChange={e => handleFormChange(idx, 'name_selector', e.target.value)} className="glass-compact text-xs p-3 rounded-xl border border-white/5" />
                            <input placeholder="연락처 셀렉터" value={form.phone_selector} onChange={e => handleFormChange(idx, 'phone_selector', e.target.value)} className="glass-compact text-xs p-3 rounded-xl border border-white/5" />
                            <input placeholder="제목 셀렉터" value={form.subject_selector} onChange={e => handleFormChange(idx, 'subject_selector', e.target.value)} className="glass-compact text-xs p-3 rounded-xl border border-white/5" />
                            <input placeholder="메시지 셀렉터" value={form.message_selector} onChange={e => handleFormChange(idx, 'message_selector', e.target.value)} className="glass-compact text-xs p-3 rounded-xl border border-white/5" />
                            <input placeholder="동의 체크박스 셀렉터" value={form.agreement_selector} onChange={e => handleFormChange(idx, 'agreement_selector', e.target.value)} className="glass-compact text-xs p-3 rounded-xl border border-white/5" />
                            <input placeholder="제출 버튼 셀렉터" value={form.submit_selector} onChange={e => handleFormChange(idx, 'submit_selector', e.target.value)} className="glass-compact text-xs p-3 rounded-xl border border-white/5" />
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            </div>

            {/* Right: Security & Spam & Advanced */}
            <div className="space-y-10">
              {/* NEW: Premium Security Section */}
              <section className="space-y-6">
                <div className="flex items-center gap-3">
                  <div className="w-1.5 h-4 bg-amber-500 rounded-full" />
                  <h3 className="text-sm font-black text-slate-300 uppercase tracking-wider">보안 및 가용성 (Premium)</h3>
                </div>

                <div className="glass-compact border border-amber-500/10 rounded-[32px] p-8 space-y-6 bg-amber-500/[0.02]">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">정상 전화번호</label>
                      <input 
                        name="expected_phone"
                        value={formData.expected_phone}
                        onChange={handleChange}
                        className="w-full glass-compact border border-white/5 rounded-xl px-4 py-3 text-sm font-bold text-amber-200"
                        placeholder="02-1234-5678"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">정상 카톡 채널 URL</label>
                      <input 
                        name="expected_kakao_url"
                        value={formData.expected_kakao_url}
                        onChange={handleChange}
                        className="w-full glass-compact border border-white/5 rounded-xl px-4 py-3 text-sm font-bold text-amber-200"
                        placeholder="pf.kakao.com/_xxxx"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">관리자 페이지 경로 (IP 보안 감시)</label>
                    <input 
                      name="admin_path"
                      value={formData.admin_path}
                      onChange={handleChange}
                      className="w-full glass-compact border border-white/5 rounded-xl px-4 py-3 text-sm font-bold text-slate-300"
                      placeholder="/admin"
                    />
                  </div>

                  <div className="pt-4 border-t border-white/5 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Activity size={16} className="text-amber-400" />
                        <span className="text-sm font-bold text-slate-200">긴급 안내 배너 (Maintenance)</span>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input 
                          type="checkbox" 
                          name="emergency_mode_active"
                          checked={formData.emergency_mode_active}
                          onChange={handleChange}
                          className="sr-only peer" 
                        />
                        <div className="w-11 h-6 bg-white/10 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-400 after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500 peer-checked:after:bg-white"></div>
                      </label>
                    </div>
                    {formData.emergency_mode_active && (
                      <textarea 
                        name="emergency_message"
                        value={formData.emergency_message}
                        onChange={handleChange}
                        rows={2}
                        className="w-full glass-compact border border-amber-500/20 rounded-xl px-4 py-3 text-sm font-medium text-amber-100 animate-in slide-in-from-top-2"
                        placeholder="현재 서버 점검 중입니다. 급한 용무는 02-1234-5678로 연락 주세요."
                      />
                    )}
                  </div>
                </div>
              </section>

              <section className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-1.5 h-4 bg-violet-500 rounded-full" />
                    <h3 className="text-sm font-black text-slate-300 uppercase tracking-wider">AI 스팸 감시 게시판 ({spams.length})</h3>
                  </div>
                  <button type="button" onClick={addSpam} className="px-3 py-1.5 bg-violet-500/10 text-violet-400 rounded-xl border border-violet-500/20 text-xs font-black hover:bg-violet-500/20 transition-all flex items-center gap-1">
                    <Plus size={14} /> 추가
                  </button>
                </div>

                <div className="space-y-3">
                  {spams.map((spam, idx) => (
                    <div key={idx} className={`border rounded-3xl transition-all ${activeSpamIndex === idx ? 'bg-violet-500/5 border-violet-500/20 p-6' : 'hover:bg-white/[0.02] border-white/5 p-4'}`}>
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4 flex-1 min-w-0 cursor-pointer" onClick={() => setActiveSpamIndex(activeSpamIndex === idx ? null : idx)}>
                          <Shield size={20} className={activeSpamIndex === idx ? 'text-violet-400' : 'text-slate-500'} />
                          <div className="truncate">
                            <div className="text-sm font-bold text-slate-200">{spam.board_url ? '감시 게시판' : `게시판 ${idx + 1}`}</div>
                            <div className="text-[10px] text-slate-500 truncate">{spam.board_url || '목록 URL 미입력'}</div>
                          </div>
                        </div>
                        <button type="button" onClick={() => removeSpam(idx)} className="p-2 text-slate-600 hover:text-red-400 transition-colors"><Trash2 size={16} /></button>
                      </div>
                      {activeSpamIndex === idx && (
                        <div className="mt-6 pt-6 border-t border-white/5 space-y-4 animate-in slide-in-from-top-2">
                           <div className="space-y-1">
                             <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">게시판 목록 URL *</label>
                             <input 
                               value={spam.board_url}
                               onChange={(e) => handleSpamChange(idx, 'board_url', e.target.value)}
                               className="w-full glass-compact border border-white/5 rounded-xl px-4 py-2.5 text-sm text-violet-400 font-bold"
                               placeholder="https://.../board.php?bo_table=free"
                             />
                           </div>
                           <div className="space-y-1">
                             <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">추가 키워드 (선택)</label>
                             <input 
                               value={spam.keywords}
                               onChange={(e) => handleSpamChange(idx, 'keywords', e.target.value)}
                               className="w-full glass-compact border border-white/5 rounded-xl px-4 py-2.5 text-sm text-slate-300"
                               placeholder="비아그라, 카지노, ..."
                             />
                           </div>
                           <div className="bg-violet-500/5 p-4 rounded-2xl border border-violet-500/10 flex items-start gap-3">
                              <Brain size={16} className="text-violet-400 mt-1 flex-shrink-0" />
                              <p className="text-[11px] text-slate-400 leading-relaxed font-medium">
                                목록 URL을 입력하면 <strong>GPT AI</strong>가 게시물 내용을 분석하여 스팸 여부를 자동 판별합니다.
                              </p>
                           </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </section>

              <section className="space-y-4 pt-4">
                <button 
                  type="button"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-2 text-slate-500 hover:text-white transition-all font-bold text-sm"
                >
                  {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  고급 설정 (공통 액션 시퀀스)
                </button>
                {showAdvanced && (
                  <textarea 
                    name="extra_steps_json"
                    value={formData.extra_steps_json}
                    onChange={handleChange}
                    rows={4}
                    className="w-full bg-white/5 border border-white/5 rounded-2xl px-5 py-4 outline-none focus:ring-1 focus:ring-blue-500/30 transition-all font-mono text-xs text-blue-300"
                    placeholder='[{"type": "click", "selector": "#close-popup"}]'
                  />
                )}
              </section>
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="px-8 py-6 border-t border-white/5 flex items-center justify-between bg-white/[0.02]">
          <div className="text-red-400 text-sm font-bold">{error}</div>
          <div className="flex gap-4">
            <button type="button" onClick={onClose} className="px-8 py-3 rounded-2xl font-bold text-slate-400 hover:text-white transition-all">취소</button>
            <button onClick={handleSubmit} disabled={loading} className="bg-gradient-to-b from-[#e9eef2] via-[#b9c4cd] to-[#8b97a1] text-[#0a0c0f] px-10 py-3 rounded-2xl font-black flex items-center gap-2 hover:brightness-110 border border-white/40 transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.5),0_8px_24px_rgba(0,0,0,0.5)] active:scale-95 disabled:opacity-50">
              {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Save size={20} />}
              저장하기
            </button>
          </div>
        </div>
      </div>
      <AutoDiscoveryModal 
        isOpen={isDiscoveryOpen}
        onClose={() => setIsDiscoveryOpen(false)}
        onApply={handleApplyDiscovery}
      />
    </div>
  );
};

export default SiteConfigModal;
