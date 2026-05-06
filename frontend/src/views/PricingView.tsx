import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Zap, Star, Crown, Shield, ArrowRight, Sparkles } from 'lucide-react';

const PLANS = [
  {
    id: 'type_a',
    name: 'Type A (Basic)',
    price: '29,000',
    description: '개인 의원을 위한 홈페이지 기초 보험',
    features: ['사이트 1개 모니터링', '5분 간격 스팸 체크', '접속 장애 및 SSL 만료 알림', '주간 보안 요약 리포트'],
    icon: Zap,
    color: 'from-emerald-400 to-teal-500',
    glow: 'shadow-emerald-500/20'
  },
  {
    id: 'type_b',
    name: 'Type B (Pro)',
    price: '59,000',
    description: '병원 매출과 보안을 동시에 잡는 표준형',
    features: ['사이트 5개 모니터링', 'AI 실시간 스팸 차단', 'SSL 인증서 자동 연장', '디도스/트래픽 장애 알림', '상담 신청폼 정상 작동 확인', '장애 시점 스크린샷 기록'],
    icon: Star,
    color: 'from-blue-400 to-indigo-500',
    glow: 'shadow-blue-500/20',
    popular: true
  },
  {
    id: 'type_c',
    name: 'Type C (Premium)',
    price: '129,000',
    description: '환자 가로채기 방지 및 브랜드 신뢰 강화',
    features: ['사이트 20개 모니터링', '연락처/카톡 링크 변조 감시', '홈페이지 화면 변조 탐지', '긴급 안내 배너 오버레이', 'SEO 검색 엔진 상태 감시', '1:1 전담 기술 지원'],
    icon: Shield,
    color: 'from-indigo-400 to-purple-500',
    glow: 'shadow-indigo-500/20'
  },
  {
    id: 'corporate',
    name: 'Corporate',
    price: '상담',
    description: '대형 의료 법인을 위한 통합 보안 관제',
    features: ['사이트 무제한 모니터링', '24/7 전담 장애 대응 팀', '관리자 페이지 무단 접속 감시', 'SLA 99.9% 가동률 보장', '정기 보안 정밀 진단', '맞춤형 보안 인프라 설계'],
    icon: Crown,
    color: 'from-purple-400 to-pink-500',
    glow: 'shadow-purple-500/20',
    isContact: true
  }
];

