import React, { useState, useEffect } from 'react';
import { Mail, Phone, Globe, Building, CheckCircle, Clock, CheckSquare, XCircle } from 'lucide-react';
import { leadsApi } from '../lib/api';

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
  contacted: { label: '연락 완료', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20', icon: CheckSquare },
  closed: { label: '종료', color: 'text-slate-400 bg-slate-500/10 border-slate-500/20', icon: XCircle },
};

export default function LeadsAdminView() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

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

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading leads...</div>;
  }

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-200">상담 관리</h1>
          <p className="text-slate-400 mt-2">랜딩 페이지를 통해 접수된 고객 문의 내역입니다.</p>
        </div>
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
                <th className="p-4 pr-6 text-right">관리</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {leads.map((lead) => (
                <tr key={lead.id} className="hover:bg-white/[0.02] transition-colors cursor-pointer" onClick={() => setSelectedLead(lead)}>
                  <td className="p-4 pl-6">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold border ${statusConfig[lead.status]?.color}`}>
                      {React.createElement(statusConfig[lead.status]?.icon || Clock, { size: 12 })}
                      {statusConfig[lead.status]?.label}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <Building size={16} className="text-slate-500" />
                      <span className="font-bold text-slate-200">{lead.hospital_name}</span>
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
                      className="bg-[#0f111a] border border-white/10 rounded-xl px-3 py-1.5 text-sm font-medium text-slate-300 focus:outline-none focus:border-emerald-500/50"
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
              {leads.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-500">접수된 문의가 없습니다.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selectedLead && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-[#0f111a] border border-white/10 rounded-3xl p-6 max-w-2xl w-full relative shadow-2xl">
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
                <Phone size={18} className="text-emerald-500" />
                <span className="font-bold">{selectedLead.phone_number}</span>
              </div>
              <div className="flex items-center gap-3 glass p-4 rounded-2xl">
                <Mail size={18} className="text-blue-500" />
                <span>{selectedLead.email}</span>
              </div>
              <div className="flex items-center gap-3 glass p-4 rounded-2xl">
                <Globe size={18} className="text-purple-500" />
                <a href={selectedLead.website_url.startsWith('http') ? selectedLead.website_url : `https://${selectedLead.website_url}`} target="_blank" rel="noreferrer" className="text-emerald-400 hover:underline">
                  {selectedLead.website_url}
                </a>
              </div>
              <div className="glass p-4 rounded-2xl border-emerald-500/20">
                <span className="text-slate-500 block mb-2">관심 요금제</span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold border border-emerald-500/30 text-emerald-400 bg-emerald-500/10">
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
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedLead(null)}
                className="px-6 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl font-bold transition-all"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
