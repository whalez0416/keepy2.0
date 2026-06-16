import React, { useState, useEffect } from 'react';
import { 
  Mail, Phone, Globe, Building, CheckCircle, Clock, 
  CheckSquare, XCircle, UserPlus, Sparkles, Plus, 
  Shield, Key, Star, Crown, Zap, X, Search 
} from 'lucide-react';
import { leadsApi, authApi } from '../lib/api';

interface Lead {
  id: number;
  hospital_name: string;
  contact_name: string;
  phone_number: string;
  email: string;
  website_url: string;
  plan: string;
  inquiry: string;
  status: string;
  created_at: string;
}

const statusConfig: Record<string, { label: string, color: string, icon: any }> = {
  new: { label: '신규 접수', color: 'text-blue-400 bg-blue-500/10 border-blue-500/20', icon: Clock },
  in_review: { label: '검토 중', color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20', icon: Clock },
  contacted: { label: '연락 완료', color: 'text-[#c8d4de] bg-[#9fb2c2]/10 border-[#9fb2c2]/20', icon: CheckSquare },
  closed: { label: '종료', color: 'text-slate-400 bg-slate-500/10 border-slate-500/20', icon: XCircle },
};

const PLAN_LABELS: Record<string, string> = {
  starter: 'Starter Plan',
  type_a: 'Type A (Basic)',
  type_b: 'Type B (Pro)',
  type_c: 'Type C (Premium)',
  corporate: 'Corporate Plan'
};

export default function LeadsAdminView() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // 계정 발급 모달 상태
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [createFormData, setCreateFormData] = useState({
    email: '',
    password: '',
    hospital_name: '',
    plan: 'type_b' // 기본값 Pro
  });

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      const response = await leadsApi.list();
      setLeads(response.data);
    } catch (error) {
      console.error('Failed to fetch leads:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (leadId: number, newStatus: string) => {
    try {
      await leadsApi.updateStatus(leadId, newStatus);
      setLeads(leads.map(lead => lead.id === leadId ? { ...lead, status: newStatus } : lead));
    } catch (error) {
      console.error('Failed to update status:', error);
      alert('상태 변경에 실패했습니다.');
    }
  };

  // 계정 직접 생성 모달 열기
  const handleOpenDirectCreate = () => {
    setCreateFormData({
      email: '',
      password: 'keepy' + Math.floor(1000 + Math.random() * 9000), // 임의 비번 자동 생성
      hospital_name: '',
      plan: 'type_b'
    });
    setCreateError(null);
    setIsCreateModalOpen(true);
  };

  // 리드 상세에서 즉시 발급 모달 열기
  const handleOpenCreateFromLead = (lead: Lead) => {
    // 리드 요금제 맵핑 (리드가 갖고 있는 요금제 텍스트가 type_a 등인지 확인)
    let planKey = 'type_b';
    const rawPlan = lead.plan.toLowerCase();
    if (rawPlan.includes('a') || rawPlan.includes('basic')) planKey = 'type_a';
    else if (rawPlan.includes('b') || rawPlan.includes('pro')) planKey = 'type_b';
    else if (rawPlan.includes('c') || rawPlan.includes('premium')) planKey = 'type_c';
    else if (rawPlan.includes('corp')) planKey = 'corporate';

    setCreateFormData({
      email: lead.email,
      password: 'keepy' + Math.floor(1000 + Math.random() * 9000),
      hospital_name: lead.hospital_name,
      plan: planKey
    });
    setCreateError(null);
    setIsCreateModalOpen(true);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setCreateError(null);

    try {
      await authApi.createHospitalAdmin(createFormData);
      alert(`성공적으로 [${createFormData.hospital_name}] 병원 관리자 계정이 발급되었습니다!\n\nID: ${createFormData.email}\nPW: ${createFormData.password}\nPlan: ${PLAN_LABELS[createFormData.plan]}`);
      setIsCreateModalOpen(false);
      
      // 만약 리드와 매핑되어 발급한 거라면, 리드 상태를 '연락 완료' 및 '종료' 상태로 전환
      if (selectedLead && selectedLead.email === createFormData.email) {
        handleStatusChange(selectedLead.id, 'closed');
        setSelectedLead(null);
      }
    } catch (err: any) {
      console.error("Failed to create admin:", err);
      setCreateError(err.response?.data?.detail || '계정 생성에 실패했습니다. 이메일 중복 등을 확인해 주세요.');
    } finally {
      setCreating(false);
    }
  };

  // 리드 검색 필터
  const filteredLeads = leads.filter(lead => 
    lead.hospital_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lead.contact_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lead.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (lead.inquiry || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return <div className="p-8 text-center text-slate-400">상담 정보를 불러오는 중...</div>;
  }

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-200">상담 및 계정 발급 관리</h1>
          <p className="text-slate-400 mt-2">고객 문의 내역을 모니터링하고 B2B 병원 관리자 계정 및 구독 플랜을 직접 발급합니다.</p>
        </div>
        <button
          onClick={handleOpenDirectCreate}
          className="bg-gradient-to-b from-[#e9eef2] via-[#b9c4cd] to-[#8b97a1] hover:brightness-110 border border-white/40 px-6 py-3.5 rounded-2xl font-bold flex items-center gap-2 transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.5),0_8px_24px_rgba(0,0,0,0.5)] active:scale-95 text-[#0a0c0f]"
        >
          <UserPlus size={18} /> 병원 계정 직접 생성
        </button>
      </div>

      {/* Search Input */}
      <div className="relative group max-w-md">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-[#c8d4de] transition-colors" size={20} />
        <input 
          type="text" 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="병원명, 문의자, 이메일, 내용으로 검색..." 
          className="w-full glass border border-white/5 rounded-2xl py-4 pl-12 pr-4 focus:ring-2 focus:ring-[#9fb2c2]/40 outline-none transition-all placeholder:text-slate-600 font-medium"
        />
      </div>

      <div className="glass rounded-3xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/5 bg-white/[0.02] text-sm font-semibold text-slate-400">
                <th className="p-4 pl-6">상태</th>
                <th className="p-4">병원/기관명</th>
                <th className="p-4">담당자 (연락처)</th>
                <th className="p-4">접수일시</th>
                <th className="p-4 pr-6 text-right">진행도 관리</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredLeads.map((lead) => (
                <tr key={lead.id} className="hover:bg-white/[0.02] transition-colors cursor-pointer group" onClick={() => setSelectedLead(lead)}>
                  <td className="p-4 pl-6">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold border ${statusConfig[lead.status]?.color}`}>
                      {React.createElement(statusConfig[lead.status]?.icon || Clock, { size: 12 })}
                      {statusConfig[lead.status]?.label}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <Building size={16} className="text-slate-500" />
                      <span className="font-bold text-slate-200 group-hover:text-[#c8d4de] transition-colors">{lead.hospital_name}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="text-sm font-medium text-slate-300">{lead.contact_name}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{lead.phone_number}</div>
                  </td>
                  <td className="p-4">
                    <div className="text-sm text-slate-400">
                      {new Date(lead.created_at).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="p-4 pr-6 text-right" onClick={(e) => e.stopPropagation()}>
                    <select
                      className="bg-[#0f111a] border border-white/10 rounded-xl px-3 py-1.5 text-sm font-medium text-slate-300 focus:outline-none focus:border-[#9fb2c2]/50"
                      value={lead.status}
                      onChange={(e) => handleStatusChange(lead.id, e.target.value)}
                    >
                      <option value="new">신규 접수</option>
                      <option value="in_review">검토 중</option>
                      <option value="contacted">연락 완료</option>
                      <option value="closed">종료</option>
                    </select>
                  </td>
                </tr>
              ))}
              {filteredLeads.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-500">조회된 문의가 없습니다.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 리드 상세 모달 */}
      {selectedLead && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-[#0f111a] border border-white/10 rounded-3xl p-6 max-w-2xl w-full relative shadow-2xl animate-in zoom-in duration-300">
            <button
              onClick={() => setSelectedLead(null)}
              className="absolute top-6 right-6 text-slate-500 hover:text-slate-300 transition-colors"
            >
              <XCircle size={24} />
            </button>
            <h2 className="text-2xl font-bold text-slate-200 mb-6">문의 상세 정보</h2>
            <div className="space-y-4 text-sm text-slate-300">
              <div className="grid grid-cols-2 gap-4">
                <div className="glass p-4 rounded-2xl">
                  <span className="text-slate-500 block mb-1">병원/기관명</span>
                  <span className="font-bold text-white text-lg">{selectedLead.hospital_name}</span>
                </div>
                <div className="glass p-4 rounded-2xl">
                  <span className="text-slate-500 block mb-1">담당자</span>
                  <span className="font-bold text-white text-lg">{selectedLead.contact_name}</span>
                </div>
              </div>
              <div className="flex items-center gap-3 glass p-4 rounded-2xl">
                <Phone size={18} className="text-[#9fb2c2]" />
                <span className="font-bold">{selectedLead.phone_number}</span>
              </div>
              <div className="flex items-center gap-3 glass p-4 rounded-2xl">
                <Mail size={18} className="text-blue-500" />
                <span>{selectedLead.email}</span>
              </div>
              <div className="flex items-center gap-3 glass p-4 rounded-2xl">
                <Globe size={18} className="text-purple-500" />
                <a href={selectedLead.website_url.startsWith('http') ? selectedLead.website_url : `https://${selectedLead.website_url}`} target="_blank" rel="noreferrer" className="text-[#c8d4de] hover:underline">
                  {selectedLead.website_url}
                </a>
              </div>
              <div className="glass p-4 rounded-2xl border-[#9fb2c2]/20">
                <span className="text-slate-500 block mb-2">관심 요금제</span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold border border-[#9fb2c2]/30 text-[#c8d4de] bg-[#9fb2c2]/10">
                  {selectedLead.plan}
                </span>
              </div>
              <div className="glass p-4 rounded-2xl bg-white/[0.02]">
                <span className="text-slate-500 block mb-2">문의 내용</span>
                <p className="whitespace-pre-wrap leading-relaxed">
                  {selectedLead.inquiry || "작성된 문의 내용이 없습니다."}
                </p>
              </div>
            </div>
            
            <div className="mt-8 flex justify-between items-center border-t border-white/5 pt-4">
              {selectedLead.status !== 'closed' && (
                <button
                  onClick={() => handleOpenCreateFromLead(selectedLead)}
                  className="bg-gradient-to-b from-[#e9eef2] via-[#b9c4cd] to-[#8b97a1] text-[#0a0c0f] px-6 py-3 rounded-xl font-bold flex items-center gap-2 hover:brightness-110 border border-white/40 transition-all active:scale-95 shadow-[inset_0_1px_0_rgba(255,255,255,0.5),0_8px_24px_rgba(0,0,0,0.5)]"
                >
                  <UserPlus size={16} /> 병원 계정/요금제 즉시 발급
                </button>
              )}
              <button
                onClick={() => setSelectedLead(null)}
                className="px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl font-bold transition-all ml-auto"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 계정 생성 모달 (Super Admin 전용) */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-[60]">
          <div className="bg-[#0c0e14] border border-white/10 rounded-[32px] p-8 max-w-md w-full relative shadow-2xl animate-in zoom-in duration-300">
            <button
              onClick={() => setIsCreateModalOpen(false)}
              className="absolute top-6 right-6 text-slate-500 hover:text-slate-300 transition-colors"
            >
              <X size={20} />
            </button>

            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-[#9fb2c2]/20 border border-[#9fb2c2]/30 flex items-center justify-center">
                <UserPlus className="text-[#c8d4de]" size={20} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">병원 관리자 계정 발급</h3>
                <p className="text-slate-500 text-[10px] uppercase font-bold tracking-wider mt-0.5">B2B Account Provisioning</p>
              </div>
            </div>

            {createError && (
              <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-xl text-red-400 text-xs font-bold mb-4">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">병원/기관 이름 *</label>
                <input
                  required
                  type="text"
                  placeholder="예: 민트치과의원"
                  value={createFormData.hospital_name}
                  onChange={e => setCreateFormData({...createFormData, hospital_name: e.target.value})}
                  className="w-full glass border border-white/5 rounded-xl px-4 py-3 text-sm font-bold text-slate-200 outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 transition-all"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">관리자 이메일 (ID) *</label>
                <input
                  required
                  type="email"
                  placeholder="예: admin@mint.com"
                  value={createFormData.email}
                  onChange={e => setCreateFormData({...createFormData, email: e.target.value})}
                  className="w-full glass border border-white/5 rounded-xl px-4 py-3 text-sm font-bold text-slate-200 outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 transition-all"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">초기 비밀번호 *</label>
                <input
                  required
                  type="text"
                  placeholder="예: keepy1234"
                  value={createFormData.password}
                  onChange={e => setCreateFormData({...createFormData, password: e.target.value})}
                  className="w-full glass border border-white/5 rounded-xl px-4 py-3 text-sm font-bold text-[#c8d4de] outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 transition-all"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">할당 요금제 플랜</label>
                <select
                  value={createFormData.plan}
                  onChange={e => setCreateFormData({...createFormData, plan: e.target.value})}
                  className="w-full glass border border-white/5 rounded-xl px-4 py-3 text-sm font-bold text-slate-200 outline-none focus:ring-2 focus:ring-[#9fb2c2]/40 transition-all"
                >
                  <option value="starter">Starter (무료)</option>
                  <option value="type_a">Type A (Basic)</option>
                  <option value="type_b">Type B (Pro)</option>
                  <option value="type_c">Type C (Premium)</option>
                  <option value="corporate">Corporate (법인)</option>
                </select>
              </div>

              <div className="bg-[#9fb2c2]/5 border border-[#9fb2c2]/10 p-4 rounded-2xl flex items-start gap-3 mt-6">
                <Shield size={16} className="text-[#c8d4de] mt-0.5 flex-shrink-0" />
                <p className="text-[10px] text-slate-400 leading-relaxed font-semibold">
                  계정 생성 시, 해당 병원의 <strong>독립된 작업 공간(Workspace)</strong>이 자동 개설되며, 선택한 요금제 구독 등급이 즉시 활성화 처리됩니다.
                </p>
              </div>

              <div className="flex gap-3 mt-8">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="flex-1 py-3 bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white rounded-xl text-sm font-bold transition-all"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 py-3 bg-gradient-to-b from-[#e9eef2] via-[#b9c4cd] to-[#8b97a1] hover:brightness-110 border border-white/40 text-[#0a0c0f] rounded-xl text-sm font-black flex items-center justify-center gap-2 transition-all shadow-[inset_0_1px_0_rgba(255,255,255,0.5),0_8px_24px_rgba(0,0,0,0.5)] active:scale-95 disabled:opacity-50"
                >
                  {creating && <Clock size={14} className="animate-spin" />}
                  계정 발급 완료
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
