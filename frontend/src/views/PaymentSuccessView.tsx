import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { CheckCircle, Loader, ArrowRight } from 'lucide-react';
import { billingApi } from '../lib/api';

const PaymentSuccessView: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const orgId = searchParams.get('orgId');
  const planId = searchParams.get('planId');
  const paymentKey = searchParams.get('paymentKey');
  const orderId = searchParams.get('orderId');
  const amount = searchParams.get('amount');

  useEffect(() => {
    const confirmPayment = async () => {
      try {
        if (!orgId || !planId || !paymentKey || !orderId || !amount) {
          throw new Error('필수 결제 정보가 누락되었습니다.');
        }

        // 실제로는 백엔드에서 토스 API를 호출하여 최종 승인을 받아야 함
        // 여기서는 시뮬레이션으로 백엔드 구독 API 호출
        await billingApi.subscribe(parseInt(orgId), planId);
        
        setLoading(false);
      } catch (err: any) {
        console.error('Payment confirmation failed:', err);
        setError(err.message || '결제 승인 중 오류가 발생했습니다.');
        setLoading(false);
      }
    };

    confirmPayment();
  }, [orgId, planId, paymentKey, orderId, amount]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#080a0f] flex flex-col items-center justify-center p-6">
        <Loader className="text-emerald-400 animate-spin mb-6" size={48} />
        <h2 className="text-2xl font-black text-white">결제 승인 중...</h2>
        <p className="text-slate-500 mt-2 font-medium">잠시만 기다려 주세요. 안전하게 결제를 처리하고 있습니다.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#080a0f] flex flex-col items-center justify-center p-6 text-center">
        <div className="w-20 h-20 rounded-3xl bg-red-500/10 flex items-center justify-center text-red-500 mb-6">
          <CheckCircle size={40} className="rotate-180" />
        </div>
        <h2 className="text-2xl font-black text-white">결제 처리 오류</h2>
        <p className="text-slate-500 mt-2 max-w-md">{error}</p>
        <button 
          onClick={() => window.location.href = '/'}
          className="mt-8 bg-white/5 text-white px-8 py-4 rounded-2xl font-black hover:bg-white/10 transition-all"
        >
          대시보드로 돌아가기
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#080a0f] flex flex-col items-center justify-center p-6 text-center">
      <div className="w-24 h-24 rounded-[40px] bg-emerald-500/20 flex items-center justify-center text-emerald-400 mb-8 shadow-2xl shadow-emerald-500/20">
        <CheckCircle size={48} />
      </div>
      <h1 className="text-4xl font-black text-white tracking-tight mb-2">결제가 완료되었습니다!</h1>
      <p className="text-slate-400 text-lg font-medium mb-10">Keepy {planId?.toUpperCase()} 플랜 구독이 성공적으로 시작되었습니다.</p>
      
      <div className="glass p-8 rounded-[32px] border-white/5 w-full max-w-sm space-y-4 mb-10">
        <div className="flex justify-between items-center text-sm">
          <span className="text-slate-500 font-bold uppercase tracking-widest">결제 금액</span>
          <span className="text-white font-black">₩{parseInt(amount || '0').toLocaleString()}</span>
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-slate-500 font-bold uppercase tracking-widest">주문 번호</span>
          <span className="text-white font-medium truncate ml-4">{orderId}</span>
        </div>
      </div>

      <button 
        onClick={() => window.location.href = '/'}
        className="bg-emerald-500 text-white px-10 py-5 rounded-2xl font-black flex items-center gap-3 hover:bg-emerald-600 transition-all shadow-2xl shadow-emerald-500/30 active:scale-95"
      >
        모니터링 시작하기 <ArrowRight size={20} />
      </button>
    </div>
  );
};

export default PaymentSuccessView;
