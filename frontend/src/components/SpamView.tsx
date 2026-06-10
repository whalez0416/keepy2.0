import React, { useState, useEffect } from 'react';
import {
  Shield, ShieldAlert, ShieldCheck, Loader, Search,
  AlertTriangle, CheckCircle, XCircle, Brain, Trash2,
  Plus, RefreshCw, Tag, Globe, ChevronDown, ChevronUp
} from 'lucide-react';
import { spamApi, SpamConfig, SpamScanResult, SpamPost } from '../lib/api';

interface SpamViewProps {
  siteId?: number;
  siteName?: string;
}

const MethodBadge: React.FC<{ method: string }> = ({ method }) => {
  const isAI = method === 'openai_ai';
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[9px] font-bold border ${
      isAI
        ? 'bg-violet-500/10 text-violet-400 border-violet-500/20'
        : 'bg-slate-500/10 text-slate-400 border-slate-500/20'
    }`}>
      {isAI ? <Brain size={9} /> : <Tag size={9} />}
      {isAI ? 'GPT AI' : '키워드'}
    </span>
  );
};

const ConfidenceDot: React.FC<{ value: number }> = ({ value }) => {
  const pct = Math.round(value * 100);
  return (
    <span className={`text-[11px] font-bold ${
      pct >= 80 ? 'text-red-400' : pct >= 60 ? 'text-yellow-400' : 'text-slate-400'
    }`}>
      {pct}%
    </span>
  );
};

const SpamView: React.FC<SpamViewProps> = ({ siteId, siteName }) => {
  const [configs, setConfigs] = useState<SpamConfig[]>([]);
  const [scanResult, setScanResult] = useState<SpamScanResult | null>(null);
  const [scanning, setScanning] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [expandedSpam, setExpandedSpam] = useState<number | null>(null);

  // Add form state
  const [newBoardUrl, setNewBoardUrl] = useState('');
  const [newKeywords, setNewKeywords] = useState('');
  const [newAdminId, setNewAdminId] = useState('');
  const [newAdminPw, setNewAdminPw] = useState('');
  const [addLoading, setAddLoading] = useState(false);

  useEffect(() => {
    if (siteId) {
      loadConfigs();
    }
  }, [siteId]);

  const loadConfigs = async () => {
    if (!siteId) return;
    try {
      const res = await spamApi.getConfigs(siteId);
      setConfigs(res.data);
    } catch (err) {
      console.error('스팸 설정 로드 실패:', err);
    }
  };

  const handleAddConfig = async () => {
    if (!newBoardUrl.trim() || !siteId) return;
    setAddLoading(true);
    try {
      await spamApi.createConfig({
        site_id: siteId,
        board_url: newBoardUrl.trim(),
        keywords: newKeywords.trim() || undefined,
        admin_id: newAdminId.trim() || undefined,
        admin_pw: newAdminPw.trim() || undefined,
        is_active: true,
      });
      setNewBoardUrl('');
      setNewKeywords('');
      setNewAdminId('');
      setNewAdminPw('');
      setShowAddForm(false);
      await loadConfigs();
    } catch (err) {
      alert('설정 추가 실패');
    } finally {
      setAddLoading(false);
    }
  };

  const handleDeleteConfig = async (id: number) => {
    if (!confirm('이 스팸 설정을 삭제하시겠습니까?')) return;
    try {
      await spamApi.deleteConfig(id);
      await loadConfigs();
    } catch (err) {
      alert('삭제 실패');
    }
  };

  const handleRunScan = async (config: SpamConfig) => {
    setScanning(true);
    setScanResult(null);
    try {
      const res = await spamApi.runConfig(config.id);
      setScanResult(res.data);
    } catch (err: any) {
      alert('스캔 실패: ' + (err?.response?.data?.detail || err.message));
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-violet-500/15 border border-violet-500/25 flex items-center justify-center">
            <Brain size={20} className="text-violet-400" />
          </div>
          <div>
            <h3 className="font-bold text-white">AI 스팸 헌터</h3>
            <p className="text-slate-400 text-xs mt-0.5">{siteName || '선택된 병원'}의 게시판 스팸 탐지</p>
          </div>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-violet-500/15 hover:bg-violet-500/25 border border-violet-500/25 px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 text-violet-300 transition-all"
        >
          <Plus size={16} />
          게시판 추가
        </button>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-5 space-y-4">
          <h4 className="font-bold text-sm text-slate-300">새 게시판 스팸 감시 설정</h4>
          
          <div className="space-y-3">
            <div>
              <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 block">게시판 URL *</label>
              <input
                type="url"
                value={newBoardUrl}
                onChange={e => setNewBoardUrl(e.target.value)}
                placeholder="https://hospital.com/bbs/board.php?bo_table=free"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-violet-500/30 transition-all"
              />
            </div>
            <div>
              <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 block">추가 금지 키워드 (콤마로 구분)</label>
              <input
                type="text"
                value={newKeywords}
                onChange={e => setNewKeywords(e.target.value)}
                placeholder="비아그라, 카지노, 무료나눔, ..."
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-violet-500/30 transition-all"
              />
              <p className="text-slate-600 text-[10px] mt-1">AI가 기본 스팸 패턴을 자동 감지합니다. 병원별 특수 키워드만 추가하세요.</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 block">관리자 ID (선택)</label>
                <input
                  type="text"
                  value={newAdminId}
                  onChange={e => setNewAdminId(e.target.value)}
                  placeholder="admin"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-violet-500/30 transition-all"
                />
              </div>
              <div>
                <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 block">관리자 PW (선택)</label>
                <input
                  type="password"
                  value={newAdminPw}
                  onChange={e => setNewAdminPw(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-violet-500/30 transition-all"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <button onClick={() => setShowAddForm(false)} className="px-4 py-2 rounded-xl text-slate-400 hover:text-white text-sm transition-all">취소</button>
            <button
              onClick={handleAddConfig}
              disabled={addLoading || !newBoardUrl.trim()}
              className="bg-violet-500 hover:bg-violet-600 disabled:opacity-40 px-5 py-2 rounded-xl font-bold text-sm transition-all flex items-center gap-2"
            >
              {addLoading ? <Loader size={14} className="animate-spin" /> : <Plus size={14} />}
              추가
            </button>
          </div>
        </div>
      )}

      {/* Configs List */}
      {!siteId ? (
        <div className="text-center py-12 text-slate-500">
          <Shield size={40} className="mx-auto mb-3 opacity-20" />
          <p className="font-medium">병원을 선택해주세요</p>
        </div>
      ) : configs.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          <ShieldAlert size={40} className="mx-auto mb-3 opacity-20" />
          <p className="font-medium">등록된 게시판이 없습니다</p>
          <p className="text-sm mt-1">위 버튼을 눌러 게시판을 추가해주세요</p>
        </div>
      ) : (
        <div className="space-y-3">
          {configs.map(config => (
            <div key={config.id} className="bg-white/[0.02] border border-white/5 rounded-2xl p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Globe size={13} className="text-blue-400 flex-shrink-0" />
                    <span className="text-blue-400 text-xs font-mono truncate">{config.board_url}</span>
                  </div>
                  {config.keywords && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {config.keywords.split(',').filter(k => k.trim()).map((kw, i) => (
                        <span key={i} className="bg-white/5 text-slate-400 px-1.5 py-0.5 rounded text-[10px] border border-white/5">
                          {kw.trim()}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleRunScan(config)}
                    disabled={scanning}
                    className="bg-violet-500/15 hover:bg-violet-500/25 border border-violet-500/20 px-3 py-1.5 rounded-lg text-xs font-bold text-violet-300 transition-all flex items-center gap-1.5"
                  >
                    {scanning ? <Loader size={12} className="animate-spin" /> : <RefreshCw size={12} />}
                    스캔
                  </button>
                  <button
                    onClick={() => handleDeleteConfig(config.id)}
                    className="text-slate-600 hover:text-red-400 p-1.5 rounded-lg hover:bg-red-500/10 transition-all"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Scan Results */}
      {scanning && (
        <div className="bg-violet-500/5 border border-violet-500/20 rounded-2xl p-6 text-center space-y-3">
          <Brain size={32} className="mx-auto text-violet-400 animate-pulse" />
          <div>
            <p className="font-semibold text-white">GPT AI가 게시물을 분석 중입니다...</p>
            <p className="text-slate-400 text-sm mt-1">게시물 텍스트를 읽고 스팸 여부를 판별합니다</p>
          </div>
        </div>
      )}

      {scanResult && !scanning && (
        <div className="space-y-4">
          {/* Result Summary */}
          <div className={`border rounded-2xl p-4 ${
            scanResult.spam_detected > 0
              ? 'bg-red-500/5 border-red-500/20'
              : 'bg-emerald-500/5 border-emerald-500/20'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {scanResult.spam_detected > 0
                  ? <ShieldAlert size={24} className="text-red-400" />
                  : <ShieldCheck size={24} className="text-emerald-400" />
                }
                <div>
                  <p className={`font-bold text-base ${scanResult.spam_detected > 0 ? 'text-red-300' : 'text-emerald-300'}`}>
                    {scanResult.spam_detected > 0
                      ? `스팸 ${scanResult.spam_detected}개 탐지!`
                      : '스팸 없음 — 게시판이 깨끗합니다'
                    }
                  </p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-slate-400 text-xs">총 {scanResult.total_posts}개 게시물 분석</span>
                    <MethodBadge method={scanResult.classification_method} />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Spam Posts */}
          {scanResult.spam_posts.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">탐지된 스팸 게시물</h4>
              {scanResult.spam_posts.map((post, idx) => (
                <div
                  key={idx}
                  className="bg-red-500/5 border border-red-500/10 rounded-xl p-3 cursor-pointer"
                  onClick={() => setExpandedSpam(expandedSpam === idx ? null : idx)}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <AlertTriangle size={14} className="text-red-400 flex-shrink-0" />
                      <span className="text-white text-sm font-medium truncate">{post.title}</span>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <MethodBadge method={post.method} />
                      <ConfidenceDot value={post.confidence} />
                      {expandedSpam === idx ? <ChevronUp size={14} className="text-slate-500" /> : <ChevronDown size={14} className="text-slate-500" />}
                    </div>
                  </div>
                  {expandedSpam === idx && (
                    <div className="mt-2 pt-2 border-t border-red-500/10">
                      <p className="text-slate-400 text-xs">{post.reason}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SpamView;