const PricingView: React.FC = () => {
  const navigate = useNavigate();

  const handleSelectPlan = (planId: string) => {
    if (planId === 'corporate') {
      window.open('https://tally.so/r/n0Dle8', '_blank');
      return;
    }
    navigate(`/register?plan=${planId}`);
  };

  return (
    <div className="min-h-screen bg-[#080a0f] text-slate-200 overflow-hidden relative pb-20">
      {/* Decorative Background Elements */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/10 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[60%] h-[60%] bg-purple-600/[0.03] blur-[150px] rounded-full" />
      </div>

      {/* Hero Section */}
      <section className="pt-24 pb-16 px-6 text-center relative">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8 animate-in fade-in slide-in-from-top-4 duration-1000">
          <Sparkles size={16} className="text-emerald-400" />
          <span className="text-xs font-black uppercase tracking-[0.2em] text-slate-400">Simple & Transparent Pricing</span>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-black text-white mb-6 tracking-tight animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-100">
          병원의 안전을 위한 <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-blue-500 to-purple-600">합리적인 선택</span>
        </h1>
        
        <p className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto font-medium leading-relaxed animate-in fade-in slide-in-from-bottom-6 duration-1000 delay-200">
          Keepy는 규모에 상관없이 모든 병원이 최상의 보안 환경을 <br className="hidden md:block" />
          구축할 수 있도록 유연한 구독 플랜을 제공합니다.
        </p>
      </section>

      {/* Pricing Cards Grid */}
      <div className="max-w-[1400px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative z-10">
        {PLANS.map((plan, index) => (
          <div 
            key={plan.id}
            className={`group glass-morphism rounded-[40px] p-10 border border-white/5 transition-all duration-500 hover:scale-[1.02] hover:border-white/20 flex flex-col relative animate-in fade-in slide-in-from-bottom-8 duration-1000`}
            style={{ animationDelay: `${300 + index * 150}ms` }}
          >
            {plan.popular && (
              <div className="absolute -top-5 left-1/2 -translate-x-1/2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-[10px] font-black uppercase tracking-[0.2em] px-6 py-2 rounded-full shadow-2xl shadow-blue-500/40 z-20">
                Most Popular
              </div>
            )}

            <div className={`w-16 h-16 rounded-3xl mb-8 flex items-center justify-center bg-gradient-to-br ${plan.color} ${plan.glow} text-white shadow-lg transform group-hover:rotate-6 transition-transform duration-500`}>
              <plan.icon size={32} />
            </div>

            <h3 className="text-3xl font-black text-white mb-2">{plan.name}</h3>
            <div className="flex items-baseline gap-2 mb-4">
              <span className="text-4xl font-black text-white tracking-tighter">
                {plan.price === '상담' ? '상담 문의' : `₩${plan.price}`}
              </span>
              {plan.price !== '상담' && <span className="text-slate-500 font-bold uppercase text-[10px] tracking-widest">/ Month</span>}
            </div>
            
            <p className="text-slate-500 text-sm font-medium leading-relaxed mb-8 h-12">
              {plan.description}
            </p>

            <div className="h-[1px] bg-white/5 w-full mb-8" />

            <ul className="space-y-5 flex-1 mb-10">
              {plan.features.map((feature, i) => (
                <li key={i} className="flex items-start gap-4 group/item">
                  <div className="w-6 h-6 rounded-full bg-white/5 flex items-center justify-center shrink-0 group-hover/item:bg-emerald-500/20 transition-colors">
                    <Check size={14} className="text-emerald-400" strokeWidth={3} />
                  </div>
                  <span className="text-sm font-bold text-slate-300 group-hover/item:text-white transition-colors">{feature}</span>
                </li>
              ))}
            </ul>

            <button 
              onClick={() => handleSelectPlan(plan.id)}
              className={`w-full py-5 rounded-2xl font-black text-sm flex items-center justify-center gap-3 transition-all active:scale-95 group/btn ${
                plan.popular 
                ? 'bg-white text-[#080a0f] hover:bg-emerald-400 hover:text-white shadow-2xl' 
                : plan.id === 'corporate'
                  ? 'bg-purple-600 text-white hover:bg-purple-700 shadow-xl shadow-purple-500/20'
                  : 'bg-white/5 text-white hover:bg-white/10 border border-white/10'
              }`}
            >
              {plan.id === 'corporate' ? '상담하기' : '시작하기'}
              <ArrowRight size={18} className="group-hover/btn:translate-x-1 transition-transform" />
            </button>
          </div>
        ))}
      </div>

      {/* Trust Badge Section */}
      <div className="max-w-4xl mx-auto mt-24 px-6 animate-in fade-in slide-in-from-bottom-10 duration-1000 delay-700">
        <div className="glass-morphism rounded-[40px] p-12 border border-white/5 flex flex-col md:flex-row items-center gap-12 text-center md:text-left">
          <div className="w-24 h-24 rounded-[32px] bg-emerald-500/10 flex items-center justify-center text-emerald-400 shrink-0 relative">
             <div className="absolute inset-0 bg-emerald-500/20 blur-2xl rounded-full" />
             <Shield size={48} className="relative" />
          </div>
          <div className="flex-1">
            <h4 className="text-2xl font-black text-white mb-3">안전한 서비스 이용을 약속합니다</h4>
            <p className="text-slate-500 font-medium leading-relaxed">
              Keepy는 모든 결제 정보를 암호화하여 처리하며, 데이터 보안을 최우선으로 생각합니다. 
              플랜 변경 및 해지는 언제든지 자유롭게 가능합니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingView;
