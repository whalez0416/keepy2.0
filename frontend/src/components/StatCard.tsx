import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  color: string;
  glowColor?: 'emerald' | 'blue' | 'red';
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon: Icon, color, glowColor }) => {
  return (
    <div className={`glass p-6 rounded-2xl border border-white/5 relative overflow-hidden group hover:border-white/10 transition-all ${glowColor ? `glow-${glowColor}` : ''}`}>
      <div className="absolute -right-4 -bottom-4 opacity-[0.03] group-hover:opacity-[0.05] transition-opacity">
        <Icon size={120} />
      </div>
      <div className="flex justify-between items-start mb-4 relative z-10">
        <span className="text-slate-400 font-medium text-sm">{label}</span>
        <div className={`p-2 rounded-lg bg-white/5 ${color}`}>
           <Icon size={20} />
        </div>
      </div>
      <div className="text-3xl font-bold tracking-tight relative z-10">{value}</div>
    </div>
  );
};

export default StatCard;
