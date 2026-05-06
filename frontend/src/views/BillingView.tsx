import React, { useState, useEffect } from 'react';
import { CreditCard, Check, Shield, Star, Crown, Zap, AlertCircle } from 'lucide-react';
import { billingApi } from '../lib/api';

interface BillingViewProps {
  selectedOrgId: number | 'all';
}

const PLANS = [
  {
    id: 'type_a',
    name: 'Type A (Basic)',
    price: '29,000',
    description: '개인 의원을 위한 홈페이지 기초 보험',
    features: ['사이트 1개 모니터링', '5분 간격 스팸 체크', '접속 장애 및 SSL 만료 알림', '주간 보안 요약 리포트'],
    icon: Zap,
    color: 'emerald'
  },
  {
    id: 'type_b',
    name: 'Type B (Pro)',
    price: '59,000',
    description: '병원 매출과 보안을 동시에 잡는 표준형',
    features: ['사이트 5개 모니터링', 'AI 실시간 스팸 차단', 'SSL 인증서 자동 연장', '디도스/트래픽 장애 알림', '상담 신청폼 정상 작동 확인', '장애 시점 스크린샷 기록'],
    icon: Star,
    color: 'blue',
    popular: true
  },
  {
    id: 'type_c',
    name: 'Type C (Premium)',
    price: '129,000',
    description: '환자 가로채기 방지 및 브랜드 신뢰 강화',
    features: ['사이트 20개 모니터링', '연락처/카톡 링크 변조 감시', '홈페이지 화면 변조 탐지', '긴급 안내 배너 오버레이', 'SEO 검색 엔진 상태 감시', '1:1 전담 기술 지원'],
    icon: Shield,
    color: 'indigo'
  },
  {
    id: 'corporate',
    name: 'Corporate',
    price: '상담',
    description: '대형 의료 법인을 위한 통합 보안 관제',
    features: ['사이트 무제한 모니터링', '24/7 전담 장애 대응 팀', '관리자 페이지 무단 접속 감시', 'SLA 99.9% 가동률 보장', '정기 보안 정밀 진단', '맞춤형 보안 인프라 설계'],
    icon: Crown,
    color: 'purple',
    isContact: true
  }
];

