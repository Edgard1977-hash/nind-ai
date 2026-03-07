import { useState, useEffect, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { CheckCircle, ArrowLeft, Sparkles, Loader2 } from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Generate random stars
const generateStars = (count) => {
  return Array.from({ length: count }).map((_, i) => ({
    id: i,
    left: Math.random() * 100,
    top: Math.random() * 100,
    size: Math.random() * 2 + 1,
    delay: Math.random() * 4,
    duration: Math.random() * 3 + 2,
  }));
};

export const SubscriptionSuccessPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session_id");
  
  const [status, setStatus] = useState("checking");
  const [paymentData, setPaymentData] = useState(null);
  const [pollAttempts, setPollAttempts] = useState(0);
  const stars = useMemo(() => generateStars(100), []);

  useEffect(() => {
    if (sessionId) {
      pollPaymentStatus();
    } else {
      setStatus("error");
    }
  }, [sessionId]);

  const pollPaymentStatus = async () => {
    if (pollAttempts >= 5) {
      setStatus("timeout");
      return;
    }

    try {
      const response = await axios.get(`${API}/subscription/status/${sessionId}`);
      const data = response.data;
      
      if (data.payment_status === "paid") {
        setStatus("success");
        setPaymentData(data);
      } else if (data.status === "expired") {
        setStatus("expired");
      } else {
        // Continue polling
        setPollAttempts(prev => prev + 1);
        setTimeout(pollPaymentStatus, 2000);
      }
    } catch (error) {
      console.error("Error checking payment status:", error);
      setStatus("error");
    }
  };

  return (
    <div className="min-h-screen bg-black relative overflow-hidden flex items-center justify-center" data-testid="subscription-success-page">
      {/* Space Background */}
      <div className="space-bg">
        <div className="stars">
          {stars.map((star) => (
            <div
              key={star.id}
              className="star"
              style={{
                left: `${star.left}%`,
                top: `${star.top}%`,
                width: `${star.size}px`,
                height: `${star.size}px`,
                animationDelay: `${star.delay}s`,
                animationDuration: `${star.duration}s`,
              }}
            />
          ))}
        </div>
      </div>

      <div className="relative z-10 text-center px-4 max-w-md mx-auto">
        {status === "checking" && (
          <>
            <Loader2 className="w-16 h-16 mx-auto mb-6 text-purple-400 animate-spin" />
            <h1 className="text-2xl font-bold mb-2">Проверяем оплату...</h1>
            <p className="text-white/60">Пожалуйста, подождите</p>
          </>
        )}

        {status === "success" && (
          <>
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-green-500/20 flex items-center justify-center">
              <CheckCircle className="w-12 h-12 text-green-400" />
            </div>
            <h1 className="text-3xl font-bold mb-2">Оплата успешна!</h1>
            <p className="text-white/60 mb-6">
              Ваша подписка активирована. Спасибо за покупку!
            </p>
            {paymentData?.metadata?.plan_name && (
              <p className="text-purple-400 font-semibold mb-6">
                План: {paymentData.metadata.plan_name}
              </p>
            )}
            <button
              onClick={() => navigate("/create")}
              className="px-8 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold hover:from-purple-600 hover:to-pink-600 transition-all"
              data-testid="start-creating-btn"
            >
              Начать создавать
            </button>
          </>
        )}

        {status === "timeout" && (
          <>
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-yellow-500/20 flex items-center justify-center">
              <Sparkles className="w-12 h-12 text-yellow-400" />
            </div>
            <h1 className="text-2xl font-bold mb-2">Обработка платежа</h1>
            <p className="text-white/60 mb-6">
              Платёж обрабатывается. Проверьте email для подтверждения.
            </p>
            <button
              onClick={() => navigate("/")}
              className="px-8 py-3 rounded-xl glass-ios text-white font-semibold hover:bg-white/10 transition-all"
            >
              На главную
            </button>
          </>
        )}

        {(status === "error" || status === "expired") && (
          <>
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-red-500/20 flex items-center justify-center">
              <ArrowLeft className="w-12 h-12 text-red-400" />
            </div>
            <h1 className="text-2xl font-bold mb-2">
              {status === "expired" ? "Сессия истекла" : "Ошибка"}
            </h1>
            <p className="text-white/60 mb-6">
              {status === "expired" 
                ? "Платёжная сессия истекла. Пожалуйста, попробуйте снова." 
                : "Произошла ошибка при проверке оплаты."}
            </p>
            <button
              onClick={() => navigate("/pricing")}
              className="px-8 py-3 rounded-xl glass-ios text-white font-semibold hover:bg-white/10 transition-all"
            >
              Вернуться к тарифам
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default SubscriptionSuccessPage;
