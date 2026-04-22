import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { Site, sitesApi } from '../lib/api';

interface SiteConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  site?: Site | null;
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
  
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (site) {
      setFormData(site);
      setShowAdvanced(!!site.form_url || !!site.name_selector);
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
      setShowAdvanced(false);
    }
  }, [site, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (site?.id) {
        await sitesApi.update(site.id, formData);
      } else {
        await sitesApi.create(formData);
      }
      onSave();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save site configuration');
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#1a1c23] border border-white/10 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/2">
          <div>
            <h2 className="text-xl font-bold">{site ? 'Edit Hospital' : 'Add New Hospital'}</h2>
            <p className="text-slate-400 text-xs">Configure monitoring parameters and selectors.</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-all">
            <X size={20} className="text-slate-500" />
          </button>
        </div>

        {/* Form Content */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-xl flex items-center gap-3 text-red-400 text-sm">
              <AlertCircle size={18} />
              {error}
            </div>
          )}

          {/* Basic Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Hospital Name *</label>
              <input 
                required
                name="site_name"
                value={formData.site_name}
                onChange={handleChange}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all"
                placeholder="e.g. Min Hospital"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Group / Branch</label>
              <input 
                name="hospital_name"
                value={formData.hospital_name}
                onChange={handleChange}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all"
                placeholder="e.g. Thyroid Center"
              />
            </div>
            <div className="md:col-span-2 space-y-2">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Homepage URL *</label>
              <input 
                required
                name="homepage_url"
                value={formData.homepage_url}
                onChange={handleChange}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all"
                placeholder="https://..."
              />
            </div>
          </div>

          {/* Monitoring Intervals */}
          <div className="grid grid-cols-2 gap-4 p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-xl">
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-emerald-400 uppercase">HP Check (Min)</label>
              <input 
                type="number"
                name="check_interval_minutes"
                value={formData.check_interval_minutes}
                onChange={handleChange}
                className="w-full bg-black/20 border border-white/5 rounded-lg px-3 py-2 text-sm outline-none"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-emerald-400 uppercase">Form Check (Min)</label>
              <input 
                type="number"
                name="form_check_interval_minutes"
                value={formData.form_check_interval_minutes}
                onChange={handleChange}
                className="w-full bg-black/20 border border-white/5 rounded-lg px-3 py-2 text-sm outline-none"
              />
            </div>
          </div>

          {/* Advanced / Dynamic Monitoring Toggle */}
          <button 
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center justify-between w-full p-4 glass border-white/10 rounded-xl hover:bg-white/5 transition-all"
          >
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${showAdvanced ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700/50 text-slate-500'}`}>
                <Info size={18} />
              </div>
              <div className="text-left">
                <div className="font-bold text-sm">Dynamic Page Monitoring</div>
                <div className="text-[10px] text-slate-500">Configure consultation form & action selectors</div>
              </div>
            </div>
            {showAdvanced ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>

          {showAdvanced && (
            <div className="space-y-6 pt-2 animate-in slide-in-from-top-4 duration-300">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Form Page URL</label>
                <input 
                  name="form_url"
                  value={formData.form_url}
                  onChange={handleChange}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all font-mono text-xs"
                  placeholder="https://.../online_consult"
                />
              </div>

              <div className="space-y-4">
                <h4 className="text-[10px] font-bold text-slate-500 uppercase border-b border-white/5 pb-2">CSS Selectors</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { label: 'Name Input', name: 'name_selector' },
                    { label: 'Phone Input', name: 'phone_selector' },
                    { label: 'Subject Input', name: 'subject_selector' },
                    { label: 'Submit Button', name: 'submit_selector' },
                    { label: 'Agreement Check', name: 'agreement_selector' },
                    { label: 'Message Textarea', name: 'message_selector' },
                  ].map(field => (
                    <div key={field.name} className="space-y-1">
                      <label className="text-[10px] text-slate-500">{field.label}</label>
                      <input 
                        name={field.name}
                        value={(formData as any)[field.name] || ''}
                        onChange={handleChange}
                        className="w-full bg-white/2 border border-white/5 rounded-lg px-3 py-2 text-xs outline-none focus:border-emerald-500/50 font-mono"
                        placeholder="#id or .class"
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Extra Actions (JSON)</label>
                <textarea 
                  name="extra_steps_json"
                  value={formData.extra_steps_json}
                  onChange={handleChange}
                  rows={3}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all font-mono text-xs"
                  placeholder='[{"type": "click", "selector": "#btn-reserve"}]'
                />
              </div>
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="p-6 border-t border-white/5 flex gap-3 bg-white/2">
          <button 
            type="button"
            onClick={onClose}
            className="flex-1 py-3 px-4 glass rounded-xl font-bold text-slate-400 hover:bg-white/5 transition-all text-sm"
          >
            Cancel
          </button>
          <button 
            onClick={handleSubmit}
            disabled={loading}
            className="flex-[2] py-3 px-4 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-emerald-500/20 text-sm"
          >
            {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Save size={18} />}
            {site ? 'Update Monitoring' : 'Start Monitoring'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SiteConfigModal;
