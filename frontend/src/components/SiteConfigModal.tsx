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
  Layout
} from 'lucide-react';
import { Site, sitesApi } from '../lib/api';

interface SiteConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  site?: Site | null;
}

interface ActionStep {
  type: 'click' | 'type' | 'wait';
  selector?: string;
  value?: string;
}

const SiteConfigModal: React.FC<SiteConfigModalProps> = ({ isOpen, onClose, onSave, site }) => {
  const [formData, setFormData] = useState<Partial<Site>>({
    site_name: '',
    hospital_name: '',
    homepage_url: '',
    form_url: '',
    check_interval_minutes: 5,
    form_check_interval_minutes: 60,
    is_active: true,
  });
  
  const [extraSteps, setExtraSteps] = useState<ActionStep[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (site) {
      setFormData(site);
      setShowAdvanced(!!site.form_url || !!site.name_selector);
      try {
        if (site.extra_steps_json) {
          setExtraSteps(JSON.parse(site.extra_steps_json));
        } else {
          setExtraSteps([]);
        }
      } catch (e) {
        setExtraSteps([]);
      }
    } else {
      setFormData({
        site_name: '',
        hospital_name: '',
        homepage_url: '',
        form_url: '',
        check_interval_minutes: 5,
        form_check_interval_minutes: 60,
        is_active: true,
      });
      setExtraSteps([]);
      setShowAdvanced(false);
    }
  }, [site, isOpen]);

  const addStep = () => {
    setExtraSteps([...extraSteps, { type: 'click', selector: '' }]);
  };

  const removeStep = (index: number) => {
    setExtraSteps(extraSteps.filter((_, i) => i !== index));
  };

  const updateStep = (index: number, updates: Partial<ActionStep>) => {
    const newSteps = [...extraSteps];
    newSteps[index] = { ...newSteps[index], ...updates };
    setExtraSteps(newSteps);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const finalData = {
      ...formData,
      extra_steps_json: extraSteps.length > 0 ? JSON.stringify(extraSteps) : null
    };

    try {
      if (site?.id) {
        await sitesApi.update(site.id, finalData);
      } else {
        await sitesApi.create(finalData);
      }
      onSave();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || '설정 저장에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value) : value
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-[#080a0f]/80 backdrop-blur-xl animate-in fade-in duration-300">
      <div className="bg-[#0c0e14] border border-white/5 w-full max-w-3xl rounded-[32px] shadow-2xl overflow-hidden flex flex-col max-h-[90vh] relative">
        {/* Background Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/2 h-1 bg-gradient-to-r from-transparent via-emerald-500/50 to-transparent blur-md" />
        
        {/* Header */}
        <div className="p-8 border-b border-white/[0.03] flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-black tracking-tight text-white">{site ? '병원 정보 수정' : '신규 병원 등록'}</h2>
            <p className="text-slate-500 text-xs font-bold mt-1 uppercase tracking-widest">Monitoring Configuration Center</p>
          </div>
          <button onClick={onClose} className="p-3 glass rounded-2xl hover:bg-white/5 transition-all group">
            <X size={20} className="text-slate-500 group-hover:text-white transition-colors" />
          </button>
        </div>

        {/* Form Content */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-8 space-y-8 scrollbar-hide">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-2xl flex items-center gap-3 text-red-400 text-sm font-bold animate-in shake duration-300">
              <AlertCircle size={20} />
              {error}
            </div>
          )}

          {/* Basic Section */}
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-2">
               <Layout size={18} className="text-emerald-400" />
               <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">기본 정보</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">병원명 *</label>
                <input 
                  required
                  name="site_name"
                  value={formData.site_name}
                  onChange={handleChange}
                  className="w-full glass border border-white/5 rounded-2xl px-5 py-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-bold placeholder:text-slate-700"
                  placeholder="예: 민병원"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">그룹 / 지점</label>
                <input 
                  name="hospital_name"
                  value={formData.hospital_name}
                  onChange={handleChange}
                  className="w-full glass border border-white/5 rounded-2xl px-5 py-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-bold placeholder:text-slate-700"
                  placeholder="예: 갑상선 센터"
                />
              </div>
              <div className="md:col-span-2 space-y-2">
                <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">홈페이지 URL *</label>
                <input 
                  required
                  name="homepage_url"
                  value={formData.homepage_url}
                  onChange={handleChange}
                  className="w-full glass border border-white/5 rounded-2xl px-5 py-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-bold placeholder:text-slate-700 text-emerald-400"
                  placeholder="https://..."
                />
              </div>
            </div>
          </div>

          {/* Monitoring Intervals */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 bg-emerald-500/[0.03] border border-emerald-500/10 rounded-[24px]">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-black text-emerald-500/70 uppercase tracking-widest">홈페이지 체크 주기</label>
                <span className="text-[10px] font-bold text-slate-500">{formData.check_interval_minutes}분 마다</span>
              </div>
              <input 
                type="range"
                min="1"
                max="60"
                name="check_interval_minutes"
                value={formData.check_interval_minutes}
                onChange={handleChange}
                className="w-full accent-emerald-500"
              />
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-black text-emerald-500/70 uppercase tracking-widest">상담폼 체크 주기</label>
                <span className="text-[10px] font-bold text-slate-500">{formData.form_check_interval_minutes}분 마다</span>
              </div>
              <input 
                type="range"
                min="5"
                max="1440"
                step="5"
                name="form_check_interval_minutes"
                value={formData.form_check_interval_minutes}
                onChange={handleChange}
                className="w-full accent-emerald-500"
              />
            </div>
          </div>

          {/* Advanced Section Toggle */}
          <button 
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center justify-between w-full p-6 glass border-white/[0.03] rounded-3xl hover:bg-white/[0.02] transition-all group"
          >
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all ${showAdvanced ? 'bg-emerald-500/20 text-emerald-400 shadow-lg shadow-emerald-500/20' : 'bg-white/5 text-slate-500'}`}>
                <MousePointer2 size={24} />
              </div>
              <div className="text-left">
                <div className="font-black text-slate-200">정밀 상담폼 모니터링</div>
                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-0.5">Consultation Form Actions</div>
              </div>
            </div>
            {showAdvanced ? <ChevronUp size={20} className="text-emerald-400" /> : <ChevronDown size={20} className="text-slate-600" />}
          </button>

          {showAdvanced && (
            <div className="space-y-8 pt-2 animate-in slide-in-from-top-4 duration-500 pb-4">
              <div className="space-y-3">
                <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">상담폼 페이지 URL</label>
                <input 
                  name="form_url"
                  value={formData.form_url}
                  onChange={handleChange}
                  className="w-full glass border border-white/5 rounded-2xl px-5 py-4 outline-none focus:ring-2 focus:ring-emerald-500/30 transition-all font-mono text-sm text-blue-400"
                  placeholder="https://.../reserve"
                />
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                   <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">폼 필드 선택자 (CSS Selectors)</span>
                   <Info size={14} className="text-slate-700" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { label: '이름 입력칸', name: 'name_selector', placeholder: '#user_name' },
                    { label: '연락처 입력칸', name: 'phone_selector', placeholder: '#user_hp' },
                    { label: '동의 체크박스', name: 'agreement_selector', placeholder: '.agree-check' },
                    { label: '전송 버튼', name: 'submit_selector', placeholder: '#btn-submit' },
                  ].map(field => (
                    <div key={field.name} className="space-y-1.5 p-4 glass rounded-2xl border border-white/[0.02]">
                      <label className="text-[10px] font-black text-slate-500 uppercase">{field.label}</label>
                      <input 
                        name={field.name}
                        value={(formData as any)[field.name] || ''}
                        onChange={handleChange}
                        className="w-full bg-transparent border-none outline-none text-xs font-mono text-emerald-400 placeholder:text-slate-700"
                        placeholder={field.placeholder}
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Builder */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                   <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">추가 액션 시퀀스 (Action Builder)</span>
                   <button 
                    type="button"
                    onClick={addStep}
                    className="flex items-center gap-1.5 text-emerald-400 text-[10px] font-black hover:text-emerald-300 transition-colors bg-emerald-500/10 px-3 py-1.5 rounded-lg"
                   >
                     <Plus size={14} /> 액션 추가
                   </button>
                </div>
                
                <div className="space-y-3">
                  {extraSteps.length === 0 ? (
                    <div className="p-8 glass rounded-2xl border border-dashed border-white/5 text-center text-slate-600 text-xs font-bold">
                      설정된 추가 액션이 없습니다.
                    </div>
                  ) : (
                    extraSteps.map((step, index) => (
                      <div key={index} className="flex items-center gap-3 p-4 glass rounded-2xl border border-white/5 animate-in slide-in-from-right-4 duration-300">
                        <div className="w-8 h-8 rounded-xl bg-white/5 flex items-center justify-center font-black text-[10px] text-slate-500">{index + 1}</div>
                        
                        <select 
                          value={step.type}
                          onChange={(e) => updateStep(index, { type: e.target.value as any })}
                          className="bg-white/5 border-none outline-none rounded-xl px-3 py-2 text-xs font-bold text-slate-300"
                        >
                          <option value="click">클릭</option>
                          <option value="type">입력</option>
                          <option value="wait">대기</option>
                        </select>

                        <div className="flex-1 flex gap-2">
                          {step.type !== 'wait' && (
                            <input 
                              placeholder="선택자 (#id, .class)"
                              value={step.selector}
                              onChange={(e) => updateStep(index, { selector: e.target.value })}
                              className="flex-1 bg-white/2 border border-white/5 rounded-xl px-4 py-2 text-xs font-mono text-emerald-400 outline-none focus:border-emerald-500/50"
                            />
                          )}
                          {step.type === 'type' && (
                            <input 
                              placeholder="입력값"
                              value={step.value}
                              onChange={(e) => updateStep(index, { value: e.target.value })}
                              className="flex-1 bg-white/2 border border-white/5 rounded-xl px-4 py-2 text-xs text-slate-300 outline-none focus:border-emerald-500/50"
                            />
                          )}
                          {step.type === 'wait' && (
                            <input 
                              type="number"
                              placeholder="밀리초 (ms)"
                              value={step.value}
                              onChange={(e) => updateStep(index, { value: e.target.value })}
                              className="w-32 bg-white/2 border border-white/5 rounded-xl px-4 py-2 text-xs font-mono text-amber-400 outline-none focus:border-emerald-500/50"
                            />
                          )}
                        </div>

                        <button 
                          onClick={() => removeStep(index)}
                          className="p-2 text-slate-600 hover:text-red-400 transition-colors"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="p-8 border-t border-white/[0.03] flex gap-4 bg-[#080a0f]/50">
          <button 
            type="button"
            onClick={onClose}
            className="flex-1 py-4 px-6 glass rounded-2xl font-black text-slate-500 hover:text-slate-200 transition-all text-sm uppercase tracking-widest"
          >
            취소
          </button>
          <button 
            onClick={handleSubmit}
            disabled={loading}
            className="flex-[2] py-4 px-6 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white rounded-2xl font-black flex items-center justify-center gap-3 transition-all shadow-2xl shadow-emerald-500/30 text-sm uppercase tracking-widest active:scale-95"
          >
            {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Save size={20} />}
            {site ? '설정 업데이트' : '모니터링 시작'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SiteConfigModal;