const BillingView: React.FC<BillingViewProps> = ({ selectedOrgId }) => {
  const [currentBilling, setCurrentBilling] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState<string | null>(null);

  useEffect(() => {
    if (selectedOrgId !== 'all') {
      fetchBillingStatus();
    }
  }, [selectedOrgId]);

  const fetchBillingStatus = async () => {
    try {
      setLoading(true);
      const res = await billingApi.getStatus(selectedOrgId as number);
      setCurrentBilling(res.data);
    } catch (err) {
      console.error('Failed to fetch billing status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (planId: string) => {
    if (selectedOrgId === 'all') {
      alert('병원을 먼저 선택해주세요.');
      return;
    }

    const plan = PLANS.find(p => p.id === planId);
    if (!plan) return;

    try {
      setSubmitting(planId);
      
      // 토스페이먼츠 결제창 호출 (테스트 클라이언트 키)
      const clientKey = 'test_ck_D5mOwv173QPp0NnGWyme38ZAnR7X';
      const tossPayments = (window as any).TossPayments(clientKey);
      
      const orderId = `KEEPY_${Date.now()}_${selectedOrgId}`;
      const amount = parseInt(plan.price.replace(/,/g, '')) || 0;

      if (amount === 0) {
        // 무료 플랜은 바로 처리
        await billingApi.subscribe(selectedOrgId as number, planId);
        alert('Starter 플랜 구독이 시작되었습니다!');
        fetchBillingStatus();
        return;
      }

      await tossPayments.requestPayment('카드', {
        amount: amount,
        orderId: orderId,
        orderName: `Keepy ${plan.name} 플랜 구독`,
        customerName: 'Keepy 고객님',
        successUrl: `${window.location.origin}/payment/success?orgId=${selectedOrgId}&planId=${planId}`,
        failUrl: `${window.location.origin}/payment/fail`,
      });

    } catch (err) {
      console.error('Toss Payment failed:', err);
      alert('결제창을 불러오지 못했습니다.');
    } finally {
      setSubmitting(null);
    }
  };

  if (selectedOrgId === 'all') {
    return (
      <div className="p-8 h-[60vh] flex flex-col items-center justify-center text-center">
        <div className="w-20 h-20 rounded-3xl bg-white/5 flex items-center justify-center text-slate-500 mb-6">
          <CreditCard size={40} />
        </div>
        <h2 className="text-2xl font-black text-white mb-2">병원을 선택해주세요</h2>
        <p className="text-slate-500 max-w-md">결제 및 구독 정보는 각 병원(조직) 단위로 관리됩니다. 상단 선택기에서 병원을 선택한 후 결제를 진행해 주세요.</p>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-10 animate-in fade-in slide-up duration-700">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-black text-white tracking-tight">구독 및 플랜 관리</h2>
          <p className="text-slate-500 mt-2 font-medium">Keepy의 프리미엄 기능을 통해 병원 보안을 한 단계 더 높이세요.</p>
        </div>
        {currentBilling && (
          <div className="glass px-6 py-3 rounded-2xl border-emerald-500/20 bg-emerald-500/5 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            <span className="text-sm font-bold text-emerald-400 uppercase tracking-widest">
              Current: {currentBilling.plan} Plan
            </span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {PLANS.map((plan) => (
          <div 
            key={plan.id}
            className={`glass rounded-[40px] p-8 border transition-all duration-500 flex flex-col relative group ${
              plan.popular ? 'border-blue-500/50 bg-blue-500/5 shadow-2xl shadow-blue-500/10 scale-105 z-10' : 'border-white/5 hover:border-white/20'
            } ${currentBilling?.plan === plan.id ? 'border-emerald-500/50 bg-emerald-500/5' : ''} ${plan.id === 'corporate' ? 'border-purple-500/30' : ''}`}
          >
            {plan.popular && (
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-blue-500 text-white text-[10px] font-black uppercase tracking-widest px-4 py-1.5 rounded-full shadow-lg">
                Most Popular
              </div>
            )}

            <div className={`w-14 h-14 rounded-2xl mb-6 flex items-center justify-center ${
              plan.color === 'emerald' ? 'bg-emerald-500/20 text-emerald-400' : 
              plan.color === 'blue' ? 'bg-blue-500/20 text-blue-400' : 
              plan.color === 'indigo' ? 'bg-indigo-500/20 text-indigo-400' : 'bg-purple-500/20 text-purple-400'
            }`}>
              <plan.icon size={28} />
            </div>

            <h3 className="text-2xl font-black text-white">{plan.name}</h3>
            <div className="flex items-baseline gap-1 mt-2">
              <span className="text-3xl font-black text-white">{plan.price === '상담' ? '상담 문의' : `₩${plan.price}`}</span>
              {plan.price !== '상담' && <span className="text-slate-500 text-sm font-bold">/ month</span>}
            </div>
            <p className="text-slate-500 text-sm mt-4 font-medium leading-relaxed h-12">
              {plan.description}
            </p>

            <div className="h-[1px] bg-white/5 my-8" />

            <ul className="space-y-4 flex-1">
              {plan.features.map((feature, i) => (
                <li key={i} className="flex items-center gap-3 text-sm font-bold text-slate-300">
                  <div className="w-5 h-5 rounded-full bg-white/5 flex items-center justify-center text-emerald-400 shrink-0">
                    <Check size={12} strokeWidth={4} />
                  </div>
                  {feature}
                </li>
              ))}
            </ul>

            <button
              onClick={() => plan.price === '상담' ? window.open('https://tally.so/r/n0Dle8', '_blank') : handleSubscribe(plan.id)}
              disabled={submitting !== null || (currentBilling?.plan === plan.id && plan.price !== '상담')}
              className={`w-full py-4 rounded-2xl font-black mt-10 transition-all active:scale-95 flex items-center justify-center gap-2 ${
                currentBilling?.plan === plan.id 
                  ? 'bg-emerald-500/20 text-emerald-400 cursor-default border border-emerald-500/30' 
                  : plan.popular 
                    ? 'bg-blue-500 text-white hover:bg-blue-600 shadow-xl shadow-blue-500/30' 
                    : plan.price === '상담'
                      ? 'bg-purple-600 text-white hover:bg-purple-700'
                      : 'bg-white/5 text-white hover:bg-white/10'
              }`}
            >
              {submitting === plan.id ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : currentBilling?.plan === plan.id ? (
                '사용 중인 플랜'
              ) : plan.price === '상담' ? (
                '상담 신청하기'
              ) : (
                '플랜 선택하기'
              )}
            </button>
          </div>
        ))}
      </div>

      <div className="glass p-10 rounded-[40px] border-white/5 flex flex-col md:flex-row items-center gap-10">
        <div className="w-20 h-20 rounded-3xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 shrink-0">
          <Shield size={40} />
        </div>
        <div className="flex-1 space-y-2">
          <h4 className="text-xl font-black text-white">안전한 결제 환경을 보장합니다</h4>
          <p className="text-slate-500 font-medium">Keepy는 국제 표준 보안 규격(PCI-DSS)을 준수하는 Stripe 결제 엔진을 사용합니다. 모든 카드 정보는 암호화되어 안전하게 처리됩니다.</p>
        </div>
        <div className="flex gap-4">
           <div className="px-4 py-2 glass rounded-xl text-[10px] font-black text-slate-500 uppercase tracking-widest border-white/10">Visa</div>
           <div className="px-4 py-2 glass rounded-xl text-[10px] font-black text-slate-500 uppercase tracking-widest border-white/10">MasterCard</div>
           <div className="px-4 py-2 glass rounded-xl text-[10px] font-black text-slate-500 uppercase tracking-widest border-white/10">Amex</div>
        </div>
      </div>
    </div>
  );
};

export default BillingView;
