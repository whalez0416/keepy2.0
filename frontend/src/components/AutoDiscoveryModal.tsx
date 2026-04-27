import React, { useState } from 'react';
import {
  Search, Globe, CheckCircle, XCircle, AlertTriangle,
  Loader, ChevronRight, Zap, Tag, Eye, ArrowRight,
  Sparkles, Target
} from 'lucide-react';
import { discoveryApi, DiscoveredForm, DiscoveryResult } from '../lib/api';

interface AutoDiscoveryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApply: (form: DiscoveredForm, homepage_url: string) => void;
}

const ConfidenceBar: React.FC<{ value: number }> = ({ value }) => {
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? 'bg-emerald-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-[11px] font-bold ${pct >= 70 ? 'text-emerald-400' : pct >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
        {pct}%
      </span>
    </div>
  );
};

const SelectorPill: React.FC<{ label: string; value?: string }> = ({ label, value }) => (
  <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-bold border ${
    value
      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
      : 'bg-white/5 text-slate-600 border-white/5'
  }`}>
    {value ? <CheckCircle size={10} /> : <XCircle size={10} />}
    {label}
  </div>
);

const AutoDiscoveryModal: React.FC<AutoDiscoveryModalProps> = ({ isOpen, onClose, onApply }) => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DiscoveryResult | null>(null);
  const [selectedForm, setSelectedForm] = useState<DiscoveredForm | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDiscover = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);
    setSelectedForm(null);

    try {
      const res = await discoveryApi.discover(url.trim());
      setResult(res.data);
      if (res.data.discovered_forms.length > 0) {
        setSelectedForm(res.data.discovered_forms[0]);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || '탐색 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = () => {
    if (selectedForm) {
      onApply(selectedForm, url.trim());
      onClose();
    }
  };

  const selectorLabels: Record<string, string> = {
    name_selector: '이름',
    phone_selector: '전화',
    subject_selector: '제목',
    message_selector: '메시지',
    agreement_selector: '동의',
    submit_selector: '제출',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-md" onClick={onClose} />

      <div className="relative w-full max-w-2xl bg-[#0d1117] border border-white/10 rounded-3xl shadow-2xl shadow-black/60 overflow-hidden">
        {/* Header */}
        <div className="relative p-6 border-b border-white/5">
          <div className="absolute inset-0 bg-gradient-to-br from-violet-500/10 to-blue-500/5" />
          <div className="relative flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-violet-500/20 border border-violet-500/30 flex items-center justify-center">
              <Sparkles size={20} className="text-violet-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">AI 자동 탐색</h2>
              <p className="text-slate-400 text-sm mt-0.5">홈페이지 URL만 입력하면 상담폼을 자동으로 찾아드립니다</p>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5 max-h-[70vh] overflow-y-auto">
          {/* URL Input */}
          <div className="space-y-3">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">병원 홈페이지 URL</label>
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Globe className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                <input
                  type="url"
                  value={url}
                  onChange={e => setUrl(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleDiscover()}
                  placeholder="https://www.hospital-example.com"
                  className="w-full bg-white/5 border border-white/10 rounded-2xl py-3.5 pl-11 pr-4 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-violet-500/40 focus:border-violet-500/50 transition-all"
                />
              </div>
              <button
                onClick={handleDiscover}
                disabled={loading || !url.trim()}
                className="bg-violet-500 hover:bg-violet-600 disabled:opacity-40 disabled:cursor-not-allowed px-5 py-3.5 rounded-2xl font-bold text-sm flex items-center gap-2 transition-all active:scale-95 shadow-lg shadow-violet-500/20 whitespace-nowrap"
              >
                {loading ? <Loader size={16} className="animate-spin" /> : <Search size={16} />}
                {loading ? '탐색 중...' : '탐색 시작'}
              </button>
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="bg-violet-500/5 border border-violet-500/20 rounded-2xl p-6 text-center space-y-3">
              <Loader size={32} className="mx-auto text-violet-400 animate-spin" />
              <div>
                <p className="font-semibold text-white">홈페이지를 분석하고 있습니다...</p>
                <p className="text-slate-400 text-sm mt-1">상담폼 링크를 탐색하고 셀렉터를 자동으로 감지합니다</p>
              </div>
              <div className="flex justify-center gap-2 text-xs text-slate-500">
                <span className="flex items-center gap-1"><CheckCircle size={11} className="text-emerald-500" /> 링크 수집</span>
                <ChevronRight size={11} />
                <span className="flex items-center gap-1"><Loader size={11} className="animate-spin text-violet-400" /> 폼 탐지</span>
                <ChevronRight size={11} />
                <span className="flex items-center gap-1 opacity-40">셀렉터 분석</span>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4 flex items-center gap-3">
              <AlertTriangle size={20} className="text-red-400 flex-shrink-0" />
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}

          {/* Results */}
          {result && !loading && (
            <div className="space-y-4">
              {/* Summary */}
              <div className={`border rounded-2xl p-4 flex items-center gap-3 ${
                result.discovered_forms.length > 0
                  ? 'bg-emerald-500/5 border-emerald-500/20'
                  : 'bg-yellow-500/5 border-yellow-500/20'
              }`}>
                {result.discovered_forms.length > 0
                  ? <CheckCircle size={20} className="text-emerald-400 flex-shrink-0" />
                  : <AlertTriangle size={20} className="text-yellow-400 flex-shrink-0" />
                }
                <div>
                  <p className={`font-semibold text-sm ${result.discovered_forms.length > 0 ? 'text-emerald-300' : 'text-yellow-300'}`}>
                    {result.discovered_forms.length > 0
                      ? `${result.discovered_forms.length}개의 상담폼을 발견했습니다!`
                      : '상담폼을 찾지 못했습니다'
                    }
                  </p>
                  {result.discovered_forms.length === 0 && (
                    <p className="text-slate-400 text-xs mt-0.5">
                      직접 폼 URL과 셀렉터를 입력하거나, 수동 설정 모드를 사용해주세요.
                    </p>
                  )}
                </div>
              </div>

              {/* Form Cards */}
              {result.discovered_forms.map((form, idx) => (
                <div
                  key={idx}
                  onClick={() => setSelectedForm(form)}
                  className={`border rounded-2xl p-4 cursor-pointer transition-all ${
                    selectedForm?.url === form.url
                      ? 'border-violet-500/50 bg-violet-500/10'
                      : 'border-white/5 bg-white/[0.02] hover:border-white/20 hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Target size={14} className="text-violet-400 flex-shrink-0" />
                        <span className="font-bold text-sm text-white truncate">{form.link_text}</span>
                        {idx === 0 && (
                          <span className="bg-violet-500/20 text-violet-400 text-[9px] font-bold px-1.5 py-0.5 rounded-md border border-violet-500/30 flex-shrink-0">추천</span>
                        )}
                      </div>
                      <p className="text-blue-400/70 text-[11px] font-mono truncate">{form.url}</p>
                    </div>
                    <div className={`w-5 h-5 rounded-full border-2 flex-shrink-0 mt-0.5 ${
                      selectedForm?.url === form.url
                        ? 'border-violet-500 bg-violet-500'
                        : 'border-white/20'
                    }`}>
                      {selectedForm?.url === form.url && (
                        <CheckCircle size={16} className="text-white m-auto" />
                      )}
                    </div>
                  </div>

                  {/* Confidence */}
                  <div className="mb-3">
                    <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                      <span>탐지 신뢰도</span>
                      <span>{form.selector_count || 0}개 셀렉터 발견</span>
                    </div>
                    <ConfidenceBar value={form.confidence} />
                  </div>

                  {/* Selectors */}
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(selectorLabels).map(([key, label]) => (
                      <SelectorPill
                        key={key}
                        label={label}
                        value={(form.selectors as any)[key]}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/5 flex justify-between items-center gap-3">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-all text-sm font-medium"
          >
            취소
          </button>
          
          <div className="flex items-center gap-3">
            {result && result.discovered_forms.length === 0 && (
              <p className="text-slate-500 text-xs">탐지 결과 없음 — 수동 입력 모드로 전환하세요</p>
            )}
            <button
              onClick={handleApply}
              disabled={!selectedForm}
              className="bg-violet-500 hover:bg-violet-600 disabled:opacity-40 disabled:cursor-not-allowed px-6 py-2.5 rounded-xl font-bold text-sm flex items-center gap-2 transition-all active:scale-95"
            >
              이 설정 적용하기
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AutoDiscoveryModal;
