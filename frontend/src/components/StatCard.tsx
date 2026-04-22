import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon: Icon, color }) => {
  return (
    <div className="glass p-6 rounded-2xl border border-white/5">
      <div className="flex justify-between items-start mb-4">
        <span className="text-slate-400 font-medium">{label}</span>
        <Icon className={color} size={24} />
      </div>
      <div className="text-3xl font-bold">{value}</div>
    </div>
  );
};

export default StatCard;
