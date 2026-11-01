import { useMemo } from "react";
import { useNavigate } from "react-router-dom";

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
  const stars = useMemo(() => generateStars(100), []);

  return (
    <div className="min-h-screen bg-black relative overflow-hidden flex items-center justify-center" data-testid="subscription-success-page">
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
        <h1 className="text-3xl font-bold mb-3">Payments are moving</h1>
        <p className="text-white/60 mb-6">
          Stripe checkout is turned off. Subscriptions will be handled with Whop in a later release.
        </p>
        <button
          type="button"
          onClick={() => navigate("/")}
          className="px-8 py-3 rounded-xl bg-white text-black font-semibold"
        >
          Back home
        </button>
      </div>
    </div>
  );
};

export default SubscriptionSuccessPage;
