import React, { useState, useEffect } from 'react';
import { Building2, ChevronDown, Check, Globe } from 'lucide-react';
import { organizationsApi, Organization } from '../lib/api';

interface HospitalSelectorProps {
  onSelect: (orgId: number | 'all') => void;
  selectedOrgId: number | 'all';
}

const HospitalSelector: React.FC<HospitalSelectorProps> = ({ onSelect, selectedOrgId }) => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const fetchOrgs = async () => {
      try {
        const res = await organizationsApi.list();
        setOrganizations(res.data);
      } catch (err) {
        console.error('Failed to fetch organizations:', err);
      }
    };
    fetchOrgs();
  }, []);

  const selectedOrg = organizations.find(o => o.id === selectedOrgId);

  return (
    <div className="relative">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 px-4 py-2 bg-white/[0.03] border border-white/5 rounded-2xl hover:bg-white/[0.05] hover:border-[#9fb2c2]/30 transition-all text-sm font-bold group"
      >
        <div className="w-8 h-8 rounded-xl bg-[#9fb2c2]/10 flex items-center justify-center text-[#c8d4de]">
          {selectedOrgId === 'all' ? <Globe size={16} /> : <Building2 size={16} />}
        </div>
        <div className="text-left">
          <div className="text-[10px] text-slate-500 uppercase tracking-widest font-black">Monitoring Scope</div>
          <div className="text-slate-200">
            {selectedOrgId === 'all' ? '모든 병원 보기' : selectedOrg?.name}
          </div>
        </div>
        <ChevronDown size={16} className={`text-slate-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full mt-3 right-0 w-64 bg-[#0c0e14] border border-white/10 rounded-2xl shadow-2xl z-50 overflow-hidden backdrop-blur-xl animate-in fade-in zoom-in duration-200 origin-top-right">
            <div className="p-2">
              <button
                onClick={() => {
                  onSelect('all');
                  setIsOpen(false);
                }}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all ${
                  selectedOrgId === 'all' ? 'bg-[#9fb2c2]/10 text-[#c8d4de]' : 'text-slate-400 hover:bg-white/5 hover:text-white'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Globe size={16} />
                  <span className="font-bold">모든 병원 통합</span>
                </div>
                {selectedOrgId === 'all' && <Check size={16} />}
              </button>

              <div className="h-[1px] bg-white/5 my-2 mx-2" />

              <div className="max-h-60 overflow-y-auto custom-scrollbar">
                {organizations.map(org => (
                  <button
                    key={org.id}
                    onClick={() => {
                      onSelect(org.id);
                      setIsOpen(false);
                    }}
                    className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all ${
                      selectedOrgId === org.id ? 'bg-[#9fb2c2]/10 text-[#c8d4de]' : 'text-slate-400 hover:bg-white/5 hover:text-white'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Building2 size={16} />
                      <span className="font-bold">{org.name}</span>
                    </div>
                    {selectedOrgId === org.id && <Check size={16} />}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="bg-white/[0.02] p-4 border-t border-white/5 text-[10px] text-slate-500 font-bold uppercase tracking-widest text-center">
              관리자 전용 마스터 뷰
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default HospitalSelector;
