import { useState, useEffect, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Check, Sparkles, Crown, Zap, Star } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import { BACKEND_URL } from "@/lib/backend";

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

const PlanCard = ({ plan, isPopular, onSelect, isLoading }) => {
  const icons = {
    starter: <Zap className="w-8 h-8" />,
    pro: <Crown className="w-8 h-8" />,
    unlimited: <Star className="w-8 h-8" />
  };

  const gradients = {
    starter: "from-blue-500/20 to-cyan-500/20",
    pro: "from-purple-500/20 to-pink-500/20",
    unlimited: "from-amber-500/20 to-orange-500/20"
  };

  const buttonColors = {
    starter: "bg-blue-500 hover:bg-blue-600",
    pro: "bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600",
    unlimited: "bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600"
  };

  return (
    <div 
      className={`relative rounded-3xl p-6 glass-ios bg-gradient-to-br ${gradients[plan.id]} ${isPopular ? 'ring-2 ring-purple-500 scale-105' : ''}`}
      data-testid={`plan-card-${plan.id}`}
    >
      {isPopular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-purple-500 rounded-full text-xs font-bold">
          Popular
        </div>
      )}
      
      <div className="flex items-center gap-3 mb-4">
        <div className={`p-3 rounded-2xl ${plan.id === 'starter' ? 'bg-blue-500/20' : plan.id === 'pro' ? 'bg-purple-500/20' : 'bg-amber-500/20'}`}>
          {icons[plan.id]}
        </div>
        <div>
          <h3 className="text-xl font-bold">{plan.name_ru}</h3>
          <p className="text-white/50 text-sm">{plan.name}</p>
        </div>
      </div>
      
      <div className="mb-6">
        <span className="text-4xl font-bold">${plan.price}</span>
        <span className="text-white/50">/month</span>
      </div>
      
      <ul className="space-y-3 mb-6">
        {plan.features.map((feature, index) => (
          <li key={index} className="flex items-center gap-2">
            <Check className="w-5 h-5 text-green-400" />
            <span className="text-white/80">{feature}</span>
          </li>
        ))}
      </ul>
      
      <button
        onClick={() => onSelect(plan.id)}
        disabled={isLoading}
        className={`w-full py-3 rounded-xl font-semibold text-white transition-all ${buttonColors[plan.id]} disabled:opacity-50`}
        data-testid={`select-plan-${plan.id}`}
      >
        {isLoading ? (
          <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
        ) : (
          "Choose plan"
        )}
      </button>
    </div>
  );
};

export const PricingPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [plans, setPlans] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const stars = useMemo(() => generateStars(100), []);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API}/subscription/plans`);
      setPlans(response.data.plans);
    } catch (error) {
      console.error("Failed to fetch plans:", error);
      // Fallback plans
      setPlans([
        {
          id: "starter",
          name: "Starter",
          name_ru: "Starter",
          price: 7.99,
          features: ["10 videos/month", "720p", "Basic formats"]
        },
        {
          id: "pro",
          name: "Pro",
          name_ru: "Pro",
          price: 19.00,
          features: ["50 videos/month", "1080p", "All formats", "Priority generation"]
        },
        {
          id: "unlimited",
          name: "Unlimited",
          name_ru: "Unlimited",
          price: 79.00,
          features: ["Unlimited videos", "4K", "All formats", "API access", "Priority support"]
        }
      ]);
    }
  };

  const handleSelectPlan = async (planId) => {
    setSelectedPlan(planId);
    setIsLoading(true);
    
    try {
      toast.info("Checkout moves to Whop in a later release.");
    } finally {
      setIsLoading(false);
      setSelectedPlan(null);
    }
  };

  return (
    <div className="min-h-screen bg-black relative overflow-hidden" data-testid="pricing-page">
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

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between p-4">
        <button
          onClick={() => navigate("/")}
          className="p-2 rounded-full glass-ios"
          data-testid="back-button"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-400" />
          <span className="font-semibold">nind</span>
        </div>
        <div className="w-10" />
      </header>

      {/* Main Content */}
      <main className="relative z-10 px-4 py-8 max-w-5xl mx-auto">
        {/* Title */}
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold mb-4 bg-gradient-to-r from-white via-purple-200 to-white bg-clip-text text-transparent">
            Choose a plan
          </h1>
          <p className="text-white/60 text-lg max-w-md mx-auto">
            Make professional videos with AI
          </p>
        </div>

        {/* Plans Grid */}
        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          {plans.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              isPopular={plan.id === "pro"}
              onSelect={handleSelectPlan}
              isLoading={isLoading && selectedPlan === plan.id}
            />
          ))}
        </div>

        {/* Features comparison */}
        <div className="mt-16 text-center">
          <p className="text-white/40 text-sm">
            Every plan includes secure payments, cancel anytime, and support
          </p>
        </div>
      </main>
    </div>
  );
};

export default PricingPage;
